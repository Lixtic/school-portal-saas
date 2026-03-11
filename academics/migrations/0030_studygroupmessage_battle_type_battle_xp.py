from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0029_schemeofwork_extracted_indicators'),
    ]

    operations = [
        migrations.AddField(
            model_name='studygroupmessage',
            name='battle_type',
            field=models.CharField(
                choices=[
                    ('battle',    'Trivia Battle'),
                    ('riddle',    'Riddle'),
                    ('math',      'Math Challenge'),
                    ('spell',     'Spelling Challenge'),
                    ('truefalse', 'True or False'),
                ],
                default='battle',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='studygroupmessage',
            name='battle_xp',
            field=models.IntegerField(default=20),
        ),
    ]
