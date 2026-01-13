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
                # 1. Create Tenant (Transaction on PUBLIC schema)
                # We separate the tenant creation from the inner data population to avoid
                # long transactions if migrations take time.
                print(f"DEBUG SIGNUP: Starting creation for {schema_name}")
                with transaction.atomic():
                    tenant = School(schema_name=schema_name, name=name, on_trial=True, is_active=True)
                    # This .save() triggers migrate_schemas which can be SLOW
                    tenant.save()
                    print(f"DEBUG SIGNUP: Tenant saved and migrated")
                    
                    domain = Domain()
                    domain.domain = f"{schema_name}.local" 
                    domain.tenant = tenant
                    domain.is_primary = True
                    domain.save()
                    print(f"DEBUG SIGNUP: Domain saved")

                # 2. Switch to Tenant Context for Data Population
                # We do this OUTSIDE the first atomic block if we want to risk partial failure
                # but better to keep it atomic if possible. For now, let's keep robust logging.
                
                try:
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
                        
                        _create_sample_data(tenant)
                        print(f"DEBUG SIGNUP: Sample data created")
                        
                except Exception as inner_e:
                    print(f"DEBUG SIGNUP ERROR (Inner): {inner_e}")
                    # If data population fails, do we delete the tenant?
                    # Ideally yes, but for diagnosing timeouts, maybe keeping the empty tenant is better?
                    # For now, let's re-raise to trigger the outer rollback.
                    raise inner_e
                
                # Switch back
                print(f"DEBUG SIGNUP: Success. Switching back to Public.")
                connection.set_schema_to_public()

                messages.success(request, f"School '{name}' created successfully! Your login URL is /{schema_name}/login/")
                return render(request, 'tenants/signup_success.html', {'schema_name': schema_name})
                    
            except Exception as e:
                print(f"DEBUG SIGNUP FAILIURE: {e}")
                connection.set_schema_to_public()
                # Generic error message to user, detailed to logs
                messages.error(request, f"Error creating school. Please try again or check logs. ({e})")

                
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
