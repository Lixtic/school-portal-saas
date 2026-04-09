"""
Curriculum API — public, read-only endpoints for querying the
centralized GES/NaCCA curriculum database.

All endpoints return JSON. No authentication required (curriculum is public data).
"""
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render

from .models import (
    CurriculumSubject, GradeLevel, Strand, SubStrand,
    ContentStandard, Indicator, Exemplar,
)


def curriculum_subjects(request):
    """List all curriculum subjects."""
    subjects = CurriculumSubject.objects.values('id', 'name', 'code')
    return JsonResponse({'items': list(subjects)})


def curriculum_grades(request):
    """List grade levels, optionally filtered by subject."""
    qs = GradeLevel.objects.select_related('subject')
    subject_id = request.GET.get('subject_id')
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    items = [{'id': g.id, 'name': g.name, 'code': g.code,
              'subject': g.subject.name} for g in qs]
    return JsonResponse({'items': items})


def curriculum_strands(request):
    """List strands for a given grade level."""
    grade_id = request.GET.get('grade_id')
    if not grade_id:
        return JsonResponse({'items': []})
    qs = Strand.objects.filter(grade_id=grade_id).values('id', 'name', 'code')
    return JsonResponse({'items': list(qs)})


def curriculum_indicators(request):
    """
    Primary endpoint for the lesson plan form.

    Accepts flexible filtering:
      - subject_name + grade_code  (fuzzy match against curriculum)
      - strand / sub_strand / topic  (searches strand + sub-strand names)
      - q  (free text search across all levels)

    Returns a flat list of indicators with their full hierarchy path.
    """
    subject_name = (request.GET.get('subject_name') or '').strip()
    grade_code = (request.GET.get('grade_code') or '').strip()
    topic = (request.GET.get('topic') or '').strip()
    sub_strand_q = (request.GET.get('sub_strand') or '').strip()
    term = (request.GET.get('term') or '').strip()
    q = (request.GET.get('q') or '').strip()

    qs = Indicator.objects.select_related(
        'content_standard__sub_strand__strand__grade__subject',
    )

    # Filter by subject (fuzzy)
    if subject_name:
        # Try exact first, then contains, then aliases
        subject_match = CurriculumSubject.objects.filter(name__iexact=subject_name).first()
        if not subject_match:
            subject_match = CurriculumSubject.objects.filter(name__icontains=subject_name).first()
        if not subject_match:
            # Reverse: check if any curriculum subject name is contained in the query
            for s in CurriculumSubject.objects.all():
                if s.name.lower() in subject_name.lower():
                    subject_match = s
                    break
        if not subject_match:
            # Try alias mapping for common school subject names
            alias = _SUBJECT_ALIASES.get(subject_name.lower())
            if alias:
                subject_match = CurriculumSubject.objects.filter(name__iexact=alias).first()
        if subject_match:
            qs = qs.filter(content_standard__sub_strand__strand__grade__subject=subject_match)
        else:
            return JsonResponse({'items': [], 'matched_topic': '', 'matched_indicator': ''})

    # Filter by grade code (e.g. B7, B8, "Basic 7")
    if grade_code:
        # Normalize: "Basic 7" → "B7", "JHS 1" → "B7", or pass through
        normalized = _normalize_grade(grade_code)
        qs = qs.filter(
            Q(content_standard__sub_strand__strand__grade__code__iexact=normalized) |
            Q(content_standard__sub_strand__strand__grade__name__icontains=grade_code)
        )

    # Filter by term
    if term:
        qs = qs.filter(term=term)

    # Filter by topic (matches strand or sub-strand name)
    if topic:
        qs = qs.filter(
            Q(content_standard__sub_strand__strand__name__icontains=topic) |
            Q(content_standard__sub_strand__name__icontains=topic)
        )

    # Filter by sub_strand
    if sub_strand_q:
        qs = qs.filter(content_standard__sub_strand__name__icontains=sub_strand_q)

    # Free text search across all text fields
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(statement__icontains=q) |
            Q(content_standard__code__icontains=q) |
            Q(content_standard__statement__icontains=q) |
            Q(content_standard__sub_strand__name__icontains=q) |
            Q(content_standard__sub_strand__strand__name__icontains=q)
        )

    qs = qs.distinct()[:50]

    items = []
    matched_indicator = ''
    matched_topic = ''

    for ind in qs:
        cs = ind.content_standard
        ss = cs.sub_strand
        st = ss.strand
        gl = st.grade

        item = {
            'code': ind.code,
            'indicator': ind.statement,
            'content_standard': cs.statement,
            'content_standard_code': cs.code,
            'sub_strand': ss.name,
            'strand': st.name,
            'grade': gl.name,
            'grade_code': gl.code,
            'subject': gl.subject.name,
            'term': ind.term,
            'suggested_weeks': ind.suggested_weeks,
            # For compatibility with existing SOW dropdown format
            'topic': st.name,
            'code_only': False,
        }
        items.append(item)

        # Auto-match: if topic matches a strand/sub-strand, pick first indicator
        if topic and not matched_indicator:
            topic_lower = topic.lower()
            if (topic_lower in st.name.lower() or topic_lower in ss.name.lower()
                    or st.name.lower() in topic_lower or ss.name.lower() in topic_lower):
                matched_topic = ss.name
                matched_indicator = f'{ind.code} — {ind.statement}'

    return JsonResponse({
        'items': items,
        'matched_topic': matched_topic,
        'matched_indicator': matched_indicator,
    })


