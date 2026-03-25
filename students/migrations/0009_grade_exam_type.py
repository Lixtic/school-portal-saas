from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_examtype'),
    ]

    operations = [
        migrations.AddField(
            model_name='grade',
            name='exam_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students.examtype'),
        ),
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together={('student', 'subject', 'academic_year', 'term', 'exam_type')},
        ),
    ]
