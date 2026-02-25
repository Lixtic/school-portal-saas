from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from academics.models import Class, AcademicYear, ClassSubject, Activity, Timetable, GalleryImage, Resource, SchoolInfo, Subject
from teachers.models import Teacher, DutyAssignment
from students.models import Student, Attendance
from announcements.models import Announcement
from django.db.models import Q, Count
from django.db import connection
from django.utils import timezone
import calendar
import datetime
import json

from django.db.utils import OperationalError, ProgrammingError


def build_academic_calendar_widget(limit=5):
    today = timezone.now().date()
    current_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()

    events = []
    if current_year:
        total_days = max((current_year.end_date - current_year.start_date).days, 1)
        first_term_start = current_year.start_date
        second_term_start = current_year.start_date + datetime.timedelta(days=total_days // 3)
        third_term_start = current_year.start_date + datetime.timedelta(days=(2 * total_days) // 3)

        term_markers = [
            ('Term 1 Start', first_term_start, 'Term'),
            ('Term 2 Start', second_term_start, 'Term'),
            ('Term 3 Start', third_term_start, 'Term'),
            ('Academic Year Ends', current_year.end_date, 'Year End'),
        ]
        for title, when, tag in term_markers:
            events.append({'title': title, 'date': when, 'tag': tag})

    upcoming_activities = Activity.objects.filter(is_active=True, date__gte=today).order_by('date')[:limit]
    for activity in upcoming_activities:
        events.append({
            'title': activity.title,
            'date': activity.date,
            'tag': activity.tag or 'Activity',
        })

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
        month_date = datetime.date(prev_month_year, prev_month, day)
        cells.append({
            'day': day,
            'date': month_date,
            'is_current_month': False,
            'is_today': month_date == today,
            'events': event_map.get(month_date.isoformat(), []),
        })

    for day in range(1, month_days + 1):
        month_date = datetime.date(display_year, display_month, day)
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
        month_date = datetime.date(next_month_year, next_month, day)
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
        'academic_calendar_month_label': datetime.date(display_year, display_month, 1).strftime('%B %Y'),
        'academic_calendar_weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'academic_calendar_weeks': calendar_weeks,
    }


def build_onboarding_checklist():
    """Compute the 8-step getting-started checklist for school admins."""
    from finance.models import FeeStructure
    from django.urls import reverse

    try:
        school_info = SchoolInfo.objects.first()
        school_profile_done = bool(school_info and school_info.name not in ('', 'School Name'))
    except Exception:
        school_info = None
        school_profile_done = False

    steps = [
        {
            'id': 'school_profile',
            'icon': 'bi-building',
            'label': 'Set up school profile',
            'desc': 'Add your school name, logo, and contact information',
            'done': school_profile_done,
            'url_name': 'academics:school_settings',
            'url_label': 'Open Settings',
        },
        {
            'id': 'academic_year',
            'icon': 'bi-calendar3',
            'label': 'Create an academic year',
            'desc': 'Set the current academic year to activate grade and attendance tracking',
            'done': AcademicYear.objects.filter(is_current=True).exists(),
            'url_name': 'academics:manage_academic_years',
            'url_label': 'Academic Years',
        },
        {
            'id': 'classes',
            'icon': 'bi-door-open',
            'label': 'Add classes',
            'desc': 'Create class groups (e.g. Basic 7, Form 1) for your school',
            'done': Class.objects.exists(),
            'url_name': 'academics:manage_classes',
            'url_label': 'Manage Classes',
        },
        {
            'id': 'subjects',
            'icon': 'bi-book',
            'label': 'Add subjects',
            'desc': 'Define the subjects taught at your school',
            'done': Subject.objects.exists(),
            'url_name': 'academics:manage_subjects',
            'url_label': 'Manage Subjects',
        },
        {
            'id': 'teachers',
            'icon': 'bi-person-badge',
            'label': 'Add a teacher',
            'desc': 'Create teacher profiles and assign them to classes and subjects',
            'done': Teacher.objects.exists(),
            'url_name': 'teachers:add_teacher',
            'url_label': 'Add Teacher',
        },
        {
            'id': 'students',
            'icon': 'bi-people',
            'label': 'Enroll a student',
            'desc': 'Register students individually or import a class list via CSV',
            'done': Student.objects.exists(),
            'url_name': 'students:add_student',
            'url_label': 'Add Student',
        },
        {
            'id': 'fees',
            'icon': 'bi-cash-stack',
            'label': 'Set up fee structure',
            'desc': 'Define fee types and amounts per class and term',
            'done': FeeStructure.objects.exists(),
            'url_name': 'finance:create_fee_structure',
            'url_label': 'Create Fee Structure',
        },
        {
            'id': 'announcement',
            'icon': 'bi-megaphone',
            'label': 'Post an announcement',
            'desc': 'Keep students, teachers, and parents informed with notices',
            'done': Announcement.objects.exists(),
            'url_name': 'announcements:manage',
            'url_label': 'Create Announcement',
        },
    ]

    done_count = sum(1 for s in steps if s['done'])
    total = len(steps)

    # Pre-resolve URLs so templates can use them directly
    for step in steps:
        try:
            step['url'] = reverse(step['url_name'])
        except Exception:
            step['url'] = '#'

    return {
        'steps': steps,
        'done_count': done_count,
        'total': total,
        'all_done': done_count == total,
        'percent': int(done_count * 100 / total),
    }


def homepage(request):
    # Route logic for different tenants
    is_public = False
    if hasattr(request, 'tenant'):
        is_public = (request.tenant.schema_name == 'public')
    
    # 1. Public Tenant -> Show SaaS Landing
    if is_public:
        return render(request, 'landing_public.html')

    # 2. School Tenant -> Show School Dashboard/Home or redirect to Login
    # If user is not logged in on school tenant, better to show login?
    # Or show specific school landing page? For now, let's keep the activity feed home
    # but ensure it's generic.
    
    # If not logged in, maybe redirect to login for school context?
    # if not request.user.is_authenticated:
    #     return redirect('login') 
    
    # ... Continue with existing logic for school home ...
    activities_qs = Activity.objects.filter(is_active=True).order_by('date')[:12]
    activities = [
        {
            'title': a.title,
            'date': a.date,
            'summary': a.summary,
            'tag': a.tag,
        }
        for a in activities_qs
    ]

    # Fallback if no activities in DB
    if not activities:
        today = datetime.date.today()
        activities = [
            {'title': 'STEM Makers Fair', 'date': today + datetime.timedelta(days=5), 'summary': 'Robotics, circuits, and coding demos led by Basic 9 tech club.', 'tag': 'Innovation'},
            {'title': 'Cultural Day Showcase', 'date': today + datetime.timedelta(days=12), 'summary': 'Performances and exhibits celebrating local heritage and arts.', 'tag': 'Community'},
            {'title': 'Reading Marathon', 'date': today + datetime.timedelta(days=20), 'summary': 'Whole-school literacy sprint with parent volunteers and prizes.', 'tag': 'Academics'},
        ]

    # Get School Info (for settings like homepage_template)
    school_info = SchoolInfo.objects.first()
    
    # Safely get template choice with fallback
    try:
        template_choice = school_info.homepage_template if school_info else 'default'
    except AttributeError:
        template_choice = 'default'

    highlights = [
        {
            'title': 'Excellence',
            'desc': 'Committed to academic rigor.',
            'icon': 'fas fa-star'
        },
        {
            'title': 'Community',
            'desc': 'Strong parent-teacher partnerships.',
            'icon': 'fas fa-users'
        },
        {
            'title': 'Innovation',
            'desc': 'Technologically advanced learning.',
            'icon': 'fas fa-desktop'
        }
    ]

    try:
        hero_images = GalleryImage.objects.all().order_by('-created_at')[:3]
        gallery_images = GalleryImage.objects.all().order_by('?')[:6]  # Random 6 for the tour hub
    except (ProgrammingError, OperationalError):
        # Table may be missing on fresh tenants before migrations
        hero_images = []
        gallery_images = []

    context = {
        'activities': activities,
        'highlights': highlights,
        'hero_images': hero_images,
        'gallery_images': gallery_images,
        'school_info': school_info
    }

    # Route to selected template
    if template_choice == 'modern':
        return render(request, 'home/modern.html', context)
    elif template_choice == 'classic':
        return render(request, 'home/classic.html', context)
    elif template_choice == 'minimal':
        return render(request, 'home/minimal.html', context)
    elif template_choice == 'playful':
        return render(request, 'home/playful.html', context)
    elif template_choice == 'elegant':
        return render(request, 'home/elegant.html', context)
    else:
        # Default View (Restoring original highlights for default)
        highlights = [
            {
                'title': 'Attendance at 98%',
                'detail': 'Consistent daily check-ins across classes.',
                'icon': 'bi-activity'
            },
            {
                'title': 'Clubs growing',
                'detail': 'STEM, Debate, and Arts clubs expanded this term.',
                'icon': 'bi-people'
            },
            {
                'title': 'Parent portal live',
                'detail': 'Guardians follow homework and grades in real time.',
                'icon': 'bi-shield-check'
            },
        ]
        context['highlights'] = highlights
        return render(request, 'home.html', context)

def login_view(request):
    if request.user.is_authenticated:
        dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
        return redirect(dashboard_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
            return redirect(dashboard_url)
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'accounts/login.html')


def find_school(request):
    query = (request.GET.get('q') or '').strip()
    exact = request.GET.get('exact') == '1'

    from tenants.models import School, Domain

    schools_qs = School.objects.exclude(schema_name='public').filter(is_active=True)

    def serialize_school(school):
        primary_domain = Domain.objects.filter(tenant=school, is_primary=True).values_list('domain', flat=True).first()
        return {
            'id': school.id,
            'name': school.name,
            'schema_name': school.schema_name,
            'domain': primary_domain,
            'login_url': f'/{school.schema_name}/login/',
        }

    if not query:
        popular_schools = schools_qs.order_by('name')[:8]
        return JsonResponse(
            {
                'results': [serialize_school(school) for school in popular_schools],
                'message': 'Popular schools',
            }
        )

    if exact:
        school = schools_qs.filter(
            Q(schema_name__iexact=query) |
            Q(name__iexact=query)
        ).first()

        if not school:
            domain_match = Domain.objects.select_related('tenant').filter(
                tenant__is_active=True,
                domain__iexact=query,
            ).exclude(tenant__schema_name='public').first()
            school = domain_match.tenant if domain_match else None

        if not school:
            return JsonResponse(
                {
                    'results': [],
                    'error': 'School not found. Check the School ID/name and try again.',
                },
                status=404,
            )

        return JsonResponse({'results': [serialize_school(school)]})

    school_ids = list(
        schools_qs.filter(
            Q(schema_name__icontains=query) |
            Q(name__icontains=query)
        ).values_list('id', flat=True)[:12]
    )

    domain_school_ids = list(
        Domain.objects.select_related('tenant').filter(
            tenant__is_active=True,
            domain__icontains=query,
        ).exclude(tenant__schema_name='public').values_list('tenant_id', flat=True)[:12]
    )

    ordered_ids = []
    for school_id in school_ids + domain_school_ids:
        if school_id not in ordered_ids:
            ordered_ids.append(school_id)

    schools_map = {
        school.id: school
        for school in schools_qs.filter(id__in=ordered_ids[:8])
    }

    results = [serialize_school(schools_map[school_id]) for school_id in ordered_ids if school_id in schools_map][:8]

    return JsonResponse({'results': results})


@login_required
def logout_view(request):
    logout(request)
    # Build proper redirect URL with tenant prefix
    login_url = request.META.get('SCRIPT_NAME', '') + '/login/'
    return redirect(login_url)


@login_required
def dashboard(request):
    user = request.user
    
    # === SAAS/PUBLIC ADMIN DASHBOARD ===
    is_public = False
    if hasattr(request, 'tenant'):
        is_public = (request.tenant.schema_name == 'public')
        
    if is_public:
        # Redirect staff users to landlord dashboard
        if user.is_staff:
            return redirect('/tenants/landlord/')
            
        # Avoid querying tenant-specific models (Student, Teacher, etc.) which don't exist in public schema
        if not user.is_superuser and not user.is_staff:
             # Basic public user? Maybe redirect to home or signup
             return redirect('home')
             
        from tenants.models import School, Domain
        context = {
            'schools_count': School.objects.exclude(schema_name='public').count(),
            'domains_count': Domain.objects.count(),
            'recent_schools': School.objects.exclude(schema_name='public').order_by('-created_on')[:10]
        }
        return render(request, 'tenants/dashboard_public.html', context)

    # === TENANT (SCHOOL) DASHBOARD ===
    
    # Check Onboarding Status for Admin
    if user.user_type == 'admin':
        try:
            school_info = SchoolInfo.objects.first()
            # If no info or setup not complete, send to wizard
            if not school_info or not school_info.setup_complete:
                return redirect('tenants:setup_wizard')
        except Exception:
            # Fallback if table missing or other error, let them pass or handle gracefully
            pass

    # Base query without slicing
    base_notices = Announcement.objects.filter(is_active=True).order_by('-created_at')
    calendar_widget = build_academic_calendar_widget()
    
    if user.user_type == 'admin':
        # Admin gets top 5 of all active notices
        notices = base_notices[:5]
        
        # Analytics Data
        
        # 1. Students per Class (Top 5 largest classes)
        # Using current academic year would be precise, but for now simple grouping
        students_per_class = Student.objects.values('current_class__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        chart_labels_classes = [item['current_class__name'] or 'Unassigned' for item in students_per_class]
        chart_data_classes = [item['count'] for item in students_per_class]

        # 2. Daily Attendance (Last 7 days)
        today = timezone.now().date()
        date_7_days_ago = today - datetime.timedelta(days=6)
        
        attendance_stats = Attendance.objects.filter(
            date__gte=date_7_days_ago, 
            status='present'
        ).values('date').annotate(
            present_count=Count('id')
        ).order_by('date')

        # Fill in missing dates with 0
        daily_presence = {}
        for item in attendance_stats:
            daily_presence[item['date']] = item['present_count']
        
        chart_labels_attendance = []
        chart_data_attendance = []
        
        for i in range(7):
            d = date_7_days_ago + datetime.timedelta(days=i)
            chart_labels_attendance.append(d.strftime("%a")) # Mon, Tue...
            chart_data_attendance.append(daily_presence.get(d, 0))

        try:
            onboarding = build_onboarding_checklist()
        except Exception:
            onboarding = None

        context = {
            'user': user,
            'notices': notices,
            'chart_labels_classes': json.dumps(chart_labels_classes),
            'chart_data_classes': json.dumps(chart_data_classes),
            'chart_labels_attendance': json.dumps(chart_labels_attendance),
            'chart_data_attendance': json.dumps(chart_data_attendance),
            'total_students': Student.objects.count(),
            'total_teachers': Teacher.objects.count(),
            'onboarding': onboarding,
            **calendar_widget,
        }

        return render(request, 'dashboard/admin_dashboard.html', context)
    elif user.user_type == 'teacher':
        teacher_profile = Teacher.objects.filter(user=user).first()
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            # Fallback to the latest academic year if none is marked current
            current_year = AcademicYear.objects.order_by('-start_date').first()

        class_subjects = ClassSubject.objects.filter(teacher=teacher_profile)
        class_teacher_classes = Class.objects.filter(class_teacher=teacher_profile)

        if current_year:
            class_subjects = class_subjects.filter(class_name__academic_year=current_year)
            class_teacher_classes = class_teacher_classes.filter(academic_year=current_year)

        class_ids = set(class_subjects.values_list('class_name_id', flat=True))
        class_ids.update(class_teacher_classes.values_list('id', flat=True))
        
        # Check for upcoming Duty
        next_duty = None
        current_date_val = timezone.now().date()
        
        if teacher_profile and current_year:
            # Look for duty in current year ending today or in future
            next_duty = DutyAssignment.objects.filter(
                teacher=teacher_profile,
                week__academic_year=current_year,
                week__end_date__gte=current_date_val
            ).select_related('week').order_by('week__start_date').first()
            
            # Debugging (visible in server logs) - REMOVE IN PROD
            # print(f"DEBUG: Teacher={teacher_profile}, Year={current_year}, Date={current_date_val}")
            # print(f"DEBUG: Next Duty Found: {next_duty}")


        # Get Today's Timetable
        today_weekday = timezone.now().weekday()
        current_time = timezone.localtime().time()
        
        todays_classes = Timetable.objects.filter(
            class_subject__teacher=teacher_profile,
            day=today_weekday
        ).select_related('class_subject', 'class_subject__class_name', 'class_subject__subject').order_by('start_time')

        # Add 'is_ongoing' attribute to each class
        for p in todays_classes:
            p.is_ongoing = p.start_time <= current_time <= p.end_time

        # Calculate Student Count (Restored)
        teacher_students_count = Student.objects.filter(current_class__id__in=class_ids).distinct().count()
        
        # Recent uploaded resources (safe when new columns may not exist yet)
        resource_fields_available = False
        try:
            with connection.cursor() as cursor:
                cols = [col.name for col in connection.introspection.get_table_description(cursor, Resource._meta.db_table)]
            resource_fields_available = 'resource_type' in cols and 'curriculum' in cols
        except Exception:
            resource_fields_available = False

        try:
            qs = Resource.objects.filter(
                Q(class_subject__teacher=teacher_profile) |
                Q(target_audience__in=['all', 'teachers'], class_subject__isnull=True)
            ).order_by('-uploaded_at')
            if not resource_fields_available:
                qs = qs.only('id', 'title', 'file', 'link', 'uploaded_at', 'class_subject', 'class_subject__subject', 'class_subject__class_name')
            recent_resources = list(qs[:5])
        except (OperationalError, ProgrammingError):
            recent_resources = []
            resource_fields_available = False

        # Filter notices for teacher
        teacher_notices = base_notices.filter(target_audience__in=['all', 'staff', 'teachers'])[:5]

        teacher_context = {
            'user': user,
            'teacher_has_classes': len(class_ids) > 0,
            'teacher_class_count': len(class_ids),
            'total_students_taught': teacher_students_count,
            'notices': teacher_notices,
            'next_duty': next_duty,
            'todays_classes': todays_classes,
            'recent_resources': recent_resources,
            'resource_fields_available': resource_fields_available,
            **calendar_widget,
        }

        return render(request, 'dashboard/teacher_dashboard.html', teacher_context)
    elif user.user_type == 'student':
        # Redirect to enhanced student dashboard
        return redirect('students:student_dashboard')
    elif user.user_type == 'parent':
        from finance.models import StudentFee
        parent_notices = base_notices.filter(target_audience__in=['all', 'parents'])
        
        # Calculate fees for all children
        try:
            parent_profile = getattr(user, 'parent_profile', None)
            if not parent_profile:
                 # Fallback/Auto-create logic or specific parents app retrieval
                 from parents.models import Parent
                 parent_profile = Parent.objects.filter(user=user).first()
            
            if parent_profile:
                children = parent_profile.children.all()
                total_outstanding = 0
                total_paid = 0
                for child in children:
                    fees = StudentFee.objects.filter(student=child)
                    for fee in fees:
                        total_outstanding += fee.balance
                        total_paid += fee.total_paid
            else:
                children = []
                total_outstanding = 0
                total_paid = 0

        except Exception as e:
            children = []
            total_outstanding = 0
            total_paid = 0

        return render(request, 'dashboard/parent_dashboard.html', {
            'user': user, 
            'notices': parent_notices,
            'children': children,
            'finance_stats': {
                'outstanding': total_outstanding,
                'paid': total_paid
            },
            **calendar_widget,
        })
    
    return redirect('login')
from django.core.management import call_command
from django.http import HttpResponse
from io import StringIO
import sys
import os

@login_required
def debug_status(request):
    """
    Debug view to check tenant status (staff only).
    """
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff only.')
        return redirect('dashboard')
    from django.db import connection, transaction
    from tenants.models import School, Domain
    
    out = StringIO()
    print("=== DEBUG STATUS ===", file=out)
    
    # 1. List Tenants
    print("\n[1] Existing Tenants:", file=out)
    try:
        schools = School.objects.all()
        if not schools:
            print("  (No tenants found)", file=out)
        for s in schools:
            print(f"  - {s.name} (Schema: {s.schema_name}, Active: {s.is_active})", file=out)
            domains = Domain.objects.filter(tenant=s)
            for d in domains:
                print(f"    -> Domain: {d.domain} (Primary: {d.is_primary})", file=out)
    except Exception as e:
        print(f"  ERROR listing tenants: {e}", file=out)

    # 2. Run Setup Tenants
    print("\n[2] Running Setup Tenants Script:", file=out)
    try:
        # Add scripts to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        from scripts.setup_tenants import setup_tenants
        
        # Redirect stdout to capture script output
        # (This is a bit hacky for a view, but works for debug)
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            setup_tenants()
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        print(f"  CRITICAL ERROR running setup_tenants: {e}", file=out)
        import traceback
        traceback.print_exc(file=out)

    print("\n=== END DEBUG ===", file=out)
    return HttpResponse(out.getvalue(), content_type='text/plain')

@login_required
def manage_users(request):
    User = get_user_model()
    # Security check setup
    if getattr(request.user, 'user_type', 'none') != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    users_list = User.objects.all().order_by('-date_joined')

    if query:
        users_list = users_list.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        )
    
    if role_filter:
        users_list = users_list.filter(user_type=role_filter)

    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/manage_users.html', {
        'users': page_obj,
        'query': query,
        'role_filter': role_filter
    })

