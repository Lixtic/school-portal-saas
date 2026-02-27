from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_classexercise_studentexercisescore'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='region',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='student',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='student',
            name='curriculum',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='student',
            name='interests',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
