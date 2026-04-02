import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0003_addonsubscription_payment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[('mathematics', 'Mathematics'), ('english', 'English Language'), ('science', 'Integrated Science'), ('social_studies', 'Social Studies'), ('computing', 'Computing / ICT'), ('french', 'French'), ('ghanaian_language', 'Ghanaian Language'), ('rme', 'Religious & Moral Education'), ('creative_arts', 'Creative Arts & Design'), ('career_tech', 'Career Technology'), ('history', 'History'), ('geography', 'Geography'), ('physics', 'Physics'), ('chemistry', 'Chemistry'), ('biology', 'Biology'), ('literature', 'Literature'), ('economics', 'Economics'), ('government', 'Government'), ('other', 'Other')], default='mathematics', max_length=30)),
                ('target_class', models.CharField(blank=True, default='', max_length=60)),
                ('topic', models.CharField(blank=True, default='', max_length=200)),
                ('question_text', models.TextField()),
                ('question_format', models.CharField(choices=[('mcq', 'Multiple Choice'), ('fill', 'Fill in the Blank'), ('short', 'Short Answer'), ('essay', 'Essay'), ('truefalse', 'True / False')], default='mcq', max_length=12)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium', max_length=8)),
                ('options', models.JSONField(blank=True, default=list, help_text='["A) …","B) …","C) …","D) …"] for MCQs')),
                ('correct_answer', models.TextField(blank=True, default='')),
                ('explanation', models.TextField(blank=True, default='', help_text='Why the answer is correct')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_questions', to='individual_users.individualprofile')),
            ],
            options={
                'verbose_name': 'Tool Question',
                'verbose_name_plural': 'Tool Questions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ToolExamPaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('subject', models.CharField(choices=[('mathematics', 'Mathematics'), ('english', 'English Language'), ('science', 'Integrated Science'), ('social_studies', 'Social Studies'), ('computing', 'Computing / ICT'), ('french', 'French'), ('ghanaian_language', 'Ghanaian Language'), ('rme', 'Religious & Moral Education'), ('creative_arts', 'Creative Arts & Design'), ('career_tech', 'Career Technology'), ('history', 'History'), ('geography', 'Geography'), ('physics', 'Physics'), ('chemistry', 'Chemistry'), ('biology', 'Biology'), ('literature', 'Literature'), ('economics', 'Economics'), ('government', 'Government'), ('other', 'Other')], default='mathematics', max_length=30)),
                ('target_class', models.CharField(blank=True, default='', max_length=60)),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('instructions', models.TextField(blank=True, default='Answer ALL questions.')),
                ('school_name', models.CharField(blank=True, default='', help_text='For paper header', max_length=200)),
                ('term', models.CharField(blank=True, default='', max_length=30)),
                ('academic_year', models.CharField(blank=True, default='', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_exam_papers', to='individual_users.individualprofile')),
                ('questions', models.ManyToManyField(blank=True, related_name='papers', to='individual_users.toolquestion')),
            ],
            options={
                'verbose_name': 'Tool Exam Paper',
                'verbose_name_plural': 'Tool Exam Papers',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ToolLessonPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('subject', models.CharField(choices=[('mathematics', 'Mathematics'), ('english', 'English Language'), ('science', 'Integrated Science'), ('social_studies', 'Social Studies'), ('computing', 'Computing / ICT'), ('french', 'French'), ('ghanaian_language', 'Ghanaian Language'), ('rme', 'Religious & Moral Education'), ('creative_arts', 'Creative Arts & Design'), ('career_tech', 'Career Technology'), ('history', 'History'), ('geography', 'Geography'), ('physics', 'Physics'), ('chemistry', 'Chemistry'), ('biology', 'Biology'), ('literature', 'Literature'), ('economics', 'Economics'), ('government', 'Government'), ('other', 'Other')], default='mathematics', max_length=30)),
                ('target_class', models.CharField(blank=True, default='', max_length=60)),
                ('topic', models.CharField(blank=True, default='', max_length=200)),
                ('duration_minutes', models.PositiveIntegerField(default=40)),
                ('objectives', models.TextField(blank=True, default='')),
                ('materials', models.TextField(blank=True, default='')),
                ('introduction', models.TextField(blank=True, default='')),
                ('development', models.TextField(blank=True, default='')),
                ('assessment', models.TextField(blank=True, default='')),
                ('closure', models.TextField(blank=True, default='')),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_lesson_plans', to='individual_users.individualprofile')),
            ],
            options={
                'verbose_name': 'Tool Lesson Plan',
                'verbose_name_plural': 'Tool Lesson Plans',
                'ordering': ['-created_at'],
            },
        ),
    ]
