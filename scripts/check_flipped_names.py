
import os
import django
import sys
import difflib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from tenants.models import School

schema_name = sys.argv[1] if len(sys.argv) > 1 else None
if not schema_name:
    tenants = list(School.objects.exclude(schema_name='public').values_list('schema_name', flat=True))
    print(f"Usage: python scripts/check_flipped_names.py <schema_name>\nAvailable: {', '.join(tenants)}")
    sys.exit(1)
tenant = School.objects.get(schema_name=schema_name)
connection.set_tenant(tenant)

from students.models import Student
from academics.models import Class

def normalize(s):
    return s.strip().lower()

class_name = "Basic 9"
try:
    c = Class.objects.get(name=class_name)
    students = list(Student.objects.filter(current_class=c))
    print(f"Checking {len(students)} students in {class_name} for similarity...")
    
    seen_names = []
    
    for s in students:
        full_name = f"{s.user.first_name} {s.user.last_name}"
        normalized = normalize(full_name)
        
        # Check against seen
        for existing_name, existing_obj in seen_names:
            ratio = difflib.SequenceMatcher(None, normalized, existing_name).ratio()
            
            # > 0.85 is very similar
            if ratio > 0.85:
                print(f"\nPOSSIBLE DUPLICATE (Match: {ratio:.2f}):")
                print(f"  A: {existing_obj.user.first_name} {existing_obj.user.last_name} (ID: {existing_obj.id}, Adm: {existing_obj.admission_number})")
                print(f"  B: {s.user.first_name} {s.user.last_name} (ID: {s.id}, Adm: {s.admission_number})")
        
        seen_names.append((normalized, s))

except Class.DoesNotExist:
    print(f"Class {class_name} not found.")

print("Check complete.")
