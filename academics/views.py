from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tenants.decorators import require_addon
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse, HttpResponseNotAllowed
from django.urls import reverse
import datetime
import json
import re
import os
import io
import base64
from huggingface_hub import InferenceClient
from django.db import connection, ProgrammingError
from django.db.models import Q, Count, Max
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
from accounts.models import User
from announcements.models import Announcement
from .models import Activity, GalleryImage, SchoolInfo, Class, Timetable, ClassSubject, Resource, AcademicYear, Subject, AdmissionApplication
from students.models import Student, Attendance, Grade
from .forms import SchoolInfoForm, GalleryImageForm, ResourceForm, ClassForm, SubjectForm, ClassSubjectForm, BulkClassForm, AcademicYearForm
from teachers.models import Teacher

def about_us(request):
    """Public about us page"""
    school_info = SchoolInfo.objects.first()
    
    activities = []
    try:
        activities = Activity.objects.filter(is_active=True).order_by('-date')[:5]
    except Exception:
        pass  # Table doesn't exist
    
    context = {
        'school_info': school_info,
        'recent_activities': activities,
    }
    return render(request, 'academics/about_us.html', context)

def system_about(request):
    """About the School Portal SaaS system"""
    return render(request, 'academics/system_about.html')

def apply_admission(request):
    """Public admission application page — saves form to AdmissionApplication."""
    school_info = SchoolInfo.objects.first()

    if request.method == 'POST':
        p = request.POST
        required = ['first_name', 'last_name', 'date_of_birth', 'gender', 'grade',
                    'parent_name', 'relationship', 'phone', 'email', 'address']
        missing = [f for f in required if not p.get(f, '').strip()]
        if missing:
            messages.error(request, 'Please fill in all required fields.')
        else:
            AdmissionApplication.objects.create(
                first_name=p['first_name'].strip(),
                last_name=p['last_name'].strip(),
                date_of_birth=p['date_of_birth'],
                gender=p['gender'],
                grade=p['grade'],
                parent_name=p['parent_name'].strip(),
                relationship=p['relationship'],
                phone=p['phone'].strip(),
                email=p['email'].strip(),
                address=p['address'].strip(),
                previous_school=p.get('previous_school', '').strip(),
                comments=p.get('comments', '').strip(),
            )
            messages.success(request, 'Application submitted! Our admissions team will contact you within 3–5 business days.')
            return redirect('academics:apply_admission')

    context = {'school_info': school_info}
    return render(request, 'academics/apply_admission.html', context)


@login_required
def admission_applications(request):
    """Admin view — list all admission applications with filtering."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    status_filter = request.GET.get('status', '')
    qs = AdmissionApplication.objects.all()
    if status_filter:
        qs = qs.filter(status=status_filter)

    context = {
        'applications': qs,
        'status_filter': status_filter,
        'status_choices': AdmissionApplication.STATUS_CHOICES,
        'counts': {
            'all':       AdmissionApplication.objects.count(),
            'pending':   AdmissionApplication.objects.filter(status='pending').count(),
            'reviewing': AdmissionApplication.objects.filter(status='reviewing').count(),
            'accepted':  AdmissionApplication.objects.filter(status='accepted').count(),
            'rejected':  AdmissionApplication.objects.filter(status='rejected').count(),
        },
    }
    return render(request, 'academics/admission_applications.html', context)


@login_required
def admission_application_detail(request, pk):
    """Admin view — review and update a single application."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    app = get_object_or_404(AdmissionApplication, pk=pk)

    if request.method == 'POST':
        new_status  = request.POST.get('status', app.status)
        admin_notes = request.POST.get('admin_notes', app.admin_notes)
        if new_status in dict(AdmissionApplication.STATUS_CHOICES):
            app.status      = new_status
            app.admin_notes = admin_notes
            app.save(update_fields=['status', 'admin_notes', 'updated_at'])
            messages.success(request, f'Application updated to "{app.get_status_display()}".')
        return redirect('academics:admission_application_detail', pk=pk)

    return render(request, 'academics/admission_application_detail.html', {'app': app})

