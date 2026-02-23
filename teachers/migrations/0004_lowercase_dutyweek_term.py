"""Data migration: Normalize DutyWeek.term values to lowercase."""

from django.db import migrations


def lowercase_terms(apps, schema_editor):
    DutyWeek = apps.get_model('teachers', 'DutyWeek')
    for old, new in [('First', 'first'), ('Second', 'second'), ('Third', 'third')]:
        DutyWeek.objects.filter(term=old).update(term=new)


def revert_terms(apps, schema_editor):
    DutyWeek = apps.get_model('teachers', 'DutyWeek')
    for old, new in [('first', 'First'), ('second', 'Second'), ('third', 'Third')]:
        DutyWeek.objects.filter(term=old).update(term=new)


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0003_lessonplan'),
    ]

    operations = [
        migrations.RunPython(lowercase_terms, revert_terms),
    ]
