from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Sum, Q, Count, Max
from django.db.models.functions import Coalesce
from django.conf import settings
from .models import FeeHead, FeeStructure, StudentFee, Payment
from .forms import FeeHeadForm, FeeStructureForm, PaymentForm
from students.models import Student
from teachers.models import Teacher
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
    sort_by = request.GET.get('sort', 'newest')

    structures_qs = (
        FeeStructure.objects
        .select_related('head', 'class_level', 'academic_year', 'assigned_collector__user')
        .annotate(
            assigned_students=Count('studentfee', distinct=True),
            paid_students=Count('studentfee', filter=Q(studentfee__status='paid'), distinct=True),
        )
    )

    if sort_by == 'class_asc':
        structures = structures_qs.order_by('class_level__name', '-academic_year__start_date', 'head__name')
    elif sort_by == 'class_desc':
        structures = structures_qs.order_by('-class_level__name', '-academic_year__start_date', 'head__name')
    else:
        structures = structures_qs.order_by('-id')

    teachers = Teacher.objects.select_related('user').order_by('user__last_name', 'user__first_name')

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
        'head_form': head_form,
        'sort_by': sort_by,
        'teachers': teachers,
    })


@login_required
def fee_collected_students(request, structure_id):
    """Display students who have fully paid a specific fee structure."""
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    structure = get_object_or_404(
        FeeStructure.objects.select_related('head', 'class_level', 'academic_year', 'assigned_collector__user'),
        id=structure_id,
    )

    paid_fees = (
        StudentFee.objects
        .filter(fee_structure=structure, status='paid')
        .select_related('student__user', 'student__current_class')
        .annotate(
            total_paid_amount=Coalesce(Sum('payments__amount'), Decimal('0')),
            latest_payment_date=Max('payments__date'),
        )
        .order_by('student__user__last_name', 'student__user__first_name')
    )

    total_collected = (
        Payment.objects
        .filter(student_fee__fee_structure=structure)
        .aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']
    )

    total_payable = (
        StudentFee.objects
        .filter(fee_structure=structure)
        .aggregate(total=Coalesce(Sum('amount_payable'), Decimal('0')))['total']
    )

    teachers = Teacher.objects.select_related('user').order_by('user__last_name', 'user__first_name')

    context = {
        'structure': structure,
        'paid_fees': paid_fees,
        'paid_count': paid_fees.count(),
        'total_collected': total_collected,
        'total_payable': total_payable,
        'teachers': teachers,
    }
    return render(request, 'finance/fee_collected_students.html', context)


@login_required
def fee_collected_students_csv(request, structure_id):
    """Download a CSV of fully-paid students for a fee structure."""
    import csv
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    structure = get_object_or_404(
        FeeStructure.objects.select_related('head', 'class_level', 'academic_year'),
        id=structure_id,
    )

    paid_fees = (
        StudentFee.objects
        .filter(fee_structure=structure, status='paid')
        .select_related('student__user', 'student__current_class')
        .annotate(
            total_paid_amount=Coalesce(Sum('payments__amount'), Decimal('0')),
            latest_payment_date=Max('payments__date'),
        )
        .order_by('student__user__last_name', 'student__user__first_name')
    )

    filename = f"paid_{structure.head.name}_{structure.class_level}_{structure.term}.csv".replace(' ', '_')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['#', 'Student Name', 'Class', 'Amount Paid (GHS)', 'Last Payment Date', 'Status'])

    for idx, sf in enumerate(paid_fees, start=1):
        student_name = sf.student.user.get_full_name()
        class_name = sf.student.current_class.name if sf.student.current_class else '-'
        amount = sf.total_paid_amount
        last_date = sf.latest_payment_date.strftime('%Y-%m-%d') if sf.latest_payment_date else '-'
        writer.writerow([idx, student_name, class_name, amount, last_date, 'Paid'])

    return response


