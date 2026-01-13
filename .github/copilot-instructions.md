# Copilot Instructions for School Management System

## Project Overview
- **Type**: Django 5 Multi-Tenant SaaS School Management System
- **Stack**: Django 5, django-tenants 3.6, PostgreSQL (Neon Console), Bootstrap 5, WhiteNoise, Cloudinary (prod)
- **Architecture**: Path-based multi-tenancy (`/school1/`, `/school2/`) with shared public schema
- **Core Apps** (Tenant-isolated):
  - `accounts`: Custom User model, Auth & Role-based Dashboards
  - `academics`: Years, Classes, Subjects, Timetable, School Info, Activities
  - `students`: Profiles, Attendance, Grades (with auto-calculation)
  - `teachers`: Profiles, Duty Roster, Lesson Plans
  - `finance`: FeeHead, FeeStructure, StudentFee, Payment tracking
  - `announcements`: Notifications with context processor
  - `parents`: Parent portal
  - `tenants`: School (TenantMixin), Domain, Custom Middleware
- **Inactive Apps**: `communication` (files exist but not in INSTALLED_APPS)

## Multi-Tenancy Architecture
- **Django-Tenants Integration**: Uses `django_tenants.postgresql_backend` engine. **SQLite NOT supported**—PostgreSQL required locally and in production.
- **Custom Middleware**: `tenants.middleware.TenantPathMiddleware` (replaces default subdomain routing):
  - Parses first URL segment as `schema_name` (e.g., `/school1/dashboard/` → tenant with `schema_name='school1'`)
  - Sets `request.tenant` and switches PostgreSQL schema via `connection.set_tenant()`
  - Modifies `request.META['SCRIPT_NAME']` and `request.path_info` for proper URL reversing
  - Public schema (`/signup/`, `/login/`) served when no tenant match found
