from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import Q, Count, Sum, Avg
from django.db.utils import OperationalError, ProgrammingError
import django
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from decimal import Decimal, InvalidOperation
from django.utils import timezone
import os
import csv
import random
import string
from datetime import date
from teachers.models import Teacher, DutyWeek, LessonPlan
from academics.models import ClassSubject, AcademicYear, Timetable, SchoolInfo, Resource, Class, Subject, SchemeOfWork
from students.models import Student, Grade, ClassExercise, StudentExerciseScore
from students.utils import normalize_term
from .forms import ResourceForm, LessonPlanForm, TeacherCreateForm, TeacherCSVImportForm #, HomeworkForm
from .models import LessonGenerationSession
from accounts.models import User
from academics.tutor_models import generate_teacher_id_card, export_id_card_to_pdf, export_multiple_id_cards_to_pdf, TutorSession, TutorMessage
from parents.models import Parent
from communication.models import Conversation, Message
from django.views.decorators.http import require_POST
# from parents.models import Homework


def _classify_ai_error(exception):
    raw_message = str(exception or '').strip()
    message_lower = raw_message.lower()

    if (
        'insufficient_quota' in message_lower
        or 'openai http 429' in message_lower
        or ('quota' in message_lower and 'openai' in message_lower)
    ):
        return {
            'error_code': 'ai_quota_exceeded',
            'message': 'Aura AI is temporarily unavailable because the OpenAI quota is exhausted. Please top up billing and try again.',
            'http_status': 503,
            'retryable': False,
        }

    if (
        'api key' in message_lower
        or 'missing openai_api_key' in message_lower
        or 'not configured' in message_lower
    ):
        return {
            'error_code': 'ai_not_configured',
            'message': 'Aura AI is currently unavailable due to configuration. Please contact your administrator.',
            'http_status': 503,
            'retryable': False,
        }

    if 'network error' in message_lower or 'timed out' in message_lower:
        return {
            'error_code': 'ai_network_error',
            'message': 'Aura AI is temporarily unreachable. Please check your connection and try again shortly.',
            'http_status': 503,
            'retryable': True,
        }

    if 'openai http 5' in message_lower:
        return {
            'error_code': 'ai_upstream_error',
            'message': 'Aura AI service is temporarily unavailable. Please try again shortly.',
            'http_status': 503,
            'retryable': True,
        }

    return {
        'error_code': 'ai_generation_failed',
        'message': raw_message or 'Aura AI could not complete this request right now.',
        'http_status': 500,
        'retryable': True,
    }


def _ai_json_error_response(exception):
    error_info = _classify_ai_error(exception)
    return JsonResponse(
        {
            'status': 'error',
            'message': error_info['message'],
            'error_code': error_info['error_code'],
            'retryable': error_info['retryable'],
        },
        status=error_info['http_status'],
    )


# Homework views moved to 'homework' app

@login_required
def teacher_ai_insights(request):
    """Dashboard for teachers to view AI Tutor usage and common student questions"""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Filter sessions - show all for admin, show relevant classes for teacher
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    sessions_qs = TutorSession.objects.select_related('student', 'student__user', 'student__current_class', 'subject')
    
    if request.user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
        # Get classes taught by teacher
        teacher_classes = ClassSubject.objects.filter(teacher=teacher, class_name__academic_year=current_year).values_list('class_name', flat=True)
        # Also managed classes
        managed_classes = Class.objects.filter(class_teacher=teacher, academic_year=current_year).values_list('id', flat=True)
        
        relevant_class_ids = set(list(teacher_classes) + list(managed_classes))
        sessions_qs = sessions_qs.filter(student__current_class__id__in=relevant_class_ids)

    # 1. Total Stats
    total_sessions = sessions_qs.count()
    if total_sessions == 0:
         return render(request, 'teachers/ai_insights.html', {'no_data': True})

    active_students_count = sessions_qs.values('student').distinct().count()
    avg_msgs_per_session = sessions_qs.aggregate(avg=Avg('message_count'))['avg'] or 0

    # 2. Most Active Students
    top_students = sessions_qs.values(
        'student__user__first_name', 'student__user__last_name', 'student__current_class__name'
    ).annotate(
        session_count=Count('id'),
        total_msgs=Sum('message_count')
    ).order_by('-session_count')[:5]

    # 3. Common Topics (Flatten topics_discussed)
    # This is slightly complex with JSONField in older Django, but simple in Python
    # Since JSONField query support varies, Python processing for top topics is acceptable for small scale
    recent_sessions = sessions_qs.order_by('-started_at')[:50]
    all_topics = []
    for s in recent_sessions:
        if isinstance(s.topics_discussed, list):
            all_topics.extend([str(t).lower().strip() for t in s.topics_discussed if t])
    
    from collections import Counter
    topic_counts = Counter(all_topics).most_common(8)

    # 4. Recent Activity Feed
    recent_activity = sessions_qs.order_by('-started_at')[:10]

    # 5. Scheme Progress: cross-reference session topics against SchemeOfWork topics
    scheme_progress = []
    try:
        if request.user.user_type == 'teacher':
            teacher_schemes = SchemeOfWork.objects.filter(
                class_subject__teacher=teacher,
                class_subject__class_name__academic_year=current_year,
            ).select_related('class_subject__subject', 'class_subject__class_name')
        else:
            teacher_schemes = SchemeOfWork.objects.filter(
                academic_year=current_year,
            ).select_related('class_subject__subject', 'class_subject__class_name')[:20]

        all_session_content = set()
        for s in recent_sessions:
            if s.title:
                all_session_content.add(s.title.lower())
            if isinstance(s.topics_discussed, list):
                for t in s.topics_discussed:
                    all_session_content.add(str(t).lower())

        for scheme in teacher_schemes:
            topics = scheme.get_topics()
            if not topics:
                continue
            covered = sum(
                1 for t in topics
                if any(t.lower() in content or content in t.lower() for content in all_session_content)
            )
            scheme_progress.append({
                'scheme': scheme,
                'topics': topics,
                'total': len(topics),
                'covered': covered,
                'pct': round(covered / len(topics) * 100) if topics else 0,
            })
    except Exception:
        pass

    context = {
        'total_sessions': total_sessions,
        'active_students_count': active_students_count,
        'avg_msgs': round(avg_msgs_per_session, 1),
        'top_students': top_students,
        'common_topics': topic_counts,
        'recent_activity': recent_activity,
        'scheme_progress': scheme_progress,
    }
    return render(request, 'teachers/ai_insights.html', context)


@login_required
def teacher_list(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        teacher_id = request.POST.get('teacher_id')
        teacher = get_object_or_404(Teacher, id=teacher_id)

        if action == 'assign_class':
            class_id = request.POST.get('class_id')
            if class_id:
                class_obj = get_object_or_404(Class, id=class_id)
                class_obj.class_teacher = teacher
                class_obj.save()
                messages.success(request, f'{teacher.user.get_full_name()} assigned to {class_obj.name}.')
            else:
                messages.error(request, 'Please select a class to assign.')
        elif action == 'clear_assignments':
            removed_count = teacher.managed_classes.update(class_teacher=None)
            messages.success(request, f'Cleared {removed_count} class assignment(s) for {teacher.user.get_full_name()}.')

        return redirect('teachers:teacher_list')
    
    query = request.GET.get('q', '')
    teachers = Teacher.objects.select_related('user').annotate(
        classes_count=Count('managed_classes', distinct=True),
        subjects_count=Count('classsubject', distinct=True)
    )
    
    if query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(user__email__icontains=query)
        )
    
    teachers = teachers.order_by('user__first_name', 'user__last_name')
    classes = Class.objects.select_related('academic_year').order_by('name')
    
    context = {
        'teachers': teachers,
        'query': query,
        'classes': classes,
    }
    return render(request, 'teachers/teacher_list.html', context)


