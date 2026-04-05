from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0021_studygrouproom_studygroupmessage'),
        ('students', '0007_add_preferred_language_and_aura_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='PowerWord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=120)),
                ('session_type', models.CharField(
                    choices=[('voice', 'SchoolPadi Voice'), ('text', 'Text Chat')],
                    default='text',
                    max_length=10,
                )),
                ('subject', models.CharField(blank=True, max_length=200)),
                ('used_count', models.IntegerField(default=1)),
                ('week', models.IntegerField(db_index=True, default=0)),
                ('year', models.IntegerField(db_index=True, default=0)),
                ('first_heard', models.DateTimeField(auto_now_add=True)),
                ('last_heard', models.DateTimeField(auto_now=True)),
                ('confirmed_by_teacher', models.BooleanField(default=False)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='power_words',
                    to='students.student',
                )),
            ],
            options={
                'verbose_name': 'Power Word',
                'verbose_name_plural': 'Power Words',
                'ordering': ['-last_heard'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='powerword',
            unique_together={('student', 'word', 'year', 'week')},
        ),
    ]
