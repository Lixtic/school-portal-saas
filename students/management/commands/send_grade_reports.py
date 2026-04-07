"""
Send term grade report summaries to parents via email and in-app notification.

Run after grades have been entered for a term:
    python manage.py send_grade_reports --term first
    python manage.py send_grade_reports --term second --dry-run
    python manage.py send_grade_reports --term third --class "Basic 9"
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg, Max, Min
from django.template.loader import render_to_string
from django.utils import timezone

from academics.models import AcademicYear
from announcements.models import Notification
from students.models import Grade, Student


class Command(BaseCommand):
    help = 'Email parents a summary of their child\'s grades for a given term'

    def add_arguments(self, parser):
        parser.add_argument(
            '--term',
            type=str,
            required=True,
            choices=['first', 'second', 'third'],
            help='Term to report on: first, second, or third',
        )
        parser.add_argument(
            '--class',
            type=str,
            default='',
            dest='class_name',
            help='Limit to a specific class name (e.g. "Basic 7")',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        term = options['term']
        class_filter = options['class_name']
        dry_run = options['dry_run']

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            self.stderr.write('No current academic year found — aborting.')
            return

        term_display = dict(Grade.TERM_CHOICES).get(term, term.title())

        # Find students who have grades this term
        grade_qs = (
            Grade.objects
            .filter(academic_year=current_year, term=term)
            .select_related('student', 'student__user', 'student__current_class', 'subject')
        )

        if class_filter:
            grade_qs = grade_qs.filter(student__current_class__name__iexact=class_filter)

        # Group grades by student
        student_ids = grade_qs.values_list('student_id', flat=True).distinct()
        students = (
            Student.objects
            .filter(id__in=student_ids)
            .select_related('user', 'current_class')
        )

        emails_sent = 0
        notifs_created = 0
        students_processed = 0

        for student in students:
            grades = list(
                grade_qs.filter(student=student)
                .order_by('subject__name')
            )
            if not grades:
                continue

            students_processed += 1
            student_name = student.user.get_full_name() or student.user.username
            class_name = getattr(student.current_class, 'name', '')

            # Build per-subject summary
            subjects = []
            total_sum = 0
            for g in grades:
                subjects.append({
                    'name': g.subject.name,
                    'class_score': float(g.class_score),
                    'exams_score': float(g.exams_score),
                    'total_score': float(g.total_score),
                    'grade': g.grade,
                    'remarks': g.remarks,
                    'position': g.subject_position,
                })
                total_sum += float(g.total_score)

            num_subjects = len(subjects)
            average = round(total_sum / num_subjects, 1) if num_subjects else 0
            best = max(subjects, key=lambda s: s['total_score']) if subjects else None
            weakest = min(subjects, key=lambda s: s['total_score']) if subjects else None

            # ── In-app notification to student ─────────────────
            notif_msg = (
                f"Your {term_display} grade report is ready. "
                f"Average: {average}% across {num_subjects} subject(s)."
            )

            if not dry_run:
                Notification.objects.get_or_create(
                    recipient=student.user,
                    alert_type='general',
                    message=notif_msg,
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

                # Respect parent email & grade preferences
                try:
                    settings = parent.user.settings
                    if not settings.email_notifications or not settings.notify_grades:
                        continue
                except Exception:
                    pass

                parent_name = parent.user.get_full_name() or parent.user.username

                ctx = {
                    'parent_name': parent_name,
                    'student_name': student_name,
                    'class_name': class_name,
                    'term_display': term_display,
                    'academic_year': current_year.name,
                    'subjects': subjects,
                    'num_subjects': num_subjects,
                    'average': average,
                    'best_subject': best,
                    'weakest_subject': weakest,
                    'report_date': timezone.localdate(),
                }

                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Email → {email_addr} | "
                        f"{student_name}: {num_subjects} subjects, "
                        f"avg {average}%"
                    )
                    emails_sent += 1
                    continue

                # Build plain text fallback
                text_lines = [
                    f"Dear {parent_name},\n",
                    f"{student_name}'s {term_display} grade report "
                    f"for {current_year.name} is now available.\n",
                    f"Class: {class_name}" if class_name else '',
                    f"Subjects: {num_subjects}",
                    f"Average Score: {average}%\n",
                    "Subject Breakdown:",
                ]
                for s in subjects:
                    text_lines.append(
                        f"  {s['name']}: {s['total_score']}% "
                        f"(Grade {s['grade']})"
                    )
                text_lines.append(
                    f"\nBest: {best['name']} ({best['total_score']}%)" if best else ''
                )
                text_lines.append(
                    f"Needs Attention: {weakest['name']} ({weakest['total_score']}%)" if weakest else ''
                )
                text_lines.append(
                    "\nPlease log in to SchoolPadi for the full detailed report."
                    "\n\nThank you."
                )
                text_body = '\n'.join(line for line in text_lines if line)

                try:
                    html_body = render_to_string(
                        'students/emails/grade_report.html', ctx
                    )
                except Exception:
                    html_body = None

                try:
                    email = EmailMultiAlternatives(
                        subject=(
                            f"Grade Report — {student_name} "
                            f"({term_display}, {current_year.name})"
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
            f"{tag} {emails_sent} grade report email(s), "
            f"{notifs_created} in-app notification(s) for "
            f"{students_processed} student(s) — "
            f"{term_display}, {current_year.name}."
        ))
