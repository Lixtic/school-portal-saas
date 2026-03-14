from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0027_studygroupmessage_reply_to'),
        ('teachers', '0008_presentation_slide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pulsesession',
            name='lesson_plan',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pulse_sessions',
                to='teachers.lessonplan',
            ),
        ),
        migrations.AddField(
            model_name='pulsesession',
            name='presentation',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pulse_sessions',
                to='teachers.presentation',
            ),
        ),
        migrations.AddField(
            model_name='pulsesession',
            name='target_class',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pulse_sessions',
                to='academics.class',
            ),
        ),
    ]
