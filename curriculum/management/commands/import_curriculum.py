"""
Import GES / NaCCA curriculum data from a JSON file.

Usage:
    python manage.py import_curriculum curriculum/data/b7_mathematics.json
    python manage.py import_curriculum curriculum/data/*.json --clear

JSON format:
{
  "subject": "Mathematics",
  "subject_code": "MATH",
  "grades": [
    {
      "name": "Basic 7 (JHS 1)",
      "code": "B7",
      "strands": [
        {
          "name": "Number",
          "sub_strands": [
            {
              "name": "Integers",
              "content_standards": [
                {
                  "code": "B7.1.1.1",
                  "statement": "Demonstrate understanding of...",
                  "indicators": [
                    {
                      "code": "B7.1.1.1.1",
                      "statement": "Identify and describe integers...",
                      "term": "first",
                      "suggested_weeks": 2,
                      "exemplars": [
                        "Use number lines to represent integers..."
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculum.models import (
    CurriculumSubject, GradeLevel, Strand, SubStrand,
    ContentStandard, Indicator, Exemplar,
)


class Command(BaseCommand):
    help = 'Import GES/NaCCA curriculum data from JSON file(s)'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str,
                            help='Path(s) to JSON curriculum file(s)')
        parser.add_argument('--clear', action='store_true',
                            help='Clear existing data for matching subjects before import')

    def handle(self, *args, **options):
        total_indicators = 0
        cleared_subjects = set()  # track which subjects were already cleared

        for filepath in options['files']:
            self.stdout.write(f'Importing {filepath}...')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise CommandError(f'Error reading {filepath}: {e}')

            subject_name = data.get('subject', '').strip()
            should_clear = options['clear'] and subject_name not in cleared_subjects
            count = self._import_subject(data, clear=should_clear)
            if should_clear:
                cleared_subjects.add(subject_name)
            total_indicators += count
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ {filepath}: {count} indicators imported'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Total indicators imported: {total_indicators}'))

    @transaction.atomic
    def _import_subject(self, data, clear=False):
        subject_name = data.get('subject', '').strip()
        subject_code = data.get('subject_code', '').strip()
        if not subject_name:
            raise CommandError('JSON must have a "subject" field')

        subject, _ = CurriculumSubject.objects.get_or_create(
            name=subject_name,
            defaults={'code': subject_code},
        )
        if subject_code and not subject.code:
            subject.code = subject_code
            subject.save(update_fields=['code'])

        if clear:
            subject.grades.all().delete()
            self.stdout.write(f'  Cleared existing data for {subject_name}')

        indicator_count = 0

        for g_idx, grade_data in enumerate(data.get('grades', [])):
            grade, created = GradeLevel.objects.get_or_create(
                subject=subject,
                code=grade_data['code'],
                defaults={
                    'name': grade_data.get('name', grade_data['code']),
                    'ordering': g_idx,
                },
            )

            if not created:
                # Grade exists — delete old children and re-import fresh
                grade.strands.all().delete()

            # Collect all objects to bulk-create per level
            strand_objs = []
            for s_idx, strand_data in enumerate(grade_data.get('strands', [])):
                strand_objs.append((
                    Strand(
                        grade=grade,
                        name=strand_data['name'],
                        code=strand_data.get('code', ''),
                        ordering=s_idx,
                    ),
                    strand_data,
                ))

            # Bulk-create strands (one query)
            created_strands = Strand.objects.bulk_create(
                [s for s, _ in strand_objs])

            sub_strand_objs = []
            for strand, strand_data in zip(created_strands, [d for _, d in strand_objs]):
                for ss_idx, ss_data in enumerate(strand_data.get('sub_strands', [])):
                    sub_strand_objs.append((
                        SubStrand(
                            strand=strand,
                            name=ss_data['name'],
                            code=ss_data.get('code', ''),
                            ordering=ss_idx,
                        ),
                        ss_data,
                    ))

            created_sub_strands = SubStrand.objects.bulk_create(
                [ss for ss, _ in sub_strand_objs])

            cs_objs = []
            for sub_strand, ss_data in zip(
                    created_sub_strands, [d for _, d in sub_strand_objs]):
                for cs_idx, cs_data in enumerate(ss_data.get('content_standards', [])):
                    cs_objs.append((
                        ContentStandard(
                            sub_strand=sub_strand,
                            code=cs_data['code'],
                            statement=cs_data.get('statement', ''),
                            ordering=cs_idx,
                        ),
                        cs_data,
                    ))

            created_cs = ContentStandard.objects.bulk_create(
                [cs for cs, _ in cs_objs])

            ind_objs = []
            for content_std, cs_data in zip(
                    created_cs, [d for _, d in cs_objs]):
                for i_idx, ind_data in enumerate(cs_data.get('indicators', [])):
                    ind_objs.append((
                        Indicator(
                            content_standard=content_std,
                            code=ind_data['code'],
                            statement=ind_data.get('statement', ''),
                            term=ind_data.get('term', ''),
                            suggested_weeks=ind_data.get('suggested_weeks', 1),
                            ordering=i_idx,
                        ),
                        ind_data,
                    ))

            created_indicators = Indicator.objects.bulk_create(
                [ind for ind, _ in ind_objs])
            indicator_count += len(created_indicators)

            exemplar_objs = []
            for indicator, ind_data in zip(
                    created_indicators, [d for _, d in ind_objs]):
                for e_idx, ex_text in enumerate(ind_data.get('exemplars', [])):
                    exemplar_objs.append(Exemplar(
                        indicator=indicator,
                        text=ex_text,
                        ordering=e_idx,
                    ))

            if exemplar_objs:
                Exemplar.objects.bulk_create(exemplar_objs)

        return indicator_count
