from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tenants.decorators import require_addon
from tenants.models import PlatformSettings
from django.conf import settings
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from academics.models import Class, AcademicYear, ClassSubject, Activity, Timetable, GalleryImage, Resource, SchoolInfo, Subject
from teachers.models import Teacher, DutyAssignment, DutyWeek, LessonPlan
from students.models import Student, Attendance
from announcements.models import Announcement, Notification
from django.db.models import Q, Count, F, Window
from django.db.models.functions import RowNumber
from django.db import connection, transaction
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
import calendar
import datetime
import json
import secrets

from django.db.utils import OperationalError, ProgrammingError


from django.core.cache import cache as _cache

def _tenant_cache_key(prefix):
    """Return a per-tenant cache key to prevent cross-tenant data leakage."""
    from django.db import connection as _conn
    schema = getattr(_conn, 'schema_name', 'public')
    return f'{prefix}_{schema}'


def build_academic_calendar_widget(limit=5):
    cal_key = _tenant_cache_key(f'cal_widget_{limit}')
    cached = _cache.get(cal_key)
    if cached:
        return cached

    today = timezone.now().date()
    
    try:
        year_key = _tenant_cache_key('current_academic_year')
        current_year = _cache.get(year_key)
        if current_year is None:
            current_year = (
                AcademicYear.objects.filter(is_current=True).first()
                or AcademicYear.objects.order_by('-start_date').first()
            )
            _cache.set(year_key, current_year, 300)
    except ProgrammingError:
        current_year = None

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

    try:
        upcoming_activities = Activity.objects.filter(is_active=True, date__gte=today).order_by('date')[:limit]
        for activity in upcoming_activities:
            events.append({
                'title': activity.title,
                'date': activity.date,
                'tag': activity.tag or 'Activity',
            })
    except ProgrammingError:
        pass  # Table doesn't exist in this tenant schema

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

    result = {
        'academic_calendar_year': current_year.name if current_year else 'Not Set',
        'academic_calendar_events': upcoming_events,
        'academic_calendar_month_label': datetime.date(display_year, display_month, 1).strftime('%B %Y'),
        'academic_calendar_weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'academic_calendar_weeks': calendar_weeks,
    }
    _cache.set(cal_key, result, 600)  # 10 min
    return result


def _safe_count(model):
    """Return model.objects.count() safely, returning 0 on any DB error."""
    try:
        return model.objects.count()
    except Exception:
        return 0


def build_onboarding_checklist():
    """Compute the 8-step getting-started checklist for school admins."""
    from finance.models import FeeStructure
    from django.urls import reverse

    try:
        # Reuse the tenant cache primed by the dashboard setup check
        school_info = _cache.get(_tenant_cache_key('school_info'))
        if school_info is None:
            school_info = SchoolInfo.objects.first()
            _cache.set(_tenant_cache_key('school_info'), school_info, 300)
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


def pwa_launch(request):
    """Lightweight redirect endpoint for PWA start_url.

    Always returns a 302 (never cacheable HTML) so the service worker
    cannot serve a stale landing page when the user relaunches the app.
    """
    if request.user.is_authenticated:
        bound_schema = request.session.get('auth_tenant_schema')
        if bound_schema:
            return redirect(f'/{bound_schema}/dashboard/')
        if request.user.is_staff:
            return redirect('/tenants/landlord/')
        if getattr(request.user, 'user_type', '') == 'individual':
            return redirect('/u/dashboard/')
    return redirect('/')


@ensure_csrf_cookie
def homepage(request):
    # Route logic for different tenants
    is_public = False
    if hasattr(request, 'tenant'):
        is_public = (request.tenant.schema_name == 'public')
    
    # 1. Public Tenant -> Show SaaS Landing (template chosen by landlord admin)
    if is_public:
        # Authenticated user with an active school session → bounce to their dashboard
        if request.user.is_authenticated:
            bound_schema = request.session.get('auth_tenant_schema')
            if bound_schema:
                return redirect(f'/{bound_schema}/dashboard/')
            # Staff/superuser without a tenant session → landlord panel
            if request.user.is_staff:
                return redirect('/tenants/landlord/')
            # Individual portal users (developers / standalone teachers)
            if getattr(request.user, 'user_type', '') == 'individual':
                return redirect('/u/dashboard/')
            # Authenticated school user with no tenant binding — clear the
            # stale session so they can find their school and sign in again.
            logout(request)
            messages.info(request, 'Please find your school and sign in.')

        try:
            platform = PlatformSettings.get()
            template_name = platform.landing_template
        except Exception:
            template_name = 'home/swiss.html'
        return render(request, template_name)

    # 2. School Tenant -> Show School Dashboard/Home or redirect to Login
    # If user is not logged in on school tenant, better to show login?
    # Or show specific school landing page? For now, let's keep the activity feed home
    # but ensure it's generic.
    
    # If not logged in, maybe redirect to login for school context?
    # if not request.user.is_authenticated:
    #     return redirect('login') 
    
    # ... Continue with existing logic for school home ...
    activities = []
    
    # Safely query activities (table may not exist if migrations aren't run)
    try:
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
    except Exception:
        # Table doesn't exist or query failed - use fallback
        pass

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
    elif template_choice == 'artdeco':
        return render(request, 'home/artdeco.html', context)
    elif template_choice == 'japandi':
        return render(request, 'home/japandi.html', context)
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

from accounts.ratelimit import rate_limit_login

