from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import date, timedelta
import calendar
import csv
import random
import string
from .models import Student, Attendance, Grade
from .forms import StudentForm, CSVImportForm, AuraPreferencesForm
from accounts.models import User

from .utils import calculate_class_position, normalize_term, term_filter_values
from academics.models import Class, AcademicYear, Timetable, Activity
from academics.gamification_models import StudentXP
from teachers.models import Teacher
from academics.tutor_models import generate_student_id_card, export_id_card_to_pdf, export_multiple_id_cards_to_pdf


def build_academic_calendar_widget(limit=5):
    today = timezone.now().date()
    current_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()

    events = []
    if current_year:
        total_days = max((current_year.end_date - current_year.start_date).days, 1)
        first_term_start = current_year.start_date
        second_term_start = current_year.start_date + timedelta(days=total_days // 3)
        third_term_start = current_year.start_date + timedelta(days=(2 * total_days) // 3)

        term_markers = [
            ('Term 1 Start', first_term_start, 'Term'),
            ('Term 2 Start', second_term_start, 'Term'),
            ('Term 3 Start', third_term_start, 'Term'),
            ('Academic Year Ends', current_year.end_date, 'Year End'),
        ]
        for title, when, tag in term_markers:
            events.append({'title': title, 'date': when, 'tag': tag})

    try:
        upcoming_activities = Activity.objects.filter(is_active=True, date__gte=today).order_by('date')[:limit]
        for activity in upcoming_activities:
            events.append({
                'title': activity.title,
                'date': activity.date,
                'tag': activity.tag or 'Activity',
            })
    except Exception:
        pass  # Table doesn't exist or query failed

    events.sort(key=lambda item: item['date'])

    display_year = today.year
    display_month = today.month
    month_start_weekday, month_days = calendar.monthrange(display_year, display_month)
    prev_month = display_month - 1 if display_month > 1 else 12
    prev_month_year = display_year if display_month > 1 else display_year - 1
    prev_month_days = calendar.monthrange(prev_month_year, prev_month)[1]

    event_map = {}
    for event in events:
        event_key = event['date'].isoformat()
        event_map.setdefault(event_key, []).append(event)

    cells = []

    for day in range(prev_month_days - month_start_weekday + 1, prev_month_days + 1):
        month_date = date(prev_month_year, prev_month, day)
        cells.append({
            'day': day,
            'date': month_date,
            'is_current_month': False,
            'is_today': month_date == today,
            'events': event_map.get(month_date.isoformat(), []),
        })

    for day in range(1, month_days + 1):
        month_date = date(display_year, display_month, day)
        cells.append({
            'day': day,
            'date': month_date,
            'is_current_month': True,
            'is_today': month_date == today,
            'events': event_map.get(month_date.isoformat(), []),
        })

    next_month = display_month + 1 if display_month < 12 else 1
    next_month_year = display_year if display_month < 12 else display_year + 1
    trailing_days = (7 - (len(cells) % 7)) % 7
    for day in range(1, trailing_days + 1):
        month_date = date(next_month_year, next_month, day)
        cells.append({
            'day': day,
            'date': month_date,
            'is_current_month': False,
            'is_today': month_date == today,
            'events': event_map.get(month_date.isoformat(), []),
        })

    calendar_weeks = [cells[index:index + 7] for index in range(0, len(cells), 7)]

    upcoming_events = [event for event in events if event['date'] >= today][:limit]

    return {
        'academic_calendar_year': current_year.name if current_year else 'Not Set',
        'academic_calendar_events': upcoming_events,
        'academic_calendar_month_label': date(display_year, display_month, 1).strftime('%B %Y'),
        'academic_calendar_weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'academic_calendar_weeks': calendar_weeks,
    }

@login_required
def student_list(request):
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    students = Student.objects.select_related('user', 'current_class').all()
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        students = students.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(admission_number__icontains=search)
        )
    
    # Filter by class
    # Logic: 
    # 1. If 'class' params in GET, use it and update session
    # 2. If no 'class' param in GET, check session
    # 3. If 'class' param is empty string (User selected "All"), clear session
    
    if 'class' in request.GET:
        class_filter = request.GET.get('class')
        if class_filter:
            request.session['student_filter_class'] = class_filter
        else:
            # User cleared filter
            if 'student_filter_class' in request.session:
                del request.session['student_filter_class']
    else:
        # No param, check session
        class_filter = request.session.get('student_filter_class', '')

    if class_filter:
        students = students.filter(current_class_id=class_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        students = students.order_by('user__first_name', 'user__last_name')
    elif sort_by == '-name':
        students = students.order_by('-user__first_name', '-user__last_name')
    elif sort_by == 'admission_number':
        students = students.order_by('admission_number')
    elif sort_by == '-admission_number':
        students = students.order_by('-admission_number')
    
    # Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(user__is_active=True).count()
    total_classes = Class.objects.filter(academic_year__is_current=True).count()
    classes = Class.objects.filter(academic_year__is_current=True)
    
    context = {
        'students': students,
        'total_students': total_students,
        'active_students': active_students,
        'total_classes': total_classes,
        'classes': classes,
        'current_class_filter': class_filter,  # Pass explicit filter state for template
    }
    
    return render(request, 'students/student_list.html', context)


@login_required
def at_risk_students(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    selected_term = request.GET.get('term', '').strip()
    selected_class = request.GET.get('class', '').strip()
    threshold_raw = request.GET.get('threshold', '').strip()

    try:
        risk_threshold = float(threshold_raw) if threshold_raw else 50.0
    except ValueError:
        risk_threshold = 50.0

    grades_qs = Grade.objects.select_related('student', 'student__user', 'student__current_class')
    if current_year:
        grades_qs = grades_qs.filter(academic_year=current_year)
    if selected_term:
        grades_qs = grades_qs.filter(term__in=term_filter_values(selected_term))
    if selected_class:
        grades_qs = grades_qs.filter(student__current_class_id=selected_class)

    averages = grades_qs.values('student_id').annotate(avg_score=Avg('total_score'))
    averages = averages.filter(avg_score__lt=risk_threshold).order_by('avg_score')

    student_ids = [row['student_id'] for row in averages]
    students = Student.objects.select_related('user', 'current_class').filter(id__in=student_ids)
    student_map = {s.id: s for s in students}

    at_risk = []
    for row in averages:
        student = student_map.get(row['student_id'])
        if student:
            at_risk.append({
                'student': student,
                'avg_score': row['avg_score'],
            })

    classes = Class.objects.filter(academic_year=current_year) if current_year else Class.objects.all()

    context = {
        'at_risk_students': at_risk,
        'risk_threshold': risk_threshold,
        'selected_term': selected_term,
        'selected_class': selected_class,
        'classes': classes,
        'current_year': current_year,
    }

    return render(request, 'students/at_risk_students.html', context)


@login_required
def student_details_ajax(request, student_id):
    """Return student details as JSON for modal"""
    student = get_object_or_404(Student, id=student_id)
    
    # Attendance stats
    total_attendance = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, status='present').count()
    absent_count = Attendance.objects.filter(student=student, status='absent').count()
    
    attendance_percentage = 0
    if total_attendance > 0:
        attendance_percentage = round((present_count / total_attendance) * 100, 2)
    
    # Grade stats
    grades = Grade.objects.filter(student=student)
    grades_count = grades.count()
    
    average_percentage = 0
    if grades.exists():
        total_percentage = sum([g.percentage() for g in grades])
        average_percentage = round(total_percentage / grades_count, 2)
    
    data = {
        'name': student.user.get_full_name(),
        'admission_number': student.admission_number,
        'date_of_birth': student.date_of_birth.strftime('%B %d, %Y'),
        'current_class': str(student.current_class) if student.current_class else None,
        'email': student.user.email,
        'emergency_contact': student.emergency_contact,
        'blood_group': student.blood_group,
        'attendance': {
            'present': present_count,
            'absent': absent_count,
            'total': total_attendance,
            'percentage': attendance_percentage
        },
        'grades_count': grades_count,
        'average_percentage': average_percentage
    }
    
    return JsonResponse(data)


@login_required
def student_detail_page(request, student_id):
    """Full student detail page with attendance calendar"""
    student = get_object_or_404(Student, id=student_id)
    
    # Access control
    if request.user.user_type == 'student':
        if request.user != student.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get current year and date filter
    current_year = AcademicYear.objects.filter(is_current=True).first()
    selected_year = request.GET.get('year', timezone.now().year)
    try:
        selected_year = int(selected_year)
    except Exception:
        selected_year = timezone.now().year
    
    # Get all attendance records for the selected year
    attendance_records = Attendance.objects.filter(
        student=student,
        date__year=selected_year
    ).order_by('date')
    
    # Calculate attendance stats
    total_present = attendance_records.filter(status='present').count()
    total_late = attendance_records.filter(status='late').count()
    total_absent = attendance_records.filter(status='absent').count()
    total_holiday = 0  # You could add holiday tracking if needed
    
    # Build attendance calendar data (all 12 months)
    attendance_calendar = {}
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        # Get days in month
        _, days_in_month = calendar.monthrange(selected_year, month)
        
        # Get attendance for this month
        month_attendance = attendance_records.filter(date__month=month)
        attendance_dict = {record.date.day: record.status for record in month_attendance}
        
        # Build days array
        days = []
        for day in range(1, days_in_month + 1):
            status = attendance_dict.get(day, None)
            days.append({
                'day': day,
                'status': status,
                'display': 'P' if status == 'present' else 'A' if status == 'absent' else 'L' if status == 'late' else 'H' if status == 'excused' else ''
            })
        
        attendance_calendar[month_name] = days
    
    # Recent grades
    recent_grades = Grade.objects.filter(student=student).select_related(
        'subject', 'academic_year', 'student__current_class'
    ).order_by('-academic_year__start_date', '-created_at')[:10]
    
    # Calculate average grade
    grades = Grade.objects.filter(student=student)
    average_grade = 0
    if grades.exists():
        total_score = sum([g.percentage() for g in grades if g.percentage() > 0])
        count = len([g for g in grades if g.percentage() > 0])
        if count > 0:
            average_grade = round(total_score / count, 2)
    
    context = {
        'student': student,
        'current_year': current_year,
        'selected_year': selected_year,
        'total_present': total_present,
        'total_late': total_late,
        'total_absent': total_absent,
        'total_holiday': total_holiday,
        'attendance_calendar': attendance_calendar,
        'recent_grades': recent_grades,
        'average_grade': average_grade,
    }
    
    return render(request, 'students/student_detail.html', context)


@login_required
def bulk_assign_class(request):
    """Bulk assign students to a class"""
    if request.user.user_type not in ['admin', 'teacher']:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)

    student_ids = data.get('student_ids', [])
    class_id = data.get('class_id')

    if not student_ids or not class_id:
        return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

    class_obj = get_object_or_404(Class, id=class_id)
    Student.objects.filter(id__in=student_ids).update(current_class=class_obj)

    return JsonResponse({
        'status': 'success',
        'message': f'{len(student_ids)} students assigned to {class_obj.name}'
    })


@login_required
def export_students(request):
    """Export selected students as CSV"""
    student_ids = request.GET.get('ids', '').split(',')
    students = Student.objects.filter(id__in=student_ids).select_related('user', 'current_class')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Admission No', 'First Name', 'Last Name', 'Class', 'Roll No', 'Email', 'Emergency Contact'])
    
    for student in students:
        writer.writerow([
            student.admission_number,
            student.user.first_name,
            student.user.last_name,
            str(student.current_class) if student.current_class else '',
            student.roll_number,
            student.user.email,
            student.emergency_contact
        ])
    
    return response


@login_required
def mark_attendance(request):
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'You do not have permission to mark attendance')
        return redirect('dashboard')

    # Limit teachers to the classes they manage/teach
    classes_qs = Class.objects.filter(academic_year__is_current=True)
    allowed_classes = classes_qs
    teacher_profile = None
    if request.user.user_type == 'teacher':
        teacher_profile = Teacher.objects.filter(user=request.user).first()
        # ONLY Class Teachers can mark attendance
        allowed_classes = classes_qs.filter(class_teacher=teacher_profile)
        
        if not allowed_classes.exists():
            messages.error(request, 'You must be a Class Teacher to mark attendance')
            return redirect('dashboard')
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        student_ids = request.POST.getlist('students')
        class_id = request.POST.get('class_id')

        if not class_id:
            messages.error(request, 'Select a class before submitting attendance')
            return redirect('students:mark_attendance')

        class_obj = get_object_or_404(classes_qs, id=class_id)
        if request.user.user_type == 'teacher' and class_obj not in allowed_classes:
            messages.error(request, 'You are not assigned to this class')
            return redirect('students:mark_attendance')
        
        for student_id in student_ids:
            status = request.POST.get(f'status_{student_id}')
            student = Student.objects.filter(id=student_id, current_class=class_obj).first()
            if not student:
                continue
            
            Attendance.objects.update_or_create(
                student=student,
                date=date_str,
                defaults={
                    'status': status,
                    'marked_by': request.user
                }
            )

            # SMS alert for absences (non-blocking — failure does not break attendance saving)
            if status == 'absent':
                try:
                    from announcements.sms_service import send_attendance_alert
                    send_attendance_alert(student, status, str(date_str))
                except Exception:
                    pass
        
        messages.success(request, f'Attendance marked successfully for {len(student_ids)} students')
        return redirect('students:mark_attendance')
    
    classes = allowed_classes
    return render(request, 'students/mark_attendance.html', {
        'classes': classes,
        'today': date.today()
    })


