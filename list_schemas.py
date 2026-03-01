import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from tenants.models import School
for s in School.objects.all():
    print(s.schema_name)
