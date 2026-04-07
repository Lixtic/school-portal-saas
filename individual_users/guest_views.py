"""
Guest / Try-Before-You-Buy views for the individual teacher portal.

Implements three tiers of deferred registration:
  1. Guest Catalog  — browse GES subjects & strands (no account needed)
  2. Freemium Preview — one free AI lesson-plan generation per session
  3. Contextual CTA  — smart signup wall after the free generation
"""
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from individual_users.ai_cache import call_and_cache, get_cached
from individual_users.models import ToolQuestion

logger = logging.getLogger(__name__)

# ── GES Curriculum Database ──────────────────────────────────────────────────
# Structured representation of the Ghana Education Service (GES) B7–B10
# curriculum organized by subject → strand → sub-strand → sample indicators.
# The 3 "showcase" subjects (marked showcase=True) are chosen for maximum
# first-impression impact on visiting teachers.

GES_CURRICULUM = [
    {
        'subject': 'mathematics',
        'label': 'Mathematics',
        'icon': 'bi-calculator',
        'color': '#4361ee',
        'showcase': True,
        'strands': [
            {
                'name': 'Number',
                'sub_strands': [
                    {
                        'name': 'Number and Numeration Systems',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Demonstrate understanding of whole numbers up to 10,000,000'},
                            {'code': 'B7.1.1.1.2', 'text': 'Demonstrate understanding of integers and perform operations on them'},
                            {'code': 'B7.1.1.1.3', 'text': 'Apply the concept of factors and multiples, including HCF and LCM'},
                            {'code': 'B8.1.1.1.1', 'text': 'Apply understanding of rational numbers including fractions and decimals'},
                        ],
                    },
                    {
                        'name': 'Number Operations',
                        'indicators': [
                            {'code': 'B7.1.2.1.1', 'text': 'Apply the four basic operations on integers using real-life problems'},
                            {'code': 'B7.1.2.1.2', 'text': 'Solve multi-step word problems involving the four operations'},
                        ],
                    },
                    {
                        'name': 'Fractions, Decimals & Percentages',
                        'indicators': [
                            {'code': 'B7.1.3.1.1', 'text': 'Perform operations on fractions — addition, subtraction, multiplication, division'},
                            {'code': 'B7.1.3.2.1', 'text': 'Convert between fractions, decimals and percentages'},
                            {'code': 'B8.1.3.1.1', 'text': 'Solve real-life problems involving fractions, decimals and percentages'},
                        ],
                    },
                ],
            },
            {
                'name': 'Algebra',
                'sub_strands': [
                    {
                        'name': 'Patterns and Relations',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Identify and extend number and shape patterns'},
                            {'code': 'B7.2.1.2.1', 'text': 'Use variables and expressions to describe real-life situations'},
                        ],
                    },
                    {
                        'name': 'Equations and Inequalities',
                        'indicators': [
                            {'code': 'B7.2.2.1.1', 'text': 'Solve simple linear equations in one variable'},
                            {'code': 'B8.2.2.1.1', 'text': 'Formulate and solve linear equations from word problems'},
                        ],
                    },
                ],
            },
            {
                'name': 'Geometry & Measurement',
                'sub_strands': [
                    {
                        'name': 'Shape and Space',
                        'indicators': [
                            {'code': 'B7.3.1.1.1', 'text': 'Classify angles — acute, right, obtuse, reflex — and measure using a protractor'},
                            {'code': 'B7.3.1.2.1', 'text': 'Identify properties of triangles and quadrilaterals'},
                        ],
                    },
                    {
                        'name': 'Measurement',
                        'indicators': [
                            {'code': 'B7.3.2.1.1', 'text': 'Calculate perimeter and area of rectangles, triangles and circles'},
                            {'code': 'B7.3.2.2.1', 'text': 'Calculate volume of cubes and cuboids'},
                        ],
                    },
                ],
            },
            {
                'name': 'Handling Data',
                'sub_strands': [
                    {
                        'name': 'Data Collection and Presentation',
                        'indicators': [
                            {'code': 'B7.4.1.1.1', 'text': 'Collect, organise and present data using tables, bar charts and pie charts'},
                            {'code': 'B7.4.1.2.1', 'text': 'Calculate mean, median and mode for a set of data'},
                        ],
                    },
                ],
            },
        ],
    },
    {
        'subject': 'science',
        'label': 'Integrated Science',
        'icon': 'bi-flask',
        'color': '#059669',
        'showcase': True,
        'strands': [
            {
                'name': 'Diversity of Matter',
                'sub_strands': [
                    {
                        'name': 'Materials',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Classify materials as living and non-living things'},
                            {'code': 'B7.1.1.2.1', 'text': 'Describe the properties and uses of metals and non-metals'},
                        ],
                    },
                    {
                        'name': 'Mixtures',
                        'indicators': [
                            {'code': 'B7.1.2.1.1', 'text': 'Distinguish between mixtures and pure substances'},
                            {'code': 'B7.1.2.1.2', 'text': 'Describe separation techniques — filtration, evaporation, distillation, magnetism'},
                        ],
                    },
                ],
            },
            {
                'name': 'Cycles',
                'sub_strands': [
                    {
                        'name': 'Earth Science',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Explain the water cycle and its effect on weather patterns'},
                            {'code': 'B7.2.1.2.1', 'text': 'Describe the rock cycle and identify types of rocks'},
                        ],
                    },
                    {
                        'name': 'Life Cycles',
                        'indicators': [
                            {'code': 'B7.2.2.1.1', 'text': 'Trace the life cycle of a flowering plant'},
                            {'code': 'B7.2.2.2.1', 'text': 'Describe the life cycle of insects — complete and incomplete metamorphosis'},
                        ],
                    },
                ],
            },
            {
                'name': 'Systems',
                'sub_strands': [
                    {
                        'name': 'The Human Body',
                        'indicators': [
                            {'code': 'B7.3.1.1.1', 'text': 'Describe the structure and function of the digestive system'},
                            {'code': 'B7.3.1.2.1', 'text': 'Explain the circulatory system — heart, blood vessels, blood'},
                        ],
                    },
                    {
                        'name': 'Ecosystems',
                        'indicators': [
                            {'code': 'B7.3.2.1.1', 'text': 'Identify components of an ecosystem — producers, consumers, decomposers'},
                            {'code': 'B7.3.2.2.1', 'text': 'Construct food chains and food webs from a given habitat'},
                        ],
                    },
                ],
            },
            {
                'name': 'Energy',
                'sub_strands': [
                    {
                        'name': 'Sources and Forms of Energy',
                        'indicators': [
                            {'code': 'B7.4.1.1.1', 'text': 'Identify forms of energy — heat, light, sound, electrical, chemical'},
                            {'code': 'B7.4.1.2.1', 'text': 'Explain energy conversion and the principle of conservation of energy'},
                        ],
                    },
                    {
                        'name': 'Electricity and Magnetism',
                        'indicators': [
                            {'code': 'B7.4.2.1.1', 'text': 'Construct simple electric circuits and identify series/parallel connections'},
                            {'code': 'B7.4.2.2.1', 'text': 'Investigate factors that affect the strength of an electromagnet'},
                        ],
                    },
                ],
            },
        ],
    },
    {
        'subject': 'english',
        'label': 'English Language',
        'icon': 'bi-book',
        'color': '#f59e0b',
        'showcase': True,
        'strands': [
            {
                'name': 'Oral Language',
                'sub_strands': [
                    {
                        'name': 'Listening Comprehension',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Listen to and summarise a passage read aloud'},
                            {'code': 'B7.1.1.2.1', 'text': 'Identify main ideas and supporting details from spoken texts'},
                        ],
                    },
                    {
                        'name': 'Speaking',
                        'indicators': [
                            {'code': 'B7.1.2.1.1', 'text': 'Deliver a 2-minute prepared speech on a given topic'},
                            {'code': 'B7.1.2.2.1', 'text': 'Participate in a class debate using formal language conventions'},
                        ],
                    },
                ],
            },
            {
                'name': 'Reading',
                'sub_strands': [
                    {
                        'name': 'Reading Comprehension',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Read and comprehend grade-level text — identify theme, setting, characters'},
                            {'code': 'B7.2.1.2.1', 'text': 'Use context clues to determine the meaning of unfamiliar words'},
                        ],
                    },
                    {
                        'name': 'Vocabulary Development',
                        'indicators': [
                            {'code': 'B7.2.2.1.1', 'text': 'Build vocabulary through word families, synonyms and antonyms'},
                            {'code': 'B7.2.2.2.1', 'text': 'Use a dictionary to find meanings, pronunciation and parts of speech'},
                        ],
                    },
                ],
            },
            {
                'name': 'Grammar & Composition',
                'sub_strands': [
                    {
                        'name': 'Grammar',
                        'indicators': [
                            {'code': 'B7.3.1.1.1', 'text': 'Identify and use the eight parts of speech correctly in sentences'},
                            {'code': 'B7.3.1.2.1', 'text': 'Construct simple, compound and complex sentences'},
                        ],
                    },
                    {
                        'name': 'Writing',
                        'indicators': [
                            {'code': 'B7.3.2.1.1', 'text': 'Write a well-structured narrative essay with introduction, body and conclusion'},
                            {'code': 'B7.3.2.2.1', 'text': 'Write formal and informal letters following standard conventions'},
                        ],
                    },
                ],
            },
        ],
    },
    {
        'subject': 'social_studies',
        'label': 'Social Studies',
        'icon': 'bi-globe-americas',
        'color': '#8b5cf6',
        'showcase': False,
        'strands': [
            {
                'name': 'Environment',
                'sub_strands': [
                    {
                        'name': 'Our Physical Environment',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Describe the physical features of Ghana — relief, drainage, vegetation'},
                            {'code': 'B7.1.1.2.1', 'text': 'Explain the effects of climate change on Ghanaian communities'},
                        ],
                    },
                ],
            },
            {
                'name': 'Governance',
                'sub_strands': [
                    {
                        'name': 'National Governance',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Describe the arms of government and their functions'},
                            {'code': 'B7.2.1.2.1', 'text': 'Explain the role of local government (District Assembly) in national development'},
                        ],
                    },
                ],
            },
            {
                'name': 'Culture & Identity',
                'sub_strands': [
                    {
                        'name': 'Ghanaian Culture',
                        'indicators': [
                            {'code': 'B7.3.1.1.1', 'text': 'Discuss naming ceremonies, festivals and rites of passage across Ghanaian ethnic groups'},
                        ],
                    },
                ],
            },
        ],
    },
    {
        'subject': 'computing',
        'label': 'Computing / ICT',
        'icon': 'bi-cpu',
        'color': '#0ea5e9',
        'showcase': False,
        'strands': [
            {
                'name': 'Introduction to Computing',
                'sub_strands': [
                    {
                        'name': 'Computer Systems',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Identify hardware and software components of a computer system'},
                            {'code': 'B7.1.1.2.1', 'text': 'Explain input, processing, storage and output functions'},
                        ],
                    },
                ],
            },
            {
                'name': 'Computational Thinking',
                'sub_strands': [
                    {
                        'name': 'Algorithms & Problem Solving',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Design simple algorithms using flowcharts and pseudocode'},
                            {'code': 'B7.2.1.2.1', 'text': 'Decompose a complex problem into smaller, manageable steps'},
                        ],
                    },
                ],
            },
            {
                'name': 'AI Literacy',
                'sub_strands': [
                    {
                        'name': 'Understanding AI',
                        'indicators': [
                            {'code': 'B7.3.1.1.1', 'text': 'Explain what artificial intelligence is and give examples of AI in daily life'},
                        ],
                    },
                ],
            },
        ],
    },
    {
        'subject': 'rme',
        'label': 'Religious & Moral Education',
        'icon': 'bi-heart',
        'color': '#e11d48',
        'showcase': False,
        'strands': [
            {
                'name': 'God and His Creation',
                'sub_strands': [
                    {
                        'name': 'The Nature of God',
                        'indicators': [
                            {'code': 'B7.1.1.1.1', 'text': 'Discuss the attributes of God from Christian, Islamic and Traditional perspectives'},
                        ],
                    },
                ],
            },
            {
                'name': 'Moral Life',
                'sub_strands': [
                    {
                        'name': 'Moral Teachings',
                        'indicators': [
                            {'code': 'B7.2.1.1.1', 'text': 'Examine moral teachings on truthfulness, honesty and respect from the three religions'},
                        ],
                    },
                ],
            },
        ],
    },
]

