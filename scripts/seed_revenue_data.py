"""
Seed revenue data for testing - creates schools with subscriptions, invoices, and churn events
Run with: python scripts/seed_revenue_data.py
"""
import os
import sys
import django
from decimal import Decimal
from datetime import timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.utils import timezone
from django.db import models
from tenants.models import (
    School, Domain, SubscriptionPlan, SchoolSubscription, 
    Invoice, ChurnEvent, AddOn, SchoolAddOn
)

print("=" * 70)
print("SEEDING REVENUE DATA FOR TESTING")
print("=" * 70)

# Ensure plans exist
plans = {
    'trial': SubscriptionPlan.objects.filter(plan_type='trial').first(),
    'basic': SubscriptionPlan.objects.filter(plan_type='basic').first(),
    'pro': SubscriptionPlan.objects.filter(plan_type='pro').first(),
    'enterprise': SubscriptionPlan.objects.filter(plan_type='enterprise').first(),
}

if not all(plans.values()):
    print("\n⚠️  Subscription plans not found. Run: python seed_subscriptions.py first")
    exit(1)

# Sample school data
schools_data = [
    {'name': 'Achimota School', 'schema_name': 'achimota', 'plan': 'pro', 'status': 'active', 'billing_cycle': 'annual', 'months_old': 18},
    {'name': 'Presec Legon', 'schema_name': 'presec', 'plan': 'enterprise', 'status': 'active', 'billing_cycle': 'annual', 'months_old': 24},
    {'name': 'Wesley Girls High', 'schema_name': 'wesley', 'plan': 'pro', 'status': 'active', 'billing_cycle': 'quarterly', 'months_old': 12},
    {'name': 'Mfantsipim School', 'schema_name': 'mfantsipim', 'plan': 'basic', 'status': 'active', 'billing_cycle': 'monthly', 'months_old': 8},
    {'name': 'Opoku Ware School', 'schema_name': 'opokuware', 'plan': 'pro', 'status': 'active', 'billing_cycle': 'annual', 'months_old': 15},
    {'name': 'St Roses Senior High', 'schema_name': 'stroses', 'plan': 'basic', 'status': 'active', 'billing_cycle': 'monthly', 'months_old': 6},
    {'name': 'Adisadel College', 'schema_name': 'adisadel', 'plan': 'pro', 'status': 'active', 'billing_cycle': 'quarterly', 'months_old': 10},
    {'name': 'Holy Child School', 'schema_name': 'holychild', 'plan': 'basic', 'status': 'active', 'billing_cycle': 'monthly', 'months_old': 4},
    {'name': 'Tema Secondary', 'schema_name': 'temasec', 'plan': 'trial', 'status': 'trial', 'billing_cycle': 'monthly', 'months_old': 0},
    {'name': 'Ridge Church School', 'schema_name': 'ridge', 'plan': 'trial', 'status': 'trial', 'billing_cycle': 'monthly', 'months_old': 0},
    {'name': 'Ghana National College', 'schema_name': 'gnc', 'plan': 'basic', 'status': 'active', 'billing_cycle': 'monthly', 'months_old': 5},
    {'name': 'Archbishop Porter Girls', 'schema_name': 'porter', 'plan': 'pro', 'status': 'active', 'billing_cycle': 'annual', 'months_old': 14},
]

created_schools = []
created_subscriptions = []

