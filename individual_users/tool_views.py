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
    AITutorConversation,
    AITutorMessage,
    GESLetter,
    IndividualProfile,
    LicensureAnswer,
    LicensureQuestion,
    LicensureQuizAttempt,
    MarkingSession,
    ReportCardEntry,
    ReportCardSet,
    StudentMark,
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
        'tools': ['ai_tutor'],
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
        'tools': ['report_card'],
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
    {
        'slug': 'letter-writer',
        'name': 'GES Letter Writer',
        'icon': 'bi-envelope-paper',
        'color': '#2563eb',
        'tagline': 'Official GES letter templates and AI-powered drafting',
        'description': (
            'Browse sample GES letters for transfers, leave, promotions, '
            'complaints and more. Use AI to generate custom letters '
            'following official GES format and conventions.'
        ),
        'features': [
            '12+ GES letter categories with samples',
            'AI-powered letter generation',
            'Official GES formatting & conventions',
            'Edit, save and print-ready output',
            'Custom letters from scratch',
        ],
        'category': 'productivity',
        'tools': ['ges_letter'],
    },
    {
        'slug': 'paper-marker',
        'name': 'Paper Marker',
        'icon': 'bi-clipboard-check',
        'color': '#e11d48',
        'tagline': 'Mark objective question papers in seconds',
        'description': (
            'Set an answer key, enter student responses and get instant '
            'auto-marking with score breakdowns, class statistics and '
            'per-question analysis — perfect for MCQ exams.'
        ),
        'features': [
            'Flexible answer key setup (A-D or A-E)',
            'Instant auto-marking with colour-coded results',
            'Per-question analysis — hardest & easiest questions',
            'Class statistics: average, highest, lowest, pass rate',
            'Print-ready results sheet per student or class',
        ],
        'category': 'assessment',
        'tools': ['paper_marker'],
    },
    {
        'slug': 'licensure-prep',
        'name': 'GTLE Licensure Prep',
        'icon': 'bi-mortarboard',
        'color': '#0d9488',
        'tagline': 'Pass the GTLE with confidence — practice, track, succeed',
        'description': (
            'Prepare for the Ghana Teacher Licensure Examination with an '
            'extensive question bank covering all four GTLE domains. '
            'Take timed mock exams, track your progress by domain, and '
            'use AI to generate unlimited practice questions.'
        ),
        'features': [
            'All 4 GTLE domains: Literacy, Numeracy, Pedagogy, Management',
            'Timed mock exams simulating real conditions',
            'AI-powered question generation by domain',
            'Performance analytics & score history',
            'Detailed explanations for every answer',
            'Past GTLE questions bank',
        ],
        'category': 'professional',
        'tools': ['licensure_prep'],
    },
]


def _get_tool_by_slug(slug):
    """Lookup a tool entry from the catalog by slug."""
    return next((t for t in TOOLS_CATALOG if t['slug'] == slug), None)


# ── Access Control ───────────────────────────────────────────────────────────

def _ensure_public_schema():
    connection.set_schema_to_public()


