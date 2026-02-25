from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import FeeHead, FeeStructure, StudentFee, Payment
from .forms import FeeHeadForm, FeeStructureForm, PaymentForm
from students.models import Student
from academics.models import Class, AcademicYear, SchoolInfo

@login_required
def finance_dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access Denied')
        return redirect('dashboard')

    # Quick Stats
    total_receivable = StudentFee.objects.aggregate(Sum('amount_payable'))['amount_payable__sum'] or 0
    total_collected = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_amount = total_receivable - total_collected

    recent_payments = Payment.objects.select_related('student_fee__student__user').order_by('-created_at')[:10]
    fee_structures = FeeStructure.objects.select_related('head', 'class_level').order_by('-id')[:5]

    context = {
        'total_receivable': total_receivable,
        'total_collected': total_collected,
        'pending_amount': pending_amount,
        'recent_payments': recent_payments,
        'fee_structures': fee_structures,
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def manage_fees(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    heads = FeeHead.objects.all()
    structures = FeeStructure.objects.select_related('head', 'class_level', 'academic_year').order_by('-id')

    if request.method == 'POST':
        # Simple handler for creating a new Fee Head inline if needed
        head_form = FeeHeadForm(request.POST)
        if head_form.is_valid():
            head_form.save()
            messages.success(request, 'Fee Type created')
            return redirect('finance:manage_fees')
    else:
        head_form = FeeHeadForm()

    return render(request, 'finance/manage_fees.html', {
        'heads': heads,
        'structures': structures,
        'head_form': head_form
    })

@login_required
def create_fee_structure(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            structure = form.save()
            
            # Auto-assign to existing students?
            assign_now = request.POST.get('assign_now') == 'on'
            if assign_now:
                students = Student.objects.filter(current_class=structure.class_level)
                count = 0
                for student in students:
                    # Check if already exists
                    if not StudentFee.objects.filter(student=student, fee_structure=structure).exists():
                        StudentFee.objects.create(
                            student=student,
                            fee_structure=structure,
                            amount_payable=structure.amount
                        )
                        count += 1
                messages.success(request, f'Fee Structure created and assigned to {count} students.')
            else:
                messages.success(request, 'Fee Structure created.')
            return redirect('finance:manage_fees')
    else:
        form = FeeStructureForm()

    return render(request, 'finance/fee_form.html', {'form': form})


@login_required
def edit_fee_structure(request, structure_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    structure = get_object_or_404(FeeStructure, id=structure_id)

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee Structure updated successfully.')
            return redirect('finance:manage_fees')
    else:
        form = FeeStructureForm(instance=structure)

    return render(request, 'finance/fee_form.html', {
        'form': form,
        'is_edit': True,
        'form_title': 'Edit Fee Structure',
        'submit_label': 'Update Fee'
    })


@login_required
def edit_fee_head(request, head_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    fee_head = get_object_or_404(FeeHead, id=head_id)

    if request.method == 'POST':
        form = FeeHeadForm(request.POST, instance=fee_head)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee Category updated successfully.')
            return redirect('finance:manage_fees')
    else:
        form = FeeHeadForm(instance=fee_head)

    return render(request, 'finance/fee_head_form.html', {
        'form': form,
        'fee_head': fee_head
    })

@login_required
def student_fees(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Permission check: Only Admin or Assigned Class Teacher
    allowed = False
    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'teacher':
        if student.current_class and student.current_class.class_teacher and student.current_class.class_teacher.user == request.user:
            allowed = True
            
    if not allowed:
        messages.error(request, "Access Denied. Only Admins or Class Teachers can view fees.")
        return redirect('dashboard')

    fees = StudentFee.objects.filter(student=student).select_related('fee_structure', 'fee_structure__head')
    
    processed_fees = []
    for fee in fees:
        processed_fees.append({
            'obj': fee,
            'paid': fee.total_paid,
            'balance': fee.balance
        })

    return render(request, 'finance/student_fees.html', {
        'student': student,
        'fees': processed_fees
    })

@login_required
def record_payment(request, fee_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
        
    fee = get_object_or_404(StudentFee, id=fee_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student_fee = fee
            payment.recorded_by = request.user
            payment.save()
            messages.success(request, 'Payment recorded successfully')
            return redirect('finance:student_fees', student_id=fee.student.id)
    else:
        form = PaymentForm(initial={'amount': fee.balance})

    return render(request, 'finance/payment_form.html', {'form': form, 'fee': fee})

@login_required
def print_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    student = payment.student_fee.student
    
    # Permission check: Admin, Assigned Class Teacher, or Parent of the student
    allowed = False
    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'teacher':
        if student.current_class and student.current_class.class_teacher and student.current_class.class_teacher.user == request.user:
            allowed = True
    elif request.user.user_type == 'parent':
        from parents.models import Parent
        try:
            parent = Parent.objects.get(user=request.user)
            if student in parent.children.all():
                allowed = True
        except Parent.DoesNotExist:
            pass

    if not allowed:
        return redirect('dashboard')
    
    school_info = SchoolInfo.objects.first()
    
    return render(request, 'finance/receipt.html', {
        'payment': payment,
        'school_info': school_info
    })
