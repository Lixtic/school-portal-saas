"""
Auto-seed starter content for new individual teacher accounts.

Call ``seed_starter_content(profile)`` once right after a teacher
verifies their account (email, phone, or Google OAuth).  It is
idempotent — calling it twice on the same profile is harmless.

What it creates:
  • Free-tier AddonSubscriptions for ALL teacher tools
  • 2 sample lesson plans (Maths & Science, B7, GES-aligned)
  • 3 sample questions + 1 exam paper
  • 1 sample slide deck (Fractions, 5 slides)
  • 2 sample CompuThink activities
  • 2 sample Literacy exercises
  • 2 sample CitizenEd activities
  • 2 sample TVET projects
  • 2 sample GES letters
  • 1 sample report card set with 5 student entries
  • 1 sample paper-marking session with 3 students
"""
import logging
from datetime import date
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
    ('ai-tutor', 'AI Teaching Assistant'),
    ('grade-analytics', 'Grade Analytics'),
    ('report-card', 'Report Card Writer'),
    ('attendance-tracker', 'Attendance Tracker'),
    ('licensure-prep', 'GTLE Licensure Prep'),
    ('letter-writer', 'GES Letter Writer'),
    ('paper-marker', 'Paper Marker'),
    ('computhink-lab', 'CompuThink Lab'),
    ('literacy-toolkit', 'Literacy Toolkit'),
    ('citizen-ed', 'CitizenEd'),
    ('tvet-workshop', 'TVET Workshop'),
]


# ── CompuThink Samples ───────────────────────────────────────────────────────

_COMPUTHINK_SAMPLES = [
    {
        'title': 'Sorting a Deck of Cards — Algorithm Design',
        'activity_type': 'algorithm',
        'level': 'b7',
        'strand': 'Computational Thinking',
        'topic': 'Sorting algorithms',
        'instructions': (
            'You have a shuffled deck of 10 numbered cards (1-10). '
            'Design a step-by-step algorithm to sort them from smallest to largest. '
            'Your algorithm should be clear enough that someone who has never sorted cards could follow it.'
        ),
        'content': {
            'problem': 'Given 10 shuffled cards numbered 1 to 10, arrange them in order from smallest to largest.',
            'steps': [
                'Look at the first two cards in your hand.',
                'If the left card is bigger than the right card, swap them.',
                'Move to the next pair of cards and compare again.',
                'Continue until you reach the end of the cards.',
                'Go back to the start and repeat until no more swaps are needed.',
                'When you complete a pass with zero swaps, the cards are sorted!',
            ],
            'hints': [
                'Think about how you naturally sort cards in a card game.',
                'This method is called "Bubble Sort" because smaller values bubble to the front.',
                'Count how many comparisons you make — is there a pattern?',
            ],
            'expected_output': 'Cards arranged in order: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10',
            'extension': 'Try with 20 cards. Does your algorithm still work? How many more steps does it take?',
        },
        'answer_key': (
            'Bubble Sort algorithm: compare adjacent pairs and swap if out of order; '
            'repeat passes until sorted. Best case O(n), worst case O(n\u00b2).'
        ),
    },
    {
        'title': "Breaking Down 'Cook Jollof Rice' into Sub-tasks",
        'activity_type': 'decomposition',
        'level': 'b7',
        'strand': 'Computational Thinking',
        'topic': 'Decomposition with everyday tasks',
        'instructions': (
            'Decompose the task "Cook Jollof Rice for the class" into smaller sub-tasks. '
            'Each sub-task should be simple enough that someone with no cooking experience can follow it. '
            'Identify which sub-tasks can happen at the same time (parallel) and which must happen in order (sequential).'
        ),
        'content': {
            'problem': 'Break down cooking Jollof Rice into the smallest possible sub-tasks and identify dependencies.',
            'steps': [
                'List ALL ingredients needed (rice, tomatoes, onions, oil, spices, water, protein).',
                'Sub-task 1: Wash and soak rice (15 min)',
                'Sub-task 2: Blend tomatoes, pepper, and onions (5 min)',
                'Sub-task 3: Heat oil in pot (3 min)',
                'Sub-task 4: Fry onions until golden (5 min) \u2014 depends on Sub-task 3',
                'Sub-task 5: Add blended tomatoes, cook until oil floats (20 min) \u2014 depends on 2 & 4',
                'Sub-task 6: Add spices and stock (2 min) \u2014 depends on Sub-task 5',
                'Sub-task 7: Add drained rice and water (5 min) \u2014 depends on 1 & 6',
                'Sub-task 8: Cover and cook on low heat (30 min) \u2014 depends on Sub-task 7',
            ],
            'hints': [
                'Some tasks can happen at the SAME TIME \u2014 which ones?',
                'Sub-tasks 1 and 2 can happen in parallel while Sub-task 3 heats the oil!',
                'In computing, this is like how a computer runs multiple processes simultaneously.',
            ],
            'expected_output': 'A decomposition diagram showing all sub-tasks with arrows showing dependencies.',
            'extension': 'Calculate total time if tasks run sequentially vs. with parallelism.',
        },
        'answer_key': (
            'Sequential time: ~85 min. With parallel execution: ~65 min. '
            'Key concept: decomposition reveals parallelism opportunities.'
        ),
    },
]


