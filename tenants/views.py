from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, connection, models
from django.db.models import Sum, Avg, Count
from django.contrib.auth.decorators import user_passes_test
from .forms import SchoolSignupForm, SchoolSetupForm, SchoolApprovalForm
from .models import School, Domain
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from academics.models import SchoolInfo, AcademicYear, Class, Subject
from django.utils import timezone
from datetime import timedelta
from .email_notifications import send_submission_confirmation, send_approval_notification

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
                print(f"DEBUG SIGNUP: Starting creation for {schema_name}")
                
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
                
                print(f"DEBUG SIGNUP: Tenant record saved (Pending approval)")
                
                domain = Domain()
                domain.domain = f"{schema_name}.local" 
                domain.tenant = tenant
                domain.is_primary = True
                domain.save()
                print(f"DEBUG SIGNUP: Domain saved")
                
                # Send submission confirmation email
                send_submission_confirmation(tenant)

                messages.success(request, f"Application submitted successfully! Your school '{name}' is pending admin approval. You will be notified at {contact_person_email} once approved.")
                return render(request, 'tenants/signup_success.html', {
                    'schema_name': schema_name,
                    'pending_approval': True,
                    'school_name': name
                })
                    
            except Exception as e:
                print(f"DEBUG SIGNUP CRITICAL FAILURE: {e}")
                connection.set_schema_to_public()
                
                # Try to clean up orphan tenant if schemas failed?
                # For debugging: LEAVE IT.
                
                messages.error(request, f"Error creating school. Please try again or check logs. ({e})")


                
    else:
        form = SchoolSignupForm()
    
    return render(request, 'tenants/signup.html', {'form': form})


def _create_sample_data(tenant, school_type='basic', phone='', address=''):
    """Auto-populate new tenant with sample academic data"""
    # Academic Year
    current_year = timezone.now().year
    academic_year, _ = AcademicYear.objects.get_or_create(
        name=f'{current_year}/{current_year + 1}',
        defaults={
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=365),
            'is_current': True
        }
    )
    
    # Sample Classes based on School Type
    classes = []
    if school_type == 'primary':
        classes = [f'Class {i}' for i in range(1, 7)]
    elif school_type == 'jhs':
        classes = ['JHS 1', 'JHS 2', 'JHS 3']
    elif school_type == 'shs':
        classes = ['SHS 1', 'SHS 2', 'SHS 3']
    elif school_type == 'basic':
        classes = ['Kindergarten 1', 'Kindergarten 2'] + [f'Class {i}' for i in range(1, 7)] + ['JHS 1', 'JHS 2', 'JHS 3']
    else:
        classes = ['Class 1', 'Class 2', 'Class 3'] # Fallback
        
    for class_name in classes:
        Class.objects.get_or_create(
            name=class_name,
            academic_year=academic_year
        )
    
    # Sample Subjects
    subjects = [
        ('Mathematics', 'MAT'),
        ('English Language', 'ENG'),
        ('Integrated Science', 'SCI'),
        ('Social Studies', 'SOC'),
        ('Computing', 'COM'),
        ('French', 'FRE'),
        ('Religious & Moral Education', 'RME'),
        ('Creative Arts', 'CRA'),
        ('Career Technology', 'CAR')
    ]
    for subject_name, code in subjects:
        Subject.objects.get_or_create(
            name=subject_name,
            defaults={'code': code}
        )
    
    # School Info - Populate with data from Signup
    if not SchoolInfo.objects.exists():
        SchoolInfo.objects.create(
            name=tenant.name,
            address=address or "To be configured",
            phone=phone or "To be configured",
            email="info@school.edu",
            motto="Excellence in Education",
            primary_color="#026e56",
            secondary_color="#0f3b57"
        )
    else:
        # Update existing record
        info = SchoolInfo.objects.first()
        info.name = tenant.name
        if address: info.address = address
        if phone: info.phone = phone
        info.save()


