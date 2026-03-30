import os
import sys
import django
import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
from tenants.models import School

schema_name = sys.argv[1] if len(sys.argv) > 1 else None
if not schema_name:
    tenants = list(School.objects.exclude(schema_name='public').values_list('schema_name', flat=True))
    print(f"Usage: python scripts/update_timetable_from_image.py <schema_name>\nAvailable: {', '.join(tenants)}")
    sys.exit(1)
tenant = School.objects.get(schema_name=schema_name)
connection.set_tenant(tenant)

from academics.models import AcademicYear, Class, Subject, ClassSubject, Timetable
from teachers.models import Teacher

# Subject name mapping (Image Name -> Database Name)
SUBJECT_MAPPING = {
    "Maths": "Mathematics",
    "Science": "Integrated Science",
    "Career Technology": "Career Technology",
    "Library": "Library",
    "English": "English Language",
    "Computing": "ICT",
    "Social Studies": "Social Studies",
    "Creative Arts & Design": "Creative Arts",
    "R.M.E.": "Religious & Moral Education",
    "Gonja": "Gonja",
    "Physical & Health Education": "Physical Education",
    "English/Library": "English Language", 
}

# Timetable Data from Image
TIMETABLE_DATA = {
    "Basic 7": {
        "Monday": [
            ("07:00", "08:40", "Maths"),
            ("08:40", "09:50", "Career Technology"),
            ("10:20", "11:30", "Science"),
            ("11:30", "12:40", "Library"),
            ("13:00", "14:00", "English"),
        ],
        "Tuesday": [
            ("07:00", "08:40", "Computing"),
            ("08:40", "09:50", "Maths"),
            ("10:20", "11:30", "Creative Arts & Design"),
            ("11:30", "12:40", "Career Technology"),
            ("13:00", "14:00", "R.M.E."),
        ],
        "Wednesday": [
            ("07:00", "08:40", "English"),
            ("08:40", "09:50", "Social Studies"),
            ("10:20", "11:30", "Career Technology"),
            ("11:30", "12:40", "Creative Arts & Design"),
            ("13:00", "14:00", "Science"),
        ],
        "Thursday": [
            ("07:00", "08:40", "Science"),
            ("08:40", "09:50", "Computing"),
            ("10:20", "11:30", "Gonja"),
            ("11:30", "12:40", "English"),
            ("13:00", "14:00", "Social Studies"),
        ],
        "Friday": [
            ("07:00", "08:40", "Maths"),
            ("08:40", "09:50", "Social Studies"),
            ("10:20", "11:30", "R.M.E."),
            ("11:30", "12:40", "Physical & Health Education"),
            ("13:00", "14:00", "Physical & Health Education"),
        ]
    },
    "Basic 8": {
        "Monday": [
            ("07:00", "08:40", "Science"),
            ("08:40", "09:50", "Gonja"),
            ("10:20", "11:30", "Career Technology"),
            ("11:30", "12:40", "English"), # Simplified English/Library
            ("13:00", "14:00", "Social Studies"),
        ],
        "Tuesday": [
            ("07:00", "08:40", "Social Studies"),
            ("08:40", "09:50", "Career Technology"),
            ("10:20", "11:30", "English"),
            ("11:30", "12:40", "Computing"),
            ("13:00", "14:00", "Creative Arts & Design"),
        ],
        "Wednesday": [
            ("07:00", "08:40", "Creative Arts & Design"),
            ("08:40", "09:50", "Science"),
            ("10:20", "11:30", "Gonja"),
            ("11:30", "12:40", "Maths"),
            ("13:00", "14:00", "R.M.E."),
        ],
        "Thursday": [
            ("07:00", "08:40", "Maths"),
            ("08:40", "09:50", "English"),
            ("10:20", "11:30", "Social Studies"),
            ("11:30", "12:40", "Computing"),
            ("13:00", "14:00", "Science"),
        ],
        "Friday": [
            ("07:00", "08:40", "R.M.E."),
            ("08:40", "09:50", "Maths"),
            ("10:20", "11:30", "English"),
            ("11:30", "12:40", "Physical & Health Education"),
            ("13:00", "14:00", "Physical & Health Education"),
        ]
    },
    "Basic 9": {
        "Monday": [
            ("07:00", "08:40", "English"),
            ("08:40", "09:50", "Social Studies"),
            ("10:20", "11:30", "Maths"),
            ("11:30", "12:40", "Library"),
            ("13:00", "14:00", "Computing"),
        ],
        "Tuesday": [
            ("07:00", "08:40", "Science"),
            ("08:40", "09:50", "Social Studies"),
            ("10:20", "11:30", "Computing"),
            ("11:30", "12:40", "Maths"),
            ("13:00", "14:00", "English"),
        ],
        "Wednesday": [
            ("07:00", "08:40", "Maths"),
            ("08:40", "09:50", "Career Technology"),
            ("10:20", "11:30", "R.M.E."),
            ("11:30", "12:40", "Science"),
            ("13:00", "14:00", "Creative Arts & Design"),
        ],
        "Thursday": [
            ("07:00", "08:40", "Social Studies"),
            ("08:40", "09:50", "Career Technology"),
            ("10:20", "11:30", "Science"),
            ("11:30", "12:40", "R.M.E."),
            ("13:00", "14:00", "Gonja"),
        ],
        "Friday": [
            ("07:00", "08:40", "Gonja"),
            ("08:40", "09:50", "English"),
            ("10:20", "11:30", "Creative Arts & Design"),
            ("11:30", "12:40", "Physical & Health Education"),
            ("13:00", "14:00", "Physical & Health Education"),
        ]
    }
}

DAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4
}

def run():
    print("Starting timetable update...")
    
    # 1. Get Current Academic Year
    try:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year:
            print("No active academic year found. Creating a default one.")
            academic_year = AcademicYear.objects.create(
                name="2025/2026",
                start_date=datetime.date(2025, 9, 10),
                end_date=datetime.date(2026, 7, 20),
                is_current=True
            )
    except Exception as e:
        print(f"Error getting academic year: {e}")
        return

    # 2. Ensure Subjects Exist
    print("Verifying subjects...")
    all_subject_names = set(SUBJECT_MAPPING.values())
    for name in all_subject_names:
        if not Subject.objects.filter(name=name).exists():
            print(f"Creating subject: {name}")
            # Generate a simple code
            code = name[:3].upper() + name[-1].upper() if len(name) > 3 else name.upper()
            if Subject.objects.filter(code=code).exists():
                code = f"{code}2"
            Subject.objects.create(name=name, code=code)

    # 3. Process each class
    for class_name, schedule in TIMETABLE_DATA.items():
        print(f"\nProcessing {class_name}...")
        
        # Get/Create Class
        school_class, created = Class.objects.get_or_create(
            name=class_name, 
            academic_year=academic_year
        )
        if created:
            print(f"Created class '{class_name}'")

        # Clear existing timetable for this class to avoid duplicates
        # We find all class_subjects for this class and delete their timetables
        class_subjects = ClassSubject.objects.filter(class_name=school_class)
        for cs in class_subjects:
            Timetable.objects.filter(class_subject=cs).delete()
        print(f"Cleared existing timetable entries for {class_name}")

        # Create entries
        for day_name, lessons in schedule.items():
            day_idx = DAY_MAP[day_name]
            
            for start, end, raw_subject in lessons:
                db_subject_name = SUBJECT_MAPPING.get(raw_subject, raw_subject)
                
                # Get Subject Object
                try:
                    subject = Subject.objects.get(name=db_subject_name)
                except Subject.DoesNotExist:
                    print(f"Warning: Subject '{db_subject_name}' not found! Skipping.")
                    continue
                except Subject.MultipleObjectsReturned:
                    # Handle duplicates by taking the first one
                    subject = Subject.objects.filter(name=db_subject_name).first()

                # Get/Create ClassSubject Link
                class_subject, cs_created = ClassSubject.objects.get_or_create(
                    class_name=school_class,
                    subject=subject,
                    defaults={'teacher': None} # Teacher to be assigned later
                )
                
                # Create Timetable Entry
                Timetable.objects.create(
                    class_subject=class_subject,
                    day=day_idx,
                    start_time=datetime.datetime.strptime(start, "%H:%M").time(),
                    end_time=datetime.datetime.strptime(end, "%H:%M").time()
                )
    
    print("\nTimetable update complete!")

if __name__ == "__main__":
    run()