# ── Literacy Toolkit Samples ─────────────────────────────────────────────────

_LITERACY_SAMPLES = [
    {
        'title': "The Cocoa Farmer's Wisdom \u2014 Reading Comprehension",
        'exercise_type': 'comprehension',
        'level': 'b7',
        'strand': 'Reading',
        'topic': 'Reading for meaning',
        'passage': (
            '  Nana Agyemang had farmed cocoa in the Ashanti Region for over forty years. '
            'Every morning before dawn, he walked three kilometres to his plantation, cutlass in hand, '
            'humming an old Akan hymn.\n\n'
            '  "The cocoa tree does not grow in a day," he would say. "It takes five years before you '
            'harvest the first pod. A young person who plants today will feed their family tomorrow."\n\n'
            '  Last year, the government introduced a new fertilizer subsidy programme. Many farmers '
            'rushed to collect the free inputs, but Nana Agyemang was cautious. He tested the fertilizer '
            'on a small plot first, watching how the soil and trees responded over three months.\n\n'
            '  "Patience is not laziness," he explained to his grandson Kofi. '
            '"It is wisdom. The farmer who experiments before committing protects his livelihood."'
        ),
        'content': {
            'questions': [
                {
                    'question': 'How long has Nana Agyemang been farming cocoa?',
                    'options': ['Twenty years', 'Over forty years', 'Five years', 'Three years'],
                    'answer': 'Over forty years',
                },
                {
                    'question': "Why does Nana Agyemang say a cocoa tree 'does not grow in a day'?",
                    'options': [
                        'Because cocoa trees are very small',
                        'Because it takes five years to get the first harvest',
                        'Because he does not water his trees',
                        'Because the government delays the fertilizer',
                    ],
                    'answer': 'Because it takes five years to get the first harvest',
                },
                {
                    'question': 'What did Nana Agyemang do before applying the new fertilizer to his whole farm?',
                    'options': [
                        'He refused to use it entirely',
                        'He asked his grandson to apply it',
                        'He tested it on a small plot first',
                        'He sold it to other farmers',
                    ],
                    'answer': 'He tested it on a small plot first',
                },
                {
                    'question': "What does 'Patience is not laziness' mean in this passage?",
                    'options': [
                        'Lazy people are always patient',
                        'Taking time to think before acting is wisdom, not weakness',
                        'Farmers should never use new products',
                        'Kofi is lazy because he only helps after school',
                    ],
                    'answer': 'Taking time to think before acting is wisdom, not weakness',
                },
            ],
            'vocabulary_words': [
                {'word': 'plantation', 'definition': 'A large farm where crops like cocoa are grown'},
                {'word': 'subsidy', 'definition': 'Money or support given by the government to reduce cost'},
                {'word': 'cautious', 'definition': 'Being careful and avoiding unnecessary risks'},
                {'word': 'livelihood', 'definition': "A person's means of earning money to live"},
            ],
        },
        'answer_key': (
            '1. Over forty years  2. Five years to first harvest  '
            '3. Tested on a small plot  4. Wisdom, not weakness'
        ),
    },
    {
        'title': 'Tenses in Everyday Life \u2014 Grammar Drill',
        'exercise_type': 'grammar',
        'level': 'b7',
        'strand': 'Grammar',
        'topic': 'Simple past, present, and future tenses',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': 'Rewrite each sentence in the SIMPLE PAST tense.',
                    'sentences': [
                        'Ama walks to school every morning. \u2192 Ama ______ to school yesterday morning.',
                        'The fishermen catch many fish. \u2192 The fishermen ______ many fish last week.',
                        'We eat banku and tilapia for dinner. \u2192 We ______ banku and tilapia last night.',
                        'The teacher writes on the whiteboard. \u2192 The teacher ______ on the whiteboard yesterday.',
                    ],
                    'answers': ['walked', 'caught', 'ate', 'wrote'],
                },
                {
                    'instruction': "Rewrite each sentence in the SIMPLE FUTURE tense using 'will'.",
                    'sentences': [
                        'She reads the newspaper every day. \u2192 She ______ the newspaper tomorrow.',
                        'They visit Cape Coast Castle during vacation. \u2192 They ______ Cape Coast Castle next holiday.',
                        'I buy kelewele from the roadside. \u2192 I ______ kelewele this evening.',
                    ],
                    'answers': ['will read', 'will visit', 'will buy'],
                },
            ],
            'rules_summary': (
                'Simple Past: describes completed actions (walked, ate). '
                'Simple Present: habitual actions or facts (walks, eats). '
                'Simple Future: actions that will happen (will walk, shall eat). '
                "Tip: look for time markers like 'yesterday', 'every day', 'tomorrow'."
            ),
        },
        'answer_key': 'Section 1: walked, caught, ate, wrote. Section 2: will read, will visit, will buy.',
    },
]


