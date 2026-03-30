"""Import teachers from CSV and assign subjects.

CSV columns expected:
- Name of Subject Teacher
- Email Address
- Subject

Behavior:
- Ensures Subject exists (maps common aliases) and attaches to teacher.
- Creates User (user_type=teacher) + Teacher profile if missing (keyed by email).
- employee_id auto-generated T###.
- Sets password=password123; DOB=1990-01-01; DOJ=today; qualification blank.
- Adds subject to Teacher.subjects M2M.
"""

import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
sys.path.append(str(BASE_DIR))
django.setup()

from django.db import connection
from tenants.models import School

schema_name = sys.argv[1] if len(sys.argv) > 1 else None
if not schema_name:
    tenants = list(School.objects.exclude(schema_name='public').values_list('schema_name', flat=True))
    print(f"Usage: python scripts/import_subject_teachers.py <schema_name>\nAvailable: {', '.join(tenants)}")
    sys.exit(1)
tenant = School.objects.get(schema_name=schema_name)
connection.set_tenant(tenant)

from accounts.models import User
from academics.models import Subject
from teachers.models import Teacher

DEFAULT_PASSWORD = "password123"
DEFAULT_DOB = date(1990, 1, 1)
DEFAULT_DOJ = date.today()

SUBJECT_ALIASES = {
    "MATHS": "Mathematics",
    "MATH": "Mathematics",
    "ENGLISH": "English Language",
    "SCIENCE": "Integrated Science",
    "RME": "Religious & Moral Education",
    "ICT": "ICT",
    "COMPUTING": "ICT",
    "CREATIVE ARTS": "Creative Arts",
    "CAREER TECH": "Career Technology",
    "GONJA": "Gonja",
}


def subject_for_label(label: str):
    key = (label or "").strip().upper()
    if not key:
        return None
    name = SUBJECT_ALIASES.get(key, label.title().strip())
    code = re.sub(r"[^A-Z0-9]", "", name.upper())[:10] or key[:10]
    subj, created = Subject.objects.get_or_create(code=code, defaults={"name": name})
    # if code clash but name differs, update name
    if subj.name != name:
        subj.name = name
        subj.save(update_fields=["name"])
    return subj, created


def next_employee_id():
    existing = Teacher.objects.values_list("employee_id", flat=True)
    max_seq = 0
    for emp in existing:
        if emp and emp.startswith("T"):
            try:
                seq = int(emp[1:])
                max_seq = max(max_seq, seq)
            except ValueError:
                continue
    return f"T{max_seq + 1:03d}"


def get_or_create_teacher(name: str, email: str) -> Teacher:
    email_norm = (email or "").strip().lower()
    teacher = None
    user = None

    if email_norm:
        user = User.objects.filter(email__iexact=email_norm).first()
        if user:
            teacher = Teacher.objects.filter(user=user).first()

    if not user:
        username_base = re.sub(r"[^a-z0-9]", "", (email_norm.split("@", 1)[0] if email_norm else name.lower()).strip()) or "teacher"
        username = username_base
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{username_base}{suffix}"

        user = User.objects.create(
            username=username,
            first_name=name.title(),
            email=email_norm,
            user_type="teacher",
            is_active=True,
        )
        user.set_password(DEFAULT_PASSWORD)
        user.save()

    if not teacher:
        employee_id = next_employee_id()
        teacher, _ = Teacher.objects.get_or_create(
            user=user,
            defaults={
                "employee_id": employee_id,
                "date_of_birth": DEFAULT_DOB,
                "date_of_joining": DEFAULT_DOJ,
                "qualification": "",
            },
        )
    return teacher


def main(csv_path: str):
    path = Path(csv_path)
    if not path.is_absolute():
        path = BASE_DIR / csv_path
    if not path.exists():
        raise FileNotFoundError(f"CSV not found at {path}")

    created_teachers = 0
    updated_teachers = 0
    created_subjects = 0

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name of Subject Teacher") or "").strip()
            email = (row.get("Email Address") or "").strip()
            subject_label = (row.get("Subject") or "").strip()
            if not name or not subject_label:
                continue

            subject, subj_created = subject_for_label(subject_label)
            if subj_created:
                created_subjects += 1
            teacher = get_or_create_teacher(name, email)

            if subject:
                before_count = teacher.subjects.count()
                teacher.subjects.add(subject)
                after_count = teacher.subjects.count()
                if after_count > before_count:
                    updated_teachers += 1
            else:
                continue

    print("Import complete.")
    print(f"Subjects created this run: {created_subjects}")
    print(f"Teacher-subject links added: {updated_teachers}")
    print(f"Teachers total: {Teacher.objects.count()}")
    print(f"Subjects total: {Subject.objects.count()}")


if __name__ == "__main__":
    main("data/subject_teachers.csv")
