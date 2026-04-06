"""
seed_math_questions — Populate the QuestionBank with 200 BECE-aligned
Mathematics items.  Idempotent: skips if ≥200 Maths questions already exist.

Usage (inside a tenant schema):
    python manage.py seed_math_questions --schema=school1

Or from a standalone script after setting the tenant via connection.set_tenant().
"""

from django.core.management.base import BaseCommand
from django.db import connection

from academics.models import Subject
from accounts.models import User
from teachers.models import QuestionBank
from teachers.math_question_bank import MATH_QUESTION_BANK


class Command(BaseCommand):
    help = "Seed 200 NaCCA-aligned Mathematics questions into the QuestionBank."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            type=str,
            default=None,
            help="Tenant schema_name to seed into (optional if already in tenant context).",
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

        # ── Resolve subject ───────────────────────────────────
        subject = Subject.objects.filter(name__icontains="math").first()
        if not subject:
            subject = Subject.objects.create(name="Mathematics")
            self.stdout.write(self.style.SUCCESS("Created 'Mathematics' subject."))

        # ── Resolve teacher (use first admin user) ────────────
        teacher = User.objects.filter(user_type="admin").first()
        if not teacher:
            teacher = User.objects.first()
        if not teacher:
            self.stderr.write(self.style.ERROR("No users exist. Create a user first."))
            return

        # ── Idempotency check ─────────────────────────────────
        existing = QuestionBank.objects.filter(subject=subject).count()
        if existing >= 200:
            self.stdout.write(
                self.style.WARNING(
                    f"Already {existing} Mathematics questions — skipping seed."
                )
            )
            return

        # ── Bulk-create questions ─────────────────────────────
        # QuestionBank model doesn't have 'ges_code' or 'bloom' fields,
        # so we store them in the explanation field for reference and
        # drop them from the create kwargs.
        objs = []
        for item in MATH_QUESTION_BANK:
            # Map essay → short for model compatibility (model has no 'essay' choice)
            fmt = item["question_format"]
            if fmt == "essay":
                fmt = "short"

            explanation = item["explanation"]
            ges_code = item.get("ges_code", "")
            bloom = item.get("bloom", "")
            if ges_code or bloom:
                explanation = f"[{ges_code} | {bloom}] {explanation}"

            objs.append(
                QuestionBank(
                    teacher=teacher,
                    subject=subject,
                    topic=item["topic"],
                    question_text=item["question_text"],
                    question_format=fmt,
                    difficulty=item["difficulty"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=explanation,
                )
            )

        QuestionBank.objects.bulk_create(objs, ignore_conflicts=True)
        final_count = QuestionBank.objects.filter(subject=subject).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {final_count} Mathematics questions now in the bank."
            )
        )