# ── CitizenEd Samples ────────────────────────────────────────────────────────

_CITIZEN_ED_SAMPLES = [
    {
        'title': 'The Akosombo Dam \u2014 Development vs. Displacement',
        'activity_type': 'case_study',
        'level': 'b9',
        'strand': 'economics',
        'topic': 'Development projects and their impact on communities',
        'scenario_text': (
            'In 1965, the Akosombo Dam was completed on the Volta River. The dam created Lake Volta \u2014 '
            'the largest man-made lake in the world by surface area \u2014 and generates hydroelectric power '
            'for most of Ghana.\n\n'
            'However, over 80,000 people from more than 700 villages were displaced and relocated. '
            'Many lost their ancestral farmlands, fishing grounds, and sacred sites. The resettlement '
            'towns often lacked adequate infrastructure.\n\n'
            'Today, the dam provides approximately 1,020 MW of electricity, supports aluminium smelting, '
            'and enables fishing and transportation on Lake Volta. Yet communities around the lake continue '
            'to face challenges including waterborne diseases and periodic flooding.'
        ),
        'content': {
            'questions': [
                'List THREE benefits the Akosombo Dam has provided to Ghana\u2019s economy.',
                'Describe TWO negative effects the dam had on displaced communities.',
                'Do you think the government made the right decision? Justify with at least two reasons.',
                'If a similar project were proposed today, what steps should the government take to protect affected communities?',
            ],
            'key_points': [
                'Development projects can bring national benefits but local hardships.',
                'Displacement disrupts livelihoods, cultural ties, and community bonds.',
                'Governments must balance economic growth with social justice.',
                'Environmental Impact Assessments (EIAs) are now required by law in Ghana.',
                'The 1992 Constitution (Article 20) protects citizens against arbitrary property seizure.',
            ],
            'tasks': [
                "Group Task: Role-play a community meeting about the dam \u2014 'Government Officials' vs. 'Affected Villagers'.",
                "Individual Task: Write a 200-word letter from a displaced farmer to the President in 1965.",
            ],
        },
        'answer_guide': (
            'Benefits: hydroelectric power (1,020 MW), lake fishing industry, inland transportation, '
            'electricity export to Togo/Benin. Negatives: displacement of 80,000+ people, '
            'spread of waterborne diseases, loss of sacred sites, broken compensation promises.'
        ),
    },
    {
        'title': 'Reporting Corruption \u2014 What Would You Do?',
        'activity_type': 'scenario',
        'level': 'b8',
        'strand': 'citizenship',
        'topic': 'Anti-corruption and civic responsibility',
        'scenario_text': (
            'You are a Form 2 student. Your school was supposed to receive 200 new desks from the '
            'District Assembly, but only 120 arrived. Your class teacher tells you a school official '
            'kept 80 desks and is selling them in the market.\n\n'
            'You see the official at the market with the desks \u2014 the school stamp is still visible. '
            'He says, "Mind your own business \u2014 you\u2019re just a child."\n\n'
            'You know that CHRAJ handles corruption complaints, and there is a corruption hotline. '
            'Your parents warn you that reporting powerful people can have consequences.'
        ),
        'content': {
            'questions': [
                'Is what the school official did illegal? Which law does it violate?',
                'List THREE possible actions you could take in this situation.',
                'What are the RISKS of reporting the corruption? What are the risks of staying silent?',
                "Ghana's motto is 'Freedom and Justice.' How does this scenario test those values?",
            ],
            'key_points': [
                'Corruption is the abuse of public office for private gain.',
                'The Public Procurement Act (Act 663) governs government purchases.',
                'CHRAJ (Article 218, 1992 Constitution) investigates corruption.',
                'The Whistleblower Act (Act 720, 2006) protects people who report corruption.',
                'Every citizen has a civic duty to report wrongdoing, regardless of age.',
            ],
            'tasks': [
                'Write a formal complaint letter to CHRAJ describing the missing desks incident.',
                'Create a poster about the Whistleblower Act and how students can report corruption safely.',
            ],
        },
        'answer_guide': (
            'The official committed theft of public property (Criminal Offences Act, 1960). '
            'Actions: Report to CHRAJ, inform PTA, tell a trusted adult, use corruption hotline. '
            'Risks of reporting: retaliation, social pressure. '
            'Risks of silence: theft continues, students suffer, corruption normalised. '
            'The Whistleblower Act (720) provides legal protection.'
        ),
    },
]