def _tool_required(view_func):
    """Decorator: require login + individual user_type + teacher role + verified."""
    from functools import wraps
    from django.contrib.auth import logout

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
        # Block unverified users
        if not profile.is_verified:
            method = 'phone' if (profile.phone_number and not request.user.email) else 'email'
            request.session['pending_verification_user_id'] = request.user.pk
            request.session['pending_verification_method'] = method
            logout(request)
            messages.info(request, 'Please verify your account to continue.')
            return redirect('individual:verify')
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
    lic_count = LicensureQuizAttempt.objects.filter(profile=profile, completed=True).count()
    tutor_count = AITutorConversation.objects.filter(profile=profile).count()
    letter_count = GESLetter.objects.filter(profile=profile).count()
    marker_count = MarkingSession.objects.filter(profile=profile).count()
    rc_count = ReportCardSet.objects.filter(profile=profile).count()

    ctx = {
        'tools': tools,
        'profile': profile,
        'role': 'teacher',
        'question_count': q_count,
        'exam_count': e_count,
        'lesson_count': l_count,
        'deck_count': d_count,
        'licensure_attempt_count': lic_count,
        'tutor_count': tutor_count,
        'letter_count': letter_count,
        'marker_count': marker_count,
        'rc_count': rc_count,
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
def lesson_plan_print(request, pk):
    """GES Standard / B7 print view for a lesson plan."""
    profile = request.user.individual_profile
    plan = get_object_or_404(ToolLessonPlan, pk=pk, profile=profile)

    template_format = (request.GET.get('template') or 'ges').strip().lower()
    b7_meta = plan.b7_meta or {}

    b7_context = {
        'week_ending': b7_meta.get('week_ending', plan.created_at.strftime('%Y-%m-%d') if plan.created_at else ''),
        'day': b7_meta.get('day', 'Monday – Friday'),
        'class_size': b7_meta.get('class_size', ''),
        'strand': b7_meta.get('strand', plan.topic),
        'indicator': b7_meta.get('indicator', plan.indicator or 'See Content Standard'),
        'lesson_of': b7_meta.get('lesson_of', '1 of 3'),
        'perf_indicator': b7_meta.get('perf_indicator', b7_meta.get('performance_indicator', 'Learners can relate the lesson to real life situations.')),
        'core_competencies': b7_meta.get('core_competencies', 'CP 5.1, CC 8.1'),
        'references': b7_meta.get('references', f"National {plan.get_subject_display()} Curriculum"),
        'keywords': b7_meta.get('keywords', plan.topic),
    }

    if template_format in {'b7', 'weekly'}:
        template_name = 'individual/tools/lesson_plan_print_b7.html'
    else:
        template_name = 'individual/tools/lesson_plan_print_ges.html'

    return render(request, template_name, {
        'plan': plan,
        'profile': profile,
        'role': 'teacher',
        'print_mode': True,
        'current_template': template_format,
        'b7_meta_json': json.dumps(b7_meta or {}),
        'b7': b7_context,
    })


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


# ── GTLE Licensure Preparation ───────────────────────────────────────────────

@_tool_required
@_require_tool('licensure-prep')
def licensure_dashboard(request):
    """Main dashboard for GTLE prep – stats, domain breakdown, recent quizzes."""
    profile = request.user.individual_profile

    # Question bank stats
    total_qs = LicensureQuestion.objects.filter(profile=profile).count()
    domain_counts = dict(
        LicensureQuestion.objects.filter(profile=profile)
        .values_list('domain')
        .annotate(c=Count('id'))
        .values_list('domain', 'c')
    )

    # Attempt stats
    attempts = LicensureQuizAttempt.objects.filter(profile=profile, completed=True)
    total_attempts = attempts.count()
    recent = attempts[:5]

    # Per-domain performance (from completed answers)
    domain_perf = {}
    for code, label in LicensureQuestion.DOMAIN_CHOICES:
        qs = LicensureAnswer.objects.filter(
            attempt__profile=profile,
            attempt__completed=True,
            question__domain=code,
        )
        total = qs.count()
        correct = qs.filter(is_correct=True).count()
        domain_perf[code] = {
            'label': label,
            'total': total,
            'correct': correct,
            'percent': round(correct / total * 100) if total else 0,
            'questions': domain_counts.get(code, 0),
        }

    # Best score
    best = None
    if total_attempts:
        best_attempt = max(attempts, key=lambda a: a.score_percent)
        best = best_attempt.score_percent

    # Group questions by domain for the question bank browser
    questions_by_domain = {}
    for code, label in LicensureQuestion.DOMAIN_CHOICES:
        qs = LicensureQuestion.objects.filter(
            profile=profile, domain=code,
        ).order_by('-created_at')
        if qs.exists():
            questions_by_domain[code] = {
                'label': label,
                'questions': qs[:50],
                'count': domain_counts.get(code, 0),
            }

    ctx = {
        'total_questions': total_qs,
        'total_attempts': total_attempts,
        'best_score': best,
        'recent_attempts': recent,
        'domain_perf': domain_perf,
        'domains': LicensureQuestion.DOMAIN_CHOICES,
        'difficulties': LicensureQuestion.DIFFICULTY_CHOICES,
        'sources': LicensureQuestion.SOURCE_CHOICES,
        'questions_by_domain': questions_by_domain,
    }
    return render(request, 'individual/tools/licensure/dashboard.html', ctx)


@_tool_required
@_require_tool('licensure-prep')
@require_POST
def licensure_quiz_start(request):
    """Create a quiz attempt and redirect to the quiz-taking page."""
    profile = request.user.individual_profile

    mode = request.POST.get('mode', 'practice')
    domain = request.POST.get('domain', '')
    num_q = min(int(request.POST.get('num_questions', 20)), 100)
    time_limit = int(request.POST.get('time_limit', 0))

    qs = LicensureQuestion.objects.filter(profile=profile)
    if domain:
        qs = qs.filter(domain=domain)

    # Random selection
    question_ids = list(qs.order_by('?').values_list('id', flat=True)[:num_q])

    if not question_ids:
        messages.warning(
            request,
            'No questions available. Generate some questions first using the AI Generator.',
        )
        return redirect('individual:licensure_dashboard')

    attempt = LicensureQuizAttempt.objects.create(
        profile=profile,
        mode=mode,
        domain_filter=domain,
        total_questions=len(question_ids),
        time_limit_minutes=time_limit,
    )

    # Create answer stubs
    answers = [
        LicensureAnswer(attempt=attempt, question_id=qid)
        for qid in question_ids
    ]
    LicensureAnswer.objects.bulk_create(answers)

    return redirect('individual:licensure_quiz_take', pk=attempt.pk)


@_tool_required
@_require_tool('licensure-prep')
def licensure_quiz_take(request, pk):
    """Render the quiz-taking interface. All questions loaded as JSON."""
    profile = request.user.individual_profile
    attempt = get_object_or_404(
        LicensureQuizAttempt, pk=pk, profile=profile, completed=False,
    )

    answer_objs = attempt.answers.select_related('question').order_by('pk')
    questions_json = []
    for ans in answer_objs:
        q = ans.question
        questions_json.append({
            'answer_id': ans.pk,
            'question_id': q.pk,
            'domain': q.get_domain_display(),
            'domain_code': q.domain,
            'difficulty': q.difficulty,
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'selected': ans.selected_option,
        })

    ctx = {
        'attempt': attempt,
        'questions_json': json.dumps(questions_json),
        'total': attempt.total_questions,
        'time_limit': attempt.time_limit_minutes,
    }
    return render(request, 'individual/tools/licensure/quiz_take.html', ctx)


@_tool_required
@_require_tool('licensure-prep')
def licensure_api(request):
    """AJAX API for licensure quiz actions."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    profile = request.user.individual_profile
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = data.get('action', '')

    # ── Submit quiz answers ──────────────────────────────────────────────
    if action == 'submit_quiz':
        attempt_id = data.get('attempt_id')
        answers = data.get('answers', [])  # [{answer_id, selected}]
        time_spent = data.get('time_spent_seconds', 0)

        attempt = get_object_or_404(
            LicensureQuizAttempt, pk=attempt_id, profile=profile, completed=False,
        )

        correct = 0
        for ans_data in answers:
            try:
                ans = LicensureAnswer.objects.select_related('question').get(
                    pk=ans_data.get('answer_id'), attempt=attempt,
                )
            except LicensureAnswer.DoesNotExist:
                continue
            selected = str(ans_data.get('selected', '')).upper()
            ans.selected_option = selected
            ans.is_correct = (selected == ans.question.correct_option.upper())
            ans.time_spent_seconds = int(ans_data.get('time_spent', 0))
            ans.save()
            if ans.is_correct:
                correct += 1

        from django.utils import timezone
        attempt.correct_count = correct
        attempt.time_spent_seconds = int(time_spent)
        attempt.completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        return JsonResponse({
            'ok': True,
            'attempt_id': attempt.pk,
            'score_percent': attempt.score_percent,
            'correct': correct,
            'total': attempt.total_questions,
            'passed': attempt.passed,
        })

    # ── AI Generate Questions ────────────────────────────────────────────
    if action == 'ai_generate':
        domain = data.get('domain', 'pedagogy')
        difficulty = data.get('difficulty', 'medium')
        count = min(int(data.get('count', 10)), 20)

        domain_labels = dict(LicensureQuestion.DOMAIN_CHOICES)
        domain_label = domain_labels.get(domain, domain)

        import openai
        client = openai.OpenAI()

        system_prompt = f"""You are a Ghana Teacher Licensure Examination (GTLE) question writer.
Generate {count} multiple-choice questions for the "{domain_label}" domain at {difficulty} difficulty.

Each question must have exactly 4 options (A, B, C, D) with one correct answer.

Return a JSON array of objects with these fields:
- "question_text": the question
- "option_a", "option_b", "option_c", "option_d": the four options
- "correct_option": "A", "B", "C", or "D"
- "explanation": why the correct answer is right (1-2 sentences)
- "topic": a short topic label (e.g. "Reading Comprehension", "Fractions", "Bloom's Taxonomy")

Domain details:
- Literacy: English language proficiency — grammar, vocabulary, reading comprehension, sentence structure, essay writing skills
- Numeracy: Mathematical competence — arithmetic, fractions, percentages, geometry, data interpretation, algebra basics
- Pedagogical Knowledge: Teaching methodology — lesson planning, Bloom's taxonomy, curriculum design, assessment methods, differentiation, constructivism, learning theories
- Classroom Management: Managing learning environments — behaviour strategies, classroom organisation, inclusive education, time management, student motivation

Make questions realistic and aligned with Ghana's NTC licensure standards. Vary the difficulty.
Return ONLY the JSON array, no explanation or markdown."""

        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'Generate {count} {difficulty} {domain_label} questions for the GTLE exam.'},
                ],
                temperature=0.8,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1]
                if raw.endswith('```'):
                    raw = raw[:-3]
            items = json.loads(raw)
        except Exception as e:
            logger.error('GTLE AI generation failed: %s', e)
            return JsonResponse({'error': 'AI generation failed. Please try again.'}, status=500)

        created = []
        for item in items:
            q = LicensureQuestion.objects.create(
                profile=profile,
                domain=domain,
                topic=item.get('topic', ''),
                difficulty=difficulty,
                source='ai_generated',
                question_text=item.get('question_text', ''),
                option_a=item.get('option_a', ''),
                option_b=item.get('option_b', ''),
                option_c=item.get('option_c', ''),
                option_d=item.get('option_d', ''),
                correct_option=item.get('correct_option', 'A'),
                explanation=item.get('explanation', ''),
            )
            created.append({
                'id': q.pk,
                'domain': domain,
                'topic': q.topic,
                'difficulty': q.difficulty,
                'question_text': q.question_text[:80],
            })

        return JsonResponse({
            'ok': True,
            'count': len(created),
            'questions': created,
        })

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


@_tool_required
@_require_tool('licensure-prep')
def licensure_quiz_review(request, pk):
    """Review a completed quiz attempt with answers and explanations."""
    profile = request.user.individual_profile
    attempt = get_object_or_404(
        LicensureQuizAttempt, pk=pk, profile=profile, completed=True,
    )

    answer_objs = attempt.answers.select_related('question').order_by('pk')

    # Domain breakdown
    domain_stats = {}
    for ans in answer_objs:
        d = ans.question.domain
        if d not in domain_stats:
            domain_stats[d] = {'label': ans.question.get_domain_display(), 'total': 0, 'correct': 0}
        domain_stats[d]['total'] += 1
        if ans.is_correct:
            domain_stats[d]['correct'] += 1
    for v in domain_stats.values():
        v['percent'] = round(v['correct'] / v['total'] * 100) if v['total'] else 0

    ctx = {
        'attempt': attempt,
        'answers': answer_objs,
        'domain_stats': domain_stats,
    }
    return render(request, 'individual/tools/licensure/quiz_review.html', ctx)


@_tool_required
@_require_tool('licensure-prep')
def licensure_history(request):
    """Full history of quiz attempts."""
    profile = request.user.individual_profile
    attempts = LicensureQuizAttempt.objects.filter(
        profile=profile, completed=True,
    ).order_by('-completed_at')

    ctx = {
        'attempts': attempts[:50],
        'domains': LicensureQuestion.DOMAIN_CHOICES,
    }
    return render(request, 'individual/tools/licensure/history.html', ctx)


@_tool_required
@_require_tool('licensure-prep')
@require_POST
def licensure_load_bank(request):
    """Load the built-in GTLE practice question bank into user's profile."""
    from .gtle_question_bank import GTLE_QUESTION_BANK

    profile = request.user.individual_profile
    existing = LicensureQuestion.objects.filter(
        profile=profile, source='practice',
    ).count()

    if existing >= len(GTLE_QUESTION_BANK):
        messages.info(request, 'Practice question bank is already loaded.')
        return redirect('individual:licensure_dashboard')

    # Avoid duplicates — check by question_text
    existing_texts = set(
        LicensureQuestion.objects.filter(profile=profile)
        .values_list('question_text', flat=True)
    )

    new_qs = []
    for q in GTLE_QUESTION_BANK:
        if q['question_text'] not in existing_texts:
            new_qs.append(LicensureQuestion(profile=profile, **q))

    if new_qs:
        LicensureQuestion.objects.bulk_create(new_qs)
        messages.success(
            request,
            f'{len(new_qs)} GTLE practice questions loaded into your question bank!',
        )
    else:
        messages.info(request, 'All practice questions are already in your bank.')

    return redirect('individual:licensure_dashboard')


# ══════════════════════════════════════════════════════════════════════════════
# AI Teaching Assistant
# ══════════════════════════════════════════════════════════════════════════════

_AI_TUTOR_SYSTEM_PROMPTS = {
    'explain': (
        'You are an expert teacher educator. Explain concepts clearly with examples, '
        'analogies and step-by-step breakdowns suitable for a Ghanaian classroom. '
        'Use simple language and relate to the GES curriculum where relevant.'
    ),
    'worksheet': (
        'You are a worksheet and activity designer for teachers. Create engaging, '
        'print-ready worksheets with clear instructions, varied question types, '
        'and answer keys. Format using markdown headings, numbered lists and tables.'
    ),
    'feedback': (
        'You are a marking and assessment feedback specialist. Help teachers write '
        'constructive, specific and encouraging feedback for student work. Provide '
        'strengths, areas for improvement and next steps.'
    ),
    'notes': (
        'You are a study notes creator for teachers and students. Generate well-structured, '
        'concise revision notes with key points, definitions, mnemonics and summary tables. '
        'Use markdown formatting for readability.'
    ),
    'general': (
        'You are an AI Teaching Assistant for Ghanaian educators. Help with lesson planning, '
        'content creation, pedagogy questions and classroom strategies. Be practical, '
        'culturally relevant and aligned with GES standards.'
    ),
}

_AI_TUTOR_MODE_META = {
    'explain': {'icon': 'bi-lightbulb', 'color': '#f59e0b', 'label': 'Concept Explainer',
                'placeholder': 'e.g. Explain photosynthesis for Basic 8 students...'},
    'worksheet': {'icon': 'bi-file-earmark-ruled', 'color': '#8b5cf6', 'label': 'Worksheet Generator',
                  'placeholder': 'e.g. Create a worksheet on fractions for Basic 7...'},
    'feedback': {'icon': 'bi-chat-square-text', 'color': '#ef4444', 'label': 'Marking Feedback',
                 'placeholder': 'e.g. Write feedback for a student who scored 12/20 on their essay about...'},
    'notes': {'icon': 'bi-journal-text', 'color': '#059669', 'label': 'Study Notes Creator',
              'placeholder': 'e.g. Create revision notes on the Water Cycle for JHS 2...'},
    'general': {'icon': 'bi-robot', 'color': '#0891b2', 'label': 'General Assistant',
                'placeholder': 'Ask me anything about teaching...'},
}


@_tool_required
@_require_tool('ai-tutor')
def ai_tutor_dashboard(request):
    """Main AI Teaching Assistant chat interface."""
    profile = request.user.individual_profile
    conversations = AITutorConversation.objects.filter(profile=profile)[:20]
    total_conversations = AITutorConversation.objects.filter(profile=profile).count()
    total_messages = AITutorMessage.objects.filter(
        conversation__profile=profile, role='user',
    ).count()

    # If a conversation ID is provided, load it
    conv_id = request.GET.get('c')
    active_conv = None
    active_messages = []
    active_mode = request.GET.get('mode', 'general')
    if conv_id:
        try:
            active_conv = AITutorConversation.objects.get(pk=conv_id, profile=profile)
            active_messages = list(active_conv.messages.all())
            active_mode = active_conv.mode
        except AITutorConversation.DoesNotExist:
            pass

    ctx = {
        'conversations': conversations,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'active_conv': active_conv,
        'active_messages': active_messages,
        'active_mode': active_mode,
        'modes': AITutorConversation.MODE_CHOICES,
        'mode_meta': _AI_TUTOR_MODE_META,
        'subjects': ToolQuestion.SUBJECT_CHOICES,
    }
    return render(request, 'individual/tools/ai-tutor/dashboard.html', ctx)


@_tool_required
@_require_tool('ai-tutor')
def ai_tutor_api(request):
    """AJAX endpoint for AI Tutor chat."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    profile = request.user.individual_profile
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = data.get('action', 'chat')

    # ── Send message ─────────────────────────────────────────────────────
    if action == 'chat':
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        # Limit message length
        if len(message) > 4000:
            return JsonResponse({'error': 'Message too long (max 4000 chars)'}, status=400)

        conv_id = data.get('conversation_id')
        mode = data.get('mode', 'general')
        subject = data.get('subject', '')

        if mode not in _AI_TUTOR_SYSTEM_PROMPTS:
            mode = 'general'

        # Get or create conversation
        if conv_id:
            try:
                conv = AITutorConversation.objects.get(pk=conv_id, profile=profile)
            except AITutorConversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            title = message[:80] + ('…' if len(message) > 80 else '')
            conv = AITutorConversation.objects.create(
                profile=profile, mode=mode, title=title, subject=subject,
            )

        # Save user message
        AITutorMessage.objects.create(conversation=conv, role='user', content=message)

        # Build message history for OpenAI (last 20 messages for context window)
        history = list(conv.messages.order_by('created_at')[:20].values('role', 'content'))
        system_prompt = _AI_TUTOR_SYSTEM_PROMPTS[conv.mode]
        if conv.subject:
            subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(conv.subject, conv.subject)
            system_prompt += f'\n\nThe teacher is currently working on: {subject_label}.'

        oai_messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            oai_messages.append({'role': msg['role'], 'content': msg['content']})

        # Call OpenAI
        import openai
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=oai_messages,
                temperature=0.7,
                max_tokens=2000,
            )
            assistant_content = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error('AI Tutor API error: %s', e)
            return JsonResponse({'error': 'AI service temporarily unavailable. Please try again.'}, status=500)

        # Save assistant response
        AITutorMessage.objects.create(
            conversation=conv, role='assistant', content=assistant_content,
        )

        return JsonResponse({
            'ok': True,
            'conversation_id': conv.pk,
            'title': conv.title,
            'message': assistant_content,
        })

    # ── Delete conversation ──────────────────────────────────────────────
    if action == 'delete_conversation':
        conv_id = data.get('conversation_id')
        try:
            conv = AITutorConversation.objects.get(pk=conv_id, profile=profile)
            conv.delete()
            return JsonResponse({'ok': True})
        except AITutorConversation.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


# ═══════════════════════════════════════════════════════════════════════════════
# GES LETTER WRITER
# ═══════════════════════════════════════════════════════════════════════════════

@_tool_required
@_require_tool('letter-writer')
def letter_dashboard(request):
    """List all letters with category filtering and sample browser."""
    _ensure_public_schema()
    profile = request.user.individual_profile

    letters = GESLetter.objects.filter(profile=profile, is_sample=False)
    samples = GESLetter.objects.filter(profile=profile, is_sample=True)

    category = request.GET.get('category', '')
    if category:
        letters = letters.filter(category=category)

    status_filter = request.GET.get('status', '')
    if status_filter:
        letters = letters.filter(status=status_filter)

    return render(request, 'individual/tools/letter-writer/dashboard.html', {
        'letters': letters,
        'samples': samples,
        'categories': GESLetter.CATEGORY_CHOICES,
        'current_category': category,
        'current_status': status_filter,
        'total_count': GESLetter.objects.filter(profile=profile, is_sample=False).count(),
        'draft_count': GESLetter.objects.filter(profile=profile, is_sample=False, status='draft').count(),
        'final_count': GESLetter.objects.filter(profile=profile, is_sample=False, status='final').count(),
    })


@_tool_required
@_require_tool('letter-writer')
def letter_create(request):
    """Create a new letter (blank or from category)."""
    _ensure_public_schema()
    profile = request.user.individual_profile

    if request.method == 'POST':
        from django.utils import timezone
        letter = GESLetter.objects.create(
            profile=profile,
            title=request.POST.get('title', 'Untitled Letter').strip() or 'Untitled Letter',
            category=request.POST.get('category', 'request'),
            status='draft',
            recipient_name=request.POST.get('recipient_name', '').strip(),
            recipient_title=request.POST.get('recipient_title', '').strip(),
            sender_name=request.POST.get('sender_name', '').strip(),
            sender_title=request.POST.get('sender_title', '').strip(),
            school_name=request.POST.get('school_name', '').strip(),
            district=request.POST.get('district', '').strip(),
            region=request.POST.get('region', '').strip(),
            reference_number=request.POST.get('reference_number', '').strip(),
            date_written=request.POST.get('date_written') or timezone.now().date(),
            body=request.POST.get('body', '').strip(),
        )
        messages.success(request, 'Letter created.')
        return redirect('individual:letter_edit', pk=letter.pk)

    # GET → show editor with blank form
    category = request.GET.get('category', 'request')
    return render(request, 'individual/tools/letter-writer/editor.html', {
        'letter': None,
        'categories': GESLetter.CATEGORY_CHOICES,
        'initial_category': category,
        'mode': 'create',
    })


@_tool_required
@_require_tool('letter-writer')
def letter_edit(request, pk):
    """Edit an existing letter."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    letter = get_object_or_404(GESLetter, pk=pk, profile=profile)

    if request.method == 'POST':
        from django.utils import timezone
        letter.title = request.POST.get('title', letter.title).strip() or letter.title
        letter.category = request.POST.get('category', letter.category)
        letter.status = request.POST.get('status', letter.status)
        letter.recipient_name = request.POST.get('recipient_name', '').strip()
        letter.recipient_title = request.POST.get('recipient_title', '').strip()
        letter.sender_name = request.POST.get('sender_name', '').strip()
        letter.sender_title = request.POST.get('sender_title', '').strip()
        letter.school_name = request.POST.get('school_name', '').strip()
        letter.district = request.POST.get('district', '').strip()
        letter.region = request.POST.get('region', '').strip()
        letter.reference_number = request.POST.get('reference_number', '').strip()
        letter.date_written = request.POST.get('date_written') or timezone.now().date()
        letter.body = request.POST.get('body', '').strip()
        letter.save()
        messages.success(request, 'Letter saved.')
        return redirect('individual:letter_edit', pk=letter.pk)

    return render(request, 'individual/tools/letter-writer/editor.html', {
        'letter': letter,
        'categories': GESLetter.CATEGORY_CHOICES,
        'mode': 'edit',
    })


@_tool_required
@_require_tool('letter-writer')
@require_POST
def letter_delete(request, pk):
    """Delete a letter."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    letter = get_object_or_404(GESLetter, pk=pk, profile=profile)
    letter.delete()
    messages.success(request, 'Letter deleted.')
    return redirect('individual:letter_dashboard')


@_tool_required
@_require_tool('letter-writer')
@require_POST
def letter_duplicate(request, pk):
    """Duplicate a letter (typically a sample) as a new personal draft."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    original = get_object_or_404(GESLetter, pk=pk, profile=profile)
    copy = GESLetter.objects.create(
        profile=profile,
        title=original.title if original.is_sample else f'{original.title} (Copy)',
        category=original.category,
        status='draft',
        recipient_name=original.recipient_name,
        recipient_title=original.recipient_title,
        sender_name=original.sender_name,
        sender_title=original.sender_title,
        school_name=original.school_name,
        district=original.district,
        region=original.region,
        reference_number=original.reference_number,
        date_written=original.date_written,
        body=original.body,
        is_sample=False,
        ai_generated=original.ai_generated,
    )
    messages.success(request, f'Letter copied to your drafts — you can now edit it.')
    return redirect('individual:letter_edit', pk=copy.pk)


@_tool_required
@_require_tool('letter-writer')
def letter_print(request, pk):
    """Print-ready standalone view of a letter."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    letter = get_object_or_404(GESLetter, pk=pk, profile=profile)
    return render(request, 'individual/tools/letter-writer/print.html', {
        'letter': letter,
    })


@_tool_required
@_require_tool('letter-writer')
def letter_api(request):
    """AJAX endpoint for AI letter generation and sample seeding."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    _ensure_public_schema()
    profile = request.user.individual_profile

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = data.get('action', '')

    # ── AI Generate Letter ───────────────────────────────────────────────
    if action == 'generate':
        category = data.get('category', 'request')
        details = data.get('details', '').strip()
        sender_name = data.get('sender_name', '').strip()
        sender_title = data.get('sender_title', '').strip()
        recipient_name = data.get('recipient_name', '').strip()
        recipient_title = data.get('recipient_title', '').strip()
        school_name = data.get('school_name', '').strip()
        district = data.get('district', '').strip()
        region = data.get('region', '').strip()

        category_label = dict(GESLetter.CATEGORY_CHOICES).get(category, category)

        if not details:
            return JsonResponse({'error': 'Please provide details about the letter you need.'}, status=400)

        import openai
        client = openai.OpenAI()

        system_prompt = f"""You are an expert at writing official Ghana Education Service (GES) letters.
Write a professional {category_label} letter following GES conventions.

GES letter conventions:
- Use formal British English (Ghana standard)
- Include proper salutation: "Dear Sir/Madam," or "Dear [Title],"
- Reference numbers typically follow format: GES/[District]/[Year]/[Number]
- Use respectful closing: "Yours faithfully," (if addressed to unknown) or "Yours sincerely,"
- Include sender's full name, title, and school
- Be concise, professional, and respectful
- Follow hierarchical addressing (e.g., through Circuit Supervisor to District Director)
- Use proper GES terminology (e.g., "posting", "release", "secondment")

Context provided:
- Category: {category_label}
- Sender: {sender_name or '[Teacher Name]'}, {sender_title or '[Title]'}
- School: {school_name or '[School Name]'}
- District: {district or '[District]'}
- Region: {region or '[Region]'}
- Recipient: {recipient_name or '[Recipient Name]'}, {recipient_title or '[Recipient Title]'}

Return ONLY the letter body text (no JSON, no markdown fences). Start from the salutation.
Do not include the letterhead, date, or reference number — they are handled separately.
End with the closing (e.g., "Yours faithfully,") and leave space for signature."""

        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'Write a {category_label} letter. Details: {details}'},
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            body = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error('Letter AI generation failed: %s', e)
            return JsonResponse({'error': 'AI generation failed. Please try again.'}, status=500)

        return JsonResponse({'ok': True, 'body': body})

    # ── Load Sample Letters ──────────────────────────────────────────────
    if action == 'load_samples':
        samples = _get_sample_letters()
        existing_titles = set(
            GESLetter.objects.filter(profile=profile, is_sample=True)
            .values_list('title', flat=True)
        )
        created = 0
        for s in samples:
            if s['title'] not in existing_titles:
                GESLetter.objects.create(profile=profile, is_sample=True, status='final', **s)
                created += 1

        total = GESLetter.objects.filter(profile=profile, is_sample=True).count()
        if created:
            msg = f'{created} new sample letter(s) added.'
        else:
            msg = 'All sample letters already loaded.'
        return JsonResponse({'ok': True, 'message': msg, 'count': total})

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


