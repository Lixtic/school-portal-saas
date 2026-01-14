from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg
from datetime import date, timedelta
import csv
from .models import Student, Attendance, Grade
from .forms import StudentForm
from accounts.models import User

from .utils import calculate_class_position, normalize_term, term_filter_values
from academics.models import Class, AcademicYear, Timetable
from teachers.models import Teacher

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
def bulk_assign_class(request):
    """Bulk assign students to a class"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        class_id = data.get('class_id')
        
        if not student_ids or not class_id:
            return JsonResponse({'error': 'Missing data'}, status=400)
        
        class_obj = get_object_or_404(Class, id=class_id)
        Student.objects.filter(id__in=student_ids).update(current_class=class_obj)
        
        return JsonResponse({
            'message': f'{len(student_ids)} students assigned to {class_obj.name}'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


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
    from teachers.models import LessonPlan
    from academics.models import Resource, ClassSubject
    
    homework_list = LessonPlan.objects.filter(
        school_class=student.current_class
    ).exclude(homework='').order_by('-week_number', '-date_added')[:5]
    
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
    
    context = {
        'student': student,
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
        }
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

