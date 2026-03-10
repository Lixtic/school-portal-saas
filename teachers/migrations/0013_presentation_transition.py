from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0012_presentation_share_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentation',
            name='transition',
            field=models.CharField(
                choices=[('slide', 'Slide'), ('fade', 'Fade'), ('zoom', 'Zoom'), ('flip', 'Flip')],
                default='slide',
                max_length=20,
            ),
        ),
    ]
