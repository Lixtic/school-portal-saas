"""
Tool views for the standalone teacher portal.
Bridges the gap between the /u/ individual portal and the rich tenant-side
teacher tools (Question Bank, Exam Paper, Lesson Planner).
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from individual_users.models import (
    AddonSubscription,
    IndividualProfile,
    ToolExamPaper,
    ToolLessonPlan,
    ToolPresentation,
    ToolQuestion,
    ToolSlide,
)

logger = logging.getLogger(__name__)


# ── Rich Tools Catalog ───────────────────────────────────────────────────────
# Mirrors the tenant-side TeacherAddOn catalog with the addons that standalone
# teachers can actually USE (not just API access).

TOOLS_CATALOG = [
    {
        'slug': 'exam-generator',
        'name': 'Question Bank & Exam Paper',
        'icon': 'bi-file-earmark-text',
        'color': '#4361ee',
        'tagline': 'Build, organise and generate exam papers in minutes',
        'description': (
            'Create a bank of categorised questions by subject, topic and '
            'difficulty. Generate polished exam papers with headers, instructions '
            'and answer keys — ready to print or share as PDF.'
        ),
        'features': [
            'MCQ, fill-in, short answer, essay & true/false formats',
            'AI-powered bulk question generation',
            'Drag-and-drop exam paper builder',
            'WAEC / GES standard formatting',
            'PDF & DOCX export with answer key',
        ],
        'category': 'assessment',
        'tools': ['question_bank', 'exam_paper'],
    },
    {
        'slug': 'lesson-planner',
        'name': 'Smart Lesson Planner',
        'icon': 'bi-journal-bookmark',
        'color': '#059669',
        'tagline': 'AI-generated lesson plans aligned to GES curriculum',
        'description': (
            'Create structured lesson plans with objectives, materials, '
            'introduction, development, assessment and closure sections. '
            'Use AI to generate plans from a topic in seconds.'
        ),
        'features': [
            'GES-aligned curriculum-based plans',
            'AI generation from topic + class level',
            'Customisable plan sections',
            'Print-ready formatting',
            'Save and reuse templates',
        ],
        'category': 'productivity',
        'tools': ['lesson_plan'],
    },
    {
        'slug': 'slide-generator',
        'name': 'Slide Deck Creator',
        'icon': 'bi-easel2',
        'color': '#7c3aed',
        'tagline': 'AI-powered Gamma-style presentations for the classroom',
        'description': (
            'Create beautiful teaching presentations with AI-generated slides. '
            'Eight premium themes, multiple layouts and a Gamma-style editor '
            'with drag-and-drop reordering.'
        ),
        'features': [
            'AI-generated 8-slide teaching decks',
            '8 premium dark/light themes',
            'Gamma-style 3-pane visual editor',
            'Fullscreen presentation mode',
            'Share via public link',
            'Print / PDF handouts',
        ],
        'category': 'presentations',
        'tools': ['slide_deck'],
    },
    {
        'slug': 'grade-analytics',
        'name': 'Grade Analytics',
        'icon': 'bi-graph-up-arrow',
        'color': '#7c3aed',
        'tagline': 'Student performance insights and grade trends',
        'description': (
            'Upload or enter student grades, visualise performance trends, '
            'and generate class reports with distribution charts.'
        ),
        'features': [
            'Performance trend charts',
            'Class distribution analysis',
            'Student comparison reports',
            'Export to CSV / PDF',
        ],
        'category': 'analytics',
        'tools': [],
        'coming_soon': True,
    },
    {
        'slug': 'ai-tutor',
        'name': 'AI Teaching Assistant',
        'icon': 'bi-robot',
        'color': '#0891b2',
        'tagline': 'AI-powered help for content creation and tutoring',
        'description': (
            'Ask the AI assistant to explain concepts, generate study notes, '
            'create worksheets, or help with marking feedback.'
        ),
        'features': [
            'Concept explainer for any subject',
            'Worksheet & activity generator',
            'Marking feedback writer',
            'Study notes creator',
        ],
        'category': 'ai_tools',
        'tools': [],
        'coming_soon': True,
    },
    {
        'slug': 'report-card',
        'name': 'Report Card Writer',
        'icon': 'bi-file-earmark-bar-graph',
        'color': '#d97706',
        'tagline': 'AI-generated report card comments with conduct ratings',
        'description': (
            'Generate personalised report card comments for each student '
            'based on their performance, conduct and attitude ratings.'
        ),
        'features': [
            'AI-generated personalised comments',
            'Conduct & attitude ratings',
            'Bulk generation for whole class',
            'Editable before export',
        ],
        'category': 'assessment',
        'tools': [],
        'coming_soon': True,
    },
    {
        'slug': 'attendance-tracker',
        'name': 'Attendance Tracker',
        'icon': 'bi-calendar-check',
        'color': '#dc2626',
        'tagline': 'Track and analyse student attendance patterns',
        'description': (
            'Log daily attendance, track patterns, and generate absence '
            'reports for your class.'
        ),
        'features': [
            'Daily attendance logging',
            'Absence pattern detection',
            'Weekly & monthly reports',
            'SMS/email absence alerts',
        ],
        'category': 'management',
        'tools': [],
        'coming_soon': True,
    },
]


def _get_tool_by_slug(slug):
    """Lookup a tool entry from the catalog by slug."""
    return next((t for t in TOOLS_CATALOG if t['slug'] == slug), None)


# ── Access Control ───────────────────────────────────────────────────────────

def _ensure_public_schema():
    connection.set_schema_to_public()


def _tool_required(view_func):
    """Decorator: require login + individual user_type + teacher role."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('individual:signin')
        if request.user.user_type != 'individual':
            messages.error(request, 'Access restricted to individual accounts.')
            return redirect('home')
        _ensure_public_schema()
        try:
            profile = request.user.individual_profile
        except IndividualProfile.DoesNotExist:
            return redirect('individual:dashboard')
        if profile.role != 'teacher':
            messages.info(request, 'Tools are available for teacher accounts.')
            return redirect('individual:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def _has_tool_access(profile, tool_slug):
    """Check if the teacher has an active subscription for this tool."""
    return AddonSubscription.objects.filter(
        profile=profile, addon_slug=tool_slug, status='active',
    ).exists()


def _require_tool(tool_slug):
    """Decorator: require an active subscription for a specific tool."""
    from functools import wraps

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            profile = request.user.individual_profile
            if not _has_tool_access(profile, tool_slug):
                tool = _get_tool_by_slug(tool_slug)
                name = tool['name'] if tool else tool_slug
                messages.warning(
                    request,
                    f'You need the "{name}" addon to use this tool. '
                    f'Subscribe from the Addon Store.',
                )
                return redirect('individual:tools_hub')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── Tools Hub (main tools page) ──────────────────────────────────────────────

@_tool_required
def tools_hub(request):
    """Main tools page showing all available teacher tools."""
    profile = request.user.individual_profile
    my_slugs = set(
        AddonSubscription.objects.filter(profile=profile, status='active')
        .values_list('addon_slug', flat=True)
    )

    tools = []
    for tool in TOOLS_CATALOG:
        tools.append({
            **tool,
            'subscribed': tool['slug'] in my_slugs,
            'coming_soon': tool.get('coming_soon', False),
        })

    # Count user's data
    q_count = ToolQuestion.objects.filter(profile=profile).count()
    e_count = ToolExamPaper.objects.filter(profile=profile).count()
    l_count = ToolLessonPlan.objects.filter(profile=profile).count()
    d_count = ToolPresentation.objects.filter(profile=profile).count()

    ctx = {
        'tools': tools,
        'profile': profile,
        'role': 'teacher',
        'question_count': q_count,
        'exam_count': e_count,
        'lesson_count': l_count,
        'deck_count': d_count,
    }
    return render(request, 'individual/tools/hub.html', ctx)


# ── Question Bank ────────────────────────────────────────────────────────────

@_tool_required
@_require_tool('exam-generator')
def question_bank_list(request):
    """List all questions in the teacher's bank with filtering."""
    profile = request.user.individual_profile
    qs = ToolQuestion.objects.filter(profile=profile)

    # Filters
    subject = request.GET.get('subject', '')
    fmt = request.GET.get('format', '')
    difficulty = request.GET.get('difficulty', '')
    search = request.GET.get('q', '')

    if subject:
        qs = qs.filter(subject=subject)
    if fmt:
        qs = qs.filter(question_format=fmt)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)
    if search:
        qs = qs.filter(
            Q(question_text__icontains=search) |
            Q(topic__icontains=search)
        )

    # Stats
    stats = ToolQuestion.objects.filter(profile=profile).aggregate(
        total=Count('id'),
        mcq=Count('id', filter=Q(question_format='mcq')),
        essay=Count('id', filter=Q(question_format='essay')),
    )

    ctx = {
        'questions': qs[:100],
        'stats': stats,
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
        'formats': ToolQuestion.FORMAT_CHOICES,
        'difficulties': ToolQuestion.DIFFICULTY_CHOICES,
        'filter_subject': subject,
        'filter_format': fmt,
        'filter_difficulty': difficulty,
        'search_query': search,
    }
    return render(request, 'individual/tools/question_bank.html', ctx)