# Count totals for the catalog hero banner
_total_strands = sum(len(s['strands']) for s in GES_CURRICULUM)
_total_sub_strands = sum(
    len(ss['sub_strands'])
    for s in GES_CURRICULUM
    for ss in s['strands']
)
_total_indicators = sum(
    len(ind['indicators'])
    for s in GES_CURRICULUM
    for st in s['strands']
    for ind in st['sub_strands']
)

CATALOG_STATS = {
    'subjects': len(GES_CURRICULUM),
    'strands': _total_strands,
    'sub_strands': _total_sub_strands,
    'indicators': _total_indicators,
}


# ── Session-based free generation tracking ───────────────────────────────────

GUEST_SESSION_KEY = 'guest_free_generations'
GUEST_MAX_FREE = 1  # one free generation before signup wall


def _guest_generations_used(request):
    """Return how many free AI generations this session has consumed."""
    return request.session.get(GUEST_SESSION_KEY, 0)


def _guest_can_generate(request):
    """True if the guest still has a free generation available."""
    return _guest_generations_used(request) < GUEST_MAX_FREE


def _guest_record_generation(request):
    """Increment the session counter after a successful generation."""
    request.session[GUEST_SESSION_KEY] = _guest_generations_used(request) + 1
    request.session.modified = True


