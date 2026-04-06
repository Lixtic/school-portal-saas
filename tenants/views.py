from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, connection, models
from django.db.models import Sum, Avg, Count
from django.db.utils import ProgrammingError
from django.contrib.auth.decorators import user_passes_test
from .forms import (
    SchoolSignupForm,
    SchoolSetupForm,
    SchoolApprovalForm,
    SuperAdminSchoolCreateForm,
    PlatformAIModelSettingsForm,
)
from .models import School, Domain, PlatformSettings
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from academics.models import SchoolInfo, AcademicYear, Class, Subject, ClassSubject
from django.utils import timezone
from datetime import timedelta
from .email_notifications import send_submission_confirmation, send_approval_notification
import logging

logger = logging.getLogger(__name__)


def _get_school_subscription_safe(school):
    """Fetch subscription with backward-compatible fallback for legacy tenant schemas.

    With ATOMIC_REQUESTS=True every request runs inside an open transaction.
    A PostgreSQL-level ProgrammingError (e.g. missing column in a legacy schema)
    marks the whole connection as aborted — subsequent queries all fail with
    InFailedSqlTransaction.  Wrapping the first attempt in transaction.atomic()
    creates a savepoint; if the query fails the savepoint is automatically rolled
    back, leaving the outer request transaction intact so the retry can proceed.
    """
    from .models import SchoolSubscription

    try:
        with transaction.atomic():
            return SchoolSubscription.objects.get(school=school)
    except ProgrammingError as exc:
        err_msg = str(exc)
        if (
            'paystack_subscription_code' not in err_msg
            and 'paystack_customer_code' not in err_msg
            and 'paystack_plan_code' not in err_msg
            and 'mrr' not in err_msg
        ):
            raise

        logger.warning(
            "Legacy SchoolSubscription schema in tenant '%s'; retrying with deferred Paystack fields.",
            getattr(school, 'schema_name', 'unknown'),
        )
        # The savepoint was already rolled back when ProgrammingError propagated
        # out of transaction.atomic(); the outer transaction is clean — retry now.
        # Only defer fields that actually exist on the model (paystack_plan_code
        # is a stale DB column present in old schemas but removed from the model,
        # so passing it to .defer() raises FieldDoesNotExist before the query runs).
        return SchoolSubscription.objects.defer(
            'paystack_subscription_code',
            'paystack_customer_code',
            'mrr',
        ).get(school=school)

def school_signup(request):
    if request.method == 'POST':
        form = SchoolSignupForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['school_name']
            schema_name = form.cleaned_data['schema_name']
            email = form.cleaned_data['email']
            school_type = form.cleaned_data['school_type']
            address = form.cleaned_data['address']
            phone = form.cleaned_data['phone']
            country = form.cleaned_data['country']
            
            # Onboarding fields
            contact_person_name = form.cleaned_data.get('contact_person_name')
            contact_person_title = form.cleaned_data.get('contact_person_title')
            contact_person_email = form.cleaned_data.get('contact_person_email')
            contact_person_phone = form.cleaned_data.get('contact_person_phone')
            registration_certificate = form.cleaned_data.get('registration_certificate')
            tax_id_document = form.cleaned_data.get('tax_id_document')
            additional_documents = form.cleaned_data.get('additional_documents')
            
            try:
                # 1. Create Tenant in PENDING status (no schema yet)
                logger.info("Starting school creation for %s", schema_name)
                
                tenant = School(
                    schema_name=schema_name, 
                    name=name, 
                    school_type=school_type,
                    address=address,
                    phone_number=phone,
                    country=country,
                    on_trial=False,  # Will be set by admin on approval
                    is_active=False,  # Inactive until approved
                    approval_status='pending',
                    contact_person_name=contact_person_name,
                    contact_person_title=contact_person_title,
                    contact_person_email=contact_person_email,
                    contact_person_phone=contact_person_phone,
                    registration_certificate=registration_certificate,
                    tax_id_document=tax_id_document,
                    additional_documents=additional_documents,
                    submitted_for_review_at=timezone.now()
                )
                # Don't create schema yet - wait for approval
                tenant.auto_create_schema = False 
                tenant.save()
                
                logger.info("Tenant record saved (pending approval): %s", schema_name)
                
                domain = Domain()
                # Support both development (.local) and production domains via settings
                base_domain = getattr(settings, 'BASE_SCHOOL_DOMAIN', 'local')
                if base_domain == 'local':
                    domain.domain = f"{schema_name}.local"
                else:
                    domain.domain = f"{schema_name}.{base_domain}"
                domain.tenant = tenant
                domain.is_primary = True
                domain.save()
                logger.debug("Domain saved for %s", schema_name)
                
                # Send submission confirmation email
                send_submission_confirmation(tenant)

                messages.success(request, f"Application submitted successfully! Your school '{name}' is pending admin approval. You will be notified at {contact_person_email} once approved.")
                return render(request, 'tenants/signup_success.html', {
                    'schema_name': schema_name,
                    'pending_approval': True,
                    'school_name': name
                })
                    
            except Exception as e:
                logger.error("Signup critical failure for %s: %s", schema_name, e)
                connection.set_schema_to_public()
                
                # Try to clean up orphan tenant if schemas failed?
                # For debugging: LEAVE IT.
                
                messages.error(request, f"Error creating school. Please try again or check logs. ({e})")


                
    else:
        form = SchoolSignupForm()
    
    return render(request, 'tenants/signup.html', {'form': form})


def _create_sample_data(tenant, school_type='basic', phone='', address=''):
    """Auto-populate new tenant with default classes, subjects, and school info.

    Ghana education levels:
      KG  – Kindergarten 1-2
      B   – Primary / Basic 1-6
      JHS – Junior High School 1-3
      SHS – Senior High School 1-3
    """
    # ── Academic Year ──────────────────────────────────────────────
    current_year = timezone.now().year
    academic_year, _ = AcademicYear.objects.get_or_create(
        name=f'{current_year}/{current_year + 1}',
        defaults={
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=365),
            'is_current': True
        }
    )

    # ── Class definitions by level ────────────────────────────────
    KG_CLASSES  = ['KG 1', 'KG 2']
    PRI_CLASSES = [f'B{i}' for i in range(1, 7)]           # B1-B6
    JHS_CLASSES = [f'JHS {i}' for i in range(1, 4)]        # JHS 1-3
    SHS_CLASSES = [f'SHS {i}' for i in range(1, 4)]        # SHS 1-3

    # Map school_type → which class levels to create
    LEVEL_MAP = {
        'primary': KG_CLASSES + PRI_CLASSES,
        'jhs':     JHS_CLASSES,
        'shs':     SHS_CLASSES,
        'basic':   KG_CLASSES + PRI_CLASSES + JHS_CLASSES,
        'other':   PRI_CLASSES,
    }
    class_names = LEVEL_MAP.get(school_type, LEVEL_MAP['basic'])

    created_classes = []
    for name in class_names:
        cls, _ = Class.objects.get_or_create(
            name=name, academic_year=academic_year
        )
        created_classes.append(cls)

    # ── Subject catalogue ─────────────────────────────────────────
    # Tuple: (name, code)
    CORE_SUBJECTS = [
        ('Mathematics',                  'MATH'),
        ('English Language',             'ENG'),
    ]

    KG_SUBJECTS = CORE_SUBJECTS + [
        ('Our World Our People',         'OWOP'),
        ('Creative Arts',                'CRA'),
        ('Physical Education',           'PHE'),
        ('Language & Literacy',          'LIT'),
    ]

    PRIMARY_SUBJECTS = CORE_SUBJECTS + [
        ('Integrated Science',           'SCI'),
        ('Our World Our People',         'OWOP'),
        ('Religious & Moral Education',  'RME'),
        ('Creative Arts',                'CRA'),
        ('Computing',                    'ICT'),
        ('Physical Education',           'PHE'),
        ('Ghanaian Language',            'GHL'),
        ('French',                       'FRE'),
    ]

    JHS_SUBJECTS = CORE_SUBJECTS + [
        ('Integrated Science',           'SCI'),
        ('Social Studies',               'SOC'),
        ('Religious & Moral Education',  'RME'),
        ('Creative Arts & Design',       'CAD'),
        ('Computing',                    'ICT'),
        ('Career Technology',            'CAR'),
        ('French',                       'FRE'),
        ('Ghanaian Language',            'GHL'),
        ('Physical Education',           'PHE'),
    ]

    SHS_SUBJECTS = CORE_SUBJECTS + [
        ('Integrated Science',           'SCI'),
        ('Social Studies',               'SOC'),
        ('Elective Mathematics',         'EMATH'),
        ('Physics',                      'PHY'),
        ('Chemistry',                    'CHEM'),
        ('Biology',                      'BIO'),
        ('Geography',                    'GEO'),
        ('History',                      'HIS'),
        ('Government',                   'GOV'),
        ('Economics',                    'ECON'),
        ('Literature in English',        'LIT-E'),
        ('French',                       'FRE'),
        ('Business Management',          'BM'),
        ('Accounting',                   'ACC'),
        ('Computing',                    'ICT'),
        ('Physical Education',           'PHE'),
    ]

    # Helper: determine which subjects a class level gets
    def _subjects_for(class_name):
        if class_name.startswith('KG'):  return KG_SUBJECTS
        if class_name.startswith('B'):   return PRIMARY_SUBJECTS
        if class_name.startswith('JHS'): return JHS_SUBJECTS
        if class_name.startswith('SHS'): return SHS_SUBJECTS
        return CORE_SUBJECTS

    # Create all subjects that this school type needs
    all_subject_tuples = set()
    for cn in class_names:
        all_subject_tuples.update(_subjects_for(cn))

    subject_cache = {}  # code → Subject instance
    for subj_name, code in all_subject_tuples:
        obj, _ = Subject.objects.get_or_create(
            code=code, defaults={'name': subj_name}
        )
        subject_cache[code] = obj

    # ── Link subjects to classes (ClassSubject) ───────────────────
    for cls in created_classes:
        for subj_name, code in _subjects_for(cls.name):
            subj = subject_cache.get(code)
            if subj:
                ClassSubject.objects.get_or_create(
                    class_name=cls, subject=subj,
                    defaults={'teacher': None}
                )

    # ── School Info ───────────────────────────────────────────────
    if not SchoolInfo.objects.exists():
        SchoolInfo.objects.create(
            name=tenant.name,
            address=address or 'To be configured',
            phone=phone or 'To be configured',
            email='info@school.edu',
            motto='Excellence in Education',
            primary_color='#026e56',
            secondary_color='#0f3b57'
        )
    else:
        info = SchoolInfo.objects.first()
        info.name = tenant.name
        if address: info.address = address
        if phone: info.phone = phone
        info.save()


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def superadmin_create_school(request):
    """Super admin only: Direct school creation (bypasses approval flow)"""
    if request.method == 'POST':
        form = SuperAdminSchoolCreateForm(request.POST)
        if form.is_valid():
            schema_name = form.cleaned_data['schema_name']
            school_name = form.cleaned_data['school_name']
            school_type = form.cleaned_data['school_type']
            admin_email = form.cleaned_data['admin_email']
            phone = form.cleaned_data.get('phone', '')
            address = form.cleaned_data.get('address', '')
            on_trial = form.cleaned_data.get('on_trial', True)
            
            try:
                import secrets
                temp_password = secrets.token_urlsafe(12)
                
                # Create tenant (active immediately)
                logger.info("Super admin creating school: %s", schema_name)
                tenant = School(
                    schema_name=schema_name,
                    name=school_name,
                    school_type=school_type,
                    phone_number=phone,
                    address=address,
                    country='Ghana',
                    on_trial=on_trial,
                    is_active=True,
                    approval_status='approved',
                    contact_person_email=admin_email,
                    reviewed_by=request.user,
                    reviewed_at=timezone.now()
                )
                tenant.auto_create_schema = True
                tenant.save()
                tenant.create_schema(check_if_exists=True, verbosity=1)
                
                # Create domain
                domain = Domain()
                base_domain = getattr(settings, 'BASE_SCHOOL_DOMAIN', 'local')
                if base_domain == 'local':
                    domain.domain = f"{schema_name}.local"
                else:
                    domain.domain = f"{schema_name}.{base_domain}"
                domain.tenant = tenant
                domain.is_primary = True
                domain.save()
                
                # Switch to tenant schema and setup
                admin_username = f'admin_{schema_name}'
                connection.set_tenant(tenant)
                try:
                    User = get_user_model()
                    admin_user = User.objects.create_superuser(
                        username=admin_username,
                        email=admin_email,
                        password=temp_password,
                        user_type='admin'
                    )
                    
                    # Create sample data
                    _create_sample_data(tenant, school_type=school_type, phone=phone, address=address)
                finally:
                    connection.set_schema_to_public()
                
                # Create subscription if trial enabled
                if on_trial:
                    from .models import SubscriptionPlan, SchoolSubscription
                    try:
                        trial_plan = SubscriptionPlan.objects.get(plan_type='trial')
                        trial_ends = timezone.now() + timedelta(days=14)
                        SchoolSubscription.objects.create(
                            school=tenant,
                            plan=trial_plan,
                            status='trial',
                            trial_ends_at=trial_ends,
                            current_period_end=trial_ends,
                            mrr=0,
                        )
                    except SubscriptionPlan.DoesNotExist:
                        logger.warning("Trial plan not found")
                
                messages.success(
                    request, 
                    f"✅ School '{school_name}' created successfully! "
                    f"Login URL: /{schema_name}/login/ | Username: {admin_username} | Password: {temp_password}"
                )
                
                # Redirect to a success page or back to create form
                return redirect('tenants:superadmin_create_school')
                
            except Exception as e:
                logger.error("Super admin school creation failed: %s", e, exc_info=True)
                connection.set_schema_to_public()
                messages.error(request, f"Error creating school: {e}")
    else:
        form = SuperAdminSchoolCreateForm()
    
    # Get recently created schools for reference
    recent_schools = School.objects.filter(
        approval_status='approved',
        is_active=True
    ).order_by('-created_on')[:10]
    
    context = {
        'form': form,
        'recent_schools': recent_schools,
    }
    return render(request, 'tenants/superadmin_create_school.html', context)


