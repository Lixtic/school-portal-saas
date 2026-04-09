"""
Centralized GES / NaCCA Curriculum Database.

Stores the national curriculum as a queryable hierarchical tree:
  Subject → Grade → Strand → SubStrand → ContentStandard → Indicator → Exemplar

This is a SHARED (public schema) app so all tenants read from the same
canonical dataset. Teachers never edit this data — it's managed via
the import_curriculum management command or admin.
"""
from django.db import models


class CurriculumSubject(models.Model):
    """Level 1 — e.g. Mathematics, Science, English Language."""
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, blank=True, default='',
                            help_text='Optional short code, e.g. MATH, SCI')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name']
        verbose_name = 'Curriculum Subject'

    def __str__(self):
        return self.name


class GradeLevel(models.Model):
    """Level 2 — e.g. B7 / JHS 1, B8 / JHS 2."""
    subject = models.ForeignKey(CurriculumSubject, on_delete=models.CASCADE,
                                related_name='grades')
    name = models.CharField(max_length=60,
                            help_text='Display name, e.g. "Basic 7 (JHS 1)"')
    code = models.CharField(max_length=20,
                            help_text='GES code prefix, e.g. B7, B8')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'code']
        unique_together = ['subject', 'code']
        verbose_name = 'Grade Level'

    def __str__(self):
        return f'{self.subject.name} — {self.name}'


class Strand(models.Model):
    """Level 3 — e.g. Number, Algebra, Geometry."""
    grade = models.ForeignKey(GradeLevel, on_delete=models.CASCADE,
                              related_name='strands')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name']
        unique_together = ['grade', 'name']

    def __str__(self):
        return f'{self.grade.code} — {self.name}'


class SubStrand(models.Model):
    """Level 4 — e.g. Fractions, Integers, Ratios."""
    strand = models.ForeignKey(Strand, on_delete=models.CASCADE,
                               related_name='sub_strands')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name']
        unique_together = ['strand', 'name']
        verbose_name = 'Sub-Strand'

    def __str__(self):
        return f'{self.strand} › {self.name}'


class ContentStandard(models.Model):
    """Level 5 — The learning goal / content standard statement."""
    sub_strand = models.ForeignKey(SubStrand, on_delete=models.CASCADE,
                                   related_name='content_standards')
    code = models.CharField(max_length=30,
                            help_text='GES code, e.g. B7.1.3.1')
    statement = models.TextField(
        help_text='Full content standard text')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'code']
        unique_together = ['sub_strand', 'code']
        verbose_name = 'Content Standard'

    def __str__(self):
        return f'{self.code}: {self.statement[:80]}'


class Indicator(models.Model):
    """Level 6 — The specific performance indicator."""
    content_standard = models.ForeignKey(ContentStandard, on_delete=models.CASCADE,
                                         related_name='indicators')
    code = models.CharField(max_length=30,
                            help_text='GES indicator code, e.g. B7.1.3.1.1')
    statement = models.TextField(
        help_text='Full indicator statement describing what learners should do')
    suggested_weeks = models.PositiveIntegerField(
        default=1, help_text='Suggested number of weeks for pacing')
    term = models.CharField(max_length=15, blank=True, default='',
                            choices=[('first', 'Term 1'), ('second', 'Term 2'),
                                     ('third', 'Term 3')],
                            help_text='Suggested term placement per GES pacing')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'code']
        unique_together = ['content_standard', 'code']

    def __str__(self):
        return f'{self.code}: {self.statement[:80]}'

    @property
    def full_path(self):
        cs = self.content_standard
        ss = cs.sub_strand
        st = ss.strand
        return f'{st.grade.code} › {st.name} › {ss.name} › {cs.code} › {self.code}'


class Exemplar(models.Model):
    """Suggested classroom activity / exemplar tied to an indicator."""
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE,
                                  related_name='exemplars')
    text = models.TextField(help_text='Exemplar activity description')
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return f'{self.indicator.code} exemplar: {self.text[:60]}'
