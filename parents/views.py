from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from parents.models import Parent
from homework.models import Homework, Submission
from .forms import ParentForm
from accounts.models import User


from students.models import Student, Attendance, Grade
from finance.models import StudentFee
from django.db.models import Sum
from django.db.models import Q

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

        # Calculate Fee Balance
        fees = StudentFee.objects.filter(student=child)
        total_payable = sum(fee.amount_payable for fee in fees)
        total_paid = sum(fee.total_paid for fee in fees)
        balance = total_payable - total_paid
        
        child.attendance_percentage = attendance_percentage
        child.grade_count = grade_count
        child.fee_balance = balance
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
        target_class=student.current_class
    ).order_by('-created_at')[:10]

    # Map homework → submission result for this student
    hw_ids = [hw.id for hw in homework]
    submissions_qs = Submission.objects.filter(student=student, homework_id__in=hw_ids)
    hw_submission_map = {sub.homework_id: sub for sub in submissions_qs}

    # Precompute homework + result pairs for template
    hw_with_results = [
        {'hw': hw_obj, 'sub': hw_submission_map.get(hw_obj.id)}
        for hw_obj in homework
    ]

    # Aura AI Learning Profile
    try:
        from academics.gamification_models import StudentXP, AuraSessionState
        from academics.tutor_models import LearnerMemory
        xp = StudentXP.objects.filter(student=student).first()
        learner_memory = LearnerMemory.objects.filter(student=student).first()
        aura_state = AuraSessionState.objects.filter(student=student).first()
    except Exception:
        xp = None
        learner_memory = None
        aura_state = None

    context = {
        'student': student,
        'attendances': attendances,
        'attendance_stats': attendance_stats,
        'grades': grades,
        'average_percentage': average_percentage,
        'overall_grade': overall_grade,
        'homework': homework,
        'hw_with_results': hw_with_results,
        'hw_submission_map': hw_submission_map,
        'xp': xp,
        'learner_memory': learner_memory,
        'aura_state': aura_state,
    }
    
    return render(request, 'parents/child_details.html', context)

@login_required
def add_parent(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    parents = Parent.objects.select_related('user').prefetch_related('children').order_by('user__first_name', 'user__last_name')
    if query:
        parents = parents.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__phone__icontains=query)
        )
        
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
            return redirect('parents:add_parent')
    else:
        form = ParentForm()
        
    return render(request, 'parents/add_parent.html', {
        'form': form,
        'parents': parents,
        'query': query,
        'is_edit': False,
    })


@login_required
def edit_parent(request, parent_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    parent = get_object_or_404(Parent.objects.select_related('user'), id=parent_id)

    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            user = parent.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.phone = form.cleaned_data.get('phone', '')
            user.address = form.cleaned_data.get('address', '')
            user.save()

            form.save()
            messages.success(request, f"Parent {user.get_full_name()} updated successfully.")
            return redirect('parents:add_parent')
    else:
        form = ParentForm(instance=parent, initial={
            'first_name': parent.user.first_name,
            'last_name': parent.user.last_name,
            'email': parent.user.email,
            'phone': parent.user.phone,
            'address': parent.user.address,
        })

    parents = Parent.objects.select_related('user').prefetch_related('children').order_by('user__first_name', 'user__last_name')
    return render(request, 'parents/add_parent.html', {
        'form': form,
        'parents': parents,
        'query': '',
        'is_edit': True,
        'editing_parent': parent,
    })


@login_required
def delete_parent(request, parent_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    parent = get_object_or_404(Parent.objects.select_related('user'), id=parent_id)

    if request.method == 'POST':
        full_name = parent.user.get_full_name() or parent.user.username
        parent.user.delete()
        messages.success(request, f"Parent {full_name} deleted successfully.")

    return redirect('parents:add_parent')

@login_required
def child_fees(request, student_id):
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
        
    parent = get_object_or_404(Parent, user=request.user)
    student = get_object_or_404(Student, id=student_id)
    
    # Verify this is the parent's child
    if student not in parent.children.all():
        messages.error(request, 'Access denied')
        return redirect('parents:my_children')
        
    fees = (StudentFee.objects
            .filter(student=student)
            .select_related('fee_structure', 'fee_structure__head')
            .prefetch_related('payments__recorded_by')
            .order_by('-fee_structure__due_date', '-created_at'))
    
    # Calculate totals
    total_payable = sum(fee.amount_payable for fee in fees)
    total_paid = sum(fee.total_paid for fee in fees)
    total_balance = total_payable - total_paid
        
    return render(request, 'parents/child_fees.html', {
        'student': student,
        'fees': fees,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_balance': total_balance,
    })


@login_required
def send_message_to_school(request):
    """Parent sends a message/query to all admins via Notification."""
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not subject or not body:
            messages.error(request, 'Please fill in both subject and message.')
            return redirect('parents:my_children')

        try:
            parent = Parent.objects.get(user=request.user)
            parent_name = request.user.get_full_name() or request.user.username
        except Parent.DoesNotExist:
            parent_name = request.user.get_full_name() or request.user.username

        from announcements.models import Notification
        admin_users = User.objects.filter(user_type='admin')
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                message=f"📬 Parent Query — {subject} | From: {parent_name}: {body[:180]}",
                alert_type='message',
                link='/dashboard/',
            )

        messages.success(request, 'Your message has been sent to the school administration.')
        return redirect('parents:my_children')

    return redirect('parents:my_children')