@_tool_required
@_require_tool('exam-generator')
def question_create(request):
    """Create a new question."""
    profile = request.user.individual_profile

    if request.method == 'POST':
        q = ToolQuestion(
            profile=profile,
            subject=request.POST.get('subject', 'mathematics'),
            target_class=request.POST.get('target_class', ''),
            topic=request.POST.get('topic', ''),
            question_text=request.POST.get('question_text', '').strip(),
            question_format=request.POST.get('question_format', 'mcq'),
            difficulty=request.POST.get('difficulty', 'medium'),
            correct_answer=request.POST.get('correct_answer', '').strip(),
            explanation=request.POST.get('explanation', '').strip(),
        )

        # Parse options for MCQ
        if q.question_format == 'mcq':
            opts = []
            for i in range(1, 7):  # Up to 6 options
                opt = request.POST.get(f'option_{i}', '').strip()
                if opt:
                    opts.append(opt)
            q.options = opts

        if not q.question_text:
            messages.error(request, 'Question text is required.')
        else:
            q.save()
            messages.success(request, 'Question added to your bank.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'id': q.id})
            return redirect('individual:question_bank')

    ctx = {
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
        'formats': ToolQuestion.FORMAT_CHOICES,
        'difficulties': ToolQuestion.DIFFICULTY_CHOICES,
    }
    return render(request, 'individual/tools/question_create.html', ctx)


@_tool_required
@_require_tool('exam-generator')
def question_edit(request, pk):
    """Edit an existing question."""
    profile = request.user.individual_profile
    q = get_object_or_404(ToolQuestion, pk=pk, profile=profile)

    if request.method == 'POST':
        q.subject = request.POST.get('subject', q.subject)
        q.target_class = request.POST.get('target_class', q.target_class)
        q.topic = request.POST.get('topic', q.topic)
        q.question_text = request.POST.get('question_text', q.question_text).strip()
        q.question_format = request.POST.get('question_format', q.question_format)
        q.difficulty = request.POST.get('difficulty', q.difficulty)
        q.correct_answer = request.POST.get('correct_answer', q.correct_answer).strip()
        q.explanation = request.POST.get('explanation', q.explanation).strip()

        if q.question_format == 'mcq':
            opts = []
            for i in range(1, 7):
                opt = request.POST.get(f'option_{i}', '').strip()
                if opt:
                    opts.append(opt)
            q.options = opts

        if not q.question_text:
            messages.error(request, 'Question text is required.')
        else:
            q.save()
            messages.success(request, 'Question updated.')
            return redirect('individual:question_bank')

    ctx = {
        'question': q,
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
        'formats': ToolQuestion.FORMAT_CHOICES,
        'difficulties': ToolQuestion.DIFFICULTY_CHOICES,
    }
    return render(request, 'individual/tools/question_edit.html', ctx)


@_tool_required
@_require_tool('exam-generator')
@require_POST
def question_delete(request, pk):
    """Delete a question."""
    profile = request.user.individual_profile
    q = get_object_or_404(ToolQuestion, pk=pk, profile=profile)
    q.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    messages.success(request, 'Question deleted.')
    return redirect('individual:question_bank')


@_tool_required
@_require_tool('exam-generator')
@require_POST
def question_ai_generate(request):
    """AI-generate questions from a topic/subject/difficulty."""
    profile = request.user.individual_profile
    subject = request.POST.get('subject', 'mathematics')
    topic = request.POST.get('topic', '')
    target_class = request.POST.get('target_class', '')
    question_format = request.POST.get('question_format', 'mcq')
    difficulty = request.POST.get('difficulty', 'medium')
    count = min(int(request.POST.get('count', 5)), 20)  # Max 20

    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)

    # Build AI prompt
    format_label = dict(ToolQuestion.FORMAT_CHOICES).get(question_format, question_format)
    subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(subject, subject)

    prompt = (
        f"Generate {count} {difficulty} {format_label} questions on "
        f"'{topic}' for {subject_label}"
    )
    if target_class:
        prompt += f" ({target_class} level)"
    prompt += (
        ". Return ONLY a JSON array of objects with keys: "
        "question_text, options (array, empty for non-MCQ), correct_answer, explanation. "
        "No markdown, no extra text."
    )

    try:
        import openai
        client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': 'You are a Ghanaian school teacher creating exam questions.'},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.7,
            max_tokens=3000,
        )
        raw_text = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw_text.startswith('```'):
            raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        items = json.loads(raw_text)
    except Exception as exc:
        logger.warning('AI question generation failed: %s', exc)
        return JsonResponse({'error': 'AI generation failed. Please try again.'}, status=500)

    # Save generated questions
    created = []
    for item in items[:count]:
        q = ToolQuestion.objects.create(
            profile=profile,
            subject=subject,
            target_class=target_class,
            topic=topic,
            question_text=item.get('question_text', ''),
            question_format=question_format,
            difficulty=difficulty,
            options=item.get('options', []),
            correct_answer=item.get('correct_answer', ''),
            explanation=item.get('explanation', ''),
        )
        created.append({
            'id': q.id,
            'question_text': q.question_text[:120],
            'correct_answer': q.correct_answer,
        })

    return JsonResponse({'ok': True, 'count': len(created), 'questions': created})