@rate_limit_login
def login_view(request):
    # If login is hit on the public path with a tenant-scoped next URL,
    # bounce to the tenant-prefixed login so auth/session checks run in
    # the correct tenant context from the start.
    if not request.META.get('SCRIPT_NAME'):
        next_hint = request.GET.get('next') or request.POST.get('next', '')
        if next_hint.startswith('/'):
            next_parts = next_hint.strip('/').split('/')
            tenant_hint = next_parts[0] if next_parts else ''
            if tenant_hint:
                from tenants.models import School
                tenant_exists = School.objects.filter(schema_name=tenant_hint, is_active=True).exists()
                if tenant_exists:
                    from urllib.parse import quote
                    encoded_next = quote(next_hint, safe='/?:=&')
                    return redirect(f'/{tenant_hint}/login/?next={encoded_next}')

    if request.user.is_authenticated:
        # If there's a safe next URL, go there; otherwise go to dashboard.
        next_url = request.GET.get('next') or request.POST.get('next', '')
        if next_url:
            from django.utils.http import url_has_allowed_host_and_scheme
            # Prepend SCRIPT_NAME (tenant prefix) if @login_required stripped it.
            script_name = request.META.get('SCRIPT_NAME', '')
            if script_name and next_url.startswith('/') and not next_url.startswith(script_name + '/'):
                next_url = script_name + next_url
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
        dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
        return redirect(dashboard_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Tenant admin accounts always get a persistent 1-year session so
            # they are never unexpectedly logged out after server restarts or
            # browser closes.  Other users follow the "Keep me logged in" checkbox.
            is_tenant_admin = getattr(user, 'user_type', None) == 'admin'
            remember_me = is_tenant_admin or (request.POST.get('remember_me') == '1')
            if remember_me:
                request.session.set_expiry(365 * 24 * 60 * 60)  # 1 year in seconds
            else:
                request.session.set_expiry(0)  # browser close
            # Bind session to the current tenant schema to prevent cross-tenant
            # identity leakage when users navigate between tenant paths.
            tenant_obj = getattr(request, 'tenant', None)
            if tenant_obj and getattr(tenant_obj, 'schema_name', '') and tenant_obj.schema_name != 'public':
                request.session['auth_tenant_schema'] = tenant_obj.schema_name
            else:
                request.session.pop('auth_tenant_schema', None)
            # Respect the ?next= parameter so @login_required redirects work.
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url:
                from django.utils.http import url_has_allowed_host_and_scheme
                # If @login_required supplied a next URL without the tenant prefix
                # (it uses path_info which strips SCRIPT_NAME), prepend the prefix
                # so the redirect lands on the correct tenant-scoped page.
                script_name = request.META.get('SCRIPT_NAME', '')
                if script_name and next_url.startswith('/') and not next_url.startswith(script_name + '/'):
                    next_url = script_name + next_url
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
            dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
            return redirect(dashboard_url)
        else:
            messages.error(request, 'Invalid credentials')
    
    next_url = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {'next': next_url})


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


