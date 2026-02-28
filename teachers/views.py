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
from teachers.models import Teacher, DutyWeek, LessonPlan
from academics.models import ClassSubject, AcademicYear, Timetable, SchoolInfo, Resource, Class
from students.models import Student, Grade, ClassExercise, StudentExerciseScore
from students.utils import normalize_term
from .forms import ResourceForm, LessonPlanForm, TeacherCreateForm #, HomeworkForm
from .models import LessonGenerationSession
from accounts.models import User
from academics.tutor_models import generate_teacher_id_card, export_id_card_to_pdf, export_multiple_id_cards_to_pdf, TutorSession
from parents.models import Parent
from communication.models import Conversation, Message
from django.views.decorators.http import require_POST
# from parents.models import Homework


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
        teacher_classes = ClassSubject.objects.filter(teacher=teacher, academic_year=current_year).values_list('class_assigned', flat=True)
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

    context = {
        'total_sessions': total_sessions,
        'active_students_count': active_students_count,
        'avg_msgs': round(avg_msgs_per_session, 1),
        'top_students': top_students,
        'common_topics': topic_counts,
        'recent_activity': recent_activity,
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
        
    if selected_class:
        # Generate mock analytics data for the selected class
        students = Student.objects.filter(current_class=selected_class).select_related('user')
        for student in students:
            # Mock logic: Randomized mastery for demo purposes
            # In production, this would query an AI analytics model
            import random
            # Use student ID to seed random content so it feels persistent
            random.seed(student.id)
            
            mastery = random.randint(40, 100)
            status = 'green' if mastery >= 80 else 'yellow' if mastery >= 60 else 'red'
            misconception = None
            suggested_intervention = None
            
            if status == 'red':
                misconceptions_list = [
                    "Confuses area with perimeter",
                    "Difficulty with negative numbers",
                    "Fraction addition errors",
                    "Linear equation variable isolation"
                ]
                misconception = random.choice(misconceptions_list)
                suggested_intervention = "Assign 'Foundations of Geometry' module"
            elif status == 'yellow':
                misconceptions_list = [
                    "Minor calculation errors",
                    "Needs more practice with word problems",
                    "Inconsistent with unit conversion"
                ]
                misconception = random.choice(misconceptions_list)
                suggested_intervention = "Review session on unit conversion"
            
            students_data.append({
                'name': student.user.get_full_name(),
                'id': student.id,
                'mastery': mastery,
                'status': status,
                'misconception': misconception,
                'intervention': suggested_intervention,
                'last_active': "2 mins ago" if random.random() > 0.5 else "1 hour ago"
            })
            
    # Calculate class aggregate stats
    avg_mastery = 0
    intervention_count = 0
    if students_data:
        avg_mastery = sum(s['mastery'] for s in students_data) / len(students_data)
        intervention_count = sum(1 for s in students_data if s['status'] == 'red')


    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students_data': students_data,
        'avg_mastery': round(avg_mastery, 1),
        'intervention_count': intervention_count,
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
    
    context = {
        'class_obj': class_obj,
        'teachers': teachers
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
    # Only Admin or Teachers can see this? Assuming Admin/Staff.
    # if request.user.user_type not in ['admin', 'teacher']: ...
    
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if not current_year:
        current_year = AcademicYear.objects.first()

    from django.utils import timezone
    today = timezone.now().date()
    # Auto-detect term if not provided
    req_term = request.GET.get('term')
    if req_term:
        term = req_term
    else:
        # Default based on active duty week
        current_week = DutyWeek.objects.filter(
            academic_year=current_year,
            start_date__lte=today,
            end_date__gte=today
        ).first()
        term = current_week.term if current_week else ('second' if 1 <= today.month <= 4 else ('third' if 5 <= today.month <= 8 else 'first'))

    year_id = request.GET.get('year', current_year.id if current_year else None)
    
    if year_id:
        year = get_object_or_404(AcademicYear, id=year_id)
    else:
        year = None

    weeks = DutyWeek.objects.filter(academic_year=year, term=term).prefetch_related('assignments', 'assignments__teacher', 'assignments__teacher__user').order_by('week_number')
    
    context = {
        'weeks': weeks,
        'year': year,
        'term': term,
        'school_info': SchoolInfo.objects.first(),
        'available_terms': ['first', 'second', 'third'],
        'academic_years': AcademicYear.objects.all(),
    }
    return render(request, 'teachers/duty_roster_pdf.html', context)


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
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    
    week = request.GET.get('week', '').strip()
    subject_id = request.GET.get('subject', '').strip()
    class_id = request.GET.get('school_class', '').strip()
    query = request.GET.get('q', '').strip()

    assigned_pairs = ClassSubject.objects.filter(teacher=teacher).select_related('class_name', 'subject')
    teacher_subjects = [pair.subject for pair in assigned_pairs]
    teacher_classes = [pair.class_name for pair in assigned_pairs]

    # de-duplicate while preserving order
    seen_subject_ids = set()
    teacher_subjects = [s for s in teacher_subjects if not (s.id in seen_subject_ids or seen_subject_ids.add(s.id))]
    seen_class_ids = set()
    teacher_classes = [c for c in teacher_classes if not (c.id in seen_class_ids or seen_class_ids.add(c.id))]

    try:
        # Force evaluation to catch DB errors if table doesn't exist yet
        lesson_plans_qs = LessonPlan.objects.filter(teacher=teacher).select_related('subject', 'school_class')
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
        lesson_plans = list(lesson_plans_qs)
    except (OperationalError, ProgrammingError):
        lesson_plans = []
        teacher_subjects = []
        teacher_classes = []
        messages.warning(request, "Lesson Plan system is initializing. Please try again later.")
        
    return render(request, 'teachers/lesson_plan_list.html', {
        'lesson_plans': lesson_plans,
        'selected_week': week,
        'selected_subject': subject_id,
        'selected_class': class_id,
        'selected_query': query,
        'teacher_subjects': teacher_subjects,
        'teacher_classes': teacher_classes,
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
    topic = request.GET.get('topic')
    if topic:
        # Simulate AI generation
        initial_data = {
            'topic': topic,
            'objectives': f"By the end of the lesson, students will be able to:\n1. Understand the core concepts of {topic}.\n2. Apply {topic} to solve simple problems.\n3. Analyze real-world examples of {topic}.",
            'introduction': f"Begin with a 5-minute warm-up activity related to {topic}. Ask students what they already know about it to gauge prior knowledge.",
            'presentation': f"1. Define {topic} and key terminology.\n2. Demonstrate the main concept using visual aids.\n3. Walk through 2-3 step-by-step examples on the board.\n4. Facilitate a class discussion to check for understanding.",
            'evaluation': f"Distribute a short worksheet with 5 problems on {topic}. Circulate to provide individual assistance.",
            'homework': f"Read the chapter on {topic} and complete exercises 1-10 on page 42.",
            'teaching_materials': f"Textbook, Whiteboard, Marker, Projector (optional), Handouts on {topic}"
        }
        messages.info(request, f"AI has drafted a lesson plan for '{topic}'. Please review and edit.")
    
    if request.method == 'POST':
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
            return redirect('teachers:lesson_plan_list')
    else:
        form = LessonPlanForm(instance=lesson_plan, teacher=teacher)
        
    return render(request, 'teachers/lesson_plan_form.html', {
        'form': form,
        'title': 'Edit Lesson Plan'
    })

@login_required
def lesson_plan_detail(request, pk):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)
    
    return render(request, 'teachers/lesson_plan_detail.html', {'lesson_plan': lesson_plan})


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
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, user=request.user)
    lesson_plan = get_object_or_404(LessonPlan, pk=pk, teacher=teacher)

    return render(request, 'teachers/lesson_plan_detail.html', {
        'lesson_plan': lesson_plan,
        'print_mode': True,
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
            except:
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
    if not hasattr(request.user, 'teacher'):
         messages.error(request, "Access restricted to teachers.")
         return redirect('dashboard')
         
    teacher = request.user.teacher
    sessions = LessonGenerationSession.objects.filter(teacher=teacher).order_by('-updated_at')
    
    from academics.models import ClassSubject, AcademicYear
    from students.models import Student, Grade
    from parents.models import Parent
    
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get subjects this teacher teaches
    teacher_subjects = list(ClassSubject.objects.filter(teacher=teacher).values_list('subject_id', flat=True))
    
    # Get classes this teacher teaches
    teacher_classes = list(ClassSubject.objects.filter(teacher=teacher).values_list('class_name_id', flat=True))
    
    # Try fetching real students
    students = Student.objects.filter(current_class_id__in=teacher_classes).select_related('user')
    student_data = []
    
    struggling_count = 0
    on_target_count = 0
    excelling_count = 0
    
    parent_updates = []
    
    class_name_display = "All Classes"
    if students.exists():
        classes_names = set(Student.objects.filter(id__in=students).values_list('current_class__name', flat=True))
        class_name_display = ", ".join(filter(None, classes_names))
        
        for student in students:
            # Check grades for this teacher's subjects
            grades = Grade.objects.filter(student=student, subject_id__in=teacher_subjects)
            if current_year:
                grades = grades.filter(academic_year=current_year)
            
            # Simple heuristic
            total_scores = [g.total_score for g in grades if getattr(g, 'total_score', None)]
            avg_score = sum(total_scores)/len(total_scores) if total_scores else None
            
            status = 'good' # default 'Progressing'
            if avg_score is not None:
                if avg_score >= 80: 
                    status = 'excellent'
                    excelling_count += 1
                elif avg_score < 50: 
                    status = 'struggling'
                    struggling_count += 1
                else: 
                    on_target_count += 1
            else:
                on_target_count += 1
                
            student_data.append({
                'id': student.id,
                'name': student.user.get_full_name() or student.user.username,
                'status': status,
                'avg_score': avg_score,
                'tooltip': f"Avg Score: {avg_score:.1f}%" if avg_score else "No grades yet."
            })
            
            # Draft parent updates
            parent = student.parents.first()
              if parent:
                parent_name = parent.user.get_full_name() or parent.user.username
                if status == 'struggling':
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is having some challenges with recent topics. Let's work together to provide additional support."
                elif status == 'excellent':
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is doing exceptionally well! Keep up the great work at home."
                else:
                    draftMsg = f"Hi {parent_name}, {student.user.first_name} is progressing smoothly and staying on target."
                    
                parent_updates.append({
                    'parent_name': parent_name,
                    'student_name': student.user.first_name,
                    'draft': draftMsg
                })
    else:
        # Mock Data for testing the UI when there are no real students
        class_name_display = "Basic 8 Science (Mock)"
        student_data = [
            {'name': 'Kwame', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Efia', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Kofi', 'status': 'struggling', 'tooltip': "Struggling with 'Factoring'. Used 'Hint' 4 times."},
            {'name': 'Yaw', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Adjoa', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Zainab', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Ama', 'status': 'struggling', 'tooltip': "Requires help with core concepts."},
            {'name': 'Kweku', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Abena', 'status': 'excellent', 'tooltip': 'Excelling. Target Achieved.'},
            {'name': 'Esi', 'status': 'good', 'tooltip': 'Progressing well.'},
            {'name': 'Kwesi', 'status': 'struggling', 'tooltip': "Requires help with core concepts."},
            {'name': 'Akosua', 'status': 'good', 'tooltip': 'Progressing well.'},
        ]
        struggling_count = 3
        on_target_count = 6
        excelling_count = 3
        
        parent_updates = [
            {'parent_name': "Mr. Osei", 'student_name': "Ama", 'draft': "Hi Mr. Osei, Ama did great with 'Friction' today, but she's still a bit confused about 'Mass.' Here is a video link..."},
            {'parent_name': "Mrs. Mensah", 'student_name': "Kofi", 'draft': "Hi Mrs. Mensah, Kofi is struggling with 'Negative Coefficients'. I have assigned him to a remedial group tomorrow..."}
        ]
        
    context = {
        'sessions': sessions,
        'student_data': student_data,
        'struggling_count': struggling_count,
        'on_target_count': on_target_count,
        'excelling_count': excelling_count,
        'class_name_display': class_name_display,
        'parent_updates': parent_updates
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
                
                from academics.ai_tutor import _post_chat_completion
                api_key = settings.OPENAI_API_KEY
                
                if not api_key:
                    raise Exception("OpenAI API key not configured.")
                
                system_prompt = "You are an expert lesson planner for teachers. Help them create detailed, engaging lesson plans."
                api_msgs = [{"role": "system", "content": system_prompt}] + messages_list
                
                payload = {
                    "model": "gpt-4o-mini",
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
                            "model": "gpt-4o-mini",
                            "messages": api_msgs + [{"role": "user", "content": "Suggest a short 3-5 word title for this chat."}],
                            "max_tokens": 15
                        }
                        title_resp = _post_chat_completion(title_payload, api_key)
                        new_title = title_resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip().strip('"')
                        if new_title:
                            session.title = new_title
                    except:
                        pass
                
                session.save()
                return JsonResponse({'status': 'success', 'reply': ai_content, 'title': session.title})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return render(request, 'teachers/ai_session_detail.html', {'session': session})

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

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt
def aura_t_api(request):
    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            topic = data.get('topic', 'General Topic')
            
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                # Fallback to simulated logic if no API key is provided
                return _simulate_aura_t(action, topic, data)
                
            from academics.ai_tutor import _post_chat_completion
            
            if action == 'class_sync':
                system_prompt = "You are Aura-T, an expert AI assistant for teachers. Generate a 'class_sync' response. Provide a json with 'introduction', 'presentation', and 'differentiation'. The response should rewrite a hook based on students struggling, and provide strategies."
                user_prompt = f"Topic: {topic}. Generate the JSON payload."
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                response = _post_chat_completion(payload, api_key)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                result['status'] = 'success'
                return JsonResponse(result)
                
            elif action == 'interest_mashup':
                interests = data.get('interests', 'Gaming')
                system_prompt = "You are Aura-T. Generate an 'interest_mashup' response. Provide a json with 'introduction' and 'presentation'. Mix the topic with the provided student interests to make it highly engaging."
                user_prompt = f"Topic: {topic}. Interests: {interests}. Generate the JSON payload."
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                response = _post_chat_completion(payload, api_key)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                result['status'] = 'success'
                return JsonResponse(result)
                
            elif action == 'standard_linker':
                system_prompt = "You are Aura-T. Generate a 'standard_linker' response. Provide a json with 'objectives'. Link the topic to official GES & WAEC standards and competencies."
                user_prompt = f"Topic: {topic}. Generate the JSON payload."
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                response = _post_chat_completion(payload, api_key)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                result['status'] = 'success'
                return JsonResponse(result)
                
            elif action == 'chat_suggest':
                context = data.get('context', '')
                system_prompt = "You are Aura-T. Provide a helpful 1-2 sentence teacher tip based on the context they are typing. If they mention introduction or hook, suggest a fun fact. If assessment, remind them."
                user_prompt = f"Topic: {topic}. User is typing: '{context}'. Suggestion?"
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                response = _post_chat_completion(payload, api_key)
                tip = response.get("choices", [{}])[0].get("message", {}).get("content", "Teacher Tip: Keep it up!")
                return JsonResponse({'status': 'success', 'suggestion': tip})

            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def _simulate_aura_t(action, topic, data):
    if action == 'class_sync':
        return JsonResponse({
            'status': 'success',
            'introduction': f"I see 12 students struggled with this. Let's rewrite today's 'Hook' to focus on a practical scenario to reinforce the visual logic before we move to '{topic}'.",
            'presentation': f"Focus heavily on the visual analogies for {topic}.",
            'differentiation': "Focus on base concepts for remedial group. Advanced group analyzes edge-cases."
        })
    elif action == 'interest_mashup':
        interests = data.get('interests', 'Gaming')
        return JsonResponse({
            'status': 'success',
            'introduction': f"Let's teach {topic} by calculating stats for {interests}.",
            'presentation': f"Use examples from {interests} to illustrate {topic}."
        })
    elif action == 'standard_linker':
        return JsonResponse({
            'status': 'success',
            'objectives': f"This lesson covers GES & WAEC standards for {topic} and develops 'Critical Thinking' and 'Digital Literacy' competencies.\n1. Understand {topic}\n2. Apply {topic}"
        })
    elif action == 'chat_suggest':
        context = data.get('context', '')
        if 'Objective' in context or 'assessment' in context.lower():
            tip = "Alert: You haven't assessed 'Objective B' yet. Should I add a question to the exit ticket?"
        elif 'introduction' in context.lower() or 'hook' in context.lower():
            tip = "Teacher Tip: Students usually find this part boring. Want a 1-minute fun fact about this?"
        else:
            tip = f"Resource: I found a PhET Interactive Simulation that perfectly matches {topic}. Click to embed."
        return JsonResponse({'status': 'success', 'suggestion': tip})
    else:
        return JsonResponse({'error': 'Unknown action'}, status=400)
