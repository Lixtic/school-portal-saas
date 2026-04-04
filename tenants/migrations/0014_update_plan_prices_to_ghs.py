"""Update subscription plan prices from USD to GHS."""
from django.db import migrations
from decimal import Decimal


def update_prices(apps, schema_editor):
    SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')

    ghs_prices = {
        'basic': {
            'monthly_price': Decimal('99.00'),
            'quarterly_price': Decimal('259.00'),
            'annual_price': Decimal('899.00'),
        },
        'pro': {
            'monthly_price': Decimal('199.00'),
            'quarterly_price': Decimal('529.00'),
            'annual_price': Decimal('1899.00'),
        },
        'enterprise': {
            'monthly_price': Decimal('499.00'),
            'quarterly_price': Decimal('1349.00'),
            'annual_price': Decimal('4999.00'),
        },
    }

    for plan_type, prices in ghs_prices.items():
        SubscriptionPlan.objects.filter(plan_type=plan_type).update(**prices)


def revert_prices(apps, schema_editor):
    SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')

    usd_prices = {
        'basic': {
            'monthly_price': Decimal('49.00'),
            'quarterly_price': Decimal('132.00'),
            'annual_price': Decimal('499.00'),
        },
        'pro': {
            'monthly_price': Decimal('99.00'),
            'quarterly_price': Decimal('267.00'),
            'annual_price': Decimal('999.00'),
        },
        'enterprise': {
            'monthly_price': Decimal('249.00'),
            'quarterly_price': Decimal('672.00'),
            'annual_price': Decimal('2499.00'),
        },
    }

    for plan_type, prices in usd_prices.items():
        SubscriptionPlan.objects.filter(plan_type=plan_type).update(**prices)


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0013_platformsettings_ai_models'),
    ]

    operations = [
        migrations.RunPython(update_prices, revert_prices),
    ]
