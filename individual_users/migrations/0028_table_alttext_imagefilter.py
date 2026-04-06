"""Batch 12: table_data JSONField, alt_text, image_filter on ToolSlide; 'table' layout choice."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0027_slide_bg_deck_accent_font'),
    ]

    operations = [
        migrations.AddField(
            model_name='toolslide',
            name='table_data',
            field=models.JSONField(blank=True, default=list, help_text='Table rows as [[cell,...],...]'),
        ),
        migrations.AddField(
            model_name='toolslide',
            name='alt_text',
            field=models.CharField(blank=True, default='', help_text='Alt text for slide image', max_length=500),
        ),
        migrations.AddField(
            model_name='toolslide',
            name='image_filter',
            field=models.CharField(blank=True, default='', help_text='CSS filter string for slide image', max_length=200),
        ),
        migrations.AlterField(
            model_name='toolslide',
            name='layout',
            field=models.CharField(
                choices=[
                    ('title', 'Title Slide'), ('bullets', 'Bullet List'),
                    ('two_col', 'Two Column'), ('big_stat', 'Big Stat'),
                    ('quote', 'Quote'), ('summary', 'Summary'),
                    ('image', 'Image + Caption'), ('table', 'Table'),
                ],
                default='bullets', max_length=20,
            ),
        ),
    ]