@login_required
def assign_fee_collector(request, structure_id):
    """Assign or remove a teacher as the fee collector for a fee structure."""
    if request.user.user_type != 'admin':
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('finance:manage_fees')

    structure = get_object_or_404(FeeStructure, id=structure_id)
    teacher_id = request.POST.get('teacher_id', '').strip()

    if teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        structure.assigned_collector = teacher
        structure.save(update_fields=['assigned_collector'])
        messages.success(
            request,
            f"{teacher.user.get_full_name()} assigned as collector for {structure.head.name} – {structure.class_level}."
        )
        # Notify the assigned teacher
        task_url = f"/{request.tenant.schema_name}/teachers/fee-tasks/"
        Notification.objects.create(
            recipient=teacher.user,
            message=f"You have been assigned to collect {structure.head.name} fees for {structure.class_level} ({structure.term} term).",
            link=task_url,
            alert_type='general',
        )
        try:
            from announcements.views import send_push_notification
            send_push_notification(
                teacher.user,
                "New Fee Collection Task",
                f"You've been assigned: {structure.head.name} – {structure.class_level}",
                url=task_url,
            )
        except Exception:
            pass  # Push notification failure must not break the main flow
    else:
        structure.assigned_collector = None
        structure.save(update_fields=['assigned_collector'])
        messages.success(request, "Collector removed from this fee.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url:
        return redirect(next_url)
    return redirect('finance:manage_fees')


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

    # Permission check: Admin, Assigned Class Teacher, or Assigned Fee Collector
    allowed = False
    collectible_fee_ids = set()  # StudentFee IDs this user can record payment for

    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'teacher':
        teacher = Teacher.objects.get(user=request.user)
        if (student.current_class and student.current_class.class_teacher and
                student.current_class.class_teacher.user == request.user):
            allowed = True
        # Also allow if assigned as collector for any of this student's fee structures
        collector_fees = StudentFee.objects.filter(
            student=student,
            fee_structure__assigned_collector=teacher,
        ).values_list('id', flat=True)
        if collector_fees.exists():
            allowed = True
            collectible_fee_ids = set(collector_fees)

    if not allowed:
        messages.error(request, "Access Denied. Only Admins or assigned teachers can view fees.")
        return redirect('dashboard')

    fees = (
        StudentFee.objects
        .filter(student=student)
        .select_related('fee_structure', 'fee_structure__head')
        .prefetch_related('payments')
    )

    processed_fees = []
    for fee in fees:
        processed_fees.append({
            'obj': fee,
            'paid': fee.total_paid,
            'balance': fee.balance,
            'can_collect': request.user.user_type == 'admin' or fee.id in collectible_fee_ids,
        })

    return render(request, 'finance/student_fees.html', {
        'student': student,
        'fees': processed_fees,
    })

@login_required
def record_payment(request, fee_id):
    fee = get_object_or_404(StudentFee.objects.select_related(
        'fee_structure__assigned_collector__user', 'student'
    ), id=fee_id)

    # Permission: admin, or the teacher assigned as collector for this fee structure
    allowed = False
    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'teacher':
        collector = fee.fee_structure.assigned_collector
        if collector and collector.user == request.user:
            allowed = True

    if not allowed:
        messages.error(request, 'Access denied. You are not the assigned collector for this fee.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PaymentForm(request.POST, fee=fee)
        if form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                fee = StudentFee.objects.select_for_update().get(pk=fee.pk)
                payment = form.save(commit=False)
                payment.student_fee = fee
                payment.recorded_by = request.user
                payment.save()
                messages.success(request, 'Payment recorded successfully.')
                # Teachers return to their fee task detail page; admins go to student fees.
                if request.user.user_type == 'teacher':
                    return redirect('teachers:fee_task_detail', structure_id=fee.fee_structure_id)
                return redirect('finance:student_fees', student_id=fee.student.id)
    else:
        form = PaymentForm(initial={'amount': fee.balance}, fee=fee)

    return render(request, 'finance/payment_form.html', {'form': form, 'fee': fee})

@login_required
def print_receipt(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related(
        'student_fee__fee_structure__assigned_collector__user',
        'student_fee__student__current_class__class_teacher__user',
    ), id=payment_id)
    student = payment.student_fee.student

    # Permission: Admin, Assigned Class Teacher, Assigned Collector, or Parent
    allowed = False
    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'teacher':
        if (student.current_class and student.current_class.class_teacher and
                student.current_class.class_teacher.user == request.user):
            allowed = True
        collector = payment.student_fee.fee_structure.assigned_collector
        if collector and collector.user == request.user:
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
                        defaults={'amount_payable': structure.amount, 'status': 'unpaid'},
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
                hasattr(request.user, 'student') and
                request.user.student == payment.student_fee.student):
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
        ['Receipt No.:', f'RCT-{payment.id:05d}', 'Date:', payment.date.strftime('%d %b %Y')],
        ['Student:', student.user.get_full_name(), 'Class:', student.current_class.name if student.current_class else 'N/A'],
        ['Fee Item:', sf.fee_structure.head.name, 'Term:', sf.fee_structure.term.title()],
        ['Amount Paid:', f'₵{payment.amount:.2f}', 'Balance After:', f'₵{sf.balance:.2f}'],
        ['Payment Status:', sf.get_status_display(), 'Method:', payment.method],

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


# ─────────────────────────────────────────────────────────────────────────────
# PAYSTACK ONLINE PAYMENT INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def initiate_paystack_payment(request, fee_id):
    """Redirect the user to Paystack's hosted payment page for a StudentFee."""
    import requests as req_lib
    import uuid

    fee = get_object_or_404(StudentFee, id=fee_id)

    # Only the student, a parent, or an admin can initiate
    allowed = False
    if request.user.user_type == 'admin':
        allowed = True
    elif request.user.user_type == 'student':
        try:
            from students.models import Student as _S
            if _S.objects.get(user=request.user) == fee.student:
                allowed = True
        except Exception:
            pass
    elif request.user.user_type == 'parent':
        from parents.models import Parent
        try:
            parent = Parent.objects.get(user=request.user)
            if fee.student in parent.children.all():
                allowed = True
        except Exception:
            pass

    if not allowed:
        messages.error(request, 'Access denied')
        return redirect('dashboard')

    if fee.status == 'paid':
        messages.info(request, 'This fee has already been fully paid.')
        return redirect('finance:student_fees', student_id=fee.student.id)

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    if not secret_key:
        messages.error(request, 'Paystack is not configured. Please contact admin.')
        return redirect('finance:student_fees', student_id=fee.student.id)

    reference = f"SPS-{fee.id}-{uuid.uuid4().hex[:8].upper()}"
    amount_minor = int(fee.balance * 100)  # Paystack uses smallest currency unit (pesewas/kobo)
    email = fee.student.user.email

    from django.urls import reverse as _rev
    callback_url = request.build_absolute_uri(_rev('finance:paystack_callback'))

    payload = {
        'email': email or f"student{fee.student.id}@schoolportal.app",
        'amount': amount_minor,
        'currency': getattr(settings, 'PAYSTACK_CURRENCY', 'GHS'),
        'reference': reference,
        'callback_url': callback_url,
        'metadata': {
            'fee_id': fee.id,
            'student_id': fee.student.id,
            'custom_fields': [
                {'display_name': 'Student', 'variable_name': 'student', 'value': fee.student.user.get_full_name()},
                {'display_name': 'Fee Item', 'variable_name': 'fee_item', 'value': fee.fee_structure.head.name},
            ]
        }
    }

    try:
        resp = req_lib.post(
            'https://api.paystack.co/transaction/initialize',
            json=payload,
            headers={
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
        data = resp.json()
        if data.get('status'):
            return redirect(data['data']['authorization_url'])
        else:
            messages.error(request, f"Paystack error: {data.get('message', 'Unknown error')}")
    except Exception as exc:
        messages.error(request, f"Payment gateway unavailable: {exc}")

    return redirect('finance:student_fees', student_id=fee.student.id)


@login_required
def paystack_callback(request):
    """Handle redirect from Paystack after payment (success or cancel)."""
    import requests as req_lib

    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('finance:dashboard')

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    try:
        resp = req_lib.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={'Authorization': f'Bearer {secret_key}'},
            timeout=15,
        )
        data = resp.json()
    except Exception as exc:
        messages.error(request, f"Could not verify payment: {exc}")
        return redirect('finance:dashboard')

    if not data.get('status') or data['data']['status'] != 'success':
        messages.warning(request, 'Payment was not completed or verification failed.')
        return redirect('finance:dashboard')

    trx     = data['data']
    meta    = trx.get('metadata', {})
    fee_id  = meta.get('fee_id')

    if fee_id:
        fee = StudentFee.objects.filter(id=fee_id).first()
        if fee:
            from decimal import Decimal
            amount_paid = Decimal(str(trx['amount'])) / 100
            _, created = Payment.objects.get_or_create(
                reference=reference,
                defaults={
                    'student_fee': fee,
                    'amount': amount_paid,
                    'method': 'Bank Transfer',
                    'recorded_by': request.user,
                },
            )
            if created:
                messages.success(request, f'Payment of ₵{amount_paid:.2f} verified and recorded. Thank you!')
            else:
                messages.info(request, 'Payment already recorded.')
            return redirect('finance:student_fees', student_id=fee.student.id)

    messages.success(request, 'Payment verified successfully.')
    return redirect('finance:dashboard')


@csrf_exempt
def paystack_webhook(request):
    """Receive Paystack charge.success webhook and auto-record the payment."""
    import hmac
    import hashlib
    import json as _json

    if request.method != 'POST':
        return HttpResponse(status=405)

    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    signature  = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
    body       = request.body

    # Verify HMAC-SHA512 signature
    expected = hmac.new(secret_key.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return HttpResponse(status=400)

    try:
        payload = _json.loads(body)
    except Exception:
        return HttpResponse(status=400)

    if payload.get('event') != 'charge.success':
        return HttpResponse(status=200)

    trx       = payload['data']
    reference = trx.get('reference', '')
    meta      = trx.get('metadata', {})
    fee_id    = meta.get('fee_id')

    if fee_id and reference:
        fee = StudentFee.objects.filter(id=fee_id).first()
        if fee:
            from decimal import Decimal
            amount_paid = Decimal(str(trx['amount'])) / 100
            Payment.objects.get_or_create(
                reference=reference,
                defaults={
                    'student_fee': fee,
                    'amount': amount_paid,
                    'method': 'Bank Transfer',
                    'remarks': 'Auto-recorded via Paystack webhook',
                },
            )

    return HttpResponse(status=200)


# ─────────────────────────────────────────────────────────────────────────────
# SMS FEE REMINDERS  (Africa's Talking)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def send_sms_fee_reminders(request):
    """Bulk-send SMS fee reminders to students with outstanding balances."""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    pending_fees = (
        StudentFee.objects
        .filter(status__in=['unpaid', 'partial'])
        .select_related('student', 'student__user', 'fee_structure', 'fee_structure__head')
    )

    if request.method == 'POST':
        from announcements.sms_service import send_fee_sms_reminder
        sent = failed = skipped = 0
        for fee in pending_fees:
            student = fee.student
            phone = getattr(student, 'emergency_contact', '').strip()
            if not phone:
                skipped += 1
                continue
            result = send_fee_sms_reminder(student, fee)
            if result.get('sent'):
                sent += 1
            else:
                failed += 1

        messages.success(
            request,
            f'SMS reminders: {sent} sent, {failed} failed, {skipped} skipped (no phone number).'
        )
        return redirect('finance:dashboard')

    # GET — confirmation page
    total_balance  = sum(f.balance for f in pending_fees)
    phones_missing = sum(1 for f in pending_fees if not getattr(f.student, 'emergency_contact', '').strip())
    return render(request, 'finance/sms_reminders.html', {
        'pending_count': pending_fees.count(),
        'total_balance': total_balance,
        'phones_missing': phones_missing,
    })