@login_required
def school_setup_wizard(request):
    """Initial setup wizard for configuring school information"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    # Ensure user is on a tenant schema (not public)
    if hasattr(request, 'tenant') and request.tenant.schema_name == 'public':
        messages.error(request, "This page is only accessible from Portalss.")
        return redirect('home')
    
    # Check if already configured
    school_info = SchoolInfo.objects.first()
    if school_info and school_info.setup_complete:
        # Already setup, redirect to dashboard with proper tenant prefix
        dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
        return redirect(dashboard_url)
    
    if request.method == 'POST':
        form = SchoolSetupForm(request.POST, request.FILES, instance=school_info)
        if form.is_valid():
            school_info = form.save(commit=False)
            school_info.setup_complete = True
            school_info.save()
            
            messages.success(request, "School setup completed successfully!")
            # Redirect with tenant prefix
            dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
            return redirect(dashboard_url)
    else:
        form = SchoolSetupForm(instance=school_info)
    
    return render(request, 'tenants/setup_wizard.html', {'form': form})


@login_required
def landlord_redirect(request):
    """Redirect the old /tenants/landlord/ and /tenants/ paths to the canonical /landlord/ URL."""
    return redirect('/landlord/')


def landlord_landing(request):
    """Redirects legacy /tenants/ landing to canonical /landlord/ dashboard."""
    return redirect('/landlord/')


@login_required
def landing_template_picker(request):
    """Landlord: choose which landing-page template is shown at /."""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Platform admins only.")
        return redirect('home')

    platform = PlatformSettings.get()

    if request.method == 'POST':
        chosen = request.POST.get('landing_template', '')
        valid_keys = [k for k, _ in PlatformSettings.TEMPLATE_CHOICES]
        if chosen in valid_keys:
            platform.landing_template = chosen
            platform.save()
            messages.success(request, f"Landing page updated to '{dict(PlatformSettings.TEMPLATE_CHOICES)[chosen]}'.")
        else:
            messages.error(request, "Invalid template selection.")
        return redirect('tenants:landing_template_picker')

    return render(request, 'tenants/landing_template_picker.html', {
        'platform': platform,
        'choices': PlatformSettings.TEMPLATE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def ai_model_settings(request):
    """Super admin: choose global AI provider and categorized models."""
    platform = PlatformSettings.get()

    if request.method == 'POST':
        form = PlatformAIModelSettingsForm(request.POST, instance=platform)
        if form.is_valid():
            form.save()
            messages.success(request, 'AI model settings updated successfully.')
            return redirect('tenants:ai_model_settings')
        messages.error(request, 'Please fix the highlighted errors and try again.')
    else:
        form = PlatformAIModelSettingsForm(instance=platform)

    return render(request, 'tenants/ai_model_settings.html', {
        'form': form,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def landlord_dashboard(request):
    """Public-schema landlord dashboard for platform admins."""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admins only.")
        return redirect('home')

    schools_count = School.objects.count()
    active_count = School.objects.filter(is_active=True).count()
    trial_count = School.objects.filter(on_trial=True).count()
    inactive_count = schools_count - active_count
    domains_count = Domain.objects.count()
    primary_domains = Domain.objects.filter(is_primary=True).count()
    
    # Approval stats
    pending_count = School.objects.filter(approval_status='pending').count()
    under_review_count = School.objects.filter(approval_status='under_review').count()
    approved_count = School.objects.filter(approval_status='approved').count()
    rejected_count = School.objects.filter(approval_status='rejected').count()
    requires_info_count = School.objects.filter(approval_status='requires_info').count()

    by_type = (
        School.objects.values('school_type')
        .order_by('school_type')
        .annotate(total=models.Count('id'))
    )

    recent_schools = School.objects.order_by('-created_on')[:6]

    # Signups over the last 30 days for trend display
    start_date = timezone.now().date() - timedelta(days=29)
    signups_qs = (
        School.objects.filter(created_on__gte=start_date)
        .values('created_on')
        .annotate(total=models.Count('id'))
        .order_by('created_on')
    )
    max_signups = max([row['total'] for row in signups_qs], default=1)
    signups_chart = [
        {
            'date': row['created_on'],
            'total': row['total'],
            'pct': int((row['total'] / max_signups) * 100) if max_signups else 0,
        }
        for row in signups_qs
    ]

    context = {
        'schools_count': schools_count,
        'active_count': active_count,
        'trial_count': trial_count,
        'inactive_count': inactive_count,
        'domains_count': domains_count,
        'primary_domains': primary_domains,
        'pending_count': pending_count,
        'under_review_count': under_review_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'requires_info_count': requires_info_count,
        'by_type': by_type,
        'recent_schools': recent_schools,
        'signups_chart': signups_chart,
    }

    # === Individual User / Referral Stats ===
    try:
        from individual_users.models import IndividualProfile, IndividualCreditTransaction
        from django.db.models import Sum as _Sum

        total_individuals = IndividualProfile.objects.count()
        verified_individuals = IndividualProfile.objects.filter(email_verified=True).count()
        total_referrals = IndividualProfile.objects.filter(referred_by__isnull=False).count()
        referral_credits_awarded = (
            IndividualCreditTransaction.objects
            .filter(transaction_type='referral', amount__gt=0)
            .aggregate(total=_Sum('amount'))['total'] or 0
        )
        # Top 5 referrers
        from django.db.models import Count as _RefCount
        top_referrers = (
            IndividualProfile.objects
            .filter(referrals__isnull=False)
            .annotate(ref_count=_RefCount('referrals'))
            .order_by('-ref_count')
            .select_related('user')[:5]
        )

        context.update({
            'total_individuals': total_individuals,
            'verified_individuals': verified_individuals,
            'total_referrals': total_referrals,
            'referral_credits_awarded': referral_credits_awarded,
            'top_referrers': top_referrers,
        })
    except Exception:
        pass  # Don't crash if individual_users tables aren't available

    # === AI Usage This Month ===
    try:
        from .models import AIUsageLog, SchoolSubscription
        from django.db.models import Count as _Count
        from django.db import transaction as _tx
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        with _tx.atomic():
            ai_total_month = AIUsageLog.objects.filter(created_at__gte=month_start).count()

            # Top 8 schools by AI calls this month
            top_ai_schools_qs = (
                AIUsageLog.objects
                .filter(created_at__gte=month_start)
                .values('school_id', 'school__name', 'school__schema_name')
                .annotate(call_count=_Count('id'))
                .order_by('-call_count')[:8]
            )

            # Annotate each row with quota info (plan limit)
            top_ai_schools = []
            for row in top_ai_schools_qs:
                try:
                    sub = SchoolSubscription.objects.select_related('plan').get(school_id=row['school_id'])
                    limit = sub.plan.ai_calls_per_month
                    used_pct = int(row['call_count'] / limit * 100) if limit > 0 else 0
                    near_quota = limit > 0 and used_pct >= 70
                except SchoolSubscription.DoesNotExist:
                    limit = 0
                    used_pct = 0
                    near_quota = False
                top_ai_schools.append({
                    'name': row['school__name'],
                    'schema_name': row['school__schema_name'],
                    'call_count': row['call_count'],
                    'limit': limit,
                    'used_pct': used_pct,
                    'near_quota': near_quota,
                })

            # Action breakdown this month
            ai_action_breakdown = list(
                AIUsageLog.objects
                .filter(created_at__gte=month_start)
                .values('action_type')
                .annotate(count=_Count('id'))
                .order_by('-count')[:5]
            )

        context.update({
            'ai_total_month': ai_total_month,
            'top_ai_schools': top_ai_schools,
            'ai_action_breakdown': ai_action_breakdown,
        })
    except Exception:
        pass  # Don't crash dashboard if AI tables are unavailable

    # === Promo Campaign Stats ===
    try:
        from .models import PromoCampaign
        promo_all = PromoCampaign.objects.all()
        context['promo_stats'] = {
            'total': promo_all.count(),
            'drafts': promo_all.filter(status='draft').count(),
            'scheduled': promo_all.filter(status='scheduled').count(),
            'sent': promo_all.filter(status='sent').count(),
            'emails_delivered': sum(c.sent_count for c in promo_all.filter(status='sent')),
        }
    except Exception:
        pass

    # === Landlord Agent Stats ===
    try:
        from .models import LandlordAgentConversation, LandlordAgentMessage
        week_ago = timezone.now() - timedelta(days=7)
        agent_convs = LandlordAgentConversation.objects.all()
        context['agent_stats'] = {
            'total_conversations': agent_convs.count(),
            'total_messages': LandlordAgentMessage.objects.count(),
            'conversations_this_week': agent_convs.filter(created_at__gte=week_ago).count(),
            'messages_this_week': LandlordAgentMessage.objects.filter(created_at__gte=week_ago).count(),
        }
    except Exception:
        pass

    return render(request, 'tenants/landlord_dashboard.html', context)


@login_required
def approval_queue(request):
    """Admin view to see schools awaiting approval"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('home')
    
    # Filter by status
    status = request.GET.get('status', 'pending')
    if status not in ['pending', 'under_review', 'approved', 'rejected', 'requires_info']:
        status = 'pending'
    
    schools = School.objects.filter(approval_status=status).order_by('-submitted_for_review_at')
    
    context = {
        'schools': schools,
        'current_status': status,
        'pending_count': School.objects.filter(approval_status='pending').count(),
        'under_review_count': School.objects.filter(approval_status='under_review').count(),
        'approved_count': School.objects.filter(approval_status='approved').count(),
        'rejected_count': School.objects.filter(approval_status='rejected').count(),
        'requires_info_count': School.objects.filter(approval_status='requires_info').count(),
    }
    return render(request, 'tenants/approval_queue.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def approval_pending_count_api(request):
    """Lightweight JSON endpoint for landlord mobile queue badge refresh."""
    tenant = getattr(request, 'tenant', None)
    if tenant and getattr(tenant, 'schema_name', None) != 'public':
        return JsonResponse({'detail': 'Forbidden'}, status=403)

    pending = School.objects.filter(approval_status='pending').count()
    under_review = School.objects.filter(approval_status='under_review').count()
    return JsonResponse({
        'pending': pending,
        'under_review': under_review,
        'total_actionable': pending + under_review,
    })


@login_required
def review_school(request, school_id):
    """Admin view to review a single school application"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('home')
    
    school = get_object_or_404(School, id=school_id)
    
    if request.method == 'POST':
        form = SchoolApprovalForm(request.POST, instance=school)
        if form.is_valid():
            old_status = school.approval_status  # Track old status for email logic
            school = form.save(commit=False)
            school.reviewed_by = request.user
            school.reviewed_at = timezone.now()

            # Audit log the approval action
            from .subscription_models import AuditLog
            _audit_action = 'school_approve' if school.approval_status == 'approved' else 'school_reject'
            AuditLog.log(_audit_action, request=request, detail=f'{school.name}: {old_status} → {school.approval_status}')
            
            # If approved, create schema and setup
            if school.approval_status == 'approved' and not school.is_active:
                try:
                    import secrets
                    
                    # Generate secure random password
                    temp_password = secrets.token_urlsafe(12)
                    
                    # Create schema
                    school.auto_create_schema = True
                    school.is_active = True
                    school.on_trial = True  # Set to trial mode when approved
                    school.save()
                    school.create_schema(check_if_exists=True, verbosity=1)
                    
                    # Switch to tenant and create admin user + sample data
                    connection.set_tenant(school)
                    admin_username = f'admin_{school.schema_name}'
                    try:
                        User = get_user_model()
                        
                        if not User.objects.filter(username=admin_username).exists():
                            temp_email = school.contact_person_email or 'admin@example.com'
                            admin_user = User.objects.create_superuser(
                                username=admin_username,
                                email=temp_email,
                                password=temp_password,
                                user_type='admin'
                            )
                        
                        _create_sample_data(school, 
                                           school_type=school.school_type,
                                           phone=school.phone_number,
                                           address=school.address)
                    finally:
                        connection.set_schema_to_public()

                    # Create trial subscription (14 days)
                    from .models import SubscriptionPlan, SchoolSubscription
                    try:
                        trial_plan = SubscriptionPlan.objects.get(plan_type='trial')
                        trial_ends = timezone.now() + timedelta(days=14)
                        SchoolSubscription.objects.get_or_create(
                            school=school,
                            defaults=dict(
                                plan=trial_plan,
                                status='trial',
                                trial_ends_at=trial_ends,
                                current_period_end=trial_ends,
                                mrr=0,
                            ),
                        )
                    except SubscriptionPlan.DoesNotExist:
                        logger.warning("Trial plan not found; skipping subscription creation for %s", school.name)
                    
                    # Send approval email notification with temporary password
                    context = {
                        'school': school,
                        'contact_name': school.contact_person_name or 'Administrator',
                        'login_url': f"/{school.schema_name}/login/",
                        'temp_password': temp_password,
                        'admin_username': admin_username,
                    }
                    
                    logger.debug("Sending approval email to %s for %s", school.contact_person_email, school.name)
                    email_sent = send_approval_notification(school, status_changed_by=request.user, extra_context=context)
                    logger.debug("Email send result: %s", email_sent)
                    
                    if email_sent:
                        messages.success(request, f"✅ School '{school.name}' approved and activated! Login credentials sent to {school.contact_person_email}.")
                    else:
                        messages.warning(request, f"⚠️ School '{school.name}' approved and activated, but email notification failed. Contact: {school.contact_person_email}")
                    
                except Exception as e:
                    logger.error("Exception during approval for %s: %s", school.schema_name, e)
                    messages.error(request, f"Approval saved but schema creation failed: {e}")
                    school.approval_status = 'requires_info'
                    school.admin_notes = f"Schema creation error: {e}"
                    school.save()
                    # Send requires_info notification
                    try:
                        send_approval_notification(school, status_changed_by=request.user)
                    except Exception as email_err:
                        logger.warning("Failed to send requires_info email: %s", email_err)
            else:
                school.save()
                
                # Send status update email for other status changes
                if old_status != school.approval_status:
                    send_approval_notification(school, status_changed_by=request.user)
                
                status_msg = dict(School.APPROVAL_STATUS).get(school.approval_status, school.approval_status)
                messages.success(request, f"School status updated to: {status_msg}. Notification email sent.")
            
            return redirect('tenants:approval_queue')
    else:
        form = SchoolApprovalForm(instance=school)
    
    context = {
        'school': school,
        'form': form,
    }
    return render(request, 'tenants/review_school.html', context)


@login_required
def resend_school_credentials(request, school_id):
    """Resend login credentials email to an already-approved school"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('home')
    
    school = get_object_or_404(School, id=school_id)
    
    # Only allow resending for approved, active schools
    if school.approval_status != 'approved' or not school.is_active:
        messages.error(request, f"Can only resend credentials for approved active schools. Current status: {school.approval_status}")
        return redirect('tenants:approval_queue')
    
    try:
        import secrets
        
        # Generate new temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # Update admin user password in school's schema
        admin_username = f'admin_{school.schema_name}'
        connection.set_tenant(school)
        User = get_user_model()
        
        try:
            # Try new-style username first, fall back to legacy 'admin'
            try:
                admin_user = User.objects.get(username=admin_username)
            except User.DoesNotExist:
                admin_user = User.objects.get(username='admin', user_type='admin')
                # Rename to new-style while we're here
                admin_user.username = admin_username
            admin_user.set_password(temp_password)
            admin_user.save()
            logger.info("Updated admin password for school %s (username: %s)", school.schema_name, admin_username)
        except User.DoesNotExist:
            logger.info("No admin user found for %s, creating one", school.schema_name)
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=school.contact_person_email or 'admin@example.com',
                password=temp_password,
                user_type='admin'
            )
        
        connection.set_schema_to_public()
        
        # Send approval email with new credentials
        context = {
            'school': school,
            'contact_name': school.contact_person_name or 'Administrator',
            'login_url': f"/{school.schema_name}/login/",
            'temp_password': temp_password,
            'admin_username': admin_username,
        }
        
        email_sent = send_approval_notification(school, status_changed_by=request.user, extra_context=context)
        
        if email_sent:
            messages.success(request, f"✅ Credentials resent to {school.contact_person_email}.")
        else:
            messages.warning(request, f"⚠️ Failed to send email, but password was reset. Please send credentials manually to {school.contact_person_email}.")
        
    except Exception as e:
        connection.set_schema_to_public()
        logger.error("Error resending credentials for %s: %s", school.schema_name, e)
        messages.error(request, f"Error resending credentials: {e}")
    
    return redirect('tenants:approval_queue')


