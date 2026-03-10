from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def set_ai_limits(apps, schema_editor):
    SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')
    limits = {
        'trial':      20,
        'basic':      50,
        'pro':        300,
        'enterprise': -1,   # unlimited
    }
    for plan_type, limit in limits.items():
        SubscriptionPlan.objects.filter(plan_type=plan_type).update(ai_calls_per_month=limit)


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_seed_subscription_plans'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='ai_calls_per_month',
            field=models.IntegerField(
                default=50,
                help_text='Monthly AI generation calls per school. -1 = unlimited, 0 = AI disabled.',
            ),
        ),
        migrations.CreateModel(
            name='AIUsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(db_index=True)),
                ('action_type', models.CharField(
                    choices=[
                        ('lesson_gen',     'Lesson Plan Generation'),
                        ('slide_gen',      'Slide Generation'),
                        ('exercise_gen',   'Exercise Generation'),
                        ('assignment_gen', 'Assignment Generation'),
                        ('study_guide',    'Study Guide Generation'),
                        ('bulk_gen',       'Bulk Lesson Generation'),
                        ('other',          'Other'),
                    ],
                    default='other',
                    max_length=30,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('school', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_usage_logs',
                    to='tenants.school',
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['school', 'created_at'], name='tenants_aiu_school_created_idx'),
                    models.Index(fields=['school', 'action_type', 'created_at'], name='tenants_aiu_school_action_idx'),
                ],
            },
        ),
        migrations.RunPython(set_ai_limits, migrations.RunPython.noop),
    ]
