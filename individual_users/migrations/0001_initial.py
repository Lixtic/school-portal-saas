from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IndividualProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, db_index=True, max_length=20)),
                ('google_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('avatar_url', models.URLField(blank=True)),
                ('company', models.CharField(blank=True, max_length=200)),
                ('bio', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='individual_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Individual Profile',
                'verbose_name_plural': 'Individual Profiles',
            },
        ),
        migrations.CreateModel(
            name='AddonSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('addon_slug', models.CharField(max_length=80)),
                ('addon_name', models.CharField(max_length=120)),
                ('plan', models.CharField(choices=[('free', 'Free'), ('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='free', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='active', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='individual_users.individualprofile')),
            ],
            options={
                'ordering': ['-started_at'],
                'unique_together': {('profile', 'addon_slug')},
            },
        ),
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A label for this key', max_length=100)),
                ('prefix', models.CharField(db_index=True, editable=False, max_length=8)),
                ('hashed_key', models.CharField(editable=False, max_length=128)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('calls_today', models.PositiveIntegerField(default=0)),
                ('calls_total', models.PositiveIntegerField(default=0)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='individual_users.individualprofile')),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
                'ordering': ['-created_at'],
            },
        ),
    ]
