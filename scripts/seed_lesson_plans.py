"""
Seed sample B7 weekly-style lesson plans with authentic GES indicator codes.
Run:  python scripts/seed_lesson_plans.py

Creates 8 lesson plans across multiple subjects for every IndividualProfile
that has an active 'lesson-planner' addon subscription.
"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.db import connection
connection.set_schema_to_public()

from individual_users.models import (
    AddonSubscription,
    IndividualProfile,
    ToolLessonPlan,
)

# ── Sample B7 Weekly Lesson Plans ─────────────────────────────────────────────
# Each entry maps directly to the ToolLessonPlan model fields + b7_meta JSON.
# Indicator codes follow the real Ghana Education Service (GES) coding scheme:
#   Subject-code  Strand.Sub-strand.Content-standard.Indicator
#   e.g. B7.1.1.1.2 → Basic 7, Strand 1, Sub-strand 1, CS 1, Indicator 2

SAMPLE_PLANS = [
    # ── 1. Mathematics: Number & Algebra ──────────────────────────────────────
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
            '2. Compare and order integers using the symbols <, > and =\n'
            '3. Add and subtract integers using the number line method'
        ),
        'materials': (
            'Number line chart (–20 to +20), integer flashcards, counters '
            '(red for negative, blue for positive), mini whiteboards, markers, '
            'GES Mathematics Curriculum for Basic 7'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Temperature Challenge"\n'
            '• Display temperatures of 5 cities: Accra (+32°C), London (+5°C), '
            'Moscow (–12°C), Cairo (+18°C), Oslo (–7°C)\n'
            '• Ask: "Which city is coldest? Which is warmest? '
            'How do you know?"\n'
            '• RPK: Elicit that numbers below zero are negative numbers.\n'
            '• Introduce the term "integer" — any whole number, positive, '
            'negative, or zero.\n'
            '• Write on board: ℤ = { … –3, –2, –1, 0, +1, +2, +3 … }'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Plotting Integers (15 min)\n'
            '• Draw a large number line on the board from –10 to +10.\n'
            '• Students come up in pairs to plot given integers.\n'
            '• Key teaching point: Numbers increase to the RIGHT, '
            'decrease to the LEFT.\n\n'
            'Activity 2: Comparing & Ordering (10 min)\n'
            '• Give each group a set of 10 integer cards.\n'
            '• Task: Arrange in ascending order, then in descending order.\n'
            '• Use <, > and = to write comparison statements.\n'
            '• Example: –5 < –2, +3 > –1, 0 > –4\n\n'
            'Activity 3: Adding Integers on the Number Line (15 min)\n'
            '• Demonstrate: (+3) + (–5) → Start at +3, move 5 steps left → –2\n'
            '• Demonstrate: (–2) + (–4) → Start at –2, move 4 steps left → –6\n'
            '• Practice: Students solve 8 addition problems using the '
            'number line on their mini whiteboards.\n'
            '• Check in pairs, then whole-class discussion of strategies.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Quick quiz (5 items): Plot, compare, and add integers.\n'
            '• Exit ticket: "Explain in your own words why –3 is greater '
            'than –7. Use the number line to support your answer."\n'
            '• Observation checklist: Can learners plot integers correctly? '
            'Can they add integers with unlike signs?'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Draw a number line from –15 to +15. Plot: –12, –7, 0, +4, +11\n'
            '2. Write 5 comparison statements using <, > or =\n'
            '3. Solve: (a) (+8) + (–3)  (b) (–6) + (+2)  (c) (–5) + (–4)  '
            '(d) (+7) + (–7)  (e) (–9) + (+12)\n'
            '4. Real-life task: Record the temperatures from 3 TV weather '
            'reports and order them from coldest to warmest.'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Class discussion: "What happens when you add two negative '
            'numbers? What about a positive and a negative?"\n'
            '• Summarise the rules discovered today.\n'
            '• Remediation: Pair struggling learners with confident peers '
            'for the homework task.\n'
            '• Extension: Challenge fast finishers to try subtraction of '
            'integers using the number line.'
        ),
        'b7_meta': {
            'period': '1',
            'duration': '60 Minutes',
            'strand': 'Number',
            'sub_strand': 'Number and Numeration Systems',
            'content_standard': (
                'B7.1.1.1 — Demonstrate understanding of the concept of '
                'integers including the position in the number system and '
                'perform operations on them'
            ),
            'indicator': (
                'B7.1.1.1.2 — Identify, compare, and order integers; '
                'add and subtract integers using the number line'
            ),
            'lesson_of': '1 of 3',
            'performance_indicator': (
                'Learners can correctly plot integers on a number line, '
                'compare them using inequality symbols, and add integers '
                'with unlike signs'
            ),
            'core_competencies': 'CP 5.1: Critical Thinking, CC 8.2: Collaboration, DL 6.3: Digital Literacy',
            'references': 'NaCCA Mathematics Curriculum for Basic 7 (2019), Strand 1',
            'keywords': 'integers, number line, positive, negative, compare, order, addition',
            'week_ending': '2026-01-16',
            'day': 'Monday',
            'class_size': '42',
        },
    },

    # ── 2. Mathematics: Geometry & Measurement ────────────────────────────────
    {
        'title': 'Properties of Triangles and Angle Relationships',
        'subject': 'mathematics',
        'target_class': 'Basic 7',
        'topic': 'Triangles',
        'indicator': 'B7.3.1.1.1',
        'sub_strand': 'Shapes and Space',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.3.1.1 — Demonstrate understanding of the '
            'properties of triangles.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Classify triangles by sides (scalene, isosceles, equilateral)\n'
            '2. Classify triangles by angles (acute, right, obtuse)\n'
            '3. Prove that interior angles of a triangle sum to 180°'
        ),
        'materials': (
            'Protractors, rulers, coloured card triangles (pre-cut), scissors, '
            'geoboard with rubber bands, GES Mathematics Curriculum, worksheet'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Triangle Hunt"\n'
            '• Show 6 images of real-world objects containing triangles '
            '(roof truss, road sign, sandwich half, bridge, hanger, slice of pizza).\n'
            '• Ask: "What shape do all of these share?"\n'
            '• RPK: What do we already know about triangles from Basic 6?\n'
            '• Elicit: 3 sides, 3 angles, closed figure.\n'
            '• Today\'s question: "Are all triangles the same? How can we tell them apart?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Classifying by Sides (12 min)\n'
            '• Distribute card triangles — 3 equilateral, 3 isosceles, 3 scalene per group.\n'
            '• Task: Measure all sides and sort into groups. Name each group.\n'
            '• Teach vocabulary: equilateral (3 equal sides), isosceles (2 equal), '
            'scalene (no equal sides).\n\n'
            'Activity 2: Classifying by Angles (12 min)\n'
            '• Use protractors to measure angles of the same 9 triangles.\n'
            '• Sort: acute (all < 90°), right (one = 90°), obtuse (one > 90°).\n'
            '• Key teaching point: A triangle can be BOTH isosceles AND right-angled.\n\n'
            'Activity 3: Angle Sum Property (16 min)\n'
            '• Each learner draws ANY triangle, cuts out the 3 corners, '
            'and arranges them on a straight line.\n'
            '• Discovery: They always form a straight angle (180°)!\n'
            '• Practice: Given 2 angles, calculate the third.\n'
            '  e.g. 65° + 48° + ? = 180° → ? = 67°'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Worksheet: 6 triangles — classify each by sides AND angles.\n'
            '• 4 missing-angle problems.\n'
            '• Peer exchange and mark.\n'
            '• Traffic light self-assessment (green/amber/red).'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Draw one equilateral, one isosceles, and one scalene triangle. '
            'Label all sides and angles.\n'
            '2. Find the missing angle: (a) 70°, 55°, ?  (b) 90°, 35°, ?  '
            '(c) 120°, 28°, ?\n'
            '3. Real-life task: Identify 3 triangles in your environment, '
            'sketch them, and classify by sides and angles.'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Gallery walk: Groups display their classified triangles.\n'
            '• Discussion: "Can a triangle have two right angles? Why or why not?"\n'
            '• Remediation: Provide templates for learners struggling with '
            'protractor use.\n'
            '• Extension: Introduce the concept of exterior angles for fast finishers.'
        ),
        'b7_meta': {
            'period': '3',
            'duration': '60 Minutes',
            'strand': 'Geometry and Measurement',
            'sub_strand': 'Shapes and Space',
            'content_standard': (
                'B7.3.1.1 — Demonstrate understanding of the properties '
                'of triangles and classify them'
            ),
            'indicator': (
                'B7.3.1.1.1 — Classify triangles according to their sides '
                'and angles; determine the angle sum property of a triangle'
            ),
            'lesson_of': '1 of 2',
            'performance_indicator': (
                'Learners can sort triangles into correct categories by '
                'sides and angles, and calculate a missing angle using '
                'the 180° rule'
            ),
            'core_competencies': 'CP 5.2: Problem Solving, CC 8.1: Collaboration, CI 6.8: Innovation',
            'references': 'NaCCA Mathematics Curriculum for Basic 7 (2019), Strand 3',
            'keywords': 'triangle, equilateral, isosceles, scalene, acute, right, obtuse, angle sum',
            'week_ending': '2026-02-06',
            'day': 'Wednesday',
            'class_size': '42',
        },
    },

    # ── 3. Integrated Science: Diversity of Matter ────────────────────────────
    {
        'title': 'Mixtures and Separation Techniques',
        'subject': 'science',
        'target_class': 'Basic 7',
        'topic': 'Mixtures',
        'indicator': 'B7.1.2.1.1',
        'sub_strand': 'Diversity of Matter',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.1.2.1 — Demonstrate knowledge and '
            'understanding of the concept of mixtures and how to separate '
            'them.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Distinguish between mixtures and pure substances\n'
            '2. Identify 4 methods of separating mixtures\n'
            '3. Select the appropriate separation technique for a given mixture'
        ),
        'materials': (
            'Sand, salt, water, iron filings, magnet, filter paper, funnel, '
            'beakers, petri dishes, methylated spirit, food colouring, '
            'chromatography paper strips, GES Integrated Science Curriculum'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Kitchen Chemistry"\n'
            '• Show a glass of garri soaked in water with groundnuts.\n'
            '• Ask: "Is this one substance or many? Can we separate them?"\n'
            '• RPK: Recall from Basic 6 — matter can be classified as elements, '
            'compounds, or mixtures.\n'
            '• Define mixture: Two or more substances physically combined, '
            'each keeping its own properties.\n'
            '• Today\'s question: "How do scientists separate mixtures?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Station Rotation — 4 Groups (10 min each):\n\n'
            'Station 1: Magnetic Separation\n'
            '• Mixture: sand + iron filings\n'
            '• Use a magnet wrapped in paper to extract iron filings.\n'
            '• Record observations in workbook.\n\n'
            'Station 2: Filtration\n'
            '• Mixture: sand + water\n'
            '• Set up funnel with filter paper over a beaker.\n'
            '• Pour mixture; observe residue and filtrate.\n\n'
            'Station 3: Evaporation\n'
            '• Mixture: salt + water (pre-prepared salt solution)\n'
            '• Heat gently in a petri dish on a hotplate (teacher demos).\n'
            '• Observe salt crystals forming as water evaporates.\n\n'
            'Station 4: Simple Chromatography\n'
            '• Place a dot of food colouring on chromatography paper.\n'
            '• Dip edge in water; watch colours separate.\n'
            '• Discuss: Some "colours" are actually mixtures of dyes.\n\n'
            'Class Synthesis (remaining time):\n'
            '• Each group presents their station findings.\n'
            '• Build class summary table: Mixture → Method → Principle.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Match-up activity: 5 mixtures → correct separation technique.\n'
            '• Short answer: "Why can\'t you use filtration to separate '
            'salt from water?"\n'
            '• Exit ticket: Name a mixture found at home and explain '
            'how you would separate it.'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Draw and label the filtration setup.\n'
            '2. Complete the table:\n'
            '   | Mixture | Method | Principle |\n'
            '   |---------|--------|-----------|\n'
            '   | Rice + stones | ? | ? |\n'
            '   | Ink (mixed dyes) | ? | ? |\n'
            '   | Oil + water | ? | ? |\n'
            '3. Research: What is distillation? When is it used?'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Group presentation of station findings.\n'
            '• Discussion: "Can all mixtures be separated? '
            'What about air — is it a mixture?"\n'
            '• Remediation: Provide illustrated step-by-step guides '
            'for learners who struggled at stations.\n'
            '• Extension: Introduce distillation and fractional distillation '
            'for petroleum.'
        ),
        'b7_meta': {
            'period': '2',
            'duration': '60 Minutes',
            'strand': 'Diversity of Matter',
            'sub_strand': 'Materials',
            'content_standard': (
                'B7.1.2.1 — Demonstrate knowledge and understanding of the '
                'concept of mixtures and how to separate them'
            ),
            'indicator': (
                'B7.1.2.1.1 — Classify materials into mixtures and pure '
                'substances and demonstrate methods of separating mixtures'
            ),
            'lesson_of': '2 of 3',
            'performance_indicator': (
                'Learners can identify types of mixtures and select the '
                'correct separation technique based on the properties of '
                'the components'
            ),
            'core_competencies': 'CP 5.3: Creativity, CC 8.1: Collaboration, DL 6.1: Digital Literacy',
            'references': 'NaCCA Integrated Science Curriculum for Basic 7 (2019), Strand 1',
            'keywords': 'mixture, filtration, evaporation, magnetic separation, chromatography, pure substance',
            'week_ending': '2026-01-23',
            'day': 'Tuesday',
            'class_size': '38',
        },
    },

    # ── 4. English Language: Grammar & Writing ────────────────────────────────
    {
        'title': 'Constructing Complex Sentences with Subordinate Clauses',
        'subject': 'english',
        'target_class': 'Basic 7',
        'topic': 'Complex Sentences',
        'indicator': 'B7.3.3.1.1',
        'sub_strand': 'Writing and Grammar Usage',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.3.3.1 — Demonstrate understanding of the '
            'structure of complex sentences.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify subordinate (dependent) clauses in sentences\n'
            '2. Use subordinating conjunctions (because, although, when, if, '
            'while, after, before, since) to join clauses\n'
            '3. Write at least 5 original complex sentences on a given topic'
        ),
        'materials': (
            'Sentence strips (main clauses and subordinate clauses), '
            'subordinating conjunction word cards, exercise books, '
            'GES English Language Curriculum, chart paper, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Sentence Upgrade"\n'
            '• Write on board: "I stayed home." and "It was raining."\n'
            '• Ask: "How can we combine these into ONE sentence?"\n'
            '• Accept responses: "I stayed home because it was raining."\n'
            '• RPK: In Basic 6, we learned compound sentences (and, but, or). '
            'Today we take the next step.\n'
            '• Introduce: A COMPLEX sentence has a main clause + a '
            'subordinate clause joined by a subordinating conjunction.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Identifying Clauses (12 min)\n'
            '• Display 8 sentences. Learners underline the main clause '
            'and circle the subordinate clause.\n'
            '• e.g. "Although he was tired, he finished his homework."\n'
            '  Main: he finished his homework\n'
            '  Subordinate: Although he was tired\n'
            '• Key rule: A subordinate clause CANNOT stand alone.\n\n'
            'Activity 2: Conjunction Matching (10 min)\n'
            '• Distribute sentence strips — main clauses on blue cards, '
            'subordinate clauses on yellow cards.\n'
            '• Groups match pairs and choose the correct conjunction.\n'
            '• Examples: "She passed the exam" + "she studied hard" '
            '→ "She passed the exam because she studied hard."\n\n'
            'Activity 3: Guided Writing (18 min)\n'
            '• Topic: "My School"\n'
            '• Each learner writes 5 complex sentences using at least '
            '3 different subordinating conjunctions.\n'
            '• Peer review: Exchange books and check if each sentence '
            'has a main clause + subordinate clause.\n'
            '• Volunteers share best sentences; class evaluates together.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Transform 5 pairs of simple sentences into complex sentences.\n'
            '• Identify the subordinating conjunction in 5 given sentences.\n'
            '• Write a short paragraph (5–7 sentences) about "A Rainy Day" '
            'using at least 3 complex sentences (underline them).'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Rewrite these pairs as complex sentences using the conjunction '
            'in brackets:\n'
            '   (a) The children played outside. It was dark. (until)\n'
            '   (b) She smiled. She saw her friend. (when)\n'
            '   (c) He bought a new book. He had saved enough money. (after)\n'
            '2. Write a diary entry (8–10 sentences) about your weekend. '
            'Include at least 4 complex sentences. Underline each subordinate clause.\n'
            '3. Find 3 complex sentences in any newspaper or storybook. '
            'Copy them and identify the conjunction.'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Volunteers read their "My School" paragraphs aloud.\n'
            '• Class gives feedback: Is the subordinate clause correct? '
            'Is the conjunction appropriate?\n'
            '• Quick oral quiz: Teacher says a conjunction, learners '
            'create a sentence on the spot.\n'
            '• Remediation: Provide a conjunction reference card for '
            'struggling learners.\n'
            '• Extension: Introduce adverbial clauses of time, reason, '
            'and condition.'
        ),
        'b7_meta': {
            'period': '4',
            'duration': '60 Minutes',
            'strand': 'Writing',
            'sub_strand': 'Grammar Usage',
            'content_standard': (
                'B7.3.3.1 — Demonstrate understanding of the structure '
                'of complex sentences and use subordinating conjunctions'
            ),
            'indicator': (
                'B7.3.3.1.1 — Construct complex sentences using '
                'subordinating conjunctions to express relationships '
                'between ideas'
            ),
            'lesson_of': '1 of 2',
            'performance_indicator': (
                'Learners can identify subordinate clauses and write '
                'original complex sentences with appropriate conjunctions'
            ),
            'core_competencies': 'CC 8.3: Communication, CP 5.1: Critical Thinking, CI 6.8: Creativity',
            'references': 'NaCCA English Language Curriculum for Basic 7 (2019), Strand 3',
            'keywords': 'complex sentence, subordinate clause, main clause, subordinating conjunction, because, although, when',
            'week_ending': '2026-02-13',
            'day': 'Thursday',
            'class_size': '40',
        },
    },

    # ── 5. Social Studies: Governance & Civic Life ────────────────────────────
    {
        'title': 'The Arms of Government and Their Functions',
        'subject': 'social_studies',
        'target_class': 'Basic 7',
        'topic': 'Arms of Government',
        'indicator': 'B7.4.2.1.1',
        'sub_strand': 'Governance, Politics and Stability',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.4.2.1 — Demonstrate understanding of the '
            'arms of government and how they work together.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Name the three arms of government\n'
            '2. State the main function of each arm\n'
            '3. Explain the concept of separation of powers and its '
            'importance for democracy'
        ),
        'materials': (
            'Chart showing the 3 arms of government, 1992 Constitution '
            '(simplified extracts), role cards for simulation, Social Studies '
            'Curriculum, projector (optional)'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Who Does What?"\n'
            '• Read a short scenario: "A new law says all students must '
            'wear helmets to school. Who made this law? Who enforces it? '
            'Who decides if it is fair?"\n'
            '• Accept answers; introduce the idea that different groups '
            'handle different parts of running a country.\n'
            '• RPK: From Basic 6, recall the meaning of government.\n'
            '• Today\'s question: "Why is it important that one person or '
            'group does NOT have all the power?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: The Three Arms (15 min)\n'
            '• Teach using a chart:\n'
            '  1. LEGISLATURE (Parliament) — Makes laws\n'
            '  2. EXECUTIVE (President & Ministers) — Implements laws\n'
            '  3. JUDICIARY (Courts) — Interprets laws\n'
            '• In Ghana: Parliament (275 MPs), President & Cabinet, '
            'Supreme Court & lower courts.\n'
            '• Discussion: Why do we separate these powers?\n\n'
            'Activity 2: Role-Play Simulation (15 min)\n'
            '• Divide class into 3 groups — Legislature, Executive, Judiciary.\n'
            '• Scenario: "Should schools open on Saturdays?"\n'
            '• Legislature debates and passes a "bill."\n'
            '• Executive signs it and plans implementation.\n'
            '• Judiciary receives a "challenge" from a citizen and '
            'decides whether the bill is constitutional.\n\n'
            'Activity 3: Checks & Balances (10 min)\n'
            '• Explain: Each arm can check the others.\n'
            '  – Parliament can impeach the President\n'
            '  – The President can veto a bill\n'
            '  – The Supreme Court can declare a law unconstitutional\n'
            '• Draw a triangle diagram showing the checks between arms.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Fill-in table: Arm | Leader in Ghana | Main Function\n'
            '• True/False quiz (6 items): e.g. "The Judiciary makes laws" '
            '→ False.\n'
            '• Group task: Write 3 reasons why separation of powers '
            'is important.'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Draw and label the "Checks & Balances Triangle" in your '
            'exercise book.\n'
            '2. Name the current (a) President of Ghana, (b) Speaker of '
            'Parliament, (c) Chief Justice.\n'
            '3. Write a short paragraph (6–8 sentences): "What would '
            'happen if one arm of government had all the power?"'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Debrief the role-play: Which arm did your group play? '
            'What was easy/difficult?\n'
            '• Key takeaway: Separation of powers prevents tyranny '
            'and protects citizens\' rights.\n'
            '• Remediation: Provide a labelled diagram for learners '
            'who struggled with vocabulary.\n'
            '• Extension: Research the role of the Council of State.'
        ),
        'b7_meta': {
            'period': '5',
            'duration': '60 Minutes',
            'strand': 'Governance, Politics and Stability',
            'sub_strand': 'Being a Leader',
            'content_standard': (
                'B7.4.2.1 — Demonstrate understanding of the arms of '
                'government and the concept of separation of powers'
            ),
            'indicator': (
                'B7.4.2.1.1 — Identify the three arms of government; '
                'explain their functions and the importance of separation '
                'of powers'
            ),
            'lesson_of': '1 of 2',
            'performance_indicator': (
                'Learners can name the 3 arms of government, state '
                'their functions, and explain checks and balances'
            ),
            'core_competencies': 'CC 8.4: Citizenship, CP 5.1: Critical Thinking, CC 8.1: Collaboration',
            'references': 'NaCCA Social Studies Curriculum for Basic 7 (2019), Strand 4',
            'keywords': 'legislature, executive, judiciary, separation of powers, parliament, constitution, checks and balances',
            'week_ending': '2026-03-06',
            'day': 'Monday',
            'class_size': '45',
        },
    },

    # ── 6. Computing / ICT: Introduction to Algorithms ────────────────────────
    {
        'title': 'Designing Algorithms with Flowcharts',
        'subject': 'computing',
        'target_class': 'Basic 7',
        'topic': 'Algorithms and Flowcharts',
        'indicator': 'B7.3.1.1.1',
        'sub_strand': 'Computational Thinking',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.3.1.1 — Demonstrate understanding of the '
            'concept of algorithms and use flowcharts to represent them.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Define "algorithm" and give real-life examples\n'
            '2. Identify the standard flowchart symbols (oval, rectangle, '
            'diamond, parallelogram, arrow)\n'
            '3. Draw a flowchart for a simple everyday process'
        ),
        'materials': (
            'Flowchart symbol chart, A3 paper, coloured markers, '
            'stencil shapes (optional), GES Computing Curriculum, '
            'projector, sample flowchart printouts'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "How to Make Indomie"\n'
            '• Ask a volunteer: "Tell us, step by step, how to make '
            'Indomie noodles."\n'
            '• Write the steps on the board as the student dictates.\n'
            '• Ask: "What happens if we do step 3 before step 1?"\n'
            '• Key idea: The ORDER of steps matters.\n'
            '• Define ALGORITHM: A step-by-step procedure to solve '
            'a problem or complete a task.\n'
            '• Today we learn how to draw these steps as a FLOWCHART.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Flowchart Symbols (10 min)\n'
            '• Teach the 5 standard symbols:\n'
            '  🔵 Oval — Start / End\n'
            '  🟦 Rectangle — Process (an action)\n'
            '  🔷 Diamond — Decision (Yes/No question)\n'
            '  ▱ Parallelogram — Input / Output\n'
            '  → Arrow — Flow direction\n'
            '• Students copy the symbol chart into their books.\n\n'
            'Activity 2: Guided Flowchart (15 min)\n'
            '• Together, draw the "Making Indomie" algorithm as a flowchart:\n'
            '  Start → Boil water → Add seasoning → Add noodles → '
            '  Cook for 3 min → Is it soft? (Decision) → Yes: Serve → End\n'
            '                                        → No: Cook 1 more min (loop back)\n'
            '• Emphasise: The diamond (decision) creates a BRANCH.\n\n'
            'Activity 3: Group Flowcharts (15 min)\n'
            '• Each group gets a different task:\n'
            '  – Group 1: Crossing the road safely\n'
            '  – Group 2: Buying credit on a mobile phone\n'
            '  – Group 3: Getting ready for school in the morning\n'
            '  – Group 4: Logging into a computer\n'
            '• Draw on A3 paper. Must include at least 1 decision box.\n'
            '• Present to class; peer feedback.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Label the 5 symbols from memory.\n'
            '• Trace through a given flowchart and write the output.\n'
            '• Spot-the-error: A flowchart with 2 deliberate mistakes '
            '(missing arrow, wrong symbol). Learners find and fix them.'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Draw a flowchart for "How to borrow a book from the '
            'school library." Include at least 1 decision symbol.\n'
            '2. Write the algorithm (numbered steps) for your flowchart.\n'
            '3. Think-ahead: Can a computer follow a flowchart? '
            'Write 3 sentences explaining your answer.'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Gallery walk: Groups display A3 flowcharts.\n'
            '• Vote for "Most Clear" and "Most Creative" flowchart.\n'
            '• Key takeaway: Algorithms are everywhere — cooking, '
            'directions, even getting dressed!\n'
            '• Remediation: Provide a flowchart template (pre-drawn '
            'shapes) for struggling learners.\n'
            '• Extension: Introduce pseudocode as another way to '
            'express algorithms.'
        ),
        'b7_meta': {
            'period': '6',
            'duration': '60 Minutes',
            'strand': 'Computational Thinking',
            'sub_strand': 'Algorithms',
            'content_standard': (
                'B7.3.1.1 — Demonstrate understanding of the concept '
                'of algorithms and use flowcharts to represent them'
            ),
            'indicator': (
                'B7.3.1.1.1 — Define algorithms and use standard '
                'flowchart symbols to represent step-by-step solutions '
                'to problems'
            ),
            'lesson_of': '1 of 3',
            'performance_indicator': (
                'Learners can identify flowchart symbols and draw '
                'a correct flowchart for a simple everyday process '
                'including at least one decision point'
            ),
            'core_competencies': 'CP 5.2: Problem Solving, DL 6.2: Digital Literacy, CI 6.8: Innovation',
            'references': 'NaCCA Computing Curriculum for Basic 7 (2019), Strand 3',
            'keywords': 'algorithm, flowchart, decision, process, input, output, sequence, symbol',
            'week_ending': '2026-01-30',
            'day': 'Friday',
            'class_size': '36',
        },
    },

    # ── 7. RME: Religious & Moral Education ───────────────────────────────────
    {
        'title': 'Moral Teachings on Truthfulness and Honesty',
        'subject': 'rme',
        'target_class': 'Basic 7',
        'topic': 'Truthfulness',
        'indicator': 'B7.2.2.1.1',
        'sub_strand': 'Moral and Ethical Foundations',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.2.2.1 — Show understanding of the moral '
            'teachings on truthfulness from various religions and traditions.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. State what truthfulness means from Christian, Islamic, and '
            'traditional perspectives\n'
            '2. Narrate at least one story/parable about honesty from '
            'each tradition\n'
            '3. Explain the benefits of truthfulness to the individual '
            'and society'
        ),
        'materials': (
            'Bible (Exodus 20:16, Proverbs 12:22), Qur\'an (Surah 33:70, '
            'Surah 9:119), Akan proverb cards, role-play props, '
            'GES RME Curriculum, chart paper'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "The Broken Window"\n'
            '• Narrate a short story: Kofi accidentally breaks a school '
            'window while playing football. He has two choices — tell the '
            'truth or blame someone else.\n'
            '• Ask: "What should Kofi do? Why?"\n'
            '• Discuss: What makes telling the truth hard sometimes?\n'
            '• RPK: From Basic 6, we learned about the Ten Commandments '
            'and Islamic pillars of character.\n'
            '• Today\'s focus: What do different religions and traditions '
            'teach about truthfulness?'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Christian Teaching on Truth (12 min)\n'
            '• Read Exodus 20:16 — "You shall not bear false witness '
            'against your neighbour."\n'
            '• Read Proverbs 12:22 — "The Lord detests lying lips, but '
            'he delights in people who are trustworthy."\n'
            '• Story: Ananias and Sapphira (Acts 5:1–11) — consequences '
            'of lying to God.\n'
            '• Key lesson: Christianity teaches that truthfulness is '
            'a commandment from God.\n\n'
            'Activity 2: Islamic Teaching on Truth (12 min)\n'
            '• Read Surah 33:70 — "O you who believe! Be conscious of '
            'Allah and speak words straight to the point."\n'
            '• Read Surah 9:119 — "Be with those who are truthful."\n'
            '• Hadith: The Prophet (SAW) said, "Truthfulness leads to '
            'righteousness and righteousness leads to Paradise."\n'
            '• Key lesson: Islam places truthfulness as a core virtue '
            'and a path to Paradise.\n\n'
            'Activity 3: Traditional African Teaching (10 min)\n'
            '• Akan proverb: "Nokware mu na ade pa hyia" — It is in '
            'truth that good things are found.\n'
            '• Ewe proverb: "Nya ŋkɔ aƒe, ame kple aƒe" — Truth goes '
            'far, but meets the person at home.\n'
            '• Discuss how traditional societies used proverbs to teach '
            'children the importance of honesty.\n\n'
            'Activity 4: Role-Play (6 min)\n'
            '• 3 volunteers act out the "Broken Window" scenario — '
            'showing the truthful ending and the consequences of lying.\n'
            '• Class discusses which outcome is better and why.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Complete a table: Religion/Tradition | Teaching | Source\n'
            '• Short answer: Why is truthfulness important for trust '
            'in the community?\n'
            '• Group task: Create a poster with 3 "truthfulness tips" '
            'for the classroom wall.'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Write one story from any religion or tradition that '
            'teaches about truthfulness.\n'
            '2. Interview an elder at home: Ask about a traditional '
            'proverb on honesty. Write it down and explain its meaning.\n'
            '3. Reflection: Write about a time when telling the truth '
            'was difficult but the right thing to do (5–7 sentences).'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Debrief role-play: How did the "truthful Kofi" feel? '
            'How did others respond?\n'
            '• Class pledge: "I will strive to be truthful in my words '
            'and actions."\n'
            '• Remediation: Provide a summary handout with all 3 '
            'religious/traditional teachings.\n'
            '• Extension: Research honesty teachings in Buddhism or '
            'Hinduism for the next class.'
        ),
        'b7_meta': {
            'period': '2',
            'duration': '60 Minutes',
            'strand': 'Moral and Religious Foundations',
            'sub_strand': 'Moral Teachings',
            'content_standard': (
                'B7.2.2.1 — Show understanding of the moral teachings '
                'on truthfulness from various religions and traditions'
            ),
            'indicator': (
                'B7.2.2.1.1 — State the moral teachings on truthfulness '
                'from Christianity, Islam, and Traditional African religion; '
                'explain benefits of truthfulness'
            ),
            'lesson_of': '1 of 2',
            'performance_indicator': (
                'Learners can state and compare truthfulness teachings '
                'from at least 3 religious/cultural perspectives and '
                'relate them to everyday life'
            ),
            'core_competencies': 'CC 8.4: Citizenship, CP 5.1: Critical Thinking, CC 8.3: Communication',
            'references': 'NaCCA RME Curriculum for Basic 7 (2019), Strand 2',
            'keywords': 'truthfulness, honesty, commandment, proverb, morality, religion, virtue',
            'week_ending': '2026-02-20',
            'day': 'Tuesday',
            'class_size': '40',
        },
    },

    # ── 8. Creative Arts & Design: Visual Arts ────────────────────────────────
    {
        'title': 'Principles of Design — Balance and Emphasis',
        'subject': 'creative_arts',
        'target_class': 'Basic 7',
        'topic': 'Principles of Design',
        'indicator': 'B7.1.1.1.2',
        'sub_strand': 'Visual Arts',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.1.1.1 — Demonstrate understanding of the '
            'elements and principles of design.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Define and identify "balance" in artwork (symmetrical and '
            'asymmetrical)\n'
            '2. Define and identify "emphasis" (focal point) in artwork\n'
            '3. Create a simple composition demonstrating both principles'
        ),
        'materials': (
            'Drawing paper (A4), pencils, coloured pencils/crayons, '
            'printed examples of balanced and unbalanced compositions, '
            'GES Creative Arts Curriculum, ruler, scissors, glue, '
            'old magazines for collage'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Spot the Difference"\n'
            '• Show 2 posters: One is well-balanced with a clear focal point; '
            'the other is cluttered with no emphasis.\n'
            '• Ask: "Which poster catches your eye? Why?"\n'
            '• Discuss: Some artworks feel "right" and others feel "off."\n'
            '• RPK: Recall the elements of design (line, shape, colour, '
            'texture, form) from previous lessons.\n'
            '• Today: We learn the PRINCIPLES that organise these elements — '
            'specifically BALANCE and EMPHASIS.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Understanding Balance (12 min)\n'
            '• Symmetrical balance: Draw a butterfly — same on both '
            'sides of a centre line. Examples: Adinkra symbols, flags.\n'
            '• Asymmetrical balance: Different elements on each side, '
            'but visual "weight" is equal. Example: A large dark shape '
            'on the left, 3 small colourful shapes on the right.\n'
            '• Students fold paper in half and create a symmetrical design.\n\n'
            'Activity 2: Understanding Emphasis (12 min)\n'
            '• Emphasis = creating a FOCAL POINT — the first thing '
            'the viewer notices.\n'
            '• Techniques: contrast (bright colour on dull background), '
            'size (one large shape among small ones), isolation '
            '(placing the focal element apart from others).\n'
            '• Look at examples: Identify the focal point in 4 images.\n\n'
            'Activity 3: Create Your Composition (16 min)\n'
            '• Task: Create a drawing or collage titled "My Favourite Place."\n'
            '• Requirements:\n'
            '  – Use symmetrical OR asymmetrical balance\n'
            '  – Include a clear focal point (emphasis)\n'
            '  – Use at least 3 colours\n'
            '• Teacher circulates, asking students to explain their '
            'design choices.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n\n'
            '• Self-assessment: Students annotate their composition — '
            'label where balance and emphasis appear.\n'
            '• Peer review: Partner identifies the focal point and '
            'type of balance without being told.\n'
            '• Exit question: "How would removing the focal point '
            'change your artwork?"'
        ),
        'closure': (
            'HOMEWORK\n\n'
            '1. Find 2 examples of balance in your environment (buildings, '
            'fabric designs, nature). Sketch them and label the type.\n'
            '2. Find 1 advertisement or poster. Identify the focal point '
            'and explain how emphasis is achieved.\n'
            '3. Complete and colour your "My Favourite Place" composition '
            'if not finished in class.'
        ),
        'notes': (
            'PHASE 3 — REFLECTION (10 min)\n\n'
            '• Mini exhibition: Pin compositions on the board.\n'
            '• Class votes for "Best Balance" and "Strongest Focal Point."\n'
            '• Discussion: "Can an artwork have balance but no emphasis? '
            'What would it look like?"\n'
            '• Remediation: Provide a template with a pre-drawn grid '
            'for learners who struggled with composition layout.\n'
            '• Extension: Introduce the principle of rhythm/repetition '
            'using African textile patterns.'
        ),
        'b7_meta': {
            'period': '7',
            'duration': '60 Minutes',
            'strand': 'Visual Arts',
            'sub_strand': 'Elements and Principles of Design',
            'content_standard': (
                'B7.1.1.1 — Demonstrate understanding of the elements '
                'and principles of design'
            ),
            'indicator': (
                'B7.1.1.1.2 — Identify and apply the principles of '
                'balance (symmetrical and asymmetrical) and emphasis '
                '(focal point) in visual art compositions'
            ),
            'lesson_of': '2 of 4',
            'performance_indicator': (
                'Learners can identify balance and emphasis in existing '
                'artwork and create an original composition that '
                'demonstrates both principles'
            ),
            'core_competencies': 'CI 6.8: Creativity and Innovation, CP 5.3: Creative Thinking, CC 8.1: Collaboration',
            'references': 'NaCCA Creative Arts & Design Curriculum for Basic 7 (2019), Strand 1',
            'keywords': 'balance, symmetry, asymmetry, emphasis, focal point, composition, design principles',
            'week_ending': '2026-03-13',
            'day': 'Wednesday',
            'class_size': '38',
        },
    },
]


def seed(profile=None):
    """
    Create sample lesson plans for a given profile, or for ALL profiles
    that have an active lesson-planner subscription.
    """
    if profile:
        profiles = [profile]
    else:
        active_subs = AddonSubscription.objects.filter(
            addon_slug='lesson-planner', status='active',
        ).select_related('profile')
        profiles = [s.profile for s in active_subs]

    if not profiles:
        print("No profiles with active lesson-planner subscription found.")
        print("Falling back to all IndividualProfiles...")
        profiles = list(IndividualProfile.objects.all()[:5])

    if not profiles:
        print("No IndividualProfile objects exist. Create one first.")
        return

    total = 0
    for prof in profiles:
        print(f"\n{'='*60}")
        print(f"Profile: {prof.user.get_full_name() or prof.user.username}")
        print(f"{'='*60}")
        created = 0
        for plan_data in SAMPLE_PLANS:
            title = plan_data['title']
            # Skip if an identical title already exists for this profile
            if ToolLessonPlan.objects.filter(profile=prof, title=title).exists():
                print(f"  ⏭  Already exists: {title}")
                continue

            ToolLessonPlan.objects.create(profile=prof, **plan_data)
            print(f"  ✅  Created: {title}")
            created += 1

        print(f"  → {created} new lesson plans created")
        total += created

    print(f"\n{'='*60}")
    print(f"✅ Done! {total} lesson plans created across {len(profiles)} profile(s).")
    print("View them at: /u/tools/lesson-plans/")


if __name__ == '__main__':
    seed()