def curriculum_pacing(request):
    """
    Generate a term pacing guide: returns indicators in suggested order
    with week assignments for a given subject + grade + term.
    """
    subject_name = (request.GET.get('subject_name') or '').strip()
    grade_code = (request.GET.get('grade_code') or '').strip()
    term = (request.GET.get('term') or '').strip()

    if not subject_name or not grade_code or not term:
        return JsonResponse({'error': 'subject_name, grade_code, and term are required'}, status=400)

    normalized = _normalize_grade(grade_code)

    indicators = Indicator.objects.filter(
        term=term,
        content_standard__sub_strand__strand__grade__code__iexact=normalized,
        content_standard__sub_strand__strand__grade__subject__name__icontains=subject_name,
    ).select_related(
        'content_standard__sub_strand__strand',
    ).order_by('ordering', 'code')

    weeks = []
    current_week = 1
    for ind in indicators:
        cs = ind.content_standard
        ss = cs.sub_strand
        st = ss.strand
        weeks.append({
            'week_start': current_week,
            'week_end': current_week + ind.suggested_weeks - 1,
            'strand': st.name,
            'sub_strand': ss.name,
            'content_standard': cs.statement,
            'content_standard_code': cs.code,
            'indicator_code': ind.code,
            'indicator': ind.statement,
        })
        current_week += ind.suggested_weeks

    return JsonResponse({'term': term, 'total_weeks': current_week - 1, 'pacing': weeks})


# ── Helpers ───────────────────────────────────────────────────

_GRADE_MAP = {
    'basic 1': 'B1', 'basic 2': 'B2', 'basic 3': 'B3',
    'basic 4': 'B4', 'basic 5': 'B5', 'basic 6': 'B6',
    'basic 7': 'B7', 'basic 8': 'B8', 'basic 9': 'B9',
    'jhs 1': 'B7', 'jhs 2': 'B8', 'jhs 3': 'B9',
    'jhs1': 'B7', 'jhs2': 'B8', 'jhs3': 'B9',
    'shs 1': 'S1', 'shs 2': 'S2', 'shs 3': 'S3',
}

# Map common school subject names to curriculum DB names
_SUBJECT_ALIASES = {
    'ict': 'Computing',
    'i.c.t': 'Computing',
    'i.c.t.': 'Computing',
    'information technology': 'Computing',
    'integrated science': 'Science',
    'int. science': 'Science',
    'religious & moral education': 'Religious and Moral Education',
    'r.m.e': 'Religious and Moral Education',
    'r.m.e.': 'Religious and Moral Education',
    'creative arts': 'Creative Arts and Design',
    'creative art': 'Creative Arts and Design',
    'career tech': 'Career Technology',
    'career tech.': 'Career Technology',
    'physical education': 'Career Technology',  # sometimes grouped
    'maths': 'Mathematics',
    'math': 'Mathematics',
    'english': 'English Language',
    'social': 'Social Studies',
}


def _normalize_grade(raw: str) -> str:
    """Convert 'Basic 7', 'JHS 1', 'JHS 1A', etc. to GES code like 'B7'."""
    lower = raw.strip().lower()
    if lower in _GRADE_MAP:
        return _GRADE_MAP[lower]
    # Strip section letters: "JHS 1A" → "JHS 1", "Basic 7B" → "Basic 7"
    stripped = re.sub(r'[a-z]$', '', lower).strip()
    if stripped in _GRADE_MAP:
        return _GRADE_MAP[stripped]
    # Already a code like B7, B8
    m = re.match(r'^[A-Z]\d+$', raw.strip(), re.IGNORECASE)
    if m:
        return raw.strip().upper()
    return raw.strip()


# ── Browser view ──────────────────────────────────────────────

@login_required
def curriculum_browser(request):
    """Interactive GES/NaCCA curriculum browser page."""
    subjects = CurriculumSubject.objects.annotate(
        grade_count=Count('grades'),
    ).order_by('ordering', 'name')
    return render(request, 'curriculum/browser.html', {'subjects': subjects})


def curriculum_tree(request):
    """
    Return the full curriculum tree for a given subject + grade.
    Used by the browser's AJAX calls.
    """
    grade_id = request.GET.get('grade_id')
    if not grade_id:
        return JsonResponse({'strands': []})

    strands = Strand.objects.filter(grade_id=grade_id).prefetch_related(
        'sub_strands__content_standards__indicators__exemplars',
    ).order_by('ordering', 'name')

    tree = []
    for strand in strands:
        s_data = {'name': strand.name, 'sub_strands': []}
        for ss in strand.sub_strands.all().order_by('ordering', 'name'):
            ss_data = {'name': ss.name, 'content_standards': []}
            for cs in ss.content_standards.all().order_by('ordering', 'code'):
                cs_data = {
                    'code': cs.code,
                    'statement': cs.statement,
                    'indicators': [],
                }
                for ind in cs.indicators.all().order_by('ordering', 'code'):
                    ind_data = {
                        'code': ind.code,
                        'statement': ind.statement,
                        'term': ind.term,
                        'suggested_weeks': ind.suggested_weeks,
                        'exemplars': list(
                            ind.exemplars.values_list('text', flat=True)
                        ),
                    }
                    cs_data['indicators'].append(ind_data)
                ss_data['content_standards'].append(cs_data)
            s_data['sub_strands'].append(ss_data)
        tree.append(s_data)

    return JsonResponse({'strands': tree})
