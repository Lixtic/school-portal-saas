from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from parents.models import Parent, Homework
from .forms import ParentForm
from accounts.models import User

from students.models import Student, Attendance, Grade

@login_required
def parent_children(request):
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    try:
        parent = Parent.objects.get(user=request.user)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found. Please contact administrator.')
        return redirect('dashboard')
    
    # Get all children with additional stats
    children = parent.children.all()
    children_data = []
    
    for child in children:
        # Calculate attendance percentage
        total_attendance = Attendance.objects.filter(student=child).count()
        present_count = Attendance.objects.filter(student=child, status='present').count()
        
        attendance_percentage = 0
        if total_attendance > 0:
            attendance_percentage = round((present_count / total_attendance) * 100, 2)
        
        # Get grade count
        grade_count = Grade.objects.filter(student=child).count()
        
        child.attendance_percentage = attendance_percentage
        child.grade_count = grade_count
        children_data.append(child)
    
    return render(request, 'parents/my_children.html', {'children': children_data})


@login_required
def child_details(request, student_id):
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    try:
        parent = Parent.objects.get(user=request.user)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found')
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    
    # Verify this is the parent's child
    if student not in parent.children.all():
        messages.error(request, 'Access denied - This is not your child')
        return redirect('parents:my_children')
    
    # Get attendance records
    attendances = Attendance.objects.filter(student=student).order_by('-date')[:30]
    
    # Calculate attendance stats
    total_attendance = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, status='present').count()
    absent_count = Attendance.objects.filter(student=student, status='absent').count()
    
    attendance_percentage = 0
    if total_attendance > 0:
        attendance_percentage = round((present_count / total_attendance) * 100, 2)
    
    attendance_stats = {
        'present': present_count,
        'absent': absent_count,
        'total': total_attendance,
        'percentage': attendance_percentage
    }
    
    # Get grades
    grades = Grade.objects.filter(student=student).select_related('subject').order_by('-created_at')
    
    # Calculate average percentage
    average_percentage = 0
    if grades.exists():
        total_percentage = sum([g.percentage() for g in grades])
        average_percentage = round(total_percentage / grades.count(), 2)
    
    # Calculate overall grade
    if average_percentage >= 90:
        overall_grade = 'A+'
    elif average_percentage >= 80:
        overall_grade = 'A'
    elif average_percentage >= 70:
        overall_grade = 'B+'
    elif average_percentage >= 60:
        overall_grade = 'B'
    elif average_percentage >= 50:
        overall_grade = 'C'
    else:
        overall_grade = 'F'
    
    # Get homework for the student's class
    homework = Homework.objects.filter(
        class_name=student.current_class
    ).order_by('-assigned_date')[:10]
    
    context = {
        'student': student,
        'attendances': attendances,
        'attendance_stats': attendance_stats,
        'grades': grades,
        'average_percentage': average_percentage,
        'overall_grade': overall_grade,
        'homework': homework,
    }
    
    return render(request, 'parents/child_details.html', context)

@login_required
def add_parent(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            base_username = f"parent_{first_name.lower()}_{last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password='password123', # Default password
                first_name=first_name,
                last_name=last_name,
                user_type='parent',
                phone=form.cleaned_data.get('phone', ''),
                address=form.cleaned_data.get('address', '')
            )
            
            parent = form.save(commit=False)
            parent.user = user
            parent.save()
            form.save_m2m() # Save children
            messages.success(request, f"Parent {user.get_full_name()} added successfully.")
            return redirect('dashboard')
    else:
        form = ParentForm()
        
    return render(request, 'parents/add_parent.html', {'form': form})
