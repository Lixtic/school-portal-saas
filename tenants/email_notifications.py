"""
Email notification utilities for school approval workflow
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)


def send_approval_notification(school, status_changed_by=None):
    """
    Send email notification based on school approval status
    
    Args:
        school: School instance
        status_changed_by: User who changed the status (for logging)
    """
    if not school.contact_person_email:
        logger.warning(f"No contact email for school {school.schema_name}, skipping notification")
        return False
    
    status = school.approval_status
    subject_map = {
        'pending': f'Application Received - {school.name}',
        'under_review': f'Application Under Review - {school.name}',
        'approved': f'🎉 School Approved - {school.name}',
        'rejected': f'Application Decision - {school.name}',
        'requires_info': f'Additional Information Required - {school.name}',
    }
    
    template_map = {
        'pending': 'tenants/emails/status_pending.html',
        'under_review': 'tenants/emails/status_under_review.html',
        'approved': 'tenants/emails/status_approved.html',
        'rejected': 'tenants/emails/status_rejected.html',
        'requires_info': 'tenants/emails/status_requires_info.html',
    }
    
    subject = subject_map.get(status, f'School Application Update - {school.name}')
    template = template_map.get(status)
    
    if not template:
        logger.error(f"No email template for status: {status}")
        return False
    
    # Context for email template
    context = {
        'school': school,
        'contact_name': school.contact_person_name or 'Administrator',
        'status_changed_by': status_changed_by,
        'login_url': f"/{school.schema_name}/login/" if status == 'approved' else None,
    }
    
    try:
        # Render HTML content
        html_content = render_to_string(template, context)
        
        # Create plain text version (strip HTML tags for fallback)
        from django.utils.html import strip_tags
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[school.contact_person_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send
        email.send(fail_silently=False)
        logger.info(f"Sent {status} notification to {school.contact_person_email} for school {school.schema_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification for {school.schema_name}: {e}")
        return False


def send_submission_confirmation(school):
    """
    Send confirmation email immediately after school submits application
    Also notifies staff admins of new submission
    
    Args:
        school: School instance (just created, status=pending)
    """
    if not school.contact_person_email:
        return False
    
    subject = f'Application Submitted - {school.name}'
    template = 'tenants/emails/submission_confirmation.html'
    
    context = {
        'school': school,
        'contact_name': school.contact_person_name or 'Administrator',
    }
    
    try:
        html_content = render_to_string(template, context)
        from django.utils.html import strip_tags
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[school.contact_person_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Sent submission confirmation to {school.contact_person_email}")
        
        # Notify staff admins of new submission
        _notify_staff_new_application(school)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send submission confirmation: {e}")
        return False


def _notify_staff_new_application(school):
    """
    Internal function to notify staff admins when a new school application is submitted
    
    Args:
        school: School instance
    """
    User = get_user_model()
    staff_emails = User.objects.filter(is_staff=True, email__isnull=False).exclude(email='').values_list('email', flat=True)
    
    if not staff_emails:
        logger.warning("No staff emails found for new application notification")
        return
    
    subject = f'🔔 New School Application: {school.name}'
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
            .info {{ background: #f0f9ff; padding: 15px; border-left: 4px solid #3b82f6; margin: 15px 0; border-radius: 4px; }}
            .btn {{ display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📬 New School Application Received</h2>
            </div>
            <p>A new school has submitted an application for review.</p>
            
            <div class="info">
                <strong>School Name:</strong> {school.name}<br>
                <strong>Schema:</strong> <code>{school.schema_name}</code><br>
                <strong>Type:</strong> {school.get_school_type_display()}<br>
                <strong>Country:</strong> {school.country}<br>
                <strong>Contact:</strong> {school.contact_person_name} ({school.contact_person_email})<br>
                <strong>Submitted:</strong> {school.submitted_for_review_at.strftime('%B %d, %Y at %I:%M %p')}
            </div>
            
            <p><strong>Action Required:</strong> Please review the application and submitted documents.</p>
            
            <a href="/tenants/approval-queue/" class="btn">Go to Approval Queue →</a>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    New School Application Received
    
    School Name: {school.name}
    Schema: {school.schema_name}
    Type: {school.get_school_type_display()}
    Country: {school.country}
    Contact: {school.contact_person_name} ({school.contact_person_email})
    Submitted: {school.submitted_for_review_at.strftime('%B %d, %Y at %I:%M %p')}
    
    Please review the application at: /tenants/approval-queue/
    """
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            bcc=list(staff_emails),  # Use BCC to hide staff emails from each other
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)  # Don't fail the whole process if staff notification fails
        logger.info(f"Notified {len(staff_emails)} staff members of new application: {school.schema_name}")
    except Exception as e:
        logger.error(f"Failed to notify staff of new application: {e}")