@login_required
def import_teachers_csv(request):
    """Import teachers from CSV file"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can import teachers.')
        return redirect('teachers:teacher_list')
    
    if request.method == 'POST':
        form = TeacherCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Validate file extension
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('teachers:import_csv')
            
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
                        employee_id = (row.get('Employee ID') or row.get('employee_id') or '').strip()
                        email = (row.get('Email') or row.get('email') or '').strip()
                        phone = (row.get('Phone') or row.get('phone') or '').strip()
                        qualification = (row.get('Qualification') or row.get('qualification') or '').strip()
                        date_of_joining = (row.get('Date of Joining') or row.get('date_of_joining') or '').strip()
                        age = (row.get('Age') or row.get('age') or '').strip()
                        
                        if not first_name:
                            errors.append(f"Row {row_num}: Missing first name")
                            skipped_count += 1
                            continue
                        
                        # Last name is optional
                        if not last_name:
                            last_name = ''
                        
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
                        
                        # Use provided employee ID or generate one
                        if employee_id and employee_id.upper() not in ['N/A', 'NA', '']:
                            # Clean up employee ID
                            employee_id = employee_id.strip().replace(' ', '')
                            # Check if it already exists
                            if Teacher.objects.filter(employee_id=employee_id).exists():
                                errors.append(f"Row {row_num}: Employee ID '{employee_id}' already exists")
                                skipped_count += 1
                                continue
                        else:
                            # Generate employee ID
                            prefix = 'TCH'
                            for _ in range(100):  # Try up to 100 times
                                suffix = ''.join(random.choices(string.digits, k=4))
                                candidate = f"{prefix}{suffix}"
                                if not Teacher.objects.filter(employee_id=candidate).exists():
                                    employee_id = candidate
                                    break
                        
                        if not employee_id:
                            errors.append(f"Row {row_num}: Could not generate unique employee ID")
                            skipped_count += 1
                            continue
                        
                        # Prepare email
                        if not email or email.upper() in ['N/A', 'NA', '']:
                            email = f"{username}@school.local"
                        
                        # Check if user with this email already exists
                        if User.objects.filter(email=email).exists():
                            email = f"{username}{random.randint(1, 999)}@school.local"
                        
                        # Parse age for date of birth
                        try:
                            teacher_age = int(age) if age else 30
                        except ValueError:
                            teacher_age = 30
                        
                        # Calculate date of birth
                        dob_year = max(1900, date.today().year - teacher_age)
                        date_of_birth = date(dob_year, 1, 1)
                        
                        # Parse date of joining
                        if date_of_joining and date_of_joining.upper() not in ['N/A', 'NA', '']:
                            try:
                                # Try parsing common date formats
                                from datetime import datetime
                                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                                    try:
                                        joining_date = datetime.strptime(date_of_joining, fmt).date()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    joining_date = date.today()
                            except Exception:
                                joining_date = date.today()
                        else:
                            joining_date = date.today()
                        
                        # Prepare qualification
                        if not qualification or qualification.upper() in ['N/A', 'NA', '']:
                            qualification = 'Bachelor of Education'
                        
                        # Create user
                        user = User.objects.create(
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            user_type='teacher'
                        )
                        user.set_unusable_password()
                        user.save()
                        
                        # Create teacher
                        teacher = Teacher.objects.create(
                            user=user,
                            employee_id=employee_id,
                            date_of_birth=date_of_birth,
                            date_of_joining=joining_date,
                            qualification=qualification
                        )
                        
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        skipped_count += 1
                        continue
                
                # Show results
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} teacher(s).')
                
                if skipped_count > 0:
                    messages.warning(request, f'Skipped {skipped_count} row(s) due to errors.')
                
                if errors and len(errors) <= 10:
                    for error in errors:
                        messages.error(request, error)
                elif errors:
                    messages.error(request, f'{len(errors)} errors occurred. First 10: {", ".join(errors[:10])}')
                
                return redirect('teachers:teacher_list')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
                return redirect('teachers:import_csv')
    else:
        form = TeacherCSVImportForm()
    
    return render(request, 'teachers/import_csv.html', {'form': form})


@login_required
def teacher_detail(request, teacher_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher.objects.select_related('user'), id=teacher_id)
    
    # Get managed classes
    managed_classes = teacher.managed_classes.select_related('academic_year')
    
    # Get subjects taught
    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related(
        'class_name', 'subject', 'class_name__academic_year'
    )
    
    # Get lesson plans
    lesson_plans = LessonPlan.objects.filter(teacher=teacher).select_related(
        'subject', 'school_class'
    ).order_by('-date_added')[:5]
    

    context = {
        'teacher': teacher,
        'managed_classes': managed_classes,
        'class_subjects': class_subjects,
        'lesson_plans': lesson_plans,
    }
    return render(request, 'teachers/teacher_detail.html', context)


@login_required
def analytics_dashboard(request):
    if request.user.user_type not in ['teacher', 'admin']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Try to get the teacher object
    teacher = None
    if request.user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
    
    # Get classes taught by the teacher
    classes = Class.objects.none()
    selected_class = None
    students_data = []
    
    if teacher:
        # Teachers see their assigned classes
        classes = Class.objects.filter(classsubject__teacher=teacher).distinct()
    elif request.user.user_type == 'admin':
        # Admins see all classes
        classes = Class.objects.all()

    class_id = request.GET.get('class_id')
    if class_id:
        selected_class = get_object_or_404(Class, id=class_id)
    elif classes.exists():
        selected_class = classes.first()
    
    # Aggregated class-level insights
    top_strength = None
    common_misconceptions_list = []
    ai_engagement_count = 0
    
    if selected_class:
        from academics.tutor_models import LearnerMemory
        from collections import Counter
        
        students = Student.objects.filter(current_class=selected_class).select_related('user')
        
        # Prefetch LearnerMemory and last session in bulk
        memory_map = {}
        try:
            memories = LearnerMemory.objects.filter(student__in=students)
            memory_map = {m.student_id: m for m in memories}
        except (OperationalError, ProgrammingError):
            pass  # Table may not exist yet
        
        # Prefetch last TutorSession per student — single aggregated query
        last_session_map = {}
        session_count_map = {}
        try:
            from django.db.models import Max
            session_stats = (
                TutorSession.objects.filter(student__in=students)
                .values('student_id')
                .annotate(
                    last_started=Max('started_at'),
                    total_sessions=Count('id'),
                )
            )
            for row in session_stats:
                last_session_map[row['student_id']] = row['last_started']
                session_count_map[row['student_id']] = row['total_sessions']
        except (OperationalError, ProgrammingError):
            pass
        
        # Prefetch average grade per student (current academic year)
        current_year = AcademicYear.objects.filter(is_current=True).first()
        grade_avg_map = {}
        if current_year:
            grade_avgs = (
                Grade.objects.filter(
                    student__in=students,
                    academic_year=current_year,
                    total_score__gt=0,
                )
                .values('student_id')
                .annotate(avg_score=Avg('total_score'))
            )
            grade_avg_map = {g['student_id']: float(g['avg_score']) for g in grade_avgs}
        
        # Collect class-wide topics for aggregation
        all_mastered = []
        all_misconceptions = []
        
        for student in students:
            memory = memory_map.get(student.id)
            grade_avg = grade_avg_map.get(student.id)
            last_session_time = last_session_map.get(student.id)
            sessions = session_count_map.get(student.id, 0)
            
            has_ai_data = memory is not None and (memory.total_sessions_analysed or 0) > 0
            has_grade_data = grade_avg is not None
            
            # ── Calculate mastery score ──
            mastery = None
            misconception = None
            suggested_intervention = None
            
            if has_ai_data:
                mastered = list(memory.mastered_topics or [])
                misconceptions = list(memory.active_misconceptions or [])
                weaknesses = list(memory.weaknesses or [])
                strengths = list(memory.strengths or [])
                
                all_mastered.extend(mastered)
                all_misconceptions.extend(misconceptions)
                
                # AI mastery heuristic: ratio of mastered to total known topics
                total_signals = len(mastered) + len(misconceptions) + len(weaknesses)
                if total_signals > 0:
                    ai_mastery = round(len(mastered) / total_signals * 100)
                else:
                    ai_mastery = 70  # Sessions exist but no clear signals yet
                
                # Blend with grade average if available
                if has_grade_data:
                    mastery = round(ai_mastery * 0.4 + grade_avg * 0.6)
                else:
                    mastery = ai_mastery
                
                # Pick top misconception/weakness for intervention
                if misconceptions:
                    misconception = misconceptions[0]
                    suggested_intervention = f"Focus on: {misconceptions[0]}"
                elif weaknesses:
                    misconception = weaknesses[0]
                    suggested_intervention = f"Review: {weaknesses[0]}"
            elif has_grade_data:
                mastery = round(grade_avg)
            
            # Determine status
            if mastery is not None:
                if mastery >= 80:
                    status = 'green'
                elif mastery >= 60:
                    status = 'yellow'
                    if not misconception and has_grade_data and grade_avg < 70:
                        suggested_intervention = "Grades trending down — consider review session"
                else:
                    status = 'red'
                    if not suggested_intervention:
                        suggested_intervention = "Low performance — schedule 1-on-1 review"
            else:
                status = 'secondary'  # No data at all
                mastery = 0
            
            if has_ai_data or last_session_time:
                ai_engagement_count += 1
            
            # Format "last active"
            last_active = None
            if last_session_time:
                delta = timezone.now() - last_session_time
                if delta.days > 0:
                    last_active = f"{delta.days}d ago"
                elif delta.seconds >= 3600:
                    last_active = f"{delta.seconds // 3600}h ago"
                elif delta.seconds >= 60:
                    last_active = f"{delta.seconds // 60}m ago"
                else:
                    last_active = "just now"
            
            students_data.append({
                'name': student.user.get_full_name(),
                'id': student.id,
                'mastery': mastery,
                'status': status,
                'misconception': misconception,
                'intervention': suggested_intervention,
                'last_active': last_active,
                'has_ai_data': has_ai_data,
                'session_count': sessions,
            })
        
        # ── Class-wide aggregated insights ──
        if all_mastered:
            strength_counts = Counter(all_mastered).most_common(1)
            top_strength = strength_counts[0][0] if strength_counts else None
        
        if all_misconceptions:
            misc_counts = Counter(all_misconceptions).most_common(5)
            common_misconceptions_list = [{'topic': t, 'count': c} for t, c in misc_counts]
            
    # Calculate class aggregate stats
    avg_mastery = 0
    intervention_count = 0
    scored_students = [s for s in students_data if s['status'] != 'secondary']
    if scored_students:
        avg_mastery = sum(s['mastery'] for s in scored_students) / len(scored_students)
        intervention_count = sum(1 for s in students_data if s['status'] == 'red')

    # ── Grade distribution for the selected class ──
    grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    if selected_class and current_year:
        for s in students_data:
            m = s.get('mastery', 0)
            if s['status'] != 'secondary':
                if m >= 80:   grade_distribution['A'] += 1
                elif m >= 70: grade_distribution['B'] += 1
                elif m >= 60: grade_distribution['C'] += 1
                elif m >= 50: grade_distribution['D'] += 1
                else:         grade_distribution['F'] += 1

    # ── Class-level attendance rate (last 30 days) ──
    class_attendance_rate = None
    if selected_class:
        from students.models import Attendance as _Att
        import datetime as _dt
        thirty_ago = timezone.now().date() - _dt.timedelta(days=30)
        att_total = _Att.objects.filter(
            student__current_class=selected_class, date__gte=thirty_ago
        ).count()
        att_present = _Att.objects.filter(
            student__current_class=selected_class, date__gte=thirty_ago, status='present'
        ).count()
        class_attendance_rate = round(att_present / att_total * 100, 1) if att_total else None

    # ── Lesson plan completion (current week) ──
    lesson_plan_completion = None
    if teacher and selected_class:
        try:
            iso = timezone.now().isocalendar()
            current_week_num = iso[1]
            submitted = LessonPlan.objects.filter(
                teacher=teacher, school_class=selected_class, week_number=current_week_num
            ).count()
            expected = ClassSubject.objects.filter(
                teacher=teacher, class_name=selected_class
            ).count()
            lesson_plan_completion = {
                'submitted': submitted,
                'expected': expected,
                'rate': round(submitted / expected * 100) if expected > 0 else 0,
            }
        except Exception:
            pass

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students_data': students_data,
        'avg_mastery': round(avg_mastery, 1),
        'intervention_count': intervention_count,
        'top_strength': top_strength,
        'common_misconceptions_list': common_misconceptions_list,
        'ai_engagement_count': ai_engagement_count,
        'total_students': len(students_data),
        'grade_distribution': grade_distribution,
        'class_attendance_rate': class_attendance_rate,
        'lesson_plan_completion': lesson_plan_completion,
    }
    return render(request, 'teachers/analytics_dashboard.html', context)




@login_required
def generate_remedial_lesson(request):
    """
    Called from analytics dashboard to 'Generate Lesson' for a misconception.
    Redirects to lesson plan creator with a pre-filled topic.
    """
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    topic = request.GET.get('topic', 'General Review')
    
    # We simply redirect to the creation form, passing the topic.
    # The lesson_plan_create view handles the 'Artificial Intelligence' part by pre-filling data.
    from django.urls import reverse
    import urllib.parse
    
    encoded_topic = urllib.parse.quote(topic)
    url = reverse('teachers:lesson_plan_create')
    return redirect(f"{url}?topic={encoded_topic}")






@login_required
def assign_class_teacher(request, class_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        # Check if this is an AJAX request to add a new teacher
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('action') == 'add_teacher':
            from django.http import JsonResponse
            import random
            import string
            
            try:
                # Extract form data
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                employee_id = request.POST.get('employee_id', '').strip()
                qualification = request.POST.get('qualification', '').strip()
                date_of_birth = request.POST.get('date_of_birth', '').strip()
                date_of_joining = request.POST.get('date_of_joining', '').strip()
                
                # Validate required fields
                if not first_name or not last_name or not email:
                    return JsonResponse({'success': False, 'error': 'First name, last name, and email are required'})
                
                # Auto-generate Employee ID if not provided
                if not employee_id:
                    while True:
                        suffix = ''.join(random.choices(string.digits, k=4))
                        employee_id = f"TCH{suffix}"
                        if not Teacher.objects.filter(employee_id=employee_id).exists() and not User.objects.filter(username=employee_id).exists():
                            break
                
                # Check if username already exists
                username = employee_id
                if User.objects.filter(username=username).exists():
                    return JsonResponse({'success': False, 'error': f'Employee ID {employee_id} already exists'})
                
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    return JsonResponse({'success': False, 'error': f'Email {email} already exists'})
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=username,  # Default password is employee ID
                    first_name=first_name,
                    last_name=last_name,
                    user_type='teacher',
                    phone=phone
                )
                
                # Create teacher
                from datetime import datetime, date
                teacher = Teacher(
                    user=user,
                    employee_id=employee_id,
                    qualification=qualification or 'Not provided'
                )
                
                # Set dates if provided
                if date_of_birth:
                    try:
                        teacher.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                if date_of_joining:
                    try:
                        teacher.date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
                    except ValueError:
                        teacher.date_of_joining = date.today()
                else:
                    teacher.date_of_joining = date.today()
                
                teacher.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Teacher {user.get_full_name()} added successfully',
                    'teacher_id': teacher.id,
                    'teacher_name': user.get_full_name(),
                    'employee_id': employee_id
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Regular form submission for assigning teacher
        teacher_id = request.POST.get('teacher_id')
        if teacher_id:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                class_obj.class_teacher = teacher
                class_obj.save()
                messages.success(request, f'{teacher.user.get_full_name()} assigned as class teacher for {class_obj.name}')
            except Teacher.DoesNotExist:
                messages.error(request, 'Invalid teacher selected')
        else:
            class_obj.class_teacher = None
            class_obj.save()
            messages.success(request, f'Class teacher removed from {class_obj.name}')
        
        return redirect('academics:manage_classes')
    
    teachers = Teacher.objects.select_related('user').order_by('user__first_name', 'user__last_name')
    
    from datetime import date
    context = {
        'class_obj': class_obj,
        'teachers': teachers,
        'today': date.today().strftime('%Y-%m-%d')
    }
    return render(request, 'teachers/assign_class_teacher.html', context)


@login_required
def edit_teacher(request, teacher_id):
    from .forms import TeacherEditForm
    
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Teacher profile for {teacher.user.get_full_name()} updated successfully.')
            return redirect('teachers:teacher_detail', teacher_id=teacher.id)
    else:
        form = TeacherEditForm(instance=teacher)
    
    context = {
        'form': form,
        'teacher': teacher
    }
    return render(request, 'teachers/edit_teacher.html', context)



@login_required
def teacher_classes(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related(
        'class_name', 'subject'
    )
    
    return render(request, 'teachers/my_classes.html', {'class_subjects': class_subjects})


@login_required
def enter_grades(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
    selected_cs_id = request.GET.get('class_subject_id')
    
    if request.method == 'POST':
        term = normalize_term(request.POST.get('term', 'first'))
        class_subject_id = request.POST.get('class_subject_id') or request.POST.get('class_subject')
        student_ids = request.POST.getlist('student_id[]') or request.POST.getlist('student_id')

        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year:
            messages.error(request, 'No academic year is marked as current.')
            return redirect('teachers:enter_grades')

        try:
            cs = class_subjects.get(id=class_subject_id)
        except ClassSubject.DoesNotExist:
            messages.error(request, 'Invalid class/subject selection.')
            return redirect('teachers:enter_grades')

        created_count = 0
        for student_id in student_ids:
            overall_raw = request.POST.get(f'overall_score_{student_id}')
            class_score_raw = request.POST.get(f'class_score_{student_id}', '')
            exams_score_raw = request.POST.get(f'exams_score_{student_id}', '')

            class_score = exams_score = None

            # Prefer the explicit class/exam fields; fall back to overall if needed
            try:
                if class_score_raw != '' and exams_score_raw != '':
                    class_score = Decimal(class_score_raw)
                    exams_score = Decimal(exams_score_raw)
                elif overall_raw not in (None, ''):
                    overall = Decimal(overall_raw)
                    overall = max(Decimal('0'), min(overall, Decimal('100')))
                    class_score = overall * Decimal('0.3')
                    exams_score = overall * Decimal('0.7')
                else:
                    continue
            except (InvalidOperation, TypeError):
                continue

            # Server-side validation of maxima
            class_score = max(Decimal('0'), min(class_score, Decimal('30')))
            exams_score = max(Decimal('0'), min(exams_score, Decimal('70')))

            Grade.objects.update_or_create(
                student_id=student_id,
                subject=cs.subject,
                academic_year=academic_year,
                term=term,
                defaults={
                    'class_score': class_score,
                    'exams_score': exams_score,
                    'created_by': request.user
                }
            )
            created_count += 1

        if created_count == 0:
            messages.warning(request, 'No grades were saved. Please ensure you loaded students and entered scores.')
        else:
            messages.success(request, f'Grades entered/updated for {created_count} students in {cs.class_name} - {cs.subject}.')
        return redirect('teachers:enter_grades')
    
    return render(request, 'teachers/enter_grades.html', {
        'class_subjects': class_subjects,
        'selected_cs_id': selected_cs_id,
    })


@login_required
@require_POST
def scan_grades_sheet(request):
    if request.user.user_type != 'teacher':
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
        
    if 'image' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'No image provided'}, status=400)
        
    try:
        import base64
        import json
        from academics.ai_tutor import _post_chat_completion
        
        image_file = request.FILES['image']
        image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        mime_type = image_file.content_type
        
        prompt = """You are an AI assistant helping a teacher digitize a handwritten or printed student grade sheet.
