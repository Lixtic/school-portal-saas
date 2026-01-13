from django.shortcuts import render, redirect
from django.db import transaction, connection
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
            
            try:
                with transaction.atomic():
                    # 1. Create Tenant
                    tenant = School(schema_name=schema_name, name=name, on_trial=True, is_active=True)
                    tenant.save()
                    
                    # 2. Create Domain (required for routing)
                    # For path-strategy, we normally dummy this or reuse localhost with different schema? 
                    # TenantSyncRouter usually needs a domain entry.
                    # We will create a pseudo-domain 'school.localhost' just to satisfy the model constraints
                    # even if we use path-routing.
                    
                    domain = Domain()
                    # In production we might not use this field for routing, but DB needs it
                    domain.domain = f"{schema_name}.local" 
                    domain.tenant = tenant
                    domain.is_primary = True
                    domain.save()
                    
                    # 3. Create Admin User (Switch to new schema)
                    connection.set_tenant(tenant)
                    User = get_user_model()
                    
                    # Check if user already exists
                    if not User.objects.filter(username='admin').exists():
                        user = User.objects.create_superuser(
                            username='admin',
                            email=email,
                            password='admin', # Hardcoded for now, user should change
                            user_type='admin'
                        )
                        print(f"DEBUG: Created admin user for {schema_name}")
                    else:
                        print(f"DEBUG: Admin user already exists for {schema_name}")
                    
                    # Auto-populate sample data
                    _create_sample_data(tenant)
                    
                    # Switch back
                    public_schema = getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public')
                    try:
                        public = School.objects.get(schema_name=public_schema)
                        connection.set_tenant(public)
                    except:
                        connection.set_schema_to_public()

                    messages.success(request, f"School '{name}' created successfully! Your login URL is /{schema_name}/login/")
                    return render(request, 'tenants/signup_success.html', {'schema_name': schema_name})
                    
            except Exception as e:
                # Switch back on error
                connection.set_schema_to_public()
                messages.error(request, f"Error creating school: {e}")
                
    else:
        form = SchoolSignupForm()
    
    return render(request, 'tenants/signup.html', {'form': form})


def _create_sample_data(tenant):
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
    
    # Sample Classes
    classes = ['Basic 7', 'Basic 8', 'Basic 9']
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
    
    # School Info placeholder (Essential for branding)
    # Ensure this is created so the new tenant has their name on the dashboard immediately.
    if not SchoolInfo.objects.exists():
        SchoolInfo.objects.create(
            name=tenant.name,
            address="To be configured",
            phone="To be configured",
            email="info@school.edu",
            motto="Excellence in Education",
            primary_color="#026e56", # Default Teal
            secondary_color="#0f3b57" # Default Dark Blue
        )
    else:
        # Update existing record if it was auto-created by migration (unlikely but safe)
        info = SchoolInfo.objects.first()
        info.name = tenant.name
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
    if school_info and school_info.address != "To be configured":
        # Already setup, redirect to dashboard with proper tenant prefix
        dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
        return redirect(dashboard_url)
    
    if request.method == 'POST':
        form = SchoolSetupForm(request.POST, request.FILES, instance=school_info)
        if form.is_valid():
            school_info = form.save()
            messages.success(request, "School setup completed successfully!")
            # Redirect with tenant prefix
            dashboard_url = request.META.get('SCRIPT_NAME', '') + '/dashboard/'
            return redirect(dashboard_url)
    else:
        form = SchoolSetupForm(instance=school_info)
    
    return render(request, 'tenants/setup_wizard.html', {'form': form})
