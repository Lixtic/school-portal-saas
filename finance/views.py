from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Sum, Q
from django.conf import settings
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
    amount_kobo = int(fee.balance * 100)  # Paystack uses smallest currency unit
    email = fee.student.user.email

    callback_url = request.build_absolute_uri(
        f"/{''.join(request.path.split('/')[:2])}/finance/paystack/callback/"
        if request.tenant
        else '/finance/paystack/callback/'
    )
    # Build tenant-aware callback URL
    from django.urls import reverse as _rev
    try:
        callback_url = request.build_absolute_uri(_rev('finance:paystack_callback'))
    except Exception:
        pass

    payload = {
        'email': email or f"student{fee.student.id}@schoolportal.app",
        'amount': amount_kobo,
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
        if fee and not Payment.objects.filter(reference=reference).exists():
            amount_paid = trx['amount'] / 100
            Payment.objects.create(
                student_fee=fee,
                amount=amount_paid,
                reference=reference,
                method='Bank Transfer',
                recorded_by=request.user,
            )
            messages.success(request, f'Payment of ₵{amount_paid:.2f} verified and recorded. Thank you!')
            return redirect('finance:student_fees', student_id=fee.student.id)
        elif fee:
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
        if fee and not Payment.objects.filter(reference=reference).exists():
            amount_paid = trx['amount'] / 100
            Payment.objects.create(
                student_fee=fee,
                amount=amount_paid,
                reference=reference,
                method='Bank Transfer',
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