def logout_view(request):
    """Log the user out. Works for both GET and POST to avoid @login_required loop."""
    if request.user.is_authenticated:
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
        # If a tenant-bound school user lands on public dashboard, route back
        # to their school context to avoid confusing cross-context sessions.
        bound_schema = request.session.get('auth_tenant_schema')
        if bound_schema and not user.is_staff:
            return redirect(f'/{bound_schema}/dashboard/')

        # Redirect staff users to landlord dashboard
        if user.is_staff:
            return redirect('/tenants/landlord/')
            
        # Individual portal users land on their own dashboard
        if getattr(user, 'user_type', '') == 'individual':
            return redirect('/u/dashboard/')

        # Authenticated non-staff user with no school binding — log out to
        # avoid an infinite redirect loop (dashboard → home → dashboard).
        if not user.is_superuser and not user.is_staff:
            logout(request)
            messages.info(request, 'Please find your school and sign in.')
            return redirect('login')
             
        from tenants.models import School, Domain
        context = {
            'schools_count': School.objects.exclude(schema_name='public').count(),
            'domains_count': Domain.objects.count(),
            'recent_schools': School.objects.exclude(schema_name='public').order_by('-created_on')[:10]
        }
        return render(request, 'tenants/dashboard_public.html', context)

    # === TENANT (SCHOOL) DASHBOARD ===
    
    # Check Onboarding Status for Admin — use the tenant cache set by the
    # context processor (or prime it now) to avoid a separate DB round-trip.
    if user.user_type == 'admin':
        try:
            info_key = _tenant_cache_key('school_info')
            school_info = _cache.get(info_key)
            if school_info is None:
                school_info = SchoolInfo.objects.first()
                _cache.set(info_key, school_info, 300)
            # If no info or setup not complete, send to wizard
            if not school_info or not school_info.setup_complete:
                return redirect('tenants:setup_wizard')
        except Exception:
            # Fallback if table missing or other error, let them pass or handle gracefully
            pass

    # Base query without slicing
    try:
        base_notices = Announcement.objects.filter(is_active=True).order_by('-created_at')
    except (OperationalError, ProgrammingError):
        base_notices = Announcement.objects.none()
    calendar_widget = build_academic_calendar_widget()
    
    if user.user_type == 'admin':
        # Admin gets top 5 of all active notices
        notices = base_notices[:5]
        try:
            message_notifications = Notification.objects.filter(
                recipient=user,
                is_read=False,
                alert_type='message',
            ).order_by('-created_at')[:5]
        except (OperationalError, ProgrammingError):
            message_notifications = []
        
        # Analytics Data
        chart_labels_classes = []
        chart_data_classes = []
        try:
            # 1. Students per Class (Top 5 largest classes)
            students_per_class = Student.objects.values('current_class__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            chart_labels_classes = [item['current_class__name'] or 'Unassigned' for item in students_per_class]
            chart_data_classes = [item['count'] for item in students_per_class]
        except (OperationalError, ProgrammingError, Exception):
            pass

        # 2. Daily Attendance (Last 7 days)
        today = timezone.now().date()
        date_7_days_ago = today - datetime.timedelta(days=6)
        chart_labels_attendance = []
        chart_data_attendance = []
        try:
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

            for i in range(7):
                d = date_7_days_ago + datetime.timedelta(days=i)
                chart_labels_attendance.append(d.strftime("%a"))  # Mon, Tue...
                chart_data_attendance.append(daily_presence.get(d, 0))
        except (OperationalError, ProgrammingError, Exception):
            for i in range(7):
                d = date_7_days_ago + datetime.timedelta(days=i)
                chart_labels_attendance.append(d.strftime("%a"))
                chart_data_attendance.append(0)

        try:
            onboarding = build_onboarding_checklist()
        except Exception:
            onboarding = None

        # Subscription / trial banner data — reuse request-level cache set by middleware
        subscription = None
        trial_days_left = None
        try:
            from django.utils import timezone as tz
            # _tenant_subscription is cached by TenantPathMiddleware.process_view();
            # fall back to a DB query only when that cache key is absent.
            subscription = getattr(request, '_tenant_subscription', None)
            if subscription is None and hasattr(request, 'tenant'):
                from tenants.subscription_models import SchoolSubscription
                # Use a savepoint so a ProgrammingError (missing column in legacy
                # tenant schemas) rolls back only the inner atomic block, leaving
                # the outer ATOMIC_REQUESTS transaction in a clean state.
                try:
                    with transaction.atomic():
                        subscription = SchoolSubscription.objects.defer(
                            'paystack_subscription_code',
                            'paystack_customer_code',
                            'mrr',
                        ).filter(school=request.tenant).first()
                except Exception:
                    subscription = None
            if subscription and subscription.status == 'trial' and subscription.trial_ends_at:
                delta = subscription.trial_ends_at - tz.now()
                trial_days_left = max(0, delta.days)
        except Exception:
            pass

        context = {
            'user': user,
            'notices': notices,
            'chart_labels_classes': json.dumps(chart_labels_classes),
            'chart_data_classes': json.dumps(chart_data_classes),
            'chart_labels_attendance': json.dumps(chart_labels_attendance),
            'chart_data_attendance': json.dumps(chart_data_attendance),
            'total_students': _safe_count(Student),
            'total_teachers': _safe_count(Teacher),
            'onboarding': onboarding,
            'message_notifications': message_notifications,
            'subscription': subscription,
            'trial_days_left': trial_days_left,
            **calendar_widget,
        }

        return render(request, 'dashboard/admin_dashboard.html', context)
    elif user.user_type == 'teacher':
        try:
            teacher_profile = Teacher.objects.filter(user=user).first()
        except (OperationalError, ProgrammingError):
            messages.warning(request, "Teacher module is not yet set up. Please ask the school admin to complete the setup.")
            return render(request, 'dashboard/teacher_dashboard.html', {
                'user': user,
                'teacher_has_classes': False,
                'teacher_class_count': 0,
                'total_students_taught': 0,
                'notices': [],
                'next_duty': None,
                'todays_classes': [],
                'next_class_reminder': None,
                'recent_resources': [],
                'resource_fields_available': False,
                'pulse_summary': {'total_sessions': 0, 'last_session': None, 'last_response_rate': 0, 'last_at_risk_count': 0},
                'pinned_addons': [],
                'custom_quick_actions': [],
                'owned_addons': [],
                **calendar_widget,
            })
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

        # === Padi-T Lesson Reminders ===
        # Match today's timetable entries with lesson plans for the current week
        next_class_reminder = None
        try:
            current_date_for_week = timezone.now().date()
            current_duty_week = DutyWeek.objects.filter(
                academic_year=current_year,
                start_date__lte=current_date_for_week,
                end_date__gte=current_date_for_week
            ).first() if current_year else None

            if current_duty_week and teacher_profile:
                week_num = current_duty_week.week_number
                # Fetch all lesson plans for this teacher this week
                week_plans = LessonPlan.objects.filter(
                    teacher=teacher_profile,
                    week_number=week_num
                ).select_related('subject', 'school_class')

                # Build lookup: (subject_id, class_id) → lesson plan
                plan_lookup = {}
                for plan in week_plans:
                    key = (plan.subject_id, plan.school_class_id)
                    plan_lookup[key] = plan

                # Attach lesson topic to each timetable period
                for p in todays_classes:
                    key = (p.class_subject.subject_id, p.class_subject.class_name_id)
                    plan = plan_lookup.get(key)
                    if plan:
                        p.lesson_topic = plan.topic
                        p.lesson_objectives = plan.objectives
                    else:
                        p.lesson_topic = None
                        p.lesson_objectives = None

                # Find the next upcoming class (or ongoing) for the Padi-T banner
                for p in todays_classes:
                    if p.is_ongoing or p.start_time > current_time:
                        if p.lesson_topic:
                            next_class_reminder = p
                        break
        except Exception:
            pass  # Gracefully degrade — schedule still shows without topics

        # === Related Files by Scheduled Subject/Class ===
        # Attach quick resources so each schedule item can expand into relevant materials.
        try:
            from collections import defaultdict
            from teachers.models import Presentation

            period_keys = {
                (p.class_subject.subject_id, p.class_subject.class_name_id)
                for p in todays_classes
            }
            subject_ids = {k[0] for k in period_keys}
            class_ids_for_periods = {k[1] for k in period_keys}

            plans_by_key = defaultdict(list)
            slides_by_key = defaultdict(list)
            resources_by_key = defaultdict(list)
            plan_count_by_key = defaultdict(int)
            slide_count_by_key = defaultdict(int)
            resource_count_by_key = defaultdict(int)

            if period_keys:
                for row in (
                    LessonPlan.objects
                    .filter(
                        teacher=teacher_profile,
                        subject_id__in=subject_ids,
                        school_class_id__in=class_ids_for_periods,
                    )
                    .values('subject_id', 'school_class_id')
                    .annotate(total=Count('id'))
                ):
                    key = (row['subject_id'], row['school_class_id'])
                    if key in period_keys:
                        plan_count_by_key[key] = row['total']

                for row in (
                    Presentation.objects
                    .filter(
                        teacher=teacher_profile,
                        subject_id__in=subject_ids,
                        school_class_id__in=class_ids_for_periods,
                    )
                    .values('subject_id', 'school_class_id')
                    .annotate(total=Count('id'))
                ):
                    key = (row['subject_id'], row['school_class_id'])
                    if key in period_keys:
                        slide_count_by_key[key] = row['total']

                for row in (
                    Resource.objects
                    .filter(
                        class_subject__teacher=teacher_profile,
                        class_subject__subject_id__in=subject_ids,
                        class_subject__class_name_id__in=class_ids_for_periods,
                    )
                    .values('class_subject__subject_id', 'class_subject__class_name_id')
                    .annotate(total=Count('id'))
                ):
                    key = (row['class_subject__subject_id'], row['class_subject__class_name_id'])
                    if key in period_keys:
                        resource_count_by_key[key] = row['total']

                plans_qs = (
                    LessonPlan.objects
                    .filter(
                        teacher=teacher_profile,
                        subject_id__in=subject_ids,
                        school_class_id__in=class_ids_for_periods,
                    )
                    .annotate(
                        row_number=Window(
                            expression=RowNumber(),
                            partition_by=[F('subject_id'), F('school_class_id')],
                            order_by=F('id').desc(),
                        )
                    )
                    .filter(row_number__lte=3)
                    .select_related('subject', 'school_class')
                    .order_by('subject_id', 'school_class_id', '-id')
                )
                for plan in plans_qs:
                    key = (plan.subject_id, plan.school_class_id)
                    if key in period_keys:
                        plans_by_key[key].append(plan)

                slides_qs = (
                    Presentation.objects
                    .filter(
                        teacher=teacher_profile,
                        subject_id__in=subject_ids,
                        school_class_id__in=class_ids_for_periods,
                    )
                    .annotate(
                        row_number=Window(
                            expression=RowNumber(),
                            partition_by=[F('subject_id'), F('school_class_id')],
                            order_by=[F('updated_at').desc(), F('id').desc()],
                        )
                    )
                    .filter(row_number__lte=3)
                    .select_related('subject', 'school_class')
                    .order_by('subject_id', 'school_class_id', '-updated_at', '-id')
                )
                for deck in slides_qs:
                    key = (deck.subject_id, deck.school_class_id)
                    if key in period_keys:
                        slides_by_key[key].append(deck)

                resource_qs = (
                    Resource.objects
                    .filter(
                        class_subject__teacher=teacher_profile,
                        class_subject__subject_id__in=subject_ids,
                        class_subject__class_name_id__in=class_ids_for_periods,
                    )
                    .annotate(
                        row_number=Window(
                            expression=RowNumber(),
                            partition_by=[F('class_subject__subject_id'), F('class_subject__class_name_id')],
                            order_by=[F('uploaded_at').desc(), F('id').desc()],
                        )
                    )
                    .filter(row_number__lte=3)
                    .select_related('class_subject', 'class_subject__subject', 'class_subject__class_name')
                    .order_by('class_subject__subject_id', 'class_subject__class_name_id', '-uploaded_at', '-id')
                )
                for res in resource_qs:
                    key = (res.class_subject.subject_id, res.class_subject.class_name_id)
                    if key in period_keys:
                        resources_by_key[key].append(res)

            for p in todays_classes:
                key = (p.class_subject.subject_id, p.class_subject.class_name_id)
                p.related_lesson_plans = plans_by_key.get(key, [])
                p.related_slides = slides_by_key.get(key, [])
                p.related_resources = resources_by_key.get(key, [])
                p.related_lesson_plans_count = plan_count_by_key.get(key, 0)
                p.related_slides_count = slide_count_by_key.get(key, 0)
                p.related_resources_count = resource_count_by_key.get(key, 0)
                p.has_more_lesson_plans = p.related_lesson_plans_count > len(p.related_lesson_plans)
                p.has_more_slides = p.related_slides_count > len(p.related_slides)
                p.has_more_resources = p.related_resources_count > len(p.related_resources)
        except Exception:
            for p in todays_classes:
                p.related_lesson_plans = []
                p.related_slides = []
                p.related_resources = []
                p.related_lesson_plans_count = 0
                p.related_slides_count = 0
                p.related_resources_count = 0
                p.has_more_lesson_plans = False
                p.has_more_slides = False
                p.has_more_resources = False

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
        try:
            teacher_notices = base_notices.filter(target_audience__in=['all', 'staff', 'teachers'])[:5]
        except Exception:
            teacher_notices = []

        # === Digital Pulse Summary for Dashboard Widget ===
        pulse_summary = {
            'total_sessions': 0,
            'last_session': None,
            'last_response_rate': 0,
            'last_at_risk_count': 0,
        }
        try:
            from academics.pulse_models import PulseSession
            sessions_qs = PulseSession.objects.filter(
                teacher=teacher_profile
            ).order_by('-created_at')
            pulse_summary['total_sessions'] = sessions_qs.count()
            last_session = sessions_qs.first()
            if last_session:
                pulse_summary['last_session'] = last_session
                total_s = last_session.total_students
                responded = last_session.responded_count
                pulse_summary['last_response_rate'] = round(
                    (responded / total_s * 100) if total_s > 0 else 0
                )
                # at-risk: submitted AND answered Q2=True (believed the misconception)
                pulse_summary['last_at_risk_count'] = last_session.responses.filter(
                    submitted_at__isnull=False, q2_answer=True
                ).count()
        except Exception:
            pass

        # === Homework Status Summary ===
        hw_summary = {'active': 0, 'submissions_pending': 0, 'overdue': 0}
        try:
            from homework.models import Homework, Submission
            today = timezone.localdate()
            teacher_hw = Homework.objects.filter(teacher=teacher_profile)
            active_hw = teacher_hw.filter(due_date__gte=today)
            hw_summary['active'] = active_hw.count()
            hw_summary['overdue'] = teacher_hw.filter(due_date__lt=today).count()
            # Pending = students who haven't submitted active homework
            for hw in active_hw[:10]:  # cap to avoid heavy queries
                expected = Student.objects.filter(current_class=hw.target_class).count()
                submitted = Submission.objects.filter(homework=hw).values('student').distinct().count()
                hw_summary['submissions_pending'] += max(0, expected - submitted)
        except Exception:
            pass

        # === Class Performance Snapshot (avg total_score per class) ===
        class_perf = []
        try:
            from students.models import Grade
            from django.db.models import Avg
            if current_year and class_ids:
                perf_qs = (
                    Grade.objects.filter(
                        academic_year=current_year,
                        student__current_class_id__in=class_ids,
                    )
                    .values('student__current_class__name')
                    .annotate(avg_score=Avg('total_score'))
                    .order_by('student__current_class__name')
                )
                class_perf = [
                    {'class_name': p['student__current_class__name'], 'avg': round(float(p['avg_score'] or 0), 1)}
                    for p in perf_qs
                ]
        except Exception:
            pass

        # === Today's Attendance Pulse ===
        att_pulse = {'marked': 0, 'present': 0, 'absent': 0, 'total_expected': 0}
        try:
            today = timezone.localdate()
            if class_ids:
                att_qs = Attendance.objects.filter(
                    date=today,
                    student__current_class_id__in=class_ids,
                )
                att_pulse['marked'] = att_qs.count()
                att_pulse['present'] = att_qs.filter(status='present').count()
                att_pulse['absent'] = att_qs.filter(status='absent').count()
                att_pulse['total_expected'] = Student.objects.filter(
                    current_class_id__in=class_ids
                ).count()
        except Exception:
            pass

        # === Pinned Add-ons & Custom Quick Actions ===
        pinned_addons = []
        custom_quick_actions = []
        owned_addon_list = []
        try:
            with transaction.atomic():
                from teachers.models import DashboardPin, QuickAction as TeacherQuickAction, TeacherAddOnPurchase
                from teachers.views import ADDON_LAUNCH_URLS

                # Pinned addons — pass url_name for template-side resolution
                pins = list(DashboardPin.objects.filter(teacher=user).select_related('addon'))
                pinned_addon_ids = {p.addon_id for p in pins}
                for pin in pins:
                    pinned_addons.append({
                        'pin_id': pin.id,
                        'addon_id': pin.addon.id,
                        'name': pin.addon.name,
                        'icon': pin.addon.icon,
                        'slug': pin.addon.slug,
                        'url_name': ADDON_LAUNCH_URLS.get(pin.addon.slug, ''),
                    })

                # Custom quick actions — pass url_name for template-side resolution
                qa_qs = TeacherQuickAction.objects.filter(teacher=user)
                for qa in qa_qs:
                    custom_quick_actions.append({
                        'label': qa.label, 'icon': qa.icon,
                        'color': qa.color,
                        'url_name': qa.url_name,
                    })

                # All owned addons (for pin picker)
                owned_ids = TeacherAddOnPurchase.objects.filter(
                    teacher=user, is_active=True
                ).values_list('addon_id', flat=True)
                from teachers.models import TeacherAddOn
                for addon in TeacherAddOn.objects.filter(id__in=owned_ids, is_active=True):
                    owned_addon_list.append({
                        'id': addon.id,
                        'name': addon.name,
                        'icon': addon.icon,
                        'pinned': addon.id in pinned_addon_ids,
                    })
        except Exception:
            pinned_addons = []
            custom_quick_actions = []
            owned_addon_list = []

        teacher_context = {
            'user': user,
            'teacher_has_classes': len(class_ids) > 0,
            'teacher_class_count': len(class_ids),
            'total_students_taught': teacher_students_count,
            'notices': teacher_notices,
            'next_duty': next_duty,
            'todays_classes': todays_classes,
            'next_class_reminder': next_class_reminder,
            'recent_resources': recent_resources,
            'resource_fields_available': resource_fields_available,
            'pulse_summary': pulse_summary,
            'hw_summary': hw_summary,
            'class_perf': class_perf,
            'class_perf_json': json.dumps(class_perf),
            'att_pulse': att_pulse,
            'pinned_addons': pinned_addons,
            'custom_quick_actions': custom_quick_actions,
            'owned_addons': owned_addon_list,
            **calendar_widget,
        }

        return render(request, 'dashboard/teacher_dashboard.html', teacher_context)
    elif user.user_type == 'student':
        # Redirect to enhanced student dashboard
        return redirect('students:student_dashboard')
    elif user.user_type == 'parent':
        from finance.models import StudentFee
        from students.models import Attendance, Grade
        try:
            parent_notices = base_notices.filter(target_audience__in=['all', 'parents'])
        except Exception:
            parent_notices = base_notices
        
        # Calculate fees for all children
        try:
            parent_profile = getattr(user, 'parent_profile', None)
            if not parent_profile:
                 # Fallback/Auto-create logic or specific parents app retrieval
                 from parents.models import Parent
                 parent_profile = Parent.objects.filter(user=user).first()
            
            if parent_profile:
                import datetime as _dt
                from django.db.models import Sum as _Sum, Value as _V, DecimalField as _DF, Subquery, OuterRef
                from django.db.models.functions import Coalesce as _Coal
                from finance.models import Payment
                from academics.gamification_models import StudentXP as _StudentXP

                thirty_ago = timezone.now().date() - _dt.timedelta(days=30)
                academic_year = AcademicYear.objects.filter(is_current=True).first()

                # Subqueries for fee totals (avoids per-child fee loops)
                fee_payable_sq = (
                    StudentFee.objects.filter(student=OuterRef('pk'))
                    .values('student')
                    .annotate(total=_Sum('amount_payable'))
                    .values('total')
                )
                fee_paid_sq = (
                    Payment.objects.filter(student_fee__student=OuterRef('pk'))
                    .values('student_fee__student')
                    .annotate(total=_Sum('amount'))
                    .values('total')
                )

                children = (
                    parent_profile.children
                    .select_related('user', 'current_class')
                    .annotate(
                        att_total=Count('attendance', filter=Q(attendance__date__gte=thirty_ago)),
                        att_present=Count('attendance', filter=Q(attendance__date__gte=thirty_ago, attendance__status='present')),
                        fee_payable=_Coal(Subquery(fee_payable_sq), _V(0), output_field=_DF()),
                        fee_paid_amt=_Coal(Subquery(fee_paid_sq), _V(0), output_field=_DF()),
                    )
                )

                total_outstanding = 0
                total_paid = 0
                children_data = []

                # Prefetch recent grades and XP for all children in bulk
                child_ids = [c.pk for c in children]
                from collections import defaultdict
                grade_map = defaultdict(list)
                if academic_year:
                    for g in Grade.objects.filter(student_id__in=child_ids, academic_year=academic_year).select_related('subject').order_by('-id'):
                        if len(grade_map[g.student_id]) < 5:
                            grade_map[g.student_id].append(g)
                xp_map = {x.student_id: x for x in _StudentXP.objects.filter(student_id__in=child_ids)}

                for child in children:
                    child_balance = float(child.fee_payable) - float(child.fee_paid_amt)
                    child_paid_val = float(child.fee_paid_amt)
                    total_outstanding += child_balance
                    total_paid += child_paid_val
                    att_pct = round((child.att_present / child.att_total * 100) if child.att_total > 0 else 0, 1)

                    children_data.append({
                        'student': child,
                        'balance': child_balance,
                        'paid': child_paid_val,
                        'att_pct': att_pct,
                        'att_present': child.att_present,
                        'att_total': child.att_total,
                        'recent_grades': grade_map.get(child.pk, []),
                        'xp': xp_map.get(child.pk),
                    })

                # Summary stats for hero section
                avg_attendance = round(sum(cd['att_pct'] for cd in children_data) / len(children_data), 1) if children_data else 0
                all_grades_flat = [g for glist in grade_map.values() for g in glist]
                avg_grade = round(sum(g.total_score for g in all_grades_flat) / len(all_grades_flat), 1) if all_grades_flat else 0
                total_xp = sum((xp_map[cid].total_xp if xp_map.get(cid) else 0) for cid in child_ids)
            else:
                children = []
                children_data = []
                total_outstanding = 0
                total_paid = 0
                avg_attendance = 0
                avg_grade = 0
                total_xp = 0

        except Exception as e:
            children = []
            children_data = []
            total_outstanding = 0
            total_paid = 0
            avg_attendance = 0
            avg_grade = 0
            total_xp = 0

        return render(request, 'dashboard/parent_dashboard.html', {
            'user': user, 
            'notices': parent_notices,
            'children': children,
            'children_data': children_data,
            'summary_stats': {
                'avg_attendance': avg_attendance,
                'avg_grade': avg_grade,
                'total_xp': total_xp,
                'child_count': len(children_data),
            },
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
def session_debug(request):
    """
    Lightweight session diagnostic endpoint.
    Staff-only (works in production too so Vercel sessions can be inspected).
    """
    from django.conf import settings as _settings
    if not request.user.is_authenticated or not request.user.is_staff:
        raise Http404
    from django.db import connection as db_conn
    import os as _os

    session_engine = getattr(_settings, 'SESSION_ENGINE', 'django.contrib.sessions.backends.db')
    using_signed_cookies = 'signed_cookies' in session_engine

    # Only check DB session table when using a DB-backed engine
    session_table_exists = 'N/A (signed_cookies engine)' if using_signed_cookies else False
    session_row_count = 'N/A' if using_signed_cookies else None
    if not using_signed_cookies:
        try:
            with db_conn.cursor() as cursor:
                tables = db_conn.introspection.table_names(cursor)
                session_table_exists = 'django_session' in tables
                if session_table_exists:
                    cursor.execute("SELECT COUNT(*) FROM django_session")
                    session_row_count = cursor.fetchone()[0]
        except Exception as e:
            session_table_exists = f"ERROR: {e}"

    # Check static files
    static_root = str(_settings.STATIC_ROOT) if _settings.STATIC_ROOT else None
    static_files_count = 0
    if static_root:
        try:
            for _root, _dirs, _files in _os.walk(static_root):
                static_files_count += len(_files)
        except Exception:
            static_files_count = -1

    # For signed_cookies, session_key is always None but session.keys() still works
    session_data_keys = list(request.session.keys()) if request.session else []

    data = {
        'debug_mode': _settings.DEBUG,
        'db_schema': getattr(db_conn, 'schema_name', 'unknown'),
        'tenant': str(getattr(request, 'tenant', 'none')),
        'tenant_schema': getattr(getattr(request, 'tenant', None), 'schema_name', 'none'),
        'authenticated': request.user.is_authenticated,
        'username': str(request.user),
        'session_engine': session_engine,
        'session_key': request.session.session_key,
        'session_cookie_in_request': 'sessionid' in request.COOKIES,
        'session_cookie_value_prefix': request.COOKIES.get('sessionid', '')[:8] + '...' if request.COOKIES.get('sessionid') else None,
        'session_data_keys': session_data_keys,
        'session_table_exists': session_table_exists,
        'session_row_count': session_row_count,
        'session_settings': {
            'SESSION_ENGINE': session_engine,
            'SESSION_COOKIE_SECURE': getattr(_settings, 'SESSION_COOKIE_SECURE', False),
            'SESSION_COOKIE_SAMESITE': getattr(_settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
            'SESSION_COOKIE_AGE': getattr(_settings, 'SESSION_COOKIE_AGE', 1209600),
            'CSRF_COOKIE_SECURE': getattr(_settings, 'CSRF_COOKIE_SECURE', False),
            'SECURE_SSL_REDIRECT': getattr(_settings, 'SECURE_SSL_REDIRECT', False),
        },
        'request_meta': {
            'HTTP_X_FORWARDED_PROTO': request.META.get('HTTP_X_FORWARDED_PROTO'),
            'SCRIPT_NAME': request.META.get('SCRIPT_NAME'),
            'PATH_INFO': request.META.get('PATH_INFO'),
            'HTTP_HOST': request.META.get('HTTP_HOST'),
            'is_secure': request.is_secure(),
        },
        'search_path_set_schemas': getattr(db_conn, 'search_path_set_schemas', 'N/A'),
        'connection_schema_name': getattr(db_conn, 'schema_name', 'N/A'),
        'session_save_every_request': getattr(_settings, 'SESSION_SAVE_EVERY_REQUEST', False),
        'secret_key_source': (
            'SECRET_KEY env' if _os.environ.get('SECRET_KEY') else
            'DJANGO_SECRET_KEY env' if _os.environ.get('DJANGO_SECRET_KEY') else
            'SECRET_KEY_BASE env' if _os.environ.get('SECRET_KEY_BASE') else
            'DEFAULT (insecure!)'
        ),
        'secret_key_prefix': _settings.SECRET_KEY[:8] + '...',
        'session_cookie_size_bytes': len(request.COOKIES.get('sessionid', '')),
        'static_root': static_root,
        'static_files_count': static_files_count,
        'vercel': _os.environ.get('VERCEL', 'not set'),
        'allowed_hosts': _settings.ALLOWED_HOSTS,
    }
    return JsonResponse(data, json_dumps_params={'indent': 2})


@login_required
def tenant_schema_health(request):
    """
    Check whether critical tenant tables exist in the CURRENT schema.
    Staff-only to avoid exposing internal schema details.
    """
    if not request.user.is_staff:
        raise Http404

    required_tables = [
        'accounts_user',
        'teachers_teacher',
        'students_student',
        'finance_feestructure',
        'finance_studentfee',
        'finance_payment',
        'academics_class',
        'academics_subject',
        'django_migrations',
    ]

    try:
        with connection.cursor() as cursor:
            existing_tables = set(connection.introspection.table_names(cursor))
    except Exception as exc:
        return JsonResponse(
            {
                'ok': False,
                'error': str(exc),
                'tenant_schema': getattr(getattr(request, 'tenant', None), 'schema_name', 'unknown'),
            },
            status=500,
        )

    missing = [t for t in required_tables if t not in existing_tables]

    return JsonResponse(
        {
            'ok': len(missing) == 0,
            'tenant_schema': getattr(getattr(request, 'tenant', None), 'schema_name', 'unknown'),
            'required_tables': required_tables,
            'missing_tables': missing,
            'hint': (
                'Run tenant migrations for this schema, e.g. '
                'python manage.py migrate_schemas --schema_name=<tenant_schema>'
            ) if missing else 'All critical tenant tables are present.',
        },
        json_dumps_params={'indent': 2},
    )


def env_health(request):
    """
    Deployment environment health endpoint.

    Returns presence/validity checks for required env vars without exposing secret values.
    Access is allowed in DEBUG, by authenticated staff users, or with a valid
    X-Healthcheck-Token header / ?token=... matching HEALTHCHECK_TOKEN.
    """
    from django.conf import settings as _settings
    import os as _os

    healthcheck_token = (_os.environ.get('HEALTHCHECK_TOKEN') or '').strip()
    provided_token = (
        request.headers.get('X-Healthcheck-Token')
        or request.GET.get('token')
        or ''
    ).strip()
    token_ok = bool(healthcheck_token) and bool(provided_token) and secrets.compare_digest(provided_token, healthcheck_token)
    staff_ok = request.user.is_authenticated and request.user.is_staff

    if not (_settings.DEBUG or staff_ok or token_ok):
        raise Http404

    default_secret = getattr(_settings, 'DEFAULT_SECRET_KEY', '')
    secret_key = (
        _os.environ.get('SECRET_KEY')
        or _os.environ.get('DJANGO_SECRET_KEY')
        or _os.environ.get('SECRET_KEY_BASE')
        or getattr(_settings, 'SECRET_KEY', '')
    )
    checks = {
        'SECRET_KEY': bool(secret_key) and secret_key != default_secret and not str(secret_key).startswith('django-insecure'),
        'DATABASE_URL': bool(_os.environ.get('DATABASE_URL', '').strip()),
    }

    optional = {
        'OPENAI_API_KEY': bool(_os.environ.get('OPENAI_API_KEY', '').strip()),
        'PAYSTACK_SECRET_KEY': bool(_os.environ.get('PAYSTACK_SECRET_KEY', '').strip()),
    }

    missing_required = [name for name, ok in checks.items() if not ok]
    payload = {
        'ok': len(missing_required) == 0,
        'debug': _settings.DEBUG,
        'environment': {
            'vercel': _os.environ.get('VERCEL', '0') == '1',
        },
        'required': checks,
        'optional': optional,
        'missing_required': missing_required,
    }
    return JsonResponse(payload, status=200 if payload['ok'] else 503)


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
def delete_user(request, user_id):
    User = get_user_model()
    if getattr(request.user, 'user_type', 'none') != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('accounts:manage_users')

    target_user = get_object_or_404(User, pk=user_id)

    if target_user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account while logged in.')
        return redirect('accounts:manage_users')

    if target_user.user_type == 'admin':
        remaining_admins = User.objects.filter(user_type='admin').exclude(id=target_user.id).count()
        if remaining_admins == 0:
            messages.error(request, 'Cannot delete the last admin account.')
            return redirect('accounts:manage_users')

    username = target_user.username
    try:
        target_user.delete()
        messages.success(request, f'User "{username}" was removed successfully.')
    except Exception as exc:
        messages.error(request, f'Could not remove user "{username}": {exc}')

    return redirect('accounts:manage_users')

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


# ---------------------------------------------------------------------------
# Admin Analytics Dashboard
# ---------------------------------------------------------------------------

@login_required
@require_addon('advanced-analytics')
def school_analytics(request):
    """School-wide analytics: enrollment, fees, attendance, grades."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from finance.models import StudentFee, Payment
    from students.models import Grade
    from django.db.models import Avg, Sum

    today = timezone.now().date()
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Safe defaults
    total_students = 0
    total_teachers = 0
    class_labels = []
    class_data = []
    fee_status = {'paid': 0, 'partial': 0, 'unpaid': 0}
    fee_total_expected = 0
    fee_total_collected = 0
    heatmap_labels = []
    heatmap_data = []
    grade_labels = []
    grade_data = []
    grade_dist_labels = []
    grade_dist_data = []
    attendance_rate = 0
    recent_payments = []

    try:
        # --- Totals ---
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()

        # --- Students per class ---
        class_qs = Student.objects.values('current_class__name').annotate(
            count=Count('id')
        ).order_by('-count').exclude(current_class__isnull=True)
        class_labels = [r['current_class__name'] for r in class_qs]
        class_data = [r['count'] for r in class_qs]

        # --- Fee collection summary ---
        fee_status = {
            'paid': StudentFee.objects.filter(status='paid').count(),
            'partial': StudentFee.objects.filter(status='partial').count(),
            'unpaid': StudentFee.objects.filter(status='unpaid').count(),
        }
        fee_total_expected = StudentFee.objects.aggregate(
            total=Sum('amount_payable')
        )['total'] or 0
        fee_total_collected = Payment.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # --- 30-day attendance heatmap (present count per day) ---
        date_30_ago = today - datetime.timedelta(days=29)
        attendance_qs = Attendance.objects.filter(
            date__gte=date_30_ago, status='present'
        ).values('date').annotate(count=Count('id')).order_by('date')
        attendance_map = {r['date']: r['count'] for r in attendance_qs}
        for i in range(30):
            d = date_30_ago + datetime.timedelta(days=i)
            heatmap_labels.append(d.strftime('%b %d'))
            heatmap_data.append(attendance_map.get(d, 0))

        # --- Average grade per class ---
        grade_qs = Grade.objects.values(
            'student__current_class__name'
        ).annotate(avg=Avg('total_score')).order_by('-avg').exclude(
            student__current_class__isnull=True
        )
        grade_labels = [r['student__current_class__name'] for r in grade_qs]
        grade_data = [round(float(r['avg']), 1) if r['avg'] else 0 for r in grade_qs]

        # --- Grade distribution (A+ through F) ---
        all_grades = Grade.objects.all()
        if current_year:
            all_grades = all_grades.filter(academic_year=current_year)
        grade_buckets = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'F': 0}
        for g in all_grades.values_list('total_score', flat=True):
            if g is None:
                continue
            pct = float(g)
            if pct >= 90:
                grade_buckets['A+'] += 1
            elif pct >= 80:
                grade_buckets['A'] += 1
            elif pct >= 70:
                grade_buckets['B+'] += 1
            elif pct >= 60:
                grade_buckets['B'] += 1
            elif pct >= 50:
                grade_buckets['C'] += 1
            else:
                grade_buckets['F'] += 1
        grade_dist_labels = list(grade_buckets.keys())
        grade_dist_data = list(grade_buckets.values())

        # --- Overall attendance rate ---
        total_records = Attendance.objects.count()
        present_records = Attendance.objects.filter(status='present').count()
        attendance_rate = round((present_records / total_records * 100), 1) if total_records else 0

        # --- Recent 10 payments ---
        recent_payments = list(Payment.objects.select_related(
            'student_fee__student__user'
        ).order_by('-date')[:10])

        # --- SchoolPadi AI activity ---
        from academics.tutor_models import TutorSession as _TS
        from academics.gamification_models import StudentXP as _SXPA
        from django.db.models import Avg as _AvgA
        date_30_ago_padi = today - datetime.timedelta(days=30)
        padi_total_sessions = _TS.objects.count()
        padi_active_30d = _TS.objects.filter(
            started_at__date__gte=date_30_ago_padi
        ).values('student').distinct().count()
        padi_avg_streak = round(
            float(_SXPA.objects.aggregate(a=_AvgA('current_streak'))['a'] or 0), 1
        )
        padi_top_xp = list(
            _SXPA.objects.select_related('student__user').order_by('-total_xp')[:5]
        )

    except Exception as e:
        messages.warning(request, f'Some analytics data could not be loaded: {e}')

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'class_labels': json.dumps(class_labels),
        'class_data': json.dumps(class_data),
        'fee_status': fee_status,
        'fee_total_expected': fee_total_expected,
        'fee_total_collected': fee_total_collected,
        'heatmap_labels': json.dumps(heatmap_labels),
        'heatmap_data': json.dumps(heatmap_data),
        'grade_labels': json.dumps(grade_labels),
        'grade_data': json.dumps(grade_data),
        'grade_dist_labels': json.dumps(grade_dist_labels),
        'grade_dist_data': json.dumps(grade_dist_data),
        'attendance_rate': attendance_rate,
        'recent_payments': recent_payments,
        'current_year': current_year,
        # SchoolPadi AI
        'padi_total_sessions': locals().get('padi_total_sessions', 0),
        'padi_active_30d': locals().get('padi_active_30d', 0),
        'padi_avg_streak': locals().get('padi_avg_streak', 0),
        'padi_top_xp': locals().get('padi_top_xp', []),
    }
    return render(request, 'accounts/school_analytics.html', context)


# ─── Onboarding endpoints ────────────────────────────────────────────────────

@login_required
def onboarding_dismiss(request):
    """Mark onboarding as dismissed (POST only). Widget will not appear again."""
    if request.method == 'POST':
        from accounts.models import OnboardingProgress
        progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)
        progress.dismissed = True
        progress.save()
        request.session['onboarding_done'] = True
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def onboarding_complete_step(request):
    """Manually mark a specific step as completed (POST only).
    Body: step_id=<str>
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    step_id = request.POST.get('step_id', '').strip()
    if not step_id:
        return JsonResponse({'error': 'step_id required'}, status=400)

    from accounts.onboarding import ONBOARDING_STEPS
    from accounts.models import OnboardingProgress

    role_steps = ONBOARDING_STEPS.get(request.user.user_type, [])
    valid_ids = {s['id'] for s in role_steps}

    if step_id not in valid_ids:
        return JsonResponse({'error': 'Invalid step_id'}, status=400)

    progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)
    changed = progress.mark_step(step_id)

    all_done = valid_ids.issubset(set(progress.steps_completed))
    if all_done and not progress.completed_at:
        from django.utils import timezone
        progress.completed_at = timezone.now()

    if changed or all_done:
        progress.save()

    return JsonResponse({'ok': True, 'all_done': all_done})


@login_required
def user_settings(request):
    """User-facing app settings: profile info and notification preferences."""
    from accounts.models import UserSettings, User as TenantUser
    from accounts.forms import UserProfileForm, UserSettingsForm
    from django.db import IntegrityError

    # In multi-tenant mode the current user may only exist in the public schema
    # (e.g. a superuser browsing a tenant URL).  Check BEFORE doing any INSERT
    # so we never corrupt the outer ATOMIC_REQUESTS transaction with a FK
    # violation that PostgreSQL would abort the whole connection for.
    #
    # IMPORTANT: We must query the tenant-specific table directly.
    # A normal ORM .exists() check uses search_path which includes 'public'
    # as fallback — so a user that only exists in public.accounts_user
    # would appear to exist, but the FK on the tenant's accounts_usersettings
    # points to the tenant's accounts_user table where that user is absent.
    from django.db import connection as _conn
    _tenant_schema = getattr(getattr(request, 'tenant', None), 'schema_name', 'public')
    with _conn.cursor() as _cur:
        _cur.execute(
            'SELECT 1 FROM "{}".accounts_user WHERE id = %s LIMIT 1'.format(
                _tenant_schema.replace('"', '')
            ),
            [request.user.pk],
        )
        _user_exists_in_tenant = _cur.fetchone() is not None
    if _user_exists_in_tenant:
        user_prefs, _ = UserSettings.objects.get_or_create(user=request.user)
    else:
        user_prefs = UserSettings(user=request.user)  # in-memory, not saved

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            prefs_form = UserSettingsForm(instance=user_prefs)
            if profile_form.is_valid():
                if _user_exists_in_tenant:
                    profile_form.save()
                    messages.success(request, 'Profile updated successfully.')
                else:
                    messages.warning(request, 'Profile changes cannot be saved in this tenant context.')
                return redirect(request.path + '?tab=profile')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif action == 'notifications':
            profile_form = UserProfileForm(instance=request.user)
            prefs_form = UserSettingsForm(request.POST, instance=user_prefs)
            if prefs_form.is_valid():
                if _user_exists_in_tenant:
                    prefs_form.save()
                    messages.success(request, 'Notification preferences saved.')
                else:
                    messages.warning(request, 'Preferences cannot be saved in this tenant context.')
                return redirect(request.path + '?tab=notifications')

        else:
            profile_form = UserProfileForm(instance=request.user)
            prefs_form = UserSettingsForm(instance=user_prefs)
    else:
        profile_form = UserProfileForm(instance=request.user)
        prefs_form = UserSettingsForm(instance=user_prefs)

    return render(request, 'accounts/settings.html', {
        'profile_form': profile_form,
        'prefs_form': prefs_form,
        'active_tab': request.GET.get('tab', 'profile'),
    })


# ── Contact Form Submission ─────────────────────────────────────────────────

from django.views.decorators.http import require_POST
from django.core.mail import mail_admins
import logging

logger = logging.getLogger(__name__)


@require_POST
def contact_submit(request):
    """Handle landing-page contact form submissions."""
    first_name = request.POST.get('first_name', '').strip()[:100]
    last_name = request.POST.get('last_name', '').strip()[:100]
    school_name = request.POST.get('school_name', '').strip()[:200]
    email = request.POST.get('email', '').strip()[:254]
    message_body = request.POST.get('message', '').strip()[:2000]

    if not email or not message_body:
        messages.error(request, 'Please fill in your email and message.')
        return redirect('/#contact')

    subject = f"Contact form: {first_name} {last_name} — {school_name or 'N/A'}"
    body = (
        f"Name: {first_name} {last_name}\n"
        f"School: {school_name}\n"
        f"Email: {email}\n\n"
        f"{message_body}"
    )
    logger.info("Contact form submission from %s <%s>: %s", school_name, email, subject)

    try:
        mail_admins(subject, body, fail_silently=True)
    except Exception:
        pass

    messages.success(request, 'Message sent! We\'ll be in touch soon.')
    return redirect('/#contact')


# ── Error Handlers ───────────────────────────────────────────────────────────

def error_400(request, exception):
    return render(request, '400.html', status=400)


def error_403(request, exception):
    return render(request, '403.html', status=403)


def error_404(request, exception):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)