@login_required
def get_class_students(request, class_id):
    if request.user.user_type not in ['admin', 'teacher']:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    classes_qs = Class.objects.filter(academic_year__is_current=True)
    class_obj = get_object_or_404(classes_qs, id=class_id)

    if request.user.user_type == 'teacher':
        teacher_profile = Teacher.objects.filter(user=request.user).first()
        allowed = classes_qs.filter(class_teacher=teacher_profile)
        if class_obj not in allowed:
            return JsonResponse({'error': 'Forbidden: You are not the class teacher for this class'}, status=403)

    students = Student.objects.filter(current_class=class_obj).select_related('user')
    
    # Check for date parameter to pre-fill attendance
    date_str = request.GET.get('date')
    attendance_map = {}
    if date_str:
        attendances = Attendance.objects.filter(student__current_class=class_obj, date=date_str)
        attendance_map = {a.student_id: a.status for a in attendances}

    data = [
        {
            'id': s.id,
            'name': s.user.get_full_name(),
            'admission_number': s.admission_number,
            'roll_number': s.roll_number,
            'existing_status': attendance_map.get(s.id) # Will be None if not marked
        }
        for s in students
    ]
    return JsonResponse(data, safe=False)


@login_required
def student_dashboard_view(request):
    """Enhanced student dashboard with grades and attendance"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Check if student profile exists
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('login')
    
    # Get recent attendance (last 10 records)
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:10]
    
    # Calculate attendance stats
    total_attendance = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, status='present').count()
    absent_count = Attendance.objects.filter(student=student, status='absent').count()
    
    attendance_percentage = 0
    if total_attendance > 0:
        attendance_percentage = round((present_count / total_attendance) * 100, 2)
    
    attendance_stats = {
        'present': present_count,
        'absent': absent_count,
        'total': total_attendance,
        'percentage': attendance_percentage
    }
    
    # Get all grades
    grades = Grade.objects.filter(student=student).select_related('subject').order_by('-created_at')
    
    # Get homework and resources
    from homework.models import Homework
    from academics.models import Resource
    
    homework_list = Homework.objects.filter(
        target_class=student.current_class
    ).order_by('-created_at')[:5]

    
    resource_fields_available = False
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cols = [col.name for col in connection.introspection.get_table_description(cursor, Resource._meta.db_table)]
        resource_fields_available = 'resource_type' in cols and 'curriculum' in cols
    except Exception:
        resource_fields_available = False

    resources_qs = Resource.objects.filter(
        Q(class_subject__class_name=student.current_class) |
        Q(target_audience__in=['all', 'students'], class_subject__isnull=True)
    ).order_by('-uploaded_at')
    if not resource_fields_available:
        resources_qs = resources_qs.only('id', 'title', 'description', 'file', 'link', 'target_audience', 'class_subject', 'uploaded_by', 'uploaded_at')
    resources = resources_qs[:8]

    # Get announcements
    from announcements.models import Announcement
    from finance.models import StudentFee
    
    notices = Announcement.objects.filter(
        is_active=True, 
        target_audience__in=['all', 'students']
    ).order_by('-created_at')[:3]

    # Calculate finance stats
    student_fees = StudentFee.objects.filter(student=student)
    total_payable = sum(fee.amount_payable for fee in student_fees)
    total_paid = sum(fee.total_paid for fee in student_fees)
    balance = val = total_payable - total_paid
    
    # Get gamification data
    try:
        student_xp, _ = StudentXP.objects.get_or_create(student=student)
    except Exception:
        student_xp = None

    context = {
        'student': student,
        'gamification': student_xp,
        'recent_attendance': recent_attendance,
        'attendance_stats': attendance_stats,
        'grades': grades,
        'homework_list': homework_list,
        'resources': resources,
        'notices': notices,
        'finance_stats': {
            'payable': total_payable,
            'paid': total_paid,
            'balance': balance
        },
        **build_academic_calendar_widget(),
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)

def _get_student_report_context(student, academic_year, term, raw_term):
    """Helper to generate report card context for a single student"""
    term_values = term_filter_values(term)
    
    # Get all grades for current academic year and term
    grades = Grade.objects.filter(
        student=student,
        academic_year=academic_year,
        term__in=term_values
    ).select_related('subject').order_by('subject__name')
    
    # Calculate statistics
    total_subjects = grades.count()
    
    total_class_work = 0
    total_exams = 0
    grand_total = 0
    
    if grades.exists():
        for grade in grades:
            total_class_work += float(grade.class_score)
            total_exams += float(grade.exams_score)
            grand_total += float(grade.total_score)
        
        average_percentage = grand_total / total_subjects if total_subjects > 0 else 0
    else:
        average_percentage = 0
    
    # Calculate overall grade based on average
    if average_percentage >= 80:
        overall_grade = '1'
        overall_remarks = 'Highest'
    elif average_percentage >= 70:
        overall_grade = '2'
        overall_remarks = 'Higher'
    elif average_percentage >= 65:
        overall_grade = '3'
        overall_remarks = 'High'
    elif average_percentage >= 60:
        overall_grade = '4'
        overall_remarks = 'High Average'
    elif average_percentage >= 55:
        overall_grade = '5'
        overall_remarks = 'Average'
    elif average_percentage >= 50:
        overall_grade = '6'
        overall_remarks = 'Low Average'
    elif average_percentage >= 45:
        overall_grade = '7'
        overall_remarks = 'Low'
    elif average_percentage >= 40:
        overall_grade = '8'
        overall_remarks = 'Lower'
    else:
        overall_grade = '9'
        overall_remarks = 'Lowest'
    
    # Calculate class position
    class_position = calculate_class_position(student, academic_year, term)
    
    # Get attendance stats
    total_attendance = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, status='present').count()
    absent_count = Attendance.objects.filter(student=student, status='absent').count()
    late_count = Attendance.objects.filter(student=student, status='late').count()
    
    attendance_percentage = 0
    if total_attendance > 0:
        attendance_percentage = round((present_count / total_attendance) * 100, 2)
    
    attendance_stats = {
        'present': present_count,
        'absent': absent_count,
        'late': late_count,
        'total': total_attendance,
        'percentage': attendance_percentage
    }
    
    # Get School Info for the header
    from academics.models import SchoolInfo
    school_info = SchoolInfo.objects.first()

    return {
        'student': student,
        'academic_year': academic_year,
        'term': term,
        'term_display': dict(Grade.TERM_CHOICES).get(term, raw_term),
        'grades': grades,
        'total_subjects': total_subjects,
        'total_class_work': total_class_work,
        'total_exams': total_exams,
        'grand_total': grand_total,
        'average_percentage': average_percentage,
        'overall_grade': overall_grade,
        'overall_remarks': overall_remarks,
        'class_position': class_position,
        'attendance_stats': attendance_stats,
        'report_date': date.today(),
        'remarks': '',
        'school_name': school_info.name if school_info else "St. Peter's Methodist Junior High School",
        'school_address': school_info.address if school_info else "P.O. Box 123, Kumasi, Ghana",
        'school_phone': school_info.phone if school_info else "+233 123 456 789",
        'school_email': school_info.email if school_info else "info@spswjh.edu.gh",
        'school_motto': school_info.motto if school_info else "Knowledge is Power",
        'school_logo': school_info.logo if school_info else None,
        'report_card_template': school_info.report_card_template if school_info else 'classic',
        'term_choices': Grade.TERM_CHOICES,
    }


@login_required
def generate_report_card(request, student_id):
    """Generate a printable report card for a student"""
    
    student = get_object_or_404(Student, id=student_id)
    
    # Check permissions (same as before)
    if request.user.user_type == 'student':
        try:
            student_profile = Student.objects.get(user=request.user)
            if student_profile.id != student_id:
                messages.error(request, 'You can only view your own report card')
                return redirect('dashboard')
        except Student.DoesNotExist:
            messages.error(request, 'Student profile not found')
            return redirect('dashboard')
    elif request.user.user_type == 'parent':
        try:
            from parents.models import Parent
            parent = Parent.objects.get(user=request.user)
            if student not in parent.children.all():
                messages.error(request, 'You can only view your children\'s report cards')
                return redirect('parents:my_children')
        except Parent.DoesNotExist:
            messages.error(request, 'Parent profile not found')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Get current academic year
    academic_year = AcademicYear.objects.filter(is_current=True).first()

    # Normalize term value from request
    raw_term = request.GET.get('term', 'first')
    term = normalize_term(raw_term)

    context = _get_student_report_context(student, academic_year, term, raw_term)
    
    return render(request, 'students/report_card.html', context)


@login_required
def generate_report_card_pdf(request, student_id):
    """Download a PDF version of the report card using ReportLab."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    student = get_object_or_404(Student, id=student_id)

    # Permission check (same as generate_report_card)
    if request.user.user_type == 'student':
        sp = get_object_or_404(Student, user=request.user)
        if sp.id != student_id:
            messages.error(request, 'You can only download your own report card')
            return redirect('dashboard')
    elif request.user.user_type == 'parent':
        from parents.models import Parent
        parent = get_object_or_404(Parent, user=request.user)
        if student not in parent.children.all():
            messages.error(request, 'Access denied')
            return redirect('parents:my_children')
    elif request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    academic_year = AcademicYear.objects.filter(is_current=True).first()
    raw_term = request.GET.get('term', 'first')
    term = normalize_term(raw_term)
    ctx = _get_student_report_context(student, academic_year, term, raw_term)

    # ─── Build PDF ────────────────────────────────────────────────────────
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    W, H = A4
    usable_w = W - 3.6*cm

    head_bold   = ParagraphStyle('hb', parent=styles['Heading1'], fontSize=14,
                                  alignment=TA_CENTER, spaceAfter=2)
    sub_style   = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9,
                                  alignment=TA_CENTER, textColor=colors.HexColor('#555555'), spaceAfter=2)
    section_hdr = ParagraphStyle('sh', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor('#1d4ed8'), spaceBefore=10, spaceAfter=4)
    body_sm     = ParagraphStyle('bs', parent=styles['Normal'], fontSize=8.5)
    footer_st   = ParagraphStyle('ft', parent=styles['Normal'], fontSize=7.5,
                                  alignment=TA_CENTER, textColor=colors.HexColor('#888888'))

    GREEN  = colors.HexColor('#059669')
    BLUE   = colors.HexColor('#1d4ed8')
    LIGHT  = colors.HexColor('#eff6ff')
    BORDER = colors.HexColor('#d1d5db')

    story = []

    # Header
    story.append(Paragraph(ctx['school_name'], head_bold))
    story.append(Paragraph(ctx.get('school_address', ''), sub_style))
    story.append(Paragraph(f"Tel: {ctx.get('school_phone','')} | {ctx.get('school_email','')}", sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=8))

    story.append(Paragraph('STUDENT REPORT CARD', ParagraphStyle(
        'rc', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold',
        alignment=TA_CENTER, textColor=BLUE, spaceAfter=6)))

    # Student info table
    yr_display = str(ctx['academic_year']) if ctx['academic_year'] else 'N/A'
    info_data = [
        ['Student Name:', ctx['student'].user.get_full_name(),
         'Term:', ctx.get('term_display', ctx['term'])],
        ['Class:', ctx['student'].current_class.name if ctx['student'].current_class else 'N/A',
         'Academic Year:', yr_display],
        ['Student ID:', str(ctx['student'].id),
         'Class Position:', str(ctx.get('class_position', 'N/A'))],
    ]
    info_table = Table(info_data, colWidths=[3.2*cm, 6*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,-1), LIGHT),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    # Grades table
    story.append(Paragraph('Academic Performance', section_hdr))
    grade_header = ['Subject', 'Class Score\n(/30)', 'Exams\n(/70)', 'Total\n(/100)', 'Grade', 'Remarks']
    grade_rows = [grade_header]
    for g in ctx['grades']:
        grade_rows.append([
            g.subject.name,
            f"{g.class_score:.1f}",
            f"{g.exams_score:.1f}",
            f"{g.total_score:.1f}",
            g.grade or '-',
            g.remarks or '-',
        ])
    # Totals row
    grade_rows.append([
        'TOTALS',
        f"{ctx['total_class_work']:.1f}",
        f"{ctx['total_exams']:.1f}",
        f"{ctx['grand_total']:.1f}",
        ctx['overall_grade'],
        ctx['overall_remarks'],
    ])

    col_widths = [5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2.2*cm]
    grade_table = Table(grade_rows, colWidths=col_widths, repeatRows=1)
    grade_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (0,-1), (-1,-1), LIGHT),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(grade_table)
    story.append(Spacer(1, 8))

    # Summary + attendance side by side
    att = ctx['attendance_stats']
    summary_data = [
        ['Average Score:', f"{ctx['average_percentage']:.1f}%", 'Days Present:', str(att['present'])],
        ['Overall Grade:', ctx['overall_grade'], 'Days Absent:', str(att['absent'])],
        ['Overall Remarks:', ctx['overall_remarks'], 'Attendance:', f"{att['percentage']:.1f}%"],
    ]
    summary_table = Table(summary_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5.2*cm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER),
        ('BACKGROUND', (0,0), (-1,-1), LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(Paragraph('Summary', section_hdr))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Footer
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph(
        f"Generated on {ctx['report_date'].strftime('%B %d, %Y')} | {ctx['school_name']} | "
        f"Motto: {ctx.get('school_motto', '')}",
        footer_st))

    doc.build(story)
    buf.seek(0)
    fname = f"report_card_{ctx['student'].user.last_name}_{ctx.get('term', 'term')}.pdf".replace(' ', '_')
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response