# Import settings for AI key
from django.conf import settings


# ── Exam Paper ───────────────────────────────────────────────────────────────

@_tool_required
@_require_tool('exam-generator')
def exam_paper_list(request):
    """List all exam papers."""
    profile = request.user.individual_profile
    papers = ToolExamPaper.objects.filter(profile=profile).annotate(
        q_count=Count('questions'),
    )

    ctx = {
        'papers': papers,
        'profile': profile,
        'role': 'teacher',
    }
    return render(request, 'individual/tools/exam_papers.html', ctx)


@_tool_required
@_require_tool('exam-generator')
def exam_paper_create(request):
    """Create a new exam paper from question bank."""
    profile = request.user.individual_profile

    if request.method == 'POST':
        paper = ToolExamPaper.objects.create(
            profile=profile,
            title=request.POST.get('title', 'Untitled Exam').strip(),
            subject=request.POST.get('subject', 'mathematics'),
            target_class=request.POST.get('target_class', ''),
            duration_minutes=int(request.POST.get('duration_minutes', 60)),
            instructions=request.POST.get('instructions', 'Answer ALL questions.').strip(),
            school_name=request.POST.get('school_name', '').strip(),
            term=request.POST.get('term', '').strip(),
            academic_year=request.POST.get('academic_year', '').strip(),
        )
        # Add selected questions
        q_ids = request.POST.getlist('question_ids')
        if q_ids:
            questions = ToolQuestion.objects.filter(
                pk__in=q_ids, profile=profile,
            )
            paper.questions.set(questions)

        messages.success(request, f'Exam paper "{paper.title}" created.')
        return redirect('individual:exam_paper_detail', pk=paper.pk)

    # Get questions for selection
    questions = ToolQuestion.objects.filter(profile=profile)
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        questions = questions.filter(subject=subject_filter)

    ctx = {
        'questions': questions,
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/exam_paper_create.html', ctx)


@_tool_required
@_require_tool('exam-generator')
def exam_paper_detail(request, pk):
    """View / preview an exam paper."""
    profile = request.user.individual_profile
    paper = get_object_or_404(ToolExamPaper, pk=pk, profile=profile)
    questions = paper.questions.all().order_by('question_format', 'difficulty')

    # Group by format for nice rendering
    sections = {}
    for q in questions:
        label = dict(ToolQuestion.FORMAT_CHOICES).get(q.question_format, q.question_format)
        sections.setdefault(label, []).append(q)

    ctx = {
        'paper': paper,
        'sections': sections,
        'question_count': questions.count(),
        'profile': profile,
        'role': 'teacher',
    }
    return render(request, 'individual/tools/exam_paper_detail.html', ctx)


@_tool_required
@_require_tool('exam-generator')
@require_POST
def exam_paper_delete(request, pk):
    """Delete an exam paper."""
    profile = request.user.individual_profile
    paper = get_object_or_404(ToolExamPaper, pk=pk, profile=profile)
    paper.delete()
    messages.success(request, 'Exam paper deleted.')
    return redirect('individual:exam_papers')


# ── Lesson Planner ───────────────────────────────────────────────────────────

@_tool_required
@_require_tool('lesson-planner')
def lesson_plan_list(request):
    """List all lesson plans."""
    profile = request.user.individual_profile
    plans = ToolLessonPlan.objects.filter(profile=profile)

    ctx = {
        'plans': plans,
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/lesson_plans.html', ctx)


@_tool_required
@_require_tool('lesson-planner')
def lesson_plan_create(request):
    """Create or AI-generate a lesson plan."""
    profile = request.user.individual_profile

    if request.method == 'POST':
        b7_meta_raw = request.POST.get('b7_meta', '').strip()
        b7_meta = json.loads(b7_meta_raw) if b7_meta_raw else None
        plan = ToolLessonPlan.objects.create(
            profile=profile,
            title=request.POST.get('title', 'Untitled Lesson').strip(),
            subject=request.POST.get('subject', 'mathematics'),
            target_class=request.POST.get('target_class', ''),
            topic=request.POST.get('topic', '').strip(),
            indicator=request.POST.get('indicator', '').strip(),
            sub_strand=request.POST.get('sub_strand', '').strip(),
            duration_minutes=int(request.POST.get('duration_minutes', 40)),
            objectives=request.POST.get('objectives', '').strip(),
            materials=request.POST.get('materials', '').strip(),
            introduction=request.POST.get('introduction', '').strip(),
            development=request.POST.get('development', '').strip(),
            assessment=request.POST.get('assessment', '').strip(),
            closure=request.POST.get('closure', '').strip(),
            notes=request.POST.get('notes', '').strip(),
            b7_meta=b7_meta,
        )
        messages.success(request, f'Lesson plan "{plan.title}" created.')
        return redirect('individual:lesson_plan_detail', pk=plan.pk)

    ctx = {
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/lesson_plan_create.html', ctx)


@_tool_required
@_require_tool('lesson-planner')
def lesson_plan_detail(request, pk):
    """View a lesson plan."""
    profile = request.user.individual_profile
    plan = get_object_or_404(ToolLessonPlan, pk=pk, profile=profile)

    ctx = {
        'plan': plan,
        'profile': profile,
        'role': 'teacher',
    }
    return render(request, 'individual/tools/lesson_plan_detail.html', ctx)


@_tool_required
@_require_tool('lesson-planner')
def lesson_plan_edit(request, pk):
    """Edit a lesson plan."""
    profile = request.user.individual_profile
    plan = get_object_or_404(ToolLessonPlan, pk=pk, profile=profile)

    if request.method == 'POST':
        plan.title = request.POST.get('title', plan.title).strip()
        plan.subject = request.POST.get('subject', plan.subject)
        plan.target_class = request.POST.get('target_class', plan.target_class)
        plan.topic = request.POST.get('topic', plan.topic).strip()
        plan.indicator = request.POST.get('indicator', plan.indicator).strip()
        plan.sub_strand = request.POST.get('sub_strand', plan.sub_strand).strip()
        plan.duration_minutes = int(request.POST.get('duration_minutes', plan.duration_minutes))
        plan.objectives = request.POST.get('objectives', plan.objectives).strip()
        plan.materials = request.POST.get('materials', plan.materials).strip()
        plan.introduction = request.POST.get('introduction', plan.introduction).strip()
        plan.development = request.POST.get('development', plan.development).strip()
        plan.assessment = request.POST.get('assessment', plan.assessment).strip()
        plan.closure = request.POST.get('closure', plan.closure).strip()
        plan.notes = request.POST.get('notes', plan.notes).strip()
        b7_meta_raw = request.POST.get('b7_meta', '').strip()
        if b7_meta_raw:
            plan.b7_meta = json.loads(b7_meta_raw)
        plan.save()
        messages.success(request, 'Lesson plan updated.')
        return redirect('individual:lesson_plan_detail', pk=plan.pk)

    ctx = {
        'plan': plan,
        'profile': profile,
        'role': 'teacher',
        'subjects': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/lesson_plan_edit.html', ctx)


@_tool_required
@_require_tool('lesson-planner')
@require_POST
def lesson_plan_delete(request, pk):
    """Delete a lesson plan."""
    profile = request.user.individual_profile
    plan = get_object_or_404(ToolLessonPlan, pk=pk, profile=profile)
    plan.delete()
    messages.success(request, 'Lesson plan deleted.')
    return redirect('individual:lesson_plans')


@_tool_required
@_require_tool('lesson-planner')
@require_POST
def lesson_plan_ai_generate(request):
    """AI-generate a lesson plan from topic + subject.

    Supports two modes:
    - Full plan: returns all sections (default)
    - Inline mode (inline=1): returns plan dict without saving to DB
    - Section mode (section=xxx): returns only the requested section
    """
    profile = request.user.individual_profile
    subject = request.POST.get('subject', 'mathematics')
    topic = request.POST.get('topic', '')
    target_class = request.POST.get('target_class', '')
    duration = int(request.POST.get('duration_minutes', 40))
    inline = request.POST.get('inline') == '1'
    section = request.POST.get('section', '').strip()

    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)

    subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(subject, subject)

    # ── Build prompt ──────────────────────────────────────────
    if section:
        section_map = {
            'objectives': 'learning objectives (numbered, measurable, GES-aligned)',
            'materials': 'teaching and learning materials/resources needed',
            'introduction': 'Phase 1: Starter activity (5-7 min) to activate prior knowledge and engage learners',
            'development': 'Phase 2: Main teaching activity (20-25 min) with demonstrations, group work, and formative assessment checkpoints',
            'assessment': 'Phase 3: Reflection activity (5-10 min) with summary questions, exit tickets, and learner self-assessment',
            'closure': 'closure/homework assignment connecting to next lesson',
        }
        section_desc = section_map.get(section, section)
        prompt = (
            f"For a lesson on '{topic}' in {subject_label}"
        )
        if target_class:
            prompt += f" for {target_class} students"
        prompt += (
            f" ({duration} min duration), write ONLY the {section_desc}. "
            "Return ONLY a JSON object with a single key '{}' containing the text. "
            "Use clear numbered or bulleted points. No markdown fences."
        ).format(section)
    else:
        prompt = (
            f"Create a detailed GES-aligned lesson plan for teaching '{topic}' in {subject_label}"
        )
        if target_class:
            prompt += f" to {target_class} students"
        prompt += (
            f". Duration: {duration} minutes. "
            "Structure the plan using Ghana Education Service 3-phase pedagogy:\n"
            "- Phase 1 (Starter/Introduction): 5-7 min activity to activate prior knowledge\n"
            "- Phase 2 (Main/Development): 20-25 min with teaching activities, demonstrations, "
            "group work, and formative assessment checkpoints\n"
            "- Phase 3 (Reflection/Assessment): 5-10 min with summary questions, exit tickets, "
            "and learner self-assessment\n\n"
            "Return ONLY a JSON object with keys: title, objectives, materials, "
            "introduction, development, assessment, closure. "
            "Each value is a string with clear numbered or bulleted points. "
            "No markdown fences, no extra text."
        )

    try:
        import openai
        client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': (
                    'You are Aura-T, an expert Ghanaian GES curriculum specialist. '
                    'You create lesson plans following the 3-phase pedagogy: '
                    'Phase 1 (Starter), Phase 2 (Main/New Learning), Phase 3 (Reflection). '
                    'Always include practical activities, formative assessment checkpoints, '
                    'and differentiation tips.'
                )},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        raw_text = resp.choices[0].message.content.strip()
        if raw_text.startswith('```'):
            raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)
    except Exception as exc:
        logger.warning('AI lesson plan generation failed: %s', exc)
        return JsonResponse({'error': 'AI generation failed. Please try again.'}, status=500)

    # ── Inline mode: return without saving ────────────────────
    if inline:
        return JsonResponse({'ok': True, 'plan': data})

    # ── Default: save to DB ───────────────────────────────────
    plan = ToolLessonPlan.objects.create(
        profile=profile,
        title=data.get('title', f'{subject_label}: {topic}'),
        subject=subject,
        target_class=target_class,
        topic=topic,
        duration_minutes=duration,
        objectives=data.get('objectives', ''),
        materials=data.get('materials', ''),
        introduction=data.get('introduction', ''),
        development=data.get('development', ''),
        assessment=data.get('assessment', ''),
        closure=data.get('closure', ''),
    )

    return JsonResponse({
        'ok': True,
        'id': plan.id,
        'title': plan.title,
        'redirect': f'/u/tools/lesson-plans/{plan.pk}/',
    })