@login_required
def admin_password_reset(request, user_id):
    User = get_user_model()
    if getattr(request.user, 'user_type', 'none') != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')

    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = SetPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for {target_user.username} has been reset successfully.')
            return redirect('accounts:manage_users')
    else:
        form = SetPasswordForm(target_user)

    return render(request, 'accounts/admin_password_reset.html', {
        'form': form,
        'target_user': target_user
    })


# =============================================================================
# CUSTOM PASSWORD RESET VIEW FOR MULTI-TENANT
# =============================================================================
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm


class TenantPasswordResetView(PasswordResetView):
    """
    Custom password reset view that includes the tenant path in the reset URL.
    This ensures password reset emails contain the correct link for path-based
    multi-tenant routing (e.g., /school1/reset/xxx/xxx/).
    """
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    
    def get_extra_email_context(self):
        """Add tenant path to the domain so reset links work correctly."""
        context = super().get_extra_email_context() or {}
        
        # Get the tenant path prefix (e.g., '/school1')
        script_name = self.request.META.get('SCRIPT_NAME', '')
        
        # Build the full domain with tenant path
        # The default domain variable doesn't include the path
        if script_name:
            # Remove leading slash for cleaner URL construction
            tenant_path = script_name.lstrip('/')
            context['tenant_path'] = tenant_path
        else:
            context['tenant_path'] = ''
            
        return context

