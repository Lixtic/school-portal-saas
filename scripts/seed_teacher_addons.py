"""
Seed the TeacherAddOn catalog and CreditPack catalog.

Run:  python scripts/seed_teacher_addons.py [schema_name]

Without a schema argument it seeds ALL tenant schemas automatically.
"""

import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection
from tenants.models import School
from teachers.models import TeacherAddOn, CreditPack

ADDONS = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER: FREE  —  Platform hooks, zero marginal cost, drive adoption
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'Task Board',
        'slug': 'task-board',
        'tagline': 'Personal kanban for teaching tasks',
        'description': 'A simple drag-and-drop board to organise your teaching to-dos — lesson prep, marking, meetings, and more.',
        'category': 'productivity',
        'icon': 'bi bi-kanban',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'Kanban columns: To Do / In Progress / Done',
            'Color-coded priority labels',
            'Due date reminders',
            'Weekly digest email',
        ],
    },
    {
        'name': 'CPD Tracker',
        'slug': 'cpd-tracker',
        'tagline': 'Log your professional development hours',
        'description': 'Track workshops, courses, and self-study hours. Generate CPD certificates and progress reports for appraisals.',
        'category': 'professional',
        'icon': 'bi bi-award',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'Log workshops & training hours',
            'Auto-generated CPD summary',
            'Certificate templates',
            'Share with head teacher',
        ],
    },
    {
        'name': 'Random Picker Wheel',
        'slug': 'random-picker',
        'tagline': 'Fun student selector for class activities',
        'description': 'Spin a colourful wheel to pick students randomly for questions, group leaders, or classroom roles. Keeps things fair and engaging.',
        'category': 'classroom',
        'icon': 'bi bi-bullseye',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'Auto-load class roster',
            'Spin-to-pick animation',
            'Group randomiser mode',
            'History of selections',
        ],
    },
    {
        'name': 'Countdown & Timer',
        'slug': 'countdown-timer',
        'tagline': 'Visible activity timer for your classroom',
        'description': 'Project a large countdown timer during group work, tests, or transitions. Customisable sounds and colours.',
        'category': 'classroom',
        'icon': 'bi bi-stopwatch',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'Full-screen projector mode',
            'Custom time presets',
            'Sound alerts on finish',
            'Traffic light colour modes',
        ],
    },
    {
        'name': 'Noise Meter',
        'slug': 'noise-meter',
        'tagline': 'Visual classroom noise level gauge',
        'description': 'Use your device microphone to display a real-time noise meter — an engaging way to manage classroom volume.',
        'category': 'classroom',
        'icon': 'bi bi-soundwave',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'Real-time noise visualisation',
            'Adjustable sensitivity',
            'Full-screen display',
            'Class reward thresholds',
        ],
    },
    {
        'name': 'Attendance Tracker',
        'slug': 'attendance-tracker',
        'tagline': 'Quick daily attendance with heatmap insights',
        'description': 'Mark attendance for any class in seconds with one-tap P/A/L/E buttons. View 30-day heatmaps and per-student term rates at a glance.',
        'category': 'classroom',
        'icon': 'bi bi-calendar-check',
        'badge_label': 'FREE',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'features': [
            'One-tap present/absent/late/excused buttons',
            'Mark All shortcut for fast entry',
            '30-day colour-coded heatmap calendar',
            'Per-student term attendance rates',
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # TIER: ESSENTIALS (GHS 3–8)  —  Non-AI utilities, 7-day trial
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'Rubric Designer',
        'slug': 'rubric-designer',
        'tagline': 'Build marking rubrics fast',
        'description': 'Create detailed rubrics for projects, presentations, and essays. Share with colleagues or reuse across terms.',
        'category': 'assessment',
        'icon': 'bi bi-list-check',
        'badge_label': '',
        'price': 3.00,
        'trial_days': 7,
        'features': [
            'Drag-and-drop criteria builder',
            'Point scale or descriptor mode',
            'Copy rubrics across subjects',
            'Student self-assessment view',
        ],
    },
    {
        'name': 'Classroom Observation Notes',
        'slug': 'observation-notes',
        'tagline': 'Structured peer observation templates',
        'description': 'Use guided templates for classroom observations — great for mentoring, NQT support, and self-reflection.',
        'category': 'professional',
        'icon': 'bi bi-binoculars',
        'badge_label': '',
        'price': 5.00,
        'trial_days': 7,
        'features': [
            'Pre-built observation forms',
            'Strengths & growth areas',
            'Action plan templates',
            'Private or shared notes',
        ],
    },
    {
        'name': 'Behavior & SEL Tracker',
        'slug': 'behavior-sel-tracker',
        'tagline': 'See the student behind the grade',
        'description': 'Quick-log positive and negative behavior events. Track SEL check-ins. Spot patterns early with automatic alerts. Generate behavior reports for parents.',
        'category': 'classroom',
        'icon': 'bi bi-heart-pulse',
        'badge_label': '',
        'price': 8.00,
        'trial_days': 7,
        'features': [
            'Positive & negative behavior logging',
            'SEL check-in prompts',
            'Pattern detection & alerts',
            'Parent-shareable behavior reports',
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # TIER: AI TOOLS (Free to activate — uses credit tokens)
    # Teachers activate for free, each generation costs credits
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'Exercise Maker',
        'slug': 'exercise-maker',
        'tagline': 'Auto-create quizzes & worksheets',
        'description': 'Generate multiple-choice, fill-in-the-blank, and short-answer exercises aligned to your curriculum indicators. Uses 1 credit per generation.',
        'category': 'ai_tools',
        'icon': 'bi bi-puzzle',
        'badge_label': 'AI',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,  # flag: this is an AI-credit add-on
        'features': [
            'Multiple question formats',
            'Aligned to GES indicators',
            'Difficulty auto-scaling',
            '1 credit per generation',
        ],
    },
    {
        'name': 'Study Guide Builder',
        'slug': 'study-guide-builder',
        'tagline': 'Student revision packs on demand',
        'description': 'Create concise, student-friendly study guides from your lesson plans — perfect for exam prep. Uses 2 credits per guide.',
        'category': 'ai_tools',
        'icon': 'bi bi-book-half',
        'badge_label': 'AI',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Key concepts summary',
            'Practice questions per topic',
            'Visual mnemonics',
            '2 credits per guide',
        ],
    },
    {
        'name': 'Quick Report Writer',
        'slug': 'quick-report-writer',
        'tagline': 'Generate student reports in minutes',
        'description': 'Craft personalised end-of-term reports using grade data plus AI-suggested remarks tailored to each student\'s performance. Uses 1 credit per report.',
        'category': 'productivity',
        'icon': 'bi bi-file-earmark-richtext',
        'badge_label': 'AI',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Personalised AI-written remarks',
            'Pull grades & attendance automatically',
            'Bulk export as PDF',
            '1 credit per report',
        ],
    },
    {
        'name': 'Grade Insight Dashboard',
        'slug': 'grade-insight-dashboard',
        'tagline': 'Deeper analytics on student performance',
        'description': 'Visualise grade trends, class averages, and per-student progress over multiple terms with interactive charts. Uses 1 credit per AI insight.',
        'category': 'assessment',
        'icon': 'bi bi-graph-up-arrow',
        'badge_label': 'POPULAR',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Term-over-term trend charts',
            'Class & subject breakdowns',
            'At-risk student alerts',
            '1 credit per AI insight',
        ],
    },
    {
        'name': 'Live Quiz Engine',
        'slug': 'live-quiz-engine',
        'tagline': 'Kahoot-style quizzes inside your portal',
        'description': 'Create quick quizzes, share a join code, and watch students answer in real time. Results flow into your gradebook. No separate app needed.',
        'category': 'classroom',
        'icon': 'bi bi-lightning-charge',
        'badge_label': 'HOT',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Real-time student responses',
            'Join via code — any device',
            'Leaderboard & results breakdown',
            '1 credit per AI-generated quiz',
        ],
    },
    {
        'name': 'Smart Planner Pro',
        'slug': 'smart-planner-pro',
        'tagline': 'AI-powered weekly planning assistant',
        'description': 'Automatically draft weekly lesson outlines from your scheme of work and syllabus. Saves hours of manual planning. Uses 1 credit per lesson plan.',
        'category': 'productivity',
        'icon': 'bi bi-calendar2-week',
        'badge_label': 'POPULAR',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Auto-generate weekly plans from scheme',
            'Drag-and-drop schedule builder',
            'Export to PDF & print-ready formats',
            '1 credit per lesson plan',
        ],
    },
    {
        'name': 'SchoolPadi Slide Generator',
        'slug': 'aura-slide-generator',
        'tagline': 'Turn any topic into a slide deck',
        'description': 'Type a topic and get a polished presentation with key points, diagrams, and discussion prompts — ready to present. Uses 3 credits per deck.',
        'category': 'ai_tools',
        'icon': 'bi bi-easel2',
        'badge_label': 'POPULAR',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'AI-generated slide content',
            'Auto-add visuals & diagrams',
            'Export to PPTX',
            '3 credits per slide deck',
        ],
    },
    {
        'name': 'Report Card AI Writer',
        'slug': 'report-card-writer',
        'tagline': 'End-of-term reports in minutes, not days',
        'description': 'AI reads each student\'s grades, attendance, and behavior data then generates personalised, professional report card comments. Uses 2 credits per class.',
        'category': 'ai_tools',
        'icon': 'bi bi-card-text',
        'badge_label': 'HOT',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'AI-personalised comment per student',
            'Pulls grades & attendance automatically',
            'Bulk generate for entire class',
            '2 credits per class report',
        ],
    },
    {
        'name': 'Exam & Question Bank Pro',
        'slug': 'exam-question-bank',
        'tagline': 'Build exams smarter, not harder',
        'description': 'Create a searchable bank of questions tagged by subject, topic, and difficulty. AI generates new questions on demand. Uses 2 credits per question set.',
        'category': 'assessment',
        'icon': 'bi bi-database-check',
        'badge_label': 'HOT',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Searchable question bank',
            'AI-generated questions on demand',
            'Multiple formats: MCQ, fill-in, essay',
            '2 credits per question set',
        ],
    },
    {
        'name': 'Differentiated Lesson AI',
        'slug': 'differentiated-lesson-ai',
        'tagline': 'One lesson, three ability levels',
        'description': 'Paste or pick a lesson plan and AI generates three versions: foundational (struggling), grade-level (on-track), and extension (advanced). Uses 2 credits per differentiation.',
        'category': 'ai_tools',
        'icon': 'bi bi-diagram-3',
        'badge_label': 'AI',
        'price': 0,
        'is_free': True,
        'trial_days': 0,
        'quota_boost': 1,
        'features': [
            'Three differentiated tiers per lesson',
            'Scaffolded activities & instructions',
            'Works with existing lesson plans',
            '2 credits per differentiation',
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # TIER: CONTENT PACKS (GHS 12–18)  —  Non-AI curated content
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'STEM Activity Pack',
        'slug': 'stem-activity-pack',
        'tagline': '50+ hands-on science & math activities',
        'description': 'Ready-to-use activities for JHS science, math, and ICT — with materials lists, step-by-step guides, and worksheets.',
        'category': 'content',
        'icon': 'bi bi-rocket-takeoff',
        'badge_label': '',
        'price': 18.00,
        'trial_days': 7,
        'features': [
            '50+ curated activities',
            'Materials & safety checklists',
            'Student worksheets included',
            'Mapped to GES curriculum',
        ],
    },
    {
        'name': 'Creative Arts Resource Kit',
        'slug': 'creative-arts-kit',
        'tagline': 'Music, drama & visual arts lesson aids',
        'description': 'Lesson starters, project briefs, and assessment criteria for creative arts across all JHS levels.',
        'category': 'content',
        'icon': 'bi bi-palette',
        'badge_label': '',
        'price': 15.00,
        'trial_days': 7,
        'features': [
            'Project-based lesson starters',
            'Assessment rubrics included',
            'Performance recording tips',
            'Cross-curricular links',
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════
# CREDIT PACKS  —  Teachers buy these to fuel AI tool usage
# ═══════════════════════════════════════════════════════════════════════
CREDIT_PACKS = [
    {
        'name': 'Starter',
        'slug': 'starter-20',
        'credits': 20,
        'price': 2.00,
        'badge_label': '',
        'icon': 'bi bi-lightning-charge',
        'position': 1,
    },
    {
        'name': 'Basic',
        'slug': 'basic-50',
        'credits': 50,
        'price': 4.00,
        'badge_label': '',
        'icon': 'bi bi-lightning-charge-fill',
        'position': 2,
    },
    {
        'name': 'Standard',
        'slug': 'standard-120',
        'credits': 120,
        'price': 8.00,
        'badge_label': 'POPULAR',
        'icon': 'bi bi-stars',
        'position': 3,
    },
    {
        'name': 'Power',
        'slug': 'power-300',
        'credits': 300,
        'price': 15.00,
        'badge_label': 'BEST VALUE',
        'icon': 'bi bi-rocket-takeoff-fill',
        'position': 4,
    },
]


def seed():
    created = 0
    updated = 0
    for orig in ADDONS:
        data = dict(orig)  # copy so we don't mutate the original
        features = data.pop('features', [])
        is_free = data.pop('is_free', False)
        quota_boost = data.pop('quota_boost', 0)
        obj, was_created = TeacherAddOn.objects.update_or_create(
            slug=data['slug'],
            defaults={**data, 'features': features, 'is_free': is_free, 'quota_boost': quota_boost},
        )
        if was_created:
            created += 1
        else:
            updated += 1
    print(f"TeacherAddOn catalog: {created} created, {updated} updated (total {len(ADDONS)})")

    # Seed credit packs
    cp_created = 0
    cp_updated = 0
    for pack_data in CREDIT_PACKS:
        obj, was_created = CreditPack.objects.update_or_create(
            slug=pack_data['slug'],
            defaults=pack_data,
        )
        if was_created:
            cp_created += 1
        else:
            cp_updated += 1
    print(f"CreditPack catalog: {cp_created} created, {cp_updated} updated (total {len(CREDIT_PACKS)})")

if __name__ == '__main__':
    schema_arg = sys.argv[1] if len(sys.argv) > 1 else None
    tenants = School.objects.exclude(schema_name='public')
    if schema_arg:
        tenants = tenants.filter(schema_name=schema_arg)
    if not tenants.exists():
        print(f"No tenant found{' for ' + schema_arg if schema_arg else ''}.")
        sys.exit(1)
    for tenant in tenants:
        connection.set_tenant(tenant)
        print(f"\n-- {tenant.schema_name} --")
        try:
            seed()
        except Exception as e:
            print(f"  SKIPPED ({e.__class__.__name__}: {e})")
else:
    seed()
