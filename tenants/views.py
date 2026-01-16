from django.shortcuts import render, redirect
from django.db import transaction, connection, models
from .forms import SchoolSignupForm, SchoolSetupForm
from .models import School, Domain
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from academics.models import SchoolInfo, AcademicYear, Class, Subject
from django.utils import timezone
from datetime import timedelta

def school_signup(request):
    if request.method == 'POST':
        form = SchoolSignupForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['school_name']
            schema_name = form.cleaned_data['schema_name']
            email = form.cleaned_data['email']
            school_type = form.cleaned_data['school_type']
            address = form.cleaned_data['address']
            phone = form.cleaned_data['phone']
            country = form.cleaned_data['country']
            
            try:
                # 1. Create Tenant (Transaction on PUBLIC schema)
                # We separate the tenant creation from the inner data population to avoid
                # long transactions if migrations take time.
                print(f"DEBUG SIGNUP: Starting creation for {schema_name}")
                
                # REMOVED outer transaction.atomic() here to allow Partial Success (Debugging Timeout)
                # Ideally, we should rollback manually if it fails, but for now we want to see if the record persists.
                
                tenant = School(
                    schema_name=schema_name, 
                    name=name, 
                    school_type=school_type,
                    address=address,
                    phone_number=phone,
                    country=country,
                    on_trial=True, 
                    is_active=True
                )
                # Force auto_create_schema to False initially to save the DB record quickly
                tenant.auto_create_schema = False 
                tenant.save()
                
                print(f"DEBUG SIGNUP: Tenant record saved (No Schema yet)")
                
                domain = Domain()
                domain.domain = f"{schema_name}.local" 
                domain.tenant = tenant
                domain.is_primary = True
                domain.save()
                print(f"DEBUG SIGNUP: Domain saved")
                
                # Now Create Schema Manually (The slow part)
                print(f"DEBUG SIGNUP: Starting Schema Creation (Migrate)...")
                tenant.create_schema(check_if_exists=True, verbosity=1)
                print(f"DEBUG SIGNUP: Schema Created & Migrated")

                # 2. Switch to Tenant Context for Data Population
                # We do this OUTSIDE the first atomic block if we want to risk partial failure
                # but better to keep it atomic if possible. For now, let's keep robust logging.
                
                try:
                    # Inner atomic is fine for data population
                    with transaction.atomic():
                        connection.set_tenant(tenant)
                        User = get_user_model()
                        
                        if not User.objects.filter(username='admin').exists():
                            user = User.objects.create_superuser(
                                username='admin',
                                email=email,
                                password='admin',
                                user_type='admin'
                            )
                            print(f"DEBUG SIGNUP: Admin user created")
                        
                        _create_sample_data(tenant, school_type=school_type, phone=phone, address=address)
                        print(f"DEBUG SIGNUP: Sample data created")
                        
                except Exception as inner_e:
                    print(f"DEBUG SIGNUP ERROR (Inner - Data Pop): {inner_e}")
                    # Don't rollback the Tenant creation itself, just log the data failure
                    # User will have an empty school but at least it exists
                    messages.warning(request, f"School created but sample data failed: {inner_e}")
                
                # Switch back
                print(f"DEBUG SIGNUP: Success. Switching back to Public.")
                connection.set_schema_to_public()

                messages.success(request, f"School '{name}' created successfully! Your login URL is /{schema_name}/login/")
                return render(request, 'tenants/signup_success.html', {'schema_name': schema_name})
                    
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
        'by_type': by_type,
        'recent_schools': recent_schools,
        'signups_chart': signups_chart,
    }
    return render(request, 'tenants/landlord_dashboard.html', context)
