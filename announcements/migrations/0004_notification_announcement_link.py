from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0003_fix_notification_table'),
    ]

    operations = [
        # Add link field
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        # Add announcement FK
        migrations.AddField(
            model_name='notification',
            name='announcement',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='announcements.announcement',
            ),
        ),
        # Widen alert_type to support new choices and add default
        migrations.AlterField(
            model_name='notification',
            name='alert_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('45_min', '45 Minutes Before Class'),
                    ('10_min', '10 Minutes Before Class'),
                    ('announcement', 'Announcement'),
                    ('message', 'New Message'),
                    ('general', 'General'),
                ],
                default='general',
                max_length=20,
            ),
        ),
    ]
