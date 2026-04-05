"""Seed Literacy Toolkit with sample exercises across all 7 types."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, LiteracyExercise

profile = IndividualProfile.objects.get(id=2)
print(f"Seeding literacy exercises for: {profile}")

EXERCISES = [
    # ── 1. Reading Comprehension ──────────────────────────────────────────
    {
        "title": "The Cocoa Farmer's Wisdom — Reading Comprehension",
        "exercise_type": "comprehension",
        "level": "b7",
        "strand": "Reading",
        "topic": "Reading for meaning",
        "passage": (
            "  Nana Agyemang had farmed cocoa in the Ashanti Region for over forty years. "
            "Every morning before dawn, he walked three kilometres to his plantation, cutlass in hand, "
            "humming an old Akan hymn. His neighbours often wondered why he still farmed at his age.\n\n"
            '  "The cocoa tree does not grow in a day," he would say. "It takes five years before you '
            'harvest the first pod. A young person who plants today will feed their family tomorrow."\n\n'
            "  Last year, the government introduced a new fertilizer subsidy programme. Many farmers "
            "rushed to collect the free inputs, but Nana Agyemang was cautious. He tested the fertilizer "
            "on a small plot first, watching how the soil and trees responded over three months before "
            "applying it to his entire farm.\n\n"
            '  "Patience is not laziness," he explained to his grandson Kofi, who helped after school. '
            '"It is wisdom. The farmer who experiments before committing protects his livelihood."\n\n'
            "  Kofi listened carefully. He was beginning to understand that his grandfather's success "
            "was not luck — it was decades of careful observation, patience, and respect for the land."
        ),
        "content": {
            "questions": [
                {
                    "question": "How long has Nana Agyemang been farming cocoa?",
                    "options": ["Twenty years", "Over forty years", "Five years", "Three years"],
                    "answer": "Over forty years",
                },
                {
                    "question": "Why does Nana Agyemang say a cocoa tree 'does not grow in a day'?",
                    "options": [
                        "Because cocoa trees are very small",
                        "Because it takes five years to get the first harvest",
                        "Because he does not water his trees",
                        "Because the government delays the fertilizer",
                    ],
                    "answer": "Because it takes five years to get the first harvest",
                },
                {
                    "question": "What did Nana Agyemang do before applying the new fertilizer to his whole farm?",
                    "options": [
                        "He refused to use it entirely",
                        "He asked his grandson to apply it",
                        "He tested it on a small plot first",
                        "He sold it to other farmers",
                    ],
                    "answer": "He tested it on a small plot first",
                },
                {
                    "question": "What does the phrase 'Patience is not laziness' mean in this passage?",
                    "options": [
                        "Lazy people are always patient",
                        "Taking time to think before acting is a sign of wisdom, not weakness",
                        "Farmers should never use new products",
                        "Kofi is lazy because he only helps after school",
                    ],
                    "answer": "Taking time to think before acting is a sign of wisdom, not weakness",
                },
                {
                    "question": "What lesson did Kofi learn from his grandfather?",
                    "options": [
                        "That farming is easy work",
                        "That success comes from observation, patience, and respect for the land",
                        "That he should stop going to school",
                        "That the government always helps farmers",
                    ],
                    "answer": "That success comes from observation, patience, and respect for the land",
                },
            ],
            "vocabulary_words": [
                {"word": "plantation", "definition": "A large farm where crops like cocoa are grown"},
                {"word": "subsidy", "definition": "Money or support given by the government to reduce the cost of something"},
                {"word": "cautious", "definition": "Being careful and avoiding unnecessary risks"},
                {"word": "livelihood", "definition": "A person's means of earning money to live"},
            ],
        },
        "answer_key": (
            "1. Over forty years\n"
            "2. Because it takes five years to get the first harvest\n"
            "3. He tested it on a small plot first\n"
            "4. Taking time to think before acting is a sign of wisdom, not weakness\n"
            "5. That success comes from observation, patience, and respect for the land"
        ),
    },

    # ── 2. Grammar Drill ─────────────────────────────────────────────────
    {
        "title": "Tenses in Everyday Life — Grammar Drill",
        "exercise_type": "grammar",
        "level": "b7",
        "strand": "Grammar",
        "topic": "Simple past, present, and future tenses",
        "passage": "",
        "content": {
            "exercises": [
                {
                    "instruction": "Rewrite each sentence in the SIMPLE PAST tense.",
                    "sentences": [
                        "Ama walks to school every morning. → Ama ______ to school yesterday morning.",
                        "The fishermen catch many fish. → The fishermen ______ many fish last week.",
                        "We eat banku and tilapia for dinner. → We ______ banku and tilapia for dinner last night.",
                        "The teacher writes on the whiteboard. → The teacher ______ on the whiteboard yesterday.",
                        "Kwame plays football after school. → Kwame ______ football after school on Friday.",
                    ],
                    "answers": ["walked", "caught", "ate", "wrote", "played"],
                },
                {
                    "instruction": "Rewrite each sentence in the SIMPLE FUTURE tense using 'will'.",
                    "sentences": [
                        "She reads the newspaper every day. → She ______ the newspaper tomorrow.",
                        "They visit Cape Coast Castle during vacation. → They ______ Cape Coast Castle next holiday.",
                        "I buy kelewele from the roadside. → I ______ kelewele from the roadside this evening.",
                        "The bus arrives at 7:00 a.m. → The bus ______ at 7:00 a.m. tomorrow.",
                    ],
                    "answers": [
                        "will read",
                        "will visit",
                        "will buy",
                        "will arrive",
                    ],
                },
                {
                    "instruction": "Identify the tense of the underlined verb in each sentence: Past, Present, or Future.",
                    "sentences": [
                        "The headmaster SPOKE at the assembly this morning.",
                        "My mother SELLS provisions at the market.",
                        "We SHALL travel to Kumasi next month.",
                        "The rain DESTROYED the crops last season.",
                        "Akosua IS READING a storybook right now.",
                    ],
                    "answers": [
                        "Past",
                        "Present",
                        "Future",
                        "Past",
                        "Present (continuous)",
                    ],
                },
            ],
            "rules_summary": (
                "Simple Past: describes actions completed in the past (walked, ate, wrote). "
                "Simple Present: describes habitual actions or facts (walks, eats, writes). "
                "Simple Future: describes actions that will happen (will walk, shall eat). "
                "Tip: look for time markers like 'yesterday', 'every day', 'tomorrow' to identify the tense."
            ),
        },
        "answer_key": (
            "Section 1: walked, caught, ate, wrote, played\n"
            "Section 2: will read, will visit, will buy, will arrive\n"
            "Section 3: Past, Present, Future, Past, Present (continuous)"
        ),
    },

    # ── 3. Vocabulary Builder ─────────────────────────────────────────────
    {
        "title": "Words About Community & Service — Vocabulary Builder",
        "exercise_type": "vocabulary",
        "level": "b8",
        "strand": "Vocabulary",
        "topic": "Community and civic responsibility",
        "passage": "",
        "content": {
            "word_list": [
                {
                    "word": "communal",
                    "definition": "Shared by or involving all members of a community.",
                    "example_sentence": "The communal labour exercise helped keep the streets of Tamale clean.",
                    "synonym": "collective",
                },
                {
                    "word": "solidarity",
                    "definition": "Unity and mutual support within a group.",
                    "example_sentence": "The market women showed solidarity by contributing to the rebuilding of the burnt stalls.",
                    "synonym": "unity",
                },
                {
                    "word": "volunteer",
                    "definition": "A person who offers to do something without being paid.",
                    "example_sentence": "Yaa volunteered to teach younger pupils how to read during the vacation.",
                    "synonym": "helper",
                },
                {
                    "word": "civic",
                    "definition": "Relating to the duties and responsibilities of citizens.",
                    "example_sentence": "Voting in elections is an important civic duty for all Ghanaians.",
                    "synonym": "public",
                },
                {
                    "word": "philanthropy",
                    "definition": "The desire to promote the welfare of others, often through generous donations.",
                    "example_sentence": "The chief's philanthropy funded three new boreholes for the village.",
                    "synonym": "generosity",
                },
                {
                    "word": "advocate",
                    "definition": "A person who publicly supports or recommends a cause.",
                    "example_sentence": "Mrs. Mensah is a strong advocate for girls' education in the Northern Region.",
                    "synonym": "champion",
                },
                {
                    "word": "initiative",
                    "definition": "An act or plan intended to solve a problem or improve a situation.",
                    "example_sentence": "The school's recycling initiative reduced waste by half in one term.",
                    "synonym": "project",
                },
                {
                    "word": "heritage",
                    "definition": "Valued traditions, sites, and objects passed down through generations.",
                    "example_sentence": "The Asante Kingdom's heritage includes the famous Golden Stool.",
                    "synonym": "legacy",
                },
            ],
            "activities": [
                "Fill-in-the-blank: Complete 8 sentences using the vocabulary words above.",
                "Word Map: Choose 3 words and create a web showing synonyms, antonyms, and related words.",
                "Paragraph Writing: Use at least 5 vocabulary words in a paragraph about community service in your town.",
                "Match the Definition: Match each word to its correct definition without looking.",
            ],
        },
        "answer_key": (
            "Answers depend on student responses. Mark for: correct word usage in context, "
            "understanding of definition, ability to use the word in original sentences, "
            "and creativity in paragraph writing. Each vocabulary word should be spelled correctly."
        ),
    },

    # ── 4. Phonics / Remedial ─────────────────────────────────────────────
    {
        "title": "Vowel Sounds & Letter Blends — Phonics Practice",
        "exercise_type": "phonics",
        "level": "b7",
        "strand": "Phonics",
        "topic": "Long and short vowel sounds, consonant blends",
        "passage": "",
        "content": {
            "exercises": [
                {
                    "instruction": "Say each word aloud. Does it have a SHORT vowel sound or a LONG vowel sound? Write S or L.",
                    "content": "cat, cake, bed, beat, ship, shine, hot, home, cup, cute",
                    "answer": "S, L, S, L, S, L, S, L, S, L",
                },
                {
                    "instruction": "Circle the consonant blend at the beginning of each word. Then use the word in a sentence.",
                    "content": "brush, class, drum, flag, grass, price, train, stream, plate, block",
                    "answer": "br-, cl-, dr-, fl-, gr-, pr-, tr-, str-, pl-, bl-",
                },
                {
                    "instruction": "Complete the word by adding the correct vowel (a, e, i, o, u). Then read the word aloud.",
                    "content": "b__g (large), b__g (a container), h__t (temperature), h__t (a strike), p__n (used to write), p__n (a cooking vessel)",
                    "answer": "big, bag, hot, hit, pen, pan",
                },
                {
                    "instruction": "Read this short passage aloud to your partner. Underline every word that has the 'sh' sound.",
                    "content": (
                        "Sheba went to the shop to buy fresh fish for supper. She wished she could also "
                        "buy some sugar but she had no cash. She rushed back before it got too dark."
                    ),
                    "answer": "Sheba, shop, fresh, fish, She, wished, she, sugar, cash, She, rushed",
                },
            ],
            "tips": [
                "Short vowels: a as in cat, e as in bed, i as in ship, o as in hot, u as in cup.",
                "Long vowels: a as in cake, e as in beat, i as in shine, o as in home, u as in cute.",
                "A consonant blend is two or more consonants together where you can hear each sound (br, cl, str).",
                "Practise reading aloud every day — start with 10 minutes and increase gradually.",
            ],
        },
        "answer_key": (
            "Section 1: S, L, S, L, S, L, S, L, S, L\n"
            "Section 2: br-, cl-, dr-, fl-, gr-, pr-, tr-, str-, pl-, bl-\n"
            "Section 3: big, bag, hot, hit, pen, pan\n"
            "Section 4: Sheba, shop, fresh, fish, She, wished, she, sugar, cash, She, rushed"
        ),
    },

    # ── 5. Essay / Creative Writing ───────────────────────────────────────
    {
        "title": "My Hometown — Descriptive Essay Writing",
        "exercise_type": "essay",
        "level": "b8",
        "strand": "Writing",
        "topic": "Descriptive essay writing",
        "passage": "",
        "content": {
            "prompts": [
                "Write a descriptive essay (250-350 words) about your hometown or village. Describe what a visitor would see, hear, smell, and feel. Include at least one memory that makes this place special to you.",
                "Alternative prompt: Describe a market day in your town. Bring the scene to life using vivid adjectives, similes, and sensory details.",
            ],
            "rubric": {
                "Content & Ideas (10 marks)": "Clear main idea, relevant details, personal voice, originality",
                "Organisation (5 marks)": "Clear introduction, body paragraphs, conclusion. Logical flow of ideas",
                "Language Use (5 marks)": "Varied vocabulary, descriptive language, similes/metaphors, sensory details",
                "Grammar & Mechanics (5 marks)": "Correct spelling, punctuation, tense consistency, sentence structure",
                "Word Count (5 marks)": "Minimum 250 words, maximum 350 words. Deduct 1 mark per 25 words over/under",
            },
            "sample_outline": (
                "I. Introduction — name your hometown, its region, one interesting fact\n"
                "II. What You See — describe the landscape, buildings, people, colours\n"
                "III. Sounds & Smells — market noise, cooking aromas, nature sounds\n"
                "IV. A Special Memory — a festival, family moment, or childhood experience\n"
                "V. Conclusion — why this place matters to you, what you'd tell a visitor"
            ),
        },
        "answer_key": (
            "Mark using the rubric above. Total: 30 marks.\n"
            "Look for: specific Ghanaian details (not generic), sensory language, "
            "at least 2 descriptive techniques (simile, metaphor, personification), "
            "correct paragraph structure, and a genuine personal voice.\n"
            "Excellent essays will make the reader feel they are visiting the town."
        ),
    },

    # ── 6. Oral Language Activity ─────────────────────────────────────────
    {
        "title": "Debate: Should Mobile Phones Be Allowed in Schools?",
        "exercise_type": "oral",
        "level": "b9",
        "strand": "Oral Language",
        "topic": "Formal debate and persuasive speaking",
        "passage": "",
        "content": {
            "exercises": [
                {
                    "instruction": "Preparation Phase (15 minutes)",
                    "content": (
                        "Divide the class into two teams:\n"
                        "• Team A (FOR): 'Mobile phones should be allowed in Ghanaian schools'\n"
                        "• Team B (AGAINST): 'Mobile phones should NOT be allowed in Ghanaian schools'\n\n"
                        "Each team must prepare:\n"
                        "1. An opening statement (1 minute)\n"
                        "2. Three strong arguments with evidence\n"
                        "3. A rebuttal strategy for the opposing team's likely points\n"
                        "4. A closing statement (1 minute)"
                    ),
                    "answer": "Teacher observes preparation: look for collaboration, note-taking, and assignment of speaking roles.",
                },
                {
                    "instruction": "Debate Structure (25 minutes)",
                    "content": (
                        "Round 1: Opening Statements — Team A speaker (1 min), then Team B speaker (1 min)\n"
                        "Round 2: Main Arguments — Team A presents 3 arguments (4 min), then Team B (4 min)\n"
                        "Round 3: Rebuttals — Team B responds (2 min), then Team A responds (2 min)\n"
                        "Round 4: Floor Questions — audience members ask 3 questions to either team (5 min)\n"
                        "Round 5: Closing Statements — Team B (1 min), then Team A (1 min)"
                    ),
                    "answer": "Score each speaker on: clarity (5), persuasiveness (5), evidence (5), manner (5). Total per team: 80 marks (4 speakers × 20).",
                },
                {
                    "instruction": "Reflection & Vocabulary (10 minutes)",
                    "content": (
                        "After the debate, each student writes a short reflection:\n"
                        "• Which argument was most convincing and why?\n"
                        "• What new vocabulary did you learn? (e.g. rebuttal, proposition, counter-argument)\n"
                        "• How could your team improve for next time?\n"
                        "• Did the debate change your personal opinion? Explain."
                    ),
                    "answer": "Collect reflections. Look for: critical thinking, honesty about weaknesses, and correct use of debate terminology.",
                },
            ],
            "tips": [
                "Teach debate etiquette: no interrupting, address the chair ('Madam/Mr Chair'), use formal language.",
                "Encourage students to use phrases like 'I respectfully disagree because...' and 'The evidence shows that...'.",
                "Possible FOR arguments: educational apps, research access, emergency communication, digital literacy.",
                "Possible AGAINST arguments: distraction, cyberbullying, inequality (not all students can afford phones), exam cheating.",
            ],
        },
        "answer_key": (
            "Assessment criteria per speaker: Clarity of expression (5), Persuasiveness of arguments (5), "
            "Use of evidence/examples (5), Delivery and manner (5). Total: 20 marks per speaker.\n"
            "Strong debaters will: maintain eye contact, use Ghanaian examples, "
            "anticipate the opposition's arguments, and speak with confidence."
        ),
    },

    # ── 7. Literature Study ───────────────────────────────────────────────
    {
        "title": "Exploring Proverbs — Akan Wisdom in Literature",
        "exercise_type": "literature",
        "level": "b8",
        "strand": "Literature",
        "topic": "Proverbs and figurative language",
        "passage": (
            "Proverbs are short, wise sayings passed down through generations. In Akan culture, "
            "proverbs (called 'ɛbɛ') are used in speeches, storytelling, and everyday conversation "
            "to teach moral lessons. Elders say, 'When a wise man speaks in proverbs, "
            "the foolish man asks for explanations.' Below are five well-known Akan proverbs:\n\n"
            "1. 'Obi nkyerɛ abɔfra Nyame.' — No one teaches a child about God.\n"
            "2. 'Tete wo bi ka; tete wo bi kyerɛ.' — The past has something to say; the past has something to teach.\n"
            "3. 'Woforo dua pa a, na yepia wo.' — When you climb a good tree, you are given a push.\n"
            "4. 'Nea onnim no sua a, ohu.' — He who does not know can learn and become knowledgeable.\n"
            "5. 'Abɔfra bo nwa, na ɔmmo akyekyedeɛ.' — A child can break a snail's shell but not a tortoise's shell."
        ),
        "content": {
            "exercises": [
                {
                    "instruction": "For each proverb above, explain its meaning in your own words (2-3 sentences each).",
                    "content": "Write the number of the proverb and your explanation beside it.",
                    "answer": (
                        "1. Some things are so obvious and natural that even a child understands them without being taught.\n"
                        "2. History carries lessons; we should learn from the experiences of those who came before us.\n"
                        "3. When you have good intentions and work hard, people will support and help you succeed.\n"
                        "4. Ignorance is not permanent — anyone who is willing to learn can gain knowledge.\n"
                        "5. A child's abilities are limited; they should not attempt things beyond their strength or maturity."
                    ),
                },
                {
                    "instruction": "Choose ONE proverb and write a short story (150-200 words) that illustrates its meaning. Set your story in a Ghanaian school, home, or community.",
                    "content": "Your story should have: a character, a problem, and a resolution that connects to the proverb's lesson.",
                    "answer": "Mark for: clear connection to proverb, Ghanaian setting, character development, narrative structure, and creativity.",
                },
                {
                    "instruction": "Identify the literary device used in proverb 5 ('A child can break a snail's shell but not a tortoise's shell'). Explain how the device works.",
                    "content": "Think about: What is being compared? Is it literal or figurative?",
                    "answer": "Metaphor/Analogy: The snail's shell represents easy tasks within a child's capability; the tortoise's shell represents challenges beyond their ability. The comparison teaches about knowing one's limits.",
                },
                {
                    "instruction": "Collect TWO proverbs from your own family or community (in any Ghanaian language). Write them down with: (a) the original language, (b) the English translation, and (c) the lesson it teaches.",
                    "content": "Ask a parent, grandparent, or elder for proverbs they use often.",
                    "answer": "Answers will vary. Mark for: accurate recording, thoughtful translation, and clear explanation of the moral lesson.",
                },
            ],
            "tips": [
                "Proverbs often use figurative language — look for metaphors, similes, and analogies.",
                "Discuss how the same moral lesson might be expressed differently in different cultures.",
                "Encourage students to share proverbs from Ewe, Ga, Dagbani, Fante, and other Ghanaian languages.",
                "Link to GES curriculum: Oral Literature strand — cultural heritage and moral education.",
            ],
        },
        "answer_key": (
            "Section 1: Meanings — see model answers above. Award 2 marks per proverb (10 total).\n"
            "Section 2: Story — 10 marks (setting 2, character 2, plot 3, connection to proverb 3).\n"
            "Section 3: Literary device — Metaphor/Analogy, 5 marks (identification 2, explanation 3).\n"
            "Section 4: Collected proverbs — 5 marks per proverb (original 1, translation 2, lesson 2).\n"
            "Total: 40 marks."
        ),
    },

    # ── 8. Comprehension (SHS level) ──────────────────────────────────────
    {
        "title": "Climate Change & Ghana's Coastline — Advanced Comprehension",
        "exercise_type": "comprehension",
        "level": "shs1",
        "strand": "Reading",
        "topic": "Informational text analysis",
        "passage": (
            "  Ghana's 550-kilometre coastline is under siege. According to a 2023 report by the "
            "Environmental Protection Agency (EPA), the sea erodes between 1.5 and 2 metres of land "
            "every year along parts of the Volta Region coast. Communities like Keta, Fuveme, and "
            "Totope have lost homes, schools, and farmland to the advancing ocean.\n\n"
            "  Scientists attribute the accelerating erosion to three main factors: rising global sea "
            "levels caused by climate change, the removal of coastal vegetation for development, and "
            "sand mining along rivers and beaches. The Keta Sea Defence Wall, completed in 2004 at a "
            "cost of $83 million, has protected some areas, but experts warn that engineered solutions "
            "alone cannot solve the crisis.\n\n"
            '  "We need a combination of hard engineering and nature-based solutions," says Dr. Kwasi '
            "Appeaning Addo, a coastal geomorphologist at the University of Ghana. He advocates for "
            "mangrove restoration along vulnerable stretches of coast. Mangroves act as natural barriers, "
            "absorbing wave energy and trapping sediment that rebuilds shorelines.\n\n"
            "  Meanwhile, affected communities are adapting. In Fuveme, residents have relocated to higher "
            "ground. Fishing families in Ada Foah now diversify their income through eco-tourism and salt "
            "production. But adaptation has limits — when ancestral lands disappear beneath the waves, "
            "no amount of ingenuity can replace what is lost.\n\n"
            "  The Ghana National Climate Change Policy (2014) outlines adaptation and mitigation strategies, "
            "yet implementation has been slow. Civil society organisations urge the government to accelerate "
            "funding for coastal protection and to enforce existing regulations against illegal sand mining."
        ),
        "content": {
            "questions": [
                {
                    "question": "According to the EPA report, how much land does the sea erode annually along parts of the Volta Region coast?",
                    "options": ["0.5 to 1 metre", "1.5 to 2 metres", "3 to 5 metres", "5 to 10 metres"],
                    "answer": "1.5 to 2 metres",
                },
                {
                    "question": "Which THREE factors are identified as causes of accelerating coastal erosion?",
                    "options": [
                        "Rising sea levels, removal of coastal vegetation, and sand mining",
                        "Overfishing, deforestation, and oil drilling",
                        "Earthquakes, hurricane damage, and river flooding",
                        "Tourism development, road construction, and factory pollution",
                    ],
                    "answer": "Rising sea levels, removal of coastal vegetation, and sand mining",
                },
                {
                    "question": "What is Dr. Appeaning Addo's proposed solution for coastal protection?",
                    "options": [
                        "Build more sea defence walls across all coastlines",
                        "Relocate all coastal communities inland",
                        "Combine hard engineering with nature-based solutions like mangrove restoration",
                        "Ban all fishing activities along the coast",
                    ],
                    "answer": "Combine hard engineering with nature-based solutions like mangrove restoration",
                },
                {
                    "question": "What does the word 'ingenuity' mean as used in paragraph 4?",
                    "options": [
                        "Wealth and financial resources",
                        "Clever and original thinking or inventiveness",
                        "Physical strength and endurance",
                        "Government assistance and support",
                    ],
                    "answer": "Clever and original thinking or inventiveness",
                },
                {
                    "question": "What is the author's overall tone in this passage?",
                    "options": [
                        "Humorous and lighthearted",
                        "Angry and accusatory",
                        "Informative and concerned",
                        "Optimistic and celebratory",
                    ],
                    "answer": "Informative and concerned",
                },
            ],
            "vocabulary_words": [
                {"word": "erosion", "definition": "The gradual wearing away of land by natural forces like wind and water"},
                {"word": "geomorphologist", "definition": "A scientist who studies landforms and the processes that shape them"},
                {"word": "mitigation", "definition": "Actions taken to reduce the severity or seriousness of something"},
                {"word": "adaptation", "definition": "The process of changing to suit new conditions or circumstances"},
                {"word": "sediment", "definition": "Material (sand, soil, stones) deposited by water, wind, or ice"},
            ],
        },
        "answer_key": (
            "1. 1.5 to 2 metres\n"
            "2. Rising sea levels, removal of coastal vegetation, and sand mining\n"
            "3. Combine hard engineering with nature-based solutions like mangrove restoration\n"
            "4. Clever and original thinking or inventiveness\n"
            "5. Informative and concerned"
        ),
    },

    # ── 9. Grammar (SHS level) ────────────────────────────────────────────
    {
        "title": "Active & Passive Voice — Grammar Mastery",
        "exercise_type": "grammar",
        "level": "shs1",
        "strand": "Grammar",
        "topic": "Active and passive voice transformations",
        "passage": "",
        "content": {
            "exercises": [
                {
                    "instruction": "Change each sentence from ACTIVE to PASSIVE voice.",
                    "sentences": [
                        "The prefect rang the bell at 6:00 a.m.",
                        "The students are cleaning the classroom.",
                        "The headmistress will announce the exam results tomorrow.",
                        "Kofi has completed the science project.",
                        "The government is building new school blocks across the country.",
                    ],
                    "answers": [
                        "The bell was rung by the prefect at 6:00 a.m.",
                        "The classroom is being cleaned by the students.",
                        "The exam results will be announced by the headmistress tomorrow.",
                        "The science project has been completed by Kofi.",
                        "New school blocks are being built across the country by the government.",
                    ],
                },
                {
                    "instruction": "Change each sentence from PASSIVE to ACTIVE voice.",
                    "sentences": [
                        "The national anthem was sung by the choir.",
                        "The letter has been delivered by the postman.",
                        "A new road is being constructed by the contractors.",
                        "The thief was arrested by the police last night.",
                    ],
                    "answers": [
                        "The choir sang the national anthem.",
                        "The postman has delivered the letter.",
                        "The contractors are constructing a new road.",
                        "The police arrested the thief last night.",
                    ],
                },
                {
                    "instruction": "Identify whether each sentence is in ACTIVE or PASSIVE voice. Write A or P.",
                    "sentences": [
                        "The farmer harvested the maize before the rains came.",
                        "The prizes were distributed by the guest of honour.",
                        "The school bus carries sixty students every day.",
                        "The test papers were marked by the external examiner.",
                        "Our team won the inter-school debate competition.",
                    ],
                    "answers": ["A", "P", "A", "P", "A"],
                },
            ],
            "rules_summary": (
                "Active voice: Subject performs the action (The dog bit the boy). "
                "Passive voice: Subject receives the action (The boy was bitten by the dog). "
                "To convert Active → Passive: move the object to subject position, use 'be' + past participle, "
                "add 'by' + original subject. Match the tense of the original sentence."
            ),
        },
        "answer_key": (
            "Section 1 (Active → Passive): See answers above. Award 2 marks each (10 total).\n"
            "Section 2 (Passive → Active): See answers above. Award 2 marks each (8 total).\n"
            "Section 3 (Identify): A, P, A, P, A. Award 1 mark each (5 total).\n"
            "Grand Total: 23 marks."
        ),
    },

    # ── 10. Vocabulary (SHS level) ────────────────────────────────────────
    {
        "title": "Academic & Formal Register — Vocabulary for Exams",
        "exercise_type": "vocabulary",
        "level": "shs2",
        "strand": "Vocabulary",
        "topic": "Formal English and academic register",
        "passage": "",
        "content": {
            "word_list": [
                {
                    "word": "analyse",
                    "definition": "To examine something in detail in order to explain and interpret it.",
                    "example_sentence": "The essay question asked students to analyse the causes of rural-urban migration in Ghana.",
                    "synonym": "examine",
                },
                {
                    "word": "consequently",
                    "definition": "As a result; therefore.",
                    "example_sentence": "The dam was not maintained; consequently, several communities experienced flooding.",
                    "synonym": "therefore",
                },
                {
                    "word": "elaborate",
                    "definition": "To explain or develop an idea in more detail.",
                    "example_sentence": "The teacher asked Esi to elaborate on her answer about photosynthesis.",
                    "synonym": "expand",
                },
                {
                    "word": "phenomenon",
                    "definition": "A fact or event that can be observed, especially one whose cause is in question.",
                    "example_sentence": "The harmattan is a weather phenomenon that affects West Africa every dry season.",
                    "synonym": "occurrence",
                },
                {
                    "word": "substantiate",
                    "definition": "To provide evidence to support or prove the truth of something.",
                    "example_sentence": "You must substantiate your claims with references from the textbook.",
                    "synonym": "verify",
                },
                {
                    "word": "unprecedented",
                    "definition": "Never done or known before; without previous example.",
                    "example_sentence": "The 2020 school closures were unprecedented in Ghana's educational history.",
                    "synonym": "unparalleled",
                },
            ],
            "activities": [
                "Sentence Construction: Write one original sentence for each word in a formal academic tone.",
                "Replace the Informal: Rewrite these sentences using the vocabulary words:\n  - 'The teacher told Kofi to say more about his answer.' → elaborate\n  - 'Because of the drought, many farmers lost their crops.' → consequently\n  - 'Nobody had ever seen anything like the floods before.' → unprecedented",
                "Paragraph Challenge: Write a formal paragraph (100 words) using at least 4 of the vocabulary words. Topic: 'The importance of education in Ghana.'",
                "Word Roots: Research the Latin/Greek origins of 'phenomenon' and 'unprecedented'. How do the roots help you remember the meaning?",
            ],
        },
        "answer_key": (
            "Sentence construction: 1 mark per correct, contextual use (6 marks).\n"
            "Replace the informal: elaborate, consequently, unprecedented (3 marks).\n"
            "Paragraph: correct usage (4 marks), formal tone (2 marks), coherence (2 marks) = 8 marks.\n"
            "Word roots: phainomenon (Greek: 'thing appearing'), un+prae+cedere (Latin: 'not gone before') = 3 marks.\n"
            "Total: 20 marks."
        ),
    },
]

created = 0
for ex in EXERCISES:
    obj, was_created = LiteracyExercise.objects.get_or_create(
        profile=profile,
        title=ex["title"],
        defaults=ex,
    )
    if was_created:
        created += 1
        print(f"  + {obj.title}")
    else:
        print(f"  = {obj.title} (exists)")

total = LiteracyExercise.objects.filter(profile=profile).count()
print(f"\nCreated {created} new exercises. Total for {profile}: {total}")
