from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0014_livesession_slide_time_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonplan',
            name='b7_meta',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Extra editable fields for B7 weekly template (period, strand, hidden rows, etc.)',
            ),
        ),
    ]