for school_data in schools_data:
    # Check if school exists
    school = School.objects.filter(schema_name=school_data['schema_name']).first()
    
    if not school:
        # Create school
        school = School.objects.create(
            name=school_data['name'],
            schema_name=school_data['schema_name'],
            is_active=True,
            approval_status='approved',
            on_trial=(school_data['status'] == 'trial')
        )
        
        # Create domain
        Domain.objects.create(
            domain=f"{school_data['schema_name']}.localhost",
            tenant=school,
            is_primary=True
        )
        
        created_schools.append(school)
        print(f"✓ Created school: {school.name}")
    else:
        print(f"○ School exists: {school.name}")
    
    # Create or update subscription
    plan = plans[school_data['plan']]
    subscription, created = SchoolSubscription.objects.get_or_create(
        school=school,
        defaults={
            'plan': plan,
            'billing_cycle': school_data['billing_cycle'],
            'status': school_data['status'],
            'started_at': timezone.now() - timedelta(days=school_data['months_old'] * 30),
            'current_period_start': timezone.now() - timedelta(days=15),
            'current_period_end': timezone.now() + timedelta(days=15),
            'trial_ends_at': timezone.now() + timedelta(days=14) if school_data['status'] == 'trial' else None,
            'current_students': random.randint(50, 500),
            'current_teachers': random.randint(10, 50),
        }
    )
    
    if created:
        # Calculate MRR
        subscription.calculate_mrr()
        created_subscriptions.append(subscription)
        print(f"  ✓ Created subscription: {plan.name} ({school_data['billing_cycle']}) - ₵{subscription.mrr}/mo")
        
        # Create historical invoices for paid subscriptions
        if school_data['status'] == 'active' and school_data['months_old'] > 0:
            months_to_create = min(school_data['months_old'], 6)  # Last 6 months
            
            for i in range(months_to_create):
                invoice_date = timezone.now() - timedelta(days=(i * 30))
                
                # Calculate amount based on billing cycle
                if subscription.billing_cycle == 'monthly':
                    amount = plan.monthly_price
                elif subscription.billing_cycle == 'quarterly':
                    if i % 3 == 0:  # Only create quarterly invoice
                        amount = plan.quarterly_price
                    else:
                        continue
                elif subscription.billing_cycle == 'annual':
                    if i == 0:  # Only one annual invoice
                        amount = plan.annual_price
                    else:
                        continue
                else:
                    amount = plan.monthly_price
                
                invoice = Invoice.objects.create(
                    subscription=subscription,
                    invoice_number=f"INV-{school.schema_name.upper()}-{invoice_date.strftime('%Y%m')}-{random.randint(1000,9999)}",
                    status='paid' if random.random() > 0.1 else 'pending',  # 90% paid
                    subtotal=amount,
                    tax=amount * Decimal('0.15'),  # 15% tax
                    total=amount * Decimal('1.15'),
                    issued_at=invoice_date,
                    due_at=invoice_date + timedelta(days=7),
                    paid_at=invoice_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.1 else None,
                    line_items=[
                        {
                            'description': f'{plan.name} Plan - {subscription.billing_cycle.title()}',
                            'quantity': 1,
                            'unit_price': float(amount),
                            'total': float(amount)
                        }
                    ]
                )
        
        # Add some add-ons to random active subscriptions
        if school_data['status'] == 'active' and random.random() > 0.5:
            available_addons = AddOn.objects.filter(is_active=True)[:3]
            for addon in available_addons:
                if random.random() > 0.6:  # 40% chance to have each addon
                    SchoolAddOn.objects.create(
                        subscription=subscription,
                        addon=addon,
                        is_active=True,
                        purchased_at=subscription.started_at + timedelta(days=random.randint(7, 60))
                    )
                    print(f"    + Added: {addon.name}")
            
            # Recalculate MRR with add-ons
            subscription.calculate_mrr()

# Create some churn events (cancelled schools)
churn_data = [
    {'name': 'Mountain View Academy', 'schema_name': 'mountainview', 'reason': 'price', 'months': 3},
    {'name': 'Sunset High School', 'schema_name': 'sunset', 'reason': 'features', 'months': 5},
    {'name': 'Riverside College', 'schema_name': 'riverside', 'reason': 'competitor', 'months': 8},
]

for churn_info in churn_data:
    school = School.objects.filter(schema_name=churn_info['schema_name']).first()
    
    if not school:
        school = School.objects.create(
            name=churn_info['name'],
            schema_name=churn_info['schema_name'],
            is_active=False,
            approval_status='approved'
        )
        print(f"✓ Created churned school: {school.name}")
    
    # Create cancelled subscription
    plan = plans['basic']
    subscription = SchoolSubscription.objects.filter(school=school).first()
    
    if not subscription:
        cancelled_date = timezone.now() - timedelta(days=random.randint(5, 25))
        subscription = SchoolSubscription.objects.create(
            school=school,
            plan=plan,
            billing_cycle='monthly',
            status='cancelled',
            started_at=timezone.now() - timedelta(days=churn_info['months'] * 30),
            current_period_start=cancelled_date - timedelta(days=30),
            current_period_end=cancelled_date,
            cancelled_at=cancelled_date,
        )
        subscription.calculate_mrr()
        
        # Create churn event
        ltv = plan.monthly_price * churn_info['months']
        ChurnEvent.objects.create(
            school=school,
            subscription=subscription,
            cancelled_at=cancelled_date,
            reason=churn_info['reason'],
            reason_detail=f"Cancelled after {churn_info['months']} months",
            lifetime_value=ltv,
            months_subscribed=churn_info['months']
        )
        print(f"✓ Created churn event: {school.name} - {churn_info['reason']}")

print("\n" + "=" * 70)
print(f"SUMMARY:")
print(f"  • Schools created: {len(created_schools)}")
print(f"  • Subscriptions created: {len(created_subscriptions)}")
print(f"  • Total active subscriptions: {SchoolSubscription.objects.filter(status__in=['active', 'trial']).count()}")
print(f"  • Total MRR: ₵{SchoolSubscription.objects.filter(status__in=['active', 'trial']).aggregate(models.Sum('mrr'))['mrr__sum'] or 0}")
print(f"  • Churn events: {ChurnEvent.objects.count()}")
print(f"  • Invoices: {Invoice.objects.count()}")
print("=" * 70)
