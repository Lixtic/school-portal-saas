from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import FeeHead, FeeStructure, StudentFee, Payment
from .forms import FeeHeadForm, FeeStructureForm, PaymentForm
from students.models import Student
from academics.models import Class, AcademicYear, SchoolInfo
from announcements.models import Notification

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


@login_required
def send_fee_reminders(request):
    """Allow admin to send bulk fee reminder notifications to all students with outstanding fees."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    pending_fees = (
        StudentFee.objects
        .filter(status__in=['unpaid', 'partial'])
        .select_related('student', 'student__user', 'fee_structure', 'fee_structure__head')
        .order_by('student__user__last_name')
    )

    if request.method == 'POST':
        from django.urls import reverse as url_reverse
        created = 0
        skipped = 0
        for fee in pending_fees:
            student = fee.student
            user = student.user
            balance = fee.balance
            head_name = fee.fee_structure.head.name
            try:
                link = url_reverse('finance:student_fees', args=[student.id])
            except Exception:
                link = '/finance/'

            message = (
                f"Fee Reminder: You have an outstanding balance of ₵{balance:.2f} "
                f"for {head_name}. Please make payment at your earliest convenience."
            )

            already_pending = Notification.objects.filter(
                recipient=user,
                alert_type='general',
                is_read=False,
                message__startswith="Fee Reminder:",
                link=link,
            ).exists()

            if already_pending:
                skipped += 1
                continue

            Notification.objects.create(
                recipient=user,
                message=message,
                alert_type='general',
                link=link,
            )
            created += 1

        messages.success(
            request,
            f"Sent {created} fee reminder notification(s). Skipped {skipped} student(s) who already have a pending reminder."
        )
        return redirect('finance:dashboard')

    # GET — show confirmation page
    total_balance = sum(fee.balance for fee in pending_fees)
    context = {
        'pending_fees': pending_fees,
        'total_balance': total_balance,
        'student_count': pending_fees.count(),
    }
    return render(request, 'finance/send_reminders.html', context)


@login_required
def bulk_assign_fees(request):
    """Bulk-assign an existing FeeStructure to all students in a class who don't have it yet."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    academic_year = AcademicYear.objects.filter(is_current=True).first()
    classes = Class.objects.filter(academic_year=academic_year).order_by('name') if academic_year else Class.objects.none()
    structures = FeeStructure.objects.filter(academic_year=academic_year).select_related('head') if academic_year else FeeStructure.objects.none()

    assigned = 0
    skipped = 0

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        structure_ids = request.POST.getlist('structure_ids')

        if not class_id or not structure_ids:
            messages.error(request, 'Please select a class and at least one fee structure.')
        else:
            target_class = get_object_or_404(Class, id=class_id)
            students_in_class = Student.objects.filter(current_class=target_class).select_related('user')

            for structure_id in structure_ids:
                try:
                    structure = FeeStructure.objects.get(id=structure_id)
                except FeeStructure.DoesNotExist:
                    continue
                for student in students_in_class:
                    _, created = StudentFee.objects.get_or_create(
                        student=student,
                        fee_structure=structure,
                        defaults={'amount_due': structure.amount, 'status': 'unpaid'},
                    )
                    if created:
                        assigned += 1
                    else:
                        skipped += 1

            messages.success(
                request,
                f"Bulk assignment complete — {assigned} new fee record(s) created, "
                f"{skipped} already existed (skipped)."
            )
            return redirect('finance:dashboard')

    context = {
        'classes': classes,
        'structures': structures,
        'academic_year': academic_year,
        'assigned': assigned,
        'skipped': skipped,
    }
    return render(request, 'finance/bulk_assign_fees.html', context)


@login_required
def payment_receipt_pdf(request, payment_id):
    """Download a payment receipt as a PDF using ReportLab."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A5
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    payment = get_object_or_404(Payment, id=payment_id)
    if request.user.user_type not in ['admin', 'teacher']:
        if not (request.user.user_type == 'student' and
                hasattr(request.user, 'student_profile') and
                request.user.student_profile == payment.student_fee.student):
            messages.error(request, 'Access denied.')
            return redirect('dashboard')

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A5, leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.2*cm, bottomMargin=1.2*cm)
    styles = getSampleStyleSheet()
    BLUE   = colors.HexColor('#1d4ed8')
    GREEN  = colors.HexColor('#059669')
    LIGHT  = colors.HexColor('#eff6ff')
    BORDER = colors.HexColor('#d1d5db')

    ctr  = ParagraphStyle('c', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub  = ParagraphStyle('s', parent=styles['Normal'], fontSize=8,  alignment=TA_CENTER, textColor=colors.HexColor('#555555'))
    body = ParagraphStyle('b', parent=styles['Normal'], fontSize=9)

    story = []
    sf = payment.student_fee
    student = sf.student

    story.append(Paragraph('PAYMENT RECEIPT', ctr))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=8))

    data = [
        ['Receipt No.:', f'RCT-{payment.id:05d}', 'Date:', payment.date_paid.strftime('%d %b %Y')],
        ['Student:', student.user.get_full_name(), 'Class:', student.current_class.name if student.current_class else 'N/A'],
        ['Fee Item:', sf.fee_structure.head.name, 'Term:', sf.fee_structure.term.title()],
        ['Amount Paid:', f'₵{payment.amount_paid:.2f}', 'Balance After:', f'₵{sf.balance:.2f}'],
        ['Payment Status:', sf.get_status_display(), 'Method:', payment.payment_method if hasattr(payment, 'payment_method') else 'N/A'],
    ]
    table = Table(data, colWidths=[3*cm, 4.5*cm, 2.5*cm, 4*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,-1), LIGHT),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=4))
    story.append(Paragraph('Thank you for your payment. Keep this receipt for your records.', sub))

    doc.build(story)
    buf.seek(0)
    fname = f"receipt_{student.user.last_name}_{payment.id}.pdf".replace(' ', '_')
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response
