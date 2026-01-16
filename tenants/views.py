from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, connection, models
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
                
                status_msg = dict(School.APPROVAL_STATUS_CHOICES).get(school.approval_status, school.approval_status)
                messages.success(request, f"School status updated to: {status_msg}. Notification email sent.")
            
            return redirect('tenants:approval_queue')
    else:
        form = SchoolApprovalForm(instance=school)
    
    context = {
        'school': school,
        'form': form,
    }
    return render(request, 'tenants/review_school.html', context)

