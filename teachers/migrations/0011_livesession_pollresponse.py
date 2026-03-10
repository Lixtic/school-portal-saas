from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0010_slide_image_url_and_image_layout'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slide',
            name='layout',
            field=models.CharField(
                choices=[
                    ('title',    'Title Slide'),
                    ('bullets',  'Bullet List'),
                    ('two_col',  'Two Column'),
                    ('big_stat', 'Big Stat'),
                    ('quote',    'Quote'),
                    ('summary',  'Summary'),
                    ('image',    'Image + Caption'),
                    ('poll',     'Live Poll'),
                    ('quiz',     'Quiz Reveal'),
                ],
                default='bullets',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='LiveSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('current_slide_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('presentation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='live_sessions',
                    to='teachers.presentation',
                )),
            ],
        ),
        migrations.CreateModel(
            name='PollResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(blank=True, default='Anonymous', max_length=100)),
                ('choice', models.CharField(max_length=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='teachers.livesession',
                )),
                ('slide', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='poll_responses',
                    to='teachers.slide',
                )),
            ],
            options={
                'unique_together': {('session', 'slide', 'student_name')},
            },
        ),
    ]
