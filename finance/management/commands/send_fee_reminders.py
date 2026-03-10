import datetime
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from finance.models import StudentFee
from announcements.models import Notification


class Command(BaseCommand):
    help = 'Send fee reminder notifications (in-app + email to parents) for unpaid/partial fees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would happen without sending anything',
        )
        parser.add_argument(
            '--overdue-only',
            action='store_true',
            help='Only process fees whose due date has already passed',
        )
        parser.add_argument(
            '--skip-email',
            action='store_true',
            help='Create in-app notifications only; do not send emails to parents',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overdue_only = options['overdue_only']
        skip_email = options['skip_email']

        qs = (
            StudentFee.objects
            .filter(status__in=['unpaid', 'partial'])
            .select_related(
                'student', 'student__user',
                'fee_structure', 'fee_structure__head', 'fee_structure__class_name',
            )
        )
        if overdue_only:
            today = timezone.localdate()
            qs = qs.filter(fee_structure__due_date__lt=today)

        in_app_created = 0
        in_app_skipped = 0
        emails_sent = 0
        emails_skipped = 0

        for fee in qs:
            student = fee.student
            user = student.user
            balance = fee.balance
            head_name = fee.fee_structure.head.name

            try:
                link = reverse('finance:student_fees', args=[student.id])
            except Exception:
                link = '/finance/'

            message = (
                f"Fee Reminder: You have an outstanding balance of \u20b5{balance:.2f} "
                f"for {head_name}. Please make payment at your earliest convenience."
            )

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] In-app → {user.get_full_name()} ({user.username}): {message}"
                )
                in_app_created += 1
            else:
                already_pending = Notification.objects.filter(
                    recipient=user,
                    alert_type='general',
                    is_read=False,
                    message__startswith='Fee Reminder: You have an outstanding balance',
                    link=link,
                ).exists()

                if already_pending:
                    in_app_skipped += 1
                else:
                    Notification.objects.create(
                        recipient=user,
                        message=message,
                        alert_type='general',
                        link=link,
                    )
                    in_app_created += 1

            # ---- Email parents ----
            if skip_email:
                continue

            try:
                from parents.models import Parent
                parents = Parent.objects.filter(children=student).select_related('user')
            except Exception:
                parents = []

            for parent in parents:
                parent_email = getattr(parent.user, 'email', '') if hasattr(parent, 'user') else ''
                if not parent_email:
                    emails_skipped += 1
                    continue

                due_date = getattr(fee.fee_structure, 'due_date', None)
                email_context = {
                    'parent_name': parent.user.get_full_name() or parent.user.username,
                    'student_name': student.user.get_full_name(),
                    'head_name': head_name,
                    'balance': balance,
                    'due_date': due_date,
                    'class_name': getattr(fee.fee_structure.class_name, 'name', ''),
                }

                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Email → {parent_email} | "
                        f"{student.user.get_full_name()} owes \u20b5{balance:.2f} for {head_name}"
                    )
                    emails_sent += 1
                    continue

                try:
                    text_body = (
                        f"Dear {email_context['parent_name']},\n\n"
                        f"This is a reminder that {email_context['student_name']} has an "
                        f"outstanding fee balance of \u20b5{balance:.2f} for {head_name}"
                        f"{(' (due ' + str(due_date) + ')') if due_date else ''}.\n\n"
                        f"Please contact the school to arrange payment.\n\nThank you."
                    )
                    try:
                        html_body = render_to_string(
                            'finance/emails/fee_reminder.html', email_context
                        )
                    except Exception:
                        html_body = None

                    email = EmailMultiAlternatives(
                        subject=f"Fee Payment Reminder — {email_context['student_name']}",
                        body=text_body,
                        to=[parent_email],
                    )
                    if html_body:
                        email.attach_alternative(html_body, 'text/html')
                    email.send(fail_silently=False)
                    emails_sent += 1
                except Exception as exc:
                    self.stderr.write(f"Email failed for {parent_email}: {exc}")
                    emails_skipped += 1

        action = 'Would send' if dry_run else 'Sent'
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {in_app_created} in-app notification(s) "
                f"(skipped {in_app_skipped} duplicates). "
                f"{action} {emails_sent} parent email(s) (skipped {emails_skipped})."
            )
        )