@login_required
def bulk_report_cards(request):
    """Generate bulk report cards for printing"""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    student_ids = request.GET.get('ids', '').split(',')
    student_ids = [sid for sid in student_ids if sid.strip()]
    
    if not student_ids:
        messages.error(request, 'No students selected')
        return redirect('students:student_list')
        
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    raw_term = request.GET.get('term', 'first')
    term = normalize_term(raw_term)
    
    students = Student.objects.filter(id__in=student_ids).select_related('user', 'current_class')
    
    reports = []
    for student in students:
        report_data = _get_student_report_context(student, academic_year, term, raw_term)
        reports.append(report_data)
        
    return render(request, 'students/bulk_report_cards.html', {'reports': reports})


@login_required
def student_schedule(request):
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    if not student.current_class:
        messages.warning(request, 'You are not assigned to any class.')
        return render(request, 'students/schedule.html', {'days': []})

    # Get all schedule entries for this student's class
    timetable_qs = Timetable.objects.filter(
        class_subject__class_name=student.current_class
    ).select_related(
        'class_subject', 'class_subject__teacher', 'class_subject__teacher__user', 
        'class_subject__subject'
    ).order_by('day', 'start_time')
    
    days_data = []
    for code, name in Timetable.DAY_CHOICES:
        entries = [t for t in timetable_qs if t.day == code]
        days_data.append({
            'name': name,
            'entries': entries
        })
            
    return render(request, 'students/schedule.html', {'days': days_data, 'student_class': student.current_class})

