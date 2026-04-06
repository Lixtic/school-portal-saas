"""Batch 10: PresentationAnalytics model, tags on ToolPresentation, bookmarks on ToolSlide."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('individual_users', '0025_add_slide_poll'),
    ]

    operations = [
        # Tags on decks
        migrations.AddField(
            model_name='toolpresentation',
            name='tags',
            field=models.JSONField(blank=True, default=list, help_text='List of tag strings'),
        ),
        # Bookmark flag on slides
        migrations.AddField(
            model_name='toolslide',
            name='is_bookmarked',
            field=models.BooleanField(default=False),
        ),
        # Analytics model
        migrations.CreateModel(
            name='PresentationAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slide_timings', models.JSONField(default=list, help_text='List of {index, seconds} dicts')),
                ('total_duration', models.PositiveIntegerField(default=0, help_text='Total seconds')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('presentation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='individual_users.toolpresentation')),
            ],
            options={
                'verbose_name_plural': 'Presentation analytics',
                'ordering': ['-created_at'],
            },
        ),
    ]
