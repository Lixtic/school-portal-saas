from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from parents.models import Parent
from homework.models import Homework, Submission
from .forms import ParentForm
from accounts.models import User
import json

from students.models import Student, Attendance, Grade
from finance.models import StudentFee, Payment
from teachers.models import Teacher
from django.db.models import Sum, Q, Count, Value, OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce

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
    
    # Single annotated query — no per-child loops
    fee_payable_sq = (
        StudentFee.objects.filter(student=OuterRef('pk'))
        .values('student')
        .annotate(total=Sum('amount_payable'))
        .values('total')
    )
    from finance.models import Payment
    fee_paid_sq = (
        Payment.objects.filter(student_fee__student=OuterRef('pk'))
        .values('student_fee__student')
        .annotate(total=Sum('amount'))
        .values('total')
    )

    children = (
        parent.children
        .select_related('user', 'current_class')
        .annotate(
            total_attendance=Count('attendance', distinct=True),
            present_count=Count('attendance', filter=Q(attendance__status='present'), distinct=True),
            grade_count=Count('grade', distinct=True),
            fee_payable=Coalesce(Subquery(fee_payable_sq), Value(0)),
            fee_paid=Coalesce(Subquery(fee_paid_sq), Value(0)),
        )
    )

    children_data = []
    for child in children:
        child.attendance_percentage = (
            round((child.present_count / child.total_attendance) * 100, 2)
            if child.total_attendance > 0 else 0
        )
        child.fee_balance = child.fee_payable - child.fee_paid
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
    if not parent.children.filter(pk=student.pk).exists():
        messages.error(request, 'Access denied - This is not your child')
        return redirect('parents:my_children')
    
    # Get attendance records
    attendances = Attendance.objects.filter(student=student).order_by('-date')[:30]
    
    # Calculate attendance stats in a single aggregate query
    att_agg = Attendance.objects.filter(student=student).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
    )
    total_attendance = att_agg['total']
    present_count = att_agg['present']
    absent_count = att_agg['absent']
    
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
    ).prefetch_related('questions').order_by('-created_at')[:10]

    # Map homework → best submission for this student
    # Order by -score so the first encountered per homework_id is the best
    hw_ids = [hw.id for hw in homework]
    submissions_qs = (
        Submission.objects
        .filter(student=student, homework_id__in=hw_ids)
        .order_by('homework_id', '-score')
    )
    hw_submission_map = {}
    for sub in submissions_qs:
        if sub.homework_id not in hw_submission_map:
            hw_submission_map[sub.homework_id] = sub  # keeps highest score

    # Precompute homework + result pairs + max_pts for template
    from django.db.models import Sum as _Sum
    hw_with_results = []
    for hw_obj in homework:
        # Sum of question points (defaults to 1 per question if not customised)
        max_pts = hw_obj.questions.aggregate(total=_Sum('points'))['total']
        if not max_pts:
            max_pts = hw_obj.questions.count() or 1
        hw_with_results.append({
            'hw': hw_obj,
            'sub': hw_submission_map.get(hw_obj.id),
            'max_pts': max_pts,
        })

    # SchoolPadi AI Learning Profile
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

    # Fee summary for this child
    fees = (StudentFee.objects
            .filter(student=student)
            .select_related('fee_structure', 'fee_structure__head')
            .prefetch_related('payments')
            .order_by('-fee_structure__due_date', '-created_at'))
    fee_total_payable = sum(f.amount_payable for f in fees)
    fee_total_paid = sum(f.total_paid for f in fees)
    fee_total_balance = fee_total_payable - fee_total_paid

    # ── Chart data: weekly attendance trend (last 8 weeks) ──
    import datetime as _dt
    from collections import OrderedDict
    today = _dt.date.today()
    # Fetch 8 weeks of attendance in ONE query, then bucket in Python
    eight_weeks_ago = today - _dt.timedelta(weeks=8, days=today.weekday())
    raw_att = list(
        Attendance.objects.filter(student=student, date__gte=eight_weeks_ago)
        .values_list('date', 'status')
    )
    week_labels = []
    week_present = []
    week_total = []
    for i in range(7, -1, -1):
        start = today - _dt.timedelta(weeks=i, days=today.weekday())
        end = start + _dt.timedelta(days=4)
        wt = sum(1 for d, s in raw_att if start <= d <= end)
        wp = sum(1 for d, s in raw_att if start <= d <= end and s == 'present')
        week_labels.append(start.strftime('%b %d'))
        week_total.append(wt)
        week_present.append(wp)

    # ── Chart data: grade average per subject ──
    from itertools import groupby
    from operator import attrgetter
    subject_scores = {}
    for g in grades:
        sname = g.subject.name if g.subject else 'Unknown'
        subject_scores.setdefault(sname, []).append(g.total_score or 0)
    subject_labels = list(subject_scores.keys())
    subject_avgs = [round(sum(v) / len(v), 1) for v in subject_scores.values()]

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
        'fees': fees,
        'fee_total_payable': fee_total_payable,
        'fee_total_paid': fee_total_paid,
        'fee_total_balance': fee_total_balance,
        'att_week_labels': json.dumps(week_labels),
        'att_week_present': json.dumps(week_present),
        'att_week_total': json.dumps(week_total),
        'subject_labels': json.dumps(subject_labels),
        'subject_avgs': json.dumps(subject_avgs),
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
def payment_history(request):
    """Consolidated payment history across all children."""
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.select_related('user', 'current_class').all()
    child_ids = list(children.values_list('pk', flat=True))

    payments = (
        Payment.objects
        .filter(student_fee__student_id__in=child_ids)
        .select_related(
            'student_fee__student__user',
            'student_fee__student__current_class',
            'student_fee__fee_structure__head',
        )
        .order_by('-date', '-created_at')
    )

    # Optional filters
    child_filter = request.GET.get('child')
    if child_filter and child_filter.isdigit():
        payments = payments.filter(student_fee__student_id=int(child_filter))

    method_filter = request.GET.get('method')
    if method_filter:
        payments = payments.filter(method=method_filter)

    # Totals
    total_amount = sum(p.amount for p in payments)
    payment_count = len(payments)

    # Per-child summary
    child_summaries = []
    for child in children:
        child_payments = [p for p in payments if p.student_fee.student_id == child.pk]
        child_summaries.append({
            'student': child,
            'count': len(child_payments),
            'total': sum(p.amount for p in child_payments),
        })

    return render(request, 'parents/payment_history.html', {
        'payments': payments,
        'children': children,
        'child_summaries': child_summaries,
        'total_amount': total_amount,
        'payment_count': payment_count,
        'selected_child': child_filter,
        'selected_method': method_filter,
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
        notifications = [
            Notification(
                recipient=admin,
                message=f"📬 Parent Query — {subject} | From: {parent_name}: {body[:180]}",
                alert_type='message',
                link='/dashboard/',
            )
            for admin in admin_users
        ]
        Notification.objects.bulk_create(notifications)

        messages.success(request, 'Your message has been sent to the school administration.')
        return redirect('parents:my_children')

    return redirect('parents:my_children')


@login_required
def contact_teachers(request):
    """List teachers of the parent's children with direct messaging links."""
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    try:
        parent = Parent.objects.get(user=request.user)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('dashboard')

    children = parent.children.select_related('user', 'current_class').all()

    # Build a mapping: teacher → list of children they teach + subjects
    from academics.models import ClassSubject
    teacher_map = {}

    # Bulk-fetch all ClassSubjects for children's classes (avoids N+1)
    class_ids = [c.current_class_id for c in children if c.current_class_id]
    all_class_subjects = (
        ClassSubject.objects.filter(class_name_id__in=class_ids)
        .select_related('teacher__user', 'subject')
    ) if class_ids else ClassSubject.objects.none()
    cs_by_class = {}
    for cs in all_class_subjects:
        cs_by_class.setdefault(cs.class_name_id, []).append(cs)

    for child in children:
        if not child.current_class:
            continue
        # Class teacher
        ct = getattr(child.current_class, 'class_teacher', None)
        if ct:
            key = ct.user_id
            if key not in teacher_map:
                teacher_map[key] = {
                    'teacher': ct,
                    'user': ct.user,
                    'is_class_teacher': True,
                    'children': set(),
                    'subjects': set(),
                }
            teacher_map[key]['children'].add(child)
            teacher_map[key]['is_class_teacher'] = True

        # Subject teachers (from pre-fetched data)
        for cs in cs_by_class.get(child.current_class_id, []):
            if not cs.teacher:
                continue
            key = cs.teacher.user_id
            if key not in teacher_map:
                teacher_map[key] = {
                    'teacher': cs.teacher,
                    'user': cs.teacher.user,
                    'is_class_teacher': False,
                    'children': set(),
                    'subjects': set(),
                }
            teacher_map[key]['children'].add(child)
            teacher_map[key]['subjects'].add(cs.subject.name)

    # Convert sets to sorted lists for template
    teacher_list = []
    for info in teacher_map.values():
        teacher_list.append({
            'teacher': info['teacher'],
            'user': info['user'],
            'is_class_teacher': info['is_class_teacher'],
            'children': sorted(info['children'], key=lambda c: c.user.get_full_name()),
            'subjects': sorted(info['subjects']),
        })
    # Sort: class teachers first, then alphabetically
    teacher_list.sort(key=lambda t: (not t['is_class_teacher'], t['user'].get_full_name()))

    return render(request, 'parents/contact_teachers.html', {
        'teacher_list': teacher_list,
        'children': children,
    })