@login_required
def add_student(request):
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            admission_number = form.cleaned_data['admission_number']
            if not admission_number:
                # Auto-generate Admission Number (ADM + 4 Digits)
                import random
                import string
                while True:
                    suffix = ''.join(random.choices(string.digits, k=4))
                    admission_number = f"ADM{suffix}"
                    if not Student.objects.filter(admission_number=admission_number).exists() and not User.objects.filter(username=admission_number).exists():
                        break
            
            username = admission_number
            if User.objects.filter(username=username).exists():
                messages.error(request, f"User {username} already exists")
                return render(request, 'students/add_student.html', {'form': form})
                
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=username,  # Default password is admission number
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                user_type='student'
            )
            
            student = form.save(commit=False)
            student.user = user
            student.admission_number = admission_number # Ensure it's set
            student.save()
            messages.success(request, f"Student {user.get_full_name()} added successfully with Admission No: {admission_number}")
            return redirect('students:student_list')
    else:
        form = StudentForm()
        
    return render(request, 'students/add_student.html', {'form': form})


@login_required
def edit_student(request, student_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            # Update user fields
            student.user.first_name = form.cleaned_data['first_name']
            student.user.last_name = form.cleaned_data['last_name']
            student.user.email = form.cleaned_data['email']
            if 'profile_picture' in form.cleaned_data:
                student.user.profile_picture = form.cleaned_data['profile_picture']
            student.user.save()
            
            form.save()
            messages.success(request, f'Student {student.user.get_full_name()} updated successfully.')
            return redirect('students:student_list')
    else:
        # Populate form with user data
        initial_data = {
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'profile_picture': student.user.profile_picture,
        }
        form = StudentForm(instance=student, initial=initial_data)
        
    return render(request, 'students/edit_student.html', {'form': form, 'student': student})


@login_required
def import_students_csv(request):
    """Import students from CSV file"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can import students.')
        return redirect('students:student_list')
    
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            default_class = form.cleaned_data.get('default_class')
            
            # Validate file extension
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('students:import_csv')
            
            # Read and process CSV
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                imported_count = 0
                skipped_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Handle both naming conventions: "First Name" or "first_name"
                        first_name = (row.get('First Name') or row.get('first_name') or '').strip()
                        last_name = (row.get('Last Name') or row.get('last_name') or '').strip()
                        admission_no = (row.get('Admission No') or row.get('admission_number') or row.get('admission_no') or '').strip()
                        class_name = (row.get('Class') or row.get('class_name') or row.get('class') or '').strip()
                        roll_no = (row.get('Roll No') or row.get('roll_no') or row.get('roll_number') or '').strip()
                        email = (row.get('Email') or row.get('email') or '').strip()
                        emergency_contact = (row.get('Emergency Contact') or row.get('emergency_contact') or '').strip()
                        age = (row.get('age') or row.get('Age') or '').strip()
                        
                        if not first_name:
                            errors.append(f"Row {row_num}: Missing first name")
                            skipped_count += 1
                            continue
                        
                        # Last name is optional - some students might only have first name
                        if not last_name:
                            last_name = ''
                        
                        # Determine class
                        student_class = None
                        if class_name:
                            try:
                                student_class = Class.objects.get(name__iexact=class_name)
                            except Class.DoesNotExist:
                                errors.append(f"Row {row_num}: Class '{class_name}' not found")
                        
                        if not student_class:
                            student_class = default_class
                        
                        if not student_class:
                            errors.append(f"Row {row_num}: No class specified and no default class selected")
                            skipped_count += 1
                            continue
                        
                        # Parse age
                        try:
                            student_age = int(age) if age else 10
                        except ValueError:
                            student_age = 10
                        
                        # Generate username
                        if last_name:
                            base_username = f"{first_name.lower()}.{last_name.lower()}"
                        else:
                            base_username = first_name.lower()
                        username = base_username.replace(' ', '').replace('-', '')
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username.replace(' ', '').replace('-', '')}{counter}"
                            counter += 1
                        
                        # Use provided admission number or generate one
                        admission_number = None
                        if admission_no and admission_no.upper() not in ['N/A', 'NA', '']:
                            # Clean up admission number
                            admission_number = admission_no.strip().replace(' ', '')
                            # Check if it already exists
                            if Student.objects.filter(admission_number=admission_number).exists():
                                errors.append(f"Row {row_num}: Admission number '{admission_number}' already exists")
                                skipped_count += 1
                                continue
                        else:
                            # Generate admission number
                            prefix = 'ADM'
                            for _ in range(100):  # Try up to 100 times
                                suffix = ''.join(random.choices(string.digits, k=4))
                                candidate = f"{prefix}{suffix}"
                                if not Student.objects.filter(admission_number=candidate).exists():
                                    admission_number = candidate
                                    break
                        
                        if not admission_number:
                            errors.append(f"Row {row_num}: Could not generate unique admission number")
                            skipped_count += 1
                            continue
                        
                        # Prepare email
                        if not email or email.upper() in ['N/A', 'NA', '']:
                            email = f"{username}@school.local"
                        
                        # Check if user with this email already exists
                        if User.objects.filter(email=email).exists():
                            email = f"{username}{random.randint(1, 999)}@school.local"
                        
                        # Prepare emergency contact
                        if not emergency_contact or emergency_contact.upper() in ['N/A', 'NA', '']:
                            emergency_contact = 'N/A'
                        
                        # Create user
                        user = User.objects.create(
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            user_type='student'
                        )
                        user.set_unusable_password()
                        user.save()
                        
                        # Calculate date of birth
                        dob_year = max(1900, date.today().year - student_age)
                        date_of_birth = date(dob_year, 1, 1)
                        
                        # Create student
                        student = Student.objects.create(
                            user=user,
                            admission_number=admission_number,
                            date_of_birth=date_of_birth,
                            gender='male',  # Default, can be updated later
                            date_of_admission=date.today(),
                            current_class=student_class,
                            emergency_contact=emergency_contact
                        )
                        
                        # Set roll number if provided
                        if roll_no and roll_no.upper() not in ['N/A', 'NA', '']:
                            try:
                                student.roll_number = int(roll_no)
                                student.save()
                            except (ValueError, AttributeError):
                                pass  # Skip if roll number is invalid or field doesn't exist
                        
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        skipped_count += 1
                        continue
                
                # Show results
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} student(s).')
                
                if skipped_count > 0:
                    messages.warning(request, f'Skipped {skipped_count} row(s) due to errors.')
                
                if errors and len(errors) <= 10:
                    for error in errors:
                        messages.error(request, error)
                elif errors:
                    messages.error(request, f'{len(errors)} errors occurred. First 10: {", ".join(errors[:10])}')
                
                return redirect('students:student_list')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
                return redirect('students:import_csv')
    else:
        form = CSVImportForm()
    
    return render(request, 'students/import_csv.html', {'form': form})


# =====================
# ID CARD GENERATION
# =====================

@login_required
def student_id_card(request, student_id):
    """Generate and download student ID card (PNG)"""
    student = get_object_or_404(Student, id=student_id)
    
    # Permission check
    if request.user.user_type == 'student':
        student_profile = get_object_or_404(Student, user=request.user)
        if student_profile.id != student_id:
            messages.error(request, 'You can only download your own ID card')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Generate card
    try:
        card = generate_student_id_card(student)
        
        # Return as PNG
        response = HttpResponse(content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="student_id_{student.id}.png"'
        card.save(response, 'PNG')
        return response
    except Exception as e:
        messages.error(request, f'Error generating ID card: {str(e)}')
        return redirect('dashboard')


@login_required
def student_id_card_pdf(request, student_id):
    """Generate and download student ID card (PDF)"""
    student = get_object_or_404(Student, id=student_id)
    
    # Permission check
    if request.user.user_type == 'student':
        student_profile = get_object_or_404(Student, user=request.user)
        if student_profile.id != student_id:
            messages.error(request, 'You can only download your own ID card')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Generate card and convert to PDF
    try:
        card = generate_student_id_card(student)
        pdf_buffer = export_id_card_to_pdf(card)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="student_id_{student.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating ID card: {str(e)}')
        return redirect('dashboard')


@login_required
def bulk_student_id_cards_pdf(request):
    """Generate bulk ID cards for a class (PDF)"""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Get parameters
    class_id = request.GET.get('class_id')
    student_ids = request.GET.get('ids', '').split(',')
    student_ids = [sid.strip() for sid in student_ids if sid.strip()]
    
    try:
        if class_id:
            students = Student.objects.filter(current_class_id=class_id).order_by('user__last_name')
        elif student_ids:
            students = Student.objects.filter(id__in=student_ids)
        else:
            messages.error(request, 'Please select a class or students')
            return redirect('students:student_list')
        
        if not students.exists():
            messages.error(request, 'No students found')
            return redirect('students:student_list')
        
        # Generate cards
        card_list = []
        for student in students:
            try:
                card = generate_student_id_card(student)
                card_list.append((student.user.get_full_name(), card))
            except Exception:
                pass  # Skip students with errors
        
        if not card_list:
            messages.error(request, 'Could not generate any ID cards')
            return redirect('students:student_list')
        
        # Export to PDF
        pdf_buffer = export_multiple_id_cards_to_pdf(card_list)
        
        class_name = students.first().current_class.name if class_id else 'bulk'
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="student_ids_{class_name}.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating ID cards: {str(e)}')
        return redirect('students:student_list')

@login_required
def update_aura_preferences(request):
    """Student self-service endpoint to update preferred language and interests."""
    if request.user.user_type != 'student':
        return JsonResponse({'success': False, 'message': 'Access denied.'}, status=403)

    student = Student.objects.filter(user=request.user).first()
    if not student:
        return JsonResponse({'success': False, 'message': 'Student profile not found.'}, status=404)

    if request.method == 'POST':
        form = AuraPreferencesForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            lang_display = dict(student._meta.get_field('preferred_language').choices).get(
                form.cleaned_data['preferred_language'], form.cleaned_data['preferred_language']
            )
            return JsonResponse({
                'success': True,
                'message': f'Aura preferences updated. Language set to {lang_display}.',
            })
        return JsonResponse({'success': False, 'message': 'Invalid data.', 'errors': form.errors}, status=400)

    return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)


@login_required
def student_power_words(request):
    """
    Student-facing Power Words history page.
    Shows lifetime word cloud, weekly progress, subject breakdown and recent log.
    """
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from collections import defaultdict
    from academics.tutor_models import PowerWord
    from django.utils import timezone as tz

    student = Student.objects.filter(user=request.user).select_related('user').first()
    if not student:
        messages.error(request, 'Student profile not found.')
        return redirect('login')

    ACADEMIC_VERBS = {
        'analyze', 'analyse', 'compare', 'evaluate', 'synthesize', 'synthesise',
        'describe', 'explain', 'justify', 'identify', 'classify', 'predict',
        'infer', 'conclude', 'hypothesize', 'hypothesise', 'illustrate',
        'summarize', 'summarise', 'argue', 'debate', 'interpret', 'calculate',
        'demonstrate', 'apply', 'construct', 'define', 'distinguish',
    }

    now = tz.now()
    iso = now.isocalendar()
    current_year, current_week = iso[0], iso[1]
    last_week = current_week - 1 if current_week > 1 else 52
    last_week_year = current_year if current_week > 1 else current_year - 1

    # All power words, newest first
    all_words = list(
        PowerWord.objects.filter(student=student).order_by('-last_heard')
    )

    # ── Headline stats ────────────────────────────────────────
    total_unique = len(all_words)
    total_uses   = sum(w.used_count for w in all_words)
    this_week_words = [w for w in all_words if w.year == current_year and w.week == current_week]
    last_week_words = [w for w in all_words if w.year == last_week_year and w.week == last_week]
    new_this_week = len(this_week_words)

    total_verbs = sum(1 for w in all_words if w.word.lower() in ACADEMIC_VERBS)
    verb_pct = round(total_verbs / total_unique * 100) if total_unique else 0

    voice_count = sum(1 for w in all_words if w.session_type == 'voice')
    text_count  = total_unique - voice_count

    # Week-on-week delta
    week_delta = new_this_week - len(last_week_words)

    # ── Word cloud (top 50 by used_count) ─────────────────────
    sorted_cloud = sorted(all_words, key=lambda w: -w.used_count)[:50]
    max_count = sorted_cloud[0].used_count if sorted_cloud else 1
    word_cloud = [
        {
            'word': w.word.title(),
            'used_count': w.used_count,
            'subject': w.subject,
            'font_size': max(13, min(36, int(13 + (w.used_count / max_count) * 23))),
            'is_verb': w.word.lower() in ACADEMIC_VERBS,
            'session_type': w.session_type,
        }
        for w in sorted_cloud
    ]

    # ── Weekly history (last 10 weeks) ─────────────────────────
    by_week = defaultdict(list)
    for w in all_words:
        by_week[(w.year, w.week)].append(w)

    # Build sorted list of weeks (most recent first)
    week_keys_sorted = sorted(by_week.keys(), reverse=True)[:10]
    weekly_history = []
    for (yr, wk) in week_keys_sorted:
        wlist = by_week[(yr, wk)]
        weekly_history.append({
            'year': yr,
            'week': wk,
            'count': len(wlist),
            'is_current': (yr == current_year and wk == current_week),
            'sample': ', '.join(w.word.title() for w in wlist[:4]),
        })

    # ── Subject breakdown ──────────────────────────────────────
    by_subject = defaultdict(int)
    for w in all_words:
        subj = w.subject.strip() if w.subject else 'General'
        by_subject[subj] += 1

    subject_breakdown = sorted(
        [{'subject': s, 'count': c} for s, c in by_subject.items()],
        key=lambda x: -x['count']
    )[:8]

    # ── Recent 20 words ────────────────────────────────────────
    recent_words = [
        {
            'word': w.word.title(),
            'subject': w.subject or '—',
            'session_type': w.get_session_type_display(),
            'is_verb': w.word.lower() in ACADEMIC_VERBS,
            'confirmed': w.confirmed_by_teacher,
            'week': w.week,
            'year': w.year,
            'last_heard': w.last_heard,
        }
        for w in all_words[:20]
    ]

    context = {
        'student': student,
        'total_unique': total_unique,
        'total_uses': total_uses,
        'new_this_week': new_this_week,
        'week_delta': week_delta,
        'verb_pct': verb_pct,
        'voice_count': voice_count,
        'text_count': text_count,
        'current_week': current_week,
        'current_year': current_year,
        'word_cloud': word_cloud,
        'weekly_history': weekly_history,
        'weekly_max': max((w['count'] for w in weekly_history), default=1),
        'subject_breakdown': subject_breakdown,
        'recent_words': recent_words,
    }
    return render(request, 'students/power_words_history.html', context)


# ---------------------------------------------------------------------------
# XP Leaderboard API (JSON)
# ---------------------------------------------------------------------------

@login_required
def class_leaderboard_json(request):
    """
    Returns top-20 classmates ranked by Aura XP for the logged-in student.
    The student's own entry is included and marked with `is_me: true`.
    """
    from academics.gamification_models import StudentXP
    from django.http import JsonResponse

    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    student = Student.objects.filter(user=request.user).select_related('current_class').first()
    if not student or not student.current_class:
        return JsonResponse({'leaderboard': [], 'my_rank': None})

    # All classmates including self
    classmates = Student.objects.filter(
        current_class=student.current_class
    ).select_related('user')

    # Fetch XP records; default to 0 if missing
    xp_map = {
        xp.student_id: xp
        for xp in StudentXP.objects.filter(student__in=classmates)
    }

    rows = []
    for s in classmates:
        xp = xp_map.get(s.id)
        rows.append({
            'id': s.id,
            'name': s.user.get_full_name() or s.user.username,
            'total_xp': xp.total_xp if xp else 0,
            'level': xp.level if xp else 1,
            'level_progress': xp.level_progress if xp else 0,
            'current_streak': xp.current_streak if xp else 0,
            'is_me': s.id == student.id,
        })

    # Sort by XP descending
    rows.sort(key=lambda r: r['total_xp'], reverse=True)

    # Assign ranks (tied XP shares the same rank)
    my_rank = None
    current_rank = 0
    prev_xp = None
    for i, row in enumerate(rows):
        if row['total_xp'] != prev_xp:
            current_rank = i + 1
            prev_xp = row['total_xp']
        row['rank'] = current_rank
        if row['is_me']:
            my_rank = current_rank

    # Return top 20; always include the user's own entry if outside top 20
    top20 = rows[:20]
    me_in_top20 = any(r['is_me'] for r in top20)
    if not me_in_top20:
        me_row = next((r for r in rows if r['is_me']), None)
        if me_row:
            top20.append(me_row)

    return JsonResponse({'leaderboard': top20, 'my_rank': my_rank})


# ─────────────────────────────────────────────────────────────────────────────
# GRADEBOOK CSV IMPORT / EXPORT
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def export_grades_csv(request):
    """Export grades for a class + term as a downloadable CSV file."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    class_id = request.GET.get('class_id')
    raw_term  = request.GET.get('term', 'first')
    year_id   = request.GET.get('year_id')

    # Resolve academic year
    if year_id:
        academic_year = AcademicYear.objects.filter(id=year_id).first()
    else:
        academic_year = AcademicYear.objects.filter(is_current=True).first()

    if not academic_year:
        messages.error(request, 'No academic year found')
        return redirect('students:student_list')

    term = normalize_term(raw_term)

    # Build queryset
    qs = Grade.objects.select_related(
        'student__user', 'subject'
    ).filter(academic_year=academic_year)

    # Optional term filter
    if term:
        term_values = term_filter_values(term)
        qs = qs.filter(term__in=term_values)

    if class_id:
        qs = qs.filter(student__current_class_id=class_id)
        cls = Class.objects.filter(id=class_id).first()
        cls_name = cls.name if cls else 'all'
    else:
        cls_name = 'all'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="grades_{cls_name}_{raw_term}_{academic_year.name}.csv"'
        .replace(' ', '_')
    )

    writer = csv.writer(response)
    writer.writerow([
        'Admission No.', 'Student Name', 'Subject', 'Term',
        'Class Score (/30)', 'Exam Score (/70)', 'Total (/100)', 'Grade', 'Remarks',
    ])

    for g in qs.order_by('student__user__last_name', 'subject__name'):
        writer.writerow([
            g.student.admission_number,
            g.student.user.get_full_name(),
            g.subject.name,
            g.term,
            g.class_score,
            g.exams_score,
            g.total_score,
            g.grade or '',
            g.remarks or '',
        ])

    return response


