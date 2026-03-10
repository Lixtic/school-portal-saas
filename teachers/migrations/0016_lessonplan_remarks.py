from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0015_lessonplan_b7_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonplan',
            name='remarks',
            field=models.TextField(blank=True, help_text='Teacher reflection / PHASE 3 notes'),
        ),
    ]
