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
    ToolQuestion,
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

    ctx = {
        'tools': tools,
        'profile': profile,
        'role': 'teacher',
        'question_count': q_count,
        'exam_count': e_count,
        'lesson_count': l_count,
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
        plan = ToolLessonPlan.objects.create(
            profile=profile,
            title=request.POST.get('title', 'Untitled Lesson').strip(),
            subject=request.POST.get('subject', 'mathematics'),
            target_class=request.POST.get('target_class', ''),
            topic=request.POST.get('topic', '').strip(),
            duration_minutes=int(request.POST.get('duration_minutes', 40)),
            objectives=request.POST.get('objectives', '').strip(),
            materials=request.POST.get('materials', '').strip(),
            introduction=request.POST.get('introduction', '').strip(),
            development=request.POST.get('development', '').strip(),
            assessment=request.POST.get('assessment', '').strip(),
            closure=request.POST.get('closure', '').strip(),
            notes=request.POST.get('notes', '').strip(),
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
        plan.duration_minutes = int(request.POST.get('duration_minutes', plan.duration_minutes))
        plan.objectives = request.POST.get('objectives', plan.objectives).strip()
        plan.materials = request.POST.get('materials', plan.materials).strip()
        plan.introduction = request.POST.get('introduction', plan.introduction).strip()
        plan.development = request.POST.get('development', plan.development).strip()
        plan.assessment = request.POST.get('assessment', plan.assessment).strip()
        plan.closure = request.POST.get('closure', plan.closure).strip()
        plan.notes = request.POST.get('notes', plan.notes).strip()
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
    """AI-generate a lesson plan from topic + subject."""
    profile = request.user.individual_profile
    subject = request.POST.get('subject', 'mathematics')
    topic = request.POST.get('topic', '')
    target_class = request.POST.get('target_class', '')
    duration = int(request.POST.get('duration_minutes', 40))

    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)

    subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(subject, subject)

    prompt = (
        f"Create a detailed lesson plan for teaching '{topic}' in {subject_label}"
    )
    if target_class:
        prompt += f" to {target_class} students"
    prompt += (
        f". Duration: {duration} minutes. "
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
                {'role': 'system', 'content': 'You are a Ghanaian GES curriculum specialist creating lesson plans.'},
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
