import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()
from django.db import connection
from tenants.models import School
from teachers.models import TeacherAddOn, CreditPack

for t in School.objects.exclude(schema_name='public'):
    connection.set_tenant(t)
    addons = TeacherAddOn.objects.count()
    ai_free = TeacherAddOn.objects.filter(is_free=True, quota_boost__gt=0).count()
    packs = CreditPack.objects.count()
    print(f"{t.schema_name}: {addons} addons ({ai_free} AI/free), {packs} credit packs")