# ── Views ────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def guest_catalog(request):
    """
    Browse the full GES curriculum — all subjects, strands, sub-strands
    and indicators.  AI generation buttons are visible but locked behind
    a signup CTA unless the user has a free generation remaining.
    """
    # If authenticated individual user, redirect to tools hub
    if request.user.is_authenticated and getattr(request.user, 'user_type', '') == 'individual':
        return redirect('individual:tools_hub')

    showcase = [s for s in GES_CURRICULUM if s.get('showcase')]
    others = [s for s in GES_CURRICULUM if not s.get('showcase')]
    can_generate = _guest_can_generate(request)

    ctx = {
        'showcase_subjects': showcase,
        'other_subjects': others,
        'stats': CATALOG_STATS,
        'can_generate': can_generate,
        'generations_used': _guest_generations_used(request),
        'max_free': GUEST_MAX_FREE,
    }
    return render(request, 'individual/guest/catalog.html', ctx)


@ensure_csrf_cookie
def guest_strand_detail(request, subject_slug, strand_idx):
    """View a single strand's full sub-strands and indicators."""
    subj = next((s for s in GES_CURRICULUM if s['subject'] == subject_slug), None)
    if not subj or strand_idx >= len(subj['strands']):
        return redirect('individual:guest_catalog')

    strand = subj['strands'][strand_idx]
    can_generate = _guest_can_generate(request)

    ctx = {
        'subject': subj,
        'strand': strand,
        'strand_idx': strand_idx,
        'can_generate': can_generate,
        'generations_used': _guest_generations_used(request),
        'max_free': GUEST_MAX_FREE,
    }
    return render(request, 'individual/guest/strand_detail.html', ctx)


