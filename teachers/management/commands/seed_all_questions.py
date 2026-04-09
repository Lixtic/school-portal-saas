"""
seed_all_questions — Seed BECE-aligned questions for all 8 JHS subjects
into the QuestionBank.  Idempotent per subject.

Usage:
    python manage.py seed_all_questions --schema=school1

Subjects seeded: Mathematics, English Language, Integrated Science,
Social Studies, RME, Computing, Career Technology, French.
"""

from django.core.management.base import BaseCommand
from django.db import connection

from academics.models import Subject
from accounts.models import User
from teachers.models import QuestionBank

# ── Subject bank imports ──────────────────────────────────────
from teachers.math_question_bank import MATH_QUESTION_BANK
from teachers.english_question_bank import ENGLISH_QUESTION_BANK
from teachers.science_question_bank import SCIENCE_QUESTION_BANK
from teachers.social_studies_question_bank import SOCIAL_STUDIES_QUESTION_BANK
from teachers.rme_question_bank import RME_QUESTION_BANK
from teachers.computing_question_bank import COMPUTING_QUESTION_BANK
from teachers.career_tech_question_bank import CAREER_TECH_QUESTION_BANK
from teachers.french_question_bank import FRENCH_QUESTION_BANK


# Map display bloom text → model choice key
BLOOM_MAP = {
    "Knowledge": "knowledge",
    "Comprehension": "comprehension",
    "Application": "application",
    "Analysis": "analysis",
    "Synthesis": "synthesis",
    "Evaluation": "synthesis",
    "Synthesis/Eval": "synthesis",
}

# Subject lookup keyword → (display name for creation, bank list, min threshold)
SUBJECT_BANKS = [
    ("math",            "Mathematics",          MATH_QUESTION_BANK,            200),
    ("english",         "English Language",      ENGLISH_QUESTION_BANK,          50),
    ("science",         "Integrated Science",    SCIENCE_QUESTION_BANK,          50),
    ("social",          "Social Studies",        SOCIAL_STUDIES_QUESTION_BANK,   50),
    ("rme",             "RME",                   RME_QUESTION_BANK,              50),
    ("comput",          "Computing",             COMPUTING_QUESTION_BANK,        50),
    ("career",          "Career Technology",     CAREER_TECH_QUESTION_BANK,      50),
    ("french",          "French",                FRENCH_QUESTION_BANK,           50),
]


class Command(BaseCommand):
    help = "Seed BECE-aligned questions for all 8 JHS subjects."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            type=str,
            default=None,
            help="Tenant schema_name to seed into.",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default=None,
            help="Seed only a specific subject (keyword match, e.g. 'math', 'french').",
        )

    def handle(self, *args, **options):
        # ── Optionally switch tenant schema ───────────────────
        schema = options.get("schema")
        if schema:
            from tenants.models import School
            try:
                tenant = School.objects.get(schema_name=schema)
            except School.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Tenant '{schema}' not found."))
                return
            connection.set_tenant(tenant)
            self.stdout.write(f"Switched to schema: {schema}")

        # ── Resolve teacher (first admin user) ────────────────
        teacher = User.objects.filter(user_type="admin").first()
        if not teacher:
            teacher = User.objects.first()
        if not teacher:
            self.stderr.write(self.style.ERROR("No users exist. Create a user first."))
            return

        filter_subject = (options.get("subject") or "").lower()
        total_created = 0

        for keyword, display_name, bank, threshold in SUBJECT_BANKS:
            if filter_subject and filter_subject not in keyword:
                continue

            # ── Resolve or create subject ─────────────────────
            subject = Subject.objects.filter(name__icontains=keyword).first()
            if not subject:
                subject = Subject.objects.create(name=display_name)
                self.stdout.write(self.style.SUCCESS(f"  Created subject: {display_name}"))

            # ── Idempotency check ─────────────────────────────
            existing = QuestionBank.objects.filter(subject=subject).count()
            if existing >= threshold:
                self.stdout.write(
                    self.style.WARNING(
                        f"  {display_name}: already {existing} questions — skipped."
                    )
                )
                continue

            # ── Build objects ─────────────────────────────────
            objs = []
            for item in bank:
                fmt = item["question_format"]
                if fmt == "essay":
                    fmt = "short"

                bloom_raw = item.get("bloom", "")
                bloom_key = BLOOM_MAP.get(bloom_raw, bloom_raw.lower() if bloom_raw else "")

                objs.append(
                    QuestionBank(
                        teacher=teacher,
                        subject=subject,
                        topic=item["topic"],
                        strand=item.get("strand", ""),
                        sub_strand=item.get("sub_strand", ""),
                        indicator_code=item.get("ges_code", ""),
                        bloom_level=bloom_key,
                        question_text=item["question_text"],
                        question_format=fmt,
                        difficulty=item["difficulty"],
                        options=item["options"],
                        correct_answer=item["correct_answer"],
                        explanation=item["explanation"],
                    )
                )

            created = QuestionBank.objects.bulk_create(objs, ignore_conflicts=True)
            count = len(created)
            total_created += count
            final = QuestionBank.objects.filter(subject=subject).count()
            self.stdout.write(
                self.style.SUCCESS(f"  {display_name}: +{count} → {final} total")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nDone — {total_created} questions seeded across subjects.")
        )
