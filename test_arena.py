import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django_tenants.utils import schema_context
from tenants.models import School
from students.models import Student
from academics.models import StudyGroupRoom, StudyGroupMessage

tenant = School.objects.filter(schema_name='school1').first()
if not tenant:
    print('No school1 tenant found')
    exit()

with schema_context(tenant.schema_name):
    try:
        student = Student.objects.first()
        room, _ = StudyGroupRoom.objects.get_or_create(student_class=student.current_class, defaults={'name': 'Arena'})
        print(f'Room: {room}')
        
        # Simulate GET
        last_id = 0
        msgs = StudyGroupMessage.objects.filter(room=room, id__gt=last_id).order_by('created_at')
        print(f"Messages count: {msgs.count()}")
        for m in msgs:
            print(f"[{m.id}] {m.sender} - {m.content}")
            
    except Exception as e:
        print(f'Error: {e}')
