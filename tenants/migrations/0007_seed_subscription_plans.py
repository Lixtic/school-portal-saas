from django.db import migrations


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')

    plans = [
        {
            'name': 'Trial',
            'plan_type': 'trial',
            'description': '14-day free trial. Explore all Pro features with up to 50 students.',
            'monthly_price': 0,
            'quarterly_price': 0,
            'annual_price': 0,
            'max_students': 50,
            'max_teachers': 10,
            'max_storage_gb': 2,
            'custom_domain': False,
            'white_label': False,
            'priority_support': False,
            'api_access': False,
            'is_active': True,
        },
        {
            'name': 'Basic',
            'plan_type': 'basic',
            'description': 'For small schools. Covers student management, attendance, grades, timetable, and finance.',
            'monthly_price': 99,
            'quarterly_price': 259,
            'annual_price': 899,
            'max_students': 300,
            'max_teachers': 30,
            'max_storage_gb': 10,
            'custom_domain': False,
            'white_label': False,
            'priority_support': False,
            'api_access': False,
            'is_active': True,
        },
        {
            'name': 'Professional',
            'plan_type': 'pro',
            'description': 'For growing schools. All Basic features plus AI lesson planner (Padi-T), parent portal, advanced analytics, and priority support.',
            'monthly_price': 199,
            'quarterly_price': 529,
            'annual_price': 1899,
            'max_students': 1000,
            'max_teachers': 100,
            'max_storage_gb': 50,
            'custom_domain': False,
            'white_label': False,
            'priority_support': True,
            'api_access': False,
            'is_active': True,
        },
        {
            'name': 'Enterprise',
            'plan_type': 'enterprise',
            'description': 'For large institutions and school chains. Unlimited capacity, white-label branding, API access, custom integrations, and dedicated support.',
            'monthly_price': 499,
            'quarterly_price': 1349,
            'annual_price': 4999,
            'max_students': 9999,
            'max_teachers': 500,
            'max_storage_gb': 200,
            'custom_domain': True,
            'white_label': True,
            'priority_support': True,
            'api_access': True,
            'is_active': True,
        },
    ]

    for plan_data in plans:
        SubscriptionPlan.objects.get_or_create(
            plan_type=plan_data['plan_type'],
            defaults=plan_data,
        )


def unseed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(plan_type__in=['trial', 'basic', 'pro', 'enterprise']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0006_alter_school_school_type'),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
