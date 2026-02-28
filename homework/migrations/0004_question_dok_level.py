from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0003_question_types_ai_grading'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='dok_level',
            field=models.PositiveSmallIntegerField(choices=[(1, 'DOK 1: Recall'), (2, 'DOK 2: Skills/Concepts'), (3, 'DOK 3: Strategic Thinking'), (4, 'DOK 4: Extended Thinking')], default=1),
        ),
    ]