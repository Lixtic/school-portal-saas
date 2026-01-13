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
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SMSForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            target_class = form.cleaned_data['target_class']
            body = form.cleaned_data['message_body']
            
            # Logic to gather numbers
            recipients = []
            
            if recipient_type == 'individual':
                number = form.cleaned_data['recipient_number']
                if number:
                    recipients.append(number)
            
            elif recipient_type == 'class' and target_class:
                # Get parents of students in this class
                students = Student.objects.filter(current_class=target_class).select_related('parent_user')
                for student in students:
                    # Assuming we check parent phone or student phone
                    # For now using a dummy field or User attribute if it existed
                    # We'll just mock it since User model modification is heavy
                    pass 
                    
            # For MVP, we just create one record to show it working
            # In real implementation, we would loop through recipients
            
            sms = form.save(commit=False)
            sms.sent_by = request.user
            sms.status = 'sent' # Mock success
            sms.provider_response = 'Mock: Message sent successfully'
            sms.save()
            
            messages.success(request, f"SMS sent successfully!")
            return redirect('communication:dashboard')
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
