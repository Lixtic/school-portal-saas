"""Seed Presentation Decks with sample slide decks across multiple subjects."""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from individual_users.models import IndividualProfile, ToolPresentation, ToolSlide

profile = IndividualProfile.objects.get(id=2)
print(f"Seeding presentation decks for: {profile}")

# Each deck: presentation metadata + list of slides
DECKS = [
    # ── 1. Mathematics — Fractions ────────────────────────────────────────
    {
        "presentation": {
            "title": "Understanding Fractions — Parts of a Whole",
            "subject": "mathematics",
            "target_class": "Basic 7",
            "theme": "aurora",
            "transition": "slide",
        },
        "slides": [
            {
                "order": 0,
                "layout": "title",
                "title": "Understanding Fractions",
                "content": "Parts of a Whole\nBasic 7 Mathematics\nTerm 1, Week 4",
                "speaker_notes": "Welcome the class. Ask: 'If I cut an orange into 4 equal parts and give you 1 piece, what fraction did you get?'",
                "emoji": "\U0001F34A",
            },
            {
                "order": 1,
                "layout": "bullets",
                "title": "What is a Fraction?",
                "content": "A fraction represents PART of a whole\nWritten as one number over another: numerator/denominator\nThe denominator (bottom) tells us how many EQUAL parts\nThe numerator (top) tells us how many parts we HAVE\nExample: 3/4 means 3 out of 4 equal parts",
                "speaker_notes": "Draw a circle on the board. Divide into 4 equal parts. Shade 3 parts. Label numerator and denominator.",
                "emoji": "\U0001F4D0",
            },
            {
                "order": 2,
                "layout": "big_stat",
                "title": "3/4",
                "content": "Three-quarters — the most common fraction in everyday life\nThink: 3 out of every 4 students passed the exam\nThink: 3/4 of a cup of rice",
                "speaker_notes": "Ask students to think of real-life examples where they've heard 'three-quarters'.",
                "emoji": "\U0001F4CA",
            },
            {
                "order": 3,
                "layout": "two_col",
                "title": "Types of Fractions",
                "content": "PROPER FRACTIONS:\nNumerator < Denominator\n1/2, 3/4, 5/8\nAlways less than 1\n---\nIMPROPER FRACTIONS:\nNumerator ≥ Denominator\n5/3, 7/4, 9/2\nAlways ≥ 1",
                "speaker_notes": "Use the two-column layout to compare. Ask: 'Can a proper fraction ever be greater than 1? Why not?'",
                "emoji": "\u2696\uFE0F",
            },
            {
                "order": 4,
                "layout": "bullets",
                "title": "Mixed Numbers",
                "content": "A whole number PLUS a fraction: 2\u00BD, 3\u00BE, 1\u2153\nConverting improper → mixed: divide numerator by denominator\nExample: 7/4 → 7 ÷ 4 = 1 remainder 3 → 1\u00BE\nConverting mixed → improper: (whole × denominator) + numerator\nExample: 2\u00BD → (2 × 2) + 1 = 5/2",
                "speaker_notes": "Work through both conversions step by step on the board. Have students practise with 11/3 and 3⅔.",
                "emoji": "\U0001F504",
            },
            {
                "order": 5,
                "layout": "bullets",
                "title": "Equivalent Fractions",
                "content": "Fractions that look different but have the SAME value\n1/2 = 2/4 = 3/6 = 4/8 = 5/10\nMultiply or divide BOTH numerator and denominator by the same number\n2/3 × 2/2 = 4/6 (same value, different form)\nUseful for adding fractions with different denominators",
                "speaker_notes": "Draw fraction strips on the board. Show visually that 1/2 and 2/4 cover the same area.",
                "emoji": "\U0001F3AF",
            },
            {
                "order": 6,
                "layout": "quote",
                "title": "Real-Life Application",
                "content": "\"If a trader at Makola Market sells 3/5 of her oranges in the morning and 1/5 in the afternoon, what fraction has she sold in total? What fraction remains?\"\n— GES Mathematics Textbook, Basic 7",
                "speaker_notes": "This is a classic GES exam-style question. Walk through it together: 3/5 + 1/5 = 4/5 sold; 1 - 4/5 = 1/5 remains.",
                "emoji": "\U0001F34E",
            },
            {
                "order": 7,
                "layout": "bullets",
                "title": "Practice Problems",
                "content": "1. Convert 11/4 to a mixed number\n2. Convert 3\u2154 to an improper fraction\n3. Find two fractions equivalent to 2/5\n4. Kofi ate 2/6 of a pizza. Ama ate 1/3. Who ate more? (Hint: simplify!)\n5. A farmer plants 3/8 of his land with maize and 2/8 with cassava. What fraction is planted?",
                "speaker_notes": "Give students 10 minutes. Walk around the class. Answers: 1) 2¾  2) 11/3  3) 4/10, 6/15  4) Same!  5) 5/8",
                "emoji": "\u270D\uFE0F",
            },
            {
                "order": 8,
                "layout": "summary",
                "title": "Key Takeaways",
                "content": "Fractions represent parts of a whole (numerator/denominator)\nProper fractions < 1; Improper fractions ≥ 1\nMixed numbers combine whole numbers and fractions\nEquivalent fractions have the same value in different forms\nAlways simplify your final answer to lowest terms",
                "speaker_notes": "Recap the main points. Assign homework: textbook page 47, exercises 1-15.",
                "emoji": "\u2705",
            },
        ],
    },

    # ── 2. Science — The Water Cycle ──────────────────────────────────────
    {
        "presentation": {
            "title": "The Water Cycle — Nature's Recycling System",
            "subject": "science",
            "target_class": "Basic 8",
            "theme": "ocean",
            "transition": "fade",
        },
        "slides": [
            {
                "order": 0,
                "layout": "title",
                "title": "The Water Cycle",
                "content": "Nature's Recycling System\nBasic 8 Integrated Science\nTerm 2, Week 6",
                "speaker_notes": "Start by asking: 'Where does the rain come from? Where does it go after it falls?'",
                "emoji": "\U0001F4A7",
            },
            {
                "order": 1,
                "layout": "bullets",
                "title": "What is the Water Cycle?",
                "content": "The continuous movement of water on, above, and below Earth's surface\nAlso called the HYDROLOGICAL CYCLE\nWater changes state: liquid → gas → liquid → solid\nDriven by the SUN's energy and GRAVITY\nThe same water has been cycling for billions of years!",
                "speaker_notes": "Emphasise that no new water is created — we drink the same water dinosaurs did!",
                "emoji": "\U0001F30D",
            },
            {
                "order": 2,
                "layout": "bullets",
                "title": "Stage 1: Evaporation",
                "content": "The sun heats water in oceans, lakes, and rivers\nWater changes from LIQUID to WATER VAPOUR (gas)\nThe vapour rises into the atmosphere\nEvaporation happens faster in hot weather\nIn Ghana, the Volta Lake and Atlantic Ocean are major sources",
                "speaker_notes": "Demonstration: Place a saucer of water on the windowsill. Check it after 24 hours. Where did the water go?",
                "emoji": "\u2600\uFE0F",
            },
            {
                "order": 3,
                "layout": "bullets",
                "title": "Stage 2: Condensation",
                "content": "Water vapour rises and COOLS at higher altitudes\nCool vapour changes back to tiny water DROPLETS\nMillions of droplets form CLOUDS\nThis is the reverse of evaporation\nYou see condensation on a cold bottle of water on a hot day",
                "speaker_notes": "Demonstration: Breathe on a cold mirror. The mist is condensation — water vapour from your breath meeting the cool surface.",
                "emoji": "\u2601\uFE0F",
            },
            {
                "order": 4,
                "layout": "bullets",
                "title": "Stage 3: Precipitation",
                "content": "Cloud droplets combine and grow heavier\nWhen too heavy to stay in the air, they FALL\nForms of precipitation: rain, hail, sleet, snow\nIn Ghana, we mainly get RAIN (tropical climate)\nThe rainy season (April–July) brings most precipitation to southern Ghana",
                "speaker_notes": "Ask: 'Why does it rain more in Kumasi than in Tamale?' (Forest zone vs. savanna — different evaporation and vegetation patterns.)",
                "emoji": "\U0001F327\uFE0F",
            },
            {
                "order": 5,
                "layout": "two_col",
                "title": "Stage 4: Collection & Runoff",
                "content": "SURFACE RUNOFF:\nRain flows into streams and rivers\nRivers carry water to the sea\nThe Volta River system is Ghana's largest\nRunoff can cause flooding and erosion\n---\nINFILTRATION:\nSome rain soaks into the ground\nBecomes GROUNDWATER\nFeeds wells and boreholes\nPlants absorb it through roots",
                "speaker_notes": "Two-column slide. Explain that some water runs off the surface and some infiltrates. Both are part of collection.",
                "emoji": "\U0001F30A",
            },
            {
                "order": 6,
                "layout": "big_stat",
                "title": "97%",
                "content": "of Earth's water is in the OCEANS (saltwater)\nOnly 3% is freshwater — and most of that is frozen in ice caps\nLess than 1% of all water is available for humans to use\nThis is why WATER CONSERVATION is so important",
                "speaker_notes": "This statistic usually shocks students. Relate to water scarcity in parts of northern Ghana.",
                "emoji": "\U0001F4A7",
            },
            {
                "order": 7,
                "layout": "bullets",
                "title": "Transpiration — The Hidden Stage",
                "content": "Plants absorb groundwater through their ROOTS\nWater travels up through stems to LEAVES\nWater evaporates from tiny pores called STOMATA\nThis process is called TRANSPIRATION\nA large tree can transpire 400 litres of water per DAY!",
                "speaker_notes": "Experiment: Tie a plastic bag around a leafy branch. After a few hours, water droplets appear inside — that's transpiration!",
                "emoji": "\U0001F33F",
            },
            {
                "order": 8,
                "layout": "bullets",
                "title": "Why the Water Cycle Matters",
                "content": "Provides freshwater for drinking, farming, and industry\nRegulates Earth's temperature and climate\nSupports all living things — no water cycle = no life\nHuman activities (deforestation, pollution) can DISRUPT the cycle\nClimate change is making the cycle more EXTREME (floods and droughts)",
                "speaker_notes": "Discuss: How does cutting down forests in the Western Region affect rainfall patterns? (Less transpiration → less local rain.)",
                "emoji": "\u26A0\uFE0F",
            },
            {
                "order": 9,
                "layout": "summary",
                "title": "Summary",
                "content": "EVAPORATION: Sun heats water → liquid becomes gas (vapour)\nCONDENSATION: Vapour cools → forms clouds (tiny droplets)\nPRECIPITATION: Droplets grow heavy → fall as rain/hail/snow\nCOLLECTION: Water gathers in oceans, rivers, lakes, and underground\nTRANSPIRATION: Plants release water vapour through leaves\nThe cycle repeats endlessly — powered by the sun",
                "speaker_notes": "Homework: Draw and label a complete water cycle diagram. Include all 5 stages with arrows showing direction.",
                "emoji": "\U0001F4DD",
            },
        ],
    },

    # ── 3. Social Studies — Ghana's Government ────────────────────────────
    {
        "presentation": {
            "title": "Ghana's System of Government",
            "subject": "social_studies",
            "target_class": "Basic 9",
            "theme": "midnight",
            "transition": "zoom",
        },
        "slides": [
            {
                "order": 0,
                "layout": "title",
                "title": "Ghana's System of Government",
                "content": "The Three Arms of Government\nBasic 9 Social Studies\nTerm 1, Week 8",
                "speaker_notes": "Ask: 'Who runs Ghana? Is it just the President?' Let students share their thoughts before beginning.",
                "emoji": "\U0001F3DB\uFE0F",
            },
            {
                "order": 1,
                "layout": "bullets",
                "title": "Constitutional Democracy",
                "content": "Ghana is a CONSTITUTIONAL DEMOCRACY since 1992\nThe 1992 Constitution is the supreme law of the land\nNo person or institution is above the Constitution\nCitizens elect their leaders through FREE and FAIR elections\nElections are held every 4 years (Presidential + Parliamentary)",
                "speaker_notes": "Show a copy of the 1992 Constitution if available. Explain that it was approved by 92% of voters in a referendum.",
                "emoji": "\U0001F4DC",
            },
            {
                "order": 2,
                "layout": "bullets",
                "title": "The Executive — Making Things Happen",
                "content": "Headed by the PRESIDENT (Head of State + Commander-in-Chief)\nVice President assists the President\nCabinet of Ministers (appointed by President, approved by Parliament)\nImplements and ENFORCES laws passed by Parliament\nManages government departments, agencies, and the civil service",
                "speaker_notes": "The President must win 50%+1 of valid votes cast. If no one wins in round one, a runoff is held.",
                "emoji": "\U0001F3E0",
            },
            {
                "order": 3,
                "layout": "bullets",
                "title": "The Legislature — Making the Laws",
                "content": "PARLIAMENT of Ghana — the lawmaking body\n275 Members of Parliament (MPs) elected from 275 constituencies\nLed by the SPEAKER of Parliament\nDebates and passes BILLS (proposed laws)\nApproves the national BUDGET\nCan summon Ministers to answer questions (oversight)",
                "speaker_notes": "Ask: 'Who is the MP for our constituency?' Discuss how laws are proposed, debated, and passed.",
                "emoji": "\U0001F4D6",
            },
            {
                "order": 4,
                "layout": "bullets",
                "title": "The Judiciary — Interpreting the Laws",
                "content": "Independent court system that interprets laws and settles disputes\nSUPREME COURT — highest court, interprets the Constitution\nCourt of Appeal — hears appeals from lower courts\nHigh Court — serious criminal and civil cases\nCircuit and District Courts — everyday cases\nJudges are appointed, NOT elected (to ensure independence)",
                "speaker_notes": "Emphasise judicial independence. Judges cannot be fired by the President for making unpopular decisions.",
                "emoji": "\u2696\uFE0F",
            },
            {
                "order": 5,
                "layout": "two_col",
                "title": "Separation of Powers",
                "content": "WHY SEPARATE?\nPrevents any one person having too much power\nEach arm CHECKS the others\nProtects citizens' rights and freedoms\nEnsures accountability\n---\nEXAMPLES OF CHECKS:\nParliament can impeach the President\nSupreme Court can declare laws unconstitutional\nPresident can refuse to sign a Bill\nParliament approves presidential appointments",
                "speaker_notes": "Draw a triangle on the board with Executive, Legislature, Judiciary at each corner. Draw arrows showing how each checks the other.",
                "emoji": "\U0001F6E1\uFE0F",
            },
            {
                "order": 6,
                "layout": "quote",
                "title": "Article 1 of the 1992 Constitution",
                "content": "\"The Sovereignty of Ghana resides in the people of Ghana in whose name and for whose welfare the powers of government are to be exercised.\"\n— Article 1(1), 1992 Constitution of the Republic of Ghana",
                "speaker_notes": "This is the foundation. Government power comes FROM the people. Elections are how we express that sovereignty.",
                "emoji": "\U0001F1EC\U0001F1ED",
            },
            {
                "order": 7,
                "layout": "bullets",
                "title": "Local Government",
                "content": "Ghana has 261 Metropolitan, Municipal, and District Assemblies (MMDAs)\n16 Regional Coordinating Councils\nDistrict Chief Executives (DCEs) appointed by the President\nAssembly members elected by communities every 4 years\n30% of revenue shared with District Assemblies (DACF)\nLocal government brings governance closer to the people",
                "speaker_notes": "Discuss: Should DCEs be elected instead of appointed? What are the advantages and disadvantages?",
                "emoji": "\U0001F3D8\uFE0F",
            },
            {
                "order": 8,
                "layout": "summary",
                "title": "Key Takeaways",
                "content": "Ghana is a constitutional democracy (1992 Constitution)\nThree arms: Executive (enforce), Legislature (make laws), Judiciary (interpret)\nSeparation of powers prevents abuse and ensures accountability\nElections every 4 years give citizens the power to choose leaders\nLocal government (MMDAs) serves communities at the grassroots level\nEvery citizen has a DUTY to participate in governance",
                "speaker_notes": "Homework: Name the current President, Vice President, Speaker of Parliament, and Chief Justice. Explain the role of each.",
                "emoji": "\u2705",
            },
        ],
    },

    # ── 4. English — Parts of Speech ──────────────────────────────────────
    {
        "presentation": {
            "title": "Parts of Speech — Building Blocks of English",
            "subject": "english",
            "target_class": "Basic 7",
            "theme": "coral",
            "transition": "flip",
        },
        "slides": [
            {
                "order": 0,
                "layout": "title",
                "title": "Parts of Speech",
                "content": "The 8 Building Blocks of English\nBasic 7 English Language\nTerm 1, Week 3",
                "speaker_notes": "Write on the board: 'The clever girl quickly ate her delicious fufu and soup.' Tell students this one sentence contains all 8 parts of speech.",
                "emoji": "\U0001F4DA",
            },
            {
                "order": 1,
                "layout": "bullets",
                "title": "1. Nouns — Naming Words",
                "content": "A noun names a person, place, thing, or idea\nCommon nouns: teacher, market, book, happiness\nProper nouns: Accra, Kwame, Ghana, January (CAPITALISED)\nAbstract nouns: love, courage, freedom, education\nCollective nouns: a flock of birds, a bunch of plantains",
                "speaker_notes": "Activity: Students list 5 nouns they can see in the classroom right now.",
                "emoji": "\U0001F3F7\uFE0F",
            },
            {
                "order": 2,
                "layout": "bullets",
                "title": "2. Pronouns — Stand-In Words",
                "content": "A pronoun replaces a noun to avoid repetition\nPersonal: I, you, he, she, it, we, they\nPossessive: my, your, his, her, its, our, their\nDemonstrative: this, that, these, those\nExample: 'Ama went to the market. SHE bought tomatoes.' (She = Ama)",
                "speaker_notes": "Without pronouns we'd say: 'Kofi told Kofi's mother that Kofi was hungry' — awkward!",
                "emoji": "\U0001F449",
            },
            {
                "order": 3,
                "layout": "bullets",
                "title": "3. Verbs — Action Words",
                "content": "A verb shows ACTION or STATE OF BEING\nAction verbs: run, eat, write, dance, cook\nLinking verbs: is, am, are, was, were, seems, becomes\nHelping verbs: can, could, will, would, shall, should, must\nEvery sentence MUST have at least one verb\nExample: 'The students STUDIED hard for the BECE.'",
                "speaker_notes": "Play 'Simon Says' using action verbs. This gets students moving and reinforces the concept.",
                "emoji": "\u26A1",
            },
            {
                "order": 4,
                "layout": "bullets",
                "title": "4. Adjectives — Describing Words",
                "content": "An adjective describes or modifies a NOUN\nTells us: What kind? Which one? How many?\nExamples: tall building, red car, three mangoes, beautiful sunset\nComparative: taller, redder, more beautiful\nSuperlative: tallest, reddest, most beautiful\nGhanaian example: 'The BUSY Makola Market sells FRESH vegetables.'",
                "speaker_notes": "Game: Hold up an object. Students compete to give the most adjectives for it.",
                "emoji": "\U0001F308",
            },
            {
                "order": 5,
                "layout": "bullets",
                "title": "5. Adverbs — How, When, Where",
                "content": "An adverb modifies a VERB, adjective, or another adverb\nHow? quickly, slowly, carefully, loudly\nWhen? yesterday, today, soon, already, never\nWhere? here, there, everywhere, inside, outside\nDegree: very, extremely, quite, rather\nMany adverbs end in -LY: quiet → quietLY, careful → carefulLY",
                "speaker_notes": "Tip: Ask 'HOW did she run?' → 'She ran QUICKLY.' The answer is the adverb.",
                "emoji": "\U0001F3C3",
            },
            {
                "order": 6,
                "layout": "two_col",
                "title": "6. Prepositions & 7. Conjunctions",
                "content": "PREPOSITIONS — Position Words:\nShow location, time, or direction\nin, on, at, under, between, beside\n'The cat sat ON the mat.'\n'We arrive AT 8 o'clock.'\n---\nCONJUNCTIONS — Joining Words:\nConnect words, phrases, or clauses\nCoordinating: and, but, or, so, yet\nSubordinating: because, although, if, when\n'I like kenkey AND fried fish.'",
                "speaker_notes": "For conjunctions, teach the FANBOYS acronym: For, And, Nor, But, Or, Yet, So.",
                "emoji": "\U0001F517",
            },
            {
                "order": 7,
                "layout": "bullets",
                "title": "8. Interjections — Emotion Words",
                "content": "An interjection expresses strong emotion or surprise\nUsually followed by an exclamation mark (!)\nExamples: Wow! Ouch! Hurray! Oh no! Hey!\nGhanaian examples: Ei! Chale! Herh! Ah!\nNot grammatically connected to the rest of the sentence\n'WOW! That goal was amazing!'",
                "speaker_notes": "Fun slide! Ask students for their favourite Ghanaian interjections. Discuss how they differ from formal English.",
                "emoji": "\U0001F4A5",
            },
            {
                "order": 8,
                "layout": "bullets",
                "title": "Practice — Find the Parts of Speech",
                "content": "Sentence: 'The clever girl quickly ate her delicious fufu and soup.'\nThe → article (special adjective)\nclever → adjective (describes girl)\ngirl → noun (person)\nquickly → adverb (how she ate)\nate → verb (action)\nher → pronoun (possessive)\ndelicious → adjective (describes fufu)\nfufu, soup → nouns (things)\nand → conjunction (joins fufu and soup)",
                "speaker_notes": "Walk through this together. Then give students 3 new sentences to parse on their own.",
                "emoji": "\U0001F50D",
            },
            {
                "order": 9,
                "layout": "summary",
                "title": "The 8 Parts of Speech",
                "content": "NOUN — names a person, place, thing, or idea\nPRONOUN — replaces a noun (I, she, they)\nVERB — shows action or state of being\nADJECTIVE — describes a noun (tall, red, three)\nADVERB — modifies a verb, adjective, or adverb (quickly, very)\nPREPOSITION — shows position/relationship (in, on, at)\nCONJUNCTION — joins words or clauses (and, but, because)\nINTERJECTION — expresses emotion (Wow! Ouch!)",
                "speaker_notes": "Memory aid: 'NAV PACPI' — Noun, Adjective, Verb, Pronoun, Adverb, Conjunction, Preposition, Interjection. Homework: page 22 exercises 1-10.",
                "emoji": "\U0001F3C6",
            },
        ],
    },

    # ── 5. Computing / ICT — Introduction to Algorithms ───────────────────
    {
        "presentation": {
            "title": "Introduction to Algorithms — Step-by-Step Thinking",
            "subject": "computing",
            "target_class": "Basic 8",
            "theme": "forest",
            "transition": "slide",
        },
        "slides": [
            {
                "order": 0,
                "layout": "title",
                "title": "Introduction to Algorithms",
                "content": "Step-by-Step Thinking for Problem Solving\nBasic 8 Computing / ICT\nTerm 2, Week 2",
                "speaker_notes": "Start with: 'Every time you follow a recipe for jollof rice, you're following an algorithm!' Let students react.",
                "emoji": "\U0001F4BB",
            },
            {
                "order": 1,
                "layout": "bullets",
                "title": "What is an Algorithm?",
                "content": "A set of STEP-BY-STEP instructions to solve a problem\nMust be CLEAR — no ambiguity (each step has one meaning)\nMust be ORDERED — steps follow a logical sequence\nMust be FINITE — it must eventually END\nMust produce a RESULT — it solves the problem\nExamples: recipes, directions to school, long division steps",
                "speaker_notes": "The word 'algorithm' comes from the name of the Persian mathematician Al-Khwarizmi (9th century).",
                "emoji": "\U0001F4CB",
            },
            {
                "order": 2,
                "layout": "bullets",
                "title": "Real-Life Algorithm: Making Jollof Rice",
                "content": "1. Wash and soak rice for 30 minutes\n2. Blend tomatoes, onions, and pepper\n3. Heat oil in a pot; fry sliced onions until golden\n4. Add blended tomato mix; cook for 20 minutes\n5. Add seasoning, salt, and tomato paste; stir\n6. Drain rice and add to the pot\n7. Add water to cover the rice; stir once\n8. Cover tightly and cook on LOW heat for 30 minutes\n9. Check — if dry and fluffy, it's done!",
                "speaker_notes": "Ask: 'What happens if you skip step 1 and don't soak the rice?' The algorithm fails — order matters!",
                "emoji": "\U0001F35A",
            },
            {
                "order": 3,
                "layout": "two_col",
                "title": "Algorithm vs. Program",
                "content": "ALGORITHM:\nWritten in plain language (English/pseudocode)\nHumans can understand it\nNot tied to any programming language\nFocuses on the LOGIC\nCan be drawn as a flowchart\n---\nPROGRAM:\nWritten in a PROGRAMMING LANGUAGE\nComputers can execute it\nPython, Scratch, JavaScript, etc.\nFollows strict SYNTAX rules\nIs an implementation of an algorithm",
                "speaker_notes": "An algorithm is like a recipe. A program is like a robot chef following the recipe in its own language.",
                "emoji": "\U0001F916",
            },
            {
                "order": 4,
                "layout": "bullets",
                "title": "Writing an Algorithm — Example",
                "content": "Problem: Find the largest of three numbers (A, B, C)\n1. START\n2. Read three numbers: A, B, C\n3. If A > B AND A > C, then LARGEST = A\n4. Else if B > A AND B > C, then LARGEST = B\n5. Else LARGEST = C\n6. Display LARGEST\n7. STOP",
                "speaker_notes": "Walk through with real numbers: A=15, B=27, C=9. Which step triggers? Step 4: B is largest (27).",
                "emoji": "\U0001F522",
            },
            {
                "order": 5,
                "layout": "bullets",
                "title": "Flowcharts — Drawing Algorithms",
                "content": "OVAL → Start / Stop\nRECTANGLE → Process (an action or calculation)\nDIAMOND → Decision (Yes/No question)\nPARALLELOGRAM → Input / Output\nARROWS → show the flow direction\nFlowcharts make algorithms VISUAL and easier to understand",
                "speaker_notes": "Show the standard flowchart symbols on the board. Students will draw a flowchart for the 'largest number' algorithm.",
                "emoji": "\U0001F4C8",
            },
            {
                "order": 6,
                "layout": "big_stat",
                "title": "3 Key Properties",
                "content": "Every algorithm must have these THREE properties:\n1. INPUT — What data goes IN?\n2. PROCESS — What steps transform the data?\n3. OUTPUT — What result comes OUT?",
                "speaker_notes": "IPO model: Input → Process → Output. This is the foundation of ALL computing. Write it big on the board.",
                "emoji": "\U0001F3AF",
            },
            {
                "order": 7,
                "layout": "bullets",
                "title": "Class Activity",
                "content": "Write an algorithm for each of these everyday tasks:\n1. Brushing your teeth (at least 6 steps)\n2. Buying credit (airtime) on your phone\n3. Finding a word in a dictionary\n4. Crossing a busy road safely\nBonus: Draw a FLOWCHART for task #4 using proper symbols",
                "speaker_notes": "Give 15 minutes. Remind students: be SPECIFIC. 'Turn on tap' not just 'use water'. Check for proper START/STOP.",
                "emoji": "\u270D\uFE0F",
            },
            {
                "order": 8,
                "layout": "summary",
                "title": "Summary",
                "content": "An algorithm is a step-by-step set of instructions to solve a problem\nAlgorithms must be clear, ordered, finite, and produce a result\nFlowcharts provide a VISUAL representation of algorithms\nEvery algorithm has INPUT → PROCESS → OUTPUT\nAlgorithms are written in plain language; programs are written in code\nGood algorithms = Good programs = Good software",
                "speaker_notes": "Next lesson: We'll learn about PSEUDOCODE and start writing algorithms that can be translated into Scratch programs.",
                "emoji": "\U0001F680",
            },
        ],
    },
]

created_decks = 0
created_slides = 0

for deck_data in DECKS:
    pres_info = deck_data["presentation"]
    pres, was_created = ToolPresentation.objects.get_or_create(
        profile=profile,
        title=pres_info["title"],
        defaults=pres_info,
    )
    if was_created:
        created_decks += 1
        print(f"  + Deck: {pres.title}")
        for slide_data in deck_data["slides"]:
            slide_data["presentation"] = pres
            ToolSlide.objects.create(**slide_data)
            created_slides += 1
    else:
        print(f"  = Deck: {pres.title} (exists)")

total = ToolPresentation.objects.filter(profile=profile).count()
total_slides = ToolSlide.objects.filter(presentation__profile=profile).count()
print(f"\nCreated {created_decks} decks with {created_slides} slides. Total: {total} decks, {total_slides} slides.")