# ── GES B5 Weekly Notes Draft ────────────────────────────────────────────────

import re as _re

_GES_CODE_RE = _re.compile(r'^[A-Z]{1,3}\d{1,2}(?:\.\d+){2,5}\s*$')


@_tool_required
@_require_tool('lesson-planner')
@require_POST
def lesson_plan_ges_generate(request):
    """Generate a GES Weekly Lesson Notes draft (B5-style table format).

    Supports:
    - Full plan: all sections
    - Inline mode (inline=1): return JSON without saving
    - Section mode (section=xxx): regenerate one section
    """
    profile = request.user.individual_profile
    subject = request.POST.get('subject', 'mathematics')
    topic = request.POST.get('topic', '').strip()
    indicator = request.POST.get('indicator', '').strip()
    sub_strand = request.POST.get('sub_strand', '').strip()
    target_class = request.POST.get('target_class', 'Basic 5')
    duration = int(request.POST.get('duration_minutes', 60))
    week_number = int(request.POST.get('week_number', 1) or 1)
    inline = request.POST.get('inline') == '1'
    section = request.POST.get('section', '').strip()

    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)
    if not indicator:
        return JsonResponse({'error': 'Indicator is required for GES draft'}, status=400)

    subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(subject, subject)
    code_only = bool(_GES_CODE_RE.match(indicator))

    indicator_instruction = (
        f"Target Indicator Code: {indicator}\n"
        "IMPORTANT: This is a Ghana GES curriculum code. "
        "Resolve it to the full performance indicator statement. "
        "Use ONLY the descriptive statement (not the numeric code) throughout."
    ) if code_only else f"Target Indicator (must be achieved): {indicator}"

    sub_strand_line = f'\n- Sub-strand: {sub_strand}' if sub_strand else ''

    # ── Section-level regeneration ─────────────────────────────
    if section:
        valid_sections = {
            'objectives', 'materials', 'introduction', 'development',
            'assessment', 'closure', 'notes',
        }
        if section not in valid_sections:
            return JsonResponse({'error': f'Invalid section: {section}'}, status=400)

        # Map standalone field names to GES section hints
        section_hints = {
            'objectives': 'Write concise content standard and indicator-focused lesson objectives.',
            'materials': 'List practical teaching and learning materials needed.',
            'introduction': 'Write Phase 1 starter activities linked to the indicator.',
            'development': 'Write Phase 2 main learning activities that teach the indicator.',
            'assessment': 'Write Phase 3 assessment checks that measure the indicator.',
            'closure': 'Write homework that directly reinforces the indicator.',
            'notes': 'Write teacher reflection prompts tied to indicator mastery.',
        }

        sys_prompt = f"""You are a Ghana GES lesson planner.
Regenerate ONLY one section of a weekly lesson notes plan.
Context:
- Subject: {subject_label}
- Class: {target_class}
- Strand/Topic: {topic}{sub_strand_line}
- {indicator_instruction}
- Week Number: {week_number}
- Section to regenerate: {section}
Return ONLY valid JSON: {{"content": "new section text"}}"""

        current_text = request.POST.get('current_text', '').strip()
        user_prompt = (
            f"Regenerate section '{section}'. {section_hints.get(section, '')} "
            f"Indicator: {indicator}. "
            + (f"Current draft to improve: {current_text[:900]}" if current_text else '')
        )

        try:
            import openai
            client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': sys_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.5,
                max_tokens=700,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            data = json.loads(raw.strip())
            content = data.get('content', '')
        except Exception as exc:
            logger.warning('GES section regen failed (%s): %s', section, exc)
            content = ''

        return JsonResponse({'ok': True, 'plan': {section: content}})

    # ── Full GES draft ────────────────────────────────────────
    sys_prompt = f"""You are a Ghana GES lesson planner.
Generate a weekly lesson notes draft for:
- Subject: {subject_label}
- Class: {target_class}
- Strand/Topic: {topic}{sub_strand_line}
- {indicator_instruction}
- Week Number: {week_number}
- Duration: {duration} minutes

The output must match a traditional GES weekly lesson-notes table style.
Every activity, assessment, and homework must directly align to the target indicator.
Never reference indicator codes in lesson text — use full descriptive sentences.

Return ONLY valid JSON with this schema:
{{
  "lesson_plan": {{
    "title": "lesson title",
    "objectives": "content standard + indicator in plain text",
    "teaching_materials": "resources list",
    "introduction": "Phase 1 starter activities (5-7 min)",
    "presentation": "Phase 2 new learning activities (20-25 min)",
    "evaluation": "Phase 3 assessment/check for understanding (5-10 min)",
    "homework": "homework task",
    "remarks": "teacher reflection note"
  }},
  "b7_meta": {{
    "period": "e.g. 1",
    "duration": "{duration} Minutes",
    "strand": "main strand",
    "sub_strand": "sub strand/topic",
    "content_standard": "single concise statement",
    "indicator": "single concise indicator statement",
    "lesson_of": "e.g. 1 of 3",
    "performance_indicator": "what learners can do",
    "core_competencies": "comma-separated competencies",
    "references": "curriculum references",
    "keywords": "comma-separated keywords"
  }}
}}"""

    if code_only:
        user_prompt = (
            f"Create a complete weekly lesson notes draft for Week {week_number}. "
            f"The GES curriculum code is {indicator}. "
            "Resolve this code to its full Ghana curriculum performance indicator, "
            "then design the entire lesson to achieve that statement."
        )
    else:
        user_prompt = (
            f"Create a complete weekly lesson notes draft for Week {week_number}. "
            f"The lesson must achieve this indicator exactly: {indicator}. "
            'Use clear teacher actions, learner actions, and assessment steps.'
        )

    try:
        import openai
        client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': sys_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.5,
            max_tokens=2000,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
        if raw.endswith('```'):
            raw = raw[:-3]
        parsed = json.loads(raw.strip())
    except Exception as exc:
        logger.warning('GES lesson generation failed: %s', exc)
        return JsonResponse({'error': 'GES draft generation failed. Please try again.'}, status=500)

    lp = parsed.get('lesson_plan', {})
    b7_meta = parsed.get('b7_meta', {})

    # Map GES field names → standalone model field names
    plan_data = {
        'title': lp.get('title', f'{subject_label}: {topic}'),
        'objectives': lp.get('objectives', ''),
        'materials': lp.get('teaching_materials', ''),
        'introduction': lp.get('introduction', ''),
        'development': lp.get('presentation', ''),
        'assessment': lp.get('evaluation', ''),
        'closure': lp.get('homework', ''),
        'notes': lp.get('remarks', ''),
    }

    # Inline mode: return without saving
    if inline:
        return JsonResponse({'ok': True, 'plan': plan_data, 'b7_meta': b7_meta})

    # Save to DB
    plan = ToolLessonPlan.objects.create(
        profile=profile,
        title=plan_data['title'],
        subject=subject,
        target_class=target_class,
        topic=topic,
        indicator=indicator,
        sub_strand=sub_strand,
        duration_minutes=duration,
        objectives=plan_data['objectives'],
        materials=plan_data['materials'],
        introduction=plan_data['introduction'],
        development=plan_data['development'],
        assessment=plan_data['assessment'],
        closure=plan_data['closure'],
        notes=plan_data['notes'],
        b7_meta=b7_meta,
    )

    return JsonResponse({
        'ok': True,
        'id': plan.id,
        'title': plan.title,
        'redirect': f'/u/tools/lesson-plans/{plan.pk}/',
    })