@login_required
def revenue_analytics(request):
    """Revenue analytics dashboard for platform admins"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('home')
    
    from .models import SchoolSubscription, ChurnEvent, Invoice
    from django.db.models import Sum, Avg, Count, Q
    from django.db.models.functions import TruncMonth
    
    # === MRR Metrics ===
    active_subscriptions = SchoolSubscription.objects.filter(
        status__in=['active', 'trial']
    )
    
    # School counts
    schools_count = active_subscriptions.count()
    active_count = active_subscriptions.filter(status='active').count()
    trial_count = active_subscriptions.filter(status='trial').count()
    
    total_mrr = active_subscriptions.aggregate(
        mrr=Sum('mrr')
    )['mrr'] or 0
    
    trial_mrr = active_subscriptions.filter(status='trial').aggregate(
        mrr=Sum('mrr')
    )['mrr'] or 0
    
    paid_mrr = total_mrr - trial_mrr
    
    # Average revenue per account
    arpa = active_subscriptions.aggregate(
        avg=Avg('mrr')
    )['avg'] or 0
    
    # === Churn Metrics ===
    # Churn in last 30 days
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    recent_churns = ChurnEvent.objects.filter(cancelled_at__gte=thirty_days_ago)
    churn_count = recent_churns.count()
    
    # Churn rate calculation
    total_schools_30d_ago = School.objects.filter(
        created_on__lt=thirty_days_ago
    ).count()
    churn_rate = (churn_count / total_schools_30d_ago * 100) if total_schools_30d_ago > 0 else 0
    
    # Churn reasons breakdown
    churn_reasons = recent_churns.values('reason').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # === Revenue Growth (Last 6 Months) ===
    from datetime import datetime as dt_type

    monthly_mrr = []
    monthly_new_schools = []
    chart_labels = []

    for i in range(5, -1, -1):
        # Proper calendar-month arithmetic (handles year-wrap correctly)
        raw_month = now.month - i
        target_year = now.year + (raw_month - 1) // 12
        target_month = ((raw_month - 1) % 12) + 1

        month_start_dt = timezone.make_aware(dt_type(target_year, target_month, 1))
        if target_month == 12:
            month_end_dt = timezone.make_aware(dt_type(target_year + 1, 1, 1))
        else:
            month_end_dt = timezone.make_aware(dt_type(target_year, target_month + 1, 1))

        chart_labels.append(month_start_dt.strftime('%b %y'))

        # Paid MRR acquired this month (active subscriptions created in window)
        month_mrr = float(
            SchoolSubscription.objects
            .filter(created_at__gte=month_start_dt, created_at__lt=month_end_dt, status='active')
            .aggregate(s=Sum('mrr'))['s'] or 0
        )
        monthly_mrr.append(month_mrr)

        # New school registrations this month
        new_schools_count = School.objects.filter(
            created_on__gte=month_start_dt.date(),
            created_on__lt=month_end_dt.date(),
        ).count()
        monthly_new_schools.append(new_schools_count)

    # Chart scaling — if all MRR is 0 (all schools on trial), chart bars show school growth instead
    all_zero_mrr = all(m == 0 for m in monthly_mrr)
    if all_zero_mrr:
        max_val = max(monthly_new_schools) if any(monthly_new_schools) else 1
        chart_heights = [int((n / max_val * 80) if max_val > 0 else 0) for n in monthly_new_schools]
    else:
        max_val = max(monthly_mrr) if any(monthly_mrr) else 1
        chart_heights = [int((m / max_val * 80) if max_val > 0 else 0) for m in monthly_mrr]
    
    # Calculate growth rate (last month vs previous month)
    growth_rate = 0
    if len(monthly_mrr) >= 2 and monthly_mrr[-2] > 0:
        growth_rate = ((monthly_mrr[-1] - monthly_mrr[-2]) / monthly_mrr[-2]) * 100
    
    current_month = now.strftime('%B %Y')
    
    # === Subscription Distribution ===
    plan_distribution = (
        active_subscriptions
        .values('plan__name')
        .annotate(count=Count('id'), revenue=Sum('mrr'))
        .order_by('-revenue')
    )
    
    billing_cycle_dist = (
        active_subscriptions
        .values('billing_cycle')
        .annotate(count=Count('id'), revenue=Sum('mrr'))
    )
    
    # === Renewals (Next 30 Days) ===
    next_30_days = timezone.now() + timedelta(days=30)
    upcoming_renewals = active_subscriptions.filter(
        current_period_end__lte=next_30_days,
        current_period_end__gte=timezone.now()
    ).order_by('current_period_end')[:10]
    
    renewal_revenue = upcoming_renewals.aggregate(
        total=Sum('mrr')
    )['total'] or 0
    
    # === Lifetime Value ===
    avg_ltv = ChurnEvent.objects.aggregate(
        avg=Avg('lifetime_value')
    )['avg'] or 0
    
    avg_subscription_months = ChurnEvent.objects.aggregate(
        avg=Avg('months_subscribed')
    )['avg'] or 0
    
    # === Invoice Stats ===
    pending_invoices = Invoice.objects.filter(status='pending').count()
    overdue_invoices = Invoice.objects.filter(
        status='pending',
        due_at__lt=timezone.now()
    ).count()
    
    total_revenue_collected = Invoice.objects.filter(
        status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0

    # === Tenant Growth Trend (12 months) ===
    import json as _json
    growth_labels_12 = []
    growth_new_12 = []
    growth_cumulative_12 = []
    running_total = 0
    for i in range(11, -1, -1):
        raw_month = now.month - i
        target_year = now.year + (raw_month - 1) // 12
        target_month = ((raw_month - 1) % 12) + 1
        from datetime import datetime as _dt
        ms = timezone.make_aware(_dt(target_year, target_month, 1))
        if target_month == 12:
            me = timezone.make_aware(_dt(target_year + 1, 1, 1))
        else:
            me = timezone.make_aware(_dt(target_year, target_month + 1, 1))
        growth_labels_12.append(ms.strftime('%b %y'))
        new_c = School.objects.filter(created_on__gte=ms.date(), created_on__lt=me.date()).count()
        growth_new_12.append(new_c)
        running_total += new_c
        growth_cumulative_12.append(running_total)

    # Offset cumulative to start from total - running_total
    base_total = School.objects.count() - running_total
    growth_cumulative_12 = [base_total + v for v in growth_cumulative_12]

    # === Churn Trend (6 months) ===
    churn_labels_6 = []
    churn_counts_6 = []
    for i in range(5, -1, -1):
        raw_month = now.month - i
        target_year = now.year + (raw_month - 1) // 12
        target_month = ((raw_month - 1) % 12) + 1
        ms = timezone.make_aware(_dt(target_year, target_month, 1))
        if target_month == 12:
            me = timezone.make_aware(_dt(target_year + 1, 1, 1))
        else:
            me = timezone.make_aware(_dt(target_year, target_month + 1, 1))
        churn_labels_6.append(ms.strftime('%b'))
        churn_counts_6.append(ChurnEvent.objects.filter(cancelled_at__gte=ms, cancelled_at__lt=me).count())

    # === Plan donut data ===
    plan_names = [p['plan__name'] or 'No Plan' for p in plan_distribution]
    plan_counts = [p['count'] for p in plan_distribution]
    plan_colors = ['#7C3AED', '#10B981', '#F59E0B', '#3B82F6', '#F43F5E'][:len(plan_names)]

    # === Audit log recent (for security widget) ===
    from .subscription_models import AuditLog
    recent_audits = AuditLog.objects.order_by('-created_at')[:10]

    context = {
        # MRR
        'total_mrr': total_mrr,
        'paid_mrr': paid_mrr,
        'trial_mrr': trial_mrr,
        'arpa': arpa,
        
        # School counts
        'schools_count': schools_count,
        'active_count': active_count,
        'trial_count': trial_count,
        
        # Churn
        'churn_count': churn_count,
        'churn_rate': round(churn_rate, 2),
        'churn_reasons': churn_reasons,
        
        # Growth
        'monthly_mrr': monthly_mrr,
        'monthly_new_schools': monthly_new_schools,
        'all_zero_mrr': all_zero_mrr,
        'chart_heights': chart_heights,
        'chart_labels': chart_labels,
        'current_month': current_month,
        'growth_rate': round(growth_rate, 1),
        
        # Distribution
        'plan_distribution': plan_distribution,
        'billing_cycle_dist': billing_cycle_dist,
        
        # Renewals
        'upcoming_renewals': upcoming_renewals,
        'renewal_revenue': renewal_revenue,
        
        # LTV
        'avg_ltv': avg_ltv,
        'avg_subscription_months': round(avg_subscription_months, 1),
        
        # Invoices
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue_collected': total_revenue_collected,

        # Chart.js JSON data
        'chart_labels_json': _json.dumps(chart_labels),
        'monthly_mrr_json': _json.dumps(monthly_mrr),
        'monthly_new_schools_json': _json.dumps(monthly_new_schools),
        'growth_labels_12_json': _json.dumps(growth_labels_12),
        'growth_new_12_json': _json.dumps(growth_new_12),
        'growth_cumulative_12_json': _json.dumps(growth_cumulative_12),
        'churn_labels_6_json': _json.dumps(churn_labels_6),
        'churn_counts_6_json': _json.dumps(churn_counts_6),
        'plan_names_json': _json.dumps(plan_names),
        'plan_counts_json': _json.dumps(plan_counts),
        'plan_colors_json': _json.dumps(plan_colors),
        'recent_audits': recent_audits,
    }
    
    return render(request, 'tenants/revenue_analytics.html', context)


@login_required
def addon_marketplace(request):
    """Add-on marketplace - universally accessible for all school users"""
    from .models import AddOn, SchoolSubscription, SchoolAddOn
    paystack_ready = bool(
        (getattr(settings, 'PAYSTACK_SECRET_KEY', '') or '').strip()
        and (getattr(settings, 'PAYSTACK_PUBLIC_KEY', '') or '').strip()
    )
    
    # Block super admins from accessing marketplace
    if request.user.is_staff and (not hasattr(request, 'tenant') or request.tenant.schema_name == 'public'):
        messages.error(request, "Add-on marketplace is for school tenants only. Super admins cannot access this area.")
        return redirect('tenants:landlord_dashboard')

    # Only school admins can access the marketplace
    if request.user.user_type not in ('admin',):
        messages.error(request, "Only school admins can access the add-on marketplace.")
        return redirect('dashboard')
    
    # Ensure user is in a tenant schema
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        messages.error(request, "Marketplace only available for school tenants")
        return redirect('home')
    
    # Get school's subscription
    try:
        subscription = _get_school_subscription_safe(request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
        return redirect('dashboard')
    except ProgrammingError:
        messages.error(request, "Subscription data is outdated for this school. Please ask support to run tenant migrations.")
        return redirect('dashboard')
    
    # Get available add-ons for this plan
    available_addons = AddOn.objects.filter(
        is_active=True,
        available_for_plans__contains=[subscription.plan.plan_type]
    )
    
    # Get already purchased add-ons
    purchased_addon_ids = SchoolAddOn.objects.filter(
        subscription=subscription,
        is_active=True
    ).values_list('addon_id', flat=True)
    
    # Categorize add-ons
    addons_by_category = {}
    for addon in available_addons:
        category = addon.get_category_display()
        if category not in addons_by_category:
            addons_by_category[category] = []
        
        addon.is_purchased = addon.id in purchased_addon_ids
        addon.is_blocked = False
        addon.block_reason = ''
        if addon.slug == 'online-payments' and not paystack_ready:
            addon.is_blocked = True
            addon.block_reason = 'Paystack keys are not configured yet by the platform admin.'
        addons_by_category[category].append(addon)
    
    context = {
        'subscription': subscription,
        'addons_by_category': addons_by_category,
        'total_addon_cost': sum(
            addon.monthly_price 
            for addon in available_addons 
            if addon.id in purchased_addon_ids and not addon.is_one_time
        ),
        'can_manage_addons': request.user.user_type == 'admin',  # Only admins can purchase/cancel
        'paystack_ready': paystack_ready,
    }
    
    return render(request, 'tenants/addon_marketplace.html', context)


@login_required
def purchase_addon(request, addon_id):
    """Purchase an add-on (admin only). Free add-ons activate instantly.
    Paid ones return Paystack params for inline popup."""
    from .models import AddOn, SchoolSubscription, SchoolAddOn
    
    # Restrict to school admins only
    if request.user.user_type != 'admin':
        messages.error(request, "Only school administrators can purchase add-ons")
        return redirect('tenants:addon_marketplace')
    
    if request.method != 'POST':
        return redirect('tenants:addon_marketplace')
    
    # Get subscription
    try:
        subscription = _get_school_subscription_safe(request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
        return redirect('dashboard')
    except ProgrammingError:
        messages.error(request, "Subscription data is outdated for this school. Please ask support to run tenant migrations.")
        return redirect('dashboard')
    
    # Get add-on
    addon = get_object_or_404(AddOn, id=addon_id, is_active=True)

    # Server-side guard for paystack-backed online payments addon.
    if addon.slug == 'online-payments':
        paystack_ready = bool(
            (getattr(settings, 'PAYSTACK_SECRET_KEY', '') or '').strip()
            and (getattr(settings, 'PAYSTACK_PUBLIC_KEY', '') or '').strip()
        )
        if not paystack_ready:
            messages.error(
                request,
                "Paystack is not configured yet. Ask the platform admin to set PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY first."
            )
            return redirect('tenants:addon_marketplace')

    # Already active?
    existing = SchoolAddOn.objects.filter(
        subscription=subscription, addon=addon, is_active=True
    ).first()
    if existing:
        messages.warning(request, f"You already have {addon.name}")
        return redirect('tenants:addon_marketplace')

    # Paid add-ons: return Paystack params if price > 0 and Paystack is configured
    if addon.monthly_price > 0:
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        public = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        if secret and public:
            import uuid
            schema = getattr(request.tenant, 'schema_name', 'unknown')
            ref = f"SA-{schema}-{addon.id}-{uuid.uuid4().hex[:8]}"
            return JsonResponse({
                'paystack': True,
                'public_key': public,
                'email': request.user.email or f'{request.user.username}@school.local',
                'amount': int(addon.monthly_price * 100),
                'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'GHS'),
                'reference': ref,
                'phone': request.user.phone,
                'addon_name': addon.name,
                'addon_id': addon.id,
            })
        # No Paystack keys — fall through to free activation (dev mode)

    # Free add-on or dev-mode activation
    try:
        with transaction.atomic():
            school_addon, created = SchoolAddOn.objects.get_or_create(
                subscription=subscription,
                addon=addon,
                defaults={'is_active': True}
            )

            if not created:
                school_addon.is_active = True
                school_addon.expires_at = None
                school_addon.save(update_fields=['is_active', 'expires_at'])
                messages.success(request, f"Successfully re-activated {addon.name}!")
            else:
                messages.success(request, f"Successfully activated {addon.name}!")
    except Exception:
        logger.exception("Failed to purchase add-on. subscription=%s addon=%s", subscription.id, addon.id)
        messages.error(request, "Could not complete add-on purchase right now. Please try again.")
        return redirect('tenants:addon_marketplace')

    subscription.calculate_mrr()
    return redirect('tenants:addon_marketplace')


@login_required
def marketplace_verify(request):
    """POST — verify a Paystack payment and activate a school add-on."""
    if request.user.user_type != 'admin':
        return JsonResponse({'ok': False, 'error': 'Access denied'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    import json
    import requests as http_requests
    from .subscription_models import SchoolSubscription, SchoolAddOn, AddOn

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Bad JSON'}, status=400)

    reference = body.get('reference', '')
    addon_id = body.get('addon_id')
    if not reference or not addon_id:
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)

    addon = get_object_or_404(AddOn, id=addon_id, is_active=True)

    secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    if secret:
        resp = http_requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers={'Authorization': f'Bearer {secret}'},
            timeout=15,
        )
        data = resp.json()
        if not data.get('status') or data.get('data', {}).get('status') != 'success':
            return JsonResponse({'ok': False, 'error': 'Payment verification failed'}, status=402)

    try:
        subscription = _get_school_subscription_safe(request.tenant)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'No subscription'}, status=400)

    with transaction.atomic():
        school_addon, created = SchoolAddOn.objects.get_or_create(
            subscription=subscription,
            addon=addon,
            defaults={'is_active': True}
        )
        if not created:
            school_addon.is_active = True
            school_addon.expires_at = None
            school_addon.save(update_fields=['is_active', 'expires_at'])

    subscription.calculate_mrr()
    return JsonResponse({'ok': True, 'addon_name': addon.name})


@login_required
def cancel_addon(request, addon_id):
    """Cancel an add-on subscription (admin only)"""
    from .models import SchoolSubscription, SchoolAddOn
    
    # Restrict to school admins only
    if request.user.user_type != 'admin':
        messages.error(request, "Only school administrators can cancel add-ons")
        return redirect('tenants:addon_marketplace')
    
    if request.method != 'POST':
        return redirect('tenants:addon_marketplace')
    
    # Get subscription
    try:
        subscription = _get_school_subscription_safe(request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
        return redirect('dashboard')
    except ProgrammingError:
        messages.error(request, "Subscription data is outdated for this school. Please ask support to run tenant migrations.")
        return redirect('dashboard')
    
    # Get school add-on
    school_addon = get_object_or_404(
        SchoolAddOn, 
        subscription=subscription, 
        addon_id=addon_id,
        is_active=True
    )
    
    # Deactivate
    school_addon.is_active = False
    school_addon.save()
    
    # Recalculate MRR
    subscription.calculate_mrr()
    
    messages.success(request, f"Cancelled {school_addon.addon.name}. Changes will apply at next billing cycle.")
    return redirect('tenants:addon_marketplace')


@csrf_exempt
def paystack_school_webhook(request):
    """Paystack server-to-server webhook for school add-on payments.
    Verifies HMAC-SHA512 signature. Handles charge.success events."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    import json
    import hmac
    import hashlib

    secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    if not secret:
        return JsonResponse({'error': 'not configured'}, status=503)

    sig = request.headers.get('X-Paystack-Signature', '')
    expected = hmac.new(secret.encode(), request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return JsonResponse({'error': 'bad signature'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad json'}, status=400)

    event = payload.get('event')
    data = payload.get('data', {})

    if event == 'charge.success':
        reference = data.get('reference', '')
        # School add-on references start with "SA-"
        if reference.startswith('SA-'):
            _handle_school_addon_payment(reference, data)

    return JsonResponse({'ok': True})


def _handle_school_addon_payment(reference, data):
    """Activate a school add-on from a confirmed Paystack charge."""
    from .subscription_models import SchoolSubscription, SchoolAddOn, AddOn
    from tenants.models import School

    # Parse reference: SA-{schema}-{addon_id}-{uuid}
    parts = reference.split('-')
    if len(parts) < 3:
        logger.warning("Webhook: bad school addon reference format: %s", reference)
        return
    try:
        schema_name = parts[1]
        addon_id = int(parts[2])
    except (ValueError, IndexError):
        logger.warning("Webhook: unparseable school addon reference: %s", reference)
        return

    try:
        school = School.objects.get(schema_name=schema_name)
        subscription = SchoolSubscription.objects.get(school=school)
        addon = AddOn.objects.get(id=addon_id, is_active=True)
    except (School.DoesNotExist, SchoolSubscription.DoesNotExist, AddOn.DoesNotExist):
        logger.warning("Webhook: school/subscription/addon not found for ref %s", reference)
        return

    school_addon, created = SchoolAddOn.objects.get_or_create(
        subscription=subscription,
        addon=addon,
        defaults={'is_active': True}
    )
    if not created and not school_addon.is_active:
        school_addon.is_active = True
        school_addon.expires_at = None
        school_addon.save(update_fields=['is_active', 'expires_at'])
        logger.info("Webhook: re-activated school addon %s for %s (ref %s)", addon.slug, schema_name, reference)
    elif created:
        logger.info("Webhook: activated school addon %s for %s (ref %s)", addon.slug, schema_name, reference)
    else:
        logger.info("Webhook: school addon %s already active for %s (ref %s)", addon.slug, schema_name, reference)

    subscription.calculate_mrr()


# =====================
# SYSTEM HEALTH & SUPPORT
# =====================

@login_required
@user_passes_test(lambda u: u.is_staff)
def system_health_dashboard(request):
    """Real-time system health monitoring dashboard"""
    from .models import SystemHealthMetric, School
    from django.db.models import Avg, Count
    from datetime import timedelta
    
    now = timezone.now()
    last_hour = now - timedelta(hours=1)
    
    # Get latest metrics for each type
    latest_metrics = {}
    for metric_type, _ in SystemHealthMetric.METRIC_TYPES:
        metric = SystemHealthMetric.objects.filter(
            metric_type=metric_type
        ).order_by('-recorded_at').first()
        if metric:
            latest_metrics[metric_type] = metric
    
    # Get hourly averages
    hourly_stats = SystemHealthMetric.objects.filter(
        recorded_at__gte=last_hour
    ).values('metric_type').annotate(
        avg_value=Avg('value'),
        count=Count('id')
    )
    
    # Get critical/warning metrics
    alerts = SystemHealthMetric.objects.filter(
        recorded_at__gte=last_hour,
        status__in=['warning', 'critical']
    ).order_by('-recorded_at')[:10]
    
    # School stats
    total_schools = School.objects.count()
    active_schools = School.objects.filter(is_active=True).count()
    trial_schools = School.objects.filter(on_trial=True).count()
    
    context = {
        'latest_metrics': latest_metrics,
        'hourly_stats': hourly_stats,
        'alerts': alerts,
        'total_schools': total_schools,
        'active_schools': active_schools,
        'trial_schools': trial_schools,
    }
    
    return render(request, 'tenants/system_health.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def support_ticket_list(request):
    """List all support tickets"""
    from .models import SupportTicket
    
    status_filter = request.GET.get('status', 'open')
    category_filter = request.GET.get('category', '')
    
    tickets = SupportTicket.objects.select_related('school', 'created_by', 'assigned_to')
    
    if status_filter and status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    if category_filter:
        tickets = tickets.filter(category=category_filter)
    
    # Count by status
    status_counts = {
        'all': SupportTicket.objects.count(),
        'open': SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'resolved': SupportTicket.objects.filter(status='resolved').count(),
    }
    
    context = {
        'tickets': tickets[:50],  # Limit to 50 for performance
        'status_filter': status_filter,
        'category_filter': category_filter,
        'status_counts': status_counts,
    }
    
    return render(request, 'tenants/support_tickets.html', context)


@login_required
def support_ticket_detail(request, ticket_id):
    """View and manage a support ticket"""
    from .models import SupportTicket, TicketComment
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    # Check permissions
    if not request.user.is_staff and ticket.school != request.tenant:
        messages.error(request, "Access denied")
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_comment':
            message = request.POST.get('message', '').strip()
            is_internal = request.POST.get('is_internal') == 'on'
            
            if message:
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    message=message,
                    is_staff_reply=request.user.is_staff,
                    is_internal=is_internal
                )
                messages.success(request, "Comment added")
        
        elif action == 'update_status' and request.user.is_staff:
            new_status = request.POST.get('status')
            ticket.status = new_status
            ticket.save()
            messages.success(request, f"Ticket status updated to {ticket.get_status_display()}")
        
        elif action == 'assign' and request.user.is_staff:
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                ticket.assigned_to_id = assigned_to_id
                ticket.save()
                messages.success(request, "Ticket assigned")
        
        return redirect('tenants:support_ticket_detail', ticket_id=ticket.id)
    
    comments = ticket.comments.select_related('user').all()
    
    # Get staff users for assignment
    staff_users = get_user_model().objects.filter(is_staff=True) if request.user.is_staff else []
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'staff_users': staff_users,
    }
    
    return render(request, 'tenants/support_ticket_detail.html', context)


@login_required
def create_support_ticket(request):
    """Create a new support ticket"""
    from .models import SupportTicket
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'technical')
        priority = request.POST.get('priority', 'medium')
        
        if not subject or not description:
            messages.error(request, "Subject and description are required")
            return redirect('tenants:create_support_ticket')
        
        # Get school from tenant context
        school = request.tenant if hasattr(request, 'tenant') else None
        
        ticket = SupportTicket.objects.create(
            school=school,
            created_by=request.user,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
        )
        
        messages.success(request, f"Ticket {ticket.ticket_number} created successfully")
        return redirect('tenants:support_ticket_detail', ticket_id=ticket.id)
    
    context = {
        'categories': SupportTicket.CATEGORY_CHOICES,
        'priorities': SupportTicket.PRIORITY_CHOICES,
    }
    
    return render(request, 'tenants/create_support_ticket.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def database_backups(request):
    """Manage database backups"""
    from .models import DatabaseBackup, School
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'trigger_backup':
            import subprocess, os, tempfile, shutil
            from django.conf import settings as _settings
            from django.utils import timezone as _tz

            school_id = request.POST.get('school_id')
            backup_type = request.POST.get('backup_type', 'full')

            school = None
            schema_name = 'public'
            if school_id:
                school = School.objects.get(id=school_id)
                schema_name = school.schema_name

            backup = DatabaseBackup.objects.create(
                school=school,
                backup_type=backup_type,
                status='in_progress',
            )

            try:
                # Build output path inside MEDIA_ROOT/backups/
                backup_dir = os.path.join(_settings.MEDIA_ROOT, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = _tz.now().strftime('%Y%m%d_%H%M%S')
                filename = f'backup_{schema_name}_{timestamp}.dump'
                output_path = os.path.join(backup_dir, filename)

                # Parse DATABASE_URL or fall back to individual settings
                db = _settings.DATABASES['default']
                env = os.environ.copy()
                env['PGPASSWORD'] = db.get('PASSWORD', '')

                cmd = [
                    'pg_dump',
                    '--format=custom',
                    f'--host={db.get("HOST", "localhost")}',
                    f'--port={db.get("PORT", 5432)}',
                    f'--username={db.get("USER", "postgres")}',
                    f'--schema={schema_name}',
                    '--no-password',
                    f'--file={output_path}',
                    db.get('NAME', ''),
                ]

                result = subprocess.run(
                    cmd, env=env, capture_output=True, text=True, timeout=300
                )

                if result.returncode == 0:
                    file_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 3)
                    backup.status = 'completed'
                    backup.file_path = f'backups/{filename}'
                    backup.file_size_mb = file_size_mb
                    backup.completed_at = _tz.now()
                    backup.save()
                    messages.success(request, f'Backup completed: {filename} ({file_size_mb} MB)')
                else:
                    backup.status = 'failed'
                    backup.notes = result.stderr[:500]
                    backup.save()
                    messages.error(request, f'pg_dump failed: {result.stderr[:200]}')

            except FileNotFoundError:
                # pg_dump not available (e.g. serverless/Vercel)
                backup.status = 'failed'
                backup.notes = 'pg_dump binary not found on this host. Use a database-level backup tool instead.'
                backup.save()
                messages.warning(request, 'pg_dump is not available on this hosting environment. Use your database provider\'s backup tool (e.g. Neon Console).')
            except subprocess.TimeoutExpired:
                backup.status = 'failed'
                backup.notes = 'pg_dump timed out after 300 seconds.'
                backup.save()
                messages.error(request, 'Backup timed out. Try a smaller scope backup.')
            except Exception as exc:
                backup.status = 'failed'
                backup.notes = str(exc)[:500]
                backup.save()
                messages.error(request, f'Backup error: {exc}')

            return redirect('tenants:database_backups')
    
    # Get recent backups
    backups = DatabaseBackup.objects.select_related('school').order_by('-started_at')[:50]
    
    # Get schools for backup selection
    schools = School.objects.filter(is_active=True).order_by('name')
    
    # Stats
    total_backups = DatabaseBackup.objects.count()
    completed_backups = DatabaseBackup.objects.filter(status='completed').count()
    failed_backups = DatabaseBackup.objects.filter(status='failed').count()
    total_size_gb = DatabaseBackup.objects.filter(
        status='completed'
    ).aggregate(total=Sum('file_size_mb'))['total'] or 0
    total_size_gb = total_size_gb / 1024
    
    context = {
        'backups': backups,
        'schools': schools,
        'total_backups': total_backups,
        'completed_backups': completed_backups,
        'failed_backups': failed_backups,
        'total_size_gb': round(total_size_gb, 2),
    }
    
    return render(request, 'tenants/database_backups.html', context)


def application_status(request):
    """Public page for applicants to check their school application approval status."""
    schema = request.GET.get('school', '').strip().lower()
    school = None
    error = None
    if schema:
        school = School.objects.filter(schema_name=schema).first()
        if not school:
            error = "No application found for that school ID. Please double-check and try again."
    return render(request, 'tenants/application_status.html', {
        'school': school,
        'queried': bool(schema),
        'error': error,
        'schema_query': schema,
    })


def pricing_page(request):
    """Public pricing page showing available subscription plans."""
    from .models import SubscriptionPlan
    plans = SubscriptionPlan.objects.filter(is_active=True).exclude(plan_type='trial').order_by('monthly_price')
    return render(request, 'tenants/pricing.html', {'plans': plans})


@login_required
def initiate_plan_upgrade(request):
    """School admin: initiate a Paystack payment to upgrade the subscription plan."""
    import requests as req_lib
    import uuid

    if not hasattr(request, 'tenant'):
        return redirect('home')
    if request.user.user_type != 'admin':
        messages.error(request, "Access denied. School admins only.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('tenants:school_subscription')

    from .models import SchoolSubscription, SubscriptionPlan
    from django.utils import timezone as _tz

    plan_id = request.POST.get('plan_id')
    billing_cycle = request.POST.get('billing_cycle', 'monthly')
    if billing_cycle not in ('monthly', 'quarterly', 'annual'):
        billing_cycle = 'monthly'

    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)

    # Determine amount based on billing cycle (GHS)
    if billing_cycle == 'annual':
        amount_ghs = plan.annual_price
    elif billing_cycle == 'quarterly':
        amount_ghs = plan.quarterly_price
    else:
        amount_ghs = plan.monthly_price

    if amount_ghs <= 0:
        messages.error(request, "Invalid plan amount. Please contact support.")
        return redirect('tenants:school_subscription')

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    if not secret_key:
        messages.error(request, 'Paystack is not configured. Please contact platform admin.')
        return redirect('tenants:school_subscription')

    try:
        subscription = _get_school_subscription_safe(request.tenant)
        email = request.user.email or f"admin_{request.tenant.schema_name}@schoolportal.app"
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No subscription found for your school.")
        return redirect('tenants:school_subscription')
    except ProgrammingError:
        messages.error(request, "Subscription data is outdated for this school. Please ask support to run tenant migrations.")
        return redirect('tenants:school_subscription')

    # Double-payment guard: block same plan/cycle if already active and >7 days remaining
    _now = _tz.now()
    if (
        subscription.status == 'active'
        and subscription.plan_id == plan.id
        and subscription.billing_cycle == billing_cycle
        and subscription.current_period_end
        and subscription.current_period_end > _now + timedelta(days=7)
    ):
        _expiry = subscription.current_period_end.strftime('%b %d, %Y')
        messages.warning(
            request,
            f"You already have an active {plan.name} ({billing_cycle}) subscription "
            f"valid until {_expiry}. No payment is needed right now. "
            "You can renew within 7 days of expiry."
        )
        return redirect('tenants:school_subscription')

    reference = f"PLN-{request.tenant.id}-{plan.id}-{uuid.uuid4().hex[:8].upper()}"
    # Paystack uses smallest currency unit (pesewas for GHS)
    amount_minor = int(amount_ghs * 100)

    from django.urls import reverse as _rev
    callback_url = request.build_absolute_uri(_rev('tenants:upgrade_plan_callback'))

    payload = {
        'email': email,
        'amount': amount_minor,
        'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'GHS'),
        'reference': reference,
        'callback_url': callback_url,
        'metadata': {
            'school_id': request.tenant.id,
            'plan_id': plan.id,
            'billing_cycle': billing_cycle,
            'custom_fields': [
                {'display_name': 'School', 'variable_name': 'school', 'value': request.tenant.name},
                {'display_name': 'Plan', 'variable_name': 'plan', 'value': plan.name},
            ],
        },
    }

    try:
        resp = req_lib.post(
            'https://api.paystack.co/transaction/initialize',
            json=payload,
            headers={
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
        data = resp.json()
        if data.get('status'):
            return redirect(data['data']['authorization_url'])
        else:
            messages.error(request, f"Paystack error: {data.get('message', 'Unknown error')}")
    except Exception as exc:
        messages.error(request, f"Payment gateway unavailable: {exc}")

    return redirect('tenants:school_subscription')


@login_required
def upgrade_plan_callback(request):
    """Handle Paystack redirect after plan upgrade payment."""
    import requests as req_lib

    if not hasattr(request, 'tenant'):
        return redirect('home')
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('tenants:school_subscription')

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    try:
        resp = req_lib.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={'Authorization': f'Bearer {secret_key}'},
            timeout=15,
        )
        data = resp.json()
    except Exception as exc:
        messages.error(request, f"Could not verify payment: {exc}")
        return redirect('tenants:school_subscription')

    if not data.get('status') or data['data']['status'] != 'success':
        messages.warning(request, 'Payment was not completed or verification failed.')
        return redirect('tenants:school_subscription')

    trx = data['data']
    meta = trx.get('metadata', {})
    plan_id = meta.get('plan_id')
    billing_cycle = meta.get('billing_cycle', 'monthly')

    if not plan_id:
        messages.error(request, 'Plan information missing from payment. Contact support.')
        return redirect('tenants:school_subscription')

    from .models import SchoolSubscription, SubscriptionPlan
    from django.utils import timezone as _tz
    from calendar import monthrange as _mr

    def _add_months(dt, months):
        """Add N months to a datetime, clamping day to month-end."""
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, _mr(year, month)[1])
        return dt.replace(year=year, month=month, day=day)

    plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()
    if not plan:
        messages.error(request, 'The selected plan no longer exists. Contact support.')
        return redirect('tenants:school_subscription')

    try:
        subscription = _get_school_subscription_safe(request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, 'No subscription found. Contact support.')
        return redirect('tenants:school_subscription')
    except ProgrammingError:
        messages.error(request, "Subscription data is outdated for this school. Please ask support to run tenant migrations.")
        return redirect('tenants:school_subscription')

    # Calculate new period end
    now_dt = _tz.now()
    if billing_cycle == 'annual':
        period_end = _add_months(now_dt, 12)
    elif billing_cycle == 'quarterly':
        period_end = _add_months(now_dt, 3)
    else:
        period_end = _add_months(now_dt, 1)

    # Calculate MRR
    if billing_cycle == 'annual':
        mrr = plan.annual_price / 12
    elif billing_cycle == 'quarterly':
        mrr = plan.quarterly_price / 3
    else:
        mrr = plan.monthly_price

    subscription.plan = plan
    subscription.billing_cycle = billing_cycle
    subscription.status = 'active'
    subscription.current_period_start = now_dt
    subscription.current_period_end = period_end
    subscription.trial_ends_at = None
    subscription.mrr = mrr
    subscription.save(update_fields=[
        'plan', 'billing_cycle', 'status',
        'current_period_start', 'current_period_end',
        'trial_ends_at', 'mrr',
    ])

    # Audit log the subscription upgrade
    from .subscription_models import AuditLog
    AuditLog.log('subscription_change', request=request,
                 detail=f'Upgraded to {plan.name} ({billing_cycle}), MRR=₵{mrr}',
                 tenant_schema=getattr(request.tenant, 'schema_name', ''))

    # Create an invoice record for billing history
    from .models import Invoice as _Inv
    _inv_amount = plan.annual_price if billing_cycle == 'annual' else (
        plan.quarterly_price if billing_cycle == 'quarterly' else plan.monthly_price
    )
    _Inv.objects.get_or_create(
        invoice_number=f"INV-{reference}",
        defaults={
            'subscription': subscription,
            'status': 'paid',
            'subtotal': _inv_amount,
            'tax': 0,
            'total': _inv_amount,
            'issued_at': now_dt,
            'due_at': now_dt,
            'paid_at': now_dt,
            'line_items': [{'description': f"{plan.name} ({billing_cycle})", 'amount': str(_inv_amount)}],
        }
    )

    messages.success(
        request,
        f"✅ Plan upgraded to {plan.name} ({billing_cycle}). Your access is now fully active!"
    )
    return redirect('tenants:school_subscription')


@login_required
def school_subscription(request):
    """School admin: view current subscription status, trial countdown, and usage."""
    if not hasattr(request, 'tenant'):
        return redirect('home')
    if request.user.user_type not in ('admin',):
        messages.error(request, "Access denied. School admins only.")
        return redirect('dashboard')

    from .models import SchoolSubscription
    from django.utils import timezone

    try:
        try:
            with transaction.atomic():
                subscription = SchoolSubscription.objects.select_related('plan').get(school=request.tenant)
        except ProgrammingError:
            subscription = SchoolSubscription.objects.defer(
                'paystack_subscription_code', 'paystack_customer_code', 'mrr',
            ).select_related('plan').get(school=request.tenant)
    except SchoolSubscription.DoesNotExist:
        subscription = None

    trial_days_left = None
    if subscription and subscription.status == 'trial' and subscription.trial_ends_at:
        delta = subscription.trial_ends_at - timezone.now()
        trial_days_left = max(0, delta.days)

    from .models import SubscriptionPlan
    upgrade_plans = SubscriptionPlan.objects.filter(
        is_active=True
    ).exclude(plan_type='trial').order_by('monthly_price')

    from .ai_quota import get_quota_status
    quota = get_quota_status(request.tenant, subscription=subscription)

    recent_invoices = []
    active_addons = []
    if subscription:
        from .models import Invoice, SchoolAddOn
        try:
            with transaction.atomic():
                recent_invoices = list(
                    Invoice.objects.defer('payment_reference')
                    .filter(subscription=subscription)
                    .order_by('-issued_at')[:6]
                )
        except (ProgrammingError, Exception):
            recent_invoices = []
        try:
            with transaction.atomic():
                active_addons = list(
                    SchoolAddOn.objects.filter(subscription=subscription, is_active=True)
                    .select_related('addon')
                )
        except (ProgrammingError, Exception):
            active_addons = []

        # Sync live counts into the subscription usage fields
        from accounts.models import User as _User
        _students = _User.objects.filter(user_type='student').count()
        _teachers = _User.objects.filter(user_type='teacher').count()
        if (subscription.current_students != _students or
                subscription.current_teachers != _teachers):
            subscription.current_students = _students
            subscription.current_teachers = _teachers
            subscription.save(update_fields=['current_students', 'current_teachers'])

    # renewal_allowed: True if school CAN pay again right now.
    # False when subscription is active AND expiry is >7 days away (block double payment).
    from datetime import timedelta as _td
    _now = timezone.now()
    renewal_allowed = not (
        subscription
        and subscription.status == 'active'
        and subscription.current_period_end
        and subscription.current_period_end > _now + _td(days=7)
    )

    context = {
        'subscription': subscription,
        'trial_active': bool(subscription and subscription.status == 'trial'),
        'trial_days_left': trial_days_left,
        'upgrade_plans': upgrade_plans,
        'school': request.tenant,
        'quota': quota,
        'recent_invoices': recent_invoices,
        'active_addons': active_addons,
        'renewal_allowed': renewal_allowed,
    }
    return render(request, 'tenants/school_subscription.html', context)


@login_required
def activate_school_plan(request, school_id):
    """Landlord: activate or change a school's subscription plan."""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('home')

    from .models import SchoolSubscription, SubscriptionPlan

    school = get_object_or_404(School, id=school_id)

    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('monthly_price')

    # Existing subscription (may not exist)
    try:
        try:
            with transaction.atomic():
                subscription = SchoolSubscription.objects.select_related('plan').get(school=school)
        except ProgrammingError:
            subscription = SchoolSubscription.objects.defer(
                'paystack_subscription_code', 'paystack_customer_code', 'mrr',
            ).select_related('plan').get(school=school)
    except SchoolSubscription.DoesNotExist:
        subscription = None

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        mrr = request.POST.get('mrr', '0')
        extend_trial_days = request.POST.get('extend_trial_days', '').strip()
        new_status = request.POST.get('status', 'active')

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except (SubscriptionPlan.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Invalid plan selected.")
            return redirect('tenants:activate_plan', school_id=school_id)

        try:
            mrr_val = float(mrr)
        except (ValueError, TypeError):
            mrr_val = 0.0

        now_dt = timezone.now()
        if billing_cycle == 'monthly':
            period_end = now_dt + timedelta(days=30)
        elif billing_cycle == 'quarterly':
            period_end = now_dt + timedelta(days=91)
        else:
            period_end = now_dt + timedelta(days=365)

        if subscription:
            subscription.plan = plan
            subscription.billing_cycle = billing_cycle
            subscription.mrr = mrr_val
            subscription.status = new_status
            subscription.current_period_start = now_dt
            subscription.current_period_end = period_end
            if new_status == 'trial':
                extra_days = int(extend_trial_days) if extend_trial_days.isdigit() else 14
                subscription.trial_ends_at = now_dt + timedelta(days=extra_days)
            else:
                subscription.trial_ends_at = None
            subscription.save()
        else:
            trial_ends = now_dt + timedelta(days=int(extend_trial_days) if extend_trial_days.isdigit() else 14)
            SchoolSubscription.objects.create(
                school=school,
                plan=plan,
                billing_cycle=billing_cycle,
                status=new_status,
                mrr=mrr_val,
                started_at=now_dt,
                current_period_start=now_dt,
                current_period_end=period_end,
                trial_ends_at=trial_ends if new_status == 'trial' else None,
            )

        messages.success(
            request,
            f"✅ {school.name} — plan set to {plan.name} ({new_status}), MRR: ${mrr_val:.2f}.",
        )
        return redirect('tenants:activate_plan', school_id=school_id)

    context = {
        'school': school,
        'subscription': subscription,
        'plans': plans,
    }
    return render(request, 'tenants/activate_plan.html', context)


@csrf_exempt
def paystack_subscription_webhook(request):
    """
    Platform-level Paystack webhook — activates a school subscription after a
    successful plan-upgrade payment (reference prefix: PLN-).

    Register this URL in the Paystack dashboard under:
      Settings → API Keys & Webhooks → Webhook URL
    e.g. https://yourdomain.com/tenants/paystack/webhook/

    This is the safety net for cases where the browser redirect callback
    (/subscription/upgrade/callback/) is missed (network drop, closed tab).
    """
    import hmac as _hmac
    import hashlib
    import json as _json
    from calendar import monthrange as _mr
    from django.utils import timezone as _tz

    if request.method != 'POST':
        return HttpResponse(status=405)

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    signature  = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
    body       = request.body

    # Verify HMAC-SHA512 signature to confirm the request is from Paystack
    if secret_key:
        expected = _hmac.new(secret_key.encode(), body, hashlib.sha512).hexdigest()
        if not _hmac.compare_digest(expected, signature):
            logger.warning("Paystack subscription webhook: HMAC mismatch — rejected.")
            return HttpResponse(status=400)

    try:
        payload = _json.loads(body)
    except Exception:
        return HttpResponse(status=400)

    if payload.get('event') != 'charge.success':
        return HttpResponse(status=200)

    trx       = payload['data']
    reference = trx.get('reference', '')
    meta      = trx.get('metadata', {})

    # Only handle plan-upgrade payments (fee payments start with SPS-)
    if not reference.startswith('PLN-'):
        return HttpResponse(status=200)

    plan_id      = meta.get('plan_id')
    billing_cycle = meta.get('billing_cycle', 'monthly')
    school_id    = meta.get('school_id')

    if not plan_id or not school_id:
        logger.error(f"Paystack subscription webhook: missing plan_id/school_id in metadata (ref={reference})")
        return HttpResponse(status=200)

    from .models import SchoolSubscription, SubscriptionPlan, Invoice

    plan   = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()
    school = School.objects.filter(id=school_id).first()

    if not plan or not school:
        logger.error(f"Paystack subscription webhook: plan {plan_id} or school {school_id} not found (ref={reference})")
        return HttpResponse(status=200)

    try:
        with transaction.atomic():
            subscription = SchoolSubscription.objects.filter(school=school).first()
    except ProgrammingError:
        subscription = SchoolSubscription.objects.defer(
            'paystack_subscription_code', 'paystack_customer_code', 'mrr',
        ).filter(school=school).first()
    if not subscription:
        logger.error(f"Paystack subscription webhook: no subscription for school {school_id} (ref={reference})")
        return HttpResponse(status=200)

    def _add_months(dt, months):
        month = dt.month - 1 + months
        year  = dt.year + month // 12
        month = month % 12 + 1
        day   = min(dt.day, _mr(year, month)[1])
        return dt.replace(year=year, month=month, day=day)

    now_dt = _tz.now()
    if billing_cycle == 'annual':
        period_end   = _add_months(now_dt, 12)
        mrr          = plan.annual_price / 12
        invoice_amt  = plan.annual_price
    elif billing_cycle == 'quarterly':
        period_end   = _add_months(now_dt, 3)
        mrr          = plan.quarterly_price / 3
        invoice_amt  = plan.quarterly_price
    else:
        period_end   = _add_months(now_dt, 1)
        mrr          = plan.monthly_price
        invoice_amt  = plan.monthly_price

    subscription.plan                      = plan
    subscription.billing_cycle             = billing_cycle
    subscription.status                    = 'active'
    subscription.current_period_start      = now_dt
    subscription.current_period_end        = period_end
    subscription.trial_ends_at             = None
    subscription.mrr                       = mrr
    # Store Paystack identifiers for future reference / renewals
    ps_sub_code = meta.get('subscription_code', '') or trx.get('subscription_code', '')
    ps_cust_code = (trx.get('customer') or {}).get('customer_code', '')
    if ps_sub_code:
        subscription.paystack_subscription_code = ps_sub_code
    if ps_cust_code:
        subscription.paystack_customer_code = ps_cust_code
    subscription.save(update_fields=[
        'plan', 'billing_cycle', 'status',
        'current_period_start', 'current_period_end',
        'trial_ends_at', 'mrr',
        'paystack_subscription_code', 'paystack_customer_code',
    ])

    Invoice.objects.get_or_create(
        invoice_number=f"INV-{reference}",
        defaults={
            'subscription': subscription,
            'status': 'paid',
            'subtotal': invoice_amt,
            'tax': 0,
            'total': invoice_amt,
            'issued_at': now_dt,
            'due_at': now_dt,
            'paid_at': now_dt,
            'payment_reference': reference,
            'line_items': [
                {'description': f"{plan.name} ({billing_cycle})", 'amount': str(invoice_amt)}
            ],
        }
    )

    logger.info(
        f"Paystack subscription webhook: activated {plan.name} ({billing_cycle}) "
        f"for school '{school.name}' (ref={reference})"
    )
    return HttpResponse(status=200)


# ── Individual Addon Pricing Management ──────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def addon_pricing_management(request):
    """Landlord view to manage individual addon catalog and prices."""
    from individual_users.models import IndividualAddon
    import json as _json

    addons = IndividualAddon.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_prices':
            updated = 0
            for addon in addons:
                prefix = f'addon_{addon.pk}_'
                new_prices = {}
                for plan in addon.plans:
                    key = f'{prefix}price_{plan}'
                    val = request.POST.get(key, '')
                    if val != '':
                        try:
                            new_prices[plan] = round(float(val), 2)
                        except (ValueError, TypeError):
                            continue
                if new_prices and new_prices != addon.prices:
                    addon.prices = new_prices
                    addon.save(update_fields=['prices', 'updated_at'])
                    updated += 1

                # Update is_active toggle
                active_key = f'{prefix}active'
                new_active = active_key in request.POST
                if new_active != addon.is_active:
                    addon.is_active = new_active
                    addon.save(update_fields=['is_active', 'updated_at'])
                    updated += 1

            if updated:
                messages.success(request, f'Updated {updated} addon(s).')
            else:
                messages.info(request, 'No changes detected.')
            return redirect('tenants:addon_pricing')

        elif action == 'create_addon':
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            category = request.POST.get('category', 'productivity')
            description = request.POST.get('description', '').strip()
            icon = request.POST.get('icon', 'bi-box-seam').strip()
            tagline = request.POST.get('tagline', '').strip()
            badge_label = request.POST.get('badge_label', '').strip()
            audience = request.POST.get('audience', 'all')
            plans_raw = request.POST.get('plans', 'free').strip()
            prices_raw = request.POST.get('prices', '{}').strip()
            features_raw = request.POST.get('features', '').strip()
            trial_days = int(request.POST.get('trial_days', '0') or '0')

            if not name or not slug:
                messages.error(request, 'Name and slug are required.')
            elif IndividualAddon.objects.filter(slug=slug).exists():
                messages.error(request, f'Addon with slug "{slug}" already exists.')
            else:
                plans_list = [p.strip() for p in plans_raw.split(',') if p.strip()]
                try:
                    prices_dict = _json.loads(prices_raw) if prices_raw.startswith('{') else {}
                except (ValueError, TypeError):
                    prices_dict = {}
                features_list = [f.strip() for f in features_raw.split('\n') if f.strip()]

                IndividualAddon.objects.create(
                    name=name, slug=slug, tagline=tagline,
                    description=description, category=category,
                    audience=audience, icon=icon, badge_label=badge_label,
                    plans=plans_list, prices=prices_dict,
                    trial_days=trial_days, features=features_list,
                )
                messages.success(request, f'Addon "{name}" created.')
            return redirect('tenants:addon_pricing')

    # Compute stats
    total = addons.count()
    active = addons.filter(is_active=True).count()
    cats = addons.values('category').annotate(c=Count('id')).order_by('category')

    context = {
        'addons': addons,
        'total_addons': total,
        'active_addons': active,
        'inactive_addons': total - active,
        'categories': list(cats),
        'category_choices': IndividualAddon.CATEGORY_CHOICES,
        'audience_choices': IndividualAddon.AUDIENCE_CHOICES,
    }
    return render(request, 'tenants/addon_pricing.html', context)


# ── Individual Credit Pack Pricing Management ────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def credit_pack_pricing(request):
    """Super-admin view to manage AI credit pack prices and settings."""
    from individual_users.models import IndividualCreditPack, IndividualCreditTransaction
    from decimal import Decimal, InvalidOperation

    packs = IndividualCreditPack.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_packs':
            updated = 0
            for pack in packs:
                prefix = f'pack_{pack.pk}_'

                # Price
                new_price = request.POST.get(f'{prefix}price', '').strip()
                if new_price:
                    try:
                        new_price = Decimal(new_price).quantize(Decimal('0.01'))
                        if new_price != pack.price and new_price >= 0:
                            pack.price = new_price
                            pack.save(update_fields=['price'])
                            updated += 1
                    except (InvalidOperation, ValueError):
                        pass

                # Credits
                new_credits = request.POST.get(f'{prefix}credits', '').strip()
                if new_credits:
                    try:
                        new_credits = int(new_credits)
                        if new_credits != pack.credits and new_credits > 0:
                            pack.credits = new_credits
                            pack.save(update_fields=['credits'])
                            updated += 1
                    except (ValueError, TypeError):
                        pass

                # Badge label
                new_badge = request.POST.get(f'{prefix}badge', '').strip()
                if new_badge != pack.badge_label:
                    pack.badge_label = new_badge
                    pack.save(update_fields=['badge_label'])
                    updated += 1

                # Icon
                new_icon = request.POST.get(f'{prefix}icon', '').strip()
                if new_icon and new_icon != pack.icon:
                    pack.icon = new_icon
                    pack.save(update_fields=['icon'])
                    updated += 1

                # Position
                new_pos = request.POST.get(f'{prefix}position', '').strip()
                if new_pos:
                    try:
                        new_pos = int(new_pos)
                        if new_pos != pack.position:
                            pack.position = new_pos
                            pack.save(update_fields=['position'])
                            updated += 1
                    except (ValueError, TypeError):
                        pass

                # Active toggle
                active_key = f'{prefix}active'
                new_active = active_key in request.POST
                if new_active != pack.is_active:
                    pack.is_active = new_active
                    pack.save(update_fields=['is_active'])
                    updated += 1

            if updated:
                messages.success(request, f'Updated {updated} field(s) across credit packs.')
            else:
                messages.info(request, 'No changes detected.')
            return redirect('tenants:credit_pack_pricing')

        elif action == 'create_pack':
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            credits_val = request.POST.get('credits', '').strip()
            price_val = request.POST.get('price', '').strip()
            badge = request.POST.get('badge_label', '').strip()
            icon = request.POST.get('icon', 'bi-lightning-charge').strip()
            position = request.POST.get('position', '0').strip()

            if not name or not slug:
                messages.error(request, 'Name and slug are required.')
            elif IndividualCreditPack.objects.filter(slug=slug).exists():
                messages.error(request, f'Pack with slug "{slug}" already exists.')
            else:
                try:
                    IndividualCreditPack.objects.create(
                        name=name, slug=slug,
                        credits=int(credits_val or '0'),
                        price=Decimal(price_val or '0').quantize(Decimal('0.01')),
                        badge_label=badge, icon=icon,
                        position=int(position or '0'),
                    )
                    messages.success(request, f'Credit pack "{name}" created.')
                except (ValueError, InvalidOperation) as e:
                    messages.error(request, f'Invalid data: {e}')
            return redirect('tenants:credit_pack_pricing')

        elif action == 'delete_pack':
            pack_id = request.POST.get('pack_id', '').strip()
            if pack_id:
                try:
                    pack = IndividualCreditPack.objects.get(pk=int(pack_id))
                    pack_name = pack.name
                    pack.delete()
                    messages.success(request, f'Deleted pack "{pack_name}".')
                except IndividualCreditPack.DoesNotExist:
                    messages.error(request, 'Pack not found.')
            return redirect('tenants:credit_pack_pricing')

    # Stats
    total = packs.count()
    active = packs.filter(is_active=True).count()

    # Recent transactions (last 20)
    recent_txns = IndividualCreditTransaction.objects.filter(
        transaction_type='purchase'
    ).select_related('user').order_by('-created_at')[:20]
    total_revenue = IndividualCreditTransaction.objects.filter(
        transaction_type='purchase'
    ).count()

    context = {
        'packs': packs,
        'total_packs': total,
        'active_packs': active,
        'inactive_packs': total - active,
        'recent_purchases': recent_txns,
        'total_purchases': total_revenue,
    }
    return render(request, 'tenants/credit_pack_pricing.html', context)


# ── Promo Campaign Management ────────────────────────────────────────────────

PROMO_TEMPLATE_BODIES = {
    'feature_launch': (
        '<h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">'
        '🚀 Introducing: [Feature Name]</h2>'
        '<p>We\'re excited to announce <strong>[Feature Name]</strong> — '
        'a powerful new addition to SchoolPadi that will help you [key benefit].</p>'
        '<h3 style="font-size:16px;font-weight:700;color:#4361ee;margin:20px 0 8px;">What\'s New</h3>'
        '<ul style="padding-left:20px;margin:0 0 16px;">'
        '<li>[Benefit 1]</li><li>[Benefit 2]</li><li>[Benefit 3]</li></ul>'
        '<p><a href="#" style="display:inline-block;background:#4361ee;color:#fff;'
        'padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700;">'
        'Try It Now →</a></p>'
    ),
    'back_to_school': (
        '<h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">'
        '📚 Welcome Back! A New Term Awaits</h2>'
        '<p>The new academic term is here, and SchoolPadi is ready to make it your best one yet.</p>'
        '<h3 style="font-size:16px;font-weight:700;color:#10B981;margin:20px 0 8px;">Get Ready Checklist</h3>'
        '<ul style="padding-left:20px;margin:0 0 16px;">'
        '<li>✅ Update your class lists and student records</li>'
        '<li>✅ Set up the new term timetable</li>'
        '<li>✅ Configure fee structures for the term</li>'
        '<li>✅ Review and assign subjects to teachers</li></ul>'
        '<p>Need help getting set up? Our support team is standing by.</p>'
    ),
    'discount_offer': (
        '<h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">'
        '🎉 Special Offer: [X]% Off [Plan/Feature]!</h2>'
        '<p>For a limited time, enjoy <strong>[X]% off</strong> when you [upgrade/subscribe/add].</p>'
        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;'
        'padding:16px;margin:16px 0;text-align:center;">'
        '<div style="font-size:28px;font-weight:800;color:#4361ee;">SAVE [X]%</div>'
        '<div style="font-size:13px;color:#6b7280;margin-top:4px;">Use code: <strong>[CODE]</strong> · Expires [Date]</div></div>'
        '<p><a href="#" style="display:inline-block;background:#4361ee;color:#fff;'
        'padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700;">'
        'Claim Your Discount →</a></p>'
    ),
    're_engagement': (
        '<h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">'
        '👋 We Miss You!</h2>'
        '<p>It\'s been a while since you logged in to SchoolPadi. '
        'We\'ve been busy making things even better for your school.</p>'
        '<h3 style="font-size:16px;font-weight:700;color:#7C3AED;margin:20px 0 8px;">Since You\'ve Been Away</h3>'
        '<ul style="padding-left:20px;margin:0 0 16px;">'
        '<li>✨ [New Feature 1]</li><li>✨ [New Feature 2]</li><li>✨ [New Feature 3]</li></ul>'
        '<p>Come back and see what\'s new — your school dashboard is waiting.</p>'
        '<p><a href="#" style="display:inline-block;background:#7C3AED;color:#fff;'
        'padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700;">'
        'Log In Now →</a></p>'
    ),
    'newsletter': (
        '<h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">'
        '📬 SchoolPadi Monthly Update</h2>'
        '<p>Here\'s what\'s been happening on the platform this month.</p>'
        '<h3 style="font-size:16px;font-weight:700;color:#4361ee;margin:20px 0 8px;">Highlights</h3>'
        '<ul style="padding-left:20px;margin:0 0 16px;">'
        '<li><strong>[Update 1]</strong> — Brief description</li>'
        '<li><strong>[Update 2]</strong> — Brief description</li>'
        '<li><strong>[Update 3]</strong> — Brief description</li></ul>'
        '<h3 style="font-size:16px;font-weight:700;color:#10B981;margin:20px 0 8px;">Coming Soon</h3>'
        '<p>[Teaser about upcoming features]</p>'
        '<p style="font-size:13px;color:#6b7280;margin-top:20px;">— The SchoolPadi Team</p>'
    ),
}


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def promo_campaigns(request):
    """List all promo campaigns and handle create / delete."""
    from .models import PromoCampaign

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            subject = request.POST.get('subject', '').strip()
            body_html = request.POST.get('body_html', '').strip()
            audience = request.POST.get('audience', 'all_schools')
            template_key = request.POST.get('template_key', '')
            scheduled_for_str = request.POST.get('scheduled_for', '').strip()

            # If template chosen and no custom body, use template body
            if template_key and template_key in PROMO_TEMPLATE_BODIES and not body_html:
                body_html = PROMO_TEMPLATE_BODIES[template_key]

            if not title or not subject or not body_html:
                messages.error(request, 'Title, subject, and body are required.')
            else:
                status = 'draft'
                scheduled_for = None
                if scheduled_for_str:
                    try:
                        from django.utils.dateparse import parse_datetime
                        scheduled_for = parse_datetime(scheduled_for_str)
                        if scheduled_for:
                            status = 'scheduled'
                    except (ValueError, TypeError):
                        pass

                PromoCampaign.objects.create(
                    title=title, subject=subject, body_html=body_html,
                    audience=audience, template_key=template_key,
                    scheduled_for=scheduled_for, status=status,
                    created_by=request.user,
                )
                label = 'scheduled' if status == 'scheduled' else 'draft'
                messages.success(request, f'Campaign "{title}" created as {label}.')
            return redirect('tenants:promo_campaigns')

        if action == 'delete':
            pk = request.POST.get('campaign_id')
            camp = PromoCampaign.objects.filter(pk=pk).exclude(status='sent').first()
            if camp:
                camp.delete()
                messages.success(request, 'Campaign deleted.')
            else:
                messages.error(request, 'Only draft/scheduled campaigns can be deleted.')
            return redirect('tenants:promo_campaigns')

    campaigns = PromoCampaign.objects.all()
    stats = {
        'total': campaigns.count(),
        'drafts': campaigns.filter(status='draft').count(),
        'scheduled': campaigns.filter(status='scheduled').count(),
        'sent': campaigns.filter(status='sent').count(),
        'total_sent': sum(c.sent_count for c in campaigns.filter(status='sent')),
    }
    return render(request, 'tenants/promo_campaigns.html', {
        'campaigns': campaigns,
        'stats': stats,
        'audience_choices': PromoCampaign.AUDIENCE_CHOICES,
        'template_choices': PromoCampaign.TEMPLATE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def promo_campaign_edit(request, pk):
    """Edit a draft or scheduled campaign."""
    from .models import PromoCampaign
    campaign = get_object_or_404(PromoCampaign, pk=pk)

    if campaign.status == 'sent':
        messages.error(request, 'Sent campaigns cannot be edited.')
        return redirect('tenants:promo_campaigns')

    if request.method == 'POST':
        campaign.title = request.POST.get('title', campaign.title).strip()
        campaign.subject = request.POST.get('subject', campaign.subject).strip()
        campaign.body_html = request.POST.get('body_html', campaign.body_html).strip()
        campaign.audience = request.POST.get('audience', campaign.audience)
        campaign.template_key = request.POST.get('template_key', campaign.template_key)

        scheduled_for_str = request.POST.get('scheduled_for', '').strip()
        if scheduled_for_str:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(scheduled_for_str)
            if dt:
                campaign.scheduled_for = dt
                campaign.status = 'scheduled'
        else:
            campaign.scheduled_for = None
            if campaign.status == 'scheduled':
                campaign.status = 'draft'

        campaign.save()
        messages.success(request, 'Campaign updated.')
        return redirect('tenants:promo_campaigns')

    return render(request, 'tenants/promo_campaign_edit.html', {
        'campaign': campaign,
        'audience_choices': PromoCampaign.AUDIENCE_CHOICES,
        'template_choices': PromoCampaign.TEMPLATE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def promo_campaign_send(request, pk):
    """Send a promo campaign to its target audience."""
    from .models import PromoCampaign
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    campaign = get_object_or_404(PromoCampaign, pk=pk)

    if campaign.status == 'sent':
        messages.warning(request, 'This campaign has already been sent.')
        return redirect('tenants:promo_campaigns')

    if request.method != 'POST':
        # Build recipient preview
        recipients = _get_campaign_recipients(campaign.audience)
        return render(request, 'tenants/promo_campaign_confirm.html', {
            'campaign': campaign,
            'recipients': recipients,
            'recipient_count': len(recipients),
        })

    # Actually send
    recipients = _get_campaign_recipients(campaign.audience)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@schoolpadi.com')
    sent = 0
    failed = 0

    for recip in recipients:
        try:
            html_body = render_to_string('tenants/emails/promo_email.html', {
                'subject': campaign.subject,
                'body_html': campaign.body_html,
                'recipient_name': recip['name'],
            })
            send_mail(
                subject=campaign.subject,
                message='',
                from_email=from_email,
                recipient_list=[recip['email']],
                html_message=html_body,
                fail_silently=True,
            )
            sent += 1
        except Exception:
            failed += 1

    campaign.status = 'sent'
    campaign.sent_count = sent
    campaign.failed_count = failed
    campaign.sent_at = timezone.now()
    campaign.save()

    messages.success(request, f'Campaign sent to {sent} recipient(s). {failed} failed.')
    return redirect('tenants:promo_campaigns')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def promo_template_body(request, template_key):
    """Return the pre-built HTML body for a template key (JSON)."""
    body = PROMO_TEMPLATE_BODIES.get(template_key, '')
    return JsonResponse({'body': body})


def _get_campaign_recipients(audience):
    """Return list of {'name': ..., 'email': ...} for campaign audience."""
    recipients = []

    if audience in ('all_schools', 'trial_schools', 'approved_schools'):
        qs = School.objects.filter(is_active=True)
        if audience == 'trial_schools':
            qs = qs.filter(on_trial=True)
        elif audience == 'approved_schools':
            qs = qs.filter(approval_status='approved')
        for s in qs.exclude(contact_person_email=''):
            recipients.append({
                'name': s.contact_person_name or s.name,
                'email': s.contact_person_email,
            })

    elif audience in ('individual_teachers', 'individual_all'):
        from individual_users.models import IndividualProfile
        qs = IndividualProfile.objects.select_related('user').filter(
            user__is_active=True,
        ).exclude(user__email='')
        if audience == 'individual_teachers':
            qs = qs.filter(role='teacher')
        for p in qs:
            recipients.append({
                'name': p.user.get_full_name() or p.user.username,
                'email': p.user.email,
            })

    return recipients


# ── Landlord AI Agents ──────────────────────────────────────────────

LANDLORD_AGENT_META = {
    'pmm': {
        'label': 'Product Marketing Manager',
        'icon': 'bi-megaphone-fill',
        'color': '#7C3AED',
        'tagline': 'Plan launches, positioning, pricing strategy & growth experiments.',
        'system': (
            "You are a senior Product Marketing Manager for SchoolPadi, "
            "a multi-tenant SaaS school management platform serving schools across Ghana and West Africa.\n\n"
            "Your expertise:\n"
            "- Go-to-market strategy for new features, addons, and pricing tiers\n"
            "- Competitive positioning against other school management tools\n"
            "- Growth experiments (referral loops, viral hooks, activation funnels)\n"
            "- Pricing & packaging optimization for schools of different sizes\n"
            "- Feature launch playbooks (emails, in-app banners, webinars)\n"
            "- User persona development and segmentation\n"
            "- Conversion rate optimization for signup → trial → paid\n\n"
            "When the user provides context about a feature, campaign, or pricing decision, "
            "give specific, actionable advice grounded in SaaS best practices. "
            "Reference real SaaS playbooks where helpful.\n\n"
            "CONVERSATION STYLE:\n"
            "- Be concise and conversational. Keep responses focused — aim for 150-300 words unless the user explicitly asks for a full deliverable.\n"
            "- Do NOT dump entire campaigns, full week plans, or multi-page strategies in one message. Instead, give a tight summary or framework FIRST, then offer to expand specific sections.\n"
            "- Example: instead of writing 7 days of social posts, outline the weekly theme structure and write Day 1 as a sample, then ask 'Want me to continue with Days 2-7?'\n"
            "- Use short bullet points and tables for clarity, not walls of text.\n"
            "- Ask clarifying questions when the request is broad rather than guessing and over-delivering.\n"
            "- End with a clear next-step question or offer to go deeper on a specific area."
        ),
    },
    'curriculum': {
        'label': 'Curriculum Analyst',
        'icon': 'bi-journal-check',
        'color': '#10B981',
        'tagline': 'Ensure GES compliance, review standards alignment & syllabus coverage.',
        'system': (
            "You are a Curriculum Analyst specialised in the Ghana Education Service (GES) "
            "National Pre-tertiary Education Curriculum Framework (NaCCA/NPTECF).\n\n"
            "Your expertise:\n"
            "- GES standards, strands, sub-strands, and learning indicators for Basic 7-9 (JHS) "
            "and SHS 1-3\n"
            "- Common reference standards: B7.1.1.1.1 format (Level.Strand.SubStrand.ContentStd.Indicator)\n"
            "- Standards-Based Curriculum (SBC) structure and assessment guidelines\n"
            "- Scheme-of-work verification against official GES syllabi\n"
            "- Content alignment audits (quiz banks, lesson plans, exam preps vs. indicators)\n"
            "- Subject-specific guidance: Mathematics, English Language, Integrated/Social Science, "
            "RME, ICT, French, Ghanaian Language, Creative Arts & Design, Career Technology\n"
            "- BECE exam pattern and weighting analysis\n\n"
            "CRITICAL BEHAVIOUR RULES:\n"
            "1. You have LIVE DATA. Below this prompt you will receive (a) the full BECE syllabus "
            "reference with strand weightings for every subject and (b) a snapshot of the school's "
            "exam bank (question counts by subject, topic, difficulty, format, and DOK level). "
            "USE THIS DATA IMMEDIATELY — do NOT ask the user to upload files, CSVs, or spreadsheets. "
            "The platform already has the data.\n"
            "2. When asked to compare or audit coverage, produce the ACTUAL analysis right away: "
            "tables showing coverage %, gaps, strand mapping, Bloom's distribution. "
            "Do NOT respond with proposals, outlines, or 'here is what I would do' — DO the work.\n"
            "3. If the exam bank snapshot shows 0 questions for a subject, say so and recommend "
            "how many items to create per strand to reach adequate BECE coverage.\n"
            "4. Always cite official GES standard codes (e.g. B7.1.1.1.1).\n"
            "5. Output markdown tables for strand-by-strand comparisons. Include:\n"
            "   - Expected weight (from BECE blueprint) vs. actual item count\n"
            "   - Coverage status: ✅ Adequate, ⚠️ Thin, ❌ Missing\n"
            "   - Bloom's level distribution vs. target\n"
            "   - Specific gaps and recommended new items\n\n"
            "When reviewing content, check indicator codes, strand coverage, Bloom's taxonomy levels, "
            "and flag gaps or misalignments.\n\n"
            "CONVERSATION STYLE:\n"
            "- Be concise and conversational. Lead with the key finding or table, not preambles.\n"
            "- For large audits (multiple subjects), start with one subject or a summary overview, then offer to drill into others.\n"
            "- Keep responses focused — aim for the most actionable output first, then offer to expand.\n"
            "- End with a clear next-step question or offer to go deeper on a specific area."
        ),
    },
    'content': {
        'label': 'Content Creator',
        'icon': 'bi-pen-fill',
        'color': '#F59E0B',
        'tagline': 'Write email campaigns, social posts, blog articles & in-app copy.',
        'system': (
            "You are a senior Content Creator and Copywriter for SchoolPadi, "
            "a school management SaaS platform.\n\n"
            "Your expertise:\n"
            "- Email marketing campaigns (welcome sequences, feature announcements, re-engagement)\n"
            "- Social media copy (Twitter/X, LinkedIn, Instagram, Facebook) optimised for education sector\n"
            "- Blog posts and thought leadership articles on EdTech, school digitisation, GES policy\n"
            "- In-app notification copy, onboarding tooltips, and microcopy\n"
            "- Landing page copy and value propositions\n"
            "- Newsletter content for school administrators\n"
            "- WhatsApp broadcast messages (concise, actionable)\n\n"
            "Brand voice: Warm, confident, and professional but approachable. "
            "Avoid jargon — school admins and teachers are busy people. "
            "Use the brand name 'SchoolPadi' consistently. "
            "When writing emails, include subject line options. "
            "When writing social posts, include hashtag suggestions. "
            "Always adapt tone to the specific channel and audience.\n\n"
            "CONVERSATION STYLE:\n"
            "- Be concise and conversational. Do NOT dump entire campaigns or full content calendars in one message.\n"
            "- For multi-piece requests (e.g. 'write a week of social posts'), write 1-2 samples first and offer to continue.\n"
            "- Keep responses under 300 words unless the user explicitly asks for a full deliverable or says 'give me everything'.\n"
            "- Ask which platform/channel to prioritize if the user's request is broad.\n"
            "- End with a clear next-step question or offer to expand a specific piece."
        ),
    },
}


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def landlord_agents(request):
    """Hub page showing all available landlord AI agents."""
    from .models import LandlordAgentConversation, AgentSharedBrief

    agents_data = []
    for slug, meta in LANDLORD_AGENT_META.items():
        recent = LandlordAgentConversation.objects.filter(
            agent=slug, created_by=request.user,
        )[:3]
        agents_data.append({
            'slug': slug,
            'label': meta['label'],
            'icon': meta['icon'],
            'color': meta['color'],
            'tagline': meta['tagline'],
            'recent_conversations': recent,
            'total': LandlordAgentConversation.objects.filter(
                agent=slug, created_by=request.user,
            ).count(),
        })

    from .models import PromoBanner, PromoBannerEvent
    active_promos = PromoBanner.objects.filter(is_active=True).count()
    promo_impressions = PromoBannerEvent.objects.filter(event_type='impression').count()
    promo_clicks = PromoBannerEvent.objects.filter(event_type='click').count()

    return render(request, 'tenants/landlord_agents.html', {
        'agents': agents_data,
        'brief_count': AgentSharedBrief.objects.filter(created_by=request.user).count(),
        'pinned_brief_count': AgentSharedBrief.objects.filter(created_by=request.user, pinned=True).count(),
        'active_promos': active_promos,
        'promo_impressions': promo_impressions,
        'promo_clicks': promo_clicks,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def landlord_agent_chat(request, agent_slug, conv_id=None):
    """Chat interface for a specific landlord agent."""
    from .models import LandlordAgentConversation, LandlordAgentMessage

    if agent_slug not in LANDLORD_AGENT_META:
        raise Http404('Agent not found')

    meta = LANDLORD_AGENT_META[agent_slug]

    # Load or create conversation
    if conv_id:
        conversation = get_object_or_404(
            LandlordAgentConversation,
            pk=conv_id, agent=agent_slug, created_by=request.user,
        )
    else:
        conversation = None

    # Create new conversation via POST
    if request.method == 'POST' and request.POST.get('action') == 'new':
        conversation = LandlordAgentConversation.objects.create(
            agent=agent_slug,
            title=request.POST.get('title', 'New conversation').strip()[:200],
            created_by=request.user,
        )
        return redirect('tenants:landlord_agent_chat_conv', agent_slug=agent_slug, conv_id=conversation.pk)

    # Delete conversation
    if request.method == 'POST' and request.POST.get('action') == 'delete' and conversation:
        conversation.delete()
        return redirect('tenants:landlord_agent_chat', agent_slug=agent_slug)

    # Rename conversation
    if request.method == 'POST' and request.POST.get('action') == 'rename' and conversation:
        new_title = request.POST.get('title', '').strip()[:200]
        if new_title:
            conversation.title = new_title
            conversation.save()
        return redirect('tenants:landlord_agent_chat_conv', agent_slug=agent_slug, conv_id=conversation.pk)

    # Sidebar conversations (with optional search)
    search_q = request.GET.get('q', '').strip()
    conversations = LandlordAgentConversation.objects.filter(
        agent=agent_slug, created_by=request.user,
    )
    if search_q:
        conversations = conversations.filter(
            models.Q(title__icontains=search_q) |
            models.Q(messages__content__icontains=search_q)
        ).distinct()
    conversations = conversations[:30]

    msgs = list(conversation.messages.all()) if conversation else []

    return render(request, 'tenants/landlord_agent_chat.html', {
        'agent_slug': agent_slug,
        'meta': meta,
        'conversation': conversation,
        'conversations': conversations,
        'messages': msgs,
        'search_q': search_q,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def landlord_agent_api(request, agent_slug):
    """Streaming API endpoint for landlord agent chat."""
    import json as _json
    from django.http import StreamingHttpResponse
    from academics.ai_tutor import (
        get_active_ai_provider, get_active_ai_model,
        _stream_chat_completion_text, _stream_gemini_chat,
        _get_openai_api_key,
    )
    from .models import LandlordAgentConversation, LandlordAgentMessage

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if agent_slug not in LANDLORD_AGENT_META:
        return JsonResponse({'error': 'Unknown agent'}, status=404)

    try:
        body = _json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_msg = (body.get('message') or '').strip()
    conv_id = body.get('conversation_id')

    if not user_msg:
        return JsonResponse({'error': 'Message required'}, status=400)

    meta = LANDLORD_AGENT_META[agent_slug]

    # Resolve or create conversation
    if conv_id:
        try:
            conversation = LandlordAgentConversation.objects.get(
                pk=conv_id, agent=agent_slug, created_by=request.user,
            )
        except LandlordAgentConversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
    else:
        title = user_msg[:80] + ('…' if len(user_msg) > 80 else '')
        conversation = LandlordAgentConversation.objects.create(
            agent=agent_slug, title=title, created_by=request.user,
        )

    # Save user message
    LandlordAgentMessage.objects.create(
        conversation=conversation, role='user', content=user_msg,
    )

    # Build message history (last 20 messages for context)
    history = list(conversation.messages.order_by('created_at')[:20].values('role', 'content'))

    # Inject shared Briefing Room context so agents collaborate
    shared_context = _build_shared_context(request.user, current_agent=agent_slug)
    system_prompt = meta['system'] + shared_context

    # Inject BECE syllabus + exam bank data for Curriculum Analyst
    if agent_slug == 'curriculum':
        from .curriculum_data import build_syllabus_summary_text, build_exam_bank_context
        system_prompt += '\n\n' + build_syllabus_summary_text()
        exam_ctx = build_exam_bank_context()
        if exam_ctx:
            system_prompt += exam_ctx
        else:
            system_prompt += (
                '\n\n=== PLATFORM EXAM BANK DATA ===\n'
                'No questions found in this school\'s exam bank yet. '
                'When asked about coverage, report that the bank is empty and '
                'recommend how many items to create per strand/subject for BECE readiness.'
                '\n=== END EXAM BANK DATA ==='
            )

    api_messages = [{'role': 'system', 'content': system_prompt}]
    for m in history:
        api_messages.append({'role': m['role'], 'content': m['content']})

    provider = get_active_ai_provider(category='general')
    model = get_active_ai_model(category='general')

    payload = {
        'model': model,
        'messages': api_messages,
        'temperature': 0.7,
        'max_tokens': 1200,
        'stream': True,
    }

    collected = []

    def stream():
        try:
            if provider == 'gemini':
                for sse in _stream_gemini_chat(payload, model_override=model):
                    if sse.startswith('data: '):
                        data_str = sse[6:].strip()
                        if data_str != '[DONE]':
                            try:
                                piece = _json.loads(data_str).get('content', '')
                            except _json.JSONDecodeError:
                                piece = ''
                            if piece:
                                collected.append(piece)
                                yield piece
                    elif sse and not sse.startswith(':'):
                        collected.append(sse)
                        yield sse
            else:
                api_key = _get_openai_api_key()
                for chunk in _stream_chat_completion_text(payload, api_key):
                    collected.append(chunk)
                    yield chunk
        except Exception:
            error_msg = 'Sorry, an error occurred generating the response.'
            collected.append(error_msg)
            yield error_msg
        finally:
            # Save assistant response
            full_text = ''.join(collected)
            if full_text.strip():
                LandlordAgentMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=full_text,
                )
                conversation.save()  # bump updated_at

    resp = StreamingHttpResponse(stream(), content_type='text/plain; charset=utf-8')
    resp['X-Conversation-Id'] = str(conversation.pk)
    return resp


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def landlord_agent_export(request, agent_slug, conv_id):
    """Export a conversation as a Markdown text file download."""
    from .models import LandlordAgentConversation

    if agent_slug not in LANDLORD_AGENT_META:
        raise Http404('Agent not found')

    conversation = get_object_or_404(
        LandlordAgentConversation,
        pk=conv_id, agent=agent_slug, created_by=request.user,
    )
    meta = LANDLORD_AGENT_META[agent_slug]
    msgs = conversation.messages.order_by('created_at')

    lines = [
        f'# {conversation.title}',
        f'Agent: {meta["label"]}',
        f'Date: {conversation.created_at.strftime("%Y-%m-%d %H:%M")}',
        '',
        '---',
        '',
    ]
    for m in msgs:
        role = 'You' if m.role == 'user' else meta['label']
        lines.append(f'**{role}** ({m.created_at.strftime("%H:%M")}):')
        lines.append(m.content)
        lines.append('')

    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
    safe_title = conversation.title[:50].replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.md"'
    return response


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def agent_briefing_room(request):
    """Shared Briefing Room — agents share knowledge, decisions and assets here."""
    from .models import AgentSharedBrief, LandlordAgentConversation

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            content_text = request.POST.get('content', '').strip()
            category = request.POST.get('category', 'insight')
            source_agent = request.POST.get('source_agent', 'pmm')
            valid_cats = [c[0] for c in AgentSharedBrief.CATEGORY_CHOICES]
            valid_agents = [a[0] for a in LandlordAgentConversation.AGENT_CHOICES]
            if title and content_text and category in valid_cats and source_agent in valid_agents:
                AgentSharedBrief.objects.create(
                    title=title, content=content_text,
                    category=category, source_agent=source_agent,
                    created_by=request.user,
                )
                messages.success(request, f'Brief "{title}" added to the Briefing Room.')
            else:
                messages.error(request, 'Title, content, category, and source agent are required.')
            return redirect('tenants:agent_briefing_room')

        if action == 'delete':
            brief_id = request.POST.get('brief_id')
            AgentSharedBrief.objects.filter(pk=brief_id).delete()
            messages.success(request, 'Brief removed.')
            return redirect('tenants:agent_briefing_room')

        if action == 'toggle_pin':
            brief_id = request.POST.get('brief_id')
            brief = AgentSharedBrief.objects.filter(pk=brief_id).first()
            if brief:
                brief.pinned = not brief.pinned
                brief.save()
            return redirect('tenants:agent_briefing_room')

    # Filter
    filter_agent = request.GET.get('agent', '')
    filter_cat = request.GET.get('category', '')
    briefs = AgentSharedBrief.objects.all()
    if filter_agent:
        briefs = briefs.filter(source_agent=filter_agent)
    if filter_cat:
        briefs = briefs.filter(category=filter_cat)

    stats = _get_brief_stats(request.user)
    _pulse_meta = [
        ('pmm', 'PMM Agent', 'graph-up', 'pmm', 'violet'),
        ('curriculum', 'Curriculum Agent', 'journal-text', 'curriculum', 'emerald'),
        ('content', 'Content Agent', 'pencil-square', 'content', 'amber'),
    ]
    max_c = max(stats['agent_counts'].values(), default=1) or 1
    agent_pulse = [
        {
            'slug': s, 'label': l, 'icon': ic, 'css': c, 'color': clr,
            'count': stats['agent_counts'].get(s, 0),
            'pct': round(stats['agent_counts'].get(s, 0) / max_c * 100),
        }
        for s, l, ic, c, clr in _pulse_meta
    ]

    return render(request, 'tenants/agent_briefing_room.html', {
        'briefs': briefs[:50],
        'brief_count': AgentSharedBrief.objects.count(),
        'pinned_count': AgentSharedBrief.objects.filter(pinned=True).count(),
        'filter_agent': filter_agent,
        'filter_category': filter_cat,
        'agent_choices': LandlordAgentConversation.AGENT_CHOICES,
        'category_choices': AgentSharedBrief.CATEGORY_CHOICES,
        'agent_meta': LANDLORD_AGENT_META,
        'agent_stats': stats,
        'agent_pulse': agent_pulse,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def agent_share_brief(request, agent_slug):
    """Share an assistant message from a chat to the Briefing Room (AJAX POST)."""
    import json as _json
    from .models import AgentSharedBrief, LandlordAgentConversation, LandlordAgentMessage

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if agent_slug not in LANDLORD_AGENT_META:
        return JsonResponse({'error': 'Unknown agent'}, status=404)

    try:
        body = _json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    message_id = body.get('message_id')
    content_text = (body.get('content') or '').strip()
    title = (body.get('title') or '').strip()[:200]
    category = body.get('category', 'insight')

    if not content_text:
        return JsonResponse({'error': 'Content required'}, status=400)

    if not title:
        title = content_text[:80] + ('…' if len(content_text) > 80 else '')

    conv = None
    if message_id:
        msg = LandlordAgentMessage.objects.filter(pk=message_id).select_related('conversation').first()
        if msg and msg.conversation.created_by == request.user:
            conv = msg.conversation
    if not conv:
        conversation_id = body.get('conversation_id')
        if conversation_id:
            conv = LandlordAgentConversation.objects.filter(
                pk=conversation_id, created_by=request.user
            ).first()

    AgentSharedBrief.objects.create(
        title=title,
        content=content_text,
        category=category,
        source_agent=agent_slug,
        source_conversation=conv,
        created_by=request.user,
    )

    return JsonResponse({'ok': True, 'message': 'Shared to Briefing Room'})


def _build_shared_context(user, current_agent=None):
    """Build a shared context block from the user's recent briefs for agent injection.

    If current_agent is provided, briefs from OTHER agents are prioritised and
    cross-agent collaboration instructions are included.
    """
    from .models import AgentSharedBrief

    briefs = AgentSharedBrief.objects.filter(created_by=user).order_by('-pinned', '-created_at')[:15]
    if not briefs:
        return ''

    lines = [
        '\n\n--- TEAM BRIEFING ROOM (Shared context from all agents) ---',
        'The following briefs were shared by your agent colleagues. '
        'Reference them when relevant to provide coordinated, consistent advice.',
    ]

    if current_agent:
        label = LANDLORD_AGENT_META.get(current_agent, {}).get('label', current_agent)
        lines.append(
            f'You are the {label}. Briefs from other agents are marked with ★. '
            'Prioritise these — they represent decisions and context from your teammates.'
        )

    lines.append('')

    for b in briefs:
        pin_tag = ' [PINNED]' if b.pinned else ''
        cross = ''
        if current_agent and b.source_agent != current_agent:
            cross = ' ★'
        lines.append(
            f'• [{b.get_source_agent_display()}]{pin_tag}{cross} "{b.title}" '
            f'({b.get_category_display()}) — {b.content[:500]}'
        )

    lines.append('')
    lines.append(
        'When your response contains a significant insight, decision, or asset, '
        'note it clearly so the user can share it to the Briefing Room for your colleagues.'
    )
    lines.append('--- END BRIEFING ROOM ---')
    return '\n'.join(lines)


def _get_brief_stats(user):
    """Per-agent brief counts and category breakdown for the Briefing Room dashboard."""
    from .models import AgentSharedBrief
    from django.db.models import Count, Q
    from datetime import timedelta
    from django.utils import timezone

    qs = AgentSharedBrief.objects.filter(created_by=user)
    agent_counts = dict(qs.values_list('source_agent').annotate(c=Count('id')).values_list('source_agent', 'c'))
    cat_counts = dict(qs.values_list('category').annotate(c=Count('id')).values_list('category', 'c'))
    week_ago = timezone.now() - timedelta(days=7)
    recent_count = qs.filter(created_at__gte=week_ago).count()

    return {
        'agent_counts': agent_counts,
        'cat_counts': cat_counts,
        'recent_count': recent_count,
    }


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def agent_send_promo(request, agent_slug):
    """Push a promo banner to tenant dashboards from the agent chat (AJAX POST)."""
    import json as _json
    from .models import PromoBanner

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if agent_slug not in LANDLORD_AGENT_META:
        return JsonResponse({'error': 'Unknown agent'}, status=404)

    try:
        body = _json.loads(request.body)
    except (ValueError, _json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    headline = (body.get('headline') or '').strip()[:120]
    if not headline:
        return JsonResponse({'error': 'Headline is required'}, status=400)

    valid_styles = [c[0] for c in PromoBanner.STYLE_CHOICES]
    valid_audiences = [c[0] for c in PromoBanner.AUDIENCE_CHOICES]

    PromoBanner.objects.create(
        headline=headline,
        body=(body.get('body') or '').strip()[:300],
        cta_text=(body.get('cta_text') or 'Learn More').strip()[:40],
        cta_link=(body.get('cta_link') or '').strip()[:500],
        style=body.get('style', 'gradient') if body.get('style') in valid_styles else 'gradient',
        audience=body.get('audience', 'all') if body.get('audience') in valid_audiences else 'all',
        source_agent=agent_slug,
        created_by=request.user,
    )
    return JsonResponse({'ok': True, 'message': 'Promo banner pushed'})


@login_required
def promo_banner_dismiss(request):
    """AJAX POST — dismiss a promo banner for the current user (persistent)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    import json as _json
    from .models import PromoBanner, PromoBannerDismissal
    try:
        body = _json.loads(request.body)
        banner_id = int(body.get('banner_id', 0))
    except (ValueError, _json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    from django.db import connection as _conn
    _conn.set_schema_to_public()
    try:
        if PromoBanner.objects.filter(pk=banner_id).exists():
            PromoBannerDismissal.objects.get_or_create(
                banner_id=banner_id, user=request.user,
            )
    finally:
        if hasattr(request, 'tenant'):
            _conn.set_tenant(request.tenant)
    return JsonResponse({'ok': True})


@login_required
def promo_banner_track(request):
    """AJAX POST — track impression or click on a promo banner."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    import json as _json
    from .models import PromoBanner, PromoBannerEvent
    try:
        body = _json.loads(request.body)
        banner_id = int(body.get('banner_id', 0))
        event_type = body.get('event_type', '')
    except (ValueError, _json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if event_type not in ('impression', 'click'):
        return JsonResponse({'error': 'Invalid event type'}, status=400)

    schema = ''
    from django.db import connection as _conn
    if hasattr(request, 'tenant'):
        schema = _conn.schema_name
    _conn.set_schema_to_public()
    try:
        if PromoBanner.objects.filter(pk=banner_id).exists():
            PromoBannerEvent.objects.create(
                banner_id=banner_id,
                event_type=event_type,
                user=request.user,
                tenant_schema=schema,
            )
    finally:
        if hasattr(request, 'tenant'):
            _conn.set_tenant(request.tenant)
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def promo_banner_manage(request):
    """Landlord page to list, edit, toggle, and delete promo banners with analytics."""
    from .models import PromoBanner, PromoBannerEvent
    from django.db.models import Count, Q

    if request.method == 'POST':
        action = request.POST.get('action', '')
        banner_id = request.POST.get('banner_id')

        if action == 'toggle' and banner_id:
            b = PromoBanner.objects.filter(pk=banner_id).first()
            if b:
                b.is_active = not b.is_active
                b.save()
                messages.success(request, f'Banner {"activated" if b.is_active else "paused"}.')
            return redirect('tenants:promo_banner_manage')

        if action == 'delete' and banner_id:
            PromoBanner.objects.filter(pk=banner_id).delete()
            messages.success(request, 'Banner deleted.')
            return redirect('tenants:promo_banner_manage')

        if action == 'edit' and banner_id:
            b = PromoBanner.objects.filter(pk=banner_id).first()
            if b:
                b.headline = request.POST.get('headline', b.headline)[:120]
                b.body = request.POST.get('body', b.body)[:300]
                b.cta_text = request.POST.get('cta_text', b.cta_text)[:40]
                b.cta_link = request.POST.get('cta_link', b.cta_link)[:500]
                b.style = request.POST.get('style', b.style)
                b.audience = request.POST.get('audience', b.audience)
                b.save()
                messages.success(request, 'Banner updated.')
            return redirect('tenants:promo_banner_manage')

    banners = PromoBanner.objects.annotate(
        impressions=Count('events', filter=Q(events__event_type='impression')),
        clicks=Count('events', filter=Q(events__event_type='click')),
        dismissals_count=Count('dismissals'),
    ).order_by('-created_at')

    # Summary stats
    total_active = banners.filter(is_active=True).count()
    total_impressions = sum(b.impressions for b in banners)
    total_clicks = sum(b.clicks for b in banners)

    return render(request, 'tenants/promo_banner_manage.html', {
        'banners': banners,
        'total_active': total_active,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'style_choices': PromoBanner.STYLE_CHOICES,
        'audience_choices': PromoBanner.AUDIENCE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def agent_auto_brief(request, agent_slug):
    """Use AI to extract a brief suggestion from an agent response (AJAX POST).

    Accepts: { content: string }
    Returns: { ok: true, suggestion: { title, category, summary, worth_sharing } }
    """
    import json as _json
    from academics.ai_tutor import (
        get_active_ai_provider, get_active_ai_model,
        _get_openai_api_key,
    )

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if agent_slug not in LANDLORD_AGENT_META:
        return JsonResponse({'error': 'Unknown agent'}, status=404)

    try:
        body = _json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = (body.get('content') or '').strip()
    if not content or len(content) < 80:
        return JsonResponse({'ok': True, 'suggestion': None})

    agent_label = LANDLORD_AGENT_META[agent_slug]['label']

    extraction_prompt = (
        "You are a brief-extraction system. Analyze the following AI agent response "
        f"from the \"{agent_label}\" agent and determine if it contains a noteworthy "
        "insight, decision, content asset, data analysis, or request that other team "
        "members should know about.\n\n"
        "Respond with ONLY a JSON object (no markdown, no backticks):\n"
        '{"worth_sharing": true/false, "title": "concise title (max 100 chars)", '
        '"category": "insight|decision|asset|request|data", '
        '"summary": "2-3 sentence distillation of the key takeaway (max 300 chars)"}\n\n'
        "Categories:\n"
        "- insight: A key finding, pattern, or recommendation\n"
        "- decision: A concrete decision or strategy recommendation\n"
        "- asset: A created artifact (email, plan, framework, template)\n"
        "- request: A question or need for input from other agents\n"
        "- data: Numbers, analysis, metrics, or research findings\n\n"
        "Set worth_sharing=false for: simple greetings, clarifying questions, "
        "very short answers, or responses that don't contain actionable knowledge.\n\n"
        f"Agent response:\n{content[:3000]}"
    )

    payload = {
        'model': get_active_ai_model(category='general'),
        'messages': [{'role': 'user', 'content': extraction_prompt}],
        'temperature': 0.2,
        'max_tokens': 300,
        'stream': False,
    }

    try:
        provider = get_active_ai_provider(category='general')
        if provider == 'gemini':
            from academics.ai_tutor import _call_gemini_chat, _extract_assistant_text_from_completion
            raw_resp = _call_gemini_chat(payload)
            raw = _extract_assistant_text_from_completion(raw_resp)
        else:
            from academics.ai_tutor import _post_chat_completion, _extract_assistant_text_from_completion
            api_key = _get_openai_api_key()
            raw_resp = _post_chat_completion(payload, api_key)
            raw = _extract_assistant_text_from_completion(raw_resp)

        if not raw:
            return JsonResponse({'ok': True, 'suggestion': None})

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0]
        cleaned = cleaned.strip()

        suggestion = _json.loads(cleaned)
        if not suggestion.get('worth_sharing'):
            return JsonResponse({'ok': True, 'suggestion': None})

        # Sanitize
        suggestion['title'] = (suggestion.get('title') or '')[:200]
        suggestion['summary'] = (suggestion.get('summary') or '')[:500]
        valid_cats = ['insight', 'decision', 'asset', 'request', 'data']
        if suggestion.get('category') not in valid_cats:
            suggestion['category'] = 'insight'

        return JsonResponse({'ok': True, 'suggestion': suggestion})

    except Exception:
        return JsonResponse({'ok': True, 'suggestion': None})
