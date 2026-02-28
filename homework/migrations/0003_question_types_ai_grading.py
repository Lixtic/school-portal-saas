from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0002_question_choice_submission_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('mcq', 'Multiple Choice'), ('short', 'Short Answer')], default='mcq', max_length=10),
        ),
        migrations.AddField(
            model_name='question',
            name='correct_answer',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='text_response',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='ai_score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='ai_feedback',
            field=models.TextField(blank=True),
        ),
    ]