from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_usersettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('teacher', 'Teacher'),
                    ('student', 'Student'),
                    ('parent', 'Parent'),
                    ('individual', 'Individual'),
                ],
                max_length=10,
            ),
        ),
    ]