# ── TVET Workshop Samples ────────────────────────────────────────────────────

_TVET_SAMPLES = [
    {
        'title': 'Design & Build a Wooden Book Shelf',
        'project_type': 'project_plan',
        'level': 'b9',
        'strand': 'design',
        'topic': 'Woodworking fundamentals \u2014 measuring, cutting, joining',
        'description': (
            'Students will design and construct a small free-standing wooden book shelf '
            '(3 shelves, approximately 90 cm tall \u00d7 60 cm wide \u00d7 25 cm deep) using locally '
            'available softwood (Wawa or Ceiba). Covers the full design-build cycle.'
        ),
        'content': {
            'objectives': [
                'Draw a labelled working sketch with dimensions in centimetres.',
                'Calculate total board length needed and estimate material cost.',
                'Demonstrate safe use of basic carpentry tools: handsaw, plane, try square, marking gauge.',
                'Apply at least TWO joining techniques: butt joint and a simple dado/housing joint.',
                'Sand and apply a finish (varnish or paint) to the completed shelf.',
            ],
            'materials': [
                'Wawa/Ceiba softwood planks (25 mm \u00d7 250 mm \u00d7 various lengths)',
                'Sandpaper (grades 80, 120, 240)', 'Wood glue (PVA-based)',
                'Nails/screws, varnish/wood stain, pencil, ruler, try square',
                'Handsaw, smoothing plane, hammer, screwdriver, workbench with clamp',
            ],
            'steps': [
                '1. DESIGN (Day 1): Sketch front and side views with dimensions.',
                '2. MATERIAL ESTIMATION (Day 1): Calculate board-metres, get market prices.',
                '3. MARKING OUT (Day 2): Transfer dimensions from sketch to wood.',
                '4. CUTTING (Day 2-3): Secure in vice and cut components with crosscut saw.',
                '5. JOINTING (Day 3-4): Cut housing/dado joints. Dry-fit before gluing.',
                '6. ASSEMBLY (Day 4): Glue, assemble, reinforce with nails/screws.',
                '7. SANDING (Day 5): Sand with 80, 120, then 240 grit along the grain.',
                '8. FINISHING (Day 5-6): Apply 2 coats of varnish, 24hr drying between coats.',
            ],
            'safety_notes': [
                'Always cut AWAY from your body. Secure wood in a vice before sawing.',
                'Wear safety goggles when sawing, planing, and sanding.',
                'Use a dust mask when sanding. Keep work area clean.',
            ],
            'assessment': {
                'Design & Planning (15)': 'Accurate sketch, complete materials list',
                'Tool Use & Technique (20)': 'Correct and safe use of all tools',
                'Assembly & Fit (20)': 'Square, stable construction, tight joints',
                'Surface Finish (15)': 'Smooth sanding, even varnish. No drips.',
                'Functionality (15)': 'Stands unsupported, holds 10+ books, level shelves',
                'Time Management (15)': 'Completed on schedule, work area clean',
            },
        },
        'answer_key': (
            'Material: ~3.6 m of 25 mm \u00d7 250 mm planks. '
            'Total cost estimate ~GHS 109 (planks, sandpaper, nails, glue, varnish). '
            'Housing joint: rectangular groove 10 mm deep into side panel for shelf.'
        ),
    },
    {
        'title': 'Workshop Safety & First Aid Assessment',
        'project_type': 'safety_quiz',
        'level': 'b7',
        'strand': 'health_safety',
        'topic': 'General workshop safety rules and first aid basics',
        'description': (
            'A comprehensive safety assessment covering workshop rules, PPE, hazard identification, '
            'fire safety, and basic first aid. Every TVET student must pass this before using tools.'
        ),
        'content': {
            'objectives': [
                'Identify at least 5 types of PPE and their uses.',
                'Explain safety sign colour coding (red, yellow, blue, green).',
                'Demonstrate correct response to cuts, burns, electric shock.',
                'List 5 general workshop safety rules.',
                'Identify fire extinguisher types and their uses.',
            ],
            'materials': [
                'PPE samples: goggles, gloves, ear defenders, dust mask, steel-toe boots, apron',
                'Safety signs posters', 'First aid kit', 'Fire extinguisher chart',
            ],
            'steps': [
                '1. PPE IDENTIFICATION: Match each PPE item to the hazard it protects against.',
                '2. SAFETY SIGNS: Classify 10 signs by colour/shape.',
                '3. HAZARD SPOTTING: Identify 8+ safety hazards in a workshop photograph.',
                '4. FIRST AID: Respond to 3 scenarios: cut, burn, electric shock.',
                '5. FIRE SAFETY: Draw Fire Triangle, match extinguisher types to fire classes.',
                '6. WRITTEN QUIZ: 20 MCQ, pass mark 80% (16/20).',
            ],
            'safety_notes': [
                'This is an ASSESSMENT \u2014 students should study the safety manual first.',
                'Never attempt to fight an electrical fire with water.',
                'First rule of first aid: ensure YOUR OWN safety before helping others.',
            ],
            'assessment': {
                'PPE Knowledge (20)': 'Correctly identifies 5+ PPE items',
                'Safety Signs (15)': 'Correctly classifies 8+ out of 10 signs',
                'Hazard Spotting (20)': 'Identifies 6+ hazards',
                'First Aid Response (25)': 'Correct procedure for all 3 scenarios',
                'Fire Safety (20)': 'Accurate Fire Triangle, correct extinguisher matching',
            },
        },
        'answer_key': (
            'PPE: goggles=eye, gloves=hands, ear defenders=hearing, dust mask=lungs, '
            'steel-toe boots=feet. Signs: red=prohibition, yellow=warning, blue=mandatory, '
            'green=safe condition. First Aid: cut=pressure+bandage, burn=cool 20min, '
            'shock=switch off power first.'
        ),
    },
]