def _get_sample_letters():
    """Return a list of sample GES letter dicts for seeding."""
    from django.utils import timezone
    today = timezone.now().date()
    return [
        {
            'title': 'Request for Transfer / Posting',
            'category': 'posting',
            'recipient_name': 'The District Director of Education',
            'recipient_title': 'Ghana Education Service',
            'sender_name': 'John Mensah',
            'sender_title': 'Classroom Teacher',
            'school_name': 'Ashaiman M/A Basic School',
            'district': 'Ashaiman Municipal',
            'region': 'Greater Accra',
            'reference_number': 'GES/ASH/2025/001',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'REQUEST FOR TRANSFER\n\n'
                'I humbly write to request a transfer from my current station at '
                'Ashaiman M/A Basic School to any school within the Tema Metropolitan '
                'area.\n\n'
                'I have served at my current post for the past four (4) years and have '
                'recently relocated to Tema due to family circumstances. The daily commute '
                'has become a significant challenge, affecting my punctuality and overall '
                'effectiveness in the classroom.\n\n'
                'I believe a transfer to a school closer to my new residence will enable me '
                'to give my best to the students and the Service. I am willing to serve at '
                'any school where my services are needed within the said area.\n\n'
                'I hope my request will receive your favourable consideration.\n\n'
                'Yours faithfully,\n\n\n'
                'John Mensah\n'
                'Staff ID: GES/TC/2020/12345\n'
                'Classroom Teacher\n'
                'Ashaiman M/A Basic School'
            ),
        },
        {
            'title': 'Application for Leave of Absence',
            'category': 'leave',
            'recipient_name': 'The Headteacher',
            'recipient_title': 'Korle-Bu M/A JHS',
            'sender_name': 'Grace Adjei',
            'sender_title': 'Assistant Teacher',
            'school_name': 'Korle-Bu M/A JHS',
            'district': 'Ablekuma South Municipal',
            'region': 'Greater Accra',
            'reference_number': '',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'APPLICATION FOR LEAVE OF ABSENCE\n\n'
                'I respectfully apply for a leave of absence from Monday, 15th September '
                '2025 to Friday, 26th September 2025 (two weeks).\n\n'
                'The purpose of this leave is to attend to a pressing family matter that '
                'requires my presence in the Ashanti Region. I have made arrangements with '
                'my colleague, Mr. Kwame Asante, who has kindly agreed to cover my lessons '
                'during my absence.\n\n'
                'All lesson notes and materials for the period have been prepared and handed '
                'over to ensure minimal disruption to the learning schedule.\n\n'
                'I shall be most grateful if my application is approved.\n\n'
                'Yours faithfully,\n\n\n'
                'Grace Adjei\n'
                'Staff ID: GES/TC/2021/23456\n'
                'Assistant Teacher\n'
                'Korle-Bu M/A JHS'
            ),
        },
        {
            'title': 'Complaint About Unpaid Salary Arrears',
            'category': 'complaint',
            'recipient_name': 'The District Director of Education',
            'recipient_title': 'Ghana Education Service',
            'sender_name': 'Emmanuel Ofori',
            'sender_title': 'Senior Superintendent I',
            'school_name': 'Adenta Community 2 Basic School',
            'district': 'Adentan Municipal',
            'region': 'Greater Accra',
            'reference_number': 'GES/ADN/2025/015',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'COMPLAINT: UNPAID SALARY ARREARS FOR SIX (6) MONTHS\n\n'
                'I write with great concern to bring to your attention the non-payment '
                'of my salary arrears for the period January to June 2025.\n\n'
                'Despite several visits to the District Education Office and verbal '
                'assurances from the Finance Unit, the situation remains unresolved. '
                'This has caused significant financial hardship to me and my family.\n\n'
                'I respectfully urge your office to look into this matter urgently and '
                'ensure the payment of the said arrears.\n\n'
                'Attached herewith are copies of my appointment letter and recent pay '
                'slips for your reference.\n\n'
                'I trust that this matter will receive your immediate and favourable '
                'attention.\n\n'
                'Yours faithfully,\n\n\n'
                'Emmanuel Ofori\n'
                'Staff ID: GES/TC/2018/34567\n'
                'Senior Superintendent I\n'
                'Adenta Community 2 Basic School'
            ),
        },
        {
            'title': 'Letter of Recommendation for Colleague',
            'category': 'recommendation',
            'recipient_name': 'To Whom It May Concern',
            'recipient_title': '',
            'sender_name': 'Dr. Abena Mensah',
            'sender_title': 'Headmistress',
            'school_name': 'Wesley Girls High School',
            'district': 'Cape Coast Metropolitan',
            'region': 'Central',
            'reference_number': '',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'LETTER OF RECOMMENDATION — MR. ISAAC DARKO\n\n'
                'I am pleased to recommend Mr. Isaac Darko, who has served as a Mathematics '
                'teacher at Wesley Girls High School for the past five (5) years.\n\n'
                'During his tenure, Mr. Darko has demonstrated exceptional commitment to '
                'teaching and learning. His innovative teaching methods have contributed '
                'significantly to improved student performance in Mathematics at both the '
                'BECE and WASSCE levels.\n\n'
                'Mr. Darko is diligent, punctual, and highly collaborative. He has also '
                'served as the school\'s Mathematics Club patron and STEM coordinator with '
                'remarkable dedication.\n\n'
                'I have no hesitation in recommending Mr. Darko for any position or '
                'opportunity he may seek. He will be a valuable asset to any institution.\n\n'
                'Yours faithfully,\n\n\n'
                'Dr. Abena Mensah\n'
                'Headmistress\n'
                'Wesley Girls High School\n'
                'Cape Coast'
            ),
        },
        {
            'title': 'Permission to Attend Workshop',
            'category': 'permission',
            'recipient_name': 'The Headteacher',
            'recipient_title': '',
            'sender_name': 'Patience Akoto',
            'sender_title': 'Science Teacher',
            'school_name': 'Osu Salem JHS',
            'district': 'Osu Klottey Sub-Metro',
            'region': 'Greater Accra',
            'reference_number': '',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'REQUEST FOR PERMISSION TO ATTEND STEM WORKSHOP\n\n'
                'I write to seek your permission to attend a three-day STEM Workshop '
                'organised by the National Science and Maths Quiz Foundation, scheduled '
                'to take place from 10th to 12th October 2025 at the University of Ghana, '
                'Legon.\n\n'
                'The workshop will cover practical approaches to teaching Integrated Science '
                'at the JHS level, which aligns directly with my responsibilities. The '
                'knowledge and skills gained will greatly benefit our students.\n\n'
                'I have coordinated with my fellow Science teachers who will ensure '
                'continuity of lessons during my brief absence.\n\n'
                'I would be grateful for your approval.\n\n'
                'Yours faithfully,\n\n\n'
                'Patience Akoto\n'
                'Science Teacher\n'
                'Osu Salem JHS'
            ),
        },
        {
            'title': 'Letter of Appreciation to District Director',
            'category': 'appreciation',
            'recipient_name': 'The District Director of Education',
            'recipient_title': 'Ghana Education Service',
            'sender_name': 'The Teaching Staff',
            'sender_title': 'Achimota Basic School',
            'school_name': 'Achimota Basic School',
            'district': 'Okaikoi North Municipal',
            'region': 'Greater Accra',
            'reference_number': '',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'LETTER OF APPRECIATION\n\n'
                'On behalf of the entire teaching staff of Achimota Basic School, I write '
                'to express our sincere gratitude for the recent provision of teaching and '
                'learning materials to our school.\n\n'
                'The textbooks, mathematical sets, and science equipment have significantly '
                'enhanced our ability to deliver quality education. Our pupils are more '
                'engaged and enthusiastic about learning.\n\n'
                'We appreciate the continuous support of the Directorate and assure you of '
                'our commitment to producing excellent academic results.\n\n'
                'May God bless the Service.\n\n'
                'Yours faithfully,\n\n\n'
                'The Teaching Staff\n'
                'Achimota Basic School\n'
                'Okaikoi North Municipal'
            ),
        },
        {
            'title': 'Application for Promotion',
            'category': 'promotion',
            'recipient_name': 'The Director-General',
            'recipient_title': 'Ghana Education Service, Headquarters, Accra',
            'sender_name': 'Samuel Kwarteng',
            'sender_title': 'Senior Superintendent II',
            'school_name': 'Tamale Senior High School',
            'district': 'Tamale Metropolitan',
            'region': 'Northern',
            'reference_number': 'GES/TAM/2025/042',
            'date_written': today,
            'body': (
                'Dear Sir/Madam,\n\n'
                'APPLICATION FOR PROMOTION FROM SENIOR SUPERINTENDENT II '
                'TO PRINCIPAL SUPERINTENDENT\n\n'
                'I humbly write to apply for promotion from my current rank of '
                'Senior Superintendent II to the rank of Principal Superintendent.\n\n'
                'I was posted to the Ghana Education Service on 1st September 2016 with '
                'Staff ID GES/TC/2016/45678 and have since served at Tamale Senior High '
                'School in the Tamale Metropolitan Directorate. I was promoted to the rank '
                'of Senior Superintendent II on 1st January 2022.\n\n'
                'During my service, I have:\n'
                '1. Consistently achieved excellent results in Mathematics at the WASSCE '
                'level, with pass rates exceeding 85% for the past four (4) years.\n'
                '2. Served as Head of the Mathematics Department since 2020.\n'
                '3. Organised inter-school Mathematics quiz competitions in the '
                'Tamale Metropolitan area.\n'
                '4. Participated in the GES-sponsored STEM capacity-building workshop '
                'for Senior High School teachers in 2023.\n'
                '5. Maintained an unblemished disciplinary record throughout my service.\n\n'
                'I have satisfied the minimum number of years at my current rank as '
                'stipulated in the GES Conditions of Service and believe I am eligible '
                'for consideration.\n\n'
                'Attached herewith for your perusal are:\n'
                '- Copies of my appointment and last promotion letters\n'
                '- Copies of academic and professional certificates\n'
                '- Recent SSNIT contribution statement\n'
                '- Performance appraisal reports for the last three (3) years\n\n'
                'I humbly appeal for your favourable consideration of this application.\n\n'
                'Yours faithfully,\n\n\n'
                'Samuel Kwarteng\n'
                'Staff ID: GES/TC/2016/45678\n'
                'Senior Superintendent II\n'
                'Tamale Senior High School\n'
                'Tamale, Northern Region'
            ),
        },
    ]


