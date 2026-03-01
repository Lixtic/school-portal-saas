from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0004_question_dok_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('mcq', 'Multiple Choice'),
                    ('short', 'Short Answer'),
                    ('essay', 'Essay'),
                ],
                default='mcq',
                max_length=10,
            ),
        ),
    ]