# ── GES Letter Writer Samples ────────────────────────────────────────────────

_LETTER_SAMPLES = [
    {
        'title': 'Request for Inter-District Transfer',
        'category': 'posting',
        'status': 'final',
        'recipient_name': 'The District Director of Education',
        'recipient_title': 'Ghana Education Service, Accra Metropolitan',
        'sender_name': 'Kwame Mensah',
        'sender_title': 'Classroom Teacher',
        'school_name': 'Osu Presbyterian Junior High School',
        'district': 'Accra Metropolitan',
        'region': 'Greater Accra',
        'reference_number': 'GES/AMA/TRANS/2025/042',
        'date_written': date(2025, 3, 15),
        'body': (
            'Dear Sir/Madam,\n\n'
            'REQUEST FOR INTER-DISTRICT TRANSFER\n\n'
            'I write to respectfully request a transfer from Osu Presbyterian Junior High School '
            'in the Accra Metropolitan District to a school within the Kumasi Metropolitan District, '
            'Ashanti Region.\n\n'
            'I have served at my current station for five (5) years since my posting in September 2020. '
            'My request is necessitated by the recent relocation of my family to Kumasi due to my '
            'spouse\u2019s job transfer.\n\n'
            'The long-distance separation has placed a significant strain on my family, particularly '
            'regarding the care of my two young children aged 3 and 6.\n\n'
            'I have maintained an excellent professional record throughout my tenure, including:\n'
            '\u2022 Consistent BECE performance above district average in Mathematics\n'
            '\u2022 Active participation in school clubs (Science & Maths Quiz)\n'
            '\u2022 Completion of all GES in-service training programmes\n\n'
            'I humbly request that my transfer be considered at the earliest convenience. I am willing '
            'to serve at any school in the Kumasi Metropolitan area.\n\n'
            'Thank you for your consideration.\n\n'
            'Yours faithfully,\n'
            'Kwame Mensah\n'
            'Staff ID: GES/GT/2018/05432'
        ),
        'is_sample': True,
    },
    {
        'title': 'Application for Leave of Absence',
        'category': 'leave',
        'status': 'final',
        'recipient_name': 'The Headmaster/Headmistress',
        'recipient_title': 'Adenta Community Junior High School',
        'sender_name': 'Abena Osei',
        'sender_title': 'Class Teacher, Basic 8',
        'school_name': 'Adenta Community Junior High School',
        'district': 'Adentan Municipal',
        'region': 'Greater Accra',
        'reference_number': 'GES/ADM/LV/2025/018',
        'date_written': date(2025, 4, 2),
        'body': (
            'Dear Sir/Madam,\n\n'
            'APPLICATION FOR LEAVE OF ABSENCE (5 WORKING DAYS)\n\n'
            'I write to formally request permission for a leave of absence from Monday 14th April '
            'to Friday 18th April 2025 (5 working days).\n\n'
            'The leave is required for a scheduled medical procedure at Korle Bu Teaching Hospital. '
            'I have enclosed a medical report from my physician confirming the need for the procedure '
            'and the expected recovery period.\n\n'
            'In my absence, I have arranged with Mr. Daniel Tetteh (Basic 9 Class Teacher) to cover '
            'my lessons. I have prepared detailed lesson notes and materials for the week.\n\n'
            'I assure you that all pending assignments and assessments have been marked and submitted '
            'to the academic office.\n\n'
            'Thank you for your understanding.\n\n'
            'Yours faithfully,\n'
            'Abena Osei\n'
            'Staff ID: GES/GT/2019/07891'
        ),
        'is_sample': True,
    },
]