- **SHARED_APPS vs TENANT_APPS**: Defined in [school_system/settings.py](school_system/settings.py#L36-L75). Tenants get isolated data for students, grades, etc. Admin and accounts exist in both contexts.
- **Schema Management**: 
  - `python manage.py migrate_schemas --shared` for public schema
  - `python manage.py migrate_schemas` for all tenants
  - New schools auto-create schemas when saved (if `auto_create_schema = True`)

## Authentication & Authorization
- **Custom User Model**: `accounts.models.User` (extends AbstractUser) with `user_type` CharField: `('admin', 'teacher', 'student', 'parent')`
- **Access Control Pattern**:
  ```python
  @login_required
  def view(request):
      if request.user.user_type != 'teacher':
          messages.error(request, "Access denied")
          return redirect('dashboard')
  ```
  - Used extensively in [teachers/views.py](teachers/views.py), [students/views.py](students/views.py), etc.
- **Dashboard Routing**: `accounts.views.dashboard` redirects to role-specific templates: `dashboard/admin_dashboard.html`, `dashboard/teacher_dashboard.html`, etc.

## Critical Data Patterns & Gotchas
- **Term Field Inconsistency** ⚠️:
  - `students.Grade.term` and `finance.FeeStructure.term`: lowercase `('first', 'second', 'third')`
  - `teachers.DutyWeek.term`: Capitalized `('First', 'Second', 'Third')`
  - **Always inspect model choices** before filtering: `.filter(term='first')` vs `.filter(term='First')`
- **Academic Year Filtering**: Always scope queries to current year:
  ```python
  current_year = AcademicYear.objects.filter(is_current=True).first()
  classes = Class.objects.filter(academic_year=current_year)
  ```
- **Student Query Optimization**: Use `select_related('user', 'current_class')` to avoid N+1 queries
- **Finance Logic**:
  - `FeeStructure`: Template/definition per Class/Term/Year
  - `StudentFee`: Assigned to individual student (allows adjustments for scholarships)
  - `Payment`: Records transactions; auto-updates `StudentFee.status` on save
  - Status flow: `unpaid` → `partial` → `paid` (calculated via `total_paid` property)

## Key Developer Workflows
### Initial Setup (Local Dev)
1. **Database**: Must use PostgreSQL (Neon or Local). Update [school_system/settings.py](school_system/settings.py#L136-L151) or set `DATABASE_URL`.
   ```python
   # Example for Local usage if not using DATABASE_URL env var
   DATABASES = {
       'default': {
           'ENGINE': 'django_tenants.postgresql_backend',
           'NAME': 'school_db_local',
           'USER': 'postgres',
           'PASSWORD': 'password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```
2. **Migrations**:
   ```bash
   python manage.py migrate_schemas --shared  # Create public schema
   python manage.py migrate_schemas           # Migrate all tenants
   ```
3. **Create Superuser**: Use [scripts/create_superuser.py](scripts/create_superuser.py) (handles `django.setup()`)
4. **Seed Data**: Run `python load_sample_data.py` to populate full test environment:
   - Creates `SchoolInfo`, `AcademicYear` (2025-2026, `is_current=True`)
   - Users (admin, teachers, students, parents) with profiles
   - Classes (Basic 7, 8, 9), Subjects, `ClassSubject` assignments
   - Sample Grades, Fees, Timetable entries
5. **Create New School Tenant**: Use [scripts/setup_tenants.py](scripts/setup_tenants.py) or `tenants.views.school_signup`

### Running Scripts
- **Standalone Scripts**: All scripts in `scripts/` include:
  ```python
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
  django.setup()
  ```
  Run directly: `python scripts/import_basic7.py`
- **Data Import Examples**: `import_basic7.py`, `import_basic8.py`, `import_subject_teachers.py` (CSV → Models)

### Development Server
```bash
python manage.py runserver  # Defaults to 127.0.0.1:8000
```
Access tenant: `http://localhost:8000/school1/dashboard/`
Public site: `http://localhost:8000/`

## Context Processors (Template Globals)
- **`academics.context_processors.school_info`**: Injects `school_name`, `school_logo`, `school_motto`, etc. into all templates. Falls back to `request.tenant.name` if `SchoolInfo` object doesn't exist yet.
- **`announcements.context_processors.user_notifications`**: Adds unread notifications for authenticated users.

## Forms & UI
- **Crispy Forms**: All forms use `crispy_forms` with Bootstrap 5 theme (`CRISPY_TEMPLATE_PACK = 'bootstrap5'`)
- **Example**:
  ```python
  from crispy_forms.helper import FormHelper
  from crispy_forms.layout import Submit
  
  self.helper = FormHelper()
  self.helper.add_input(Submit('submit', 'Save'))
  ```
- **Static Assets**:
  - Dev: Served from `static/` and `STATICFILES_DIRS`
  - Prod: WhiteNoise with `CompressedStaticFilesStorage`
  - Media: Local `media/` (dev), Cloudinary (prod when `VERCEL=1`)

## Common Patterns
- **Filtering by Tenant**: Done automatically via django-tenants schema routing. Models in TENANT_APPS are isolated per school.
- **Marking Attendance**: `students.models.Attendance` with `unique_together = ['student', 'date']`
- **Grade Auto-Calculation**: `students.models.Grade.save()` computes `total_score` (class_score + exams_score), assigns grade/remarks
- **Fee Assignment**: Bulk assign via `finance.views` creates `StudentFee` records from `FeeStructure` templates

## Important Files
- **Settings**: [school_system/settings.py](school_system/settings.py) - Tenancy config, DB, middleware order
- **Custom Middleware**: [tenants/middleware.py](tenants/middleware.py) - Path-based tenant detection
- **Tenant Models**: [tenants/models.py](tenants/models.py) - `School`, `Domain`
- **User Model**: [accounts/models.py](accounts/models.py) - Custom User with `user_type`
- **Main Routing**: [school_system/urls.py](school_system/urls.py) - Includes all app URLs
- **Data Loaders**: [load_sample_data.py](load_sample_data.py), [scripts/](scripts/)

## Production Notes
- **Deployment**: Configured for Neon (Database) and Vercel/Railway (App) with Cloudinary (media)
- **Required Env Vars**: `DATABASE_URL` (Neon Connection String), `SECRET_KEY`, `DEBUG=False`, `CLOUDINARY_*` for media
- **CSRF**: Update `CSRF_TRUSTED_ORIGINS` in settings for new domains
