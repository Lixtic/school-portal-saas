from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SMSMessage, EmailCampaign
from .forms import SMSForm, EmailForm
from students.models import Student
from teachers.models import Teacher
from accounts.models import User

@login_required
def dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, "Access Denied")
        return redirect('dashboard')
        
    recent_sms = SMSMessage.objects.order_by('-created_at')[:5]
    recent_emails = EmailCampaign.objects.order_by('-created_at')[:5]
    
    return render(request, 'communication/dashboard.html', {
        'recent_sms': recent_sms,
        'recent_emails': recent_emails
    })

@login_required
def send_sms(request):
    if request.user.user_type != 'admin':
        messages.error(request, "Access Denied")
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SMSForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            target_class = form.cleaned_data['target_class']
            message_body = form.cleaned_data['message_body']
            
            recipients = set() # Use set to dedup numbers
            
            try:
                if recipient_type == 'individual':
                    number = form.cleaned_data['recipient_number']
                    if number:
                        recipients.add(number)
                
                elif recipient_type == 'class':
                    if target_class:
                        # Get students in class
                        students = Student.objects.filter(current_class=target_class).prefetch_related('parents__user')
                        for student in students:
                            for parent in student.parents.all():
                                if parent.user.phone:
                                    recipients.add(parent.user.phone)
                    else:
                        messages.error(request, "Please select a class")
                        return render(request, 'communication/send_sms.html', {'form': form})

                elif recipient_type == 'teachers':
                    teachers = Teacher.objects.select_related('user').all()
                    for teacher in teachers:
                        if teacher.user.phone:
                            recipients.add(teacher.user.phone)
                            
                elif recipient_type == 'staff':
                    # Assuming staff are Admin + Teachers for now
                    users = User.objects.filter(user_type__in=['admin', 'teacher'])
                    for user in users:
                        if user.phone:
                            recipients.add(user.phone)

                if not recipients:
                    messages.warning(request, "No valid phone numbers found for the selected group.")
                    return redirect('communication:send_sms')

                # Mock Sending Process
                success_count = 0
                for phone in recipients:
                    # Create Record
                    SMSMessage.objects.create(
                        recipient_number=phone,
                        message_body=message_body,
                        status='sent',
                        provider_response='Mock Gateway: Delivered',
                        sent_by=request.user
                    )
                    success_count += 1
                
                messages.success(request, f"SMS queued/sent to {success_count} recipients.")
                return redirect('communication:dashboard')

            except Exception as e:
                messages.error(request, f"Error processing SMS: {str(e)}")
                
    else:
        form = SMSForm()

    return render(request, 'communication/send_sms.html', {'form': form})

@login_required
def send_email(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.sent_by = request.user
            email.status = 'sent'
            email.save()
            messages.success(request, "Email campaign queued successfully")
            return redirect('communication:dashboard')
    else:
        form = EmailForm()
        
    return render(request, 'communication/send_email.html', {'form': form})
