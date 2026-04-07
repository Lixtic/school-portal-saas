"""
Send email alerts to parents when their child's attendance drops below a threshold.

Unlike send_absence_alerts (daily, single-absence), this command checks cumulative
attendance over a rolling window and flags students below the threshold.

Usage:
    python manage.py send_low_attendance_alerts
    python manage.py send_low_attendance_alerts --threshold 75
    python manage.py send_low_attendance_alerts --days 30 --dry-run
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.utils import timezone

from academics.models import AcademicYear
from announcements.models import Notification
from students.models import Attendance, Student


class Command(BaseCommand):
    help = (
        'Email parents when a student\'s attendance rate drops below a '
        'threshold over a rolling window (default: 80%% over 30 days)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=80,
            help='Minimum attendance percentage (default 80)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Rolling window in calendar days (default 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        days = options['days']
        dry_run = options['dry_run']

        today = timezone.localdate()
        window_start = today - timedelta(days=days)

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            self.stderr.write('No current academic year found — aborting.')
            return

        # Get all students with at least one attendance record in the window
        students_with_attendance = (
            Student.objects
            .filter(
                attendance__date__gte=window_start,
                attendance__date__lte=today,
            )
            .annotate(
                total_days=Count('attendance', filter=Q(
                    attendance__date__gte=window_start,
                    attendance__date__lte=today,
                )),
                absent_days=Count('attendance', filter=Q(
                    attendance__date__gte=window_start,
                    attendance__date__lte=today,
                    attendance__status='absent',
                )),
                present_days=Count('attendance', filter=Q(
                    attendance__date__gte=window_start,
                    attendance__date__lte=today,
                    attendance__status__in=['present', 'late'],
                )),
            )
            .select_related('user', 'current_class')
        )

        emails_sent = 0
        notifs_created = 0
        students_flagged = 0

        for student in students_with_attendance:
            if student.total_days == 0:
                continue

            rate = round((student.present_days / student.total_days) * 100, 1)
            if rate >= threshold:
                continue

            students_flagged += 1
            student_name = student.user.get_full_name() or student.user.username
            class_name = getattr(student.current_class, 'name', '')

            # ── In-app notification to student ─────────────────
            msg_text = (
                f"Attendance alert: Your attendance is {rate}% over the "
                f"last {days} days ({student.absent_days} absent out of "
                f"{student.total_days} school days). Please improve your attendance."
            )

            if not dry_run:
                Notification.objects.get_or_create(
                    recipient=student.user,
                    alert_type='general',
                    message=msg_text,
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

                # Respect parent email preference
                try:
                    settings = parent.user.settings
                    if not settings.email_notifications or not settings.notify_attendance:
                        continue
                except Exception:
                    pass

                parent_name = parent.user.get_full_name() or parent.user.username

                ctx = {
                    'parent_name': parent_name,
                    'student_name': student_name,
                    'class_name': class_name,
                    'attendance_rate': rate,
                    'threshold': threshold,
                    'days': days,
                    'total_days': student.total_days,
                    'present_days': student.present_days,
                    'absent_days': student.absent_days,
                    'window_start': window_start,
                    'window_end': today,
                }

                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Email → {email_addr} | "
                        f"{student_name} at {rate}% attendance "
                        f"({student.absent_days}/{student.total_days} absent)"
                    )
                    emails_sent += 1
                    continue

                text_body = (
                    f"Dear {parent_name},\n\n"
                    f"We are writing to inform you that {student_name}"
                    f"{(' (' + class_name + ')') if class_name else ''} "
                    f"has an attendance rate of {rate}% over the last {days} days.\n\n"
                    f"  - Days tracked: {student.total_days}\n"
                    f"  - Days present/late: {student.present_days}\n"
                    f"  - Days absent: {student.absent_days}\n\n"
                    f"The school requires a minimum of {threshold}% attendance. "
                    f"Please ensure your child attends school regularly.\n\n"
                    f"If there are extenuating circumstances, please contact "
                    f"the school administration.\n\nThank you."
                )

                try:
                    html_body = render_to_string(
                        'students/emails/low_attendance_alert.html', ctx
                    )
                except Exception:
                    html_body = None

                try:
                    email = EmailMultiAlternatives(
                        subject=(
                            f"Low Attendance Alert — {student_name} ({rate}%)"
                        ),
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
            f"{tag} {emails_sent} low-attendance email(s), "
            f"{notifs_created} in-app notification(s). "
            f"{students_flagged} student(s) below {threshold}% "
            f"in the last {days} days."
        ))