# ══════════════════════════════════════════════════════════════════════════════
# ██  Paper Marker                                                           ██
# ══════════════════════════════════════════════════════════════════════════════

@_tool_required
@_require_tool('paper-marker')
def marker_dashboard(request):
    """List all marking sessions for the current user."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    sessions = MarkingSession.objects.filter(profile=profile)

    ctx = {
        'sessions': sessions,
        'session_count': sessions.count(),
        'profile': profile,
        'role': 'teacher',
    }
    return render(request, 'individual/tools/paper-marker/dashboard.html', ctx)


@_tool_required
@_require_tool('paper-marker')
def marker_create(request):
    """Create a new marking session (answer key setup)."""
    _ensure_public_schema()
    profile = request.user.individual_profile

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subject = request.POST.get('subject', '').strip()
        class_name = request.POST.get('class_name', '').strip()
        total_q = int(request.POST.get('total_questions', 40))
        options = int(request.POST.get('options_per_question', 4))
        answer_key_raw = request.POST.get('answer_key', '').strip()

        if not title:
            messages.error(request, 'Please provide a title.')
            return redirect('individual:marker_create')
        if total_q < 1 or total_q > 200:
            messages.error(request, 'Total questions must be between 1 and 200.')
            return redirect('individual:marker_create')

        # Parse answer key — comma-separated or space-separated
        if answer_key_raw:
            if ',' in answer_key_raw:
                key_list = [a.strip().upper() for a in answer_key_raw.split(',') if a.strip()]
            else:
                key_list = [a.strip().upper() for a in answer_key_raw.split() if a.strip()]
        else:
            key_list = []

        session = MarkingSession.objects.create(
            profile=profile,
            title=title,
            subject=subject,
            class_name=class_name,
            total_questions=total_q,
            options_per_question=options,
            answer_key=key_list,
        )
        messages.success(request, f'Session "{title}" created.')
        return redirect('individual:marker_session', pk=session.pk)

    return render(request, 'individual/tools/paper-marker/create.html', {
        'profile': profile,
        'role': 'teacher',
    })


@_tool_required
@_require_tool('paper-marker')
def marker_session(request, pk):
    """View / manage a marking session — enter student responses."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    session = get_object_or_404(MarkingSession, pk=pk, profile=profile)
    marks = session.marks.all()

    # Per-question stats
    question_stats = []
    if marks.exists() and session.answer_key:
        num_q = len(session.answer_key)
        for i in range(num_q):
            correct_count = 0
            for m in marks:
                if i < len(m.responses) and str(m.responses[i]).strip().upper() == str(session.answer_key[i]).strip().upper():
                    correct_count += 1
            pct = round((correct_count / marks.count()) * 100, 1) if marks.count() else 0
            question_stats.append({
                'number': i + 1,
                'correct_answer': session.answer_key[i],
                'correct_count': correct_count,
                'total': marks.count(),
                'percentage': pct,
            })

    # Class stats
    if marks.exists():
        scores = [m.percentage for m in marks]
        class_stats = {
            'average': round(sum(scores) / len(scores), 1),
            'highest': round(max(scores), 1),
            'lowest': round(min(scores), 1),
            'pass_count': sum(1 for s in scores if s >= 50),
            'fail_count': sum(1 for s in scores if s < 50),
            'total_students': len(scores),
        }
    else:
        class_stats = None

    # Option letters for templates
    option_letters = [chr(65 + i) for i in range(session.options_per_question)]

    ctx = {
        'session': session,
        'marks': marks,
        'question_stats': question_stats,
        'class_stats': class_stats,
        'option_letters': option_letters,
        'answer_key_json': json.dumps(session.answer_key),
        'profile': profile,
        'role': 'teacher',
    }
    return render(request, 'individual/tools/paper-marker/session.html', ctx)