# ── Report Card Writer Sample ────────────────────────────────────────────────

_REPORT_CARD_SET = {
    'set': {
        'title': 'Basic 7A \u2014 First Term Report Cards (Sample)',
        'class_name': 'Basic 7A',
        'term': 'first',
        'academic_year': '2025/2026',
        'school_name': 'SchoolPadi Demo Junior High School',
    },
    'entries': [
        {
            'student_name': 'Ama Serwaa Mensah',
            'subjects': [
                {'subject': 'Mathematics', 'class_score': 38, 'exam_score': 52, 'total': 90, 'grade': '1', 'remark': 'Excellent'},
                {'subject': 'English Language', 'class_score': 35, 'exam_score': 48, 'total': 83, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'Integrated Science', 'class_score': 36, 'exam_score': 50, 'total': 86, 'grade': '1', 'remark': 'Excellent'},
                {'subject': 'Social Studies', 'class_score': 34, 'exam_score': 45, 'total': 79, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'Computing (ICT)', 'class_score': 40, 'exam_score': 55, 'total': 95, 'grade': '1', 'remark': 'Excellent'},
            ],
            'overall_score': 86.6, 'overall_grade': '1', 'position': 1, 'total_students': 35,
            'conduct': 'excellent', 'attitude': 'excellent', 'interest': 'excellent',
            'attendance': '58/60',
            'class_teacher_comment': 'An outstanding start to the year! Ama consistently leads the class in all subjects. Her enthusiasm and dedication are exemplary.',
            'head_teacher_comment': 'Impressive performance. Keep up the excellent work.',
            'promoted': True, 'next_class': 'Basic 7A',
        },
        {
            'student_name': 'Kweku Asante Boateng',
            'subjects': [
                {'subject': 'Mathematics', 'class_score': 30, 'exam_score': 42, 'total': 72, 'grade': '3', 'remark': 'Good'},
                {'subject': 'English Language', 'class_score': 32, 'exam_score': 40, 'total': 72, 'grade': '3', 'remark': 'Good'},
                {'subject': 'Integrated Science', 'class_score': 28, 'exam_score': 38, 'total': 66, 'grade': '3', 'remark': 'Good'},
                {'subject': 'Social Studies', 'class_score': 35, 'exam_score': 46, 'total': 81, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'Computing (ICT)', 'class_score': 30, 'exam_score': 35, 'total': 65, 'grade': '4', 'remark': 'Satisfactory'},
            ],
            'overall_score': 71.2, 'overall_grade': '3', 'position': 8, 'total_students': 35,
            'conduct': 'good', 'attitude': 'good', 'interest': 'very_good',
            'attendance': '55/60',
            'class_teacher_comment': 'Kweku shows strong ability in Social Studies. Needs to improve focus in Computing and Science. Regular revision will help.',
            'head_teacher_comment': 'Good effort. There is room for improvement.',
            'promoted': True, 'next_class': 'Basic 7A',
        },
        {
            'student_name': 'Nana Adwoa Frimpong',
            'subjects': [
                {'subject': 'Mathematics', 'class_score': 25, 'exam_score': 30, 'total': 55, 'grade': '5', 'remark': 'Fail'},
                {'subject': 'English Language', 'class_score': 30, 'exam_score': 35, 'total': 65, 'grade': '4', 'remark': 'Satisfactory'},
                {'subject': 'Integrated Science', 'class_score': 27, 'exam_score': 32, 'total': 59, 'grade': '5', 'remark': 'Fail'},
                {'subject': 'Social Studies', 'class_score': 28, 'exam_score': 36, 'total': 64, 'grade': '4', 'remark': 'Satisfactory'},
                {'subject': 'Computing (ICT)', 'class_score': 26, 'exam_score': 30, 'total': 56, 'grade': '5', 'remark': 'Fail'},
            ],
            'overall_score': 59.8, 'overall_grade': '5', 'position': 28, 'total_students': 35,
            'conduct': 'good', 'attitude': 'satisfactory', 'interest': 'needs_improvement',
            'attendance': '45/60',
            'class_teacher_comment': 'Nana Adwoa is a quiet student who can do much better. Attendance must improve \u2014 she missed 15 days this term. Extra tuition recommended in Maths and Science.',
            'head_teacher_comment': 'Must attend school regularly. Parents should monitor homework.',
            'promoted': True, 'next_class': 'Basic 7A',
        },
        {
            'student_name': 'Yaw Owusu Darko',
            'subjects': [
                {'subject': 'Mathematics', 'class_score': 35, 'exam_score': 48, 'total': 83, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'English Language', 'class_score': 28, 'exam_score': 35, 'total': 63, 'grade': '4', 'remark': 'Satisfactory'},
                {'subject': 'Integrated Science', 'class_score': 33, 'exam_score': 44, 'total': 77, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'Social Studies', 'class_score': 30, 'exam_score': 38, 'total': 68, 'grade': '3', 'remark': 'Good'},
                {'subject': 'Computing (ICT)', 'class_score': 36, 'exam_score': 50, 'total': 86, 'grade': '1', 'remark': 'Excellent'},
            ],
            'overall_score': 75.4, 'overall_grade': '2', 'position': 5, 'total_students': 35,
            'conduct': 'very_good', 'attitude': 'very_good', 'interest': 'excellent',
            'attendance': '57/60',
            'class_teacher_comment': 'Yaw excels in Mathematics and Computing. English Language needs attention \u2014 encourage more reading at home.',
            'head_teacher_comment': 'A promising student. Work on English Language skills.',
            'promoted': True, 'next_class': 'Basic 7A',
        },
        {
            'student_name': 'Akua Konadu Appiah',
            'subjects': [
                {'subject': 'Mathematics', 'class_score': 32, 'exam_score': 43, 'total': 75, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'English Language', 'class_score': 36, 'exam_score': 50, 'total': 86, 'grade': '1', 'remark': 'Excellent'},
                {'subject': 'Integrated Science', 'class_score': 30, 'exam_score': 40, 'total': 70, 'grade': '3', 'remark': 'Good'},
                {'subject': 'Social Studies', 'class_score': 33, 'exam_score': 42, 'total': 75, 'grade': '2', 'remark': 'Very Good'},
                {'subject': 'Computing (ICT)', 'class_score': 30, 'exam_score': 38, 'total': 68, 'grade': '3', 'remark': 'Good'},
            ],
            'overall_score': 74.8, 'overall_grade': '2', 'position': 6, 'total_students': 35,
            'conduct': 'excellent', 'attitude': 'very_good', 'interest': 'very_good',
            'attendance': '59/60',
            'class_teacher_comment': 'Akua is the best English Language student in the class. She is well-behaved and helps others. Keep up the good work.',
            'head_teacher_comment': 'Excellent conduct and very good results. Well done.',
            'promoted': True, 'next_class': 'Basic 7A',
        },
    ],
}