# ── Slide Deck / Presentations ───────────────────────────────────────────────

def _detect_slide_layout(title, index, total):
    """Pick layout based on slide title keywords and position."""
    if index == 0:
        return 'title'
    if index == total - 1:
        return 'summary'
    t = title.lower()
    if any(w in t for w in ('vocabulary', 'definition', 'key term', 'key vocab')):
        return 'two_col'
    if any(w in t for w in ('comparison', 'compare', 'vs', 'versus', 'did you know')):
        return 'two_col'
    if any(w in t for w in ('quote', 'saying', 'proverb')):
        return 'quote'
    if any(w in t for w in ('stat', 'figure', 'number', 'big stat')):
        return 'big_stat'
    return 'bullets'


@_tool_required
@_require_tool('slide-generator')
def deck_list(request):
    """List all presentations for this teacher."""
    from django.db.models import Subquery, OuterRef

    profile = request.user.individual_profile
    decks = (
        ToolPresentation.objects.filter(profile=profile)
        .annotate(
            annotated_slide_count=Count('slides'),
            cover_emoji=Subquery(
                ToolSlide.objects.filter(
                    presentation=OuterRef('pk'), order=0,
                ).values('emoji')[:1]
            ),
        )
    )
    total_slides = ToolSlide.objects.filter(presentation__profile=profile).count()

    ctx = {
        'decks': decks,
        'total_decks': decks.count(),
        'total_slides': total_slides,
        'SUBJECT_CHOICES': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/presentations/list.html', ctx)


@_tool_required
@_require_tool('slide-generator')
def deck_create(request):
    """Create a new presentation."""
    profile = request.user.individual_profile

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Title is required.')
            return redirect('individual:deck_create')

        subject = request.POST.get('subject', '')
        target_class = request.POST.get('target_class', '')
        theme = request.POST.get('theme', 'aurora')

        if theme not in dict(ToolPresentation.THEME_CHOICES):
            theme = 'aurora'

        deck = ToolPresentation.objects.create(
            profile=profile,
            title=title,
            subject=subject,
            target_class=target_class,
            theme=theme,
        )

        # Smart seed: create starter slides from latest lesson plan
        if request.POST.get('smart_seed'):
            last_plan = (
                ToolLessonPlan.objects.filter(profile=profile)
                .order_by('-created_at')
                .first()
            )
            if last_plan:
                ToolSlide.objects.create(
                    presentation=deck, order=0, layout='title',
                    title=last_plan.title,
                    content=f'{last_plan.topic}\n{last_plan.target_class}',
                    emoji='\U0001F3AF',
                )
                ToolSlide.objects.create(
                    presentation=deck, order=1, layout='bullets',
                    title='Learning Objectives',
                    content=last_plan.objectives or '',
                    emoji='\U0001F4CB',
                )
                ToolSlide.objects.create(
                    presentation=deck, order=2, layout='bullets',
                    title='Lesson Flow',
                    content=last_plan.development or '',
                    emoji='\U0001F4D6',
                )
            else:
                ToolSlide.objects.create(
                    presentation=deck, order=0, layout='title',
                    title=title, content='', emoji='\u2728',
                )
        else:
            ToolSlide.objects.create(
                presentation=deck, order=0, layout='title',
                title=title, content='', emoji='\u2728',
            )

        return redirect('individual:deck_editor', pk=deck.pk)

    # GET
    ctx = {
        'THEME_CHOICES': ToolPresentation.THEME_CHOICES,
        'SUBJECT_CHOICES': ToolQuestion.SUBJECT_CHOICES,
        'prefill_title': request.GET.get('title', ''),
        'prefill_subject': request.GET.get('subject', ''),
        'prefill_theme': request.GET.get('theme', 'aurora'),
    }
    return render(request, 'individual/tools/presentations/create.html', ctx)


@_tool_required
@_require_tool('slide-generator')
def deck_editor(request, pk):
    """Gamma-style slide editor."""
    profile = request.user.individual_profile
    deck = get_object_or_404(ToolPresentation, pk=pk, profile=profile)
    slides = list(deck.slides.order_by('order'))

    slides_json = json.dumps([
        {
            'id': s.pk,
            'order': s.order,
            'layout': s.layout,
            'title': s.title,
            'content': s.content,
            'speaker_notes': s.speaker_notes,
            'emoji': s.emoji,
            'image_url': s.image_url,
        }
        for s in slides
    ])

    share_url = request.build_absolute_uri(
        f'/u/tools/presentations/share/{deck.share_token}/',
    )

    EMOJI_LIST = [
        '\U0001F3AF', '\U0001F4D6', '\U0001F52C', '\U0001F9EE', '\u2753',
        '\u2705', '\U0001F4A1', '\U0001F4CB', '\U0001F30D', '\u26A1',
        '\U0001F3A8', '\U0001F4CA', '\U0001F9EA', '\U0001F4DD', '\U0001F393',
        '\U0001F3C6', '\U0001F4BB', '\U0001F511', '\U0001F31F', '\U0001F4CC',
    ]

    ctx = {
        'deck': deck,
        'slides': slides,
        'slides_json': slides_json,
        'share_url': share_url,
        'THEME_CHOICES': ToolPresentation.THEME_CHOICES,
        'TRANSITION_CHOICES': ToolPresentation.TRANSITION_CHOICES,
        'LAYOUT_CHOICES': ToolSlide.LAYOUT_CHOICES,
        'EMOJI_LIST': EMOJI_LIST,
    }
    return render(request, 'individual/tools/presentations/editor.html', ctx)


@_tool_required
@_require_tool('slide-generator')
@require_POST
def deck_api(request):
    """AJAX API for the slide editor: save, add, delete, reorder, ai_generate."""
    from django.db import transaction
    from django.db.models import Max

    profile = request.user.individual_profile

    try:
        data = json.loads(request.body)
        action = data.get('action')
        deck_id = data.get('deck_id')
        deck = get_object_or_404(ToolPresentation, pk=deck_id, profile=profile)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    # ── save_slide ──────────────────────────────────────────
    if action == 'save_slide':
        slide_id = data.get('slide_id')
        slide = get_object_or_404(ToolSlide, pk=slide_id, presentation=deck)
        slide.title = data.get('title', slide.title)
        slide.content = data.get('content', slide.content)
        slide.speaker_notes = data.get('speaker_notes', slide.speaker_notes)
        slide.layout = data.get('layout', slide.layout)
        slide.emoji = data.get('emoji', slide.emoji)
        slide.image_url = data.get('image_url', slide.image_url)
        slide.save()
        deck.save()  # bump updated_at
        return JsonResponse({'ok': True})

    # ── add_slide ───────────────────────────────────────────
    elif action == 'add_slide':
        max_order = deck.slides.aggregate(m=Max('order'))['m'] or -1
        slide = ToolSlide.objects.create(
            presentation=deck,
            order=max_order + 1,
            layout=data.get('layout', 'bullets'),
            title=data.get('title', 'New Slide'),
            content=data.get('content', ''),
            emoji=data.get('emoji', ''),
        )
        deck.save()
        return JsonResponse({
            'ok': True,
            'slide_id': slide.pk,
            'order': slide.order,
            'layout': slide.layout,
            'title': slide.title,
            'content': slide.content,
            'emoji': slide.emoji,
            'speaker_notes': slide.speaker_notes,
            'image_url': slide.image_url,
        })

    # ── delete_slide ────────────────────────────────────────
    elif action == 'delete_slide':
        slide_id = data.get('slide_id')
        slide = get_object_or_404(ToolSlide, pk=slide_id, presentation=deck)
        slide.delete()
        with transaction.atomic():
            for i, s in enumerate(deck.slides.order_by('order')):
                s.order = i
                s.save(update_fields=['order'])
        deck.save()
        return JsonResponse({'ok': True})

    # ── reorder ─────────────────────────────────────────────
    elif action == 'reorder':
        order_list = data.get('order', [])
        with transaction.atomic():
            for i, sid in enumerate(order_list):
                ToolSlide.objects.filter(pk=sid, presentation=deck).update(order=i)
        deck.save()
        return JsonResponse({'ok': True})

    # ── update_deck ─────────────────────────────────────────
    elif action == 'update_deck':
        if 'title' in data:
            deck.title = data['title'] or deck.title
        if 'theme' in data and data['theme'] in dict(ToolPresentation.THEME_CHOICES):
            deck.theme = data['theme']
        if 'transition' in data and data['transition'] in dict(ToolPresentation.TRANSITION_CHOICES):
            deck.transition = data['transition']
        deck.save()
        return JsonResponse({
            'ok': True,
            'title': deck.title,
            'theme': deck.theme,
            'transition': deck.transition,
        })

    # ── ai_generate ─────────────────────────────────────────
    elif action == 'ai_generate':
        topic = data.get('topic', '').strip()
        if not topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)

        subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(
            deck.subject, deck.subject or 'General Studies',
        )
        class_name = deck.target_class or 'General'

        system_prompt = (
            "You are an expert teaching assistant who creates rich, "
            "presentation-ready slide decks.\n\n"
            f"Generate a complete teaching slide deck for {class_name} "
            f"{subject_label} on the topic: \"{topic}\".\n\n"
            "Return a JSON object with EXACTLY this structure:\n"
            "{\n"
            "  \"slides\": [\n"
            "    {\"title\": \"...\", \"bullets\": [\"...\"], "
            "\"notes\": \"...\", \"emoji\": \"...\"}\n"
            "  ],\n"
            "  \"activities\": [\"...\", \"...\"]\n"
            "}\n\n"
            "Each slide MUST include an \"emoji\" field.\n\n"
            "SLIDE STRUCTURE \u2014 8 SLIDES (MANDATORY):\n"
            "1. TITLE & HOOK: engaging title, objective, question\n"
            "2. KEY VOCABULARY: 3-4 terms with definitions\n"
            "3. CORE CONCEPT: 3-4 digestible points\n"
            "4. WORKED EXAMPLE: step-by-step (3-4 steps)\n"
            "5. REAL-WORLD APPLICATION: scenario\n"
            "6. COMPARISON / DID YOU KNOW: facts\n"
            "7. PRACTICE QUESTIONS: 3-4 of increasing difficulty\n"
            "8. SUMMARY & TAKEAWAYS: 3-4 concise statements\n\n"
            "RULES:\n"
            "- Write FULL, MEANINGFUL content \u2014 not outlines\n"
            "- Bullets must be complete thoughts\n"
            "- Every slide must have 3-4 bullets\n"
            "- Speaker notes are for the TEACHER"
        )
        user_prompt = (
            f"Create a complete presentation on '{topic}' for "
            f"{class_name} {subject_label}. "
            "Fill every slide with real content ready to present."
        )

        try:
            import openai
            from django.conf import settings as django_settings
            client = openai.OpenAI(
                api_key=getattr(django_settings, 'OPENAI_API_KEY', ''),
            )
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.7,
                max_tokens=3000,
            )
            raw_text = resp.choices[0].message.content.strip()
            if raw_text.startswith('```'):
                raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            result = json.loads(raw_text.strip())
        except Exception as exc:
            logger.warning('AI slide generation failed: %s', exc)
            return JsonResponse(
                {'error': 'AI generation failed. Please try again.'},
                status=500,
            )

        raw_slides = result.get('slides', [])

        with transaction.atomic():
            deck.slides.all().delete()
            created = []
            for i, s in enumerate(raw_slides):
                bullets = s.get('bullets', [])
                content = '\n'.join(bullets)
                layout = _detect_slide_layout(
                    s.get('title', ''), i, len(raw_slides),
                )
                slide = ToolSlide.objects.create(
                    presentation=deck,
                    order=i,
                    layout=layout,
                    title=s.get('title', ''),
                    content=content,
                    speaker_notes=s.get('notes', ''),
                    emoji=s.get('emoji', ''),
                )
                created.append({
                    'slide_id': slide.pk,
                    'order': slide.order,
                    'layout': slide.layout,
                    'title': slide.title,
                    'content': slide.content,
                    'emoji': slide.emoji,
                    'speaker_notes': slide.speaker_notes,
                    'image_url': '',
                })
            if data.get('update_title') and topic:
                deck.title = topic
            deck.save()

        return JsonResponse({
            'ok': True,
            'slides': created,
            'deck_title': deck.title,
            'activities': result.get('activities', []),
        })

    # ── ges_generate ────────────────────────────────────────
    elif action == 'ges_generate':
        indicator = data.get('indicator', '').strip()
        sub_strand = data.get('sub_strand', '').strip()
        topic = data.get('topic', '').strip() or indicator
        if not indicator:
            return JsonResponse({'error': 'Indicator is required for GES generation'}, status=400)

        subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(
            deck.subject, deck.subject or 'General Studies',
        )
        class_name = deck.target_class or 'Basic 5'

        code_only = bool(_GES_CODE_RE.match(indicator))
        indicator_instruction = (
            f"Target Indicator Code: {indicator}\n"
            "IMPORTANT: This is a Ghana GES curriculum code. "
            "Resolve it to the full performance indicator statement. "
            "Use ONLY the descriptive statement (not the numeric code) throughout."
        ) if code_only else f"Target Indicator: {indicator}"

        sub_strand_line = f'\n- Sub-strand: {sub_strand}' if sub_strand else ''

        system_prompt = (
            "You are a Ghana Education Service (GES) curriculum expert who "
            "creates rich, presentation-ready slide decks aligned to GES standards.\n\n"
            f"Generate a complete GES-aligned teaching slide deck for {class_name} "
            f"{subject_label}.\n"
            f"- {indicator_instruction}{sub_strand_line}\n\n"
            "Return a JSON object with EXACTLY this structure:\n"
            "{\n"
            '  "slides": [\n'
            '    {"title": "...", "bullets": ["..."], '
            '"notes": "...", "emoji": "..."}\n'
            "  ],\n"
            '  "ges_meta": {\n'
            '    "strand": "...", "sub_strand": "...",\n'
            '    "content_standard": "...", "indicator": "...",\n'
            '    "performance_indicator": "...", "core_competencies": "...",\n'
            '    "keywords": "..."\n'
            "  }\n"
            "}\n\n"
            "Each slide MUST include an \"emoji\" field.\n\n"
            "SLIDE STRUCTURE \u2014 8 SLIDES (MANDATORY):\n"
            "1. TITLE & INDICATOR: title, indicator statement, strand/sub-strand context\n"
            "2. CORE COMPETENCIES & OBJECTIVES: what learners will achieve (linked to indicator)\n"
            "3. KEY VOCABULARY: 3-4 essential terms with clear definitions\n"
            "4. INTRODUCTION / STARTER: Phase 1 starter activity (5-7 min)\n"
            "5. DEVELOPMENT / NEW LEARNING: Phase 2 main teaching content aligned to indicator\n"
            "6. WORKED EXAMPLE: step-by-step worked example with Ghanaian context\n"
            "7. ASSESSMENT / EVALUATION: Phase 3 check for understanding (3-4 questions)\n"
            "8. SUMMARY & HOMEWORK: key takeaways + homework task reinforcing indicator\n\n"
            "RULES:\n"
            "- Write FULL, MEANINGFUL content \u2014 not outlines or placeholders\n"
            "- Every slide MUST directly connect to the target indicator\n"
            "- Use Ghanaian context (local names, currency, places, practices)\n"
            "- Bullets must be complete sentences students can read and learn from\n"
            "- Speaker notes are for the TEACHER: include delivery tips, expected answers\n"
            "- Never reference indicator codes in slide text \u2014 use descriptive language"
        )
        user_prompt = (
            f"Create a complete GES-aligned presentation on '{topic}' for "
            f"{class_name} {subject_label}. "
            f"Indicator: {indicator}. "
            "Every slide must directly support achieving this indicator."
        )

        try:
            import openai
            from django.conf import settings as django_settings
            client = openai.OpenAI(
                api_key=getattr(django_settings, 'OPENAI_API_KEY', ''),
            )
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.6,
                max_tokens=3000,
            )
            raw_text = resp.choices[0].message.content.strip()
            if raw_text.startswith('```'):
                raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            result = json.loads(raw_text.strip())
        except Exception as exc:
            logger.warning('GES slide generation failed: %s', exc)
            return JsonResponse(
                {'error': 'GES generation failed. Please try again.'},
                status=500,
            )

        raw_slides = result.get('slides', [])
        ges_meta = result.get('ges_meta', {})

        # Map GES slide positions to appropriate layouts
        ges_layout_map = {
            0: 'title',       # Title & Indicator
            1: 'bullets',     # Core Competencies & Objectives
            2: 'bullets',     # Key Vocabulary
            3: 'bullets',     # Introduction / Starter
            4: 'bullets',     # Development / New Learning
            5: 'bullets',     # Worked Example
            6: 'bullets',     # Assessment / Evaluation
            7: 'summary',     # Summary & Homework
        }

        with transaction.atomic():
            deck.slides.all().delete()
            created = []
            for i, s in enumerate(raw_slides):
                bullets = s.get('bullets', [])
                content = '\n'.join(bullets)
                layout = ges_layout_map.get(i, _detect_slide_layout(
                    s.get('title', ''), i, len(raw_slides),
                ))
                slide = ToolSlide.objects.create(
                    presentation=deck,
                    order=i,
                    layout=layout,
                    title=s.get('title', ''),
                    content=content,
                    speaker_notes=s.get('notes', ''),
                    emoji=s.get('emoji', ''),
                )
                created.append({
                    'slide_id': slide.pk,
                    'order': slide.order,
                    'layout': slide.layout,
                    'title': slide.title,
                    'content': slide.content,
                    'emoji': slide.emoji,
                    'speaker_notes': slide.speaker_notes,
                    'image_url': '',
                })
            if data.get('update_title') and topic:
                deck.title = topic
            deck.save()

        return JsonResponse({
            'ok': True,
            'slides': created,
            'deck_title': deck.title,
            'ges_meta': ges_meta,
        })

    # ── duplicate_slide ─────────────────────────────────────
    elif action == 'duplicate_slide':
        slide_id = data.get('slide_id')
        source = get_object_or_404(ToolSlide, pk=slide_id, presentation=deck)
        max_order = deck.slides.aggregate(m=Max('order'))['m'] or -1
        new_slide = ToolSlide.objects.create(
            presentation=deck,
            order=max_order + 1,
            layout=source.layout,
            title=source.title + ' (copy)',
            content=source.content,
            speaker_notes=source.speaker_notes,
            emoji=source.emoji,
            image_url=source.image_url,
        )
        deck.save()
        return JsonResponse({
            'ok': True,
            'slide_id': new_slide.pk,
            'order': new_slide.order,
            'layout': new_slide.layout,
            'title': new_slide.title,
            'content': new_slide.content,
            'emoji': new_slide.emoji,
            'speaker_notes': new_slide.speaker_notes,
            'image_url': new_slide.image_url,
        })

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