@_tool_required
@_require_tool('paper-marker')
def marker_edit(request, pk):
    """Edit marking session details (answer key, title, etc.)."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    session = get_object_or_404(MarkingSession, pk=pk, profile=profile)

    if request.method == 'POST':
        session.title = request.POST.get('title', session.title).strip()
        session.subject = request.POST.get('subject', '').strip()
        session.class_name = request.POST.get('class_name', '').strip()
        session.total_questions = int(request.POST.get('total_questions', session.total_questions))
        session.options_per_question = int(request.POST.get('options_per_question', session.options_per_question))

        answer_key_raw = request.POST.get('answer_key', '').strip()
        if answer_key_raw:
            if ',' in answer_key_raw:
                session.answer_key = [a.strip().upper() for a in answer_key_raw.split(',') if a.strip()]
            else:
                session.answer_key = [a.strip().upper() for a in answer_key_raw.split() if a.strip()]
        session.save()
        messages.success(request, 'Session updated.')
        return redirect('individual:marker_session', pk=session.pk)

    return render(request, 'individual/tools/paper-marker/edit.html', {
        'session': session,
        'profile': profile,
        'role': 'teacher',
    })


@_tool_required
@_require_tool('paper-marker')
@require_POST
def marker_delete(request, pk):
    """Delete a marking session."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    session = get_object_or_404(MarkingSession, pk=pk, profile=profile)
    session.delete()
    messages.success(request, 'Session deleted.')
    return redirect('individual:marker_dashboard')


