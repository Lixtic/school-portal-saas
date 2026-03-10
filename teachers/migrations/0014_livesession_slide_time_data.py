from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0013_presentation_transition'),
    ]

    operations = [
        migrations.AddField(
            model_name='livesession',
            name='slide_time_data',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
