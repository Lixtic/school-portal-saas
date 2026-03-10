import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0011_livesession_pollresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentation',
            name='share_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
