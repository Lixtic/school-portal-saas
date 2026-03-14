from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0007_subject_nullable'),
        ('academics', '0001_initial'),
        ('teachers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source_deck', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sent_notes',
                    to='teachers.presentation',
                )),
                ('target_class', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='class_notes',
                    to='academics.class',
                )),
                ('teacher', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='class_notes',
                    to='teachers.teacher',
                )),
            ],
            options={
                'verbose_name': 'Class Note',
                'verbose_name_plural': 'Class Notes',
                'ordering': ['-created_at'],
            },
        ),
    ]
