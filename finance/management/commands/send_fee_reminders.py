from django.core.management.base import BaseCommand
from django.urls import reverse
from finance.models import StudentFee
from announcements.models import Notification


class Command(BaseCommand):
    help = 'Send fee reminder notifications to all students with unpaid or partial fees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would happen without creating notifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        pending_fees = (
            StudentFee.objects
            .filter(status__in=['unpaid', 'partial'])
            .select_related('student', 'student__user', 'fee_structure', 'fee_structure__head')
        )

        created = 0
        skipped = 0

        for fee in pending_fees:
            student = fee.student
            user = student.user
            balance = fee.balance
            head_name = fee.fee_structure.head.name

            # Build the link to the student's fee page
            try:
                link = reverse('finance:student_fees', args=[student.id])
            except Exception:
                link = '/finance/'

            message = (
                f"Fee Reminder: You have an outstanding balance of ₵{balance:.2f} "
                f"for {head_name}. Please make payment at your earliest convenience."
            )

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would notify {user.get_full_name()} ({user.username}): {message}"
                )
                created += 1
                continue

            # Avoid duplicate reminders (check if an unread one already exists)
            already_pending = Notification.objects.filter(
                recipient=user,
                alert_type='general',
                is_read=False,
                message__startswith=f"Fee Reminder: You have an outstanding balance",
                link=link,
            ).exists()

            if already_pending:
                skipped += 1
                continue

            Notification.objects.create(
                recipient=user,
                message=message,
                alert_type='general',
                link=link,
            )
            created += 1

        action = "Would send" if dry_run else "Sent"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {created} fee reminder(s). Skipped {skipped} (already pending)."
            )
        )
