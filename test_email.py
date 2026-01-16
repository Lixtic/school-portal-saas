"""
Test script for email notifications
Run with: python test_email.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
os.environ['EMAIL_BACKEND_TYPE'] = 'console'  # Print emails to console
django.setup()

from tenants.models import School
from tenants.email_notifications import send_submission_confirmation, send_approval_notification

print("=" * 60)
print("EMAIL NOTIFICATION TEST")
print("=" * 60)

# Get a pending school or create a test one
school = School.objects.filter(approval_status='pending').first()

if not school:
    print("\nNo pending schools found. Create one via signup first.")
    print("Or manually set a school's approval_status to 'pending'")
else:
    print(f"\nTesting with school: {school.name}")
    print(f"Contact email: {school.contact_person_email}")
    print(f"Status: {school.approval_status}")
    print("\n" + "=" * 60)
    print("TEST 1: Submission Confirmation Email")
    print("=" * 60)
    result1 = send_submission_confirmation(school)
    print(f"\nEmail sent successfully: {result1}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Status Under Review Email")
    print("=" * 60)
    school.approval_status = 'under_review'
    result2 = send_approval_notification(school)
    print(f"\nEmail sent successfully: {result2}")
    
    # Reset to pending
    school.approval_status = 'pending'
    school.save()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
