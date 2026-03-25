"""Add paystack_subscription_code, paystack_customer_code to SchoolSubscription
and payment_reference to Invoice.

These fields were added to the Python models but never had a migration, causing
ProgrammingError on any schema that doesn't have them yet.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0010_platformsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="schoolsubscription",
            name="paystack_subscription_code",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Paystack subscription code (PLN-xxx) for recurring billing",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="schoolsubscription",
            name="paystack_customer_code",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Paystack customer code (CUS-xxx)",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="payment_reference",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Paystack transaction reference that settled this invoice",
                max_length=100,
            ),
        ),
    ]
