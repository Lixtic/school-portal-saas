from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
import datetime
from django.db import connection, ProgrammingError
from django.db.models import Q, Count
from accounts.models import User
from announcements.models import Announcement
from .models import Activity, GalleryImage, SchoolInfo, Class, Timetable, ClassSubject, Resource, AcademicYear
from .forms import SchoolInfoForm, GalleryImageForm, ResourceForm

def about_us(request):
    """Public about us page"""
    school_info = SchoolInfo.objects.first()
    activities = Activity.objects.filter(is_active=True).order_by('-date')[:5]
    
    context = {
        'school_info': school_info,
        'recent_activities': activities,
    }
    return render(request, 'academics/about_us.html', context)

def apply_admission(request):
    """Public admission application page"""
    school_info = SchoolInfo.objects.first()
    
    if request.method == 'POST':
        # Handle admission form submission
        messages.success(request, 'Thank you for your interest! We will contact you soon.')
        return redirect('academics:apply_admission')
    
    context = {
        'school_info': school_info,
    }
    return render(request, 'academics/apply_admission.html', context)

@login_required
def manage_classes(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all classes with counts
    classes = Class.objects.select_related('academic_year', 'class_teacher', 'class_teacher__user').annotate(
        student_count=Count('student')
    ).order_by('-academic_year__start_date', 'name')
    
    context = {
        'classes': classes,
        'current_year': current_year
    }
    return render(request, 'academics/manage_classes.html', context)

@login_required
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
def delete_resource(request, resource_id):
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


def gallery_view(request):
    images = GalleryImage.objects.all()
    
    # Filter by category if requested
    category = request.GET.get('category')
    if category and category != 'all':
        images = images.filter(category=category)
        
    categories = GalleryImage.CATEGORY_CHOICES
        
    context = {
        'images': images,
        'categories': categories,
        'current_category': category
    }
    return render(request, 'gallery.html', context)



@login_required
def manage_activities(request):
	if request.user.user_type != 'admin':
		messages.error(request, 'Access denied. Admins only.')
		return redirect('dashboard')

	staff_queryset = User.objects.filter(user_type__in=['admin', 'teacher']).order_by('first_name', 'last_name')

	# Admins see all activities
	activities = Activity.objects.all()

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
        form = SchoolInfoForm(request.POST, request.FILES, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, 'School settings updated successfully')
            return redirect('academics:school_settings')
    else:
        form = SchoolInfoForm(instance=info)
        
    return render(request, 'academics/school_settings.html', {'form': form})


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