@require_POST
def guest_generate(request):
    """
    Freemium AI generation — one free GES-aligned lesson plan per session.
    After the free generation, subsequent calls return a contextual CTA
    instead of lesson content.
    """
    # Already signed in? redirect to the real tool
    if request.user.is_authenticated and getattr(request.user, 'user_type', '') == 'individual':
        return JsonResponse({
            'redirect': '/u/tools/lesson-plans/new/',
        })

    if not _guest_can_generate(request):
        # Build contextual CTA based on what they're trying to generate
        subject = request.POST.get('subject', 'this subject')
        topic = request.POST.get('topic', 'this topic')
        indicator_code = request.POST.get('indicator', '')
        target_class = request.POST.get('target_class', 'Basic 7')

        cta_message = (
            f"I've drafted a {target_class} {subject.replace('_', ' ').title()} lesson "
            f"on \"{topic}\" for you. Want me to generate the SBA Quiz to go with it? "
            f"Sign up in 10 seconds to unlock unlimited lesson plans, exam papers, "
            f"slide decks and 20+ AI teaching tools."
        )
        return JsonResponse({
            'wall': True,
            'cta': cta_message,
            'signup_url': '/u/signup/',
        }, status=200)

    # ── Validate inputs ──────────────────────────────────────
    subject = request.POST.get('subject', 'mathematics')
    topic = request.POST.get('topic', '').strip()
    indicator = request.POST.get('indicator', '').strip()
    sub_strand = request.POST.get('sub_strand', '').strip()
    target_class = request.POST.get('target_class', 'Basic 7')
    duration = 60

    if not topic and not indicator:
        return JsonResponse({'error': 'Please provide a topic or indicator.'}, status=400)

    subject_label = dict(ToolQuestion.SUBJECT_CHOICES).get(subject, subject.replace('_', ' ').title())

    # ── Build AI prompt ──────────────────────────────────────
    system_prompt = (
        'You are Padi-T, an expert Ghanaian GES curriculum specialist. '
        'You create lesson plans following the 3-phase pedagogy: '
        'Phase 1 (Starter), Phase 2 (Main/New Learning), Phase 3 (Reflection). '
        'Always include practical activities, formative assessment checkpoints, '
        'and differentiation tips. '
        'Return ONLY a JSON object with these keys: '
        'title, objectives, materials, introduction, development, assessment, closure. '
        'Each value should be a detailed string with numbered or bulleted points. '
        'No markdown fences, no extra keys.'
    )

    user_prompt = f"Create a detailed GES-aligned lesson plan for {target_class} {subject_label}"
    if indicator:
        user_prompt += f" (indicator: {indicator})"
    if sub_strand:
        user_prompt += f", sub-strand: {sub_strand}"
    user_prompt += f" on the topic: '{topic or sub_strand}'. Duration: {duration} minutes."
    user_prompt += (
        "\nStructure using GES 3-phase pedagogy:\n"
        "- Phase 1 (Starter): 10 min — activate prior knowledge\n"
        "- Phase 2 (Main/New Learning): 40 min — demonstrations, group work, formative checks\n"
        "- Phase 3 (Reflection): 10 min — summary, exit ticket, self-assessment\n"
    )

    try:
        # Check cache first to avoid unnecessary API calls
        raw = get_cached(system=system_prompt, prompt=user_prompt)
        if raw is None:
            raw = call_and_cache(system=system_prompt, prompt=user_prompt)
        # Parse JSON from the AI response
        text = raw.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
        plan = json.loads(text)
    except (json.JSONDecodeError, Exception) as exc:
        logger.exception('Guest AI generation failed: %s', exc)
        return JsonResponse({
            'error': 'AI generation failed. Please try again.',
        }, status=500)

    # Record the free generation
    _guest_record_generation(request)

    # Build contextual follow-up CTA
    title = plan.get('title', topic)
    followup_cta = (
        f"I've drafted \"{title}\" for you — a full GES-aligned {target_class} "
        f"{subject_label} lesson plan. Want me to generate the SBA Quiz to go "
        f"with it? Sign up in 10 seconds to unlock everything."
    )

    return JsonResponse({
        'ok': True,
        'plan': plan,
        'followup_cta': followup_cta,
        'signup_url': '/u/signup/',
        'generations_remaining': max(0, GUEST_MAX_FREE - _guest_generations_used(request)),
    })
