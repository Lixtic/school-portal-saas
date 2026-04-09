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

        for filepath in options['files']:
            self.stdout.write(f'Importing {filepath}...')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise CommandError(f'Error reading {filepath}: {e}')

            count = self._import_subject(data, clear=options['clear'])
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
            # Cascade deletes grades→strands→...→exemplars
            subject.grades.all().delete()
            self.stdout.write(f'  Cleared existing data for {subject_name}')

        indicator_count = 0

        for g_idx, grade_data in enumerate(data.get('grades', [])):
            grade, _ = GradeLevel.objects.get_or_create(
                subject=subject,
                code=grade_data['code'],
                defaults={
                    'name': grade_data.get('name', grade_data['code']),
                    'ordering': g_idx,
                },
            )

            for s_idx, strand_data in enumerate(grade_data.get('strands', [])):
                strand, _ = Strand.objects.get_or_create(
                    grade=grade,
                    name=strand_data['name'],
                    defaults={
                        'code': strand_data.get('code', ''),
                        'ordering': s_idx,
                    },
                )

                for ss_idx, ss_data in enumerate(strand_data.get('sub_strands', [])):
                    sub_strand, _ = SubStrand.objects.get_or_create(
                        strand=strand,
                        name=ss_data['name'],
                        defaults={
                            'code': ss_data.get('code', ''),
                            'ordering': ss_idx,
                        },
                    )

                    for cs_idx, cs_data in enumerate(ss_data.get('content_standards', [])):
                        content_std, _ = ContentStandard.objects.get_or_create(
                            sub_strand=sub_strand,
                            code=cs_data['code'],
                            defaults={
                                'statement': cs_data.get('statement', ''),
                                'ordering': cs_idx,
                            },
                        )

                        for i_idx, ind_data in enumerate(cs_data.get('indicators', [])):
                            indicator, created = Indicator.objects.get_or_create(
                                content_standard=content_std,
                                code=ind_data['code'],
                                defaults={
                                    'statement': ind_data.get('statement', ''),
                                    'term': ind_data.get('term', ''),
                                    'suggested_weeks': ind_data.get('suggested_weeks', 1),
                                    'ordering': i_idx,
                                },
                            )
                            if created:
                                indicator_count += 1

                            for e_idx, ex_text in enumerate(ind_data.get('exemplars', [])):
                                Exemplar.objects.get_or_create(
                                    indicator=indicator,
                                    text=ex_text,
                                    defaults={'ordering': e_idx},
                                )

        return indicator_count