@_tool_required
@_require_tool('slide-generator')
def deck_present(request, pk):
    """Fullscreen presentation mode."""
    from django.utils import timezone

    profile = request.user.individual_profile
    deck = get_object_or_404(ToolPresentation, pk=pk, profile=profile)
    slides = list(deck.slides.order_by('order'))

    deck.times_presented += 1
    deck.last_presented_at = timezone.now()
    deck.save(update_fields=['times_presented', 'last_presented_at'])

    share_url = request.build_absolute_uri(
        f'/u/tools/presentations/share/{deck.share_token}/',
    )
    ctx = {
        'deck': deck,
        'slides': slides,
        'share_url': share_url,
    }
    return render(request, 'individual/tools/presentations/present.html', ctx)


@_tool_required
@_require_tool('slide-generator')
@require_POST
def deck_delete(request, pk):
    """Delete a presentation."""
    profile = request.user.individual_profile
    deck = get_object_or_404(ToolPresentation, pk=pk, profile=profile)
    deck.delete()
    messages.success(request, 'Presentation deleted.')
    return redirect('individual:deck_list')


@_tool_required
@_require_tool('slide-generator')
@require_POST
def deck_duplicate(request, pk):
    """Duplicate a presentation with all its slides."""
    profile = request.user.individual_profile
    deck = get_object_or_404(ToolPresentation, pk=pk, profile=profile)

    new_deck = ToolPresentation.objects.create(
        profile=profile,
        title=f'{deck.title} (copy)',
        subject=deck.subject,
        target_class=deck.target_class,
        theme=deck.theme,
        transition=deck.transition,
    )
    for slide in deck.slides.order_by('order'):
        ToolSlide.objects.create(
            presentation=new_deck,
            order=slide.order,
            layout=slide.layout,
            title=slide.title,
            content=slide.content,
            speaker_notes=slide.speaker_notes,
            emoji=slide.emoji,
            image_url=slide.image_url,
        )

    messages.success(request, f'Duplicated \u201c{deck.title}\u201d.')
    return redirect('individual:deck_editor', pk=new_deck.pk)


@_tool_required
@_require_tool('slide-generator')
def deck_print(request, pk):
    """Print-friendly handout view."""
    profile = request.user.individual_profile
    deck = get_object_or_404(ToolPresentation, pk=pk, profile=profile)
    slides = list(deck.slides.order_by('order'))
    ctx = {'deck': deck, 'slides': slides}
    return render(request, 'individual/tools/presentations/print.html', ctx)


def deck_share(request, token):
    """Public read-only view of a shared presentation (no login required)."""
    _ensure_public_schema()
    deck = get_object_or_404(ToolPresentation, share_token=token)
    slides = list(deck.slides.order_by('order'))
    ctx = {
        'deck': deck,
        'slides': slides,
        'share_url': request.build_absolute_uri(),
        'is_shared_view': True,
    }
    return render(request, 'individual/tools/presentations/present.html', ctx)