# ── Paper Marker Sample ──────────────────────────────────────────────────────

_PAPER_MARKER_SAMPLE = {
    'session': {
        'title': 'B7 Maths Mid-Term Test \u2014 Sample Marking',
        'subject': 'Mathematics',
        'class_name': 'Basic 7',
        'total_questions': 10,
        'options_per_question': 4,
        'answer_key': ['B', 'A', 'C', 'D', 'A', 'B', 'C', 'A', 'D', 'B'],
    },
    'students': [
        {
            'student_name': 'Kofi Mensah',
            'student_index': 'B7/001',
            'responses': ['B', 'A', 'C', 'D', 'A', 'B', 'C', 'A', 'D', 'B'],
            'score': 10, 'total': 10, 'percentage': 100.0,
        },
        {
            'student_name': 'Esi Asante',
            'student_index': 'B7/002',
            'responses': ['B', 'C', 'C', 'D', 'B', 'B', 'A', 'A', 'D', 'B'],
            'score': 7, 'total': 10, 'percentage': 70.0,
        },
        {
            'student_name': 'Yaw Frimpong',
            'student_index': 'B7/003',
            'responses': ['A', 'A', 'B', 'D', 'A', 'C', 'C', 'B', 'A', 'B'],
            'score': 5, 'total': 10, 'percentage': 50.0,
        },
    ],
}


# ── Per-tool seeding (called on subscription activation) ─────────────────────

def seed_tool_content(profile, slug):
    """Seed sample content for a specific tool. Idempotent: safe to call multiple times."""
    if profile.role != 'teacher':
        return

    try:
        _TOOL_SEEDERS.get(slug, lambda p: None)(profile)
    except Exception:
        logger.exception('Failed to seed %s content for %s', slug, profile)


def _seed_computhink(profile):
    from individual_users.models import CompuThinkActivity
    for item in _COMPUTHINK_SAMPLES:
        if not CompuThinkActivity.objects.filter(profile=profile, title=item['title']).exists():
            CompuThinkActivity.objects.create(profile=profile, **item)