@_tool_required
@_require_tool('paper-marker')
def marker_api(request):
    """AJAX API for Paper Marker operations."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    _ensure_public_schema()
    profile = request.user.individual_profile

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = data.get('action', '')

    # ── Add Student Mark ─────────────────────────────────────────────────
    if action == 'add_mark':
        session_id = data.get('session_id')
        student_name = data.get('student_name', '').strip()
        student_index = data.get('student_index', '').strip()
        responses = data.get('responses', [])

        if not session_id or not student_name:
            return JsonResponse({'error': 'Session ID and student name required.'}, status=400)

        session = get_object_or_404(MarkingSession, pk=session_id, profile=profile)

        # Clean responses
        clean_responses = [str(r).strip().upper() if r else '' for r in responses]

        mark = StudentMark(
            session=session,
            student_name=student_name,
            student_index=student_index,
            responses=clean_responses,
        )
        mark.grade_responses()
        mark.save()

        return JsonResponse({
            'ok': True,
            'mark': {
                'id': mark.pk,
                'student_name': mark.student_name,
                'student_index': mark.student_index,
                'score': mark.score,
                'total': mark.total,
                'percentage': mark.percentage,
            }
        })

    # ── Delete Student Mark ──────────────────────────────────────────────
    if action == 'delete_mark':
        mark_id = data.get('mark_id')
        if not mark_id:
            return JsonResponse({'error': 'Mark ID required.'}, status=400)

        mark = get_object_or_404(StudentMark, pk=mark_id, session__profile=profile)
        mark.delete()
        return JsonResponse({'ok': True})

    # ── Update Answer Key ────────────────────────────────────────────────
    if action == 'update_key':
        session_id = data.get('session_id')
        answer_key = data.get('answer_key', [])

        if not session_id:
            return JsonResponse({'error': 'Session ID required.'}, status=400)

        session = get_object_or_404(MarkingSession, pk=session_id, profile=profile)
        session.answer_key = [str(a).strip().upper() for a in answer_key]
        session.save()

        # Re-grade all students
        for mark in session.marks.all():
            mark.grade_responses()
            mark.save()

        return JsonResponse({'ok': True, 'regraded': session.marks.count()})

    # ── Bulk Add Marks ───────────────────────────────────────────────────
    if action == 'bulk_add':
        session_id = data.get('session_id')
        students = data.get('students', [])

        if not session_id:
            return JsonResponse({'error': 'Session ID required.'}, status=400)

        session = get_object_or_404(MarkingSession, pk=session_id, profile=profile)
        created = []
        for s in students:
            name = s.get('student_name', '').strip()
            if not name:
                continue
            index = s.get('student_index', '').strip()
            responses = [str(r).strip().upper() if r else '' for r in s.get('responses', [])]
            mark = StudentMark(
                session=session,
                student_name=name,
                student_index=index,
                responses=responses,
            )
            mark.grade_responses()
            mark.save()
            created.append({
                'id': mark.pk,
                'student_name': mark.student_name,
                'score': mark.score,
                'total': mark.total,
                'percentage': mark.percentage,
            })

        return JsonResponse({'ok': True, 'count': len(created), 'marks': created})

    # ── Scan Answer Sheet (AI Vision) ─────────────────────────────────
    if action == 'scan_sheet':
        session_id = data.get('session_id')
        image_data = data.get('image', '')  # data:image/...;base64,... URI

        if not session_id or not image_data:
            return JsonResponse({'error': 'Session ID and image are required.'}, status=400)

        session = get_object_or_404(MarkingSession, pk=session_id, profile=profile)
        if not session.answer_key:
            return JsonResponse({'error': 'Set an answer key before scanning.'}, status=400)

        num_q = len(session.answer_key)
        opt_count = session.options_per_question
        opt_letters = ', '.join(chr(65 + i) for i in range(opt_count))

        system_msg = (
            'You are a specialist at reading scanned/photographed multiple-choice '
            'answer sheets (also called OMR or bubble sheets). You have perfect '
            'accuracy at distinguishing filled/shaded bubbles from empty ones.'
        )

        prompt = (
            f'Carefully analyse this photograph of an MCQ answer sheet.\n\n'
            f'**Sheet layout:** {num_q} questions, each with options {opt_letters}.\n'
            'The sheet may have questions in a SINGLE column (1-to-N top-to-bottom) '
            'or split into TWO columns (e.g. 1-15 on the left, 16-30 on the right). '
            'Read in numerical question order regardless of column layout.\n\n'
            '**How to identify a selected answer:**\n'
            '- A SHADED bubble is filled, darkened, or coloured in with pencil/pen. '
            'It looks noticeably darker than the empty bubbles around it.\n'
            '- An EMPTY bubble is a hollow circle/oval outline with a light or '
            'white interior.\n'
            '- If a question has NO bubble shaded, return "" for that question.\n'
            '- If a question has multiple bubbles shaded, return the darkest one.\n\n'
            '**Also extract:**\n'
            '- Student name or candidate name (handwritten text near "Name", '
            '"Candidate", "Student" label at the top of the sheet).\n'
            '- Register number / index number / student ID if visible.\n\n'
            '**CRITICAL RULES:**\n'
            '- Go through EVERY question from 1 to '
            f'{num_q} in order. Do not skip any.\n'
            f'- Your "answers" array MUST contain exactly {num_q} entries.\n'
            '- Each entry must be one of: '
            + ', '.join(f'"{chr(65 + i)}"' for i in range(opt_count))
            + ', or "" if unanswered.\n'
            '- Double-check your work: re-examine any answer you are uncertain '
            'about by looking at which bubble in that row is darkest.\n\n'
            'Return ONLY valid JSON — no markdown fences, no explanation:\n'
            '{\n'
            '  "student_name": "<name or register number>",\n'
            '  "student_index": "<index/ID if visible, else empty string>",\n'
            f'  "answers": [/* exactly {num_q} entries */]\n'
            '}'
        )

        try:
            from academics.ai_tutor import _post_chat_completion, _get_openai_api_key

            payload = {
                'model': 'gpt-4o',
                'messages': [
                    {'role': 'system', 'content': system_msg},
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': image_data,
                                    'detail': 'high',
                                },
                            },
                        ],
                    },
                ],
                'temperature': 0.0,
                'max_tokens': 3000,
            }

            resp = _post_chat_completion(payload, _get_openai_api_key())

            if 'error' in resp:
                return JsonResponse({'error': f"AI error: {resp['error']}"}, status=500)

            choices = resp.get('choices', [])
            if not choices:
                return JsonResponse({'error': 'AI returned no response.'}, status=500)

            raw = choices[0].get('message', {}).get('content', '').strip()
            # Strip markdown fences
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            raw = raw.strip()

            extracted = json.loads(raw)
            answers = [str(a).strip().upper() for a in extracted.get('answers', [])]
            student_name = str(extracted.get('student_name', '')).strip()
            student_index = str(extracted.get('student_index', '')).strip()

            return JsonResponse({
                'ok': True,
                'extracted': {
                    'student_name': student_name,
                    'student_index': student_index,
                    'answers': answers,
                },
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'AI returned invalid data. Try a clearer photo.'}, status=500)
        except Exception as exc:
            logger.warning('Scan sheet AI error: %s', exc)
            return JsonResponse({'error': 'Failed to process image. Please try again.'}, status=500)

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


# ── Report Card Writer ───────────────────────────────────────────────────────

@_tool_required
@_require_tool('report-card')
def report_card_dashboard(request):
    """List all report card sets with stats."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    sets = ReportCardSet.objects.filter(profile=profile).annotate(
        entry_count=Count('entries'),
        comment_count=Count('entries', filter=Q(entries__class_teacher_comment__gt='')),
    )

    total = sets.count()
    total_entries = ReportCardEntry.objects.filter(card_set__profile=profile).count()
    ai_count = ReportCardEntry.objects.filter(card_set__profile=profile, ai_generated=True).count()

    return render(request, 'individual/tools/report-card/dashboard.html', {
        'sets': sets,
        'total_sets': total,
        'total_entries': total_entries,
        'ai_count': ai_count,
    })