@login_required
def school_setup_wizard(request):
    """Initial setup wizard for configuring school information"""
    # Ensure user is on a tenant schema (not public)
    if hasattr(request, 'tenant') and request.tenant.schema_name == 'public':
        messages.error(request, "This page is only accessible from school portals.")
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
            
            # If approved, create schema and setup
            if school.approval_status == 'approved' and not school.is_active:
                try:
                    # Create schema
                    school.auto_create_schema = True
                    school.is_active = True
                    school.save()
                    school.create_schema(check_if_exists=True, verbosity=1)
                    
                    # Switch to tenant and create admin user + sample data
                    connection.set_tenant(school)
                    User = get_user_model()
                    
                    if not User.objects.filter(username='admin').exists():
                        temp_email = school.contact_person_email or 'admin@example.com'
                        admin_user = User.objects.create_superuser(
                            username='admin',
                            email=temp_email,
                            password='admin',
                            user_type='admin'
                        )
                    
                    _create_sample_data(school, 
                                       school_type=school.school_type,
                                       phone=school.phone_number,
                                       address=school.address)
                    
                    connection.set_schema_to_public()
                    
                    # Send approval email notification
                    send_approval_notification(school, status_changed_by=request.user)
                    
                    messages.success(request, f"School '{school.name}' approved and activated! Schema created with sample data. Notification email sent.")
                    
                except Exception as e:
                    connection.set_schema_to_public()
                    messages.error(request, f"Approval saved but schema creation failed: {e}")
                    school.approval_status = 'requires_info'
                    school.admin_notes = f"Schema creation error: {e}"
                    school.save()
                    # Send requires_info notification
                    send_approval_notification(school, status_changed_by=request.user)
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
    thirty_days_ago = timezone.now() - timedelta(days=30)
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
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_mrr = (
        SchoolSubscription.objects
        .filter(created_at__gte=six_months_ago, status__in=['active', 'trial'])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(mrr_sum=Sum('mrr'))
        .order_by('month')
    )
    
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
        'monthly_mrr': list(monthly_mrr),
        
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
    }
    
    return render(request, 'tenants/revenue_analytics.html', context)


@login_required
def addon_marketplace(request):
    """Add-on marketplace for school admins"""
    from .models import AddOn, SchoolSubscription, SchoolAddOn
    
    # Get school's subscription
    try:
        if hasattr(request, 'tenant') and request.tenant.schema_name != 'public':
            subscription = SchoolSubscription.objects.get(school=request.tenant)
        else:
            messages.error(request, "Marketplace only available for school tenants")
            return redirect('home')
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
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
        addons_by_category[category].append(addon)
    
    context = {
        'subscription': subscription,
        'addons_by_category': addons_by_category,
        'total_addon_cost': sum(
            addon.monthly_price 
            for addon in available_addons 
            if addon.id in purchased_addon_ids and not addon.is_one_time
        ),
    }
    
    return render(request, 'tenants/addon_marketplace.html', context)


@login_required
def purchase_addon(request, addon_id):
    """Purchase an add-on"""
    from .models import AddOn, SchoolSubscription, SchoolAddOn
    
    if request.method != 'POST':
        return redirect('tenants:addon_marketplace')
    
    # Get subscription
    try:
        subscription = SchoolSubscription.objects.get(school=request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
        return redirect('dashboard')
    
    # Get add-on
    addon = get_object_or_404(AddOn, id=addon_id, is_active=True)
    
    # Check if already purchased
    if SchoolAddOn.objects.filter(subscription=subscription, addon=addon, is_active=True).exists():
        messages.warning(request, f"You already have {addon.name}")
        return redirect('tenants:addon_marketplace')
    
    # Create purchase
    school_addon = SchoolAddOn.objects.create(
        subscription=subscription,
        addon=addon,
        is_active=True
    )
    
    # Recalculate MRR
    subscription.calculate_mrr()
    
    messages.success(request, f"Successfully purchased {addon.name}! Your billing has been updated.")
    return redirect('tenants:addon_marketplace')


@login_required
def cancel_addon(request, addon_id):
    """Cancel an add-on subscription"""
    from .models import SchoolSubscription, SchoolAddOn
    
    if request.method != 'POST':
        return redirect('tenants:addon_marketplace')
    
    # Get subscription
    try:
        subscription = SchoolSubscription.objects.get(school=request.tenant)
    except SchoolSubscription.DoesNotExist:
        messages.error(request, "No active subscription found")
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
            school_id = request.POST.get('school_id')
            backup_type = request.POST.get('backup_type', 'full')
            
            school = None
            if school_id:
                school = School.objects.get(id=school_id)
            
            backup = DatabaseBackup.objects.create(
                school=school,
                backup_type=backup_type,
                status='pending',
            )
            
            # TODO: Trigger actual backup process (Celery task, Cloud Function, etc.)
            
            messages.success(request, f"Backup initiated: {backup.id}")
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
