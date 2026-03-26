from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0012_alter_platformsettings_landing_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformsettings',
            name='ai_model_admissions',
            field=models.CharField(default='openai:gpt-4o-mini', help_text='Admissions and public FAQ assistant model.', max_length=80),
        ),
        migrations.AddField(
            model_name='platformsettings',
            name='ai_model_analytics',
            field=models.CharField(default='openai:gpt-5-mini', help_text='Reports, summaries, and analytics-oriented model.', max_length=80),
        ),
        migrations.AddField(
            model_name='platformsettings',
            name='ai_model_general',
            field=models.CharField(default='openai:gpt-5-mini', help_text='General AI model for global assistant-style tasks.', max_length=80),
        ),
        migrations.AddField(
            model_name='platformsettings',
            name='ai_model_tutor',
            field=models.CharField(default='openai:gpt-5-nano', help_text='Tutor/copilot classroom workflows model.', max_length=80),
        ),
        migrations.AddField(
            model_name='platformsettings',
            name='ai_primary_provider',
            field=models.CharField(choices=[('openai', 'OpenAI'), ('gemini', 'Google Gemini')], default='openai', help_text='Default provider used across AI features unless a category model overrides provider.', max_length=20),
        ),
    ]