@_tool_required
@_require_tool('report-card')
def report_card_create(request):
    """Create a new report card set."""
    _ensure_public_schema()
    profile = request.user.individual_profile

    if request.method == 'POST':
        title = request.POST.get('title', '').strip() or 'Untitled Report Cards'
        card_set = ReportCardSet.objects.create(
            profile=profile,
            title=title,
            class_name=request.POST.get('class_name', '').strip(),
            term=request.POST.get('term', 'first'),
            academic_year=request.POST.get('academic_year', '2025/2026').strip(),
            school_name=request.POST.get('school_name', '').strip(),
            next_term_begins=request.POST.get('next_term_begins') or None,
        )
        messages.success(request, f'Report card set "{card_set.title}" created.')
        return redirect('individual:report_card_edit', pk=card_set.pk)

    return render(request, 'individual/tools/report-card/editor.html', {
        'card_set': None,
        'mode': 'create',
        'terms': ReportCardSet.TERM_CHOICES,
    })


@_tool_required
@_require_tool('report-card')
def report_card_edit(request, pk):
    """Edit a report card set and manage entries."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    card_set = get_object_or_404(ReportCardSet, pk=pk, profile=profile)

    if request.method == 'POST':
        card_set.title = request.POST.get('title', card_set.title).strip() or card_set.title
        card_set.class_name = request.POST.get('class_name', card_set.class_name).strip()
        card_set.term = request.POST.get('term', card_set.term)
        card_set.academic_year = request.POST.get('academic_year', card_set.academic_year).strip()
        card_set.school_name = request.POST.get('school_name', card_set.school_name).strip()
        card_set.next_term_begins = request.POST.get('next_term_begins') or None
        card_set.save()
        messages.success(request, 'Report card set updated.')
        return redirect('individual:report_card_edit', pk=card_set.pk)

    entries = card_set.entries.all()
    return render(request, 'individual/tools/report-card/editor.html', {
        'card_set': card_set,
        'entries': entries,
        'mode': 'edit',
        'terms': ReportCardSet.TERM_CHOICES,
        'rating_choices': ReportCardEntry.RATING_CHOICES,
    })


@_tool_required
@_require_tool('report-card')
@require_POST
def report_card_delete(request, pk):
    """Delete a report card set and all its entries."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    card_set = get_object_or_404(ReportCardSet, pk=pk, profile=profile)
    title = card_set.title
    card_set.delete()
    messages.success(request, f'Report card set "{title}" deleted.')
    return redirect('individual:report_card_dashboard')


