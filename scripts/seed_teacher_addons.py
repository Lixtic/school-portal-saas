"""
Seed the TeacherAddOn catalog with curated tools for teachers.

Run:  python scripts/seed_teacher_addons.py [schema_name]

Without a schema argument it seeds ALL tenant schemas automatically.
"""

import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection
from tenants.models import School
from teachers.models import TeacherAddOn

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
    # TIER: PRO (GHS 12–20)  —  Moderate AI or content, 7-day trial
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'Exercise Maker',
        'slug': 'exercise-maker',
        'tagline': 'Auto-create quizzes & worksheets',
        'description': 'Generate multiple-choice, fill-in-the-blank, and short-answer exercises aligned to your curriculum indicators.',
        'category': 'ai_tools',
        'icon': 'bi bi-puzzle',
        'badge_label': '',
        'price': 12.00,
        'trial_days': 7,
        'quota_boost': 10,
        'features': [
            'Multiple question formats',
            'Aligned to GES indicators',
            'Difficulty auto-scaling',
            'Printable answer keys',
        ],
    },
    {
        'name': 'Study Guide Builder',
        'slug': 'study-guide-builder',
        'tagline': 'Student revision packs on demand',
        'description': 'Create concise, student-friendly study guides from your lesson plans — perfect for exam prep.',
        'category': 'ai_tools',
        'icon': 'bi bi-book-half',
        'badge_label': '',
        'price': 12.00,
        'trial_days': 7,
        'quota_boost': 10,
        'features': [
            'Key concepts summary',
            'Practice questions per topic',
            'Visual mnemonics',
            'Shareable PDF links',
        ],
    },
    {
        'name': 'Quick Report Writer',
        'slug': 'quick-report-writer',
        'tagline': 'Generate student reports in minutes',
        'description': 'Craft personalised end-of-term reports using grade data plus AI-suggested remarks tailored to each student\'s performance.',
        'category': 'productivity',
        'icon': 'bi bi-file-earmark-richtext',
        'badge_label': '',
        'price': 15.00,
        'trial_days': 7,
        'quota_boost': 15,
        'features': [
            'Personalised AI-written remarks',
            'Pull grades & attendance automatically',
            'Bulk export as PDF',
            'Custom report templates',
        ],
    },
    {
        'name': 'Grade Insight Dashboard',
        'slug': 'grade-insight-dashboard',
        'tagline': 'Deeper analytics on student performance',
        'description': 'Visualise grade trends, class averages, and per-student progress over multiple terms with interactive charts.',
        'category': 'assessment',
        'icon': 'bi bi-graph-up-arrow',
        'badge_label': 'POPULAR',
        'price': 15.00,
        'trial_days': 7,
        'quota_boost': 10,
        'features': [
            'Term-over-term trend charts',
            'Class & subject breakdowns',
            'At-risk student alerts',
            'Export data to CSV',
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
        'price': 12.00,
        'trial_days': 7,
        'quota_boost': 5,
        'features': [
            'Real-time student responses',
            'Join via code — any device',
            'Leaderboard & results breakdown',
            'Auto-generate questions with AI',
        ],
    },
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

    # ═══════════════════════════════════════════════════════════════════
    # TIER: PREMIUM (GHS 25–40)  —  Heavy AI, max value, 14-day trial
    # ═══════════════════════════════════════════════════════════════════
    {
        'name': 'Smart Planner Pro',
        'slug': 'smart-planner-pro',
        'tagline': 'AI-powered weekly planning assistant',
        'description': 'Automatically draft weekly lesson outlines from your scheme of work and syllabus. Saves hours of manual planning.',
        'category': 'productivity',
        'icon': 'bi bi-calendar2-week',
        'badge_label': 'POPULAR',
        'price': 25.00,
        'trial_days': 14,
        'quota_boost': 30,
        'features': [
            'Auto-generate weekly plans from scheme',
            'Drag-and-drop schedule builder',
            'Export to PDF & print-ready formats',
            'Sync with school timetable',
        ],
    },
    {
        'name': 'Aura Slide Generator',
        'slug': 'aura-slide-generator',
        'tagline': 'Turn any topic into a slide deck',
        'description': 'Type a topic and get a polished presentation with key points, diagrams, and discussion prompts — ready to present.',
        'category': 'ai_tools',
        'icon': 'bi bi-easel2',
        'badge_label': 'POPULAR',
        'price': 30.00,
        'trial_days': 14,
        'quota_boost': 30,
        'features': [
            'AI-generated slide content',
            'Auto-add visuals & diagrams',
            'Export to PPTX',
            'Live session integration',
        ],
    },
    {
        'name': 'Report Card AI Writer',
        'slug': 'report-card-writer',
        'tagline': 'End-of-term reports in minutes, not days',
        'description': 'AI reads each student\'s grades, attendance, and behavior data then generates personalised, professional report card comments. Bulk-generate for an entire class in one click.',
        'category': 'ai_tools',
        'icon': 'bi bi-card-text',
        'badge_label': 'HOT',
        'price': 30.00,
        'trial_days': 14,
        'quota_boost': 25,
        'features': [
            'AI-personalised comment per student',
            'Pulls grades & attendance automatically',
            'Bulk generate for entire class',
            'Edit, regenerate, or write your own',
        ],
    },
    {
        'name': 'Exam & Question Bank Pro',
        'slug': 'exam-question-bank',
        'tagline': 'Build exams smarter, not harder',
        'description': 'Create a searchable bank of questions tagged by subject, topic, and difficulty. AI generates new questions on demand. Assemble exam papers with auto-shuffled variants.',
        'category': 'assessment',
        'icon': 'bi bi-database-check',
        'badge_label': 'HOT',
        'price': 35.00,
        'trial_days': 14,
        'quota_boost': 25,
        'features': [
            'Searchable question bank',
            'AI-generated questions on demand',
            'Multiple formats: MCQ, fill-in, essay',
            'Assemble & print exam papers',
        ],
    },
    {
        'name': 'Differentiated Lesson AI',
        'slug': 'differentiated-lesson-ai',
        'tagline': 'One lesson, three ability levels',
        'description': 'Paste or pick a lesson plan and AI generates three versions: foundational (struggling), grade-level (on-track), and extension (advanced). Inclusive teaching made easy.',
        'category': 'ai_tools',
        'icon': 'bi bi-diagram-3',
        'badge_label': '',
        'price': 25.00,
        'trial_days': 14,
        'quota_boost': 20,
        'features': [
            'Three differentiated tiers per lesson',
            'Scaffolded activities & instructions',
            'Works with existing lesson plans',
            'Aligned to GES inclusive education policy',
        ],
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
