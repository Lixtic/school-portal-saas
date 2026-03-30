"""Assign subjects to Basic 7/8/9 classes for current academic year.

- Ensures classes Basic 7/8/9 exist for the current AcademicYear (is_current=True).
- For each subject in the core list, picks the first available teacher linked to that subject (if any) and creates/updates ClassSubject.
- Safe to re-run; uses get_or_create on ClassSubject.
"""

import os
import sys
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
    print(f"Usage: python scripts/assign_class_subjects.py <schema_name>\nAvailable: {', '.join(tenants)}")
    sys.exit(1)
tenant = School.objects.get(schema_name=schema_name)
connection.set_tenant(tenant)

from academics.models import AcademicYear, Class, Subject, ClassSubject
from teachers.models import Teacher


CORE_SUBJECT_NAMES = [
    "Mathematics",
    "English Language",
    "Integrated Science",
    "Social Studies",
    "Religious & Moral Education",
    "Creative Arts",
    "Career Technology",
    "ICT",
    "Gonja",
]


def get_current_year():
    ay = AcademicYear.objects.filter(is_current=True).first()
    if not ay:
        raise RuntimeError("No AcademicYear marked is_current=True")
    return ay


def ensure_classes(ay):
    classes = {}
    for name in ["Basic 7", "Basic 8", "Basic 9"]:
        cls, _ = Class.objects.get_or_create(name=name, academic_year=ay)
        classes[name] = cls
    return classes


def pick_teacher_for_subject(subj: Subject):
    return (
        Teacher.objects.filter(subjects=subj)
        .select_related("user")
        .order_by("id")
        .first()
    )


def assign_for_class(cls: Class):
    created = 0
    updated = 0
    for subj_name in CORE_SUBJECT_NAMES:
        subj = Subject.objects.filter(name__iexact=subj_name).first()
        if not subj:
            continue
        teacher = pick_teacher_for_subject(subj)
        cs, made = ClassSubject.objects.get_or_create(
            class_name=cls,
            subject=subj,
            defaults={"teacher": teacher},
        )
        if made:
            created += 1
        else:
            # update teacher if different
            if cs.teacher != teacher:
                cs.teacher = teacher
                cs.save(update_fields=["teacher"])
                updated += 1
    return created, updated


def main():
    ay = get_current_year()
    classes = ensure_classes(ay)
    total_created = 0
    total_updated = 0
    for cls in classes.values():
        c, u = assign_for_class(cls)
        total_created += c
        total_updated += u

    print(f"Assigned subjects for classes in {ay.name}. Created: {total_created}, Updated: {total_updated}")


if __name__ == "__main__":
    main()