def _seed_literacy(profile):
    from individual_users.models import LiteracyExercise
    for item in _LITERACY_SAMPLES:
        if not LiteracyExercise.objects.filter(profile=profile, title=item['title']).exists():
            LiteracyExercise.objects.create(profile=profile, **item)


def _seed_citizen_ed(profile):
    from individual_users.models import CitizenEdActivity
    for item in _CITIZEN_ED_SAMPLES:
        if not CitizenEdActivity.objects.filter(profile=profile, title=item['title']).exists():
            CitizenEdActivity.objects.create(profile=profile, **item)


def _seed_tvet(profile):
    from individual_users.models import TVETProject
    for item in _TVET_SAMPLES:
        if not TVETProject.objects.filter(profile=profile, title=item['title']).exists():
            TVETProject.objects.create(profile=profile, **item)


def _seed_letters(profile):
    from individual_users.models import GESLetter
    for item in _LETTER_SAMPLES:
        if not GESLetter.objects.filter(profile=profile, title=item['title']).exists():
            GESLetter.objects.create(profile=profile, **item)


def _seed_report_cards(profile):
    from individual_users.models import ReportCardSet, ReportCardEntry
    set_data = _REPORT_CARD_SET['set']
    if not ReportCardSet.objects.filter(profile=profile, title=set_data['title']).exists():
        card_set = ReportCardSet.objects.create(profile=profile, **set_data)
        ReportCardEntry.objects.bulk_create([
            ReportCardEntry(card_set=card_set, **entry)
            for entry in _REPORT_CARD_SET['entries']
        ])


def _seed_paper_marker(profile):
    from individual_users.models import MarkingSession, StudentMark
    sess_data = _PAPER_MARKER_SAMPLE['session']
    if not MarkingSession.objects.filter(profile=profile, title=sess_data['title']).exists():
        session = MarkingSession.objects.create(profile=profile, **sess_data)
        StudentMark.objects.bulk_create([
            StudentMark(session=session, **s)
            for s in _PAPER_MARKER_SAMPLE['students']
        ])


def _seed_lesson_plans(profile):
    from individual_users.models import ToolLessonPlan
    for plan_data in _LESSON_PLANS:
        if not ToolLessonPlan.objects.filter(profile=profile, title=plan_data['title']).exists():
            ToolLessonPlan.objects.create(profile=profile, **plan_data)


def _seed_exam_generator(profile):
    from individual_users.models import ToolExamPaper, ToolQuestion
    q_objs = []
    for q_data in _QUESTIONS:
        q, _ = ToolQuestion.objects.get_or_create(
            profile=profile,
            question_text=q_data['question_text'],
            defaults=q_data,
        )
        q_objs.append(q)
    exam_title = 'Sample B7 Mid-Term Assessment'
    if not ToolExamPaper.objects.filter(profile=profile, title=exam_title).exists():
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


def _seed_slide_generator(profile):
    from individual_users.models import ToolPresentation, ToolSlide
    deck_meta = _DECK['presentation']
    if not ToolPresentation.objects.filter(profile=profile, title=deck_meta['title']).exists():
        pres = ToolPresentation.objects.create(profile=profile, **deck_meta)
        ToolSlide.objects.bulk_create([
            ToolSlide(presentation=pres, **slide)
            for slide in _DECK['slides']
        ])


# Slug → seeder function mapping
_TOOL_SEEDERS = {
    'computhink-lab': _seed_computhink,
    'literacy-toolkit': _seed_literacy,
    'citizen-ed': _seed_citizen_ed,
    'tvet-workshop': _seed_tvet,
    'letter-writer': _seed_letters,
    'report-card': _seed_report_cards,
    'paper-marker': _seed_paper_marker,
    'lesson-planner': _seed_lesson_plans,
    'exam-generator': _seed_exam_generator,
    'slide-generator': _seed_slide_generator,
}


# ── Public API ───────────────────────────────────────────────────────────────

def seed_starter_content(profile):
    """Create free subscriptions and sample content for a new teacher.

    Idempotent: skips any record that already exists (checks by title).
    Runs synchronously; typical wall-time < 150 ms (pure DB inserts).
    """
    if profile.role != 'teacher':
        return  # Only seed for teachers

    from individual_users.models import AddonSubscription

    try:
        # ── 1. Free addon subscriptions for ALL tools ────────────
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

        # ── 2. Seed sample content for each tool ─────────────────
        for slug, _name in _FREE_ADDONS:
            seed_tool_content(profile, slug)

        logger.info('Seeded starter content for %s', profile)

    except Exception:
        # Never break the signup flow if seeding fails
        logger.exception('Failed to seed starter content for %s', profile)
