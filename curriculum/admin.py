from django.contrib import admin
from .models import (
    CurriculumSubject, GradeLevel, Strand, SubStrand,
    ContentStandard, Indicator, Exemplar,
)


class GradeLevelInline(admin.TabularInline):
    model = GradeLevel
    extra = 0


class StrandInline(admin.TabularInline):
    model = Strand
    extra = 0


class SubStrandInline(admin.TabularInline):
    model = SubStrand
    extra = 0


class ContentStandardInline(admin.TabularInline):
    model = ContentStandard
    extra = 0


class IndicatorInline(admin.TabularInline):
    model = Indicator
    extra = 0


class ExemplarInline(admin.TabularInline):
    model = Exemplar
    extra = 0


@admin.register(CurriculumSubject)
class CurriculumSubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'ordering']
    inlines = [GradeLevelInline]


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'code', 'ordering']
    list_filter = ['subject']
    inlines = [StrandInline]


@admin.register(Strand)
class StrandAdmin(admin.ModelAdmin):
    list_display = ['grade', 'name', 'code', 'ordering']
    list_filter = ['grade__subject', 'grade']
    inlines = [SubStrandInline]


@admin.register(SubStrand)
class SubStrandAdmin(admin.ModelAdmin):
    list_display = ['strand', 'name', 'ordering']
    list_filter = ['strand__grade__subject', 'strand__grade']
    inlines = [ContentStandardInline]


@admin.register(ContentStandard)
class ContentStandardAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_statement', 'ordering']
    list_filter = ['sub_strand__strand__grade__subject', 'sub_strand__strand__grade']
    search_fields = ['code', 'statement']
    inlines = [IndicatorInline]

    def short_statement(self, obj):
        return obj.statement[:100]


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_statement', 'term', 'suggested_weeks']
    list_filter = ['term', 'content_standard__sub_strand__strand__grade__subject',
                   'content_standard__sub_strand__strand__grade']
    search_fields = ['code', 'statement']
    inlines = [ExemplarInline]

    def short_statement(self, obj):
        return obj.statement[:100]
