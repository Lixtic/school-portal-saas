from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0028_add_ges_fields_to_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonplan',
            name='share_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
