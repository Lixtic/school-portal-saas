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
    # ── English Language ──────────────────────────────────────────────────
    {
        'title': 'Comprehension — Identifying Main Ideas and Supporting Details',
        'subject': 'english',
        'target_class': 'Basic 7',
        'topic': 'Reading Comprehension',
        'indicator': 'B7.2.1.1.1',
        'sub_strand': 'Reading',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.2.1.1 — Read and demonstrate '
            'understanding of a variety of texts.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify the main idea in a passage\n'
            '2. Locate supporting details that reinforce the main idea\n'
            '3. Summarise a passage in their own words'
        ),
        'materials': (
            'Short passage handouts (3 graded texts), highlighters, '
            'chart paper, markers, comprehension worksheet'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Headline Hunt"\n'
            '• Display 5 newspaper headlines on the board.\n'
            '• Ask: "What do you think each article is about?"\n'
            '• Explain that the headline captures the main idea — '
            'today we learn to find main ideas inside a passage.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Guided Reading (15 min)\n'
            '• Read passage aloud; students follow along.\n'
            '• Model: underline main idea sentence, circle supporting details.\n\n'
            'Activity 2: Pair Practice (15 min)\n'
            '• Pairs read a second passage and highlight main idea in yellow, '
            'supporting details in green.\n\n'
            'Activity 3: Summarisation (10 min)\n'
            '• Each pair writes a 2-sentence summary on chart paper.\n'
            '• Gallery walk to compare summaries.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Comprehension worksheet: 1 passage, 5 questions.\n'
            '• Exit ticket: "What is the difference between a main idea and a detail?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Read any short story and write the main idea in one sentence.\n'
            '2. List 3 supporting details from the story.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Reading',
            'sub_strand': 'Comprehension',
            'content_standard': 'B7.2.1.1',
            'indicator': 'B7.2.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Communication, Critical Thinking',
        },
    },
    # ── Social Studies ────────────────────────────────────────────────────
    {
        'title': 'The Environment — Physical Features of Ghana',
        'subject': 'social_studies',
        'target_class': 'Basic 7',
        'topic': 'Physical Features of Ghana',
        'indicator': 'B7.3.1.1.1',
        'sub_strand': 'The Environment',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.3.1.1 — Demonstrate knowledge of the '
            'physical features of Ghana.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify major physical features (rivers, mountains, plains)\n'
            '2. Locate at least 5 features on a map of Ghana\n'
            '3. Explain how physical features influence human activities'
        ),
        'materials': (
            'Map of Ghana (wall-size), atlas, coloured pins, '
            'physical features flashcards, chart paper'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Name That Landmark"\n'
            '• Show 5 photos: Lake Volta, Mt. Afadjato, Kakum Canopy Walk, '
            'Volta River, Accra Plains.\n'
            '• Students guess the feature and its location.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Map Work (15 min)\n'
            '• Groups label rivers, mountains, and plains on outline maps.\n\n'
            'Activity 2: Feature Cards (15 min)\n'
            '• Match feature cards (name + description) to correct regions.\n\n'
            'Activity 3: Class Discussion (10 min)\n'
            '• How does the Volta River affect farming and transport?\n'
            '• Why do people settle near rivers and fertile plains?'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Fill-in-the-blank map worksheet.\n'
            '• Exit ticket: "Name 2 ways physical features affect daily life."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw a sketch map of Ghana and label 5 physical features.\n'
            '2. Write 2 sentences about one feature near your community.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'The Environment',
            'sub_strand': 'Physical Features',
            'content_standard': 'B7.3.1.1',
            'indicator': 'B7.3.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Collaboration',
        },
    },
    # ── Computing / ICT ───────────────────────────────────────────────────
    {
        'title': 'Introduction to Computer Hardware Components',
        'subject': 'computing',
        'target_class': 'Basic 7',
        'topic': 'Computer Hardware',
        'indicator': 'B7.4.1.1.1',
        'sub_strand': 'Introduction to Computing',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.4.1.1 — Show understanding of '
            'the components of a computer system.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify input, output, storage, and processing devices\n'
            '2. State the function of at least 5 hardware components\n'
            '3. Classify peripherals into correct categories'
        ),
        'materials': (
            'Desktop computer (or labelled diagram), keyboard, mouse, '
            'monitor, CPU casing, motherboard poster, sorting worksheet'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "What Am I?"\n'
            '• Teacher describes a device: "I display images and text."\n'
            '• Students guess the component (monitor).\n'
            '• Repeat for 4 more components to build curiosity.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Explore & Label (15 min)\n'
            '• Groups examine real/photo components and label them.\n\n'
            'Activity 2: Classification (15 min)\n'
            '• Sort 12 hardware cards into Input, Output, Storage, Processing.\n\n'
            'Activity 3: Function Match (10 min)\n'
            '• Match component names to descriptions on a worksheet.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Quick quiz: Name 3 input devices, 2 output devices.\n'
            '• Exit ticket: "What is the function of the CPU?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw and label 6 computer hardware components.\n'
            '2. Explain the difference between input and output devices.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Introduction to Computing',
            'sub_strand': 'Hardware',
            'content_standard': 'B7.4.1.1',
            'indicator': 'B7.4.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Digital Literacy, Critical Thinking',
        },
    },
    # ── French ────────────────────────────────────────────────────────────
    {
        'title': 'Se Présenter — Introducing Yourself in French',
        'subject': 'french',
        'target_class': 'Basic 7',
        'topic': 'Self Introduction',
        'indicator': 'B7.5.1.1.1',
        'sub_strand': 'Oral Communication',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.5.1.1 — Use basic French expressions '
            'to introduce oneself.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Greet and respond to greetings in French\n'
            '2. State their name, age, and nationality\n'
            '3. Ask and answer simple personal questions'
        ),
        'materials': (
            'Flashcards with French phrases, audio clips (greetings), '
            'role-play cue cards, mini dialogue scripts, whiteboard'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Bonjour!"\n'
            '• Teacher greets the class in French; students repeat.\n'
            '• Play a short audio clip of a French self-introduction.\n'
            '• Ask: "What information did the speaker share?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Vocabulary Drill (15 min)\n'
            '• Teach: Je m\'appelle…, J\'ai … ans, Je suis…\n'
            '• Choral repetition and individual practice.\n\n'
            'Activity 2: Pair Dialogues (15 min)\n'
            '• Pairs use cue cards to role-play introductions.\n\n'
            'Activity 3: Class Presentation (10 min)\n'
            '• 5 volunteers introduce themselves to the class in French.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Listen-and-fill worksheet (complete missing words).\n'
            '• Exit ticket: Write 3 sentences introducing yourself in French.'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Write a 5-sentence self-introduction in French.\n'
            '2. Practise saying it aloud 3 times.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Oral Communication',
            'sub_strand': 'Self Introduction',
            'content_standard': 'B7.5.1.1',
            'indicator': 'B7.5.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Communication, Cultural Diversity',
        },
    },
    # ── Ghanaian Language ─────────────────────────────────────────────────
    {
        'title': 'Greetings and Everyday Expressions in Twi',
        'subject': 'ghanaian_language',
        'target_class': 'Basic 7',
        'topic': 'Greetings in Twi',
        'indicator': 'B7.6.1.1.1',
        'sub_strand': 'Listening and Speaking',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.6.1.1 — Use appropriate greetings '
            'and expressions in the Ghanaian language.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Greet elders, peers, and strangers appropriately in Twi\n'
            '2. Use at least 8 everyday expressions correctly\n'
            '3. Demonstrate cultural norms associated with greetings'
        ),
        'materials': (
            'Greeting phrase chart, audio recordings, role-play props '
            '(traditional cloth, stool), picture cards of greeting scenarios'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Maakye!"\n'
            '• Teacher enters and greets each row: Maakye, Maaha, Maadwo.\n'
            '• Students respond; discuss which greeting matches the time of day.\n'
            '• Ask: "Why do we greet differently at different times?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Phrase Building (15 min)\n'
            '• Teach 8 expressions with meanings and pronunciation.\n'
            '• Choral and individual repetition.\n\n'
            'Activity 2: Scenario Role-Play (15 min)\n'
            '• Groups act out: greeting a chief, meeting a friend, '
            'thanking a teacher.\n\n'
            'Activity 3: Cultural Context (10 min)\n'
            '• Discuss: Why do we use the right hand? Why bow to elders?'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Matching exercise: expression ↔ English meaning.\n'
            '• Exit ticket: "Greet your teacher as if it is morning, then evening."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Write 5 Twi greetings with their English meanings.\n'
            '2. Greet 3 family members in Twi and note their responses.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Listening and Speaking',
            'sub_strand': 'Greetings',
            'content_standard': 'B7.6.1.1',
            'indicator': 'B7.6.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Communication, Cultural Identity',
        },
    },
    # ── Religious & Moral Education ───────────────────────────────────────
    {
        'title': 'God as Creator — Respecting the Environment',
        'subject': 'rme',
        'target_class': 'Basic 7',
        'topic': 'God the Creator',
        'indicator': 'B7.7.1.1.1',
        'sub_strand': 'God and His Creation',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.7.1.1 — Show understanding of God as '
            'the creator and the need to care for creation.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Describe how different religions view God as Creator\n'
            '2. State 3 reasons why we should protect the environment\n'
            '3. Suggest practical ways to care for creation'
        ),
        'materials': (
            'Pictures of nature / environment, Bible, Quran, '
            'traditional proverbs chart, chart paper, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Beautiful World"\n'
            '• Show 5 pictures: sunrise, forest, river, animals, farm.\n'
            '• Ask: "Who made all these? How should we treat them?"\n'
            '• Introduce the concept of God as Creator across faiths.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Scriptural Exploration (15 min)\n'
            '• Read Genesis 1:1 (Christianity), Surah Al-Baqarah 2:164 '
            '(Islam), traditional Akan proverb about nature.\n\n'
            'Activity 2: Group Discussion (15 min)\n'
            '• Groups discuss: "What happens when we harm the environment?"\n'
            '• Each group presents 2 consequences.\n\n'
            'Activity 3: Action Plan (10 min)\n'
            '• Class creates a "Care for Creation" poster with 5 actions.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Short quiz: 5 True/False questions.\n'
            '• Exit ticket: "Name one thing you will do this week to care for creation."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Interview a parent about how they cared for the environment as children.\n'
            '2. Write a short paragraph on why God wants us to protect nature.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Religion and the Environment',
            'sub_strand': 'God and His Creation',
            'content_standard': 'B7.7.1.1',
            'indicator': 'B7.7.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Cultural Identity',
        },
    },
    # ── Creative Arts & Design ────────────────────────────────────────────
    {
        'title': 'Elements of Design — Line, Shape, and Colour',
        'subject': 'creative_arts',
        'target_class': 'Basic 7',
        'topic': 'Elements of Design',
        'indicator': 'B7.8.1.1.1',
        'sub_strand': 'Visual Arts',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.8.1.1 — Demonstrate understanding '
            'of the basic elements of visual arts.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify and describe line, shape, and colour\n'
            '2. Create a simple design using all three elements\n'
            '3. Explain how artists use these elements'
        ),
        'materials': (
            'Drawing paper, coloured pencils, crayons, ruler, '
            'examples of artworks (prints), element-of-design poster'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Art Around Us"\n'
            '• Show 4 images: Kente cloth, Adinkra symbol, '
            'a landscape painting, a logo.\n'
            '• Ask: "What lines, shapes, and colours do you see?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Element Exploration (15 min)\n'
            '• Teacher demonstrates types of lines (straight, curved, zigzag), '
            'basic shapes, and primary/secondary colours.\n\n'
            'Activity 2: Guided Practice (15 min)\n'
            '• Students create a pattern using 3 line types and 4 colours.\n\n'
            'Activity 3: Mini Gallery (10 min)\n'
            '• Display work; peers identify elements in each design.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Label-the-elements worksheet (identify lines, shapes, colours in an image).\n'
            '• Exit ticket: "Draw one straight, one curved, and one zigzag line."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Find 3 objects at home that show interesting lines and shapes. Sketch them.\n'
            '2. Colour your sketches using at least 4 different colours.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Visual Arts',
            'sub_strand': 'Elements of Design',
            'content_standard': 'B7.8.1.1',
            'indicator': 'B7.8.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Creativity, Communication',
        },
    },
    # ── Career Technology ─────────────────────────────────────────────────
    {
        'title': 'Career Awareness — Exploring Types of Occupations',
        'subject': 'career_tech',
        'target_class': 'Basic 7',
        'topic': 'Types of Occupations',
        'indicator': 'B7.9.1.1.1',
        'sub_strand': 'Career Awareness',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.9.1.1 — Show understanding of different '
            'types of occupations.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Classify occupations into primary, secondary, and tertiary sectors\n'
            '2. Name at least 3 occupations in each sector\n'
            '3. Relate their personal interests to possible career paths'
        ),
        'materials': (
            'Occupation picture cards, sector classification chart, '
            'career quiz handout, sticky notes, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "When I Grow Up"\n'
            '• Students write their dream job on a sticky note and place '
            'it on the board.\n'
            '• Group similar jobs together and ask: "What do these have in common?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Sector Classification (15 min)\n'
            '• Introduce primary (farming, fishing), secondary (manufacturing), '
            'tertiary (services) sectors.\n\n'
            'Activity 2: Card Sort (15 min)\n'
            '• Groups sort 15 occupation cards into the 3 sectors.\n\n'
            'Activity 3: Career Interest Quiz (10 min)\n'
            '• Students complete a short quiz to discover their interests.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Classification worksheet: place 10 jobs in the correct sector.\n'
            '• Exit ticket: "Name one job from each sector that interests you."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Interview a family member about their job: What sector is it?\n'
            '2. Write 3 sentences about a career you find interesting.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Career Technology',
            'sub_strand': 'Career Awareness',
            'content_standard': 'B7.9.1.1',
            'indicator': 'B7.9.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Personal Development',
        },
    },
    # ── History ───────────────────────────────────────────────────────────
    {
        'title': 'The Ancient Ghana Empire',
        'subject': 'history',
        'target_class': 'Basic 7',
        'topic': 'Ancient Ghana Empire',
        'indicator': 'B7.10.1.1.1',
        'sub_strand': 'Civilisations of Africa',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.10.1.1 — Demonstrate understanding of '
            'the rise, achievements, and fall of the Ancient Ghana Empire.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Describe the location and founding of the Ghana Empire\n'
            '2. State 3 key achievements (trade, governance, military)\n'
            '3. Explain factors that led to its decline'
        ),
        'materials': (
            'Map of ancient West Africa, timeline chart, picture cards '
            'of trade items (gold, salt), short primary source excerpt'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Gold and Salt"\n'
            '• Show a piece of salt and a gold-coloured item.\n'
            '• Ask: "Which is more valuable? Would you trade gold for salt?"\n'
            '• Introduce the Ghana Empire as the "Land of Gold."'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Location & Timeline (15 min)\n'
            '• Locate the Ghana Empire on a map (not modern Ghana).\n'
            '• Build a timeline: founding → peak → decline.\n\n'
            'Activity 2: Achievements Gallery (15 min)\n'
            '• Groups research one achievement and present to the class.\n\n'
            'Activity 3: Decline Discussion (10 min)\n'
            '• Discuss factors: Almoravid attacks, overgrazing, trade route shifts.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Fill-in-the-blank worksheet about the Ghana Empire.\n'
            '• Exit ticket: "Name 2 achievements and 1 reason for decline."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw a map showing the Ghana Empire and its trade routes.\n'
            '2. Write 4 sentences comparing the Ghana Empire to modern Ghana.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Civilisations',
            'sub_strand': 'Civilisations of Africa',
            'content_standard': 'B7.10.1.1',
            'indicator': 'B7.10.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Cultural Identity',
        },
    },
    # ── Geography ─────────────────────────────────────────────────────────
    {
        'title': 'Map Reading — Understanding Scale and Direction',
        'subject': 'geography',
        'target_class': 'Basic 7',
        'topic': 'Map Reading',
        'indicator': 'B7.11.1.1.1',
        'sub_strand': 'Map Skills',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: B7.11.1.1 — Demonstrate knowledge of '
            'basic map reading skills.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify the 4 cardinal and 4 intercardinal directions\n'
            '2. Use scale to calculate actual distance from map distance\n'
            '3. Interpret key/legend symbols on a topographic map'
        ),
        'materials': (
            'Compass, topographic map (local area), ruler, atlas, '
            'map symbols chart, scale conversion worksheet'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Find Your Way"\n'
            '• Blindfold a volunteer; classmates give directions using '
            'cardinal points to reach a chair.\n'
            '• Ask: "Why do explorers and travellers need maps?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Compass Points (10 min)\n'
            '• Teach 8 compass directions with body-movement drill.\n\n'
            'Activity 2: Scale Practice (15 min)\n'
            '• Demonstrate: 1 cm = 1 km. Students measure 5 distances on the map.\n\n'
            'Activity 3: Symbol Identification (15 min)\n'
            '• Groups list 10 symbols from the map and match to the legend.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Scale worksheet: calculate 5 real distances.\n'
            '• Exit ticket: "What does a blue line on a map represent?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw a simple map of your school compound with a key.\n'
            '2. Include a compass rose and a scale.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Map Skills',
            'sub_strand': 'Map Reading',
            'content_standard': 'B7.11.1.1',
            'indicator': 'B7.11.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Digital Literacy',
        },
    },
    # ── Physics ───────────────────────────────────────────────────────────
    {
        'title': 'Introduction to Motion — Speed, Distance, and Time',
        'subject': 'physics',
        'target_class': 'SHS 1',
        'topic': 'Linear Motion',
        'indicator': 'S1.P.1.1.1',
        'sub_strand': 'Mechanics',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.P.1.1 — Demonstrate understanding of '
            'the concepts of speed, velocity, and acceleration.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Define speed, distance, and time and state their SI units\n'
            '2. Calculate speed using the formula s = d/t\n'
            '3. Interpret distance-time graphs'
        ),
        'materials': (
            'Stopwatch, metre rule, toy car, ramp, graph paper, '
            'calculator, speed-formula poster'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Who Is Faster?"\n'
            '• Two students race 10 m; class records time with stopwatch.\n'
            '• Ask: "How do we know who is faster? What did we measure?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Concept Introduction (10 min)\n'
            '• Define speed = distance ÷ time. SI units: m/s, km/h.\n'
            '• Worked examples.\n\n'
            'Activity 2: Practical Measurement (15 min)\n'
            '• Groups roll a toy car down a ramp; measure distance and time.\n'
            '• Calculate speed for 3 trials.\n\n'
            'Activity 3: Graph Interpretation (15 min)\n'
            '• Plot distance-time graph from their data; identify rest and motion.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Solve 5 speed calculation problems.\n'
            '• Exit ticket: "A car travels 120 km in 2 hours. What is its speed?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Solve 8 problems involving speed, distance, and time.\n'
            '2. Draw a distance-time graph for a trip description provided.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Mechanics',
            'sub_strand': 'Linear Motion',
            'content_standard': 'S1.P.1.1',
            'indicator': 'S1.P.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Problem Solving',
        },
    },
    # ── Chemistry ─────────────────────────────────────────────────────────
    {
        'title': 'The Periodic Table — Groups and Periods',
        'subject': 'chemistry',
        'target_class': 'SHS 1',
        'topic': 'Periodic Table',
        'indicator': 'S1.C.1.1.1',
        'sub_strand': 'Atomic Structure',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.C.1.1 — Demonstrate knowledge of '
            'the arrangement of elements on the Periodic Table.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Describe the layout of the Periodic Table (groups & periods)\n'
            '2. Locate at least 10 common elements by symbol\n'
            '3. Explain trends in metallic character across a period'
        ),
        'materials': (
            'Large Periodic Table poster, element cards, blank table worksheet, '
            'coloured pencils, element sample set (Fe, Cu, Al, S)'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Element Bingo"\n'
            '• Students get bingo cards with element symbols.\n'
            '• Teacher calls names; first to complete a row wins.\n'
            '• Ask: "How are these elements organised?"'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Table Tour (15 min)\n'
            '• Walk through groups (1–18) and periods (1–7).\n'
            '• Highlight metals, non-metals, metalloids.\n\n'
            'Activity 2: Element Hunt (15 min)\n'
            '• Groups locate 10 elements and record group, period, type.\n\n'
            'Activity 3: Trend Discussion (10 min)\n'
            '• Why are Group 1 elements so reactive? Compare Na and K.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Blank table worksheet: fill in 15 elements.\n'
            '• Exit ticket: "Is Chlorine a metal or non-metal? Which group?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Memorise the first 20 elements (symbol, name, atomic number).\n'
            '2. Classify them as metals, non-metals, or metalloids.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Atomic Structure',
            'sub_strand': 'Periodic Table',
            'content_standard': 'S1.C.1.1',
            'indicator': 'S1.C.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Digital Literacy',
        },
    },
    # ── Biology ───────────────────────────────────────────────────────────
    {
        'title': 'Cell Structure — Plant and Animal Cells',
        'subject': 'biology',
        'target_class': 'SHS 1',
        'topic': 'Cell Structure',
        'indicator': 'S1.B.1.1.1',
        'sub_strand': 'Cell Biology',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.B.1.1 — Demonstrate understanding of '
            'the structure and function of plant and animal cells.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Draw and label a plant cell and an animal cell\n'
            '2. State the function of 5 cell organelles\n'
            '3. Compare and contrast plant and animal cells'
        ),
        'materials': (
            'Microscope, prepared slides (onion epidermis, cheek cells), '
            'cell model/poster, drawing paper, coloured pencils'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Building Blocks"\n'
            '• Show a brick wall photo. Ask: "What is a wall made of?"\n'
            '• Then: "What is your body made of?" → Introduce cells '
            'as the building blocks of life.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Microscope Observation (15 min)\n'
            '• View onion epidermis (plant) and cheek cells (animal).\n'
            '• Sketch what they see.\n\n'
            'Activity 2: Organelle Functions (15 min)\n'
            '• Label diagram: nucleus, cytoplasm, cell membrane, '
            'cell wall, chloroplast, mitochondria, vacuole.\n\n'
            'Activity 3: Venn Diagram (10 min)\n'
            '• Compare plant vs. animal cells using a Venn diagram.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Label-the-cell worksheet (10 structures).\n'
            '• Exit ticket: "Name 2 organelles found only in plant cells."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Draw, label, and colour a plant and an animal cell.\n'
            '2. Write the function of each labelled organelle.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Cell Biology',
            'sub_strand': 'Cell Structure',
            'content_standard': 'S1.B.1.1',
            'indicator': 'S1.B.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Observation',
        },
    },
    # ── Literature ────────────────────────────────────────────────────────
    {
        'title': 'Introduction to Prose — Elements of a Short Story',
        'subject': 'literature',
        'target_class': 'SHS 1',
        'topic': 'Elements of Prose',
        'indicator': 'S1.L.1.1.1',
        'sub_strand': 'Prose',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.L.1.1 — Analyse the key elements '
            'of prose fiction.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify setting, character, plot, theme, and point of view\n'
            '2. Analyse each element in a short story excerpt\n'
            '3. Write a brief critical response using literary terms'
        ),
        'materials': (
            'Short story excerpt (2 pages), element definition handout, '
            'chart paper, highlighters, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Story in 60 Seconds"\n'
            '• Teacher tells a very short story (Anansi tale).\n'
            '• Ask: "Where did it happen? Who was in it? What happened?"\n'
            '• Introduce the 5 elements of fiction.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Guided Reading (15 min)\n'
            '• Read excerpt together; model identifying setting and characters.\n\n'
            'Activity 2: Element Hunt (15 min)\n'
            '• Pairs find plot structure (exposition, rising action, climax, '
            'resolution), theme, and point of view.\n\n'
            'Activity 3: Group Presentation (10 min)\n'
            '• Each group presents one element with evidence from the text.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Element identification worksheet.\n'
            '• Exit ticket: "What is the difference between theme and plot?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Read a short story of your choice.\n'
            '2. Identify and write about each of the 5 elements.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Prose',
            'sub_strand': 'Elements of Fiction',
            'content_standard': 'S1.L.1.1',
            'indicator': 'S1.L.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Communication',
        },
    },
    # ── Economics ──────────────────────────────────────────────────────────
    {
        'title': 'Basic Economic Concepts — Scarcity and Choice',
        'subject': 'economics',
        'target_class': 'SHS 1',
        'topic': 'Scarcity and Choice',
        'indicator': 'S1.E.1.1.1',
        'sub_strand': 'Basic Economics',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.E.1.1 — Demonstrate understanding of '
            'the concept of scarcity, choice, and opportunity cost.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. Define scarcity, choice, and opportunity cost\n'
            '2. Give real-life examples of each concept\n'
            '3. Explain how scarcity forces individuals and nations to choose'
        ),
        'materials': (
            'Play money (GH¢50 per student), price list poster, '
            'decision-making scenario cards, chart paper'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "The GH¢50 Challenge"\n'
            '• Give each student GH¢50 play money and a list of 8 items '
            '(total: GH¢200).\n'
            '• Ask: "Can you buy everything? What will you give up?"\n'
            '• Introduce scarcity and choice.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Concept Building (15 min)\n'
            '• Define scarcity (unlimited wants, limited resources).\n'
            '• Define opportunity cost (next best alternative forgone).\n\n'
            'Activity 2: Scenario Analysis (15 min)\n'
            '• Groups solve scenario cards: "The government has GH¢10M — '
            'build a hospital or a road?"\n\n'
            'Activity 3: Class Debate (10 min)\n'
            '• Should Ghana spend more on education or health? Justify.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Define-and-apply worksheet (3 scenarios).\n'
            '• Exit ticket: "You chose to study instead of watching TV. '
            'What is the opportunity cost?"'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. List 3 choices you made today and identify the opportunity cost.\n'
            '2. Explain why scarcity is a problem for every country.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Basic Economics',
            'sub_strand': 'Scarcity and Choice',
            'content_standard': 'S1.E.1.1',
            'indicator': 'S1.E.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Problem Solving',
        },
    },
    # ── Government ────────────────────────────────────────────────────────
    {
        'title': 'The 1992 Constitution of Ghana — Fundamental Rights',
        'subject': 'government',
        'target_class': 'SHS 1',
        'topic': 'Fundamental Human Rights',
        'indicator': 'S1.G.1.1.1',
        'sub_strand': 'The Constitution',
        'duration_minutes': 60,
        'objectives': (
            'Content Standard: S1.G.1.1 — Demonstrate knowledge of '
            'the fundamental human rights and freedoms in the 1992 Constitution.\n\n'
            'By the end of the lesson, learners will be able to:\n'
            '1. List at least 5 fundamental human rights in Chapter 5\n'
            '2. Explain the importance of rights and responsibilities\n'
            '3. Identify situations where rights may be limited'
        ),
        'materials': (
            'Copy of 1992 Constitution (Chapter 5 extract), rights flashcards, '
            'case study handout, chart paper, markers'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Your Rights"\n'
            '• Ask: "What can nobody take away from you?"\n'
            '• Students brainstorm on sticky notes.\n'
            '• Introduce Chapter 5 of the 1992 Constitution.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Rights Exploration (15 min)\n'
            '• Read Articles 12–33; list rights on the board.\n'
            '• Categorise: civil, political, economic, social.\n\n'
            'Activity 2: Case Studies (15 min)\n'
            '• Groups analyse: "Is this a violation?" (3 scenarios).\n\n'
            'Activity 3: Rights vs. Responsibilities (10 min)\n'
            '• Discussion: "If you have a right to education, what is your '
            'responsibility?"'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Match-the-right worksheet (right → article number).\n'
            '• Exit ticket: "Name 2 rights and their corresponding responsibilities."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Read Articles 12–20 and summarise 3 rights in your own words.\n'
            '2. Give one example of how each right affects your daily life.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'The Constitution',
            'sub_strand': 'Fundamental Rights',
            'content_standard': 'S1.G.1.1',
            'indicator': 'S1.G.1.1.1',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Critical Thinking, Citizenship',
        },
    },
    # ── Other (General) ───────────────────────────────────────────────────
    {
        'title': 'Study Skills — Effective Note-Taking Strategies',
        'subject': 'other',
        'target_class': 'Basic 7',
        'topic': 'Note-Taking Strategies',
        'indicator': 'N/A',
        'sub_strand': 'Study Skills',
        'duration_minutes': 60,
        'objectives': (
            'By the end of the lesson, learners will be able to:\n'
            '1. Identify 3 note-taking methods (Cornell, outline, mind map)\n'
            '2. Apply the Cornell method to a short lecture passage\n'
            '3. Explain why good notes improve revision and retention'
        ),
        'materials': (
            'Cornell note template handout, sample lecture paragraph, '
            'mind map poster, coloured pens, A4 paper'
        ),
        'introduction': (
            'PHASE 1 — STARTER (10 min)\n\n'
            'Activity: "Can You Remember?"\n'
            '• Read a 1-minute passage aloud.\n'
            '• Students try to recall 5 key points without notes.\n'
            '• Then repeat with note-taking allowed — compare results.'
        ),
        'development': (
            'PHASE 2 — NEW LEARNING (40 min)\n\n'
            'Activity 1: Method Introduction (15 min)\n'
            '• Demonstrate Cornell (cue column, notes, summary), '
            'outline (headings + bullets), mind map (central idea + branches).\n\n'
            'Activity 2: Guided Practice (15 min)\n'
            '• Teacher reads a 3-minute passage; students take notes using Cornell.\n\n'
            'Activity 3: Comparison (10 min)\n'
            '• Pairs compare notes and fill gaps; discuss which method they prefer.'
        ),
        'assessment': (
            'FORMATIVE CHECK\n'
            '• Review student Cornell notes for completeness.\n'
            '• Exit ticket: "Name the 3 sections of a Cornell note page."'
        ),
        'closure': (
            'HOMEWORK\n'
            '1. Take Cornell notes during one lesson tomorrow.\n'
            '2. Write a summary section at the bottom of your notes.'
        ),
        'notes': 'Sample lesson plan — auto-generated for your starter workspace.',
        'b7_meta': {
            'strand': 'Study Skills',
            'sub_strand': 'Note-Taking',
            'content_standard': 'N/A',
            'indicator': 'N/A',
            'period': '1',
            'duration': '60 Minutes',
            'core_competencies': 'Personal Development, Critical Thinking',
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


# ── Sample Slide Decks ───────────────────────────────────────────────────────

_DECKS = [
    # ── 1. Mathematics — Fractions ────────────────────────────────────────
    {
        'presentation': {
            'title': 'Understanding Fractions — Parts of a Whole',
            'subject': 'mathematics',
            'target_class': 'Basic 7',
            'theme': 'aurora',
            'transition': 'slide',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Understanding Fractions',
                'content': 'Parts of a Whole\nBasic 7 Mathematics\nTerm 1, Week 4',
                'speaker_notes': 'Ask: "If I cut an orange into 4 equal parts and give you 1 piece, what fraction did you get?"',
                'emoji': '\U0001F34A',
            },
            {
                'order': 1, 'layout': 'bullets',
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
                'order': 2, 'layout': 'two_col',
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
                'order': 3, 'layout': 'bullets',
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
                'order': 4, 'layout': 'summary',
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
    },
    # ── 2. Science — The Water Cycle ──────────────────────────────────────
    {
        'presentation': {
            'title': 'The Water Cycle — Nature\'s Recycling System',
            'subject': 'science',
            'target_class': 'Basic 7',
            'theme': 'ocean',
            'transition': 'fade',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'The Water Cycle',
                'content': 'Nature\'s Recycling System\nBasic 7 Integrated Science\nTerm 1',
                'speaker_notes': 'Ask: "Where does rain come from? Where does it go?"',
                'emoji': '\U0001F4A7',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'The Four Stages',
                'content': (
                    'Evaporation — water heats up and becomes vapour\n'
                    'Condensation — vapour cools and forms clouds\n'
                    'Precipitation — water falls as rain, snow, or hail\n'
                    'Collection — water gathers in rivers, lakes, and oceans'
                ),
                'speaker_notes': 'Draw the cycle on the board as you explain each stage.',
                'emoji': '\u2601\uFE0F',
            },
            {
                'order': 2, 'layout': 'two_col',
                'title': 'Evaporation vs. Condensation',
                'content': (
                    'EVAPORATION:\nLiquid \u2192 Gas\nNeeds heat energy\nSun heats oceans & lakes\n'
                    '---\n'
                    'CONDENSATION:\nGas \u2192 Liquid\nReleases heat energy\nForms clouds & dew'
                ),
                'speaker_notes': 'Demo: breathe on a cold mirror to show condensation.',
                'emoji': '\U0001F321\uFE0F',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'Why the Water Cycle Matters',
                'content': (
                    'Provides fresh drinking water for communities\n'
                    'Supports agriculture and food production\n'
                    'Regulates the Earth\'s temperature\n'
                    'Replenishes rivers, lakes, and underground aquifers'
                ),
                'speaker_notes': 'Ask: "What happens to farming if the water cycle is disrupted?"',
                'emoji': '\U0001F30D',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'Water moves in a continuous cycle\n'
                    '4 stages: evaporation, condensation, precipitation, collection\n'
                    'The Sun drives the water cycle\n'
                    'Every drop of water you drink has been recycled millions of times'
                ),
                'speaker_notes': 'Assign homework: draw and label the water cycle.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 3. English — Parts of Speech ──────────────────────────────────────
    {
        'presentation': {
            'title': 'Parts of Speech — Building Blocks of Language',
            'subject': 'english',
            'target_class': 'Basic 7',
            'theme': 'coral',
            'transition': 'slide',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Parts of Speech',
                'content': 'Building Blocks of Language\nBasic 7 English\nTerm 1',
                'speaker_notes': 'Ask: "How many types of words do you think exist in English?"',
                'emoji': '\U0001F4DA',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'The 8 Parts of Speech',
                'content': (
                    'Noun — names a person, place, or thing (Ama, Accra, book)\n'
                    'Pronoun — replaces a noun (she, they, it)\n'
                    'Verb — shows action or state (run, is, eat)\n'
                    'Adjective — describes a noun (tall, red, beautiful)\n'
                    'Adverb — describes a verb (quickly, very, always)'
                ),
                'speaker_notes': 'Write one example of each on the board.',
                'emoji': '\U0001F4DD',
            },
            {
                'order': 2, 'layout': 'bullets',
                'title': 'More Parts of Speech',
                'content': (
                    'Preposition — shows position or direction (in, on, under, between)\n'
                    'Conjunction — joins words or clauses (and, but, or, because)\n'
                    'Interjection — expresses strong emotion (Wow! Oh! Ouch!)'
                ),
                'speaker_notes': 'Demonstrate prepositions using a book and a desk.',
                'emoji': '\U0001F517',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'Practice: Identify the Parts',
                'content': (
                    '1. The tall girl runs quickly. (article, adj, noun, verb, adverb)\n'
                    '2. Kofi and Ama eat banku in the kitchen.\n'
                    '3. Wow! She jumped over the fence bravely.\n'
                    '4. They are reading because the exam is tomorrow.'
                ),
                'speaker_notes': 'Students work in pairs to label each word.',
                'emoji': '\u270D\uFE0F',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    '8 parts of speech: noun, pronoun, verb, adjective, adverb, preposition, conjunction, interjection\n'
                    'Every word belongs to at least one category\n'
                    'Some words can be multiple parts depending on context\n'
                    'Understanding parts of speech helps you write better sentences'
                ),
                'speaker_notes': 'Homework: Find 2 examples of each part of speech in a newspaper article.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 4. Social Studies — Ghana\'s Independence ─────────────────────────
    {
        'presentation': {
            'title': 'Ghana\'s Road to Independence — 6th March 1957',
            'subject': 'social_studies',
            'target_class': 'Basic 8',
            'theme': 'midnight',
            'transition': 'fade',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Ghana\'s Independence',
                'content': '6th March 1957\nThe First Sub-Saharan African Nation to Gain Freedom',
                'speaker_notes': 'Play a few seconds of Nkrumah\'s midnight declaration speech if possible.',
                'emoji': '\U0001F1EC\U0001F1ED',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'Key Events on the Road to Independence',
                'content': (
                    '1947 — UGCC formed (Danquah, Nkrumah, others)\n'
                    '1948 — Ex-servicemen\'s march \u2192 Accra riots\n'
                    '1949 — Nkrumah forms CPP ("Self-Government Now!")\n'
                    '1950 — Positive Action campaign \u2192 Nkrumah imprisoned\n'
                    '1951 — CPP wins election; Nkrumah released'
                ),
                'speaker_notes': 'Timeline on board. Ask students to guess what each event led to.',
                'emoji': '\U0001F4C5',
            },
            {
                'order': 2, 'layout': 'quote',
                'title': 'Nkrumah\'s Famous Words',
                'content': '"At long last, the battle has ended! And thus Ghana, your beloved country, is free forever!"',
                'speaker_notes': 'Explain the emotional impact on the crowd at the Old Polo Grounds.',
                'emoji': '\U0001F399\uFE0F',
            },
            {
                'order': 3, 'layout': 'two_col',
                'title': 'Before vs. After Independence',
                'content': (
                    'BEFORE (Gold Coast):\nBritish colonial rule\nNo self-governance\nForced labour & taxation\n'
                    '---\n'
                    'AFTER (Ghana):\nSelf-governing republic\nOwn parliament & laws\nInspired other African nations'
                ),
                'speaker_notes': 'Discuss: "What changed for ordinary people?"',
                'emoji': '\u2696\uFE0F',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'Ghana became independent on 6 March 1957\n'
                    'Kwame Nkrumah led the independence movement\n'
                    'CPP\'s "Self-Government Now" mobilised the masses\n'
                    'Ghana was the FIRST sub-Saharan African nation to gain independence\n'
                    'This inspired liberation movements across Africa'
                ),
                'speaker_notes': 'Homework: Why is 6 March a public holiday? Write 5 sentences.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 5. Computing — Internet Safety ────────────────────────────────────
    {
        'presentation': {
            'title': 'Internet Safety — Staying Secure Online',
            'subject': 'computing',
            'target_class': 'Basic 8',
            'theme': 'slate',
            'transition': 'zoom',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Internet Safety',
                'content': 'Staying Secure Online\nBasic 8 Computing\nTerm 2',
                'speaker_notes': 'Ask: "Have you ever received a suspicious message online?"',
                'emoji': '\U0001F512',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'Common Online Dangers',
                'content': (
                    'Cyberbullying — harassment through digital platforms\n'
                    'Phishing — fake emails/messages that steal your info\n'
                    'Malware — harmful software that damages your device\n'
                    'Identity theft — someone steals and uses your personal data\n'
                    'Inappropriate content — material not suitable for your age'
                ),
                'speaker_notes': 'Show an example phishing email (with personal info redacted).',
                'emoji': '\u26A0\uFE0F',
            },
            {
                'order': 2, 'layout': 'bullets',
                'title': '5 Golden Rules of Internet Safety',
                'content': (
                    '1. Never share your password with anyone\n'
                    '2. Think before you click — verify links and senders\n'
                    '3. Keep personal information private (address, school, phone)\n'
                    '4. Tell a trusted adult if something feels wrong\n'
                    '5. Use strong passwords: mix letters, numbers, and symbols'
                ),
                'speaker_notes': 'Activity: assess if a password like "ama123" is strong or weak.',
                'emoji': '\U0001F6E1\uFE0F',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'What Makes a Strong Password?',
                'content': (
                    'At least 8 characters long\n'
                    'Mix uppercase and lowercase letters\n'
                    'Include numbers and symbols (!@#$)\n'
                    'NOT your name, birthday, or "password123"\n'
                    'Example: Gh@n@_2025_Safe!'
                ),
                'speaker_notes': 'Students create their own strong password and test it.',
                'emoji': '\U0001F511',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'The internet is powerful but has real dangers\n'
                    'Protect yourself: strong passwords, privacy, critical thinking\n'
                    'Never share personal data with strangers online\n'
                    'If in doubt, ask a trusted adult\n'
                    'Be kind online — no cyberbullying'
                ),
                'speaker_notes': 'Homework: create a poster on internet safety for younger students.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 6. RME — Moral Teachings ──────────────────────────────────────────
    {
        'presentation': {
            'title': 'Moral Teachings from World Religions',
            'subject': 'rme',
            'target_class': 'Basic 7',
            'theme': 'amber',
            'transition': 'slide',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Moral Teachings',
                'content': 'Common Values Across World Religions\nBasic 7 RME\nTerm 1',
                'speaker_notes': 'Ask: "Do all religions agree on what is right and wrong?"',
                'emoji': '\U0001F54C',
            },
            {
                'order': 1, 'layout': 'two_col',
                'title': 'The Golden Rule Across Faiths',
                'content': (
                    'CHRISTIANITY:\n"Do unto others as you would have them do unto you." — Matthew 7:12\n'
                    '---\n'
                    'ISLAM:\n"None of you truly believes until he wishes for his brother what he wishes for himself." — Hadith'
                ),
                'speaker_notes': 'Emphasise that the SAME principle appears in many traditions.',
                'emoji': '\u2764\uFE0F',
            },
            {
                'order': 2, 'layout': 'two_col',
                'title': 'More Golden Rules',
                'content': (
                    'AFRICAN TRADITIONAL:\n"I am because we are" (Ubuntu)\nCommunity over selfishness\n'
                    '---\n'
                    'HINDUISM:\n"This is the sum of duty: do not do to others what would cause pain if done to you." — Mahabharata'
                ),
                'speaker_notes': 'Ask: "How is Ubuntu practised in your community?"',
                'emoji': '\U0001F91D',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'Shared Moral Values',
                'content': (
                    'Honesty — all faiths condemn lying and deception\n'
                    'Respect for elders — universal across cultures\n'
                    'Kindness to others — charity, compassion, generosity\n'
                    'Justice — standing up for what is right\n'
                    'Forgiveness — letting go of anger and grudges'
                ),
                'speaker_notes': 'Students share a proverb from their own culture about one of these values.',
                'emoji': '\U0001F4D6',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'The Golden Rule appears in every major religion\n'
                    'Honesty, respect, kindness, justice, and forgiveness are universal\n'
                    'Different religions use different words for the same values\n'
                    'Living by these values builds peaceful communities'
                ),
                'speaker_notes': 'Homework: interview 2 people from different faiths about a shared value.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 7. Creative Arts — Adinkra Symbols ────────────────────────────────
    {
        'presentation': {
            'title': 'Adinkra Symbols — Art with Meaning',
            'subject': 'creative_arts',
            'target_class': 'Basic 7',
            'theme': 'forest',
            'transition': 'flip',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Adinkra Symbols',
                'content': 'Art with Meaning\nBasic 7 Creative Arts\nTerm 2',
                'speaker_notes': 'Show a piece of Adinkra cloth or a clear image of one.',
                'emoji': '\U0001F3A8',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'What Are Adinkra Symbols?',
                'content': (
                    'Visual symbols of the Akan people of Ghana\n'
                    'Each symbol represents a concept, proverb, or value\n'
                    'Originally stamped on cloth for funerals and ceremonies\n'
                    'Over 80 known symbols with unique meanings\n'
                    'Used today in art, fashion, architecture, and branding'
                ),
                'speaker_notes': 'Ask: "Have you seen any of these symbols before? Where?"',
                'emoji': '\U0001F310',
            },
            {
                'order': 2, 'layout': 'two_col',
                'title': '4 Famous Adinkra Symbols',
                'content': (
                    'GYE NYAME:\n"Except for God"\nSupremacy of God\n\n'
                    'SANKOFA:\n"Go back and get it"\nLearn from the past\n'
                    '---\n'
                    'DWENNIMMEN:\nRam\'s horns\nHumility with strength\n\n'
                    'AKOMA:\nHeart shape\nPatience and tolerance'
                ),
                'speaker_notes': 'Draw each symbol on the board as you explain the meaning.',
                'emoji': '\U0001F4A1',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'Create Your Own Adinkra Design',
                'content': (
                    '1. Choose 3 Adinkra symbols that are meaningful to you\n'
                    '2. Sketch them on paper with correct proportions\n'
                    '3. Arrange them into a repeating pattern\n'
                    '4. Use 2-3 colours to stamp or paint your design\n'
                    '5. Write the meaning of each symbol below your artwork'
                ),
                'speaker_notes': 'Provide stamp materials: foam, cardboard, and paint.',
                'emoji': '\u270D\uFE0F',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'Adinkra symbols carry deep cultural meaning\n'
                    '80+ symbols representing proverbs and values\n'
                    'Gye Nyame is the most popular symbol\n'
                    'Sankofa teaches us to learn from the past\n'
                    'You can use these symbols in modern art and design'
                ),
                'speaker_notes': 'Homework: Find 3 more Adinkra symbols and their meanings.',
                'emoji': '\u2705',
            },
        ],
    },
    # ── 8. Physics — Forces and Motion ────────────────────────────────────
    {
        'presentation': {
            'title': 'Forces and Motion — Push, Pull, and Everything In Between',
            'subject': 'physics',
            'target_class': 'SHS 1',
            'theme': 'rose',
            'transition': 'zoom',
        },
        'slides': [
            {
                'order': 0, 'layout': 'title',
                'title': 'Forces and Motion',
                'content': 'Push, Pull, and Everything In Between\nSHS 1 Physics\nTerm 1',
                'speaker_notes': 'Push a book across the desk. Ask: "What made it move? What made it stop?"',
                'emoji': '\U0001F680',
            },
            {
                'order': 1, 'layout': 'bullets',
                'title': 'What is a Force?',
                'content': (
                    'A force is a push or pull on an object\n'
                    'Measured in Newtons (N)\n'
                    'Forces can change speed, direction, or shape\n'
                    'Contact forces: friction, tension, normal force\n'
                    'Non-contact forces: gravity, magnetism, electrostatic'
                ),
                'speaker_notes': 'Demonstrate with a magnet and paper clips (non-contact force).',
                'emoji': '\U0001F9F2',
            },
            {
                'order': 2, 'layout': 'two_col',
                'title': 'Balanced vs. Unbalanced Forces',
                'content': (
                    'BALANCED (net force = 0):\nObject stays at rest or constant speed\n'
                    'Book on a table\nTug of war (equal teams)\n'
                    '---\n'
                    'UNBALANCED (net force \u2260 0):\nObject accelerates or decelerates\n'
                    'Kicking a football\nBraking a bicycle'
                ),
                'speaker_notes': 'Draw force arrows: equal and opposite for balanced, unequal for unbalanced.',
                'emoji': '\u2696\uFE0F',
            },
            {
                'order': 3, 'layout': 'bullets',
                'title': 'Newton\'s Three Laws of Motion',
                'content': (
                    '1st Law (Inertia): An object at rest stays at rest unless acted on by a force\n'
                    '2nd Law: F = ma (Force = mass \u00D7 acceleration)\n'
                    '3rd Law: Every action has an equal and opposite reaction\n'
                    'Example: You push the wall \u2192 the wall pushes you back'
                ),
                'speaker_notes': 'Demo: place a coin on a card over a glass, flick the card (1st law). ',
                'emoji': '\U0001F4D0',
            },
            {
                'order': 4, 'layout': 'summary',
                'title': 'Key Takeaways',
                'content': (
                    'Forces are pushes or pulls measured in Newtons\n'
                    'Balanced forces = no change in motion\n'
                    'Unbalanced forces = acceleration\n'
                    'Newton\'s 3 laws explain ALL motion\n'
                    'F = ma is the most important equation in mechanics'
                ),
                'speaker_notes': 'Homework: solve 5 F = ma problems.',
                'emoji': '\u2705',
            },
        ],
    },
]


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
    # ── 3. Pattern Recognition ────────────────────────────────────────────
    {
        'title': 'Number Patterns in Kente Weaving',
        'activity_type': 'pattern',
        'level': 'b7',
        'strand': 'Computational Thinking',
        'topic': 'Identifying repeating patterns in real-world artifacts',
        'instructions': (
            'Kente cloth uses repeating colour patterns. Study the sequences below '
            'and identify the rule that governs each pattern. Then predict the next 3 elements.'
        ),
        'content': {
            'problem': 'Find the pattern rule and predict the next 3 values in each sequence.',
            'steps': [
                'Sequence A: 2, 6, 18, 54, ___, ___, ___  (Hint: look at multiplication)',
                'Sequence B: Red, Gold, Green, Red, Gold, Green, ___, ___, ___',
                'Sequence C: 1, 1, 2, 3, 5, 8, ___, ___, ___  (Fibonacci)',
                'Sequence D: ABA, ABBA, ABBBA, ___, ___, ___',
            ],
            'hints': [
                'For Sequence A, divide each number by the previous one.',
                'Sequence B is a colour cycle — like threads in Kente.',
                'In Sequence C, each number is the SUM of the two before it.',
                'Sequence D adds one more B each time.',
            ],
            'expected_output': 'A: 162, 486, 1458. B: Red, Gold, Green. C: 13, 21, 34. D: ABBBBA, ABBBBBA, ABBBBBBA.',
            'extension': 'Design your own 4-colour Kente pattern using a repeating rule. Describe it in words.',
        },
        'answer_key': (
            'A: ×3 rule → 162, 486, 1458. B: 3-colour cycle. '
            'C: Fibonacci → 13, 21, 34. D: A + (n)B + A.'
        ),
    },
    # ── 4. Pseudocode Writing ─────────────────────────────────────────────
    {
        'title': 'ATM Cash Withdrawal — Writing Pseudocode',
        'activity_type': 'pseudocode',
        'level': 'b8',
        'strand': 'Computational Thinking',
        'topic': 'Writing pseudocode for everyday processes',
        'instructions': (
            'Write pseudocode (step-by-step instructions in plain English) for withdrawing '
            'money from an ATM machine. Include input validation, balance checks, and error handling.'
        ),
        'content': {
            'problem': 'Write pseudocode for an ATM withdrawal process.',
            'steps': [
                'START',
                'DISPLAY "Insert your card"',
                'INPUT card',
                'DISPLAY "Enter PIN"',
                'INPUT pin',
                'IF pin is wrong THEN DISPLAY "Incorrect PIN" and go to step 4',
                'IF 3 wrong attempts THEN DISPLAY "Card blocked" and STOP',
                'DISPLAY "Enter amount"',
                'INPUT amount',
                'IF amount > balance THEN DISPLAY "Insufficient funds"',
                'ELSE dispense amount, UPDATE balance',
                'DISPLAY "Take your cash and card"',
                'END',
            ],
            'hints': [
                'Think about what happens when the PIN is wrong (how many tries?).',
                'What if the person asks for more money than they have?',
                'What are the INPUTS? (card, pin, amount) What are the OUTPUTS? (cash, receipt)',
            ],
            'expected_output': 'A complete pseudocode with at least 10 steps including 2 IF/ELSE decisions.',
            'extension': 'Add a feature: ask the user if they want a receipt (Yes/No decision).',
        },
        'answer_key': (
            'Key decision points: PIN validation (max 3 attempts), '
            'balance check (amount ≤ balance), receipt option. '
            'Must include START, END, INPUT, OUTPUT, IF/ELSE.'
        ),
    },
    # ── 5. Abstraction ────────────────────────────────────────────────────
    {
        'title': 'Designing a School Map — What Details Matter?',
        'activity_type': 'abstraction',
        'level': 'b7',
        'strand': 'Computational Thinking',
        'topic': 'Abstraction: removing unnecessary details',
        'instructions': (
            'You are asked to draw a map of your school for a visitor. A photograph shows '
            'every detail — but a useful map only shows what matters. Decide which details '
            'to KEEP and which to REMOVE.'
        ),
        'content': {
            'problem': 'Create an abstract map of a school by including only essential information.',
            'steps': [
                'List 10 things you can see in a photograph of your school compound.',
                'Classify each item: ESSENTIAL (visitor needs it) or NON-ESSENTIAL.',
                'Essential examples: buildings, paths, gates, assembly ground, office.',
                'Non-essential examples: individual flowers, cracks in walls, bird nests.',
                'Draw a simplified map with only the essential items.',
                'Add labels and a key/legend.',
            ],
            'hints': [
                'Think about WHO will use the map and WHAT they need to find.',
                'A London Underground map removes geography but keeps connections — that is abstraction.',
                'In programming, abstraction hides complexity (you press "Call" without knowing how the phone works).',
            ],
            'expected_output': 'A labelled simplified school map with 6–10 essential features and a key.',
            'extension': 'Compare your map with a partner. Did you keep/remove the same things? Why?',
        },
        'answer_key': (
            'Abstraction removes unnecessary details while keeping essential features. '
            'A good school map: buildings, paths, gates, offices, toilets, assembly ground.'
        ),
    },
    # ── 6. Coding Challenge ───────────────────────────────────────────────
    {
        'title': 'Scratch Challenge — Build a Quiz App',
        'activity_type': 'coding',
        'level': 'b8',
        'strand': 'Programming',
        'topic': 'Using variables, loops, and conditionals in Scratch',
        'instructions': (
            'Create a 5-question quiz in Scratch. The program should ask a question, '
            'accept the user\'s answer, check if it is correct, keep score, '
            'and display the final result at the end.'
        ),
        'content': {
            'problem': 'Build a Scratch quiz with score tracking.',
            'steps': [
                'Create a variable called "score" and set it to 0.',
                'Ask question 1 using the ASK block. Store the answer.',
                'Use IF/ELSE: IF answer = correct THEN change score by 1, SAY "Correct!"',
                'ELSE SAY "Wrong! The answer is…"',
                'Repeat for 5 questions.',
                'After all questions, SAY "Your score is" + score + "/5".',
            ],
            'hints': [
                'Use the "ask ___ and wait" block for input.',
                'The answer is stored in the "answer" variable automatically.',
                'Use "join" to combine text with the score variable.',
            ],
            'expected_output': 'A working Scratch project: 5 questions, score out of 5 displayed at end.',
            'extension': 'Add a timer (10 seconds per question). If time runs out, count it as wrong.',
        },
        'answer_key': (
            'Blocks: when green flag clicked → set score to 0 → ask Q1 → '
            'if answer = "correct" change score by 1 → … → say join "Score: " score.'
        ),
    },
    # ── 7. AI Literacy ────────────────────────────────────────────────────
    {
        'title': 'Is This Written by AI or a Human?',
        'activity_type': 'ai_literacy',
        'level': 'b9',
        'strand': 'AI Literacy',
        'topic': 'Identifying AI-generated content',
        'instructions': (
            'Read 4 short paragraphs. Decide which were written by an AI and which by a human. '
            'Explain the clues that helped you decide. This activity builds critical thinking '
            'about AI-generated content.'
        ),
        'content': {
            'problem': 'Classify each paragraph as "AI-written" or "Human-written" and justify your choice.',
            'steps': [
                'Paragraph A: Perfectly structured, no personal opinion, generic examples → likely AI.',
                'Paragraph B: Includes spelling error, personal anecdote about grandmother → likely human.',
                'Paragraph C: Uses "It is important to note that…" repeatedly → common AI phrase.',
                'Paragraph D: References a specific local event with dates and names → likely human.',
            ],
            'hints': [
                'AI text is often very polished but generic — no personal stories.',
                'AI frequently uses phrases like "It is worth noting", "In conclusion".',
                'Humans make small errors, include emotions, and reference personal experiences.',
                'AI struggles with very recent or very local events.',
            ],
            'expected_output': 'Correct classification of all 4 paragraphs with at least 2 clues each.',
            'extension': 'Ask ChatGPT to write a paragraph, then try to improve it by adding personal voice.',
        },
        'answer_key': (
            'A: AI (generic, perfect structure). B: Human (personal anecdote, small error). '
            'C: AI (repetitive formal phrases). D: Human (specific local details).'
        ),
    },
    # ── 8. Digital Productivity ───────────────────────────────────────────
    {
        'title': 'Spreadsheet Challenge — School Canteen Budget',
        'activity_type': 'productivity',
        'level': 'b8',
        'strand': 'Digital Productivity',
        'topic': 'Using spreadsheets for budgeting and calculations',
        'instructions': (
            'The school canteen needs a weekly budget. Using a spreadsheet (Google Sheets or Excel), '
            'create a table of items, quantities, unit prices, and totals. Use formulas to calculate costs.'
        ),
        'content': {
            'problem': 'Create a canteen budget spreadsheet with formulas.',
            'steps': [
                'Column A: Item (rice, oil, tomatoes, fish, onions, charcoal, water, spices)',
                'Column B: Quantity needed per week',
                'Column C: Unit price in GHS',
                'Column D: Total cost = Quantity × Unit Price (use formula: =B2*C2)',
                'Row at bottom: GRAND TOTAL = SUM of all totals (use: =SUM(D2:D9))',
                'Add conditional formatting: highlight items over GHS 50 in red.',
            ],
            'hints': [
                'Always use formulas (=B2*C2) instead of typing the answer manually.',
                'SUM() adds a range of cells. AVERAGE() gives the mean.',
                'Format currency cells to 2 decimal places.',
            ],
            'expected_output': 'A spreadsheet with 8 items, formulas in column D, grand total, and conditional formatting.',
            'extension': 'Create a bar chart showing which items cost the most.',
        },
        'answer_key': (
            'Sample totals: rice GHS 120, oil GHS 85, tomatoes GHS 60, fish GHS 95, '
            'onions GHS 30, charcoal GHS 40, water GHS 25, spices GHS 15. Grand total: GHS 470.'
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
    # ── 3. Vocabulary Builder ─────────────────────────────────────────────
    {
        'title': 'Context Clues — Unlocking New Words',
        'exercise_type': 'vocabulary',
        'level': 'b7',
        'strand': 'Vocabulary',
        'topic': 'Using context clues to determine word meaning',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': 'Read each sentence and choose the best meaning for the underlined word.',
                    'sentences': [
                        'The *arid* land received no rain for six months. (a) fertile (b) dry (c) cold (d) green',
                        'Ama felt *elated* after winning the spelling bee. (a) sad (b) angry (c) very happy (d) tired',
                        'The chief *admonished* the youth for disrespecting the elders. (a) praised (b) warned (c) rewarded (d) ignored',
                        'Farmers use *irrigation* to water their crops during the dry season. (a) flooding (b) harvesting (c) artificial watering (d) planting',
                        'The teacher spoke in a *monotone* voice that made the students sleepy. (a) loud (b) exciting (c) unchanging tone (d) high-pitched',
                    ],
                    'answers': ['dry', 'very happy', 'warned', 'artificial watering', 'unchanging tone'],
                },
            ],
            'word_list': [
                {'word': 'arid', 'definition': 'Very dry with little or no rainfall'},
                {'word': 'elated', 'definition': 'Extremely happy and excited'},
                {'word': 'admonished', 'definition': 'Warned or reprimanded firmly'},
                {'word': 'irrigation', 'definition': 'Supplying water to land for crop production'},
                {'word': 'monotone', 'definition': 'A continuous sound that does not change in pitch'},
            ],
        },
        'answer_key': '1. dry  2. very happy  3. warned  4. artificial watering  5. unchanging tone',
    },
    # ── 4. Phonics / Remedial ─────────────────────────────────────────────
    {
        'title': 'Silent Letters — Know What You Cannot Hear',
        'exercise_type': 'phonics',
        'level': 'b7',
        'strand': 'Phonics',
        'topic': 'Identifying and spelling words with silent letters',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': 'Identify the SILENT letter in each word and write the word correctly.',
                    'sentences': [
                        'k-n-i-f-e → silent letter: ___',
                        'w-r-i-t-e → silent letter: ___',
                        'l-i-s-t-e-n → silent letter: ___',
                        'k-n-o-w → silent letter: ___',
                        'w-e-d-n-e-s-d-a-y → silent letter: ___',
                        'c-a-s-t-l-e → silent letter: ___',
                        'd-o-u-b-t → silent letter: ___',
                        'i-s-l-a-n-d → silent letter: ___',
                    ],
                    'answers': ['k', 'w', 't', 'k', 'd', 't', 'b', 's'],
                },
                {
                    'instruction': 'Use each word in a sentence that shows you understand its meaning.',
                    'sentences': [
                        'knife: ___',
                        'doubt: ___',
                        'island: ___',
                        'listen: ___',
                    ],
                    'answers': ['(student\'s own sentence)', '(student\'s own sentence)',
                                '(student\'s own sentence)', '(student\'s own sentence)'],
                },
            ],
            'rules_summary': (
                'Silent letters are letters we write but do not pronounce. '
                'Common patterns: kn- (know, knife), wr- (write, wrong), '
                '-bt (doubt, debt), -tle (castle, whistle), -sland (island).'
            ),
        },
        'answer_key': 'Silent letters: k, w, t, k, d, t, b, s. Sentences: open-ended.',
    },
    # ── 5. Essay / Creative Writing ───────────────────────────────────────
    {
        'title': 'Descriptive Writing — My Favourite Place',
        'exercise_type': 'essay',
        'level': 'b8',
        'strand': 'Writing',
        'topic': 'Descriptive essay using sensory language',
        'passage': '',
        'content': {
            'prompts': [
                {
                    'prompt': (
                        'Write a descriptive essay (200–250 words) about your favourite place. '
                        'Use at least 3 of the 5 senses (sight, sound, smell, taste, touch) to make '
                        'your reader FEEL like they are there.'
                    ),
                    'planning_guide': [
                        'Paragraph 1: Introduce the place — where is it? Why is it special?',
                        'Paragraph 2: Describe what you SEE and HEAR when you are there.',
                        'Paragraph 3: Describe smells, textures, or tastes you associate with the place.',
                        'Paragraph 4: Conclude — how does the place make you feel? Would you recommend it?',
                    ],
                },
            ],
            'rubric': {
                'Content & Ideas (10)': 'Clear description of a specific place with vivid details.',
                'Sensory Language (10)': 'At least 3 senses used effectively.',
                'Organisation (5)': 'Logical paragraph structure with introduction and conclusion.',
                'Language & Grammar (5)': 'Correct spelling, punctuation, and tense consistency.',
            },
            'example_opening': (
                'The beach at Busua stretches like a golden ribbon between the green forest and '
                'the endless blue sea. Every Saturday morning, I walk there barefoot, feeling the '
                'cool, damp sand push between my toes…'
            ),
        },
        'answer_key': 'Teacher-assessed using rubric. Total: 30 marks.',
    },
    # ── 6. Oral Language Activity ─────────────────────────────────────────
    {
        'title': 'Picture Story Narration — Tell Me What You See',
        'exercise_type': 'oral',
        'level': 'b7',
        'strand': 'Speaking',
        'topic': 'Oral narration using picture prompts',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': (
                        'Look at each picture description carefully. Tell a partner what is happening, '
                        'using at least 5 complete sentences. Speak clearly and use correct tenses.'
                    ),
                    'sentences': [
                        'Picture 1: A market woman selling tomatoes under a large umbrella while it rains.',
                        'Picture 2: Children playing football on a dusty field after school.',
                        'Picture 3: A fisherman mending his net by the seashore at dawn.',
                        'Picture 4: A grandmother telling a story to her grandchildren under a mango tree.',
                    ],
                    'answers': ['(student\'s oral narration — assessed by teacher/peer)',
                                '(student\'s oral narration)', '(student\'s oral narration)',
                                '(student\'s oral narration)'],
                },
            ],
            'rubric': {
                'Fluency (5)': 'Speaks without long pauses or hesitation.',
                'Vocabulary (5)': 'Uses descriptive words and varied vocabulary.',
                'Grammar (5)': 'Correct tense and subject-verb agreement.',
                'Creativity (5)': 'Adds imaginative details beyond what is shown.',
            },
        },
        'answer_key': 'Oral assessment — teacher uses rubric. Total: 20 marks per picture.',
    },
    # ── 7. Literature Study ───────────────────────────────────────────────
    {
        'title': 'Anansi and the Pot of Wisdom — Folktale Analysis',
        'exercise_type': 'literature',
        'level': 'b7',
        'strand': 'Literature',
        'topic': 'Analysing Ghanaian folktales',
        'passage': (
            '  Long ago, Anansi the Spider decided to collect all the wisdom in the world and keep it '
            'for himself. He gathered every piece of wisdom into a large clay pot.\n\n'
            'When the pot was full, Anansi decided to hide it at the top of the tallest tree in the '
            'forest. He tied the pot to his belly and began to climb. But the pot kept getting in the '
            'way, and he slipped again and again.\n\n'
            'His young son Ntikuma watched from below. "Father," the boy called, "why don\'t you tie '
            'the pot to your BACK instead of your belly?"\n\n'
            'Anansi realised that his son — a mere child — had wisdom that he had failed to collect. '
            'In frustration, he dropped the pot. It shattered on the ground, and the wisdom scattered '
            'to the four winds. That is why no one person has ALL the wisdom in the world.'
        ),
        'content': {
            'questions': [
                {
                    'question': 'What did Anansi want to do with all the wisdom?',
                    'options': ['Share it with everyone', 'Keep it for himself', 'Sell it at the market', 'Give it to the chief'],
                    'answer': 'Keep it for himself',
                },
                {
                    'question': 'Why did Anansi keep slipping while climbing the tree?',
                    'options': ['The tree was wet', 'The pot on his belly blocked him',
                                'He was too lazy', 'The wind was blowing'],
                    'answer': 'The pot on his belly blocked him',
                },
                {
                    'question': 'What lesson does the story teach?',
                    'options': ['Never climb trees', 'No one person can possess all wisdom',
                                'Children should not speak to elders', 'Anansi is very clever'],
                    'answer': 'No one person can possess all wisdom',
                },
            ],
            'literary_elements': {
                'Characters': 'Anansi (protagonist), Ntikuma (his son)',
                'Setting': 'A forest in Ashanti land, long ago',
                'Conflict': 'Anansi vs. his own greed — he wants all the wisdom',
                'Theme': 'Wisdom belongs to everyone; no one can monopolise knowledge',
                'Moral': 'Even the wisest person can learn from a child',
            },
            'tasks': [
                'Retell the story in your own words (at least 8 sentences).',
                'Draw a comic strip showing the beginning, middle, and end of the story.',
            ],
        },
        'answer_key': 'MCQ: 1. Keep it for himself  2. The pot blocked him  3. No one can possess all wisdom',
    },
    # ── 8. Comprehension (SHS level) ─────────────────────────────────────
    {
        'title': 'The Impact of Social Media on Youth — SHS Comprehension',
        'exercise_type': 'comprehension',
        'level': 'shs1',
        'strand': 'Reading',
        'topic': 'Critical reading of argumentative text',
        'passage': (
            '  Social media platforms such as Facebook, TikTok, and WhatsApp have become central '
            'to the lives of young Ghanaians. A 2024 survey by the National Communications Authority '
            'found that 78% of Ghanaians aged 15–24 use at least one social media platform daily.\n\n'
            'Proponents argue that social media democratises information, enables youth entrepreneurship, '
            'and provides a platform for civic engagement. During the 2024 elections, young voters used '
            'Twitter/X to fact-check political claims in real time.\n\n'
            'However, critics point to rising cyberbullying, misinformation, and shortened attention spans. '
            'A University of Ghana study found that students who spend more than 3 hours daily on social '
            'media scored 15% lower in standardised tests compared to peers who used it less.\n\n'
            'The challenge is not to ban social media but to teach digital literacy — helping young '
            'people distinguish credible sources from false ones and manage screen time responsibly.'
        ),
        'content': {
            'questions': [
                {
                    'question': 'According to the NCA survey, what percentage of youth use social media daily?',
                    'options': ['55%', '78%', '90%', '64%'],
                    'answer': '78%',
                },
                {
                    'question': 'Which argument SUPPORTS social media use among youth?',
                    'options': ['It causes cyberbullying', 'It shortens attention spans',
                                'It enables civic engagement', 'It lowers test scores'],
                    'answer': 'It enables civic engagement',
                },
                {
                    'question': 'What does the University of Ghana study suggest?',
                    'options': ['Social media should be banned', 'Excessive use hurts academic performance',
                                'All students use social media', 'Social media improves grades'],
                    'answer': 'Excessive use hurts academic performance',
                },
                {
                    'question': "What does the author mean by 'digital literacy'?",
                    'options': ['Being able to type fast', 'Knowing how to code',
                                'Distinguishing credible from false information online',
                                'Having many followers'],
                    'answer': 'Distinguishing credible from false information online',
                },
            ],
            'vocabulary_words': [
                {'word': 'democratises', 'definition': 'Makes accessible to everyone'},
                {'word': 'proponents', 'definition': 'People who support or advocate for something'},
                {'word': 'cyberbullying', 'definition': 'Using digital platforms to harass or intimidate'},
                {'word': 'misinformation', 'definition': 'False or inaccurate information spread unintentionally'},
            ],
        },
        'answer_key': '1. 78%  2. Civic engagement  3. Excessive use hurts academics  4. Distinguishing credible from false info',
    },
    # ── 9. Grammar (Advanced) ─────────────────────────────────────────────
    {
        'title': 'Active and Passive Voice — Transformations',
        'exercise_type': 'grammar',
        'level': 'b8',
        'strand': 'Grammar',
        'topic': 'Converting between active and passive voice',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': 'Rewrite each sentence in the PASSIVE voice.',
                    'sentences': [
                        'The farmer harvested the maize. → The maize ______.',
                        'The teacher praised Ama. → Ama ______.',
                        'The government built a new hospital. → A new hospital ______.',
                        'Lightning struck the mango tree. → The mango tree ______.',
                    ],
                    'answers': [
                        'was harvested by the farmer',
                        'was praised by the teacher',
                        'was built by the government',
                        'was struck by lightning',
                    ],
                },
                {
                    'instruction': 'Rewrite each sentence in the ACTIVE voice.',
                    'sentences': [
                        'The ball was kicked by Kwame. → Kwame ______.',
                        'The anthem was sung by the choir. → The choir ______.',
                        'The road was repaired by the workers. → The workers ______.',
                    ],
                    'answers': [
                        'kicked the ball',
                        'sang the anthem',
                        'repaired the road',
                    ],
                },
            ],
            'rules_summary': (
                'Active voice: Subject performs the action (The cat chased the mouse). '
                'Passive voice: Subject receives the action (The mouse was chased by the cat). '
                'Formula: Object + was/were + past participle + by + subject. '
                'Use passive when the action matters more than who did it.'
            ),
        },
        'answer_key': 'Passive: was harvested, was praised, was built, was struck. Active: kicked, sang, repaired.',
    },
    # ── 10. Vocabulary Builder (SHS) ──────────────────────────────────────
    {
        'title': 'Prefixes and Suffixes — Word Formation',
        'exercise_type': 'vocabulary',
        'level': 'shs1',
        'strand': 'Vocabulary',
        'topic': 'Using prefixes and suffixes to form new words',
        'passage': '',
        'content': {
            'exercises': [
                {
                    'instruction': 'Add the correct PREFIX to change the meaning of each word.',
                    'sentences': [
                        '___happy (opposite) → ______',
                        '___possible (not) → ______',
                        '___write (again) → ______',
                        '___national (between) → ______',
                        '___agree (opposite) → ______',
                    ],
                    'answers': ['unhappy', 'impossible', 'rewrite', 'international', 'disagree'],
                },
                {
                    'instruction': 'Add the correct SUFFIX to form a new word.',
                    'sentences': [
                        'teach + ___ (person who) → ______',
                        'care + ___ (full of) → ______',
                        'beauty + ___ (having quality) → ______',
                        'govern + ___ (institution) → ______',
                        'child + ___ (state of being) → ______',
                    ],
                    'answers': ['teacher', 'careful', 'beautiful', 'government', 'childhood'],
                },
            ],
            'word_list': [
                {'word': 'un-', 'definition': 'Prefix meaning "not" or "opposite"'},
                {'word': 'im-/in-', 'definition': 'Prefix meaning "not"'},
                {'word': 're-', 'definition': 'Prefix meaning "again"'},
                {'word': '-er/-or', 'definition': 'Suffix meaning "person who does"'},
                {'word': '-ful', 'definition': 'Suffix meaning "full of"'},
                {'word': '-ment', 'definition': 'Suffix meaning "result of action"'},
            ],
        },
        'answer_key': 'Prefixes: unhappy, impossible, rewrite, international, disagree. Suffixes: teacher, careful, beautiful, government, childhood.',
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
    # ── 3. Debate — Governance ────────────────────────────────────────────
    {
        'title': 'Should Ghana Lower the Voting Age to 16?',
        'activity_type': 'debate',
        'level': 'shs1',
        'strand': 'governance',
        'topic': 'Youth participation in democratic governance',
        'scenario_text': (
            'A proposal has been put before Parliament to amend Article 42 of the 1992 Constitution '
            'to lower the voting age from 18 to 16. Proponents argue that young people are affected '
            'by government policies (education, NHIS, employment) and should have a say. Opponents '
            'argue 16-year-olds lack the maturity and experience to make informed electoral decisions.'
        ),
        'content': {
            'questions': [
                'What does Article 42 of the 1992 Constitution say about the right to vote?',
                'Name two countries where 16-year-olds can already vote in national elections.',
                'What responsibilities come with the right to vote?',
                'How does civic education help young voters make informed choices?',
            ],
            'key_points': [
                'Democracy = government by the people. More inclusion strengthens legitimacy.',
                'Young people are the largest demographic in Ghana (~57% under 25).',
                'Right to vote is linked to age of criminal responsibility and tax-paying status.',
                'Civic education quality determines voter readiness more than age.',
                'Countries like Austria, Scotland, and Brazil allow voting at 16.',
            ],
            'tasks': [
                'Divide into FOR and AGAINST teams. Prepare 5-minute opening statements.',
                'Each side presents 3 evidence-based arguments.',
                'Cross-examination round: each side asks 2 questions to the other.',
                'Closing statements (2 min each). Class votes by secret ballot.',
            ],
        },
        'answer_guide': (
            'FOR: Youth are stakeholders, taxation without representation is unjust, '
            'earlier engagement builds lifelong civic habits, other democracies allow it. '
            'AGAINST: Brain development (prefrontal cortex) incomplete until ~25, '
            'susceptibility to manipulation, need to focus on education quality first.'
        ),
    },
    # ── 4. Map Activity — Globalism ───────────────────────────────────────
    {
        'title': 'Mapping Ghana\'s International Trade Partners',
        'activity_type': 'map_activity',
        'level': 'b9',
        'strand': 'globalism',
        'topic': 'Ghana\'s trade relationships and globalisation',
        'scenario_text': (
            'Ghana exports cocoa, gold, oil, and timber to countries worldwide, and imports '
            'machinery, vehicles, electronics, and pharmaceuticals. Use a world map to trace '
            'Ghana\'s major trade routes and understand how globalisation connects economies.'
        ),
        'content': {
            'questions': [
                'What are Ghana\'s top 3 export products by value?',
                'Name Ghana\'s top 5 trading partners (import and export).',
                'What is the meaning of "trade deficit" and does Ghana have one?',
                'How does the AfCFTA (African Continental Free Trade Area) affect Ghana?',
            ],
            'key_points': [
                'Ghana\'s top exports: gold (~$6.7B), crude oil (~$4B), cocoa (~$2B).',
                'Major export destinations: Switzerland, China, India, UAE, EU.',
                'Major import origins: China, USA, UK, Netherlands, India.',
                'Trade balance: Ghana often runs a deficit (imports > exports in value).',
                'AfCFTA HQ is in Accra — Ghana plays a key role in intra-Africa trade.',
            ],
            'tasks': [
                'On a blank world map, locate and label Ghana and its top 10 trade partners.',
                'Draw RED arrows from Ghana to export destinations. Label with the product.',
                'Draw BLUE arrows from import origins to Ghana. Label with the product.',
                'Calculate: If Ghana exports $14B and imports $16B, what is the trade balance?',
                'Write a paragraph: How would AfCFTA change the map of trade routes?',
            ],
        },
        'answer_guide': (
            'Trade balance = Exports - Imports = $14B - $16B = -$2B (deficit). '
            'AfCFTA would add more arrows within Africa (Nigeria, Côte d\'Ivoire, SA). '
            'Currently, most arrows go outside Africa (China, EU, India).'
        ),
    },
    # ── 5. Timeline — Culture ─────────────────────────────────────────────
    {
        'title': 'Timeline of Ghana\'s Cultural Milestones (1957–Present)',
        'activity_type': 'timeline',
        'level': 'b8',
        'strand': 'culture',
        'topic': 'Key cultural events and policies since independence',
        'scenario_text': (
            'Ghana\'s cultural identity has evolved since independence in 1957. From the establishment '
            'of the National Theatre to the Year of Return in 2019, cultural milestones reflect the '
            'nation\'s values, heritage, and global connections. Create a timeline of 10 key events.'
        ),
        'content': {
            'questions': [
                'Why was the National Theatre of Ghana established?',
                'What is the significance of the Year of Return (2019)?',
                'Name two UNESCO World Heritage Sites in Ghana.',
                'How does PANAFEST promote Pan-African cultural unity?',
            ],
            'key_points': [
                '1957: Independence — kente cloth and adinkra symbols gain international visibility.',
                '1963: Institute of African Studies, UG, established to study Ghanaian culture.',
                '1992: National Theatre complex opened in Accra.',
                '1992: PANAFEST (Pan-African Historical Theatre Festival) launched in Cape Coast.',
                '2001: National Commission on Culture Act establishes cultural policy framework.',
                '2006: Cape Coast and Elmina Castles become major heritage tourism sites.',
                '2019: Year of Return — 500,000+ diaspora visitors, $1.9B tourism revenue.',
                '2023: Beyond the Return — permanent diaspora engagement initiative.',
            ],
            'tasks': [
                'Create a visual timeline (horizontal or vertical) with 10 events from 1957 to 2024.',
                'For each event, write: date, event name, and one sentence about its significance.',
                'Illustrate at least 3 events with drawings or printed images.',
                'Write a reflection: Which event do you think had the most impact on Ghanaian identity? Why?',
            ],
        },
        'answer_guide': (
            'The timeline should span 1957–2024 with at least 10 events. '
            'Most impactful arguments often centre on Independence (1957) for political identity, '
            'or Year of Return (2019) for global cultural reconnection.'
        ),
    },
    # ── 6. Research Project — Environment ─────────────────────────────────
    {
        'title': 'Investigating Plastic Waste in Our Community',
        'activity_type': 'research',
        'level': 'b8',
        'strand': 'environment',
        'topic': 'Plastic pollution: causes, effects, and community solutions',
        'scenario_text': (
            'Ghana generates over 1 million tonnes of plastic waste annually, with only 5% recycled. '
            'Sachet water bags ("pure water") are the most visible form of plastic pollution. '
            'Conduct a community research project to investigate the scale of the problem locally '
            'and propose evidence-based solutions.'
        ),
        'content': {
            'questions': [
                'How many sachet water bags does your school community use per day?',
                'Where does most plastic waste in your area end up (landfill, drains, burning)?',
                'What health and environmental impacts does plastic pollution cause?',
                'What alternatives to single-use plastics are available locally?',
            ],
            'key_points': [
                'Ghana produces ~1.1 million tonnes of plastic waste/year; only ~5% is recycled.',
                'Plastic in drains causes flooding — major problem in Accra during rainy season.',
                'Burning plastic releases dioxins and furans — linked to cancer and respiratory disease.',
                'Sachet water production: ~270 million sachets/month consumed in Ghana.',
                'Solutions: deposit return schemes, refill stations, biodegradable alternatives.',
                'The National Plastics Management Policy (2020) sets framework for action.',
            ],
            'tasks': [
                'SURVEY: Count plastic items in your school compound (1 day). Record types and quantities.',
                'INTERVIEW: Ask 5 community members where they dispose of plastic waste.',
                'DATA ANALYSIS: Create a bar chart showing types and quantities of plastic found.',
                'SOLUTION PROPOSAL: Write a 1-page plan for reducing plastic waste at your school.',
                'PRESENTATION: Create a poster and present findings to the class.',
            ],
        },
        'answer_guide': (
            'Typical school findings: 200-500 sachet bags/day, 50-100 food wrappers. '
            'Most waste goes to open burning or drains. Key solutions: school recycling bin system, '
            'refillable water bottles, student-led clean-up campaigns, engaging local waste collectors.'
        ),
    },
    # ── 7. Values Clarification — Citizenship ─────────────────────────────
    {
        'title': 'Honesty vs. Loyalty — A Values Dilemma',
        'activity_type': 'values',
        'level': 'b7',
        'strand': 'citizenship',
        'topic': 'Resolving conflicts between personal values',
        'scenario_text': (
            'Your best friend confides that they cheated on the end-of-term maths exam by copying '
            'from a hidden phone. They scored 92% and are being praised by teachers and parents. '
            'You scored 78% honestly. Your friend begs you not to tell anyone. The teacher has '
            'announced that anyone with information about cheating should come forward.'
        ),
        'content': {
            'questions': [
                'What values are in conflict in this scenario? (honesty, loyalty, fairness, courage)',
                'What are the consequences of staying silent? For you? For your friend? For the class?',
                'What are the consequences of reporting? For you? For your friend?',
                'Is there a middle ground between full silence and full reporting?',
            ],
            'key_points': [
                'Honesty: telling the truth even when it is difficult.',
                'Loyalty: standing by people you care about.',
                'Fairness: everyone being treated equally and playing by the same rules.',
                'Courage: doing the right thing even when it scares you.',
                'Integrity: being consistent in your values regardless of the situation.',
                'A true friend helps you do the right thing, not cover up wrongdoing.',
            ],
            'tasks': [
                'JOURNAL: Write a private reflection on what you would do and why.',
                'ROLE PLAY: Act out 3 different responses: (a) tell the teacher, (b) stay silent, (c) talk to your friend first.',
                'FOUR CORNERS: Stand in the corner that matches your choice. Explain your reasoning.',
                'GROUP DISCUSSION: Is there ever a time when loyalty should override honesty?',
            ],
        },
        'answer_guide': (
            'No single "right" answer, but key reasoning: '
            'Staying silent makes you complicit and is unfair to honest students. '
            'Talking to the friend first (encouraging self-reporting) balances honesty and loyalty. '
            'Courage is needed regardless of the choice. The exam system\'s fairness depends on all '
            'participants following the rules.'
        ),
    },
    # ── 8. Case Study — Economics ─────────────────────────────────────────
    {
        'title': 'Mobile Money Revolution — Financial Inclusion in Ghana',
        'activity_type': 'case_study',
        'level': 'shs1',
        'strand': 'economics',
        'topic': 'Impact of mobile money on Ghana\'s economy and society',
        'scenario_text': (
            'Since MTN Mobile Money launched in 2009, Ghana has become one of the fastest-growing '
            'mobile money markets in Africa. By 2023, there were over 60 million registered accounts '
            '(in a country of 33 million people) processing over GHS 1.4 trillion annually. '
            'The E-Levy (Electronic Transfer Levy) of 2022 sparked nationwide debate.'
        ),
        'content': {
            'questions': [
                'How has mobile money improved financial inclusion for unbanked Ghanaians?',
                'What is the E-Levy and why did it generate controversy?',
                'How do mobile money agents in rural areas function as "mini banks"?',
                'What are the risks of an increasingly cashless economy?',
            ],
            'key_points': [
                '~43% of Ghanaian adults were using mobile money by 2022 (Bank of Ghana).',
                'Mobile money enables: P2P transfers, bill payments, savings, merchant payments.',
                'Financial inclusion: People without bank accounts can now save and transact digitally.',
                'E-Levy (1.5%, later reduced to 1%): Government revenue vs. transaction costs.',
                'Risks: fraud (social engineering scams), system outages, digital divide.',
                'Mobile money interoperability launched in 2018 — cross-network transfers.',
            ],
            'tasks': [
                'Research: How many mobile money transactions occur in Ghana per month?',
                'Interview: Ask 3 adults how mobile money has changed their daily life.',
                'Analysis: Write a balanced essay (400 words) on the E-Levy: arguments FOR and AGAINST.',
                'Design: Create an infographic showing mobile money growth from 2009 to 2023.',
            ],
        },
        'answer_guide': (
            'E-Levy FOR: Government needs revenue, digital transactions should be taxed like others, '
            'funds education and infrastructure. '
            'AGAINST: Discourages digital adoption, hurts the poor disproportionately, '
            'drives transactions back to cash, reduces financial inclusion gains.'
        ),
    },
    # ── 9. Map Activity — Environment ─────────────────────────────────────
    {
        'title': 'Ghana\'s Forest Reserves and Deforestation Hotspots',
        'activity_type': 'map_activity',
        'level': 'b9',
        'strand': 'environment',
        'topic': 'Mapping deforestation patterns and conservation efforts',
        'scenario_text': (
            'Ghana lost 60% of its forest cover between 1990 and 2020. Illegal logging, galamsey '
            '(illegal mining), and agricultural expansion are the main drivers. Some forest reserves '
            'like Kakum and Atewa are under conservation, while others face severe degradation.'
        ),
        'content': {
            'questions': [
                'What percentage of Ghana\'s land was forested in 1990 vs. 2020?',
                'What are the three main causes of deforestation in Ghana?',
                'Name three forest reserves in Ghana and their current conservation status.',
                'How does deforestation affect water bodies and rainfall patterns?',
            ],
            'key_points': [
                'Ghana: ~8.6 million hectares of forest in 1990 → ~3.6 million in 2020.',
                'Main drivers: galamsey, cocoa farming expansion, illegal chainsaw logging.',
                'Kakum National Park: well-protected, ecotourism hub, canopy walkway.',
                'Atewa Forest Reserve: threatened by bauxite mining plans.',
                'Deforestation → soil erosion → siltation of rivers → reduced rainfall.',
                'REDD+ programme: Ghana receives payments for verified forest conservation.',
            ],
            'tasks': [
                'On a map of Ghana, shade all 16 regions. Mark major forest reserves in GREEN.',
                'Identify and mark 3 deforestation hotspots in RED based on your research.',
                'Mark 3 galamsey-affected river bodies in ORANGE (e.g., Pra, Offin, Ankobra).',
                'Create a legend explaining all map symbols and colours.',
                'Write a short report: What should Ghana prioritise — mining or conservation?',
            ],
        },
        'answer_guide': (
            'Forest reserves to mark: Kakum, Atewa, Bia, Ankasa, Boin-Tano, Subri River. '
            'Deforestation hotspots: Western Region (galamsey + cocoa), Ashanti (galamsey), '
            'Bono (agricultural expansion). Rivers affected: Pra, Offin, Birim, Ankobra.'
        ),
    },
    # ── 10. Research Project — Governance ─────────────────────────────────
    {
        'title': 'How Does the District Assembly Work?',
        'activity_type': 'research',
        'level': 'b7',
        'strand': 'governance',
        'topic': 'Understanding local government in Ghana',
        'scenario_text': (
            'Ghana has 261 Metropolitan, Municipal, and District Assemblies (MMDAs) responsible '
            'for local governance. Assembly Members are elected every 4 years, while the District '
            'Chief Executive (DCE) is appointed by the President. Your task is to research how '
            'your local District Assembly works and what it does for your community.'
        ),
        'content': {
            'questions': [
                'How many District Assemblies are there in Ghana and which one covers your area?',
                'What is the difference between an elected Assembly Member and an appointed DCE?',
                'What services does the District Assembly provide (roads, sanitation, education)?',
                'How can citizens participate in District Assembly meetings?',
            ],
            'key_points': [
                'Local government structure: Metropolitan (pop 250K+), Municipal (95K+), District.',
                'Assembly Members elected by universal adult suffrage on non-partisan basis.',
                'DCE appointed by President, approved by 2/3 of Assembly Members.',
                'District Assemblies Common Fund: share of national revenue for development.',
                'Functions: local roads, waste management, market regulation, birth/death registration.',
                'Citizen participation: attend Assembly meetings, join Unit Committees.',
            ],
            'tasks': [
                'RESEARCH: Find the name of your District Assembly and your Assembly Member.',
                'INTERVIEW: Ask a community elder or Unit Committee member about what the Assembly has done.',
                'PRESENTATION: Create a poster showing the structure of the District Assembly.',
                'LETTER: Write a letter to your Assembly Member suggesting one improvement for your area.',
            ],
        },
        'answer_guide': (
            'Assembly structure: Presiding Member (elected from members), DCE (appointed), '
            '70% elected members + 30% appointed by President. Meets at least 3 times/year. '
            'Common Fund formula: based on need, population, and equality factors.'
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
    # ── 3. Tools & Materials Identification ───────────────────────────────
    {
        'title': 'Identify and Classify Hand Tools',
        'project_type': 'tool_id',
        'level': 'b7',
        'strand': 'tools',
        'topic': 'Identification and classification of common hand tools',
        'description': (
            'Students identify, name, and classify 20 common hand tools into categories: '
            'measuring, cutting, striking, holding, and finishing tools.'
        ),
        'content': {
            'objectives': [
                'Name and spell 20 hand tools correctly.',
                'Classify each tool into its functional category.',
                'Describe the purpose and safe use of each tool.',
                'Demonstrate the correct way to hand a tool to another person.',
            ],
            'materials': [
                'Tool display board (20 labelled tools or high-quality photos)',
                'Classification worksheet', 'Safety gloves',
                'Actual tools: hammer, screwdriver, pliers, tape measure, hacksaw, file',
            ],
            'steps': [
                '1. OBSERVATION: Examine each tool on the display — shape, size, material.',
                '2. NAMING: Write the correct name for each tool on your worksheet.',
                '3. CLASSIFICATION: Sort into: Measuring, Cutting, Striking, Holding, Finishing.',
                '4. FUNCTION: Write one sentence describing what each tool does.',
                '5. SAFETY DEMO: Show the correct way to carry, pass, and store 3 tools.',
            ],
            'safety_notes': [
                'Never run with tools. Carry sharp tools with the blade pointing down.',
                'Pass tools handle-first to the other person.',
                'Return all tools to the tool rack after use.',
            ],
            'assessment': {
                'Identification (25)': 'Correctly names 18+ out of 20 tools',
                'Classification (25)': 'Correctly classifies 18+ tools',
                'Function Description (25)': 'Accurate purpose for each tool',
                'Safety Demonstration (25)': 'Correct handling of all 3 tools',
            },
        },
        'answer_key': (
            'Measuring: tape measure, ruler, try square, marking gauge. '
            'Cutting: hacksaw, chisel, scissors, craft knife. '
            'Striking: hammer, mallet. Holding: pliers, vice, clamp. '
            'Finishing: file, sandpaper, plane.'
        ),
    },
    # ── 4. Innovation Challenge ───────────────────────────────────────────
    {
        'title': 'Solar-Powered Phone Charger — Innovation Challenge',
        'project_type': 'innovation',
        'level': 'shs1',
        'strand': 'innovation',
        'topic': 'Designing a low-cost solar charger for rural communities',
        'description': (
            'Design and prototype a solar-powered phone charger using affordable, locally '
            'available materials. Target: charge a basic phone in 3–4 hours of sunlight. '
            'Budget constraint: maximum GHS 80.'
        ),
        'content': {
            'objectives': [
                'Research solar panel ratings (voltage, wattage) needed for phone charging.',
                'Design a circuit diagram showing panel, regulator, USB output.',
                'Build a functional prototype within the GHS 80 budget.',
                'Present a cost-benefit analysis vs. grid electricity.',
                'Suggest how this could become a small business.',
            ],
            'materials': [
                '6V/2W mini solar panel (GHS 25)', 'USB voltage regulator module 5V (GHS 10)',
                'USB cable and port (GHS 5)', 'Connecting wires, solder, shrink tubing (GHS 10)',
                'Enclosure: recycled plastic container or wooden box (GHS 5)',
                'Multimeter for testing (shared)', 'Soldering iron (shared)',
            ],
            'steps': [
                '1. RESEARCH (Day 1): How much power does a phone need? (5V, 500mA–1A)',
                '2. CIRCUIT DESIGN (Day 1): Draw circuit: panel → regulator → USB output.',
                '3. MATERIAL PROCUREMENT (Day 2): Source components within GHS 80.',
                '4. ASSEMBLY (Day 2-3): Solder connections. Test voltage with multimeter.',
                '5. TESTING (Day 3): Charge a phone in sunlight. Measure charge time.',
                '6. ENCLOSURE (Day 4): Mount components in a protective case.',
                '7. PRESENTATION (Day 5): Demo + business plan for selling 10 units.',
            ],
            'safety_notes': [
                'Soldering iron reaches 350°C — use a stand and work on a heat-resistant surface.',
                'Never short-circuit the solar panel (can cause burns).',
                'Ensure correct polarity before connecting to a phone.',
            ],
            'assessment': {
                'Research & Design (20)': 'Accurate circuit diagram, correct voltage calculations',
                'Build Quality (25)': 'Neat soldering, secure connections, protected wires',
                'Functionality (25)': 'Successfully charges a phone within 4 hours',
                'Budget Compliance (15)': 'All materials within GHS 80',
                'Presentation & Business Plan (15)': 'Clear pitch, realistic pricing, identified market',
            },
        },
        'answer_key': (
            'A 6V/2W panel with a 5V USB regulator can charge a basic phone (1500 mAh battery) '
            'in ~3–4 hours of direct sunlight. Cost per unit: ~GHS 55. Selling price: GHS 90–120.'
        ),
    },
    # ── 5. Workshop Activity — Sewing ─────────────────────────────────────
    {
        'title': 'Hand Sewing — Basic Stitches Sampler',
        'project_type': 'workshop',
        'level': 'b7',
        'strand': 'materials',
        'topic': 'Hand sewing: running stitch, backstitch, blanket stitch',
        'description': (
            'Students learn and practise 4 basic hand stitches by creating a fabric sampler. '
            'The sampler can later be used as a reference card for future sewing projects.'
        ),
        'content': {
            'objectives': [
                'Thread a needle and tie a starting knot correctly.',
                'Demonstrate running stitch with even spacing (5 mm).',
                'Demonstrate backstitch for strong seams.',
                'Demonstrate blanket stitch for fabric edges.',
                'Create a neat sampler showing all 4 stitches labelled.',
            ],
            'materials': [
                'Cotton fabric pieces (15 cm × 25 cm)', 'Hand sewing needles (size 7)',
                'Cotton thread (3 colours)', 'Scissors, thimble, pins',
                'Ruler, fabric marker/chalk', 'Stitch diagram handout',
            ],
            'steps': [
                '1. PREPARATION: Cut fabric to size. Draw 4 horizontal lines 4 cm apart.',
                '2. RUNNING STITCH (Line 1): In-out-in-out, 5 mm spacing.',
                '3. BACKSTITCH (Line 2): Sew forward one stitch, then back half a stitch.',
                '4. BLANKET STITCH (Line 3): Loop stitch along the edge.',
                '5. CROSS STITCH (Line 4): Make X shapes along the line.',
                '6. LABELLING: Write the name of each stitch next to it with fabric marker.',
                '7. FINISHING: Tie off thread securely. Trim loose ends.',
            ],
            'safety_notes': [
                'Always push the needle AWAY from your fingers.',
                'Use a thimble to protect your pushing finger.',
                'Store needles in a pin cushion — never leave them loose.',
            ],
            'assessment': {
                'Running Stitch (20)': 'Even spacing, straight line, consistent length',
                'Backstitch (25)': 'No gaps, strong and neat',
                'Blanket Stitch (25)': 'Even loops, correct technique',
                'Cross Stitch (20)': 'Uniform X shapes, aligned',
                'Presentation (10)': 'Neat labelling, clean sampler',
            },
        },
        'answer_key': (
            'Running stitch: fastest, weakest. Backstitch: strongest for seams. '
            'Blanket stitch: for finishing edges. Cross stitch: decorative.'
        ),
    },
    # ── 6. Skill Assessment Rubric ────────────────────────────────────────
    {
        'title': 'Electrical Wiring — Practical Skills Assessment',
        'project_type': 'rubric',
        'level': 'b9',
        'strand': 'materials',
        'topic': 'Assessing basic domestic electrical wiring skills',
        'description': (
            'A structured rubric for assessing students\' ability to wire a simple lighting circuit '
            '(one switch, one lamp) on a practice board. Covers safety, technique, and functionality.'
        ),
        'content': {
            'objectives': [
                'Identify live, neutral, and earth wires by colour.',
                'Strip wire insulation to the correct length without damaging the conductor.',
                'Connect wires to a switch, lampholder, and consumer unit correctly.',
                'Test the circuit with a low-voltage supply (12V DC for safety).',
                'Explain how to isolate a circuit before working on it.',
            ],
            'materials': [
                'Practice wiring board', 'PVC-insulated cable (3-core: brown, blue, green/yellow)',
                'Switch, lampholder, junction box', 'Wire strippers, screwdriver, pliers',
                '12V DC power supply (safe for practice)', 'Multimeter for continuity testing',
            ],
            'steps': [
                '1. SAFETY BRIEFING: Explain isolation procedure. Check supply is OFF.',
                '2. WIRE IDENTIFICATION: Match colours to functions (brown=live, blue=neutral).',
                '3. CABLE PREPARATION: Cut to length. Strip insulation (8-10 mm exposed).',
                '4. CONNECTIONS: Wire switch (live in, switched live out). Wire lampholder.',
                '5. INSPECTION: Visual check. Tug test all connections.',
                '6. TESTING: Connect 12V supply. Switch on. Lamp should illuminate.',
                '7. FAULT FINDING: If lamp doesn\'t work, use multimeter to find the break.',
            ],
            'safety_notes': [
                'NEVER practise on mains voltage (230V). Use 12V DC practice boards only.',
                'Always assume a circuit is LIVE until proven dead (test before touch).',
                'Ensure all exposed conductors are insulated after testing.',
            ],
            'assessment': {
                'Wire Identification (15)': 'Correctly identifies L, N, E by colour',
                'Cable Preparation (20)': 'Clean strip, correct length, no conductor damage',
                'Connection Quality (25)': 'Tight connections, correct terminals, no loose strands',
                'Circuit Function (20)': 'Lamp illuminates when switch is ON, off when OFF',
                'Safety Compliance (20)': 'Follows isolation procedure, wears PPE, tidy workspace',
            },
        },
        'answer_key': (
            'Brown=live, Blue=neutral, Green-Yellow=earth. '
            'Switch breaks the LIVE wire only. '
            'Lampholder: live to centre pin, neutral to outer ring.'
        ),
    },
    # ── 7. Project Plan — Food Processing ─────────────────────────────────
    {
        'title': 'Produce and Package Groundnut Paste (Nkate Butter)',
        'project_type': 'project_plan',
        'level': 'b8',
        'strand': 'innovation',
        'topic': 'Food processing: roasting, grinding, and packaging for sale',
        'description': (
            'Students learn food processing by producing groundnut paste from raw peanuts. '
            'Covers hygiene, processing techniques, costing, packaging, and marketing.'
        ),
        'content': {
            'objectives': [
                'Practise food hygiene: handwashing, hairnets, clean workspace.',
                'Roast groundnuts evenly using controlled heat.',
                'Grind roasted nuts to smooth paste using a grinding mill or blender.',
                'Calculate production cost per jar and set a selling price.',
                'Design a label for the product.',
            ],
            'materials': [
                'Raw groundnuts (2 kg)', 'Roasting pan, wooden spatula, gas stove',
                'Grinding mill or heavy-duty blender', 'Salt (pinch), optional sugar',
                'Clean glass jars (200 ml) with lids', 'Labels, markers, packaging tape',
                'Hairnets, aprons, hand sanitiser',
            ],
            'steps': [
                '1. HYGIENE SETUP: Wash hands, wear hairnets and aprons, sanitise workspace.',
                '2. SORTING: Remove damaged, mouldy, or discoloured nuts.',
                '3. ROASTING: Roast in batches (medium heat) stirring constantly until golden brown.',
                '4. COOLING & PEELING: Cool for 10 min. Rub to remove skins.',
                '5. GRINDING: Grind in batches until smooth. Add pinch of salt.',
                '6. JARRING: Fill jars, leaving 1 cm headspace. Seal tightly.',
                '7. LABELLING: Affix label with: product name, ingredients, date, weight.',
                '8. COSTING: Calculate total cost ÷ number of jars = cost per jar.',
            ],
            'safety_notes': [
                'Hot roasting pans can cause burns — use oven mitts and long utensils.',
                'Ensure grinding equipment is clean and dry before use.',
                'Check for peanut allergies among students before starting.',
            ],
            'assessment': {
                'Hygiene & Safety (20)': 'Follows all hygiene protocols throughout',
                'Processing Quality (25)': 'Even roast, smooth paste, no burnt flavour',
                'Packaging (20)': 'Clean jars, professional labels, sealed properly',
                'Costing & Pricing (20)': 'Accurate cost calculation, reasonable profit margin',
                'Teamwork (15)': 'Shares tasks, communicates, cleans up',
            },
        },
        'answer_key': (
            'Cost example: 2 kg nuts GHS 30, jars GHS 20, fuel GHS 5, labels GHS 3 = GHS 58. '
            'Yield: ~8 jars. Cost/jar: GHS 7.25. Selling price: GHS 12–15/jar. Profit: GHS 38–62.'
        ),
    },
    # ── 8. Innovation Challenge — Recycling ───────────────────────────────
    {
        'title': 'Plastic Bottle Furniture — Upcycling Challenge',
        'project_type': 'innovation',
        'level': 'b8',
        'strand': 'design',
        'topic': 'Designing functional furniture from recycled plastic bottles',
        'description': (
            'Design and build a small stool or side table using plastic bottles as the structural core, '
            'wrapped with fabric or rope. Promotes environmental awareness and creative problem-solving.'
        ),
        'content': {
            'objectives': [
                'Collect and clean 40+ plastic bottles of uniform size.',
                'Design a stable structure (stool/table) with sketches and dimensions.',
                'Bind bottles together using tape, twine, or wire for structural integrity.',
                'Cover with cardboard, fabric, or rope for a finished appearance.',
                'Test load-bearing capacity (target: support 40 kg).',
            ],
            'materials': [
                '40-60 plastic bottles (500 ml or 1.5 L, same size)', 'Packing tape or duct tape',
                'Twine or rope', 'Cardboard (for seat/top)', 'Old fabric or sack material',
                'Scissors, craft knife (supervised)', 'Ruler, pencil',
            ],
            'steps': [
                '1. COLLECTION (Week 1): Gather 40+ clean, dry bottles with caps on.',
                '2. DESIGN (Day 1): Sketch front and top views. Decide shape: round or hexagonal.',
                '3. BUNDLING (Day 2): Tape 7 bottles together into a tight hexagonal cluster.',
                '4. STACKING (Day 2-3): Build multiple clusters. Tape clusters together for the body.',
                '5. TOP/SEAT (Day 3): Cut cardboard to shape. Glue and tape securely to the top.',
                '6. WRAPPING (Day 4): Wrap body with fabric or rope for aesthetics and strength.',
                '7. TESTING (Day 5): Sit on the stool carefully. Measure load it supports.',
            ],
            'safety_notes': [
                'Craft knives must only be used under teacher supervision.',
                'Ensure bottles are dry inside — moisture causes mould.',
                'Test load gradually — do not jump on the stool.',
            ],
            'assessment': {
                'Design & Planning (20)': 'Clear sketch, dimensions, bill of materials',
                'Construction Quality (25)': 'Tight bindings, stable structure, no wobble',
                'Aesthetics (15)': 'Neat covering, visually appealing',
                'Functionality (25)': 'Supports 40+ kg, suitable height',
                'Environmental Awareness (15)': 'Can explain environmental benefits of upcycling',
            },
        },
        'answer_key': (
            '19 bottles in a hexagonal cluster makes a very stable stool. '
            'Two layers (38 bottles) = standard seat height (45 cm). '
            'Cap bottles tightly — air inside provides rigidity.'
        ),
    },
    # ── 9. Workshop Activity — Metalwork ──────────────────────────────────
    {
        'title': 'Sheet Metal Dustpan — Marking, Cutting, and Bending',
        'project_type': 'workshop',
        'level': 'b9',
        'strand': 'materials',
        'topic': 'Basic sheet metal work using hand tools',
        'description': (
            'Students fabricate a functional dustpan from a single sheet of galvanised mild steel. '
            'Covers marking out, cutting with tin snips, bending, folding, and riveting a handle.'
        ),
        'content': {
            'objectives': [
                'Read and interpret a simple working drawing with fold lines.',
                'Mark out a development (net) on sheet metal using scriber and rule.',
                'Cut along marked lines with aviation tin snips.',
                'Make accurate bends using a folding bar or bench vice.',
                'Attach a wire handle using pop rivets.',
            ],
            'materials': [
                'Galvanised mild steel sheet (0.5 mm, 30 cm × 20 cm)',
                'Scriber, steel rule, engineer\'s square', 'Aviation tin snips (left and right)',
                'Folding bars or bench vice with flat jaws', 'Ball-peen hammer, mallet',
                'Pop rivet gun, rivets (3.2 mm)', 'Steel wire (3 mm) for handle',
                'File, emery cloth', 'Safety gloves, goggles',
            ],
            'steps': [
                '1. STUDY DRAWING: Understand the net/development with fold lines and cut lines.',
                '2. MARKING OUT: Transfer dimensions using scriber and rule. Mark fold lines lightly.',
                '3. CUTTING: Cut along outer lines with tin snips. Cut away waste corners.',
                '4. FILING: File all edges smooth to remove burrs. Round sharp corners.',
                '5. BENDING: Fold sides up using folding bar. Fold lip for strength.',
                '6. HANDLE: Cut wire to length. Bend to U-shape. Rivet to back of dustpan.',
                '7. FINISHING: Ensure all edges are safe. Test that dustpan sits flat on floor.',
            ],
            'safety_notes': [
                'Sheet metal edges are extremely sharp — ALWAYS wear safety gloves.',
                'File all cut edges before handling the piece bare-handed.',
                'Wear goggles when using the rivet gun.',
            ],
            'assessment': {
                'Marking Out (15)': 'Accurate dimensions, clear lines, square corners',
                'Cutting (20)': 'Follows lines closely, minimal waste, smooth edges',
                'Bending (25)': 'Sharp folds, correct angles, symmetrical sides',
                'Handle Attachment (20)': 'Secure rivets, handle centred, comfortable grip',
                'Functionality (20)': 'Sits flat, collects dust effectively, no sharp edges',
            },
        },
        'answer_key': (
            'Net layout: rectangle for base, tabs on 3 sides for folding up, '
            'lip fold (10 mm) on front edge for rigidity. '
            'Handle riveted 3 cm from top edge on each side.'
        ),
    },
    # ── 10. Tool ID — Measuring Instruments ───────────────────────────────
    {
        'title': 'Measuring Instruments — Reading Scales Accurately',
        'project_type': 'tool_id',
        'level': 'b8',
        'strand': 'tools',
        'topic': 'Using and reading measuring instruments in the workshop',
        'description': (
            'Students learn to use 6 common measuring instruments: steel rule, tape measure, '
            'vernier caliper, try square, protractor, and spirit level. Focus on accurate reading.'
        ),
        'content': {
            'objectives': [
                'Read a steel rule to the nearest millimetre.',
                'Measure lengths up to 3 m with a tape measure.',
                'Read a vernier caliper to 0.1 mm (0.02 mm with practice).',
                'Check squareness with a try square.',
                'Measure angles with a protractor.',
                'Check horizontal/vertical with a spirit level.',
            ],
            'materials': [
                'Steel rule (30 cm)', 'Tape measure (3 m)', 'Vernier caliper (150 mm)',
                'Try square', 'Protractor (180°)', 'Spirit level',
                'Various objects to measure (bolts, blocks, wooden pieces)',
                'Measurement recording worksheet',
            ],
            'steps': [
                '1. STATION ROTATION: 6 stations, 8 min each, 4 students per station.',
                '2. Station 1 — STEEL RULE: Measure 5 objects. Record to nearest mm.',
                '3. Station 2 — TAPE MEASURE: Measure desk length, door height, room width.',
                '4. Station 3 — VERNIER CALIPER: Measure bolt diameter, pipe thickness.',
                '5. Station 4 — TRY SQUARE: Check 5 wooden blocks for squareness.',
                '6. Station 5 — PROTRACTOR: Measure 5 angles drawn on paper.',
                '7. Station 6 — SPIRIT LEVEL: Check 3 surfaces for level/plumb.',
            ],
            'safety_notes': [
                'Handle vernier calipers carefully — they are precision instruments.',
                'Do not drop measuring tools — they lose accuracy.',
                'Return tools to their case/pouch after use.',
            ],
            'assessment': {
                'Steel Rule (15)': 'All 5 measurements within ±1 mm of actual',
                'Tape Measure (15)': 'All 3 measurements within ±2 mm',
                'Vernier Caliper (25)': 'Reads to 0.1 mm. At least 3/5 correct',
                'Try Square (15)': 'Correctly identifies square and non-square pieces',
                'Protractor (15)': 'Angle readings within ±2°',
                'Spirit Level (15)': 'Correctly identifies level and non-level surfaces',
            },
        },
        'answer_key': (
            'Vernier reading: main scale + (vernier division × 0.02 mm). '
            'Try square: hold stock flat against edge, check blade against surface — '
            'light gap = not square.'
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
    for deck in _DECKS:
        deck_meta = deck['presentation']
        if not ToolPresentation.objects.filter(profile=profile, title=deck_meta['title']).exists():
            pres = ToolPresentation.objects.create(profile=profile, **deck_meta)
            ToolSlide.objects.bulk_create([
                ToolSlide(presentation=pres, **slide)
                for slide in deck['slides']
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
