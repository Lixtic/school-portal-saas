"""
Send email alerts to parents when their children are marked absent.

Run daily after attendance has been recorded:
    python manage.py send_absence_alerts
    python manage.py send_absence_alerts --date 2025-06-10
    python manage.py send_absence_alerts --dry-run
"""
from datetime import date as date_type

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from students.models import Attendance
from announcements.models import Notification


class Command(BaseCommand):
    help = 'Email parents when a child is marked absent today (or a given date)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default='',
            help='YYYY-MM-DD date to check. Defaults to today.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        if options['date']:
            target = date_type.fromisoformat(options['date'])
        else:
            target = timezone.localdate()

        dry_run = options['dry_run']

        absences = (
            Attendance.objects
            .filter(date=target, status='absent')
            .select_related('student', 'student__user', 'student__current_class')
        )

        emails_sent = 0
        notifs_created = 0

        for att in absences:
            student = att.student
            student_name = student.user.get_full_name() or student.user.username
            class_name = getattr(student.current_class, 'name', '')

            # ── In-app notification to student ─────────────────
            if not dry_run:
                Notification.objects.get_or_create(
                    recipient=student.user,
                    alert_type='general',
                    message=f"You were marked absent on {target.strftime('%d %b %Y')}.",
                    defaults={'link': ''},
                )
                notifs_created += 1

            # ── Email each linked parent ───────────────────────
            try:
                from parents.models import Parent
                parents = Parent.objects.filter(children=student).select_related('user')
            except Exception:
                parents = []

            for parent in parents:
                email_addr = getattr(parent.user, 'email', '')
                if not email_addr:
                    continue

                parent_name = parent.user.get_full_name() or parent.user.username

                ctx = {
                    'parent_name': parent_name,
                    'student_name': student_name,
                    'class_name': class_name,
                    'absence_date': target,
                    'remarks': att.remarks,
                }

                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Email → {email_addr} | "
                        f"{student_name} absent on {target}"
                    )
                    emails_sent += 1
                    continue

                text_body = (
                    f"Dear {parent_name},\n\n"
                    f"This is to inform you that {student_name}"
                    f"{(' (' + class_name + ')') if class_name else ''} "
                    f"was marked absent on {target.strftime('%A, %d %B %Y')}.\n"
                )
                if att.remarks:
                    text_body += f"Remarks: {att.remarks}\n"
                text_body += (
                    "\nIf your child was absent for a valid reason, "
                    "please contact the school to provide an excuse note.\n\n"
                    "Thank you."
                )

                try:
                    html_body = render_to_string(
                        'students/emails/absence_alert.html', ctx
                    )
                except Exception:
                    html_body = None

                try:
                    email = EmailMultiAlternatives(
                        subject=f"Absence Alert — {student_name} ({target.strftime('%d %b %Y')})",
                        body=text_body,
                        to=[email_addr],
                    )
                    if html_body:
                        email.attach_alternative(html_body, 'text/html')
                    email.send(fail_silently=False)
                    emails_sent += 1
                except Exception as exc:
                    self.stderr.write(f"Email failed for {email_addr}: {exc}")

        tag = 'Would send' if dry_run else 'Sent'
        self.stdout.write(self.style.SUCCESS(
            f"{tag} {emails_sent} absence alert email(s), "
            f"{notifs_created} in-app notification(s) for {target}."
        ))
