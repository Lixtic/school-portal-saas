"""
Auto-seed starter content for new individual teacher accounts.

Call ``seed_starter_content(profile)`` once right after a teacher
verifies their account (email, phone, or Google OAuth).  It is
idempotent — calling it twice on the same profile is harmless.

What it creates:
  • Free-tier AddonSubscriptions for 3 core tools
  • 2 sample lesson plans (Maths & Science, B7, GES-aligned)
  • 3 sample questions + 1 exam paper
  • 1 sample slide deck (Fractions, 5 slides)
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Sample Lesson Plans ──────────────────────────────────────────────────────

_LESSON_PLANS = [
    {
        'title': 'Understanding Integers and Their Operations',
        'subject': 'mathematics',
        'target_class': 'Basic 7',
        'topic': 'Integers',
        'indicator': 'B7.1.1.1.2',
        'sub_strand': 'Number and Numeration Systems',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.1.1.1 — Demonstrate understanding of the '
            'concept of integers and perform operations on them.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify positive and negative integers on a number line\n'
            '2. Compare and order integers using < , > and =\n'
            '3. Add and subtract integers using the number line method'
        ),
        'materials': (
            'Number line chart (–20 to +20), integer flashcards, counters '
            '(red for negative, blue for positive), mini whiteboards, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Temperature Challenge"\n'
            '• Display temperatures of 5 cities: Accra (+32 °C), London (+5 °C), '
            'Moscow (–12 °C), Cairo (+18 °C), Oslo (–7 °C)\n'
            '• Ask: "Which city is coldest? Which is warmest?"\n'
            '• Introduce the term "integer" — any whole number, positive, '
            'negative, or zero.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Plotting Integers (15 min)\n'
            '• Draw a number line from –10 to +10.\n'
            '• Students plot given integers in pairs.\n\n'
            'Activity 2: Comparing & Ordering (10 min)\n'
            '• Groups arrange 10 integer cards in ascending/descending order.\n'
            '• Write comparison statements using <, >, =.\n\n'
            'Activity 3: Adding Integers (15 min)\n'
            '• Demonstrate: (+3) + (–5) → start at +3, move 5 left → –2\n'
            '• Students solve 8 problems on mini whiteboards.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Quick quiz: Plot, compare, and add 5 integers.\n'
            '• Exit ticket: Explain why –3 > –7 using the number line.'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw a number line –15 to +15, plot: –12, –7, 0, +4, +11\n'
            '2. Solve: (+8)+(–3), (–6)+(+2), (–5)+(–4), (+7)+(–7), (–9)+(+12)'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Number',
            'sub_strand': 'Number and Numeration Systems',
            'content_standard': 'B7.1.1.1',
            'indicator': 'B7.1.1.1.2',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Collaboration',
        },
    },
    {
        'title': 'Mixtures and Separation Techniques',
        'subject': 'science',
        'target_class': 'Basic 7',
        'topic': 'Mixtures',
        'indicator': 'B7.1.2.1.1',
        'sub_strand': 'Diversity of Matter',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.1.2.1 — Demonstrate knowledge of '
            'mixtures and how to separate them.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Distinguish between mixtures and pure substances\n'
            '2. Identify 4 separation methods\n'
            '3. Select the appropriate technique for a given mixture'
        ),
        'materials': (
            'Sand, salt, water, iron filings, magnet, filter paper, funnel, '
            'beakers, chromatography paper, food colouring'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Kitchen Chemistry"\n'
            '• Show garri soaked in water with groundnuts.\n'
            '• Ask: "Is this one substance or many? Can we separate them?"\n'
            '• Define mixture: two or more substances physically combined.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Station Rotation — 4 groups, 10 min each:\n\n'
            'Station 1: Magnetic Separation — sand + iron filings\n'
            'Station 2: Filtration — sand + water\n'
            'Station 3: Evaporation — salt solution\n'
            'Station 4: Chromatography — food colouring on paper\n\n'
            'Class Synthesis: Groups present findings; build summary table.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Match-the-method worksheet (4 mixtures → 4 techniques).\n'
            '• Exit ticket: "Why can\'t you use filtration to separate salt water?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Name 3 mixtures found in your home.\n'
            '2. State the best separation method for each and explain why.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Diversity of Matter',
            'sub_strand': 'Materials',
            'content_standard': 'B7.1.2.1',
            'indicator': 'B7.1.2.1.1',
            'period': '2',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Problem Solving',
        },
    },
]


# ── Sample Questions ─────────────────────────────────────────────────────────

_QUESTIONS = [
    {
        'subject': 'mathematics',
        'target_class': 'Basic 7',
        'topic': 'Integers',
        'question_text': 'Evaluate: (–8) + (+5)',
        'question_format': 'mcq',
        'difficulty': 'easy',
        'options': ['A) –13', 'B) –3', 'C) 3', 'D) 13'],
        'correct_answer': 'B',
        'explanation': 'Start at –8, move 5 steps to the right → –3.',
    },
    {
        'subject': 'mathematics',
        'target_class': 'Basic 7',
        'topic': 'Integers',
        'question_text': 'Which integer is greater: –4 or –9?',
        'question_format': 'mcq',
        'difficulty': 'easy',
        'options': ['A) –4', 'B) –9', 'C) They are equal', 'D) Cannot determine'],
        'correct_answer': 'A',
        'explanation': '–4 is closer to zero on the number line, so –4 > –9.',
    },
    {
        'subject': 'science',
        'target_class': 'Basic 7',
        'topic': 'Mixtures',
        'question_text': 'Which separation technique is best for removing iron filings from sand?',
        'question_format': 'mcq',
        'difficulty': 'medium',
        'options': ['A) Filtration', 'B) Evaporation', 'C) Magnetic separation', 'D) Distillation'],
        'correct_answer': 'C',
        'explanation': 'Iron is magnetic; a magnet attracts it out of the sand.',
    },
]


# ── Sample Slide Deck ────────────────────────────────────────────────────────

_DECK = {
    'presentation': {
        'title': 'Understanding Fractions — Parts of a Whole',
        'subject': 'mathematics',
        'target_class': 'Basic 7',
        'theme': 'aurora',
        'transition': 'slide',
    },
    'slides': [
        {
            'order': 0,
            'layout': 'title',
            'title': 'Understanding Fractions',
            'content': 'Parts of a Whole\nBasic 7 Mathematics\nTerm 1, Week 4',
            'speaker_notes': 'Ask: "If I cut an orange into 4 equal parts and give you 1 piece, what fraction did you get?"',
            'emoji': '\U0001F34A',
        },
        {
            'order': 1,
            'layout': 'bullets',
            'title': 'What is a Fraction?',
            'content': (
                'A fraction represents PART of a whole\n'
                'Written as numerator / denominator\n'
                'Denominator = how many equal parts\n'
                'Numerator = how many parts we have\n'
                'Example: 3/4 means 3 out of 4 equal parts'
            ),
            'speaker_notes': 'Draw a circle divided into 4, shade 3 parts.',
            'emoji': '\U0001F4D0',
        },
        {
            'order': 2,
            'layout': 'two_col',
            'title': 'Types of Fractions',
            'content': (
                'PROPER FRACTIONS:\nNumerator < Denominator\n1/2, 3/4, 5/8\n'
                '---\n'
                'IMPROPER FRACTIONS:\nNumerator \u2265 Denominator\n5/3, 7/4, 9/2'
            ),
            'speaker_notes': 'Ask: "Can a proper fraction be greater than 1?"',
            'emoji': '\u2696\uFE0F',
        },
        {
            'order': 3,
            'layout': 'bullets',
            'title': 'Practice Problems',
            'content': (
                '1. Convert 11/4 to a mixed number\n'
                '2. Convert 3\u2154 to an improper fraction\n'
                '3. Find two fractions equivalent to 2/5\n'
                '4. A farmer plants 3/8 maize and 2/8 cassava. Total fraction planted?'
            ),
            'speaker_notes': 'Answers: 1) 2\u00BE  2) 11/3  3) 4/10, 6/15  4) 5/8',
            'emoji': '\u270D\uFE0F',
        },
        {
            'order': 4,
            'layout': 'summary',
            'title': 'Key Takeaways',
            'content': (
                'Fractions = parts of a whole\n'
                'Proper < 1, Improper \u2265 1\n'
                'Mixed numbers = whole + fraction\n'
                'Equivalent fractions have the same value\n'
                'Always simplify to lowest terms'
            ),
            'speaker_notes': 'Recap and assign homework.',
            'emoji': '\u2705',
        },
    ],
}


# ── Free add-on slugs to auto-subscribe ──────────────────────────────────────

_FREE_ADDONS = [
    ('lesson-planner', 'Smart Lesson Planner'),
    ('exam-generator', 'Question Bank & Exam Paper'),
    ('slide-generator', 'Slide Deck Generator'),
]


# ── Public API ───────────────────────────────────────────────────────────────

def seed_starter_content(profile):
    """Create free subscriptions and sample content for a new teacher.

    Idempotent: skips any record that already exists (checks by title).
    Runs synchronously; typical wall-time < 50 ms (pure DB inserts).
    """
    if profile.role != 'teacher':
        return  # Only seed for teachers

    from individual_users.models import (
        AddonSubscription,
        ToolExamPaper,
        ToolLessonPlan,
        ToolPresentation,
        ToolQuestion,
        ToolSlide,
    )

    try:
        # ── 1. Free addon subscriptions ──────────────────────────
        for slug, name in _FREE_ADDONS:
            AddonSubscription.objects.get_or_create(
                profile=profile,
                addon_slug=slug,
                defaults={
                    'addon_name': name,
                    'plan': 'free',
                    'status': 'active',
                },
            )

        # ── 2. Lesson plans ──────────────────────────────────────
        for plan_data in _LESSON_PLANS:
            if not ToolLessonPlan.objects.filter(
                profile=profile, title=plan_data['title'],
            ).exists():
                ToolLessonPlan.objects.create(profile=profile, **plan_data)

        # ── 3. Questions + exam paper ────────────────────────────
        q_objs = []
        for q_data in _QUESTIONS:
            q, _ = ToolQuestion.objects.get_or_create(
                profile=profile,
                question_text=q_data['question_text'],
                defaults=q_data,
            )
            q_objs.append(q)

        exam_title = 'Sample B7 Mid-Term Assessment'
        if not ToolExamPaper.objects.filter(
            profile=profile, title=exam_title,
        ).exists():
            paper = ToolExamPaper.objects.create(
                profile=profile,
                title=exam_title,
                subject='mathematics',
                target_class='Basic 7',
                duration_minutes=45,
                instructions='Answer ALL questions. Write your answers clearly.',
                term='First Term',
                academic_year='2025/2026',
            )
            paper.questions.set([q for q in q_objs if q.subject == 'mathematics'])

        # ── 4. Slide deck ────────────────────────────────────────
        deck_meta = _DECK['presentation']
        if not ToolPresentation.objects.filter(
            profile=profile, title=deck_meta['title'],
        ).exists():
            pres = ToolPresentation.objects.create(profile=profile, **deck_meta)
            ToolSlide.objects.bulk_create([
                ToolSlide(presentation=pres, **slide)
                for slide in _DECK['slides']
            ])

        logger.info('Seeded starter content for %s', profile)

    except Exception:
        # Never break the signup flow if seeding fails
        logger.exception('Failed to seed starter content for %s', profile)