Please extract the list of student names and their corresponding grades. 
Look for either 'overall_score', or specific 'class_score' and 'exams_score' if broken down.
Return ONLY valid JSON in the following format:
[
  {
     "name": "Student Full Name",
     "overall_score": 85,
     "class_score": 25,
     "exams_score": 60
  }
]
If a score is missing or unable to be read, set it to null. Ensure the response contains no markdown formatting around the output, just raw JSON text. No '''json.
"""

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        response_data = _post_chat_completion(payload)
        
        if 'error' in response_data:
             return JsonResponse({'status': 'error', 'message': f"AI Error: {response_data['error']}"}, status=500)

        choices = response_data.get('choices', [])
        if not choices:
            return JsonResponse({'status': 'error', 'message': 'Failed to process image. No response from AI.'}, status=500)
            
        content = choices[0]['message']['content'].strip()
        
        # Strip potential markdown formatting
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
            
        grades_data = json.loads(content.strip())
        return JsonResponse({'status': 'success', 'data': grades_data})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'AI returned malformed data format. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'}, status=500)


@login_required
def get_students(request, class_id):
    subject_id = request.GET.get('subject_id')
    term = normalize_term(request.GET.get('term', 'first'))

    students = Student.objects.filter(current_class_id=class_id).select_related('user')

    academic_year = AcademicYear.objects.filter(is_current=True).first()
    grades_by_student = {}
    if academic_year and subject_id:
        grades = Grade.objects.filter(
            student__current_class_id=class_id,
            subject_id=subject_id,
            academic_year=academic_year,
            term=term,
        )
        grades_by_student = {g.student_id: g for g in grades}

    data = []
    for s in students:
        g = grades_by_student.get(s.id)
        data.append({
            'id': s.id,
            'name': s.user.get_full_name(),
            'admission_number': s.admission_number,
            'class_score': str(g.class_score) if g else '',
            'exams_score': str(g.exams_score) if g else '',
            'total_score': str(g.total_score) if g else '',
            'grade': g.grade if g else '',
            'remarks': g.remarks if g else '',
        })

    return JsonResponse(data, safe=False)


@login_required
def teacher_schedule(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('dashboard')

    # Get all schedule entries for this teacher/class-subject
    timetable_qs = Timetable.objects.filter(class_subject__teacher=teacher).select_related(
        'class_subject', 'class_subject__class_name', 'class_subject__subject'
    ).order_by('day', 'start_time')
    
    # Organize by day for simpler template loop
    days_data = []
    # Timetable.DAY_CHOICES is ((0,'Monday'), ...)
    for code, name in Timetable.DAY_CHOICES:
        # Filter in python to avoid N queries, 
        # or just filter in loop if list is short. 
        # Since timetable_qs is likely small ( < 50 items), list filter is fine.
        entries = [t for t in timetable_qs if t.day == code]
        days_data.append({
            'name': name,
            'entries': entries
        })
            
    return render(request, 'teachers/schedule.html', {'days': days_data})

@login_required
def print_duty_roster(request):
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if not current_year:
        current_year = AcademicYear.objects.first()

    today = timezone.now().date()

    req_term = request.GET.get('term')
    if req_term:
        term = req_term
    else:
        current_duty = DutyWeek.objects.filter(
            academic_year=current_year,
            start_date__lte=today,
            end_date__gte=today
        ).first()
        term = current_duty.term if current_duty else (
            'second' if 1 <= today.month <= 4 else
            ('third' if 5 <= today.month <= 8 else 'first')
        )

    year_id = request.GET.get('year', current_year.id if current_year else None)
    year = get_object_or_404(AcademicYear, id=year_id) if year_id else None

    weeks = DutyWeek.objects.filter(
        academic_year=year, term=term
    ).prefetch_related(
        'assignments', 'assignments__teacher', 'assignments__teacher__user'
    ).order_by('week_number')

    # Personalised "My Duty" banner
    my_next_duty = None
    teacher = getattr(request.user, 'teacher', None)
    if teacher:
        # Currently on duty this week?
        my_next_duty = DutyWeek.objects.filter(
            assignments__teacher=teacher,
            start_date__lte=today,
            end_date__gte=today,
        ).prefetch_related('assignments__teacher__user').first()
        # Otherwise, next upcoming duty
        if not my_next_duty:
            my_next_duty = DutyWeek.objects.filter(
                assignments__teacher=teacher,
                start_date__gt=today,
            ).prefetch_related('assignments__teacher__user').order_by('start_date').first()

    context = {
        'weeks': weeks,
        'year': year,
        'term': term,
        'today': today,
        'teacher': teacher,
        'my_next_duty': my_next_duty,
        'school_info': SchoolInfo.objects.first(),
        'available_terms': ['first', 'second', 'third'],
        'academic_years': AcademicYear.objects.all(),
    }
    return render(request, 'teachers/duty_roster_pdf.html', context)


@login_required
def generate_duty_weeks(request):
    """Admin-only: auto-create DutyWeek rows for a full term."""
    if request.user.user_type != 'admin':
        messages.error(request, "Only admins can generate duty weeks.")
        return redirect('teachers:duty_roster')

    if request.method != 'POST':
        return redirect('teachers:duty_roster')

    from datetime import timedelta
    from django.urls import reverse as url_reverse

    year_id   = request.POST.get('year')
    term      = request.POST.get('term', 'first')
    start_str = request.POST.get('start_date', '')
    try:
        num_weeks = max(1, min(int(request.POST.get('num_weeks') or 13), 20))
    except (ValueError, TypeError):
        num_weeks = 13

    year = get_object_or_404(AcademicYear, id=year_id)

    try:
        start = date.fromisoformat(start_str)
    except (ValueError, TypeError):
        messages.error(request, "Invalid start date.")
        return redirect(f"{url_reverse('teachers:duty_roster')}?term={term}&year={year_id}")

    created = skipped = 0
    for i in range(num_weeks):
        week_start = start + timedelta(weeks=i)
        week_end   = week_start + timedelta(days=4)   # Mon → Fri
        _, was_created = DutyWeek.objects.get_or_create(
            academic_year=year,
            term=term,
            week_number=i + 1,
            defaults={'start_date': week_start, 'end_date': week_end},
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    if created:
        messages.success(request, f"{created} duty week(s) generated for {term.title()} Term {year.name}.")
    if skipped:
        messages.info(request, f"{skipped} week(s) already existed and were skipped.")

    return redirect(f"{url_reverse('teachers:duty_roster')}?term={term}&year={year_id}")


@login_required
def manage_exercises(request, class_subject_id):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id, teacher=teacher)
    
    term = request.GET.get('term', 'first')
    
    exercises = ClassExercise.objects.filter(
        class_subject=class_subject,
        term=term
    ).order_by('-date_assigned')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        max_marks = request.POST.get('max_marks')
        term_input = request.POST.get('term')
        
        if title and max_marks:
            ClassExercise.objects.create(
                class_subject=class_subject,
                term=term_input,
                title=title,
                max_marks=max_marks
            )
            messages.success(request, 'Exercise created successfully.')
            return redirect(f"{request.path}?term={term_input}")

    # Helper for term names
    term_choices = Grade.TERM_CHOICES

    return render(request, 'teachers/manage_exercises.html', {
        'class_subject': class_subject,
        'exercises': exercises,
        'selected_term': term,
        'term_choices': term_choices,
    })


@login_required
def enter_exercise_scores(request, exercise_id):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    exercise = get_object_or_404(ClassExercise, id=exercise_id, class_subject__teacher=teacher)
    
    students = Student.objects.filter(current_class=exercise.class_subject.class_name).order_by('user__last_name')
    
    if request.method == 'POST':
        try:
            with django.db.transaction.atomic():
                updated_count = 0
                for student in students:
                    score_val = request.POST.get(f'score_{student.id}')
                    remarks_val = request.POST.get(f'remarks_{student.id}', '')
                    
                    if score_val:
                        try:
                            score = Decimal(score_val)
                            score = max(Decimal('0'), min(score, exercise.max_marks))
                            
                            StudentExerciseScore.objects.update_or_create(
                                student=student,
                                exercise=exercise,
                                defaults={'score': score, 'remarks': remarks_val}
                            )
                            updated_count += 1
                        except (InvalidOperation, TypeError):
                            continue
                
                # RECALCULATION LOGIC
                all_exercises = ClassExercise.objects.filter(
                    class_subject=exercise.class_subject,
                    term=exercise.term
                )
                total_possible = sum(ex.max_marks for ex in all_exercises)
                
                if total_possible > 0:
                    current_year = AcademicYear.objects.filter(is_current=True).first()
                    if not current_year:
                        current_year = AcademicYear.objects.order_by('-start_date').first()

                    # Pre-fetch all scores for this subject/term to avoid N+1 inside loop if possible 
                    # but simple iteration is fine for class size < 50
                    
                    for student in students:
                        student_scores = StudentExerciseScore.objects.filter(
                            student=student,
                            exercise__in=all_exercises
                        ).aggregate(total=models.Sum('score'))['total'] or Decimal('0')
                        
                        # (Obtained / Possible) * 30
                        new_class_score = (student_scores / total_possible) * Decimal('30')
                        
                        grade_obj, _ = Grade.objects.get_or_create(
                            student=student,
                            subject=exercise.class_subject.subject,
                            academic_year=current_year,
                            term=exercise.term,
                            defaults={'created_by': request.user}
                        )
                        grade_obj.class_score = new_class_score
                        grade_obj.save()

            messages.success(request, f'Scores saved for {updated_count} students. Class assessment totals updated.')
        except Exception as e:
            messages.error(request, f"Error saving scores: {e}")
            
        return redirect('teachers:enter_exercise_scores', exercise_id=exercise.id)

    existing_scores = StudentExerciseScore.objects.filter(exercise=exercise)
    score_map = {s.student_id: s for s in existing_scores}
    
    student_list = []
    for s in students:
        student_list.append({
            'student': s,
            'score_obj': score_map.get(s.id)
        })

    return render(request, 'teachers/enter_exercise_scores.html', {
        'exercise': exercise,
        'student_list': student_list,
    })


@login_required
def search_students(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    query = request.GET.get('q', '').strip()
    students = []
    
    if query:
        students = Student.objects.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(admission_number__icontains=query)
        ).select_related('user', 'current_class').distinct()[:20]
        
    return render(request, 'teachers/search_results.html', {
        'query': query,
        'students': students,
        'school_name': SchoolInfo.objects.first().name if SchoolInfo.objects.exists() else 'School'
    })


@login_required
def curriculum_library(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = Teacher.objects.get(user=request.user)

    resource_fields_available = False
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cols = [col.name for col in connection.introspection.get_table_description(cursor, Resource._meta.db_table)]
        resource_fields_available = 'resource_type' in cols and 'curriculum' in cols
    except Exception:
        resource_fields_available = False

    try:
        qs = Resource.objects.filter(
            Q(target_audience__in=['teachers', 'all']) | Q(class_subject__teacher=teacher)
        ).order_by('-uploaded_at')
        if resource_fields_available:
            qs = qs.filter(resource_type='curriculum')
        else:
            qs = qs.filter(class_subject__isnull=True)
            qs = qs.only('id', 'title', 'description', 'file', 'link', 'uploaded_at')
        resources = list(qs)
    except (OperationalError, ProgrammingError):
        resources = []
        resource_fields_available = False

    curriculum_options = [('all', 'All Curricula')]
    if resource_fields_available:
        curriculum_options = [('all', 'All Curricula')] + list(Resource.CURRICULUM_CHOICES)

    selected_curriculum = request.GET.get('curriculum', 'all')
    if resource_fields_available and selected_curriculum != 'all':
        resources = [r for r in resources if getattr(r, 'curriculum', None) == selected_curriculum]

    return render(request, 'teachers/curriculum_library.html', {
        'resources': resources,
        'resource_fields_available': resource_fields_available,
        'curriculum_options': curriculum_options,
        'selected_curriculum': selected_curriculum,
    })


@login_required
def class_resources(request, class_subject_id):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id, teacher=teacher)

    # Detect availability of new fields on the DB
    resource_fields_available = False
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cols = [col.name for col in connection.introspection.get_table_description(cursor, Resource._meta.db_table)]
        resource_fields_available = 'resource_type' in cols and 'curriculum' in cols
    except Exception:
        resource_fields_available = False

    resource_type_filter = request.GET.get('type', 'all')
    curriculum_filter = request.GET.get('curriculum', 'all')
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.class_subject = class_subject
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Resource uploaded successfully.')
            return redirect('teachers:class_resources', class_subject_id=class_subject.id)
    else:
        form = ResourceForm(initial={
            'class_subject': class_subject.id,
            'resource_type': 'teaching',
            'curriculum': 'ges_jhs_new',
        })

    if 'class_subject' in form.fields:
        form.fields['class_subject'].widget = forms.HiddenInput()
        form.fields['class_subject'].initial = class_subject.id

    base_qs = Resource.objects.filter(class_subject=class_subject).order_by('-uploaded_at')
    if not resource_fields_available:
        resources = base_qs.only('id', 'title', 'description', 'file', 'link', 'uploaded_at')
        curriculum_options = [('all', 'All Curricula')]
        resource_type_filter = 'all'
        curriculum_filter = 'all'
    else:
        resources = base_qs
        if resource_type_filter in ['curriculum', 'teaching']:
            resources = resources.filter(resource_type=resource_type_filter)
        if curriculum_filter != 'all':
            resources = resources.filter(curriculum=curriculum_filter)
        curriculum_options = [('all', 'All Curricula')] + list(Resource.CURRICULUM_CHOICES)
    
    return render(request, 'teachers/class_resources.html', {
        'class_subject': class_subject,
        'resources': resources,
        'form': form,
        'resource_type_filter': resource_type_filter,
        'curriculum_filter': curriculum_filter,
        'curriculum_options': curriculum_options,
        'resource_fields_available': resource_fields_available,
    })

@login_required
def delete_resource(request, resource_id):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    resource = get_object_or_404(Resource, id=resource_id, class_subject__teacher__user=request.user)
    class_subject_id = resource.class_subject.id
    resource.delete()
    messages.success(request, 'Resource deleted successfully.')
    return redirect('teachers:class_resources', class_subject_id=class_subject_id)



@login_required
def lesson_plan_list(request):
    is_teacher = request.user.user_type == 'teacher'
    is_admin = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = None
    if is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)
    
    week = request.GET.get('week', '').strip()
    subject_id = request.GET.get('subject', '').strip()
    class_id = request.GET.get('school_class', '').strip()
    query = request.GET.get('q', '').strip()
    aura_only = request.GET.get('aura_only', '').strip()

    teacher_subjects = []
    teacher_classes = []
    teacher_list = []
    selected_teacher = request.GET.get('teacher', '').strip()

    if is_teacher:
        assigned_pairs = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
        teacher_subjects = [pair.subject for pair in assigned_pairs]
        teacher_classes = [pair.class_name for pair in assigned_pairs]
    else:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        class_qs = Class.objects.all()
        if current_year:
            class_qs = class_qs.filter(academic_year=current_year)
        teacher_subjects = Subject.objects.all().order_by('name')
        teacher_classes = class_qs.order_by('name')
        teacher_list = Teacher.objects.select_related('user').order_by('user__first_name', 'user__last_name')

    # de-duplicate while preserving order
    seen_subject_ids = set()
    teacher_subjects = [s for s in teacher_subjects if not (s.id in seen_subject_ids or seen_subject_ids.add(s.id))]
    seen_class_ids = set()
    teacher_classes = [c for c in teacher_classes if not (c.id in seen_class_ids or seen_class_ids.add(c.id))]

    try:
        # Force evaluation to catch DB errors if table doesn't exist yet
        lesson_plans_qs = LessonPlan.objects.select_related('subject', 'school_class', 'teacher', 'teacher__user')
        if is_teacher:
            lesson_plans_qs = lesson_plans_qs.filter(teacher=teacher)
        elif selected_teacher:
            lesson_plans_qs = lesson_plans_qs.filter(teacher_id=selected_teacher)
        if week:
            lesson_plans_qs = lesson_plans_qs.filter(week_number=week)
        if subject_id:
            lesson_plans_qs = lesson_plans_qs.filter(subject_id=subject_id)
        if class_id:
            lesson_plans_qs = lesson_plans_qs.filter(school_class_id=class_id)
        if query:
            lesson_plans_qs = lesson_plans_qs.filter(
                Q(topic__icontains=query) |
                Q(objectives__icontains=query) |
                Q(presentation__icontains=query)
            )
        if aura_only:
            lesson_plans_qs = lesson_plans_qs.filter(introduction__icontains='PULSE CHECK')
        lesson_plans = list(lesson_plans_qs)
        aura_drafted_count = sum(1 for p in lesson_plans if 'PULSE CHECK' in (p.introduction or ''))
    except (OperationalError, ProgrammingError):
        lesson_plans = []
        teacher_subjects = []
        teacher_classes = []
        aura_drafted_count = 0
        messages.warning(request, "Lesson Plan system is initializing. Please try again later.")
        
    return render(request, 'teachers/lesson_plan_list.html', {
        'lesson_plans': lesson_plans,
        'aura_drafted_count': aura_drafted_count,
        'selected_week': week,
        'selected_subject': subject_id,
        'selected_class': class_id,
        'selected_teacher': selected_teacher,
        'selected_query': query,
        'selected_aura_only': aura_only,
        'teacher_subjects': teacher_subjects,
        'teacher_classes': teacher_classes,
        'teacher_list': teacher_list,
        'is_teacher': is_teacher,
        'is_admin': is_admin,
    })
        
@login_required

@login_required
def lesson_plan_create(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Check for AI generation request
    initial_data = {}
    
    # CASE 1: Full AI Content passed via POST (from Chat) or huge GET
    # Ideally we'd use POST for large content, but if coming from a link, it's GET.
    # We might need to parse the unstructured text from Aura-T.
    
    ai_content = request.POST.get('ai_content') or request.GET.get('ai_content')
    topic = request.GET.get('topic') # Legacy/Simple Fallback
    # Pre-fill subject/class when coming from Scheme of Work topic chip
    prefill_subject_id = request.GET.get('subject_id')
    prefill_class_id   = request.GET.get('class_id')

    if ai_content:
        # PARSING LOGIC: Extract fields from the Aura-T standardized format
        import re
        
        def extract_section(header, text):
            # Allow for optional suffix inside the bold tag (like duration "[10 mins]")
            # Pattern matches: **Header[optional text]**:? content...
            # We use re.escape(header) but need to allow trailing chars before the closing **
            # Matches: **PHASE 1: STARTER [10mins]** or **PHASE 1: STARTER**
            pattern = re.compile(rf"\*\*{re.escape(header)}.*?\*\*\s*(.*?)(?=\n\*\*|\Z)", re.DOTALL | re.IGNORECASE)
            match = pattern.search(text)
            return match.group(1).strip() if match else ""

        # Attempt to map Aura-T output format to LessonPlan model fields
        parsed_topic = extract_section("Strand", ai_content) + ": " + extract_section("Sub Strand", ai_content)
        if len(parsed_topic) < 5: parsed_topic = topic or "New Lesson Plan"
            
        initial_data = {
            'topic': parsed_topic,
            'week_number': extract_section("WEEK", ai_content) or 1,
            'objectives': extract_section("Content Standard", ai_content) + "\n\n" + extract_section("Indicator", ai_content),
            'teaching_materials': extract_section("Resources", ai_content),
            'introduction': extract_section("PHASE 1: STARTER", ai_content),
            'presentation': extract_section("PHASE 2: NEW LEARNING", ai_content),
            'evaluation': extract_section("PHASE 3: REFLECTION", ai_content) or extract_section("Assessment", ai_content),
            'homework': extract_section("Homework", ai_content) or "Refer to textbook exercises.",
            'core_competencies': extract_section("Core Competencies", ai_content), # If you add this field to model later
        }
        messages.success(request, "Lesson plan draft populated from Aura-T session.")

    elif topic:
        # CASE 2: Simpler generation (Old method)
        initial_data = {
            'topic': topic,
            'objectives': f"By the end of the lesson, students will be able to:\n1. Understand the core concepts of {topic}.\n2. Apply {topic} to solve simple problems.\n3. Analyze real-world examples of {topic}.",
            'introduction': f"Begin with a 5-minute warm-up activity related to {topic}. Ask students what they already know about it to gauge prior knowledge.",
            'presentation': f"1. Define {topic} and key terminology.\n2. Demonstrate the main concept using visual aids.\n3. Walk through 2-3 step-by-step examples on the board.\n4. Facilitate a class discussion to check for understanding.",
            'evaluation': f"Distribute a short worksheet with 5 problems on {topic}. Circulate to provide individual assistance.",
            'homework': f"Read the chapter on {topic} and complete exercises 1-10 on page 42.",
            'teaching_materials': f"Textbook, Whiteboard, Marker, Projector (optional), Handouts on {topic}"
        }
        messages.info(request, f"AI has drafted a lesson plan block for '{topic}'. Please review and edit.")

    # Pre-select subject / class when redirected from Scheme of Work
    if prefill_subject_id and not initial_data.get('subject'):
        initial_data['subject'] = prefill_subject_id
    if prefill_class_id and not initial_data.get('school_class'):
        initial_data['school_class'] = prefill_class_id

    if request.method == 'POST' and 'topic' in request.POST: # Standard form submit
        form = LessonPlanForm(request.POST, teacher=teacher)
        if form.is_valid():
            lesson_plan = form.save(commit=False)
            lesson_plan.teacher = teacher
            lesson_plan.save()
            messages.success(request, 'Lesson plan created successfully.')
            return redirect('teachers:lesson_plan_list')
    else:
        form = LessonPlanForm(teacher=teacher, initial=initial_data)
        
    return render(request, 'teachers/lesson_plan_form.html', {
        'form': form,
        'title': 'Create Lesson Plan'
    })


@login_required
def lesson_plan_edit(request, pk):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    
    if request.method == 'POST':
        form = LessonPlanForm(request.POST, instance=lesson_plan, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lesson plan updated successfully.')
            
            # Check for next URL to return to same view (e.g. from inline edit)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('teachers:lesson_plan_list')
    else:
        form = LessonPlanForm(instance=lesson_plan, teacher=teacher)
        
    return render(request, 'teachers/lesson_plan_form.html', {
        'form': form,
        'title': 'Edit Lesson Plan'
    })

@login_required
def lesson_plan_detail(request, pk):
    is_teacher = request.user.user_type == 'teacher'
    is_admin = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    if is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)
        lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    else:
        lesson_plan = get_object_or_404(LessonPlan, pk=pk)
    
    intro = lesson_plan.introduction or ''
    pres  = lesson_plan.presentation or ''
    evl   = lesson_plan.evaluation or ''
    has_pulse       = 'PULSE CHECK' in intro
    has_checkpoints = 'CHECKPOINT QUESTIONS' in pres or 'CQ1:' in pres
    has_sprint      = 'MASTERY SPRINT' in evl or 'MS1:' in evl
    has_insight     = 'TEACHER INSIGHT' in evl
    aura_score      = sum([has_pulse, has_checkpoints, has_sprint, has_insight])

    return render(request, 'teachers/lesson_plan_detail.html', {
        'lesson_plan': lesson_plan,
        'is_admin': is_admin,
        'has_pulse': has_pulse,
        'has_checkpoints': has_checkpoints,
        'has_sprint': has_sprint,
        'has_insight': has_insight,
        'aura_score': aura_score,
    })


@login_required
def lesson_plan_duplicate(request, pk):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)

    duplicate_plan = LessonPlan.objects.create(
        teacher=teacher,
        subject=lesson_plan.subject,
        school_class=lesson_plan.school_class,
        week_number=lesson_plan.week_number,
        topic=f"{lesson_plan.topic} (Copy)",
        objectives=lesson_plan.objectives,
        teaching_materials=lesson_plan.teaching_materials,
        introduction=lesson_plan.introduction,
        presentation=lesson_plan.presentation,
        evaluation=lesson_plan.evaluation,
        homework=lesson_plan.homework,
    )

    messages.success(request, 'Lesson plan duplicated. You can now edit the copy.')
    return redirect('teachers:lesson_plan_edit', pk=duplicate_plan.pk)


@login_required
def lesson_plan_print(request, pk):
    is_teacher = request.user.user_type == 'teacher'
    is_admin = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    if is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)
        lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    else:
        lesson_plan = get_object_or_404(LessonPlan, pk=pk)
    
    # Check for template preference
    template_format = request.GET.get('template', 'standard')
    
    if template_format == 'b7' or template_format == 'weekly':
        template_name = 'teachers/lesson_plan_print_b7.html'
    else:
        # Default to standard GES detail view with print mode
        template_name = 'teachers/lesson_plan_detail.html'
    
    return render(request, template_name, {
        'lesson_plan': lesson_plan, 
        'print_mode': True,
        'current_template': template_format
    })

@login_required
def aura_t_api(request):
    """
    API Endpoint for Aura-T (Teacher Copilot) features.
    Handles AJAX requests for lesson plan generation, differentiation, and assignment creation.
    """
    if request.method == "POST":
        try:
            import json
            from teachers.services.aura_gen_engine import AuraGenEngine
            
            data = json.loads(request.body)
            action = data.get('action')
            
            teacher = get_object_or_404(Teacher, user=request.user)
            
            if action == 'generate_lesson':
                topic = data.get('topic')
                class_id = data.get('class_id')
                subject_id = data.get('subject_id')

                if not topic:
                    return JsonResponse({"status": "error", "message": "Topic is required"}, status=400)

                subject_name = "General Studies"
                class_name = "General"
                if subject_id:
                    from academics.models import Subject
                    subject = get_object_or_404(Subject, pk=subject_id)
                    subject_name = subject.name
                if class_id:
                    from academics.models import Class
                    school_class = get_object_or_404(Class, pk=class_id)
                    class_name = school_class.name

                result = AuraGenEngine.generate_lesson_plan(topic, subject_name, class_name)
                return JsonResponse({"status": "success", "data": result})
            elif action == 'differentiate':
                # Placeholder for differentiation logic
                return JsonResponse({
                    "status": "success", 
                    "content": "Differentiation suggestions ready"
                })

            elif action == 'generate_slides':
                topic = data.get('topic')
                class_id = data.get('class_id')
                subject_id = data.get('subject_id')

                if not topic:
                    return JsonResponse({"status": "error", "message": "Topic is required"}, status=400)

                subject_name = "General Studies"
                class_name = "General"
                if subject_id:
                    from academics.models import Subject
                    subject = get_object_or_404(Subject, pk=subject_id)
                    subject_name = subject.name
                if class_id:
                    from academics.models import Class
                    school_class = get_object_or_404(Class, pk=class_id)
                    class_name = school_class.name

                result = AuraGenEngine.generate_slides_outline(topic, subject_name, class_name)
                return JsonResponse({"status": "success", "data": result})

            elif action == 'generate_exercises':
                topic = data.get('topic')
                class_id = data.get('class_id')
                subject_id = data.get('subject_id')

                if not topic:
                    return JsonResponse({"status": "error", "message": "Topic is required"}, status=400)

                subject_name = "General Studies"
                class_name = "General"
                if subject_id:
                    from academics.models import Subject
                    subject = get_object_or_404(Subject, pk=subject_id)
                    subject_name = subject.name
                if class_id:
                    from academics.models import Class
                    school_class = get_object_or_404(Class, pk=class_id)
                    class_name = school_class.name

                result = AuraGenEngine.generate_interactive_exercises(topic, subject_name, class_name)
                return JsonResponse({"status": "success", "data": result})

            elif action == 'generate_exercises_and_assign':
                topic = data.get('topic')
                class_id = data.get('class_id')
                subject_id = data.get('subject_id')
                due_date = data.get('due_date')

                if not topic or not class_id or not subject_id:
                    return JsonResponse({"status": "error", "message": "Topic, class, and subject are required"}, status=400)

                from academics.models import Class, Subject
                from homework.models import Homework, Question, Choice
                from django.utils import timezone
                from datetime import timedelta, datetime

                school_class = get_object_or_404(Class, pk=class_id)
                subject = get_object_or_404(Subject, pk=subject_id)
                
                result = AuraGenEngine.generate_interactive_exercises(topic, subject.name, school_class.name)

                try:
                    if due_date:
                        due_date_value = datetime.strptime(due_date, '%Y-%m-%d').date()
                    else:
                        due_date_value = timezone.now().date() + timedelta(days=7)
                except ValueError:
                    due_date_value = timezone.now().date() + timedelta(days=7)

                homework = Homework.objects.create(
                    title=f"{topic} - Interactive Exercise",
                    description=f"AI-generated interactive exercise on {topic}.",
                    teacher=teacher,
                    subject=subject,
                    target_class=school_class,
                    due_date=due_date_value
                )

                exercises = result.get('exercises', [])
                if not exercises:
                    exercises = AuraGenEngine.generate_interactive_exercises(topic, subject.name, school_class.name).get('exercises', [])

                if isinstance(exercises, dict):
                    exercises = exercises.get('items', [])
                normalized_exercises = []
                for item in exercises:
                    if isinstance(item, str):
                        normalized_exercises.append({'type': 'short', 'prompt': item, 'answer': '', 'dok_level': 1})
                    elif isinstance(item, dict):
                        if not item.get('prompt') and item.get('question'):
                            item['prompt'] = item.get('question')
                        normalized_exercises.append(item)
                exercises = normalized_exercises

                if len(exercises) < 5:
                    fallback = AuraGenEngine._mock_exercises(topic)
                    exercises = (exercises + fallback)[:5]
                elif len(exercises) > 10:
                    exercises = exercises[:10]

                type_map = {
                    'multiple_choice': 'mcq',
                    'multiple choice': 'mcq',
                    'mcq': 'mcq',
                    'quiz': 'mcq',
                    'short_answer': 'short',
                    'short answer': 'short',
                    'short': 'short',
                }
                questions_created = 0
                for item in exercises:
                    raw_type = (item.get('type') or '').lower()
                    ex_type = type_map.get(raw_type, raw_type or 'short')
                    prompt = item.get('prompt') or 'Untitled question'
                    dok_level = item.get('dok_level')
                    try:
                        dok_level = int(dok_level)
                    except (TypeError, ValueError):
                        dok_level = 1
                    if dok_level not in [1, 2, 3, 4]:
                        dok_level = 1
                    if ex_type not in ['mcq', 'short']:
                        ex_type = 'short'

                    question = Question.objects.create(
                        homework=homework,
                        text=prompt,
                        points=1,
                        question_type=ex_type,
                        dok_level=dok_level,
                        correct_answer=item.get('answer', '')
                    )
                    questions_created += 1

                    if ex_type == 'mcq':
                        options = item.get('options') or []
                        correct = item.get('answer')
                        if not options and correct:
                            options = [
                                str(correct),
                                'Option B',
                                'Option C',
                                'Option D'
                            ]

                        if not options:
                            options = ['Option A', 'Option B', 'Option C', 'Option D']

                        def normalize_text(value):
                            return str(value or '').strip().lower()

                        correct_norm = normalize_text(correct)
                        correct_index = None
                        label_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
                        if correct_norm in label_map:
                            correct_index = label_map[correct_norm]
                        elif correct_norm.isdigit():
                            idx = int(correct_norm) - 1
                            if 0 <= idx < len(options):
                                correct_index = idx

                        has_correct = False
                        for idx, opt in enumerate(options):
                            opt_norm = normalize_text(opt)
                            is_correct = False

                            if correct_index is not None and idx == correct_index:
                                is_correct = True
                            elif correct_norm and opt_norm == correct_norm:
                                is_correct = True

                            if is_correct:
                                has_correct = True

                            Choice.objects.create(
                                question=question,
                                text=opt,
                                is_correct=is_correct
                            )

                        if not has_correct:
                            first_choice = question.choices.first()
                            if first_choice:
                                first_choice.is_correct = True
                                first_choice.save(update_fields=['is_correct'])

                return JsonResponse({
                    "status": "success",
                    "data": {
                        "homework_id": homework.id,
                        "homework_title": homework.title,
                        "questions_created": questions_created
                    }
                })
            
            elif action == 'generate_assignment':
                lesson_id = data.get('lesson_id')
                topic = data.get('topic')
                
                if lesson_id:
                    lesson_plan = get_object_or_404(LessonPlan, pk=lesson_id, teacher=teacher)
                    result = AuraGenEngine.generate_assignment_package(lesson_plan)
                elif topic and data.get('class_id'):
                    # Create a temporary lesson object for the engine if topic is provided manually
                    # This is a simplified path
                    from academics.models import Class, Subject
                    school_class = get_object_or_404(Class, pk=data.get('class_id'))
                    subject = get_object_or_404(Subject, pk=data.get('subject_id')) # Assuming subject passed
                    
                    # Mock lesson plan for the engine
                    mock_lesson = LessonPlan(
                        teacher=teacher,
                        subject=subject,
                        school_class=school_class,
                        topic=topic,
                        objectives=f"Understand {topic}",
                        week_number=1 # Dummy
                    )
                    result = AuraGenEngine.generate_assignment_package(mock_lesson, topic_prompt=topic)
                else:
                    return JsonResponse({"status": "error", "message": "Missing lesson_id or topic/class_id"}, status=400)
                
                return JsonResponse({
                    "status": "success", 
                    "data": result
                })

            elif action == 'save_assignment_package':
                from homework.models import Homework as HW
                from academics.models import Class, Subject
                from datetime import datetime, timedelta
                from django.utils import timezone as tz

                title        = data.get('title', '').strip() or 'AI Generated Assignment'
                description  = data.get('description', '').strip() or ''
                class_id     = data.get('class_id')
                subject_id   = data.get('subject_id')
                due_date_str = data.get('due_date', '')

                if not class_id or not subject_id:
                    return JsonResponse({"status": "error", "message": "Class and subject are required."}, status=400)

                school_class = get_object_or_404(Class, pk=class_id)
                subject      = get_object_or_404(Subject, pk=subject_id)

                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    due_date = tz.now().date() + timedelta(days=7)

                hw = HW.objects.create(
                    title=title,
                    description=description,
                    teacher=teacher,
                    subject=subject,
                    target_class=school_class,
                    due_date=due_date,
                )

                # Persist AI-generated questions as Question objects
                from homework.models import Question as HWQuestion
                questions_payload = data.get('questions', [])
                if isinstance(questions_payload, list):
                    for i, q_text in enumerate(questions_payload):
                        if isinstance(q_text, str) and q_text.strip():
                            HWQuestion.objects.create(
                                homework=hw,
                                text=q_text.strip(),
                                question_type='short',
                                dok_level=1,
                                points=1,
                            )

                schema = request.tenant.schema_name
                return JsonResponse({
                    "status": "success",
                    "homework_id": hw.pk,
                    "redirect_url": f"/{schema}/homework/{hw.pk}/",
                })

            elif action == 'regenerate':
                import re as _re
                plan_id = data.get('plan_id')
                if not plan_id:
                    return JsonResponse({"status": "error", "message": "plan_id required"}, status=400)

                regen_plan = get_object_or_404(LessonPlan, pk=plan_id, teacher=teacher)
                topic_r = regen_plan.topic
                subject_r = regen_plan.subject.name if regen_plan.subject else "General Studies"
                class_r = regen_plan.school_class.name if regen_plan.school_class else "General"

                regen_result = AuraGenEngine.generate_lesson_plan(topic_r, subject_r, class_r)
                lesson_body = (regen_result.get('lesson_plan') or '').strip()
                if not lesson_body:
                    return JsonResponse({"status": "error",
                                         "message": regen_result.get('error', 'Generation failed')}, status=500)

                def _extract_r(header, text):
                    pat = _re.compile(
                        rf"\*\*{_re.escape(header)}.*?\*\*\s*(.*?)(?=\n\*\*|\Z)",
                        _re.DOTALL | _re.IGNORECASE
                    )
                    m = pat.search(text)
                    return m.group(1).strip() if m else ''

                regen_plan.objectives = (
                    _extract_r('Content Standard', lesson_body) + '\n' +
                    _extract_r('Indicator', lesson_body)
                ).strip() or regen_plan.objectives
                regen_plan.introduction = _extract_r('PHASE 1: STARTER', lesson_body) or regen_plan.introduction
                regen_plan.presentation = (
                    _extract_r('PHASE 2: NEW LEARNING', lesson_body) or
                    _extract_r('PHASE 2', lesson_body) or
                    regen_plan.presentation
                )
                regen_plan.evaluation = (
                    _extract_r('PHASE 3: REFLECTION', lesson_body) or
                    _extract_r('Assessment', lesson_body) or
                    regen_plan.evaluation
                )
                hw_new = _extract_r('Homework', lesson_body)
                if hw_new:
                    regen_plan.homework = hw_new
                regen_plan.save()

                return JsonResponse({
                    "status": "success",
                    "message": "Lesson plan upgraded to Aura-T v3.",
                    "plan_id": regen_plan.pk,
                })

            return JsonResponse({"status": "error", "message": "Unknown action"}, status=400)
            
        except Exception as e:
            return _ai_json_error_response(e)
            
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@login_required
@login_required
def aura_command_center(request):
    """
    Aura-T Command Center: overview of all lesson plans with per-plan
    Aura-T feature badges (Pulse Check / Checkpoints / Mastery Sprint / Insight).
    """
    is_teacher = request.user.user_type == 'teacher'
    is_admin   = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = None
    if is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)

    plans_qs = LessonPlan.objects.select_related('subject', 'school_class', 'teacher', 'teacher__user')
    if is_teacher:
        plans_qs = plans_qs.filter(teacher=teacher)
    plans = list(plans_qs)

    for p in plans:
        intro = p.introduction or ''
        pres  = p.presentation or ''
        evl   = p.evaluation or ''
        p.has_pulse       = 'PULSE CHECK' in intro
        p.has_checkpoints = 'CHECKPOINT QUESTIONS' in pres or 'CQ1:' in pres
        p.has_sprint      = 'MASTERY SPRINT' in evl or 'MS1:' in evl
        p.has_insight     = 'TEACHER INSIGHT' in evl
        p.aura_score      = sum([p.has_pulse, p.has_checkpoints, p.has_sprint, p.has_insight])
        p.teacher_name    = p.teacher.user.get_full_name() if p.teacher and p.teacher.user else 'Unknown'
        p.pulse_count     = 0
        p.has_active_pulse = False

    # ── Per-plan pulse session counts & active detection ──────────────────
    try:
        from academics.pulse_models import PulseSession
        plan_pks = [p.pk for p in plans]
        pulse_counts  = {}
        active_pk_set = set()
        for row in PulseSession.objects.filter(lesson_plan_id__in=plan_pks).values('lesson_plan_id', 'status'):
            lpk = row['lesson_plan_id']
            pulse_counts[lpk] = pulse_counts.get(lpk, 0) + 1
            if row['status'] == 'active':
                active_pk_set.add(lpk)
        for p in plans:
            p.pulse_count      = pulse_counts.get(p.pk, 0)
            p.has_active_pulse = p.pk in active_pk_set
    except Exception:
        pass

    total         = len(plans)
    v3_ready      = sum(1 for p in plans if p.aura_score == 4)
    partial_count = sum(1 for p in plans if 0 < p.aura_score < 4)
    no_aura_count = sum(1 for p in plans if p.aura_score == 0)
    v3_pct        = round(v3_ready / total * 100) if total else 0

    # Filter dropdown options
    subjects = sorted(set(p.subject.name for p in plans if p.subject))
    classes  = sorted(set(p.school_class.name for p in plans if p.school_class))

    # Admin: sort by teacher name then score; teacher: sort by score desc
    if is_admin:
        plans.sort(key=lambda p: (p.teacher_name, -p.aura_score, -p.pk))
        prev_tname = None
        for p in plans:
            p.teacher_changed = p.teacher_name != prev_tname
            prev_tname = p.teacher_name
    else:
        plans.sort(key=lambda p: (-p.aura_score, -p.pk))
        for p in plans:
            p.teacher_changed = False

    return render(request, 'teachers/aura_command_center.html', {
        'plans':         plans,
        'total':         total,
        'v3_ready':      v3_ready,
        'v3_pct':        v3_pct,
        'partial_count': partial_count,
        'no_aura_count': no_aura_count,
        'is_teacher':    is_teacher,
        'is_admin':      is_admin,
        'teacher':       teacher,
        'subjects':      subjects,
        'classes':       classes,
    })


@login_required
def aura_flight_manual(request):
    """
    Aura-T Teacher Flight Manual — quick-start guide for the AI-integrated lesson.
    """
    is_teacher = request.user.user_type == 'teacher'
    is_admin   = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    return render(request, 'teachers/aura_flight_manual.html', {
        'is_teacher': is_teacher,
        'is_admin': is_admin,
    })


@login_required
def lesson_plan_cards_print(request, pk):
    """
    Printable Student Nuggets + Mastery Sprint cards for a lesson plan.
    Cut-and-distribute format: support card | extension card, then exit ticket strip.
    """
    is_teacher = request.user.user_type == 'teacher'
    is_admin   = request.user.user_type == 'admin'
    if not is_teacher and not is_admin:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    if is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)
        lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    else:
        lesson_plan = get_object_or_404(LessonPlan, pk=pk)

    return render(request, 'teachers/lesson_plan_cards_print.html', {
        'lesson_plan': lesson_plan,
    })


@login_required
def lesson_plan_delete(request, pk):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    
    if request.method == 'POST':
        lesson_plan.delete()
        messages.success(request, 'Lesson plan deleted successfully.')
        return redirect('teachers:lesson_plan_list')
        
    return render(request, 'teachers/lesson_plan_confirm_delete.html', {'lesson_plan': lesson_plan})

@login_required
def add_teacher(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            if not employee_id:
                # Auto-generate Employee ID (TCHR + 4 Digits)
                import random
                import string
                while True:
                    suffix = ''.join(random.choices(string.digits, k=4))
                    employee_id = f"TCHR{suffix}"
                    if not Teacher.objects.filter(employee_id=employee_id).exists() and not User.objects.filter(username=employee_id).exists():
                        break

            username = employee_id
            if User.objects.filter(username=username).exists():
                messages.error(request, f"User {username} already exists")
                return render(request, 'teachers/add_teacher.html', {'form': form})
                
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=username,  # Default password is employee ID
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                user_type='teacher',
                phone=form.cleaned_data.get('phone', '')
            )
            
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.employee_id = employee_id # Ensure it's set
            teacher.save()
            form.save_m2m() # Save subjects
            messages.success(request, f"Teacher {user.get_full_name()} added successfully with Employee ID: {employee_id}")
            return redirect('teachers:teacher_list')
    else:
        form = TeacherCreateForm()
        
    return render(request, 'teachers/add_teacher.html', {'form': form})


# =====================
# ID CARD GENERATION
# =====================

@login_required
def teacher_id_card(request, teacher_id):
    """Generate and download teacher ID card (PNG)"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Permission check
    if request.user.user_type == 'teacher':
        teacher_profile = get_object_or_404(Teacher, user=request.user)
        if teacher_profile.id != teacher_id:
            messages.error(request, 'You can only download your own ID card')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Generate card
    try:
        card = generate_teacher_id_card(teacher)
        
        # Return as PNG
        response = HttpResponse(content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="teacher_id_{teacher.id}.png"'
        card.save(response, 'PNG')
        return response
    except Exception as e:
        messages.error(request, f'Error generating ID card: {str(e)}')
        return redirect('dashboard')


@login_required
def teacher_id_card_pdf(request, teacher_id):
    """Generate and download teacher ID card (PDF)"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Permission check
    if request.user.user_type == 'teacher':
        teacher_profile = get_object_or_404(Teacher, user=request.user)
        if teacher_profile.id != teacher_id:
            messages.error(request, 'You can only download your own ID card')
            return redirect('dashboard')
    elif request.user.user_type not in ['admin']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Generate card and convert to PDF
    try:
        card = generate_teacher_id_card(teacher)
        pdf_buffer = export_id_card_to_pdf(card)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="teacher_id_{teacher.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating ID card: {str(e)}')
        return redirect('dashboard')


@login_required
def bulk_teacher_id_cards_pdf(request):
    """Generate bulk ID cards for all teachers (PDF)"""
    if request.user.user_type not in ['admin']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Get parameters
    teacher_ids = request.GET.get('ids', '').split(',')
    teacher_ids = [tid.strip() for tid in teacher_ids if tid.strip()]
    
    try:
        if teacher_ids:
            teachers = Teacher.objects.filter(id__in=teacher_ids).select_related('user')
        else:
            teachers = Teacher.objects.all().select_related('user')
        
        if not teachers.exists():
            messages.error(request, 'No teachers found')
            return redirect('teachers:teacher_list')
        
        # Generate cards
        card_list = []
        for teacher in teachers:
            try:
                card = generate_teacher_id_card(teacher)
                card_list.append((teacher.user.get_full_name(), card))
            except Exception:
                pass  # Skip teachers with errors
        
        if not card_list:
            messages.error(request, 'Could not generate any ID cards')
            return redirect('teachers:teacher_list')
        
        # Export to PDF
        pdf_buffer = export_multiple_id_cards_to_pdf(card_list)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="teacher_ids_all.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating ID cards: {str(e)}')
        return redirect('teachers:teacher_list')


import json
from django.views.decorators.http import require_POST
from communication.models import Conversation, Message
from parents.models import Parent


# ─── Power Words — Teacher Command Center ──────────────────────────────────

@login_required
def power_words_dashboard(request):
    """
    Teacher Command Center: per-student Power Word clouds, weekly growth,
    Aura-T academic verb trend insights, and one-click action buttons.

    Access: teacher (own classes) or admin (all classes).
    """
    if request.user.user_type not in ['teacher', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from collections import defaultdict
    from academics.tutor_models import PowerWord
    from django.utils import timezone as tz

    teacher = None
    if request.user.user_type == 'teacher':
        teacher = Teacher.objects.filter(user=request.user).first()

    # ── Select class ────────────────────────────────────────────────
    if teacher:
        classes = Class.objects.filter(classsubject__teacher=teacher).distinct().order_by('name')
    else:
        classes = Class.objects.all().order_by('name')

    class_id = request.GET.get('class_id')
    selected_class = None
    if class_id:
        selected_class = get_object_or_404(Class, id=class_id)
    elif classes.exists():
        selected_class = classes.first()

    # ── Derive week numbers for "this week" and "last week" ──────────
    now = tz.now()
    iso = now.isocalendar()
    current_year, current_week = iso[0], iso[1]
    last_week = current_week - 1 if current_week > 1 else 52
    last_week_year = current_year if current_week > 1 else current_year - 1

    # ── Academic verbs to detect in Power Words ──────────────────────
    ACADEMIC_VERBS = {
        'analyze', 'analyse', 'compare', 'evaluate', 'synthesize', 'synthesise',
        'describe', 'explain', 'justify', 'identify', 'classify', 'predict',
        'infer', 'conclude', 'hypothesize', 'hypothesise', 'illustrate',
        'summarize', 'summarise', 'argue', 'debate', 'interpret', 'calculate',
        'demonstrate', 'apply', 'construct', 'define', 'distinguish',
    }

    student_cards = []

    if selected_class:
        students = Student.objects.filter(
            current_class=selected_class
        ).select_related('user').order_by('user__last_name', 'user__first_name')

        # Bulk-fetch Power Words for all students in the class
        all_words = PowerWord.objects.filter(
            student__in=students
        ).select_related('student').order_by('-last_heard')

        # Group by student
        words_by_student = defaultdict(list)
        for pw in all_words:
            words_by_student[pw.student_id].append(pw)

        for student in students:
            student_words = words_by_student.get(student.id, [])

            # This-week and last-week splits
            this_week_words = [
                w for w in student_words
                if w.year == current_year and w.week == current_week
            ]
            last_week_words = [
                w for w in student_words
                if w.year == last_week_year and w.week == last_week
            ]

            # Academic verb percentage (this week vs last week)
            def verb_pct(word_list):
                if not word_list:
                    return 0
                verbs = sum(1 for w in word_list if w.word.lower() in ACADEMIC_VERBS)
                return round(verbs / len(word_list) * 100)

            verb_pct_this = verb_pct(this_week_words)
            verb_pct_last = verb_pct(last_week_words)
            verb_delta = verb_pct_this - verb_pct_last

            # Aura-T insight string
            aura_insight = None
            all_historical_verbs = sum(1 for w in student_words if w.word.lower() in ACADEMIC_VERBS)
            total = len(student_words)
            if total >= 3:
                overall_verb_pct = round(all_historical_verbs / total * 100)
                if verb_delta > 10:
                    aura_insight = (
                        f"{student.user.first_name} is using academic verbs (Analyze, Compare) "
                        f"{verb_delta}% more often than last week."
                    )
                elif verb_delta < -10:
                    aura_insight = (
                        f"{student.user.first_name}'s academic verb usage dropped {abs(verb_delta)}% "
                        "this week — may need a vocabulary review."
                    )
                elif overall_verb_pct >= 30:
                    aura_insight = (
                        f"{student.user.first_name} consistently uses academic verbs in {overall_verb_pct}% "
                        "of Power Words — strong academic language command!"
                    )

            # Word cloud: (word, font_size) pairs sized by used_count
            max_count = max((w.used_count for w in student_words), default=1)
            word_cloud = [
                {
                    'word': w.word.title(),
                    'used_count': w.used_count,
                    'subject': w.subject,
                    'font_size': max(12, min(32, int(12 + (w.used_count / max_count) * 20))),
                    'is_verb': w.word.lower() in ACADEMIC_VERBS,
                    'session_type': w.session_type,
                }
                for w in student_words[:30]  # cap at 30 for display
            ]

            student_cards.append({
                'student': student,
                'total_words': total,
                'new_this_week': len(this_week_words),
                'new_this_week_list': [w.word.title() for w in this_week_words[:8]],
                'verb_pct_this': verb_pct_this,
                'verb_delta': verb_delta,
                'aura_insight': aura_insight,
                'word_cloud': word_cloud,
            })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'student_cards': student_cards,
        'current_week': current_week,
        'current_year': current_year,
    }
    return render(request, 'teachers/power_words_dashboard.html', context)


@require_POST
@login_required
def power_words_action(request):
    """
    Handle teacher actions on the Power Words dashboard:
      - send_congratulations: Creates an in-app notification for the student.
      - add_to_report:         Flags the student's top Power Words for term report.
    """
    if request.user.user_type not in ['teacher', 'admin']:
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = body.get('action')
    student_id = body.get('student_id')

    if not action or not student_id:
        return JsonResponse({'error': 'action and student_id required'}, status=400)

    try:
        student = Student.objects.select_related('user').get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)

    from academics.tutor_models import PowerWord
    from django.utils import timezone as tz
    from announcements.models import Notification

    if action == 'send_congratulations':
        # Build uplifting note based on top 3 recent words
        recent_words = PowerWord.objects.filter(student=student).order_by('-last_heard')[:3]
        word_list = ', '.join(w.word.title() for w in recent_words) if recent_words else 'your Power Words'
        teacher_name = request.user.get_full_name() or request.user.username
        msg = (
            f"🌟 Great work, {student.user.first_name}! "
            f"{teacher_name} noticed you've been mastering academic vocabulary: "
            f"{word_list}. Keep it up!"
        )
        try:
            Notification.objects.create(
                recipient=student.user,
                message=msg,
                alert_type='general',
            )
            return JsonResponse({'status': 'ok', 'message': 'Congratulations note sent!'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif action == 'add_to_report':
        # Mark recent Power Words as confirmed by teacher so they appear in reports
        try:
            from django.utils import timezone as tz
            iso = tz.now().isocalendar()
            updated = PowerWord.objects.filter(
                student=student,
                year=iso[0],
                week=iso[1],
            ).update(confirmed_by_teacher=True)
            return JsonResponse({
                'status': 'ok',
                'message': f"{updated} Power Word(s) flagged for term report.",
                'count': updated,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': f"Unknown action: {action}"}, status=400)


@require_POST
@login_required
def boost_intervention(request):
    """
    AJAX endpoint to trigger an AI intervention 'Boost'.
    1. Creates a remedial assignment (ClassExercise)
    2. Notifies the parent via internal message system
    """
    if request.user.user_type != 'teacher':
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        intervention_text = data.get('interventionText')

        student = get_object_or_404(Student, id=student_id)
        # Note: request.user might not be Teacher instance directly, but user linked to Teacher
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Teacher profile not found'}, status=404)
        
        # 1. Assign Remedial Task
        # Find a subject this teacher teaches to this student
        # We look for a ClassSubject where teacher=teacher and class_name=student.current_class
        class_subject = ClassSubject.objects.filter(
            teacher=teacher, 
            class_name=student.current_class
        ).first()

        log_message = []
        
        if class_subject:
            # Create a specialized ClassExercise
            exercise = ClassExercise.objects.create(
                class_subject=class_subject,
                title=f"Boost: {intervention_text[:20]}...",
                description=f"AI-suggested intervention: {intervention_text}",
                max_marks=10,
                term='first' # Defaulting to first term
            )
            # Assign score entry (initializes it for student)
            StudentExerciseScore.objects.create(
                student=student,
                exercise=exercise,
                score=0,
                remarks="Assigned via AI Boost"
            )
            log_message.append(f"Assigned '{exercise.title}' in {class_subject.subject.name}")
        else:
            log_message.append("No class subject found to assign work")

        # 2. Notify Parent
        # Student -> Parents (ManyToMany)
        # We pick the first one
        parent = student.parents.first() # Using related_name='parents' from Parent model? 
        # Wait, Parent model has: children = models.ManyToManyField('students.Student', related_name='parents')
        # So yes, student.parents.all() returns QuerySet of Parent objects.
        
        if parent:
            parent_user = parent.user
            # Create or get conversation
            # Using specific method from Conversation model or get_or_create
            conversation, created = Conversation.get_or_create_between(request.user, parent_user)
            
            msg_content = (
                f"Dear {parent_user.last_name}, we noticed {student.user.first_name} could use a little extra help with "
                f"'{intervention_text}'. I've assigned a short practice module (Boost) to support them. "
                f"Please encourage them to complete it effectively. Thanks!"
            )
            
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=msg_content
            )
            log_message.append(f"Notified {parent_user.get_full_name()}")
        else:
            log_message.append("No parent linked for notification")

        return JsonResponse({
            'status': 'success', 
            'message': f"Intervention deployed! {'. '.join(log_message)}."
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==========================================
# AI Chat Sessions
# ==========================================

from django.http import JsonResponse
from django.conf import settings
import json

@login_required
def ai_sessions_list(request):
    """
    Aura-T Command Centre:
    Displays AI Copilot sessions, actively scheduled class (or next one),
    and a matrix of students with (simulated) real-time engagement status.
    """
    if not hasattr(request.user, 'teacher'):
         messages.error(request, "Access restricted to teachers.")
         return redirect('dashboard')
         
    teacher = request.user.teacher
    sessions = LessonGenerationSession.objects.filter(teacher=teacher).order_by('-updated_at')
    
    # --- REDESIGN: REAL DATA INJECTION ---
    from datetime import datetime
    now = datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    current_time = now.time()
    
    # 1. Fetch Next Active Class
    # Query: Find classes for this teacher today that haven't ended yet
    next_class_session = Timetable.objects.filter(
        class_subject__teacher=teacher,
        day=weekday,
        end_time__gte=current_time
    ).select_related('class_subject__class_name', 'class_subject__subject').order_by('start_time').first()
    
    # 2. Determine Scope Context (Which class to show in matrix?)
    active_class = None
    if next_class_session:
        active_class = next_class_session.class_subject.class_name
    elif teacher.managed_classes.exists():
        # Fallback to the first class they manage (e.g. homeroom)
        active_class = teacher.managed_classes.first()
    else:
        # Fallback to any class they teach
        first_subject = ClassSubject.objects.filter(teacher=teacher).select_related('class_name').first()
        if first_subject:
            active_class = first_subject.class_name
            
    # 3. Build Student Matrix Data
    student_data = []
    struggling_count = 0
    total_students = 0

    if active_class:
        # Get up to 40 students for the visualization grid
        students = list(Student.objects.filter(current_class=active_class).select_related('user')[:40])
        student_ids = [s.id for s in students]
        total_students = len(students)

        # Real engagement: query today's TutorSession activity
        from datetime import date as _date
        today = _date.today()
        active_today_ids = set(
            TutorSession.objects.filter(
                student_id__in=student_ids,
                started_at__date=today
            ).values_list('student_id', flat=True)
        )
        # Recent sessions (last 3 days) for "idle" — logged in but not today
        recent_ids = set(
            TutorSession.objects.filter(
                student_id__in=student_ids,
                started_at__date__gte=today - timezone.timedelta(days=3)
            ).values_list('student_id', flat=True)
        ) - active_today_ids

        # Struggling: students with last session showing low engagement (msg_count < 4)
        struggling_set = set(
            TutorSession.objects.filter(
                student_id__in=student_ids,
                message_count__lt=4,
                started_at__date=today
            ).values_list('student_id', flat=True)
        )

        # Latest session ID per student (for "peek" link)
        latest_sessions = {}
        for ts in TutorSession.objects.filter(
            student_id__in=student_ids
        ).order_by('student_id', '-started_at').distinct('student_id').values('student_id', 'id'):
            latest_sessions[ts['student_id']] = ts['id']

        for s in students:
            if s.id in struggling_set:
                status = 'struggling'
                struggling_count += 1
            elif s.id in active_today_ids:
                status = 'active'
            elif s.id in recent_ids:
                status = 'idle'
            else:
                status = 'offline'

            student_data.append({
                'id': s.id,
                'name': s.user.get_full_name() or s.user.username,
                'status': status,
                'tooltip': f"{s.admission_number} | {status.title()}",
                'latest_session_id': latest_sessions.get(s.id),
            })
    
    from academics.ai_tutor import get_openai_chat_model

    active_ai_model = get_openai_chat_model()

    context = {
        'sessions': sessions,
        'next_class': next_class_session,
        'active_class': active_class,
        'student_data': student_data,
        'struggling_count': struggling_count,
        'student_count': total_students,
        'current_time': now,
        'active_ai_model': active_ai_model,
    }
    return render(request, 'teachers/ai_sessions_list.html', context)

@login_required
def ai_session_new(request):
    if not hasattr(request.user, 'teacher'):
         return redirect('dashboard')
    
    teacher = request.user.teacher
    session = LessonGenerationSession.objects.create(teacher=teacher)
    return redirect('teachers:ai_session_detail', session_id=session.id)

@login_required
def ai_session_detail(request, session_id):
    if not hasattr(request.user, 'teacher'):
         return redirect('dashboard')
         
    teacher = request.user.teacher
    session = get_object_or_404(LessonGenerationSession, id=session_id, teacher=teacher)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            
            if user_message:
                messages_list = list(session.messages)
                messages_list.append({"role": "user", "content": user_message})
                session.messages = messages_list
                session.save()
                
                from academics.ai_tutor import _post_chat_completion, get_openai_chat_model
                api_key = settings.OPENAI_API_KEY
                
                system_prompt = """You are an expert lesson planner for teachers. Help them create detailed, engaging lesson plans.
When generating a lesson plan, ALWAYS structure your output to exactly match this template (do not include markdown tables, strictly use this vertical text format with bold headings):

[School Name] [Phone Numbers]
**TERM:** [Term]
**WEEKLY LESSON PLAN – [Class Name]**
**WEEK:** [Week Number]

**Week Ending:** [Date]
**DAY:** [Day of week]
**Subject:** [Subject]
**Duration:** [Duration in minutes]
**Strand:** [Strand description]
**Sub Strand:** [Sub strand description]
**Class:** [Class Name]
**Class Size:** [Number]

**Content Standard:** 
[Details here]

**Indicator:** 
[Details here]

**Lesson:** 
[Lesson Number/Total]

**Performance Indicator:** 
[Details here]

**Core Competencies:** 
[Details here]

**Key words:** 
[Keywords here]

**Reference:** 
[Reference book or curriculum link]

**Phase/Duration** | **Learners Activities** | **Resources**

**PHASE 1: STARTER [Time]**
[Provide starter activity details here...]

**PHASE 2: NEW LEARNING [Time]**
[Provide main teaching activity details here...]

**PHASE 3: REFLECTION [Time]**
[Provide reflection and summary details here...]"""
                api_msgs = [{"role": "system", "content": system_prompt}] + messages_list
                
                payload = {
                    "model": get_openai_chat_model(),
                    "messages": api_msgs,
                    "temperature": 0.7
                }
                
                response_data = _post_chat_completion(payload, api_key)
                
                if "error" in response_data:
                    raise Exception(response_data["error"].get("message", "API Error"))
                    
                ai_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                messages_list.append({"role": "assistant", "content": ai_content})
                session.messages = messages_list
                
                if session.title == "New Session" and len(messages_list) >= 2:
                    try:
                        title_payload = {
                            "model": get_openai_chat_model(),
                            "messages": api_msgs + [{"role": "user", "content": "Suggest a short 3-5 word title for this chat."}],
                            "max_tokens": 15
                        }
                        title_resp = _post_chat_completion(title_payload, api_key)
                        new_title = title_resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip().strip('"')
                        if new_title:
                            session.title = new_title
                    except Exception:
                        pass
                
                session.save()
                return JsonResponse({'status': 'success', 'reply': ai_content, 'title': session.title})
        except Exception as e:
            return _ai_json_error_response(e)
    
    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
    classes = sorted(list(set(cs.class_name for cs in class_subjects)), key=lambda c: c.name)
    subjects = sorted(list(set(cs.subject for cs in class_subjects)), key=lambda s: s.name)

    return render(request, 'teachers/ai_session_detail.html', {
        'session': session,
        'classes': classes,
        'subjects': subjects,
    })

@login_required
def ai_session_rename(request, session_id):
    if request.method == 'POST':
        teacher = request.user.teacher
        session = get_object_or_404(LessonGenerationSession, id=session_id, teacher=teacher)
        new_title = request.POST.get('title')
        if new_title:
            session.title = new_title
            session.save()
            messages.success(request, "Session renamed.")
    return redirect('teachers:ai_sessions_list')

@login_required
def ai_session_delete(request, session_id):
    teacher = request.user.teacher
    session = get_object_or_404(LessonGenerationSession, id=session_id, teacher=teacher)
    session.delete()
    messages.success(request, "Session deleted.")
    return redirect('teachers:ai_sessions_list')

@login_required
def assignment_creator(request):
    """
    View for Aura-T Assignment Creator Interface.
    Allows teachers to generate assignments, differentiation, and rubrics.
    """
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    recent_lessons = LessonPlan.objects.filter(teacher=teacher).order_by('-date_added')[:5]
    
    # Get classes and subjects for manual entry
    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
    classes = sorted(list(set(cs.class_name for cs in class_subjects)), key=lambda c: c.name)
    subjects = sorted(list(set(cs.subject for cs in class_subjects)), key=lambda s: s.name)
    
    return render(request, 'teachers/assignment_creator.html', {
        'recent_lessons': recent_lessons,
        'classes': classes,
        'subjects': subjects
    })


# ─────────────────────────────────────────────────────────────
# SCHEME OF WORK — upload, list, delete
# ─────────────────────────────────────────────────────────────

@login_required
def scheme_of_work_list(request):
    """List all schemes of work for the logged-in teacher."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, user=request.user)
    current_year = AcademicYear.objects.filter(is_current=True).first()

    class_subjects = ClassSubject.objects.filter(
        teacher=teacher,
        class_name__academic_year=current_year
    ).select_related('class_name', 'subject') if current_year else ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')

    schemes = SchemeOfWork.objects.filter(
        class_subject__in=class_subjects
    ).select_related('class_subject__class_name', 'class_subject__subject', 'academic_year').order_by('-uploaded_at')

    return render(request, 'teachers/scheme_of_work.html', {
        'schemes': schemes,
        'class_subjects': class_subjects,
        'current_year': current_year,
    })


@login_required
def scheme_of_work_upload(request):
    """Upload or replace a scheme of work for a class/subject/term."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, user=request.user)
    current_year = AcademicYear.objects.filter(is_current=True).first()

    if not current_year:
        messages.error(request, 'No active academic year found.')
        return redirect('teachers:scheme_of_work_list')

    class_subjects = ClassSubject.objects.filter(
        teacher=teacher, class_name__academic_year=current_year
    ).select_related('class_name', 'subject')

    if request.method == 'POST':
        cs_id = request.POST.get('class_subject')
        term = request.POST.get('term')
        image = request.FILES.get('image')

        if not cs_id or not term or not image:
            messages.error(request, 'Please fill all fields and upload an image.')
        else:
            cs = get_object_or_404(ClassSubject, id=cs_id, teacher=teacher)

            # Upsert — one scheme per class/subject/term/year
            scheme, created = SchemeOfWork.objects.get_or_create(
                class_subject=cs,
                term=term,
                academic_year=current_year,
                defaults={'uploaded_by': teacher, 'image': image, 'extracted_topics': '[]'},
            )
            if not created:
                # Replace image
                scheme.image = image
                scheme.extracted_topics = '[]'
                scheme.uploaded_by = teacher
                scheme.save()

            # Extract topics using GPT-4 Vision (async-style: do it inline for simplicity)
            try:
                from academics.ai_tutor import extract_scheme_of_work_topics
                # Use absolute path for local storage; fall back to URL for remote
                # backends (Cloudinary etc.) that don't support .path
                try:
                    image_ref = scheme.image.path
                except (NotImplementedError, AttributeError, ValueError):
                    image_ref = scheme.image.url
                topics = extract_scheme_of_work_topics(image_ref)
                import json
                scheme.extracted_topics = json.dumps(topics)
                scheme.save(update_fields=['extracted_topics'])
                topic_count = len(topics)
                if topic_count > 0:
                    messages.success(request, f'Scheme of work uploaded! {topic_count} topics extracted for Aura.')
                else:
                    messages.warning(request, 'Scheme uploaded but Aura could not extract topics from the image. You can re-upload a clearer image.')
            except Exception as exc:
                messages.warning(request, f'Scheme saved but topic extraction failed: {exc}')

            return redirect('teachers:scheme_of_work_list')

    return render(request, 'teachers/scheme_of_work_upload.html', {
        'class_subjects': class_subjects,
        'term_choices': SchemeOfWork.TERM_CHOICES,
    })


@login_required
def scheme_of_work_delete(request, pk):
    """Delete a scheme of work."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, user=request.user)
    scheme = get_object_or_404(
        SchemeOfWork,
        pk=pk,
        class_subject__teacher=teacher
    )
    scheme.delete()
    messages.success(request, 'Scheme of work deleted.')
    return redirect('teachers:scheme_of_work_list')


@login_required
@require_POST
def scheme_of_work_update_topics(request, pk):
    """AJAX: replace extracted_topics list for a scheme."""
    if request.user.user_type not in ['admin', 'teacher']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    teacher = get_object_or_404(Teacher, user=request.user)
    scheme = get_object_or_404(SchemeOfWork, pk=pk, class_subject__teacher=teacher)
    try:
        payload = json.loads(request.body)
        topics = payload.get('topics', [])
        if not isinstance(topics, list):
            raise ValueError('topics must be a list')
        topics = [str(t).strip() for t in topics if str(t).strip()]
        scheme.extracted_topics = json.dumps(topics)
        scheme.save(update_fields=['extracted_topics'])
        return JsonResponse({'ok': True, 'count': len(topics)})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=400)


@login_required
@require_POST
def scheme_of_work_reextract(request, pk):
    """Re-run GPT-4o Vision extraction on the stored image."""
    if request.user.user_type not in ['admin', 'teacher']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    teacher = get_object_or_404(Teacher, user=request.user)
    scheme = get_object_or_404(SchemeOfWork, pk=pk, class_subject__teacher=teacher)
    try:
        from academics.ai_tutor import extract_scheme_of_work_topics
        try:
            image_ref = scheme.image.path
        except (NotImplementedError, AttributeError, ValueError):
            image_ref = scheme.image.url
        topics = extract_scheme_of_work_topics(image_ref)
        scheme.extracted_topics = json.dumps(topics)
        scheme.save(update_fields=['extracted_topics'])
        return JsonResponse({'ok': True, 'count': len(topics), 'topics': topics})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


@login_required
@require_POST
def scheme_of_work_bulk_generate(request, pk):
    """
    Bulk-generate Aura-T lesson plans for all topics in a scheme of work.
    Skips topics that already have a matching lesson plan.
    Returns JSON: {ok, created, skipped, errors: [...], total}
    """
    if request.user.user_type not in ['admin', 'teacher']:
        return JsonResponse({'error': 'Access denied'}, status=403)

    teacher = get_object_or_404(Teacher, user=request.user)
    scheme = get_object_or_404(SchemeOfWork, pk=pk, class_subject__teacher=teacher)

    topics = scheme.get_topics()
    if not topics:
        return JsonResponse({'error': 'No topics found. Extract topics from the scheme first.'}, status=400)

    from teachers.services.aura_gen_engine import AuraGenEngine
    import re as _re

    subject     = scheme.class_subject.subject
    school_class = scheme.class_subject.class_name
    subject_name = subject.name
    class_name   = school_class.name

    # Start week numbering after any existing plans for this teacher / subject / class
    existing_max = LessonPlan.objects.filter(
        teacher=teacher, subject=subject, school_class=school_class
    ).aggregate(max_week=models.Max('week_number'))['max_week'] or 0

    def _extract(header, text):
        pat = _re.compile(
            rf"\*\*{_re.escape(header)}.*?\*\*\s*(.*?)(?=\n\*\*|\Z)",
            _re.DOTALL | _re.IGNORECASE
        )
        m = pat.search(text)
        return m.group(1).strip() if m else ''

    created = 0
    skipped = 0
    errors  = []

    for idx, topic in enumerate(topics):
        # Skip if a plan for this topic already exists for this teacher/subject/class
        if LessonPlan.objects.filter(
            teacher=teacher, subject=subject,
            school_class=school_class, topic__iexact=topic
        ).exists():
            skipped += 1
            continue

        try:
            result      = AuraGenEngine.generate_lesson_plan(topic, subject_name, class_name)
            lesson_body = (result.get('lesson_plan') or '').strip()
            if not lesson_body:
                errors.append({'topic': topic, 'error': result.get('error', 'Empty response')})
                continue

            LessonPlan.objects.create(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
                week_number=existing_max + idx + 1,
                topic=topic,
                objectives=(
                    _extract('Content Standard', lesson_body) + '\n' +
                    _extract('Indicator', lesson_body)
                ).strip() or topic,
                teaching_materials=_extract('Teaching/Learning Materials', lesson_body),
                introduction=_extract('PHASE 1: STARTER', lesson_body),
                presentation=(
                    _extract('PHASE 2: NEW LEARNING', lesson_body) or
                    _extract('PHASE 2', lesson_body)
                ),
                evaluation=(
                    _extract('PHASE 3: REFLECTION', lesson_body) or
                    _extract('Assessment', lesson_body)
                ),
                homework=_extract('Homework', lesson_body),
            )
            created += 1
        except Exception as exc:
            errors.append({'topic': topic, 'error': str(exc)})

    return JsonResponse({
        'ok': True,
        'created': created,
        'skipped': skipped,
        'errors': errors,
        'total': len(topics),
    })


@login_required
def student_session_peek(request, session_id):
    """
    Teacher-only read-only view of a student's AI Tutor session transcript.
    Access is permitted only if the teacher teaches or manages the student's class.
    """
    if request.user.user_type not in ['teacher', 'admin']:
        messages.error(request, "Access restricted to teachers.")
        return redirect('dashboard')

    session = get_object_or_404(TutorSession, id=session_id)
    student = session.student

    if request.user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
        # Check teacher teaches or manages this student's class
        teaches_class = (
            student.current_class and (
                teacher.managed_classes.filter(id=student.current_class_id).exists() or
                ClassSubject.objects.filter(
                    teacher=teacher,
                    class_name=student.current_class
                ).exists()
            )
        )
        if not teaches_class:
            messages.error(request, "You do not have access to this student's session.")
            return redirect('teachers:teacher_ai_insights')

    messages_qs = TutorMessage.objects.filter(session=session).order_by('created_at')

    return render(request, 'teachers/student_session_peek.html', {
        'session': session,
        'student': student,
        'chat_messages': messages_qs,
    })


@login_required
@require_POST
def submit_to_hod(request):
    """
    Submit a lesson plan / summary to the Head of Department (school admin).
    Creates a Notification for all admin users.
    """
    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Access denied'}, status=403)

    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_title = request.POST.get('lesson_title', '').strip() or 'Untitled Lesson Plan'
    lesson_body = request.POST.get('lesson_body', '').strip()

    from announcements.models import Notification
    admin_users = User.objects.filter(user_type='admin')
    created = 0
    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            title=f"Lesson Plan Submitted: {lesson_title}",
            message=(
                f"Teacher {teacher.user.get_full_name()} submitted a lesson plan for your review.\n\n"
                f"{lesson_body[:500]}" if lesson_body else
                f"Teacher {teacher.user.get_full_name()} submitted a lesson plan for your review."
            ),
            notification_type='announcement',
        )
        created += 1

    return JsonResponse({'ok': True, 'notified': created, 'message': f'Submitted to {created} admin(s).'})


@login_required
def save_aura_t_plan(request):
    """Save the Aura-T command centre lesson plan preview as a LessonPlan record."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    if request.user.user_type != 'teacher':
        return JsonResponse({'ok': False, 'error': 'Teachers only'}, status=403)

    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Teacher profile not found'}, status=404)

    lesson_title = request.POST.get('lesson_title', '').strip() or 'Aura-T Lesson Plan'
    lesson_body = request.POST.get('lesson_body', '').strip()

    # Parse from body using the same section extractor as lesson_plan_create
    import re as _re

    def _extract(header, text):
        pat = _re.compile(rf"\*\*{_re.escape(header)}.*?\*\*\s*(.*?)(?=\n\*\*|\Z)", _re.DOTALL | _re.IGNORECASE)
        m = pat.search(text)
        return m.group(1).strip() if m else ''

    topic = _extract('Sub Strand', lesson_body) or _extract('Strand', lesson_body) or lesson_title

    # Get first class the teacher is associated with
    from academics.models import ClassSubject
    class_subject = ClassSubject.objects.filter(teacher=teacher).select_related('school_class', 'subject').first()

    plan = LessonPlan.objects.create(
        teacher=teacher,
        subject=class_subject.subject if class_subject else None,
        school_class=class_subject.school_class if class_subject else None,
        week_number=1,
        topic=topic,
        objectives=_extract('Content Standard', lesson_body) + '\n' + _extract('Indicator', lesson_body),
        introduction=_extract('PHASE 1: STARTER', lesson_body),
        presentation=_extract('PHASE 2: NEW LEARNING', lesson_body) or _extract('PHASE 2', lesson_body),
        evaluation=_extract('PHASE 3: REFLECTION', lesson_body) or _extract('Assessment', lesson_body),
        homework=_extract('Homework', lesson_body) or 'Refer to textbook exercises.',
    )

    return JsonResponse({'ok': True, 'plan_id': plan.id, 'detail_url': f'/lesson-plans/{plan.id}/'})


# ─────────────────────────────────────────────────────────────────────────────
# DIGITAL PULSE — real-time class engagement
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def pulse_launch(request, plan_pk):
    """Teacher launches a pulse for a lesson plan.  Returns JSON {session_id}."""
    if request.user.user_type not in ('teacher', 'admin'):
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        from academics.pulse_models import PulseSession, parse_pulse_questions, parse_q3_chips
    except ImportError:
        return JsonResponse({'error': 'Pulse feature not available'}, status=500)

    teacher = None
    if request.user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
        plan = get_object_or_404(LessonPlan, pk=plan_pk, teacher=teacher)
    else:
        plan = get_object_or_404(LessonPlan, pk=plan_pk)
        teacher = plan.teacher

    # Close any previous active sessions for this plan
    PulseSession.objects.filter(lesson_plan=plan, status='active').update(status='closed')

    q1, q2, q3 = parse_pulse_questions(plan.introduction or '')
    chips       = parse_q3_chips(plan)

    session = PulseSession.objects.create(
        lesson_plan=plan,
        teacher=teacher,
        q1_text=q1,
        q2_text=q2,
        q3_text=q3,
        q3_chips=chips,
    )
    return JsonResponse({
        'session_id': session.pk,
        'q1': q1, 'q2': q2, 'q3': q3,
        'chips': chips,
        'total_students': session.total_students,
    })


@login_required
def pulse_live(request, session_id):
    """Polling endpoint — teacher gets live response count + who's typing."""
    if request.user.user_type not in ('teacher', 'admin'):
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        from academics.pulse_models import PulseSession
    except ImportError:
        return JsonResponse({'error': 'unavailable'}, status=500)

    session = get_object_or_404(PulseSession, pk=session_id)

    responded = session.responded_count
    total     = session.total_students
    typing    = [f'{fn} {ln}'.strip() for fn, ln in session.typing_students]

    # Build aggregate for Q1 / Q2
    q1_true = q1_false = q2_true = q2_false = 0
    q3_counts = {}
    for r in session.responses.filter(submitted_at__isnull=False):
        if r.q1_answer is True:  q1_true  += 1
        if r.q1_answer is False: q1_false += 1
        if r.q2_answer is True:  q2_true  += 1
        if r.q2_answer is False: q2_false += 1
        if r.q3_answer:
            q3_counts[r.q3_answer] = q3_counts.get(r.q3_answer, 0) + 1

    return JsonResponse({
        'status': session.status,
        'responded': responded,
        'total': total,
        'typing': typing,
        'q1': {'true': q1_true, 'false': q1_false},
        'q2': {'true': q2_true, 'false': q2_false},
        'q3_counts': q3_counts,
    })


@login_required
@require_POST
def pulse_close(request, session_id):
    """Teacher closes an active pulse session."""
    if request.user.user_type not in ('teacher', 'admin'):
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        from academics.pulse_models import PulseSession
    except ImportError:
        return JsonResponse({'error': 'unavailable'}, status=500)

    session = get_object_or_404(PulseSession, pk=session_id)
    if session.status == 'active':
        session.status    = 'closed'
        session.closed_at = timezone.now()
        session.save(update_fields=['status', 'closed_at'])

    from django.urls import reverse
    # Prepend SCRIPT_NAME so path-based tenant prefix (/school1/) is included
    script_name  = request.META.get('SCRIPT_NAME', '').rstrip('/')
    results_path = reverse('teachers:pulse_results', args=[session_id])
    results_url  = script_name + results_path
    return JsonResponse({'ok': True, 'redirect': results_url})


@login_required
def pulse_results(request, session_id):
    """Post-session Pulse results summary for the teacher."""
    if request.user.user_type not in ('teacher', 'admin'):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    try:
        from academics.pulse_models import PulseSession, PulseResponse
    except ImportError:
        messages.error(request, 'Pulse feature not available.')
        return redirect('teachers:lesson_plan_list')

    session = get_object_or_404(PulseSession, pk=session_id)

    # Ensure the requesting teacher owns the session (admins bypass)
    if request.user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
        if session.teacher != teacher:
            messages.error(request, 'Access denied.')
            return redirect('teachers:lesson_plan_list')

    # ── All students in the target class ───────────────────────────────────
    school_class = session.lesson_plan.school_class
    all_students = (
        Student.objects.filter(current_class=school_class, user__is_active=True)
        .select_related('user')
        .order_by('user__last_name', 'user__first_name')
    )

    # ── Index responses by student_id ──────────────────────────────────────
    response_map = {
        r.student_id: r
        for r in session.responses.select_related('student__user').all()
    }

    # ── Build per-student rows ─────────────────────────────────────────────
    rows = []
    q1_true = q1_false = q1_skip = 0
    q2_true = q2_false = q2_skip = 0
    q3_counts = {}
    no_show_count = 0

    for stu in all_students:
        resp = response_map.get(stu.pk)
        submitted = resp is not None and resp.submitted_at is not None

        if resp and resp.q1_answer is True:   q1_true  += 1
        elif resp and resp.q1_answer is False: q1_false += 1
        else:                                  q1_skip  += 1

        if resp and resp.q2_answer is True:   q2_true  += 1
        elif resp and resp.q2_answer is False: q2_false += 1
        else:                                  q2_skip  += 1

        q3_val = (resp.q3_answer or '').strip() if resp else ''
        if q3_val:
            q3_counts[q3_val] = q3_counts.get(q3_val, 0) + 1

        if not submitted:
            no_show_count += 1

        # ── At-risk logic ──────────────────────────────────────────────
        # Q1 = prerequisite (correct = True), Q2 = misconception (correct = False)
        # Flag if: didn't respond, OR answered Q1 False, OR answered Q2 True
        at_risk = (
            not submitted
            or (resp and resp.q1_answer is False)
            or (resp and resp.q2_answer is True)
        )

        rows.append({
            'student': stu,
            'submitted': submitted,
            'q1': resp.q1_answer if resp else None,
            'q2': resp.q2_answer if resp else None,
            'q3': q3_val,
            'at_risk': at_risk,
        })

    total = len(rows)
    responded = total - no_show_count
    response_pct = round(responded / total * 100) if total else 0

    # Q3 sorted by frequency
    q3_sorted = sorted(q3_counts.items(), key=lambda x: -x[1])

    # At-risk count
    at_risk_count = sum(1 for r in rows if r['at_risk'])

    context = {
        'session': session,
        'plan': session.lesson_plan,
        'rows': rows,
        'total': total,
        'responded': responded,
        'response_pct': response_pct,
        'no_show_count': no_show_count,
        'at_risk_count': at_risk_count,
        'q1_true': q1_true, 'q1_false': q1_false, 'q1_skip': q1_skip,
        'q2_true': q2_true, 'q2_false': q2_false, 'q2_skip': q2_skip,
        'q3_counts': q3_sorted,
        'q3_chips': session.q3_chips,
        'school_class': school_class,
    }
    return render(request, 'teachers/pulse_results.html', context)


@login_required
def pulse_history(request):
    """All past Pulse sessions for the teacher (or all sessions for admins)."""
    if request.user.user_type not in ('teacher', 'admin'):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    try:
        from academics.pulse_models import PulseSession
    except ImportError:
        messages.error(request, 'Pulse feature not available.')
        return redirect('teachers:aura_command_center')

    is_admin = request.user.user_type == 'admin'

    if is_admin:
        qs = PulseSession.objects.select_related(
            'lesson_plan__school_class', 'lesson_plan__subject', 'teacher__user'
        ).order_by('-created_at')
    else:
        teacher = get_object_or_404(Teacher, user=request.user)
        qs = PulseSession.objects.filter(teacher=teacher).select_related(
            'lesson_plan__school_class', 'lesson_plan__subject', 'teacher__user'
        ).order_by('-created_at')

    sessions = []
    for s in qs:
        total     = s.total_students
        responded = s.responded_count
        pct       = round(responded / total * 100) if total else 0
        sessions.append({
            'session':    s,
            'plan':       s.lesson_plan,
            'school_class': s.lesson_plan.school_class if s.lesson_plan else None,
            'total':      total,
            'responded':  responded,
            'pct':        pct,
        })

    return render(request, 'teachers/pulse_history.html', {
        'sessions':       sessions,
        'is_admin':       is_admin,
        'total_sessions': len(sessions),
        'active_count':   sum(1 for s in sessions if s['session'].status == 'active'),
        'closed_count':   sum(1 for s in sessions if s['session'].status == 'closed'),
    })
