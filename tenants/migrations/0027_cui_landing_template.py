from django.db import migrations, models


def promote_cui_template(apps, schema_editor):
    PlatformSettings = apps.get_model('tenants', 'PlatformSettings')
    PlatformSettings.objects.filter(pk=1).update(landing_template='home/cui.html')


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0026_agent_memory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platformsettings',
            name='landing_template',
            field=models.CharField(
                choices=[
                    ('home/classic.html', 'Classic — Sidebar Navigation'),
                    ('home/modern.html', 'Modern — Bold Hero'),
                    ('home/minimal.html', 'Minimal — Clean Cards'),
                    ('home/playful.html', 'Playful — Colourful & Animated'),
                    ('home/elegant.html', 'Elegant — Navy / Gold'),
                    ('home/swiss.html', 'Swiss — Grid System'),
                    ('home/glass.html', 'Glass — Digital Lucidity'),
                    ('home/artdeco.html', 'Art Deco — Gilded Authority'),
                    ('home/japandi.html', 'Japandi — Natural Clarity'),
                    ('home/cui.html', 'CUI — Conversational Workspace'),
                ],
                default='home/cui.html',
                help_text='Which landing page template to show at /',
                max_length=60,
            ),
        ),
        migrations.RunPython(promote_cui_template, migrations.RunPython.noop),
    ]
