from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='individualprofile',
            name='role',
            field=models.CharField(
                choices=[('developer', 'Developer'), ('teacher', 'Teacher')],
                db_index=True,
                default='developer',
                max_length=20,
            ),
        ),
    ]