@login_required
def manage_classes(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Filter by academic year if specified
    year_filter = request.GET.get('year', '')
    classes_qs = Class.objects.select_related('academic_year', 'class_teacher', 'class_teacher__user').annotate(
        student_count=Count('student', distinct=True),
        subject_count=Count('classsubject', distinct=True),
    )
    if year_filter:
        classes_qs = classes_qs.filter(academic_year_id=year_filter)
    elif current_year:
        classes_qs = classes_qs.filter(academic_year=current_year)
    
    classes = classes_qs.order_by('name')
    academic_years = AcademicYear.objects.order_by('-start_date')
    
    # Stats
    total_classes = classes.count()
    assigned_count = classes.filter(class_teacher__isnull=False).count()
    total_students = sum(c.student_count for c in classes)
    
    context = {
        'classes': classes,
        'current_year': current_year,
        'academic_years': academic_years,
        'year_filter': int(year_filter) if year_filter else (current_year.id if current_year else ''),
        'total_classes': total_classes,
        'assigned_count': assigned_count,
        'unassigned_count': total_classes - assigned_count,
        'total_students': total_students,
    }
    return render(request, 'academics/manage_classes.html', context)


@login_required
def add_class(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Class "{form.cleaned_data["name"]}" created successfully.')
            return redirect('academics:manage_classes')
    else:
        form = ClassForm()
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            form.fields['academic_year'].initial = current_year.id
    
    return render(request, 'academics/class_form.html', {'form': form, 'title': 'Add Class'})


@login_required
def edit_class(request, class_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    cls = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=cls)
        if form.is_valid():
            form.save()
            messages.success(request, f'Class "{cls.name}" updated successfully.')
            return redirect('academics:manage_classes')
    else:
        form = ClassForm(instance=cls)
    
    return render(request, 'academics/class_form.html', {'form': form, 'title': f'Edit Class: {cls.name}', 'editing': True})


@login_required
def delete_class(request, class_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    cls = get_object_or_404(Class, id=class_id)
    student_count = Student.objects.filter(current_class=cls).count()
    
    if request.method == 'POST':
        if student_count > 0:
            messages.error(request, f'Cannot delete "{cls.name}" — it has {student_count} student(s) assigned. Reassign them first.')
        else:
            name = cls.name
            cls.delete()
            messages.success(request, f'Class "{name}" deleted.')
        return redirect('academics:manage_classes')
    
    return render(request, 'academics/confirm_delete.html', {
        'object': cls,
        'object_type': 'Class',
        'warning': f'This class has {student_count} student(s) assigned.' if student_count else None,
        'can_delete': student_count == 0,
        'cancel_url': reverse('academics:manage_classes'),
    })


@login_required
def bulk_add_classes(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BulkClassForm(request.POST)
        if form.is_valid():
            level = form.cleaned_data['level']
            sections = [s.strip().upper() for s in form.cleaned_data['sections'].split(',') if s.strip()]
            academic_year = form.cleaned_data['academic_year']
            
            # Determine class names based on level
            if level == 'KG':
                base_names = [f'KG {i}' for i in range(1, 3)]
            elif level == 'Primary':
                base_names = [f'Primary {i}' for i in range(1, 7)]
            elif level == 'JHS':
                base_names = [f'JHS {i}' for i in range(1, 4)]
            else:
                messages.error(request, 'Invalid level selected.')
                return redirect('academics:manage_classes')
            
            created_count = 0
            skipped_count = 0
            if sections:
                for base in base_names:
                    for sec in sections:
                        name = f'{base}{sec}'
                        _, created = Class.objects.get_or_create(
                            name=name, academic_year=academic_year
                        )
                        if created:
                            created_count += 1
                        else:
                            skipped_count += 1
            else:
                for base in base_names:
                    _, created = Class.objects.get_or_create(
                        name=base, academic_year=academic_year
                    )
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1
            
            msg = f'{created_count} class(es) created.'
            if skipped_count:
                msg += f' {skipped_count} already existed (skipped).'
            messages.success(request, msg)
            return redirect('academics:manage_classes')
    else:
        form = BulkClassForm()
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            form.fields['academic_year'].initial = current_year.id
    
    return render(request, 'academics/bulk_add_classes.html', {'form': form})


# ─── Subject CRUD ─────────────────────────────────────────────
@login_required
def manage_subjects(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    subjects = Subject.objects.annotate(
        class_count=Count('classsubject', distinct=True),
        teacher_count=Count('classsubject__teacher', distinct=True),
    ).order_by('name')
    
    return render(request, 'academics/manage_subjects.html', {'subjects': subjects})


@login_required
def bulk_add_subjects(request):
    """Accept a textarea of lines (Name, CODE) and create subjects in bulk."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('academics:manage_subjects')

    raw = request.POST.get('lines', '')
    created_count = 0
    skipped_count = 0
    error_lines = []

    for lineno, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Accept: "Name, CODE"  |  "Name | CODE"  |  "Name" (auto code)
        if ',' in line:
            parts = [p.strip() for p in line.split(',', 1)]
        elif '|' in line:
            parts = [p.strip() for p in line.split('|', 1)]
        else:
            parts = [line.strip()]

        name = parts[0]
        if not name:
            error_lines.append(f'Line {lineno}: empty name')
            continue

        if len(parts) >= 2 and parts[1]:
            code = parts[1].upper()[:20]
        else:
            # Auto-generate a code from the first letters of each word, max 6 chars
            words = name.split()
            if len(words) == 1:
                code = name[:6].upper()
            else:
                code = ''.join(w[0] for w in words)[:6].upper()

        # Ensure code uniqueness by appending a number if needed
        base_code = code
        suffix = 1
        while suffix < 100:
            exists = Subject.objects.filter(code=code).first()
            if not exists:
                break
            if exists.name.lower() == name.lower():
                # Exact duplicate — skip it
                code = None
                break
            code = f'{base_code}{suffix}'
            suffix += 1

        if code is None:
            skipped_count += 1
            continue

        _, created = Subject.objects.get_or_create(
            name__iexact=name,
            defaults={'name': name, 'code': code},
        )
        if created:
            created_count += 1
        else:
            skipped_count += 1

    parts_msg = []
    if created_count:
        parts_msg.append(f'{created_count} subject{"s" if created_count != 1 else ""} created')
    if skipped_count:
        parts_msg.append(f'{skipped_count} already existed (skipped)')
    if error_lines:
        parts_msg.append(f'{len(error_lines)} line{"s" if len(error_lines) != 1 else ""} had errors')

    if created_count:
        messages.success(request, '. '.join(parts_msg) + '.')
    elif skipped_count and not error_lines:
        messages.info(request, 'All subjects already exist — nothing new to create.')
    else:
        messages.warning(request, '. '.join(parts_msg) + '.' if parts_msg else 'No valid subjects found.')

    return redirect('academics:manage_subjects')


@login_required
def add_subject(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{form.cleaned_data["name"]}" created.')
            return redirect('academics:manage_subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'academics/subject_form.html', {'form': form, 'title': 'Add Subject'})


@login_required
def edit_subject(request, subject_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{subject.name}" updated.')
            return redirect('academics:manage_subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'academics/subject_form.html', {'form': form, 'title': f'Edit Subject: {subject.name}', 'editing': True})


@login_required
def delete_subject(request, subject_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    usage_count = ClassSubject.objects.filter(subject=subject).count()
    
    if request.method == 'POST':
        if usage_count > 0:
            messages.error(request, f'Cannot delete "{subject.name}" — it is assigned to {usage_count} class(es). Remove assignments first.')
        else:
            name = subject.name
            subject.delete()
            messages.success(request, f'Subject "{name}" deleted.')
        return redirect('academics:manage_subjects')
    
    return render(request, 'academics/confirm_delete.html', {
        'object': subject,
        'object_type': 'Subject',
        'warning': f'This subject is assigned to {usage_count} class(es).' if usage_count else None,
        'can_delete': usage_count == 0,
        'cancel_url': reverse('academics:manage_subjects'),
    })


# ─── Class-Subject Management ────────────────────────────────
@login_required
def manage_class_subjects(request, class_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    cls = get_object_or_404(Class.objects.select_related('academic_year', 'class_teacher', 'class_teacher__user'), id=class_id)
    class_subjects = ClassSubject.objects.filter(class_name=cls).select_related('subject', 'teacher', 'teacher__user').order_by('subject__name')
    
    # Subjects not yet assigned to this class
    assigned_subject_ids = class_subjects.values_list('subject_id', flat=True)
    available_subjects = Subject.objects.exclude(id__in=assigned_subject_ids).order_by('name')
    teachers = Teacher.objects.select_related('user').order_by('user__first_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            subject_id = request.POST.get('subject_id')
            teacher_id = request.POST.get('teacher_id') or None
            if subject_id:
                subject = get_object_or_404(Subject, id=subject_id)
                teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id else None
                _, created = ClassSubject.objects.get_or_create(
                    class_name=cls, subject=subject,
                    defaults={'teacher': teacher}
                )
                if created:
                    messages.success(request, f'Added {subject.name} to {cls.name}.')
                else:
                    messages.info(request, f'{subject.name} is already assigned to {cls.name}.')
        
        elif action == 'update_teacher':
            cs_id = request.POST.get('cs_id')
            teacher_id = request.POST.get('teacher_id') or None
            cs = get_object_or_404(ClassSubject, id=cs_id, class_name=cls)
            cs.teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id else None
            cs.save()
            messages.success(request, f'Teacher updated for {cs.subject.name}.')
        
        elif action == 'remove':
            cs_id = request.POST.get('cs_id')
            cs = get_object_or_404(ClassSubject, id=cs_id, class_name=cls)
            subject_name = cs.subject.name
            cs.delete()
            messages.success(request, f'Removed {subject_name} from {cls.name}.')
        
        return redirect('academics:manage_class_subjects', class_id=cls.id)
    
    context = {
        'cls': cls,
        'class_subjects': class_subjects,
        'available_subjects': available_subjects,
        'teachers': teachers,
    }
    return render(request, 'academics/manage_class_subjects.html', context)


# ─── Academic Year Management ─────────────────────────────────
@login_required
def manage_academic_years(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    years = AcademicYear.objects.annotate(
        class_count=Count('class', distinct=True),
    ).order_by('-start_date')

    total_classes = sum(y.class_count for y in years)

    return render(request, 'academics/manage_academic_years.html', {'years': years, 'total_classes': total_classes})


@login_required
def add_academic_year(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            year = form.save(commit=False)
            if year.is_current:
                AcademicYear.objects.filter(is_current=True).update(is_current=False)
            year.save()
            messages.success(request, f'Academic year "{year.name}" created.')
            return redirect('academics:manage_academic_years')
    else:
        form = AcademicYearForm()

    return render(request, 'academics/academic_year_form.html', {'form': form, 'title': 'Add Academic Year'})


@login_required
def edit_academic_year(request, year_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    year = get_object_or_404(AcademicYear, id=year_id)
    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=year)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.is_current:
                AcademicYear.objects.filter(is_current=True).exclude(id=year.id).update(is_current=False)
            updated.save()
            messages.success(request, f'Academic year "{year.name}" updated.')
            return redirect('academics:manage_academic_years')
    else:
        form = AcademicYearForm(instance=year)

    return render(request, 'academics/academic_year_form.html', {'form': form, 'title': f'Edit: {year.name}', 'editing': True})


@login_required
def delete_academic_year(request, year_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    year = get_object_or_404(AcademicYear, id=year_id)
    class_count = Class.objects.filter(academic_year=year).count()

    if request.method == 'POST':
        if class_count > 0:
            messages.error(request, f'Cannot delete "{year.name}" — it has {class_count} class(es). Remove them first.')
        elif year.is_current:
            messages.error(request, f'Cannot delete the current academic year. Set another year as current first.')
        else:
            name = year.name
            year.delete()
            messages.success(request, f'Academic year "{name}" deleted.')
        return redirect('academics:manage_academic_years')

    return render(request, 'academics/confirm_delete.html', {
        'object': year,
        'object_type': 'Academic Year',
        'warning': f'This academic year has {class_count} class(es).' if class_count else ('This is the current academic year.' if year.is_current else None),
        'can_delete': class_count == 0 and not year.is_current,
        'cancel_url': reverse('academics:manage_academic_years'),
    })


@login_required
def set_current_year(request, year_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        year = get_object_or_404(AcademicYear, id=year_id)
        AcademicYear.objects.filter(is_current=True).update(is_current=False)
        year.is_current = True
        year.save()
        messages.success(request, f'"{year.name}" is now the current academic year.')

    return redirect('academics:manage_academic_years')


@login_required
def manage_id_cards(request):
    """ID Card management dashboard for admins."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from teachers.models import Teacher

    # Handle template selection POST
    if request.method == 'POST' and 'id_card_template' in request.POST:
        template_choice = request.POST.get('id_card_template', 'classic')
        school_info = SchoolInfo.objects.first()
        if school_info:
            school_info.id_card_template = template_choice
            school_info.save(update_fields=['id_card_template'])
            messages.success(request, f'ID card template changed to {school_info.get_id_card_template_display()}.')
        else:
            messages.error(request, 'Please set up School Info first.')
        return redirect('academics:manage_id_cards')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    classes = Class.objects.filter(academic_year=current_year).order_by('name') if current_year else Class.objects.none()

    # Get selected class filter
    selected_class_id = request.GET.get('class_id', '')

    # Students
    students_qs = Student.objects.select_related('user', 'current_class')
    if selected_class_id:
        students_qs = students_qs.filter(current_class_id=selected_class_id)
    elif current_year:
        students_qs = students_qs.filter(current_class__academic_year=current_year)
    students = students_qs.order_by('current_class__name', 'user__last_name')

    # Teachers
    teachers = Teacher.objects.select_related('user').order_by('user__last_name')

    # Current template
    school_info = SchoolInfo.objects.first()
    current_template = school_info.id_card_template if school_info else 'classic'

    context = {
        'classes': classes,
        'students': students,
        'teachers': teachers,
        'selected_class_id': selected_class_id,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
        'current_year': current_year,
        'current_template': current_template,
        'school_info': school_info,
    }
    return render(request, 'academics/manage_id_cards.html', context)


@login_required
@require_addon('resource-library')
def manage_resources(request):
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Resource added successfully.')
            return redirect('academics:manage_resources')
    else:
        form = ResourceForm()
        
    # Detect if new resource fields exist in DB (for deployments that haven't run latest migration)
    resource_fields_available = False
    try:
        with connection.cursor() as cursor:
            cols = [col.name for col in connection.introspection.get_table_description(cursor, Resource._meta.db_table)]
        resource_fields_available = 'resource_type' in cols and 'curriculum' in cols
    except Exception:
        resource_fields_available = False

    base_qs = Resource.objects.select_related('class_subject', 'uploaded_by')
    if not resource_fields_available:
        base_qs = base_qs.only(
            'id', 'title', 'description', 'file', 'link',
            'target_audience', 'class_subject', 'uploaded_by', 'uploaded_at'
        )

    if request.user.user_type == 'admin':
        resources = base_qs
    else:
        resources = base_qs.filter(uploaded_by=request.user)
        
    return render(request, 'academics/manage_resources.html', {
        'form': form,
        'resources': resources,
        'resource_fields_available': resource_fields_available,
    })

@login_required
@require_addon('resource-library')
def delete_resource(request, resource_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Allow deletion if Admin OR if Teacher owns it
    if request.user.user_type == 'admin' or resource.uploaded_by == request.user:
        resource.delete()
        messages.success(request, 'Resource deleted.')
    else:
        messages.error(request, 'You cannot delete this resource.')
        
    return redirect('academics:manage_resources')


@require_addon('school-gallery')
def gallery_view(request):
    category = request.GET.get('category')
    categories = GalleryImage.CATEGORY_CHOICES
    gallery_error = None

    try:
        images = GalleryImage.objects.all()
        if category and category != 'all':
            images = images.filter(category=category)
    except ProgrammingError:
        images = []
        gallery_error = "Gallery tables are not ready. Please run tenant migrations to enable the gallery."
        messages.warning(request, gallery_error)
    
    context = {
        'images': images,
        'categories': categories,
        'current_category': category,
        'gallery_error': gallery_error,
    }
    return render(request, 'gallery.html', context)


def activities_public(request):
    activities = []
    try:
        activities = Activity.objects.filter(is_active=True).order_by('-date')
    except ProgrammingError:
        messages.warning(request, 'Activities are not available yet. Please run tenant migrations to enable this page.')

    context = {
        'activities': activities,
        'school_info': SchoolInfo.objects.first(),
    }
    return render(request, 'academics/activities_public.html', context)


@ensure_csrf_cookie
@require_addon('ai-admissions-assistant')
def admissions_assistant(request):
    logger.debug("Admissions assistant: %s %s", request.method, request.content_type)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    # Basic IP-based rate limiting (20 requests per 60s window)
    from django.core.cache import cache
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    schema = connection.tenant.schema_name
    rate_key = f"{schema}:chatbot_rate:{ip}"
    hits = cache.get(rate_key, 0)
    if hits >= 20:
        return JsonResponse({'error': 'Too many requests. Please wait a moment.'}, status=429)
    cache.set(rate_key, hits + 1, 60)

    try:
        # Parse request body
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
    except Exception as e:
        logger.warning("Chatbot payload parsing error: %s", e)
        return JsonResponse({'error': 'Invalid payload', 'details': str(e)}, status=400)

    question = (payload.get('question') or '').strip()
    logger.debug("Chatbot question received: %s", question[:120])
    
    if not question:
        return JsonResponse({'answer': 'Please ask a question about admissions, fees, or term dates.'})

    # Safely get school info
    try:
        school_info = SchoolInfo.objects.first()
        logger.debug("Chatbot school info: %s", school_info.name if school_info else 'None')
    except Exception as e:
        logger.warning("Chatbot error getting school info: %s", e)
        school_info = None

    def fallback_answer():
        faq = [
            (('fee', 'tuition', 'fees', 'payment'), "Our fees vary by class. Please see the fee structure shared during enrollment or ask which class you're interested in."),
            (('term', 'calendar', 'date', 'schedule'), "Terms follow a three-term calendar: First (Sept-Dec), Second (Jan-Apr), Third (May-Jul). Exact dates are in the school calendar."),
            (('apply', 'enroll', 'admission', 'register'), "You can apply online via the Apply page. Submit student details, parent contact, and prior school info if available."),
            (('document', 'requirements', 'forms'), "Commonly needed: birth certificate, prior report (if any), passport photo, and completed application form."),
            (('scholarship', 'discount', 'financial aid'), "Limited scholarships/fee waivers may be available. Please indicate interest in your application or ask admin for current options."),
            (('contact', 'phone', 'email'), f"You can reach us at {school_info.phone if school_info else 'the school office phone'} or {school_info.email if school_info else 'our email'} for more details."),
        ]

        answer_text = "I can help with admissions, fees, and term dates. What would you like to know?"
        question_lower = question.lower()
        for keywords, response in faq:
            if any(k in question_lower for k in keywords):
                answer_text = response
                break
        return answer_text

    # Try OpenAI API first with streaming response
    from django.conf import settings
    logger.debug("Chatbot OpenAI API key configured: %s", bool(settings.OPENAI_API_KEY))
    
    if settings.OPENAI_API_KEY:
        try:
            logger.debug("Chatbot calling OpenAI API via REST")
            from academics.ai_tutor import _stream_chat_completion_text, get_openai_chat_model
            
            # Build context from school info
            school_context = f"""
You are a helpful admissions assistant for {school_info.name if school_info else 'our school'}.

School Information:
- Name: {school_info.name if school_info else 'N/A'}
- Phone: {school_info.phone if school_info else 'Contact admin'}
- Email: {school_info.email if school_info else 'Contact admin'}
- Address: {school_info.address if school_info else 'Contact admin'}
- Motto: {school_info.motto if school_info else 'Excellence in Education'}

General Information:
- Academic Calendar: Three terms - First (Sept-Dec), Second (Jan-Apr), Third (May-Jul)
- Admission Process: Apply online via our Apply page with student details, parent contact, and prior school info
- Required Documents: Birth certificate, prior report card (if any), passport photo, completed application form
- Scholarships: Limited scholarships and fee waivers may be available - indicate interest in application
- Fee Structure: Varies by class level - details provided during enrollment process

Please provide helpful, concise answers about admissions, fees, term dates, and enrollment processes.
"""

            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": school_context},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 200,
                "temperature": 0.7,
                "stream": True
            }

            def stream_chat():
                try:
                    for chunk in _stream_chat_completion_text(payload, settings.OPENAI_API_KEY):
                        yield chunk
                except Exception as e:
                    logger.error("Chatbot streaming error: %s", e, exc_info=True)
                
            return StreamingHttpResponse(stream_chat(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            # Fall back to FAQ if OpenAI fails
            logger.error("Chatbot OpenAI API error: %s", e, exc_info=True)

    # Fallback FAQ system (plain text)
    fallback_text = fallback_answer()
    return HttpResponse(fallback_text, content_type='text/plain; charset=utf-8')


@login_required
def copilot_history(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    try:
        from .tutor_models import CopilotConversation

        conversation = CopilotConversation.objects.filter(user=request.user, is_active=True).first()
        if not conversation:
            return JsonResponse({'conversation_id': None, 'messages': []})

        messages_qs = conversation.messages.order_by('created_at')[:30]
        messages = [
            {
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
            for message in messages_qs
        ]

        return JsonResponse({'conversation_id': conversation.id, 'messages': messages})
    except Exception as e:
        logger.warning('copilot_history DB error (table may not exist): %s', e)
        return JsonResponse({'conversation_id': None, 'messages': []})


@ensure_csrf_cookie
def copilot_assistant(request):
    logger.debug("Copilot assistant: %s %s", request.method, request.content_type)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    # Rate limiting for unauthenticated users (30 requests per 60s window)
    if not request.user.is_authenticated:
        from django.core.cache import cache
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        schema = connection.tenant.schema_name
        rate_key = f"{schema}:copilot_rate:{ip}"
        hits = cache.get(rate_key, 0)
        if hits >= 30:
            return JsonResponse({'error': 'Too many requests. Please wait a moment.'}, status=429)
        cache.set(rate_key, hits + 1, 60)

    def violates_school_policy(text: str) -> bool:
        if not text:
            return False
        lowered = text.lower()
        banned_terms = [
            # Violence / weapons
            'kill', 'murder', 'suicide', 'bomb', 'shoot', 'stab', 'weapon',
            # Sexual content
            'sex', 'porn', 'explicit', 'nsfw', 'nude', 'onlyfans',
            # Self-harm / harm
            'self-harm', 'self harm', 'hurt myself', 'cutting',
            # Hate / harassment
            'hate crime', 'racial slur', 'racist', 'homophobic', 'transphobic',
            # Drugs / illicit
            'cocaine', 'heroin', 'meth', 'lsd', 'ecstasy', 'fentanyl', 'weed', 'marijuana', 'ganja', 'vape',
        ]
        return any(term in lowered for term in banned_terms)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
    except Exception as e:
        logger.warning("Copilot payload parsing error: %s", e)
        return JsonResponse({'error': 'Invalid payload', 'details': str(e)}, status=400)

    question = (payload.get('question') or '').strip()
    user_role = (payload.get('role') or '').strip()
    incoming_conversation_id = payload.get('conversation_id')

    if not user_role and request.user.is_authenticated:
        user_role = getattr(request.user, 'user_type', '') or ''

    logger.debug("Copilot role=%s question=%s", user_role, question[:120])

    if violates_school_policy(question):
        return HttpResponse('This assistant cannot discuss that topic. Please ask about schoolwork, schedules, grades, or fees.', content_type='text/plain; charset=utf-8', status=400)

    # Guardrail: require role before continuing
    try:
        school_info = SchoolInfo.objects.first()
    except Exception:
        school_info = None

    if not user_role:
        prompt_role = f"Welcome to {school_info.name if school_info else 'our school'}! To help you better, are you a student, parent, or staff member?"
        return HttpResponse(prompt_role, content_type='text/plain; charset=utf-8')

    if not question:
        return HttpResponse('Ask me anything about your classes, calendar, grades, fees, or school updates.', content_type='text/plain; charset=utf-8')

    conversation = None
    if request.user.is_authenticated:
        try:
            from .tutor_models import CopilotConversation, CopilotMessage

            if incoming_conversation_id:
                conversation = CopilotConversation.objects.filter(
                    id=incoming_conversation_id,
                    user=request.user,
                    is_active=True,
                ).first()

            if not conversation:
                conversation = CopilotConversation.objects.filter(user=request.user, is_active=True).first()

            if not conversation:
                conversation = CopilotConversation.objects.create(
                    user=request.user,
                    title=question[:120],
                    user_role=user_role or getattr(request.user, 'user_type', ''),
                    is_active=True,
                )

            CopilotMessage.objects.create(
                conversation=conversation,
                role='user',
                content=question,
            )
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])
        except Exception as persistence_err:
            logger.warning("Copilot could not persist user message: %s", persistence_err)

    def build_data_snapshot():
        if not request.user.is_authenticated:
            return ""

        snapshot_lines = []

        try:
            if user_role == 'student':
                student = Student.objects.select_related('current_class', 'user').filter(user=request.user).first()
                if student:
                    snapshot_lines.append(f"Student: {student.user.get_full_name()} ({student.admission_number})")
                    snapshot_lines.append(f"Class: {student.current_class.name if student.current_class else 'Unassigned'}")

                    recent_att = Attendance.objects.filter(student=student).order_by('-date')[:5]
                    if recent_att:
                        att_lines = [f"{a.date}: {a.status}" + (f" ({a.remarks})" if a.remarks else '') for a in recent_att]
                        snapshot_lines.append("Recent Attendance: " + " | ".join(att_lines))

                    current_year = AcademicYear.objects.filter(is_current=True).first()
                    recent_grades_qs = Grade.objects.filter(student=student)
                    if current_year:
                        recent_grades_qs = recent_grades_qs.filter(academic_year=current_year)
                        
                    # Trend Analysis (Average across terms)
                    try:
                        from django.db.models import Avg
                        term_avgs = []
                        for t in ['first', 'second', 'third']:
                            qs = recent_grades_qs.filter(term__iexact=t, total_score__isnull=False)
                            if qs.exists():
                                term_avgs.append((t.title(), round(qs.aggregate(val=Avg('total_score'))['val'], 1)))
                        if term_avgs:
                            trend_str = ", ".join([f"{term} Term: {avg}%" for term, avg in term_avgs])
                            snapshot_lines.append(f"Term Averages: {trend_str}")
                            if len(term_avgs) > 1:
                                cur_avg, prev_avg = term_avgs[-1][1], term_avgs[-2][1]
                                if cur_avg >= prev_avg + 2:
                                    snapshot_lines.append("Trend Insight: The student is showing improvement recently.")
                                elif cur_avg <= prev_avg - 2:
                                    snapshot_lines.append("Trend Insight: The student's average has dropped. Mention they might need study support.")
                                else:
                                    snapshot_lines.append("Trend Insight: The student's academic performance is very stable.")
                    except Exception:
                        pass

                    recent_grades = recent_grades_qs.select_related('subject').order_by('-updated_at')[:5]
                    if recent_grades:
                        grade_lines = [f"{g.subject.name} ({g.term}): {g.total_score} ({g.remarks})" for g in recent_grades]
                        snapshot_lines.append("Recent Assessed Grades: " + " | ".join(grade_lines))

            if user_role == 'parent':
                from parents.models import Parent
                parent = Parent.objects.select_related('user').prefetch_related('children').filter(user=request.user).first()
                if parent:
                    child_lines = []
                    for child in parent.children.all():
                        line = f"{child.user.get_full_name()} ({child.admission_number})"
                        recent_att = Attendance.objects.filter(student=child).order_by('-date')[:3]
                        if recent_att:
                            att_bits = [f"{a.date}: {a.status}" for a in recent_att]
                            line += " | Attendance: " + "; ".join(att_bits)
                        
                        # Add Trend insight for Parent
                        try:
                            from django.db.models import Avg
                            term_avgs = []
                            for t in ['first', 'second', 'third']:
                                qs = Grade.objects.filter(student=child, term__iexact=t, total_score__isnull=False)
                                if qs.exists():
                                    term_avgs.append(round(qs.aggregate(val=Avg('total_score'))['val'], 1))
                            if len(term_avgs) > 1:
                                if term_avgs[-1] >= term_avgs[-2] + 2:
                                    line += f" | Trend: Improving (Latest Avg: {term_avgs[-1]}%)"
                                elif term_avgs[-1] <= term_avgs[-2] - 2:
                                    line += f" | Trend: Decreased (Latest Avg: {term_avgs[-1]}%)"
                                else:
                                    line += f" | Trend: Stable"
                        except Exception:
                            pass
                            
                        recent_grades = Grade.objects.filter(student=child).select_related('subject').order_by('-updated_at')[:3]
                        if recent_grades:
                            grade_bits = [f"{g.subject.name} {g.term}: {g.total_score} ({g.remarks})" for g in recent_grades]
                            line += " | Grades: " + "; ".join(grade_bits)
                        child_lines.append(line)
                    if child_lines:
                        snapshot_lines.append("Children: " + " || ".join(child_lines))

            if user_role in ['teacher', 'admin']:
                # Provide minimal context without exposing other users' PII
                current_year = AcademicYear.objects.filter(is_current=True).first()
                if current_year:
                    snapshot_lines.append(f"Current academic year: {current_year.name}")
                
                # Expose today's attendance summary for the teacher's classes
                try:
                    from teachers.models import Teacher
                    from students.models import Attendance
                    from django.utils import timezone
                    
                    teacher = Teacher.objects.filter(user=request.user).first()
                    if teacher:
                        today = timezone.now().date()
                        my_classes = Class.objects.filter(class_teacher=teacher)
                        
                        if my_classes.exists():
                            for c in my_classes:
                                students_in_class = Student.objects.filter(current_class=c)
                                total_students = students_in_class.count()
                                if total_students > 0:
                                    present = Attendance.objects.filter(
                                        student__in=students_in_class, 
                                        date=today, 
                                        status='present'
                                    ).count()
                                    absent = Attendance.objects.filter(
                                        student__in=students_in_class, 
                                        date=today, 
                                        status__in=['absent', 'late', 'excused']
                                    ).count()
                                    
                                    unmarked = total_students - (present + absent)
                                    att_summary = f"{c.name} Attendance (Today {today.strftime('%b %d')}): {present} Present, {absent} Absent"
                                    if unmarked > 0:
                                        att_summary += f", {unmarked} Not Marked Yet"
                                        
                                    # Allow Aura to name absentees if asked
                                    absentees = list(Attendance.objects.filter(
                                        student__in=students_in_class, 
                                        date=today, 
                                        status='absent'
                                    ).select_related('student__user'))
                                    
                                    if absentees:
                                        names = ", ".join([a.student.user.get_full_name() for a in absentees])
                                        att_summary += f". (Absent: {names})"
                                        
                                    snapshot_lines.append(att_summary)
                except Exception as e:
                    pass

        except Exception as ctx_err:
            logger.warning("Copilot data snapshot error: %s", ctx_err)

        return "\n".join(snapshot_lines)

    data_snapshot = build_data_snapshot()

    school_context = f"""
School Name: {school_info.name if school_info else (payload.get('school') or 'Unknown School')}
Motto: {school_info.motto if school_info else ''}
Address: {school_info.address if school_info else ''}
Phone: {school_info.phone if school_info else ''}
Email: {school_info.email if school_info else ''}
Current User Role: {user_role}
"""

    teacher_response_guide = ""
    if user_role == 'teacher':
        teacher_response_guide = (
            "Teacher Response Style:\n"
            "- Be concise and action-focused.\n"
            "- Use bullet points where possible.\n"
            "- Keep to 3-6 short lines unless the user asks for more.\n"
            "- Avoid long introductions or filler.\n"
        )

    system_prompt = f"""portals AI Copilot 2026
Role & Objective:
You are the School-Portals AI Copilot, the central intelligence layer for a comprehensive K-12/Higher-Ed SaaS application. Your goal is to provide proactive, role-specific assistance to Students, Parents, Teachers, and Administrators while maintaining strict FERPA/GDPR data privacy standards.

Persona Adaptation:
- Students: Act as a Socratic Tutor. Do not just give answers; explain concepts, provide practice problems, and offer encouragement.
- Parents: Act as a Concierge. Provide clear, empathetic updates on school events, child progress, and administrative tasks (fees, forms).
- Teachers: Act as an Executive Assistant. Be efficient and technical. Assist with lesson plan generation, rubric creation, and automated student performance summaries.
- Admins: Act as a Data Analyst. Provide high-level insights on enrollment, attendance trends, and resource allocation.

Core Capabilities & Task Execution:
- Proactive Intelligence: Use If-Then logic to nudge users (e.g., "I noticed you have a math test tomorrow; would you like to review the study guide?").
- Task Automation: You may suggest triggering actions (simulated) like scheduling conferences, updating attendance, or sending payment links; clearly mark them as simulated.
- Sentiment Analysis: Watch for distress, bullying, or frustration. If detected, advise involving a human and flag gently.
- Multilingual Support: Detect the user's preferred language and respond fluently while keeping educational terms accurate.

Operational Guardrails:
- Privacy: Never disclose one student’s data to another student or unauthorized parent. Keep answers scoped to the asking user.
- Accuracy: If information is not in the known school context, say you do not know and offer to connect to staff.
- Tone: Professional, encouraging, and supportive. Avoid robotic or overly formal language.
- Safety: Decline and redirect any violent, sexual, self-harm, hate, or illicit-drug content; keep responses appropriate for K-12.

Context Initialization:
- The user role is {user_role}. If context is insufficient, ask for clarification briefly.
- School context: {school_context}
- Data snapshot (only for authorized users): {data_snapshot if data_snapshot else 'None'}
{teacher_response_guide}
"""

    from django.conf import settings
    hf_token = (
        os.environ.get('HUGGINGFACE_API_TOKEN')
        or os.environ.get('HF_TOKEN')
        or os.environ.get('HUGGINGFACEHUB_API_TOKEN')
    )
    if not settings.OPENAI_API_KEY and not hf_token:
        return HttpResponse('Copilot is offline: no AI provider credentials configured.', content_type='text/plain; charset=utf-8', status=503)

    try:
        def persist_assistant_message(full_text):
            if not conversation:
                return
            text = (full_text or '').strip()
            if not text:
                return
            try:
                from .tutor_models import CopilotMessage
                CopilotMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=text,
                )
                conversation.updated_at = timezone.now()
                conversation.save(update_fields=['updated_at'])
            except Exception as persistence_err:
                logger.warning("Copilot could not persist assistant message: %s", persistence_err)

        def stream_and_store(generator):
            full_text = ''
            try:
                for token in generator:
                    full_text += token
                    yield token
            except Exception as stream_err:
                logger.error("Copilot stream iteration error: %s", stream_err, exc_info=True)
                err_fragment = f"\n\n[An error occurred while generating the response. Please try again.]"
                full_text += err_fragment
                yield err_fragment
            finally:
                persist_assistant_message(full_text)

        def build_stream_response(generator):
            response = StreamingHttpResponse(stream_and_store(generator), content_type='text/plain; charset=utf-8')
            if conversation:
                response['X-Conversation-Id'] = str(conversation.id)
            return response

        def build_plain_response(text, status=200):
            persist_assistant_message(text)
            response = HttpResponse(text, content_type='text/plain; charset=utf-8', status=status)
            if conversation:
                response['X-Conversation-Id'] = str(conversation.id)
            return response

        def normalize_delta(delta_content):
            if not delta_content:
                return ""
            if isinstance(delta_content, list):
                parts = []
                for item in delta_content:
                    text_part = ''
                    if isinstance(item, dict):
                        text_part = item.get('text', '')
                    else:
                        text_part = getattr(item, 'text', '') or str(item)
                    parts.append(text_part)
                return ''.join(parts)
            return str(delta_content)

        def stream_via_rest():
            from academics.ai_tutor import (
                _stream_chat_completion_text,
                get_active_ai_model,
                _is_gemini_provider,
                _stream_gemini_chat,
                GEMINI_CHAT_MODELS,
            )

            # Retrieve recent conversation history for continuous context memory
            api_messages = [{"role": "system", "content": system_prompt}]

            if conversation:
                try:
                    recent_msgs = conversation.messages.order_by('-created_at')[:10]
                    for msg in reversed(list(recent_msgs)):
                        api_messages.append({"role": msg.role, "content": msg.content})
                except Exception as history_err:
                    logger.warning("Copilot history unavailable: %s", history_err)
                    api_messages.append({"role": "user", "content": question})
            else:
                api_messages.append({"role": "user", "content": question})

            active_model = get_active_ai_model()
            use_gemini = _is_gemini_provider() or active_model in GEMINI_CHAT_MODELS or active_model.startswith("gemini")

            payload = {
                "model": active_model,
                "messages": api_messages,
                "max_tokens": 600,
                "temperature": 0.7,
                "stream": True,
            }
            try:
                if use_gemini:
                    for sse in _stream_gemini_chat(payload, model_override=active_model if use_gemini else None):
                        if not sse.startswith("data: "):
                            continue
                        data_str = sse[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            piece = json.loads(data_str).get("content", "")
                            if piece:
                                yield piece
                        except Exception:
                            pass
                else:
                    for chunk in _stream_chat_completion_text(payload, settings.OPENAI_API_KEY):
                        yield chunk
            except Exception as e:
                logger.error("Copilot streaming error: %s", e, exc_info=True)
                yield f"\n\n[Error: {e}]"

        return build_stream_response(stream_via_rest())
    except Exception as e:
        err_msg = f"Copilot error: {e}"
        logger.error(err_msg, exc_info=True)
        return build_plain_response(err_msg, status=502)



@login_required
def manage_activities(request):
	if request.user.user_type != 'admin':
		messages.error(request, 'Access denied. Admins only.')
		return redirect('dashboard')

	staff_queryset = User.objects.filter(user_type__in=['admin', 'teacher']).order_by('first_name', 'last_name')

	# Admins see all activities
	try:
		activities = Activity.objects.all()
	except Exception:
		activities = []
		messages.warning(request, 'Activities table not initialized. Please run migrations.')

	if request.method == 'POST':
		activity_id = request.POST.get('activity_id')
		title = request.POST.get('title')
		summary = request.POST.get('summary', '')
		date = request.POST.get('date')
		tag = request.POST.get('tag', '')
		is_active = request.POST.get('is_active') == 'on'

		if not title or not date:
			messages.error(request, 'Title and date are required')
			return redirect('academics:manage_activities')

		if activity_id:
			activity = get_object_or_404(Activity, id=activity_id)
		else:
			activity = Activity(created_by=request.user)

		activity.title = title
		activity.summary = summary
		activity.date = date
		activity.tag = tag
		activity.is_active = is_active
		activity.save()

		# Assign staff: admins can pick
		assigned_ids = request.POST.getlist('assigned_staff')
		assigned_users = staff_queryset.filter(id__in=assigned_ids)
		activity.assigned_staff.set(assigned_users)

		messages.success(request, 'Activity saved successfully')
		return redirect('academics:manage_activities')

	context = {
		'activities': activities.order_by('-date'),
		'staff_queryset': staff_queryset,
		'is_admin': True,
	}
	return render(request, 'academics/manage_activities.html', context)


@login_required
def school_settings_view(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    info = SchoolInfo.objects.first()
    if not info:
        info = SchoolInfo()
        
    if request.method == 'POST':
        # Check if it's a preview request
        if 'preview' in request.POST:
            # Don't save, just pass form data to preview
            form = SchoolInfoForm(request.POST, request.FILES, instance=info)
            if form.is_valid():
                # Get template choice from form
                template_choice = form.cleaned_data.get('homepage_template', 'default')
                # Store form data in session for preview
                request.session['preview_data'] = {
                    'template': template_choice,
                    'form_data': {k: v for k, v in form.cleaned_data.items() if k != 'logo'}
                }
                # Redirect to preview
                return redirect('academics:preview_homepage')
        else:
            # Regular save
            form = SchoolInfoForm(request.POST, request.FILES, instance=info)
            if form.is_valid():
                form.save()
                messages.success(request, 'School settings updated successfully')
                return redirect('academics:school_settings')
    else:
        form = SchoolInfoForm(instance=info)
        
    return render(request, 'academics/school_settings_new.html', {'form': form})


@login_required
def preview_homepage(request):
    """Preview homepage with unsaved customization changes"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    # Get preview data from session
    preview_data = request.session.get('preview_data', {})
    if not preview_data:
        messages.warning(request, 'No preview data found. Please try again.')
        return redirect('academics:school_settings')
    
    # Get current school info as base
    info = SchoolInfo.objects.first()
    if not info:
        info = SchoolInfo()
    
    # Create a temporary object with preview data (don't save to DB)
    class PreviewSchoolInfo:
        def __init__(self, base_obj, preview_data):
            # Copy all attributes from base object safely
            try:
                for field in base_obj._meta.fields:
                    try:
                        setattr(self, field.name, getattr(base_obj, field.name, ''))
                    except Exception:
                        setattr(self, field.name, '')
            except Exception:
                pass
            # Override with preview data
            for key, value in preview_data.items():
                setattr(self, key, value)
        
        def __getattr__(self, name):
            # Return empty string for any missing attributes
            return ''
    
    preview_info = PreviewSchoolInfo(info, preview_data.get('form_data', {}))
    template_choice = preview_data.get('template', 'default')
    
    # Prepare context similar to homepage view
    from academics.models import Activity, GalleryImage
    
    activities = []
    try:
        activities = Activity.objects.all().order_by('-date')[:5]
    except Exception:
        pass  # Table doesn't exist
    
    gallery_images = GalleryImage.objects.all().order_by('?')[:6]
    hero_images = GalleryImage.objects.all().order_by('-created_at')[:3]
    
    # Build highlights from preview features
    highlights = [
        {
            'title': getattr(preview_info, 'feature1_title', ''),
            'desc': getattr(preview_info, 'feature1_description', ''),
            'icon': f'fas {getattr(preview_info, "feature1_icon", "fa-star")}'
        },
        {
            'title': getattr(preview_info, 'feature2_title', ''),
            'desc': getattr(preview_info, 'feature2_description', ''),
            'icon': f'fas {getattr(preview_info, "feature2_icon", "fa-book")}'
        },
        {
            'title': getattr(preview_info, 'feature3_title', ''),
            'desc': getattr(preview_info, 'feature3_description', ''),
            'icon': f'fas {getattr(preview_info, "feature3_icon", "fa-users")}'
        }
    ]
    
    context = {
        'activities': activities,
        'highlights': highlights,
        'hero_images': hero_images,
        'gallery_images': gallery_images,
        'school_info': preview_info,
        'is_preview': True  # Flag to show preview banner
    }
    
    # Route to selected template
    template_map = {
        'modern': 'home/modern.html',
        'classic': 'home/classic.html',
        'minimal': 'home/minimal.html',
        'playful': 'home/playful.html',
        'elegant': 'home/elegant.html',
    }
    
    template = template_map.get(template_choice, 'home/modern.html')
    return render(request, template, context)


@login_required
def timetable_view(request):
    if request.user.user_type not in ['admin', 'teacher', 'student']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    classes = Class.objects.filter(academic_year__is_current=True)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    timetable_grid = {day: [] for day in days}
    
    selected_class = None
    is_teacher_schedule = False
    
    if request.user.user_type == 'teacher':
        is_teacher_schedule = True
        # Teacher sees their own schedule across all classes
        entries = Timetable.objects.filter(
            class_subject__teacher__user=request.user,
            class_subject__class_name__academic_year__is_current=True
        ).select_related('class_subject__subject', 'class_subject__class_name')
        
        for entry in entries:
            day_name = entry.get_day_display()
            if day_name in timetable_grid:
                timetable_grid[day_name].append(entry)
                
    else:
        # Admin and Student see Class Timetables
        selected_class_id = request.GET.get('class_id')
        
        # Auto-select class for students
        if not selected_class_id:
            if request.user.user_type == 'student':
                student = getattr(request.user, 'student', None)
                if student and student.current_class:
                    selected_class_id = student.current_class.id
        
        if selected_class_id:
            selected_class = get_object_or_404(Class, id=selected_class_id)
            entries = Timetable.objects.filter(class_subject__class_name=selected_class).select_related('class_subject__subject', 'class_subject__teacher')
            
            for entry in entries:
                day_name = entry.get_day_display()
                if day_name in timetable_grid:
                    timetable_grid[day_name].append(entry)
        
        # Sort each day by start time
    for day in days:
        timetable_grid[day].sort(key=lambda x: x.start_time)

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'timetable': timetable_grid,
        'days': days,
        'is_teacher_schedule': is_teacher_schedule,
    }
    return render(request, 'academics/timetable.html', context)

@login_required
def edit_timetable(request, class_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('academics:timetable')
    
    school_class = get_object_or_404(Class, id=class_id)
    class_subjects = ClassSubject.objects.filter(class_name=school_class).select_related('subject')
    
    # Define standard time slots
    slots = [
        {'start': '07:00:00', 'end': '08:40:00', 'label': 'Lesson 1'},
        {'start': '08:40:00', 'end': '09:50:00', 'label': 'Lesson 2'},
        {'start': '10:20:00', 'end': '11:30:00', 'label': 'Lesson 3'},
        {'start': '11:30:00', 'end': '12:40:00', 'label': 'Lesson 4'},
        {'start': '13:00:00', 'end': '14:00:00', 'label': 'Lesson 5'},
    ]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_map = {day: idx for idx, day in enumerate(days)}

    if request.method == 'POST':
        # Clear existing timetable for standard slots to avoid complex updates
        # But maybe we should be more granular. 
        # Strategy: Iterate through POST data, update/create.
        
        updated_count = 0
        for day in days:
            day_idx = day_map[day]
            for slot_idx, slot in enumerate(slots):
                field_name = f"slot_{day}_{slot_idx}"
                subject_id = request.POST.get(field_name)
                
                start_time = datetime.datetime.strptime(slot['start'], "%H:%M:%S").time()
                end_time = datetime.datetime.strptime(slot['end'], "%H:%M:%S").time()

                # Find existing entry
                existing = Timetable.objects.filter(
                    class_subject__class_name=school_class,
                    day=day_idx,
                    start_time=start_time
                ).first()

                if subject_id:
                    # Update or Create
                    try:
                        cs = ClassSubject.objects.get(id=subject_id)
                        if existing:
                            existing.class_subject = cs
                            existing.end_time = end_time # Ensure end time matches slot
                            existing.save()
                        else:
                            Timetable.objects.create(
                                class_subject=cs,
                                day=day_idx,
                                start_time=start_time,
                                end_time=end_time
                            )
                        updated_count += 1
                    except ClassSubject.DoesNotExist:
                        pass
                else:
                    # Remove if it exists and field is empty
                    if existing:
                        try:
                            existing.delete()
                        except ProgrammingError as e:
                            # Fallback if announcements_notification table is missing (migration issue)
                            if 'announcements_notification' in str(e):
                                with connection.cursor() as cursor:
                                    try:
                                        # Try simple delete first
                                        cursor.execute("DELETE FROM academics_timetable WHERE id = %s", [existing.id])
                                    except Exception as inner_e:
                                        # If simple delete fails due to constraints, try ignoring constraints? 
                                        # Postgres doesn't easily allow disabling constraints session-wide for a specific table without superuser.
                                        # But if the table is missing, foreign keys from it shouldn't exist?
                                        # The error suggests the RELATION is missing, so checking it for cascade is failing.
                                        raise inner_e
                            else:
                                raise e
        
        messages.success(request, f'Timetable updated for {school_class.name}')
        return redirect('academics:timetable')

    # Prepare current data for form pre-fill
    timetable_data = {}
    entries = Timetable.objects.filter(class_subject__class_name=school_class)
    for entry in entries:
        day_name = entry.get_day_display()
        time_key = entry.start_time.strftime("%H:%M:%S")
        timetable_data[f"{day_name}_{time_key}"] = entry.class_subject.id

    context = {
        'school_class': school_class,
        'class_subjects': class_subjects,
        'slots': slots,
        'days': days,
        'timetable_data': timetable_data,
    }
    return render(request, 'academics/edit_timetable.html', context)


@login_required
def upload_gallery_image(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('academics:gallery')
    
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Image uploaded successfully!')
                return redirect('academics:gallery')
            except Exception as e:
                messages.error(request, f'Upload failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GalleryImageForm()
    
    return render(request, 'academics/upload_gallery_image.html', {'form': form})


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if len(query) < 2:
        return JsonResponse({'results': []})

    # 1. Search Users
    if request.user.user_type in ['admin', 'teacher']:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:5]
        
        for u in users:
            url = '#'
            if u.user_type == 'student':
                 # Redirect to student list with search filter
                 url = reverse('students:student_list') + f'?q={u.username}'
            elif request.user.user_type == 'admin':
                 url = reverse('accounts:manage_users') + f'?q={u.username}'
            
            results.append({
                'category': f'User ({u.user_type.title()})',
                'title': u.get_full_name(),
                'url': url,
                'icon': 'bi-person-circle'
            })

    # 2. Search Resources
    resources = Resource.objects.filter(title__icontains=query)[:5]
    for r in resources:
        results.append({
            'category': 'Resource',
            'title': r.title,
            'url': r.file.url if r.file else r.link,
            'icon': 'bi-file-earmark-text'
        })

    # 3. Search Announcements
    notices = Announcement.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query)
    )[:3]
    for n in notices:
        results.append({
            'category': 'Announcement',
            'title': n.title,
            'url': reverse('announcements:manage'),
            'icon': 'bi-megaphone'
        })

    # 4. Search Pages (Navigation)
    nav_items = [
        {'title': 'Dashboard', 'url': reverse('dashboard'), 'keywords': 'home main'},
        {'title': 'Timetable', 'url': reverse('academics:timetable'), 'keywords': 'schedule class time'},
        {'title': 'Gallery', 'url': reverse('academics:gallery'), 'keywords': 'photos images'},
    ]
    
    if request.user.user_type == 'admin':
        nav_items.extend([
            {'title': 'Finance', 'url': reverse('finance:dashboard'), 'keywords': 'fees payments'},
            {'title': 'School Settings', 'url': reverse('academics:school_settings'), 'keywords': 'config setup'},
            {'title': 'Manage Users', 'url': reverse('accounts:manage_users'), 'keywords': 'people staff'},
        ])
    
    for item in nav_items:
        if query.lower() in item['title'].lower() or query.lower() in item['keywords']:
            results.append({
                'category': 'Navigate',
                'title': item['title'],
                'url': item['url'],
                'icon': 'bi-arrow-right-circle'
            })

    return JsonResponse({'results': results})


# =====================
# AI TUTOR ASSISTANT
# =====================

def _get_student_tutor_context(user, tenant=None):
    """Return (student, subjects, error_message) for AI Tutor endpoints."""
    from students.models import Student
    from tenants.models import SchoolSubscription, SchoolAddOn, AddOn

    if user.user_type != 'student':
        return None, [], "AI Tutor is only available for students"

    try:
        student = Student.objects.select_related('current_class').get(user=user)
    except Student.DoesNotExist:
        return None, [], "Student profile not found"
    except ProgrammingError:
        return None, [], "AI Tutor is unavailable because this school database is not fully migrated yet. Please contact your administrator."

    try:
        subjects = list(
            Subject.objects.filter(classsubject__isnull=False)
            .distinct()
            .order_by('name')
        )

        if not subjects:
            subjects = list(Subject.objects.all().order_by('name'))
    except ProgrammingError:
        return None, [], "AI Tutor is unavailable because this school database is not fully migrated yet. Please contact your administrator."

    if tenant is not None:
        try:
            subscription = SchoolSubscription.objects.filter(school=tenant).first()
            ai_tutor_addon = AddOn.objects.filter(slug='ai-tutor').first()

            if not subscription or not ai_tutor_addon:
                return student, subjects, None

            addon_link = SchoolAddOn.objects.filter(
                subscription=subscription,
                addon=ai_tutor_addon,
            ).first()

            if addon_link is not None and not addon_link.is_active:
                return None, [], "AI Tutor is not available. Please contact your administrator."
        except Exception:
            return None, [], "Unable to verify AI Tutor access"

    return student, subjects, None


def _persist_to_learner_memory(student, summary_payload):
    """
    Persist a session_summary payload into the student's LearnerMemory.
    Creates the LearnerMemory row on first use.
    """
    try:
        from .tutor_models import LearnerMemory
        memory, _ = LearnerMemory.objects.get_or_create(student=student)
        memory.ingest_session_summary(summary_payload)
    except Exception as e:
        # Non-critical — log but don't break the response
        logger.warning("LearnerMemory failed to persist for %s: %s", student, e)


def _check_and_send_review_reminders(student):
    """
    After a session ends, look at the student's LearnerMemory review_queue
    for any items due today or overdue and create one Notification if there
    are items due and none has been sent today.
    """
    try:
        import datetime
        from .tutor_models import LearnerMemory
        from announcements.models import Notification

        memory = LearnerMemory.objects.filter(student=student).first()
        if not memory or not memory.review_queue:
            return

        from django.utils import timezone as tz
        today = tz.localdate()

        due_topics = []
        for item in memory.review_queue:
            if not isinstance(item, dict):
                continue
            due_str = item.get('due_date')
            if not due_str:
                continue
            try:
                due_date = datetime.date.fromisoformat(str(due_str))
                if due_date <= today:
                    due_topics.append(item.get('topic', 'a topic'))
            except ValueError:
                continue

        if not due_topics:
            return

        # One notification per student per day — deduplicate
        already_sent = Notification.objects.filter(
            recipient=student.user,
            alert_type='general',
            message__startswith='⏰ Time to review',
            created_at__date=today,
        ).exists()
        if already_sent:
            return

        topic_list = ', '.join(due_topics[:3])
        if len(due_topics) > 3:
            topic_list += f' +{len(due_topics) - 3} more'

        Notification.objects.create(
            recipient=student.user,
            message=f'⏰ Time to review: {topic_list}. Open Aura to continue!',
            alert_type='general',
            link='../../academics/ai-tutor/',
        )
    except Exception as e:
        logger.warning('review reminder check failed: %s', e)


def _log_session_power_words(student, full_text, subject_name=''):
    """
    Parse [POWER_WORDS: word1, word2] tokens from an assistant response
    and upsert them into the PowerWord table via PowerWord.log().
    Non-critical — failures are logged but never surface to the student.
    """
    if not full_text:
        return
    try:
        import re as _re
        from .tutor_models import PowerWord

        pattern = r'\[POWER_WORDS:\s*([^\]]+)\]'
        all_words = []
        for match in _re.finditer(pattern, full_text, flags=_re.IGNORECASE):
            raw = match.group(1)
            words = [w.strip() for w in raw.split(',') if w.strip()]
            all_words.extend(words)

        if all_words:
            PowerWord.log(student, all_words, session_type='text', subject=subject_name)
            logger.info("Power Words logged for %s: %s", student, all_words)
    except Exception as e:
        logger.warning("_log_session_power_words failed for %s: %s", student, e)



def _extract_session_summary_payload(text):
    if not text:
        return None
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except Exception:
        return None
    if isinstance(payload, dict) and isinstance(payload.get('session_summary'), dict):
        return payload
    return None


def _strip_session_summary_block(text):
    if not text:
        return text
    # Strip summary block
    text = re.sub(r"\n?```json\s*\{.*?\}\s*```\s*$", "", text, flags=re.DOTALL).strip()
    return text

def _strip_suggested_responses_block(text):
    if not text:
        return text
    # Strip suggested responses XML block
    return re.sub(r"\n?<suggested_responses>.*?</suggested_responses>\s*$", "", text, flags=re.DOTALL).strip()


def _strip_internal_control_tokens(text):
    """Remove internal control tokens from assistant-visible text.

    Includes complete tags and partial/malformed fragments that can leak during
    streaming truncation (e.g. "[AWARD_").
    """
    if not text:
        return text
    cleaned = str(text)
    # Complete internal tags.
    cleaned = re.sub(r'\[AWARD_XP:\s*\d+\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[DRAW:\s*.*?\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[POWER_WORDS:\s*[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[LESSON_STATE:\s*[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[VOCAB_LEVEL:\s*\d\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[MOOD:\s*\w+\]', '', cleaned, flags=re.IGNORECASE)
    # Partial/malformed tags (stream cut-off).
    cleaned = re.sub(r'\[AWARD_[^\]\n]*(?:\]|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[LESSON_[^\]\n]*(?:\]|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[VOCAB_[^\]\n]*(?:\]|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[MOOD_[^\]\n]*(?:\]|$)', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _notify_parents_if_critical_misconception_uncleared(student, session, payload):
    session_summary = payload.get('session_summary', {}) if isinstance(payload, dict) else {}
    uncleared_flag = bool(session_summary.get('critical_misconception_uncleared'))
    uncleared = session_summary.get('uncleared_critical_misconceptions') or []

    if isinstance(uncleared, str):
        uncleared = [uncleared]
    elif not isinstance(uncleared, list):
        uncleared = []

    if not uncleared_flag and not uncleared:
        return

    marker = 'critical_misconception_parent_notified'
    existing_markers = session.topics_discussed if isinstance(session.topics_discussed, list) else []
    if marker in existing_markers:
        return

    try:
        from parents.models import Parent
        from announcements.models import Notification

        parents = Parent.objects.select_related('user').filter(children=student)
        parent_users = [parent.user for parent in parents if parent.user_id]
        if not parent_users:
            return

        topic = session_summary.get('topic') or 'AI Tutor lesson'
        unresolved_text = ', '.join(str(item) for item in uncleared[:3]) if uncleared else 'critical misconception'
        msg = (
            f"⚠️ AI Tutor alert: {student.user.get_full_name()} has an unresolved critical misconception "
            f"in {topic} ({unresolved_text})."
        )

        Notification.objects.bulk_create([
            Notification(
                recipient=user,
                message=msg,
                alert_type='general',
            )
            for user in parent_users
        ], ignore_conflicts=True)

        existing_markers.append(marker)
        session.topics_discussed = existing_markers
        session.save(update_fields=['topics_discussed'])
    except Exception:
        return

@login_required
def ai_tutor(request):
    """AI Tutor chat interface for students"""
    from .ai_tutor import get_active_ai_model, get_active_ai_provider, get_student_schedule_data

    student, subjects, error_message = _get_student_tutor_context(
        request.user,
        getattr(request, 'tenant', None),
    )
    if error_message:
        messages.error(request, error_message)
        return redirect('dashboard')

    # Get recent sessions
    from .models import TutorSession
    recent_sessions = (
        TutorSession.objects.filter(student=student)
        .select_related('subject')
        .order_by('-started_at')[:20]
    )

    selected_session = None
    selected_session_id = request.GET.get('session')
    if selected_session_id:
        selected_session = TutorSession.objects.filter(
            student=student,
            id=selected_session_id,
        ).first()

    latest_session = recent_sessions.first()
    active_session = selected_session or latest_session
    initial_messages = []
    initial_subject_id = None

    if active_session:
        initial_messages = []
        for message in active_session.messages.order_by('created_at'):
            if message.role in ['user', 'assistant']:
                content = message.content
                if message.role == 'assistant':
                    content = _strip_session_summary_block(content)
                    content = _strip_internal_control_tokens(content)
                initial_messages.append({'role': message.role, 'content': content})

        if active_session.subject_id:
            initial_subject_id = active_session.subject_id

    # Get Gamification Profile
    from .gamification_models import StudentXP
    xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    
    # Calculate progress to next level
    xp_for_current_level = (xp_profile.level - 1) * 100
    xp_for_next_level = xp_profile.level * 100
    xp_in_level = xp_profile.total_xp - xp_for_current_level
    level_progress = (xp_in_level / 100) * 100
    if level_progress > 100: level_progress = 100

    ai_tutor_bootstrap = {
        'session_id': active_session.id if active_session else None,
        'messages': initial_messages,
        'subject_id': initial_subject_id,
        'active_ai_model': get_active_ai_model(),
        'active_ai_provider': get_active_ai_provider(),
        'student_xp': {
            'level': xp_profile.level,
            'total_xp': xp_profile.total_xp,
            'progress': level_progress,
            'streak': xp_profile.current_streak
        }
    }

    # Get student schedule for after-school auto-prompt
    schedule_data = get_student_schedule_data(student)
    
    context = {
        'student': student,
        'subjects': subjects,
        'recent_sessions': recent_sessions,
        'selected_session_id': str(active_session.id) if active_session else '',
        'initial_messages': initial_messages,
        'initial_subject_id': initial_subject_id,
        'active_ai_model': get_active_ai_model(),
        'active_ai_provider': get_active_ai_provider(),
        'ai_tutor_bootstrap': ai_tutor_bootstrap,
        'schedule_data': schedule_data,
    }
    
    return render(request, 'academics/ai_tutor.html', context)



def _process_xp_awards(student, full_text):
    """
    Scan assistant response for [AWARD_XP: <amount>] tokens 
    and update student's Gamification profile.
    """
    try:
        xp_pattern = r'\[AWARD_XP:\s*(\d+)\]'
        matches = re.finditer(xp_pattern, full_text)
        
        total_awarded = 0
        for match in matches:
            try:
                amount = int(match.group(1))
                total_awarded += amount
            except ValueError:
                pass
                
        if total_awarded > 0:
            from .gamification_models import StudentXP, check_and_unlock_achievements
            profile, created = StudentXP.objects.get_or_create(student=student)
            leveled_up = profile.add_xp(total_awarded)
            profile.update_streak()
            check_and_unlock_achievements(student, profile)
            if leveled_up:
                try:
                    from announcements.models import Notification
                    Notification.objects.create(
                        recipient=student.user,
                        message=f'⭐ Level Up! You reached Level {profile.level} — keep learning with Aura!',
                        alert_type='general',
                        link='../../students/aura-portfolio/',
                    )
                except Exception:
                    pass
            logger.info("Awarded %d XP to %s. New Level: %d", total_awarded, student, profile.level)
            return total_awarded, leveled_up
    except Exception as e:
        logger.error("Gamification error: %s", e)
        
    return 0, False


def _save_lesson_state(student, lesson_state, updated_by='text'):
    """
    Persist the student's current Lesson State to AuraSessionState.
    Safe to call on every response — uses get_or_create + update_fields.
    """
    try:
        from .gamification_models import AuraSessionState
        state, _ = AuraSessionState.objects.get_or_create(student=student)
        state.lesson_state = lesson_state
        state.updated_by = updated_by
        state.save(update_fields=['lesson_state', 'updated_by', 'updated_at'])
    except Exception as e:
        logger.warning('_save_lesson_state failed: %s', e)


@login_required
def aura_session_state(request):
    """
    Shared State Manager endpoint — Redux-style single source of truth.
    Both text-chat (ai_tutor.html) and voice (aura_voice.html) read/write here.

    GET  → returns the student's current state as JSON
    PATCH → updates one or more fields and returns the updated state
    """
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)

    from .gamification_models import AuraSessionState
    try:
        from students.models import Student
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)

    state, _ = AuraSessionState.objects.get_or_create(
        student=student,
        defaults={'vocab_level': 3},
    )

    if request.method == 'GET':
        return JsonResponse(state.as_dict())

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        changed = []
        if 'lesson_state' in body:
            val = str(body['lesson_state']).strip().upper()
            if val:
                state.lesson_state = val
                changed.append('lesson_state')
        if 'vocab_level' in body:
            try:
                v = int(body['vocab_level'])
                state.vocab_level = max(1, min(v, 6))
                changed.append('vocab_level')
            except (ValueError, TypeError):
                pass
        if 'mood' in body:
            val = str(body['mood']).strip().lower()
            allowed = {c[0] for c in AuraSessionState.MOOD_CHOICES}
            if val in allowed:
                state.mood = val
                changed.append('mood')
        if 'updated_by' in body:
            val = str(body['updated_by']).strip().lower()
            if val in ('text', 'voice'):
                state.updated_by = val
                changed.append('updated_by')
        if changed:
            state.save(update_fields=changed + ['updated_at'])
        return JsonResponse(state.as_dict())

    return JsonResponse({'error': 'GET or PATCH only'}, status=405)


@login_required
def ai_tutor_chat(request):
    from .ai_tutor import stream_tutor_response
    from .models import TutorSession, TutorMessage, Subject
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        student, subjects, error_message = _get_student_tutor_context(
            request.user,
            getattr(request, 'tenant', None),
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)

        data = json.loads(request.body)
        messages_list = data.get('messages', [])
        subject_id = data.get('subject_id')
        session_id = data.get('session_id')
        requested_model = data.get('model') or None

        if not isinstance(messages_list, list):
            return JsonResponse({'error': 'Invalid messages payload'}, status=400)

        allowed_subject_ids = {str(subject.id) for subject in subjects}
        
        # Get or create session
        if session_id:
            session = TutorSession.objects.get(id=session_id, student=student)
            # Backfill title if missing and subject is now known
            if not session.title and session.subject_id:
                session.title = session.subject.name
                session.save(update_fields=['title'])
        else:
            subject_pk = None
            session_title = 'General Chat'
            if subject_id:
                if str(subject_id) not in allowed_subject_ids:
                    return JsonResponse({'error': 'Invalid subject selected'}, status=400)
                subject_pk = subject_id
                matched = next((s for s in subjects if str(s.id) == str(subject_id)), None)
                if matched:
                    session_title = matched.name
            session = TutorSession.objects.create(
                student=student,
                subject_id=subject_pk,
                title=session_title,
            )
        
        # Save user message
        if messages_list and isinstance(messages_list[-1], dict) and messages_list[-1].get('role') == 'user':
            try:
                TutorMessage.objects.create(
                    session=session,
                    role='user',
                    content=messages_list[-1].get('content', '')
                )
                session.message_count += 1
                session.save()
            except (ProgrammingError, Exception) as _e:
                logger.warning('TutorMessage user-save failed (schema may be missing): %s', _e)
        
        # Get subject context
        subject = None
        if subject_id:
            if str(subject_id) not in allowed_subject_ids:
                return JsonResponse({'error': 'Invalid subject selected'}, status=400)
            subject = Subject.objects.get(id=subject_id)

        def _stream_and_persist():
            assistant_chunks = []
            for chunk in stream_tutor_response(messages_list, student, subject, model=requested_model):
                if chunk.startswith('data: '):
                    payload = chunk[6:].strip()
                    if payload and payload != '[DONE]':
                        try:
                            parsed = json.loads(payload)
                            content_piece = parsed.get('content')
                            if content_piece:
                                assistant_chunks.append(content_piece)
                        except Exception:
                            pass
                yield chunk

            full_assistant_message = ''.join(assistant_chunks).strip()
            if full_assistant_message:
                # Strip internal blocks (suggestions, summary) before saving to history
                visible_message = _strip_session_summary_block(full_assistant_message)
                visible_message = _strip_suggested_responses_block(visible_message)
                visible_message = _strip_internal_control_tokens(visible_message)
                
                # Process Gamification (XP Awards)
                _process_xp_awards(student, full_assistant_message)

                # ── Always update study streak (even when no XP was awarded) ────
                try:
                    from .gamification_models import StudentXP as _SXP
                    _xp_s, _ = _SXP.objects.get_or_create(student=student)
                    _prev_streak = _xp_s.current_streak
                    _prev_date = _xp_s.last_activity_date
                    _xp_s.update_streak()
                    # Streak-break notification — fires once when student returns after gap
                    if _prev_date and _prev_streak > 1:
                        from django.utils import timezone as _tz
                        _gap = (_tz.now().date() - _prev_date).days
                        if _gap > 1:
                            try:
                                from announcements.models import Notification as _Notif
                                already = _Notif.objects.filter(
                                    recipient=student.user,
                                    message__startswith='🔥 Welcome back!',
                                    created_at__date=_tz.now().date(),
                                ).exists()
                                if not already:
                                    _Notif.objects.create(
                                        recipient=student.user,
                                        message=f'🔥 Welcome back! Your {_prev_streak}-day streak was broken. Start a new one today!',
                                        alert_type='general',
                                    )
                            except Exception:
                                pass
                except Exception as _se:
                    logger.warning('streak update failed: %s', _se)

                # ── Shared State Manager: persist LESSON_STATE token ──────────
                _ls = re.search(r'\[LESSON_STATE:\s*([\w_]+)\]', full_assistant_message, re.I)
                if _ls:
                    _save_lesson_state(student, _ls.group(1).strip().upper(), updated_by='text')

                # ── Shared State Manager: persist VOCAB_LEVEL token ──────────
                _vl = re.search(r'\[VOCAB_LEVEL:\s*(\d)\]', full_assistant_message, re.I)
                if _vl:
                    try:
                        from .gamification_models import AuraSessionState
                        _aura_state, _ = AuraSessionState.objects.get_or_create(student=student)
                        _aura_state.vocab_level = max(1, min(int(_vl.group(1)), 6))
                        _aura_state.updated_by = 'text'
                        _aura_state.save(update_fields=['vocab_level', 'updated_by', 'updated_at'])
                    except Exception as e:
                        logger.warning('vocab_level persist failed: %s', e)

                # ── Shared State Manager: persist MOOD token ────────────────
                _md = re.search(r'\[MOOD:\s*(\w+)\]', full_assistant_message, re.I)
                if _md:
                    _mood_val = _md.group(1).strip().lower()
                    _allowed_moods = {'positive', 'neutral', 'negative', 'frustrated'}
                    if _mood_val in _allowed_moods:
                        try:
                            from .gamification_models import AuraSessionState
                            _aura_state, _ = AuraSessionState.objects.get_or_create(student=student)
                            _aura_state.mood = _mood_val
                            _aura_state.updated_by = 'text'
                            _aura_state.save(update_fields=['mood', 'updated_by', 'updated_at'])
                        except Exception as e:
                            logger.warning('mood persist failed: %s', e)

                # ── Session auto-title from [SESSION_TITLE: X] token ────────
                _st = re.search(r'\[SESSION_TITLE:\s*([^\]]+)\]', full_assistant_message, re.I)
                if _st and session.title in ('General Chat', 'Voice Session', ''):
                    _title_val = _st.group(1).strip()[:200]
                    if _title_val:
                        session.title = _title_val
                        session.save(update_fields=['title'])

                try:
                    TutorMessage.objects.create(
                        session=session,
                        role='assistant',
                        content=visible_message or full_assistant_message
                    )
                    session.message_count += 1
                    session.save(update_fields=['message_count'])
                except (ProgrammingError, Exception) as _e:
                    logger.warning('TutorMessage assistant-save failed (schema may be missing): %s', _e)

                summary_payload = _extract_session_summary_payload(full_assistant_message)
                if summary_payload:
                    _notify_parents_if_critical_misconception_uncleared(
                        student,
                        session,
                        summary_payload,
                    )
                    # ── Continuous Context Awareness: Persist to LearnerMemory ──
                    _persist_to_learner_memory(student, summary_payload)
                    # ── Spaced-rep review reminders ──────────────────────
                    _check_and_send_review_reminders(student)

                # ── Power Word Tracking ──────────────────────────────────────
                _log_session_power_words(student, full_assistant_message, subject_name=subject.name if subject else '')
        
        # Stream response
        response = StreamingHttpResponse(
            _stream_and_persist(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['X-Session-Id'] = str(session.id)
        
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@login_required
def ai_tutor_new_session(request):
    """Create a new AI Tutor session for the current student."""
    from .models import TutorSession

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    try:
        student, subjects, error_message = _get_student_tutor_context(
            request.user,
            getattr(request, 'tenant', None),
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)

        data = json.loads(request.body or '{}')
        subject_id = data.get('subject_id')

        allowed_subject_ids = {str(subject.id) for subject in subjects}
        subject_pk = None
        if subject_id:
            if str(subject_id) not in allowed_subject_ids:
                return JsonResponse({'error': 'Invalid subject selected'}, status=400)
            subject_pk = subject_id

        session_title = 'General Chat'
        if subject_pk:
            matched = next((s for s in subjects if str(s.id) == str(subject_pk)), None)
            if matched:
                session_title = matched.name
        session = TutorSession.objects.create(
            student=student,
            subject_id=subject_pk,
            title=session_title,
        )

        return JsonResponse({'session_id': str(session.id), 'title': session.title})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def rename_tutor_session(request, session_id):
    """PATCH a tutor session title. The authenticated student must own the session."""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'PATCH only'}, status=405)
    try:
        from .models import TutorSession
        student, _subjects, error_message = _get_student_tutor_context(
            request.user, getattr(request, 'tenant', None)
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)
        session = TutorSession.objects.get(id=session_id, student=student)
        data = json.loads(request.body)
        title = str(data.get('title', '')).strip()[:200]
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        session.title = title
        session.save(update_fields=['title'])
        return JsonResponse({'ok': True, 'title': session.title})
    except TutorSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def generate_practice(request):
    """Generate practice questions"""
    from .ai_tutor import generate_practice_questions
    from .models import Subject, PracticeQuestionSet
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        student, subjects, error_message = _get_student_tutor_context(
            request.user,
            getattr(request, 'tenant', None),
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)

        data = json.loads(request.body)
        
        subject_id = data.get('subject_id')
        topic = data.get('topic', '')
        difficulty = data.get('difficulty', 'medium')
        count = data.get('count', 5)
        
        allowed_subject_ids = {str(subject.id) for subject in subjects}
        if str(subject_id) not in allowed_subject_ids:
            return JsonResponse({'error': 'Invalid subject selected'}, status=400)

        subject = Subject.objects.get(id=subject_id)
        
        # Generate questions
        result = generate_practice_questions(subject, topic, difficulty, count)
        
        if 'error' not in result:
            # Save question set
            practice_set = PracticeQuestionSet.objects.create(
                student=student,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                questions=result
            )
            result['practice_set_id'] = practice_set.id
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def scheme_topic_suggest(request):
    """Return scheme-of-work topics for a given subject (student's current class).
    GET ?subject_id=<int>  → {topics: [...], suggested: "..."} """
    from .models import SchemeOfWork, ClassSubject, AcademicYear
    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'topics': [], 'suggested': ''})

    # Resolve student's class
    student_class = None
    if request.user.user_type == 'student':
        try:
            from students.models import Student
            student = Student.objects.select_related('current_class').get(user=request.user)
            student_class = student.current_class
        except Exception:
            pass

    current_year = AcademicYear.objects.filter(is_current=True).first()
    qs = SchemeOfWork.objects.filter(class_subject__subject_id=subject_id)
    if student_class:
        qs = qs.filter(class_subject__class_name=student_class)
    if current_year:
        qs = qs.filter(academic_year=current_year)

    topics = []
    for scheme in qs[:3]:
        topics.extend(scheme.get_topics())

    # Deduplicate (preserve order)
    seen = set()
    unique_topics = [t for t in topics if t and not (t in seen or seen.add(t))]
    suggested = unique_topics[0] if unique_topics else ''
    return JsonResponse({'topics': unique_topics, 'suggested': suggested})


@login_required
def explain_concept(request):
    """Get AI explanation of a concept"""
    from .ai_tutor import explain_concept as get_explanation
    from .models import Subject
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        student, subjects, error_message = _get_student_tutor_context(
            request.user,
            getattr(request, 'tenant', None),
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)

        data = json.loads(request.body)
        
        subject_id = data.get('subject_id')
        concept = data.get('concept', '')

        allowed_subject_ids = {str(subject.id) for subject in subjects}
        if str(subject_id) not in allowed_subject_ids:
            return JsonResponse({'error': 'Invalid subject selected'}, status=400)
        
        subject = Subject.objects.get(id=subject_id)
        explanation = get_explanation(subject, concept)
        
        return JsonResponse({'explanation': explanation})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@login_required
def tutor_sessions(request):
    """View all tutor sessions"""
    from .models import TutorSession
    
    try:
        student, _subjects, error_message = _get_student_tutor_context(
            request.user,
            getattr(request, 'tenant', None),
        )
        if error_message and request.GET.get('format') != 'json':
            messages.error(request, error_message)
            return redirect('dashboard')
        elif error_message:
             return JsonResponse({'error': error_message}, status=400)

        sessions = (
            TutorSession.objects.filter(student=student)
            .select_related('subject')
            .annotate(
                last_message_at=Max('messages__created_at'),
                total_msgs=Count('messages')
            )
            .order_by('-started_at')
        )
        
        if request.GET.get('format') == 'json':
            data = []
            for s in sessions:
                # Safely handle topics
                topics = s.topics_discussed if isinstance(s.topics_discussed, list) else []
                topic_text = ", ".join([str(t) for t in topics[:2]])
                
                display_title = s.title or (s.subject.name if s.subject else 'General Chat')
                data.append({
                    'id': s.id,
                    'title': display_title,
                    'subject': s.subject.name if s.subject else None,
                    'topic': topic_text,
                    'date': s.started_at.strftime('%b %d, %I:%M %p'),
                    'started_at_iso': s.started_at.isoformat(),
                    'msg_count': s.total_msgs,
                    'is_active': s.ended_at is None
                })
            return JsonResponse({'sessions': data})
        
        context = {
            'sessions': sessions,
        }
        
        return render(request, 'academics/tutor_sessions.html', context)

    except Exception as e:
        if request.GET.get('format') == 'json':
             return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, "Unable to load tutor sessions")
        return redirect('dashboard')


@login_required
def generate_tutor_image(request):
    """Generate whiteboard image using selected model (FLUX or Gemini Nano Banana)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
        image_model = (data.get('image_model') or 'flux-schnell').strip().lower()
        if not prompt:
             return JsonResponse({'error': 'No prompt provided'}, status=400)

        # Google Nano Banana path (Gemini image generation)
        if image_model in ('google-nano-banana', 'nano-banana'):
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_api_key:
                return JsonResponse({'error': 'GEMINI_API_KEY not configured'}, status=500)

            gemini_payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            }

            import urllib.request as _urllib_req
            import urllib.error as _urllib_err

            def _normalize_model_name(name):
                model_name = (name or '').strip()
                if model_name.startswith('models/'):
                    model_name = model_name[len('models/'):]
                return model_name

            def _try_gemini_image_model(model_name):
                model_name = _normalize_model_name(model_name)
                if not model_name:
                    return None, (0, 'empty model name')

                gemini_url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}"
                    f":generateContent?key={gemini_api_key}"
                )
                req = _urllib_req.Request(
                    gemini_url,
                    data=json.dumps(gemini_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST',
                )
                try:
                    with _urllib_req.urlopen(req, timeout=120) as resp:
                        return json.loads(resp.read().decode('utf-8')), None
                except _urllib_err.HTTPError as exc:
                    detail = exc.read().decode('utf-8', errors='ignore') if exc.fp else str(exc)
                    return None, (exc.code, detail)
                except _urllib_err.URLError as exc:
                    return None, (0, str(exc.reason))

            # Candidate model order:
            # 1) explicit env override
            # 2) known image-capable model aliases
            candidates = []
            env_image_model = _normalize_model_name(os.environ.get('GEMINI_IMAGE_MODEL', ''))
            if env_image_model:
                candidates.append(env_image_model)
            candidates.extend([
                'gemini-2.0-flash-preview-image-generation',
                'gemini-2.0-flash-exp-image-generation',
                'gemini-2.5-flash-image-preview',
            ])

            # De-duplicate while preserving order
            seen = set()
            ordered_candidates = []
            for c in candidates:
                key = _normalize_model_name(c)
                if key and key not in seen:
                    seen.add(key)
                    ordered_candidates.append(key)

            gemini_res = None
            chosen_model = None
            probe_errors = []

            for model_name in ordered_candidates:
                result, err = _try_gemini_image_model(model_name)
                if result is not None:
                    gemini_res = result
                    chosen_model = model_name
                    break
                probe_errors.append((model_name, err))

            # If known candidates failed, discover from ListModels and probe image-capable entries.
            if gemini_res is None:
                list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}"
                try:
                    with _urllib_req.urlopen(list_url, timeout=60) as resp:
                        listed = json.loads(resp.read().decode('utf-8'))
                    models = listed.get('models', []) if isinstance(listed, dict) else []
                    discovered = []
                    for m in models:
                        if not isinstance(m, dict):
                            continue
                        name = _normalize_model_name(m.get('name', ''))
                        methods = m.get('supportedGenerationMethods') or []
                        if 'generateContent' not in methods:
                            continue
                        # Prioritize likely image models.
                        lowered = name.lower()
                        if 'image' in lowered:
                            discovered.append(name)

                    for model_name in discovered:
                        result, err = _try_gemini_image_model(model_name)
                        if result is not None:
                            gemini_res = result
                            chosen_model = model_name
                            break
                        probe_errors.append((model_name, err))
                except Exception as list_exc:
                    probe_errors.append(('list_models', (0, str(list_exc))))

            if gemini_res is None:
                compact_errors = []
                for model_name, err in probe_errors[:5]:
                    if not err:
                        continue
                    compact_errors.append(f"{model_name}: {err[0]}")
                return JsonResponse(
                    {
                        'error': 'Nano Banana model unavailable. '
                                 'Set GEMINI_IMAGE_MODEL to a valid image-capable Gemini model.',
                        'details': '; '.join(compact_errors) if compact_errors else 'No compatible Gemini image model found.',
                    },
                    status=502,
                )

            inline_data = None
            try:
                for part in gemini_res.get('candidates', [{}])[0].get('content', {}).get('parts', []):
                    if isinstance(part, dict) and (part.get('inlineData') or part.get('inline_data')):
                        inline_data = part.get('inlineData') or part.get('inline_data')
                        break
            except Exception:
                inline_data = None

            if not inline_data:
                return JsonResponse({'error': 'Nano Banana returned no image data'}, status=502)

            b64 = inline_data.get('data') or ''
            mime = inline_data.get('mimeType') or inline_data.get('mime_type') or 'image/png'
            if not b64:
                return JsonResponse({'error': 'Nano Banana returned empty image payload'}, status=502)

            return JsonResponse({'image_url': f'data:{mime};base64,{b64}', 'model_used': chosen_model or 'google-nano-banana'})

        # Default FLUX path
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            return JsonResponse({'error': 'HF_TOKEN not configured'}, status=500)

        client = InferenceClient(token=hf_token)
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
            num_inference_steps=4
        )

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return JsonResponse({'image_url': f"data:image/png;base64,{img_str}", 'model_used': 'flux-schnell'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def timetable_conflicts(request):
    """Detect teacher double-bookings and class overlaps in the timetable."""
    if request.user.user_type not in ['admin', 'teacher']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    academic_year = AcademicYear.objects.filter(is_current=True).first()

    # Fetch all timetable entries with related data
    entries = (
        Timetable.objects
        .select_related(
            'class_subject__teacher__user',
            'class_subject__class_name',
            'class_subject__subject',
        )
        .filter(class_subject__class_name__academic_year=academic_year)
        .order_by('day', 'start_time')
    )

    DAY_NAMES = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

    def times_overlap(s1, e1, s2, e2):
        """Return True if (s1,e1) and (s2,e2) overlap (exclusive end)."""
        return s1 < e2 and s2 < e1

    teacher_conflicts = []
    class_conflicts = []
    checked_pairs = set()

    entry_list = list(entries)

    for i, a in enumerate(entry_list):
        for j in range(i + 1, len(entry_list)):
            b = entry_list[j]
            if a.day != b.day:
                continue  # different day — no conflict possible
            if not times_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                continue  # no time overlap

            pair_key = (min(a.id, b.id), max(a.id, b.id))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            a_teacher = a.class_subject.teacher
            b_teacher = b.class_subject.teacher
            a_class   = a.class_subject.class_name
            b_class   = b.class_subject.class_name

            # Teacher in two places at once
            if a_teacher and b_teacher and a_teacher == b_teacher and a_class != b_class:
                teacher_conflicts.append({
                    'day': DAY_NAMES.get(a.day, a.day),
                    'time': f"{a.start_time.strftime('%H:%M')} – {a.end_time.strftime('%H:%M')}",
                    'teacher': a_teacher.user.get_full_name() if a_teacher.user else str(a_teacher),
                    'class_a': str(a_class),
                    'subject_a': str(a.class_subject.subject),
                    'class_b': str(b_class),
                    'subject_b': str(b.class_subject.subject),
                })

            # Same class double-booked
            if a_class == b_class:
                class_conflicts.append({
                    'day': DAY_NAMES.get(a.day, a.day),
                    'time': f"{a.start_time.strftime('%H:%M')} – {a.end_time.strftime('%H:%M')}",
                    'class_name': str(a_class),
                    'subject_a': str(a.class_subject.subject),
                    'teacher_a': a_teacher.user.get_full_name() if a_teacher and a_teacher.user else 'N/A',
                    'subject_b': str(b.class_subject.subject),
                    'teacher_b': b_teacher.user.get_full_name() if b_teacher and b_teacher.user else 'N/A',
                })

    context = {
        'teacher_conflicts': teacher_conflicts,
        'class_conflicts': class_conflicts,
        'total_conflicts': len(teacher_conflicts) + len(class_conflicts),
        'academic_year': academic_year,
    }
    return render(request, 'academics/timetable_conflicts.html', context)


# ---------------------------------------------------------------------------
# Help Chat API  (authenticated, role-aware AI assistant)
# ---------------------------------------------------------------------------

HELP_ROLE_PROMPTS = {
    'admin': (
        "You help school admins use the School Management System.\n"
        "Key sections they manage:\n"
        "- Students: enroll, edit, import via CSV, promote, view report cards\n"
        "- Teachers: add, edit, assign classes\n"
        "- Classes & Subjects: create classes, assign subjects and class teachers\n"
        "- Finance: fee structures, assign fees to students, record payments, send reminders\n"
        "- Attendance: mark daily attendance per class\n"
        "- Timetable: build and view weekly schedules\n"
        "- Homework: create assignments with AI-generated questions\n"
        "- Announcements: post notices to all or specific roles\n"
        "- Analytics: enrollment, fee collection, attendance heatmap, grade averages\n"
        "- Settings: school name, logo, term dates, academic year\n"
        "- AI Tools: Aura AI tutor for students, teacher AI lesson assistant\n"
    ),
    'teacher': (
        "You help teachers use the School Management System.\n"
        "Key features available:\n"
        "- Enter Grades: input class scores and exam scores; system auto-calculates totals\n"
        "- My Classes: see assigned subjects and classes\n"
        "- Attendance: mark daily attendance for your classes\n"
        "- Lesson Plans: create, edit, print and AI-generate lesson plans\n"
        "- AI Command Centre: Aura T – AI that helps plan lessons and generate assignments\n"
        "- Homework: create homework with AI-generated questions for students\n"
        "- Timetable: view the school timetable\n"
        "- Schedule: view your personal teaching schedule\n"
        "- Duty Roster: view duty week assignments\n"
        "- Curriculum Library: store and retrieve teaching resources\n"
        "- Analytics: view class performance insights and at-risk students\n"
    ),
    'student': (
        "You help students use the School Management System.\n"
        "Key features available:\n"
        "- Dashboard: quick overview of grades, attendance, upcoming homework\n"
        "- Report Card: view term report cards\n"
        "- Schedule: view your personal class timetable\n"
        "- AI Tutor (Aura): chat with an AI tutor for help with subjects\n"
        "- Aura Arena: competitive AI quiz battle with classmates\n"
        "- Aura Voice: voice-based AI learning assistant\n"
        "- Homework: view and submit assigned homework\n"
        "- Announcements: read school notices\n"
        "- Messages: communicate with teachers and staff\n"
    ),
    'parent': (
        "You help parents use the School Management System.\n"
        "Key features available:\n"
        "- My Children: view profile, attendance, and grades for each child\n"
        "- Fees: check fee balances, payment history, and download receipts\n"
        "- Report Cards: view and print your child's report cards\n"
        "- Homework: see homework assigned to your children\n"
        "- Announcements: read school notices\n"
        "- Messages: contact teachers or school administration\n"
    ),
}

HELP_FALLBACK_FAQ = [
    (['grade', 'score', 'result', 'mark'], "Grades are entered by teachers under **Enter Grades**. Each student gets a class score and exam score; the system calculates the total and assigns a grade automatically."),
    (['attendance', 'absent', 'present'], "Attendance is marked daily per class. Go to **Mark Attendance**, select the class and date, then mark each student's status."),
    (['fee', 'payment', 'balance', 'receipt'], "Go to **Finance → Manage Fees** to view fee structures, assign fees to students, and record payments. Students/parents can see balances under their portal."),
    (['report card', 'report'], "Report cards are generated per student per term. Go to **Students → Report Card** and select the student and term."),
    (['timetable', 'schedule', 'period'], "The timetable is managed under **Academics → Timetable**. Teachers can view their personal schedule under **My Schedule**."),
    (['homework', 'assignment', 'task'], "Homework is created under the **Homework** section. You can add questions manually or use AI to generate them. Students see assigned work in their portal."),
    (['password', 'login', 'access', 'sign in'], "Passwords can be changed under your profile (top-right menu → Change Password). Admins can reset any user's password from **Manage Users**."),
    (['class', 'subject', 'enroll'], "Classes and subjects are managed under **Academics → Manage Classes** and **Manage Subjects**. Assign subjects to classes and teachers via **Class Subjects**."),
    (['announcement', 'notice', 'notification'], "Post announcements under **Announcements → Manage**. Set the audience to All, Admin, Teachers, Students, or Parents."),
    (['setting', 'logo', 'school name', 'term', 'academic year'], "School settings (name, logo, motto, term dates) are under **Academics → School Settings**."),
]


@login_required
def help_page(request):
    """Dedicated help page with assistant chat and quick guidance."""
    return render(request, 'academics/help_page.html')


@login_required
def help_chat_api(request):
    """Role-aware AI help assistant for all authenticated users."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # Rate limiting: 30 requests per minute per user
    from django.core.cache import cache
    schema = connection.tenant.schema_name
    rate_key = f"{schema}:help_chat:{request.user.pk}"
    hits = cache.get(rate_key, 0)
    if hits >= 30:
        return JsonResponse({'error': 'Too many requests. Please wait a moment.'}, status=429)
    cache.set(rate_key, hits + 1, 60)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    question = (payload.get('question') or '').strip()
    history = payload.get('history') or []  # [{role, content}, ...]

    if not question:
        return JsonResponse({'answer': 'Please ask a question and I\'ll do my best to help!'})

    user_role = getattr(request.user, 'user_type', 'admin')
    role_context = HELP_ROLE_PROMPTS.get(user_role, HELP_ROLE_PROMPTS['admin'])

    try:
        school_info = SchoolInfo.objects.first()
        school_name = school_info.name if school_info else (request.tenant.name if hasattr(request, 'tenant') else 'your school')
    except Exception:
        school_name = 'your school'

    system_prompt = (
        f"You are the friendly help assistant for {school_name}'s School Management System. "
        f"Your job is to guide users step-by-step.\n\n"
        f"{role_context}\n"
        "Rules:\n"
        "- Be concise (2–4 sentences max unless a step-by-step list is needed).\n"
        "- Use **bold** for menu names and button labels.\n"
        "- If unsure of a school-specific detail, say so and point to the relevant section.\n"
        "- Never make up data about the school."
    )

    from django.conf import settings as _dj_settings
    api_key = getattr(_dj_settings, 'OPENAI_API_KEY', '') or os.environ.get('OPENAI_API_KEY', '')

    if api_key:
        try:
            from academics.ai_tutor import get_openai_chat_model, OPENAI_CHAT_COMPLETIONS_URL
            import urllib.request as _urllib_req
            messages = [{"role": "system", "content": system_prompt}]
            # Include last 6 turns of history to keep context
            for turn in history[-6:]:
                if turn.get('role') in ('user', 'assistant') and turn.get('content'):
                    messages.append({"role": turn['role'], "content": str(turn['content'])[:500]})
            messages.append({"role": "user", "content": question})

            req_payload = json.dumps({
                "model": get_openai_chat_model(),
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.4,
            }).encode('utf-8')

            req = _urllib_req.Request(
                OPENAI_CHAT_COMPLETIONS_URL,
                data=req_payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            answer = result['choices'][0]['message']['content'].strip()
            return JsonResponse({'answer': answer})
        except Exception as e:
            logger.warning("help_chat_api OpenAI error: %s", e)
            # fall through to FAQ

    # --- Static FAQ fallback ---
    q_lower = question.lower()
    for keywords, response in HELP_FALLBACK_FAQ:
        if any(k in q_lower for k in keywords):
            return JsonResponse({'answer': response})

    return JsonResponse({'answer': (
        "I'm not sure about that specific question. Try checking the relevant section in the "
        "navigation menu, or ask your school administrator for assistance."
    )})


@login_required
def assign_practice_as_homework(request, practice_set_id):
    """
    Convert an AI-generated PracticeQuestionSet into a Homework record.
    POST body: { "due_date": "YYYY-MM-DD" }   (optional — defaults to 7 days from now)
    Returns: { "ok": true, "homework_id": <id>, "title": "..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        student, _subjects, error_message = _get_student_tutor_context(
            request.user, getattr(request, 'tenant', None)
        )
        if error_message:
            return JsonResponse({'error': error_message}, status=403)

        from .tutor_models import PracticeQuestionSet
        practice_set = get_object_or_404(PracticeQuestionSet, id=practice_set_id, student=student)

        # Resolve the subject teacher for this student's class
        from .models import ClassSubject
        class_subject = ClassSubject.objects.filter(
            class_name=student.current_class,
            subject=practice_set.subject,
        ).select_related('teacher').first()

        teacher = class_subject.teacher if class_subject else None
        if not teacher:
            return JsonResponse({
                'error': f'No teacher found for {practice_set.subject.name} in your class. Ask your teacher to assign homework directly.'
            }, status=400)

        # Parse due_date from request
        import datetime
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
            due_date_str = body.get('due_date', '')
            due_date = datetime.date.fromisoformat(due_date_str) if due_date_str else None
        except Exception:
            due_date = None
        if not due_date:
            due_date = timezone.now().date() + datetime.timedelta(days=7)

        # Build homework title
        title = f"AI Practice: {practice_set.topic or practice_set.subject.name}"
        if practice_set.difficulty:
            title += f" ({practice_set.difficulty.title()})"

        from homework.models import Homework, Question, Choice
        homework = Homework.objects.create(
            title=title[:200],
            description=(
                f"AI-generated practice set from Aura Tutor.\n"
                f"Subject: {practice_set.subject.name}\n"
                f"Topic: {practice_set.topic}\n"
                f"Difficulty: {practice_set.get_difficulty_display() if hasattr(practice_set, 'get_difficulty_display') else practice_set.difficulty.title()}"
            ),
            teacher=teacher,
            subject=practice_set.subject,
            target_class=student.current_class,
            due_date=due_date,
        )

        # Create Question + Choice rows from the JSONField
        questions_data = practice_set.questions
        if isinstance(questions_data, dict):
            questions_data = questions_data.get('questions', [])

        for q_data in (questions_data or []):
            if not isinstance(q_data, dict):
                continue
            q_type_raw = str(q_data.get('type', 'mcq')).lower()
            q_type = 'mcq' if 'choice' in q_type_raw or 'mcq' in q_type_raw else (
                'essay' if 'essay' in q_type_raw else 'short'
            )
            question = Question.objects.create(
                homework=homework,
                text=str(q_data.get('question', ''))[:2000],
                question_type=q_type,
                correct_answer=str(q_data.get('correct_answer', '') or q_data.get('answer', ''))[:500],
                points=1,
                dok_level=2,
            )
            # For MCQ, create choices
            options = q_data.get('options') or []
            correct_raw = str(q_data.get('correct_answer', '')).strip().upper()
            for idx, opt in enumerate(options):
                label = chr(65 + idx)  # A, B, C, D …
                Choice.objects.create(
                    question=question,
                    text=str(opt)[:200],
                    is_correct=(label == correct_raw or str(opt).strip() == correct_raw),
                )

        return JsonResponse({
            'ok': True,
            'homework_id': homework.id,
            'title': homework.title,
            'due_date': due_date.isoformat(),
        })

    except Exception as e:
        logger.error('assign_practice_as_homework error: %s', e, exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
