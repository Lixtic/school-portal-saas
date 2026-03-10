"""
Management command: send_trial_reminders

Run this daily (e.g. via Vercel cron or Railway cron) to notify schools
when their trial is 7, 3 or 1 day(s) from expiring.

Usage:
    python manage.py send_trial_reminders
    python manage.py send_trial_reminders --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

REMINDER_DAYS = [7, 3, 1]


class Command(BaseCommand):
    help = 'Send trial-expiry reminder emails to schools (7-day, 3-day, 1-day warnings)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which schools would be emailed without actually sending',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        today = now.date()

        # Import here to avoid AppRegistryNotReady issues
        from tenants.models import SchoolSubscription

        sent = 0
        skipped = 0
        errors = 0

        for days_left in REMINDER_DAYS:
            target_date = today + timedelta(days=days_left)

            # Find trial subscriptions that expire on the target date
            subscriptions = SchoolSubscription.objects.filter(
                status='trial',
                trial_ends_at__date=target_date,
            ).select_related('school', 'plan')

            for sub in subscriptions:
                school = sub.school
                email = school.contact_person_email

                if not email:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  SKIP {school.schema_name}: no contact email'
                        )
                    )
                    skipped += 1
                    continue

                label = f'{days_left} day{"s" if days_left != 1 else ""}'
                subject = f'⏰ Your school trial expires in {label} — {school.name}'

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [DRY RUN] Would send {label} reminder → {email} ({school.name})'
                        )
                    )
                    sent += 1
                    continue

                try:
                    _send_reminder(school, sub, days_left, subject)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Sent {label} reminder → {email} ({school.name})'
                        )
                    )
                    sent += 1
                except Exception as exc:
                    logger.error(
                        f'Failed to send trial reminder for {school.schema_name}: {exc}',
                        exc_info=True,
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ FAILED {label} reminder → {email} ({school.name}): {exc}'
                        )
                    )
                    errors += 1

        action = 'Would send' if dry_run else 'Sent'
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone — {action}: {sent}, Skipped: {skipped}, Errors: {errors}'
            )
        )


def _send_reminder(school, subscription, days_left, subject):
    """Render and send a single trial reminder email."""
    site_url = getattr(settings, 'SITE_URL', 'https://yourapp.com')
    login_url = f'{site_url}/{school.schema_name}/login/'

    context = {
        'school': school,
        'subscription': subscription,
        'contact_name': school.contact_person_name or 'Administrator',
        'days_left': days_left,
        'trial_ends_at': subscription.trial_ends_at,
        'plan': subscription.plan,
        'login_url': login_url,
        'pricing_url': f'{site_url}/tenants/pricing/',
        'subscription_url': f'{site_url}/{school.schema_name}/tenants/subscription/',
        'urgent': days_left <= 1,
    }

    html_content = render_to_string('tenants/emails/trial_reminder.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[school.contact_person_email],
        reply_to=[settings.DEFAULT_FROM_EMAIL],
    )
    email.attach_alternative(html_content, 'text/html')
    email.send(fail_silently=False)
