class OnboardingAutoMarkMiddleware:
    """
    After every successful GET response, checks if the current page matches
    an onboarding step trigger and marks it automatically. Uses
    request.session['onboarding_done'] to skip the DB query once the user
    has finished or dismissed onboarding.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.user.is_authenticated
            and request.method == 'GET'
            and response.status_code < 400
            and not request.session.get('onboarding_done')
            and not request.path.startswith('/admin/')
        ):
            self._auto_mark(request)
        return response

    # -----------------------------------------------------------
    def _auto_mark(self, request):
        try:
            rm = getattr(request, 'resolver_match', None)
            if not rm or not rm.url_name:
                return

            current_view = (
                f"{rm.app_name}:{rm.url_name}" if rm.app_name else rm.url_name
            )

            from accounts.onboarding import ONBOARDING_STEPS

            role_steps = ONBOARDING_STEPS.get(request.user.user_type, [])
            triggered = [
                s for s in role_steps if s.get('trigger_view') == current_view
            ]
            if not triggered:
                return

            from accounts.models import OnboardingProgress

            progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)
            if progress.dismissed or progress.completed_at:
                request.session['onboarding_done'] = True
                return

            changed = False
            just_marked = None
            for s in triggered:
                if progress.mark_step(s['id']):
                    just_marked = s
                    changed = True

            if not changed:
                return

            # Detect full completion
            all_ids = {s['id'] for s in role_steps}
            if all_ids.issubset(set(progress.steps_completed)):
                from django.utils import timezone
                progress.completed_at = timezone.now()

            progress.save()

            # Store nudge for the context processor to display on the NEXT page
            if just_marked:
                request.session['onboarding_just_marked'] = {
                    'id': just_marked['id'],
                    'title': just_marked['title'],
                    'icon': just_marked['icon'],
                }

        except Exception:
            pass
