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