@_tool_required
@_require_tool('report-card')
def report_card_entry_edit(request, pk, entry_pk):
    """Edit an individual student report card entry."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    card_set = get_object_or_404(ReportCardSet, pk=pk, profile=profile)
    entry = get_object_or_404(ReportCardEntry, pk=entry_pk, card_set=card_set)

    if request.method == 'POST':
        entry.student_name = request.POST.get('student_name', entry.student_name).strip()
        entry.conduct = request.POST.get('conduct', entry.conduct)
        entry.attitude = request.POST.get('attitude', entry.attitude)
        entry.interest = request.POST.get('interest', entry.interest)
        entry.attendance = request.POST.get('attendance', entry.attendance).strip()
        entry.class_teacher_comment = request.POST.get('class_teacher_comment', entry.class_teacher_comment).strip()
        entry.head_teacher_comment = request.POST.get('head_teacher_comment', entry.head_teacher_comment).strip()
        entry.position = request.POST.get('position') or None
        entry.total_students = request.POST.get('total_students') or None
        entry.overall_score = request.POST.get('overall_score') or None
        entry.overall_grade = request.POST.get('overall_grade', entry.overall_grade).strip()

        promoted = request.POST.get('promoted', '')
        if promoted == 'yes':
            entry.promoted = True
        elif promoted == 'no':
            entry.promoted = False
        else:
            entry.promoted = None
        entry.next_class = request.POST.get('next_class', entry.next_class).strip()

        # Parse subjects JSON from hidden field
        subjects_json = request.POST.get('subjects_json', '')
        if subjects_json:
            try:
                entry.subjects = json.loads(subjects_json)
            except (json.JSONDecodeError, ValueError):
                pass

        entry.save()
        messages.success(request, f'Report card for {entry.student_name} updated.')
        return redirect('individual:report_card_edit', pk=card_set.pk)

    return render(request, 'individual/tools/report-card/entry_edit.html', {
        'card_set': card_set,
        'entry': entry,
        'rating_choices': ReportCardEntry.RATING_CHOICES,
    })


@_tool_required
@_require_tool('report-card')
def report_card_print(request, pk, entry_pk):
    """Print-ready view for a single student report card."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    card_set = get_object_or_404(ReportCardSet, pk=pk, profile=profile)
    entry = get_object_or_404(ReportCardEntry, pk=entry_pk, card_set=card_set)
    return render(request, 'individual/tools/report-card/print.html', {
        'card_set': card_set,
        'entry': entry,
    })


@_tool_required
@_require_tool('report-card')
def report_card_print_all(request, pk):
    """Print-ready view for all students in a set (page-break between each)."""
    _ensure_public_schema()
    profile = request.user.individual_profile
    card_set = get_object_or_404(ReportCardSet, pk=pk, profile=profile)
    entries = card_set.entries.all()
    return render(request, 'individual/tools/report-card/print.html', {
        'card_set': card_set,
        'entries': entries,
        'print_all': True,
    })


@_tool_required
@_require_tool('report-card')
def report_card_api(request):
    """AJAX API for report card operations: add/delete entries, AI comments."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    _ensure_public_schema()
    profile = request.user.individual_profile

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = data.get('action', '')

    # ── Add Entry ────────────────────────────────────────────────────────
    if action == 'add_entry':
        set_id = data.get('set_id')
        student_name = data.get('student_name', '').strip()
        if not set_id or not student_name:
            return JsonResponse({'error': 'Set ID and student name required.'}, status=400)

        card_set = get_object_or_404(ReportCardSet, pk=set_id, profile=profile)
        entry = ReportCardEntry.objects.create(
            card_set=card_set,
            student_name=student_name,
        )
        return JsonResponse({
            'ok': True,
            'entry': {
                'id': entry.pk,
                'student_name': entry.student_name,
            },
        })

    # ── Bulk Add Entries ─────────────────────────────────────────────────
    if action == 'bulk_add':
        set_id = data.get('set_id')
        names = data.get('names', [])
        if not set_id:
            return JsonResponse({'error': 'Set ID required.'}, status=400)

        card_set = get_object_or_404(ReportCardSet, pk=set_id, profile=profile)
        created = []
        for name in names:
            name = str(name).strip()
            if not name:
                continue
            entry = ReportCardEntry.objects.create(
                card_set=card_set,
                student_name=name,
            )
            created.append({'id': entry.pk, 'student_name': entry.student_name})

        return JsonResponse({'ok': True, 'count': len(created), 'entries': created})

    # ── Delete Entry ─────────────────────────────────────────────────────
    if action == 'delete_entry':
        entry_id = data.get('entry_id')
        if not entry_id:
            return JsonResponse({'error': 'Entry ID required.'}, status=400)

        entry = get_object_or_404(ReportCardEntry, pk=entry_id, card_set__profile=profile)
        entry.delete()
        return JsonResponse({'ok': True})

    # ── AI Generate Comment (single student) ─────────────────────────────
    if action == 'generate_comment':
        entry_id = data.get('entry_id')
        if not entry_id:
            return JsonResponse({'error': 'Entry ID required.'}, status=400)

        entry = get_object_or_404(ReportCardEntry, pk=entry_id, card_set__profile=profile)
        card_set = entry.card_set

        comment = _generate_report_comment(entry, card_set)
        if comment is None:
            return JsonResponse({'error': 'AI generation failed. Please try again.'}, status=500)

        entry.class_teacher_comment = comment
        entry.ai_generated = True
        entry.save()
        return JsonResponse({'ok': True, 'comment': comment})

    # ── AI Bulk Generate Comments ────────────────────────────────────────
    if action == 'bulk_generate':
        set_id = data.get('set_id')
        overwrite = data.get('overwrite', False)
        if not set_id:
            return JsonResponse({'error': 'Set ID required.'}, status=400)

        card_set = get_object_or_404(ReportCardSet, pk=set_id, profile=profile)
        entries = card_set.entries.all()
        if not overwrite:
            entries = entries.filter(class_teacher_comment='')

        generated = 0
        for entry in entries:
            comment = _generate_report_comment(entry, card_set)
            if comment:
                entry.class_teacher_comment = comment
                entry.ai_generated = True
                entry.save()
                generated += 1

        return JsonResponse({
            'ok': True,
            'generated': generated,
            'message': f'Generated comments for {generated} student(s).',
        })

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


def _generate_report_comment(entry, card_set):
    """Generate a personalised report card comment using AI."""
    subjects_text = ''
    if entry.subjects:
        lines = []
        for s in entry.subjects:
            lines.append(f"  {s.get('subject', '?')}: {s.get('total', '?')}/100 ({s.get('grade', '?')})")
        subjects_text = '\n'.join(lines)

    conduct_label = dict(ReportCardEntry.RATING_CHOICES).get(entry.conduct, entry.conduct)
    attitude_label = dict(ReportCardEntry.RATING_CHOICES).get(entry.attitude, entry.attitude)
    interest_label = dict(ReportCardEntry.RATING_CHOICES).get(entry.interest, entry.interest)

    prompt = f"""You are a class teacher writing end-of-term report card comments for a school in Ghana.
Write a brief, personalised comment (2-3 sentences) for this student.

Student: {entry.student_name}
Class: {card_set.class_name}
Term: {dict(ReportCardSet.TERM_CHOICES).get(card_set.term, card_set.term)}
Academic Year: {card_set.academic_year}
{f'Overall Position: {entry.position} out of {entry.total_students}' if entry.position else ''}
{f'Overall Grade: {entry.overall_grade}' if entry.overall_grade else ''}
Conduct: {conduct_label}
Attitude to Work: {attitude_label}
Interest: {interest_label}
{f'Attendance: {entry.attendance}' if entry.attendance else ''}
{f'Subjects:\\n{subjects_text}' if subjects_text else ''}

Guidelines:
- Write in formal British English (Ghana standard)
- Be encouraging but honest about areas for improvement
- Reference specific subjects if data is provided
- Mention conduct/attitude where relevant
- Keep it warm and professional — 2-3 sentences max
- Do NOT include the student name at the start
- Do NOT add quotes or formatting

Return ONLY the comment text."""

    try:
        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': 'You are a Ghanaian class teacher writing report card comments.'},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.8,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error('Report card AI comment failed: %s', e)
        return None
