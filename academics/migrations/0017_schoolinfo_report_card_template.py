from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0016_schoolinfo_id_card_template_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolinfo',
            name='report_card_template',
            field=models.CharField(
                choices=[
                    ('classic', 'Classic — Traditional bordered report card'),
                    ('modern_plus', 'Modern Plus — Contemporary gradient style'),
                    ('minimal_clean', 'Minimal Clean — Lightweight monochrome style'),
                ],
                default='classic',
                help_text='Report card design template',
                max_length=20,
            ),
        ),
    ]
