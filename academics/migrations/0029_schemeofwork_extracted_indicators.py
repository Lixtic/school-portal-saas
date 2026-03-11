from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0028_pulse_session_presentation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='schemeofwork',
            name='extracted_indicators',
            field=models.TextField(
                blank=True,
                default='{}',
                help_text='JSON dict mapping topic to indicator code',
            ),
        ),
    ]