@login_required
def import_grades_csv(request):
    """Upload a CSV file to bulk-create or update Grade records."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    academic_year = AcademicYear.objects.filter(is_current=True).first()
    classes       = Class.objects.filter(academic_year=academic_year).order_by('name')

    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file')
            return redirect('students:import_grades_csv')

        decoded = csv_file.read().decode('utf-8').splitlines()
        reader  = csv.DictReader(decoded)

        created = updated = skipped = 0
        errors  = []

        from academics.models import Subject

        for row_num, row in enumerate(reader, start=2):
            try:
                admission_no = (
                    row.get('Admission No.') or row.get('Admission No') or
                    row.get('admission_number') or ''
                ).strip()
                subject_name = (row.get('Subject') or row.get('subject') or '').strip()
                raw_term     = (row.get('Term')    or row.get('term')    or 'first').strip().lower()
                class_score_raw = (row.get('Class Score (/30)') or row.get('class_score') or '0').strip()
                exam_score_raw  = (row.get('Exam Score (/70)')  or row.get('exams_score') or '0').strip()

                if not admission_no or not subject_name:
                    errors.append(f'Row {row_num}: Missing admission number or subject name — skipped')
                    skipped += 1
                    continue

                student = Student.objects.filter(admission_number=admission_no).first()
                if not student:
                    errors.append(f'Row {row_num}: Student "{admission_no}" not found — skipped')
                    skipped += 1
                    continue

                subject = Subject.objects.filter(name__iexact=subject_name).first()
                if not subject:
                    errors.append(f'Row {row_num}: Subject "{subject_name}" not found — skipped')
                    skipped += 1
                    continue

                term = normalize_term(raw_term) or 'first'

                grade_obj, was_created = Grade.objects.get_or_create(
                    student=student,
                    subject=subject,
                    academic_year=academic_year,
                    term=term,
                )
                grade_obj.class_score  = float(class_score_raw)
                grade_obj.exams_score  = float(exam_score_raw)
                grade_obj.save()   # triggers auto-calc of total_score, grade, remarks

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as exc:
                errors.append(f'Row {row_num}: {exc}')
                skipped += 1

        summary = f'Import complete — {created} created, {updated} updated, {skipped} skipped.'
        if errors:
            summary += f' First error: {errors[0]}'
        messages.success(request, summary)
        return redirect('students:import_grades_csv')

    return render(request, 'students/import_grades.html', {
        'academic_year': academic_year,
        'classes': classes,
    })


# ─────────────────────────────────────────────────────────────────────────────
# BULK REPORT CARD ZIP  (all students in a class → one ZIP of PDFs)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def bulk_report_cards_zip(request, class_id):
    """Generate PDF report cards for every student in a class and return them as a ZIP."""
    import zipfile
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    cls = get_object_or_404(Class, id=class_id)
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    raw_term = request.GET.get('term', 'first')
    term     = normalize_term(raw_term)

    students = Student.objects.filter(current_class=cls).select_related('user', 'current_class')
    if not students.exists():
        messages.warning(request, f'No students found in {cls.name}')
        return redirect('students:student_list')

    def _build_pdf_bytes(student):
        ctx = _get_student_report_context(student, academic_year, term, raw_term)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=1.8*cm, rightMargin=1.8*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        W, H = A4

        head_bold   = ParagraphStyle('hb', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=2)
        sub_style   = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER,
                                     textColor=colors.HexColor('#555555'), spaceAfter=2)
        section_hdr = ParagraphStyle('sh', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold',
                                     textColor=colors.HexColor('#1d4ed8'), spaceBefore=10, spaceAfter=4)
        footer_st   = ParagraphStyle('ft', parent=styles['Normal'], fontSize=7.5,
                                     alignment=TA_CENTER, textColor=colors.HexColor('#888888'))

        BLUE   = colors.HexColor('#1d4ed8')
        LIGHT  = colors.HexColor('#eff6ff')
        BORDER = colors.HexColor('#d1d5db')

        story = []
        story.append(Paragraph(ctx['school_name'], head_bold))
        story.append(Paragraph(ctx.get('school_address', ''), sub_style))
        story.append(Paragraph(f"Tel: {ctx.get('school_phone','')} | {ctx.get('school_email','')}", sub_style))
        story.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=8))
        story.append(Paragraph('STUDENT REPORT CARD', ParagraphStyle(
            'rc', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold',
            alignment=TA_CENTER, textColor=BLUE, spaceAfter=6)))

        yr_display = str(ctx['academic_year']) if ctx['academic_year'] else 'N/A'
        info_data = [
            ['Student Name:', ctx['student'].user.get_full_name(), 'Term:', ctx.get('term_display', ctx['term'])],
            ['Class:', ctx['student'].current_class.name if ctx['student'].current_class else 'N/A', 'Academic Year:', yr_display],
            ['Student ID:', str(ctx['student'].id), 'Class Position:', str(ctx.get('class_position', 'N/A'))],
        ]
        info_table = Table(info_data, colWidths=[3.2*cm, 6*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,-1), LIGHT),
            ('GRID', (0,0), (-1,-1), 0.4, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8))

        story.append(Paragraph('Academic Performance', section_hdr))
        grade_header = ['Subject', 'Class\n(/30)', 'Exams\n(/70)', 'Total\n(/100)', 'Grade', 'Remarks']
        grade_rows = [grade_header]
        for g in ctx['grades']:
            grade_rows.append([
                g.subject.name, f"{g.class_score:.1f}",
                f"{g.exams_score:.1f}", f"{g.total_score:.1f}",
                g.grade or '-', g.remarks or '-',
            ])
        grade_rows.append([
            'TOTALS', f"{ctx['total_class_work']:.1f}", f"{ctx['total_exams']:.1f}",
            f"{ctx['grand_total']:.1f}", ctx['overall_grade'], ctx['overall_remarks'],
        ])
        grade_table = Table(grade_rows, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2.2*cm], repeatRows=1)
        grade_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BACKGROUND', (0,-1), (-1,-1), LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.4, BORDER),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(grade_table)
        story.append(Spacer(1, 8))

        att = ctx['attendance_stats']
        summary_data = [
            ['Average Score:', f"{ctx['average_percentage']:.1f}%", 'Days Present:', str(att['present'])],
            ['Overall Grade:', ctx['overall_grade'], 'Days Absent:', str(att['absent'])],
            ['Overall Remarks:', ctx['overall_remarks'], 'Attendance:', f"{att['percentage']:.1f}%"],
        ]
        summary_table = Table(summary_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5.2*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.4, BORDER),
            ('BACKGROUND', (0,0), (-1,-1), LIGHT),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(Paragraph('Summary', section_hdr))
        story.append(summary_table)
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=4))
        story.append(Paragraph(
            f"Generated on {ctx['report_date'].strftime('%B %d, %Y')} | {ctx['school_name']}",
            footer_st))

        doc.build(story)
        buf.seek(0)
        return buf.read()

    # Build ZIP in memory
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for student in students:
            try:
                pdf_bytes = _build_pdf_bytes(student)
                filename  = f"report_{student.user.last_name}_{student.user.first_name}_{raw_term}.pdf".replace(' ', '_')
                zf.writestr(filename, pdf_bytes)
            except Exception:
                pass  # skip one bad student rather than aborting the whole ZIP

    zip_buf.seek(0)
    zip_name = f"report_cards_{cls.name}_{raw_term}.zip".replace(' ', '_')
    response = HttpResponse(zip_buf, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
    return response


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT PROMOTION / YEAR-END ROLLOVER
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def promote_students(request):
    """Admin tool — bulk-promote students from their current class to a target class."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('dashboard')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    all_classes  = Class.objects.filter(academic_year=current_year).order_by('name')

    if request.method == 'POST':
        promoted_total = 0
        errors = []

        source_class_ids = request.POST.getlist('source_class_ids')
        for src_id in source_class_ids:
            target_id = request.POST.get(f'target_{src_id}')
            if not target_id:
                continue
            src_cls = Class.objects.filter(id=src_id).first()
            tgt_cls = Class.objects.filter(id=target_id).first()
            if not src_cls or not tgt_cls:
                errors.append(f'Class id {src_id}/{target_id} not found')
                continue
            if src_cls == tgt_cls:
                continue

            count = Student.objects.filter(current_class=src_cls).update(current_class=tgt_cls)
            promoted_total += count

        if promoted_total:
            msg = f'Successfully promoted {promoted_total} student(s).'
            if errors:
                msg += f' Some errors: {"; ".join(errors[:3])}'
            messages.success(request, msg)
        else:
            messages.warning(request, 'No students were promoted. Check your class selections.')

        return redirect('students:promote_students')

    return render(request, 'students/promote_students.html', {
        'current_year': current_year,
        'all_classes': all_classes,
    })
