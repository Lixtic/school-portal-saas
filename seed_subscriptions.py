"""
Seed subscription plans and add-ons for testing
Run with: python seed_subscriptions.py
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from tenants.models import SubscriptionPlan, AddOn

print("=" * 60)
print("SEEDING SUBSCRIPTION PLANS & ADD-ONS")
print("=" * 60)

# Create Subscription Plans
plans_data = [
    {
        'name': 'Trial',
        'plan_type': 'trial',
        'description': '14-day free trial with all features',
        'monthly_price': Decimal('0.00'),
        'quarterly_price': Decimal('0.00'),
        'annual_price': Decimal('0.00'),
        'max_students': 50,
        'max_teachers': 10,
        'max_storage_gb': 5,
        'custom_domain': False,
        'white_label': False,
        'priority_support': False,
        'api_access': False,
    },
    {
        'name': 'Basic',
        'plan_type': 'basic',
        'description': 'Essential features for small schools',
        'monthly_price': Decimal('49.00'),
        'quarterly_price': Decimal('132.00'),  # 10% off
        'annual_price': Decimal('470.00'),  # 20% off
        'max_students': 200,
        'max_teachers': 30,
        'max_storage_gb': 20,
        'custom_domain': False,
        'white_label': False,
        'priority_support': False,
        'api_access': False,
    },
    {
        'name': 'Professional',
        'plan_type': 'pro',
        'description': 'Advanced features for growing schools',
        'monthly_price': Decimal('149.00'),
        'quarterly_price': Decimal('402.00'),
        'annual_price': Decimal('1432.00'),
        'max_students': 1000,
        'max_teachers': 100,
        'max_storage_gb': 100,
        'custom_domain': True,
        'white_label': False,
        'priority_support': True,
        'api_access': True,
    },
    {
        'name': 'Enterprise',
        'plan_type': 'enterprise',
        'description': 'Complete solution for large institutions',
        'monthly_price': Decimal('499.00'),
        'quarterly_price': Decimal('1347.00'),
        'annual_price': Decimal('4790.00'),
        'max_students': 999999,
        'max_teachers': 999999,
        'max_storage_gb': 500,
        'custom_domain': True,
        'white_label': True,
        'priority_support': True,
        'api_access': True,
    },
]

for plan_data in plans_data:
    plan, created = SubscriptionPlan.objects.get_or_create(
        plan_type=plan_data['plan_type'],
        defaults=plan_data
    )
    if created:
        print(f"✓ Created plan: {plan.name}")
    else:
        print(f"- Plan exists: {plan.name}")

# Create Add-ons
addons_data = [
    {
        'name': 'AI Tutor Assistant',
        'slug': 'ai-tutor',
        'category': 'ai',
        'description': 'AI-powered personalized tutoring for students with adaptive learning paths',
        'icon': 'bi-robot',
        'monthly_price': Decimal('29.00'),
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'name': 'Advanced Analytics Pro',
        'slug': 'analytics-pro',
        'category': 'analytics',
        'description': 'Deep insights into student performance, attendance trends, and predictive analytics',
        'icon': 'bi-graph-up',
        'monthly_price': Decimal('19.00'),
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'name': 'SMS Gateway',
        'slug': 'sms-gateway',
        'category': 'communication',
        'description': 'Bulk SMS notifications to parents and students (includes 1000 messages/mo)',
        'icon': 'bi-chat-dots',
        'monthly_price': Decimal('15.00'),
        'is_one_time': False,
        'available_for_plans': ['pro', 'enterprise'],
    },
    {
        'name': 'Google Classroom Integration',
        'slug': 'google-classroom',
        'category': 'integration',
        'description': 'Seamless sync with Google Classroom for assignments and grades',
        'icon': 'bi-google',
        'monthly_price': Decimal('12.00'),
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'name': 'Extra Storage 100GB',
        'slug': 'storage-100gb',
        'category': 'storage',
        'description': 'Additional 100GB cloud storage for documents, videos, and resources',
        'icon': 'bi-cloud-upload',
        'monthly_price': Decimal('9.00'),
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
    {
        'name': 'Mobile App (iOS & Android)',
        'slug': 'mobile-app',
        'category': 'feature',
        'description': 'Branded mobile apps for iOS and Android with push notifications',
        'icon': 'bi-phone',
        'monthly_price': Decimal('99.00'),
        'is_one_time': False,
        'available_for_plans': ['pro', 'enterprise'],
    },
    {
        'name': 'Video Conferencing',
        'slug': 'video-conferencing',
        'category': 'communication',
        'description': 'Built-in video conferencing for virtual classes (up to 100 participants)',
        'icon': 'bi-camera-video',
        'monthly_price': Decimal('39.00'),
        'is_one_time': False,
        'available_for_plans': ['pro', 'enterprise'],
    },
    {
        'name': 'Parent Portal Plus',
        'slug': 'parent-portal-plus',
        'category': 'feature',
        'description': 'Enhanced parent portal with real-time notifications and payment integration',
        'icon': 'bi-people',
        'monthly_price': Decimal('19.00'),
        'is_one_time': False,
        'available_for_plans': ['basic', 'pro', 'enterprise'],
    },
]

for addon_data in addons_data:
    addon, created = AddOn.objects.get_or_create(
        slug=addon_data['slug'],
        defaults=addon_data
    )
    if created:
        print(f"✓ Created add-on: {addon.name}")
    else:
        print(f"- Add-on exists: {addon.name}")

print("\n" + "=" * 60)
print("SEEDING COMPLETE!")
print("=" * 60)
print(f"\nCreated {SubscriptionPlan.objects.count()} plans and {AddOn.objects.count()} add-ons")
print("\nAccess:")
print("- Revenue Analytics: /tenants/revenue/")
print("- Add-on Marketplace: /tenants/marketplace/ (as school tenant)")
