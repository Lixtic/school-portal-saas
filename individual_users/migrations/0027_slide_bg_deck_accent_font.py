"""Batch 11: Per-slide bg_color/bg_image, deck accent_color/font_family."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0026_analytics_tags_bookmarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='toolslide',
            name='bg_color',
            field=models.CharField(blank=True, default='', help_text='Custom background color (hex or rgba)', max_length=30),
        ),
        migrations.AddField(
            model_name='toolslide',
            name='bg_image',
            field=models.TextField(blank=True, default='', help_text='Custom background image URL'),
        ),
        migrations.AddField(
            model_name='toolpresentation',
            name='accent_color',
            field=models.CharField(blank=True, default='', help_text='Custom accent color override', max_length=30),
        ),
        migrations.AddField(
            model_name='toolpresentation',
            name='font_family',
            field=models.CharField(blank=True, default='', help_text='Custom Google Font family name', max_length=80),
        ),
    ]
