from django.urls import NoReverseMatch
from django.db import transaction


def onboarding_context(request):
    """
    Injects onboarding progress into every authenticated page.
    Uses a session flag to short-circuit after completion/dismissal.
    """
    if not request.user.is_authenticated:
        return {}

    if request.session.get('onboarding_done'):
        return {}

    from accounts.onboarding import ONBOARDING_STEPS
    from accounts.models import OnboardingProgress
    from django.urls import reverse

    try:
        with transaction.atomic():
            progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)

        if progress.dismissed:
            request.session['onboarding_done'] = True
            return {}

        role = request.user.user_type
        steps_config = ONBOARDING_STEPS.get(role, [])
        if not steps_config:
            return {}

        steps = []
        done_count = 0
        for s in steps_config:
            done = s['id'] in progress.steps_completed
            if done:
                done_count += 1
            try:
                url = reverse(s['url_name'])
            except (NoReverseMatch, Exception):
                url = '#'
            steps.append({**s, 'done': done, 'url': url})

        total = len(steps)
        pct = round((done_count / total * 100) if total else 0)
        all_done = done_count == total

        # Mark completion timestamp if all steps done and not yet recorded
        if all_done and not progress.completed_at:
            from django.utils import timezone
            progress.completed_at = timezone.now()
            progress.save()

        # If previously completed: show celebration exactly once, then hide widget
        if progress.completed_at:
            if request.session.get('onboarding_celebration_shown'):
                request.session['onboarding_done'] = True
                return {}
            # First time seeing completion — show confetti, mark celebration shown
            request.session['onboarding_celebration_shown'] = True

        # Consume the "just marked" nudge set by the middleware
        just_marked = request.session.pop('onboarding_just_marked', None)

        # Auto-open / intro tip fires exactly once (on the very first page view)
        is_first_visit = not request.session.get('ob_intro_shown', False)
        if is_first_visit:
            request.session['ob_intro_shown'] = True

        return {
            'onboarding_steps': steps,
            'onboarding_done_count': done_count,
            'onboarding_total': total,
            'onboarding_pct': pct,
            'onboarding_just_marked': just_marked,
            'onboarding_is_first_visit': is_first_visit,
            'onboarding_all_done': all_done,
        }

    except Exception:
        return {}
