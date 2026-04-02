from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0002_individualprofile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='addonsubscription',
            name='payment_reference',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='addonsubscription',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
