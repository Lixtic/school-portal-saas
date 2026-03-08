from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0006_lessongenerationsession'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                default='male',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='teacher',
            name='region',
            field=models.CharField(
                blank=True,
                choices=[
                    ('greater_accra', 'Greater Accra'),
                    ('ashanti', 'Ashanti'),
                    ('central', 'Central'),
                    ('western', 'Western'),
                    ('eastern', 'Eastern'),
                    ('volta', 'Volta'),
                    ('oti', 'Oti'),
                    ('bono', 'Bono'),
                    ('bono_east', 'Bono East'),
                    ('ahafo', 'Ahafo'),
                    ('northern', 'Northern'),
                    ('north_east', 'North East'),
                    ('savannah', 'Savannah'),
                    ('upper_east', 'Upper East'),
                    ('upper_west', 'Upper West'),
                    ('western_north', 'Western North'),
                    ('other', 'Other / Outside Ghana'),
                ],
                default='',
                help_text='Region where the teacher is currently based / teaches',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='teacher',
            name='city',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Town or city of current residence/posting',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='teacher',
            name='hometown',
            field=models.CharField(
                blank=True,
                default='',
                help_text="Teacher's hometown / town of origin (informs cultural context)",
                max_length=150,
            ),
        ),
        migrations.AddField(
            model_name='teacher',
            name='preferred_language',
            field=models.CharField(
                blank=True,
                choices=[
                    ('english', 'English'),
                    ('twi', 'Twi / Akan'),
                    ('hausa', 'Hausa'),
                    ('ewe', 'Ewe'),
                    ('ga', 'Ga'),
                    ('dagbani', 'Dagbani'),
                    ('french', 'French'),
                    ('other', 'Other'),
                ],
                default='english',
                help_text="Teacher's primary spoken language",
                max_length=20,
            ),
        ),
    ]
