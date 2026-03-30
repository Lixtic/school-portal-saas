"""Import Basic 8 students from data/basic8.csv.

Assumptions mirror import_basic7:
- Uses current AcademicYear (is_current=True).
- Creates Class "Basic 8" for the current academic year if missing.
- All students are female; admission numbers B8-### sequentially.
- Default DOB 2011-01-01, date_of_admission=today, emergency_contact="N/A".
- Usernames slugged from names, deduped; password=password123.
"""

import csv
import os
import re
from datetime import date
from pathlib import Path

import django


BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
import sys

sys.path.append(str(BASE_DIR))
django.setup()

from django.db import connection
from tenants.models import School

schema_name = sys.argv[1] if len(sys.argv) > 1 else None
if not schema_name:
    tenants = list(School.objects.exclude(schema_name='public').values_list('schema_name', flat=True))
    print(f"Usage: python scripts/import_basic8.py <schema_name>\nAvailable: {', '.join(tenants)}")
    sys.exit(1)
tenant = School.objects.get(schema_name=schema_name)
connection.set_tenant(tenant)

from accounts.models import User
from academics.models import AcademicYear, Class
from students.models import Student


CSV_PATH = BASE_DIR / "data" / "basic8.csv"
DEFAULT_DOB = date(2011, 1, 1)
DEFAULT_PASSWORD = "password123"


def slugify_username(name: str) -> str:
    base = re.sub(r"[^a-z0-9]", "", name.lower())
    return base or "student"


def next_admission_number():
    existing = Student.objects.filter(admission_number__startswith="B8-").values_list("admission_number", flat=True)
    max_seq = 0
    for adm in existing:
        try:
            seq = int(adm.split("-")[-1])
            max_seq = max(max_seq, seq)
        except ValueError:
            continue
    return max_seq + 1


def ensure_class():
    ay = AcademicYear.objects.filter(is_current=True).first()
    if not ay:
        ay = AcademicYear.objects.create(name=str(date.today().year), start_date=date.today(), end_date=date.today(), is_current=True)
    cls, _ = Class.objects.get_or_create(name="Basic 8", academic_year=ay)
    return cls


def create_student_record(full_name: str, class_obj: Class, seq_start: int):
    seq = seq_start
    base_username = slugify_username(full_name)
    username = base_username
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base_username}{suffix}"

    admission_number = f"B8-{seq:03d}"

    user = User.objects.create(
        username=username,
        first_name=full_name.title(),
        user_type="student",
        is_active=True,
    )
    user.set_password(DEFAULT_PASSWORD)
    user.save()

    Student.objects.create(
        user=user,
        admission_number=admission_number,
        date_of_birth=DEFAULT_DOB,
        gender="female",
        date_of_admission=date.today(),
        current_class=class_obj,
        roll_number=str(seq),
        emergency_contact="N/A",
    )

    return seq + 1


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

    class_obj = ensure_class()
    seq = next_admission_number()

    created = 0
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("STUDENT NAME") or "").strip()
            if not name:
                continue
            seq = create_student_record(name, class_obj, seq)
            created += 1

    print(f"Created {created} students into class {class_obj.name}")


if __name__ == "__main__":
    main()