"""Seed sample activities for Literacy Toolkit, CitizenEd, and TVET Workshop."""
import os, sys, json, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
django.setup()

from individual_users.models import (
    IndividualProfile, LiteracyExercise, CitizenEdActivity, TVETProject,
)

profile = IndividualProfile.objects.get(id=1)

# ── Literacy Toolkit (5) ────────────────────────────────────────────────────

literacy_data = [
    dict(
        title="The Cocoa Farmer \u2014 Reading Comprehension",
        exercise_type="comprehension",
        level="b7",
        strand="Reading",
        topic="Agriculture & Livelihoods",
        passage=(
            "Kwame Mensah wakes every morning at 4:30 a.m. to tend his cocoa farm "
            "in the Ashanti Region of Ghana. The cocoa tree, Theobroma cacao, "
            "thrives in the tropical climate and produces the beans that eventually "
            "become chocolate enjoyed around the world.\n\n"
            "Harvesting is hard work. Kwame uses a sharp cutlass to slice the ripe "
            "pods from the branches. The beans inside are scooped out, fermented for "
            "five to seven days, and then dried in the sun. Only after this careful "
            "process are they ready for sale to the Licensed Buying Companies.\n\n"
            "Ghana is the second-largest cocoa producer in the world, contributing "
            "about 20 percent of the global supply. For farmers like Kwame, cocoa is "
            "not just a crop \u2014 it is a way of life that supports families, funds "
            "education, and builds communities."
        ),
        content={
            "questions": [
                {"q": "What time does Kwame wake up each morning?", "options": ["4:30 a.m.", "5:00 a.m.", "6:00 a.m.", "3:30 a.m."], "answer": 0},
                {"q": "What tool does Kwame use to harvest cocoa pods?", "options": ["Axe", "Cutlass", "Scissors", "Machete"], "answer": 1},
                {"q": "How long are cocoa beans fermented?", "options": ["1-2 days", "3-4 days", "5-7 days", "10-14 days"], "answer": 2},
                {"q": "What percentage of global cocoa does Ghana supply?", "options": ["10%", "15%", "20%", "30%"], "answer": 2},
                {"q": "Which region does Kwame farm in?", "options": ["Greater Accra", "Volta", "Ashanti", "Northern"], "answer": 2},
            ],
            "vocabulary": ["fermented", "tropical", "thrives", "cutlass", "livelihoods"],
        },
        answer_key="1) 4:30 a.m.  2) Cutlass  3) 5-7 days  4) 20%  5) Ashanti Region",
    ),
    dict(
        title="Parts of Speech \u2014 Nouns, Verbs & Adjectives",
        exercise_type="grammar",
        level="b7",
        strand="Grammar",
        topic="Parts of Speech",
        passage="",
        content={
            "sections": [
                {
                    "instruction": "Identify the nouns in each sentence.",
                    "sentences": [
                        "The children played in the park after school.",
                        "Accra is the capital city of Ghana.",
                        "My grandmother makes the best jollof rice.",
                    ],
                    "answers": [
                        ["children", "park", "school"],
                        ["Accra", "capital", "city", "Ghana"],
                        ["grandmother", "jollof rice"],
                    ],
                },
                {
                    "instruction": "Pick out the verbs.",
                    "sentences": [
                        "The cat jumped over the fence and ran away.",
                        "She sings beautifully at church every Sunday.",
                    ],
                    "answers": [["jumped", "ran"], ["sings"]],
                },
                {
                    "instruction": "Underline the adjectives.",
                    "sentences": [
                        "The tall man wore a bright yellow shirt.",
                        "We enjoyed the delicious, warm meal.",
                    ],
                    "answers": [["tall", "bright", "yellow"], ["delicious", "warm"]],
                },
            ]
        },
        answer_key="Section 1: children/park/school; Accra/capital/city/Ghana; grandmother/jollof rice\nSection 2: jumped/ran; sings\nSection 3: tall/bright/yellow; delicious/warm",
    ),
    dict(
        title="Word Power \u2014 Common Prefixes & Suffixes",
        exercise_type="vocabulary",
        level="b8",
        strand="Vocabulary",
        topic="Word Formation",
        passage="",
        content={
            "word_list": [
                {"word": "unhappy", "prefix": "un-", "root": "happy", "meaning": "not happy; sad"},
                {"word": "rewrite", "prefix": "re-", "root": "write", "meaning": "to write again"},
                {"word": "misunderstand", "prefix": "mis-", "root": "understand", "meaning": "to understand wrongly"},
                {"word": "beautiful", "suffix": "-ful", "root": "beauty", "meaning": "full of beauty"},
                {"word": "careless", "suffix": "-less", "root": "care", "meaning": "without care"},
                {"word": "enjoyment", "suffix": "-ment", "root": "enjoy", "meaning": "the state of enjoying"},
            ],
            "matching": {
                "instruction": "Match each prefix/suffix with its meaning.",
                "items": [
                    {"term": "un-", "definition": "not / opposite of"},
                    {"term": "re-", "definition": "again"},
                    {"term": "mis-", "definition": "wrongly / badly"},
                    {"term": "-ful", "definition": "full of"},
                    {"term": "-less", "definition": "without"},
                    {"term": "-ment", "definition": "state or result of"},
                ],
            },
        },
        answer_key="un- = not, re- = again, mis- = wrongly, -ful = full of, -less = without, -ment = state of",
    ),
    dict(
        title="Persuasive Essay \u2014 Should School Uniforms Be Compulsory?",
        exercise_type="essay",
        level="b9",
        strand="Writing",
        topic="Persuasive Writing",
        passage="",
        content={
            "prompts": [
                "Write a persuasive essay arguing FOR or AGAINST compulsory school uniforms.",
                "Your essay should include: an introduction with a clear thesis, at least three supporting arguments with evidence, a counter-argument, and a conclusion.",
            ],
            "rubric": [
                {"criterion": "Thesis & Position", "max_marks": 5},
                {"criterion": "Supporting Arguments", "max_marks": 10},
                {"criterion": "Counter-argument", "max_marks": 5},
                {"criterion": "Organisation & Flow", "max_marks": 5},
                {"criterion": "Grammar & Spelling", "max_marks": 5},
                {"criterion": "Conclusion", "max_marks": 5},
            ],
            "sample_outline": {
                "intro": "Hook + background + thesis statement",
                "body1": "Argument 1 \u2014 Equality: uniforms reduce peer pressure",
                "body2": "Argument 2 \u2014 Discipline: sense of belonging and identity",
                "body3": "Argument 3 \u2014 Cost: cheaper than buying trendy clothes",
                "counter": "Some say uniforms limit self-expression \u2014 rebuttal",
                "conclusion": "Restate thesis + call to action",
            },
        },
        answer_key="Open-ended. Mark using the rubric provided (total 35 marks).",
    ),
    dict(
        title="Anansi and the Pot of Wisdom \u2014 Literature Study",
        exercise_type="literature",
        level="b7",
        strand="Literature",
        topic="Ghanaian Folktales",
        passage=(
            "Long ago, Anansi the Spider decided he wanted to keep all the wisdom "
            "in the world for himself. He gathered every last bit of wisdom and "
            "sealed it inside a large clay pot.\n\n"
            "'I will hide this pot at the top of the tallest tree,' Anansi said, "
            "'so nobody else can reach it.'\n\n"
            "He tied the pot to his belly and began climbing the silk-cotton tree. "
            "But the pot kept getting in the way, and he slipped again and again. "
            "His young son, Ntikuma, watched from below.\n\n"
            "'Father,' Ntikuma called out, 'why not tie the pot to your back "
            "instead? Then your arms will be free to climb.'\n\n"
            "Anansi realised that even after collecting all the wisdom, a child "
            "could still think of something he had not. In anger and shame, he "
            "threw the pot down. It shattered on the ground, and wisdom scattered "
            "across the world for everyone to share."
        ),
        content={
            "discussion_questions": [
                "Why did Anansi want to keep all the wisdom for himself?",
                "What problem did Anansi face while climbing the tree?",
                "What advice did Ntikuma give his father?",
                "What lesson does this folktale teach us?",
                "Can you think of a time when someone younger helped you solve a problem?",
            ],
            "literary_elements": {
                "genre": "Folktale / Oral tradition",
                "setting": "A forest with a tall silk-cotton tree",
                "protagonist": "Anansi the Spider",
                "antagonist": "Anansi himself (his greed)",
                "theme": "Wisdom belongs to everyone; no one person can own all knowledge",
                "moral": "Even the wisest can learn from the young",
            },
        },
        answer_key="Discussion-based \u2014 no single correct answer. Assess depth of reasoning.",
    ),
]

created = 0
for item in literacy_data:
    obj, new = LiteracyExercise.objects.get_or_create(
        profile=profile, title=item["title"], defaults=item,
    )
    if new:
        created += 1
        print(f"  + Literacy: {obj.title}")
    else:
        print(f"  = Literacy (exists): {obj.title}")
print(f"Literacy Toolkit: {created} created\n")


# ── CitizenEd (5) ───────────────────────────────────────────────────────────

citizen_data = [
    dict(
        title="The Galamsey Crisis \u2014 Mining vs Livelihoods",
        activity_type="case_study",
        level="b9",
        strand="environment",
        topic="Illegal Mining & Environmental Impact",
        scenario_text=(
            "Galamsey (illegal small-scale mining) has become one of the most "
            "pressing environmental issues in Ghana. Rivers like the Pra and "
            "Birim have turned brown due to mercury and chemical pollution from "
            "mining activities.\n\n"
            "Proponents argue that galamsey provides employment for thousands of "
            "rural youth who have no other source of income. Opponents point to "
            "the destruction of farmlands, water bodies, and forests.\n\n"
            "In 2017, the government launched Operation Vanguard to crack down on "
            "illegal mining. However, enforcement has been inconsistent, and "
            "galamsey continues in many regions."
        ),
        content={
            "questions": [
                "What is galamsey and why is it called illegal?",
                "Name two rivers affected by galamsey pollution.",
                "What arguments do supporters of galamsey make?",
                "Describe two environmental effects of illegal mining.",
                "Suggest two alternative livelihood programmes the government could introduce.",
            ],
            "key_points": [
                "Mercury pollution of water bodies",
                "Loss of farmland and forest cover",
                "Youth unemployment as root cause",
                "Operation Vanguard enforcement challenges",
            ],
            "tasks": [
                "Write a letter to your MP suggesting solutions to the galamsey problem.",
                "Draw a before-and-after diagram of a river affected by mining.",
                "Hold a class debate: This house believes galamsey should be legalised and regulated.",
            ],
        },
        answer_guide="Open-ended case study. Assess critical thinking, evidence use, and proposed solutions.",
    ),
    dict(
        title="Debate: Should the Voting Age Be Lowered to 16?",
        activity_type="debate",
        level="b9",
        strand="governance",
        topic="Youth Participation in Democracy",
        scenario_text=(
            "Some countries have lowered the voting age to 16, including Austria, "
            "Scotland, and Brazil. In Ghana, the current voting age is 18. Some "
            "people believe that 16-year-olds are mature enough to participate in "
            "elections, while others think they lack the experience to make informed "
            "political decisions."
        ),
        content={
            "questions": [
                "What is the current voting age in Ghana?",
                "Name two countries that allow 16-year-olds to vote.",
                "Give two arguments in favour of lowering the voting age.",
                "Give two arguments against lowering the voting age.",
            ],
            "for_arguments": [
                "Young people are affected by government policies on education and employment.",
                "Early participation builds a lifelong habit of civic engagement.",
                "16-year-olds can work, pay taxes, and drive in many countries.",
            ],
            "against_arguments": [
                "Young people may be easily influenced by social media and peer pressure.",
                "Brain development research suggests decision-making matures around age 25.",
                "Low turnout among 18-24 year-olds suggests even older youth are disengaged.",
            ],
            "tasks": [
                "Divide the class into two teams and hold a formal debate.",
                "Write a 200-word opinion piece for a school newspaper.",
                "Conduct a class vote and discuss the results.",
            ],
        },
        answer_guide="Debate format. Assess argumentation, evidence, rebuttal quality, and respectful dialogue.",
    ),
    dict(
        title="Mapping Ghana \u2014 Regions, Capitals & Resources",
        activity_type="map_activity",
        level="b7",
        strand="environment",
        topic="Geography of Ghana",
        scenario_text=(
            "Ghana is divided into 16 administrative regions, each with its own "
            "capital city and unique resources. Understanding the geography of our "
            "country helps us appreciate its diversity and plan for development."
        ),
        content={
            "regions": [
                {"name": "Greater Accra", "capital": "Accra", "resource": "Commerce & Industry"},
                {"name": "Ashanti", "capital": "Kumasi", "resource": "Gold & Cocoa"},
                {"name": "Western", "capital": "Sekondi-Takoradi", "resource": "Oil & Timber"},
                {"name": "Eastern", "capital": "Koforidua", "resource": "Diamonds & Cocoa"},
                {"name": "Central", "capital": "Cape Coast", "resource": "Tourism & Fishing"},
                {"name": "Volta", "capital": "Ho", "resource": "Kente Weaving & Rice"},
                {"name": "Northern", "capital": "Tamale", "resource": "Shea Nuts & Yams"},
                {"name": "Upper East", "capital": "Bolgatanga", "resource": "Basketry & Millet"},
                {"name": "Upper West", "capital": "Wa", "resource": "Guinea Fowl & Groundnuts"},
                {"name": "Bono", "capital": "Sunyani", "resource": "Cocoa & Timber"},
                {"name": "Bono East", "capital": "Techiman", "resource": "Yams & Cashew"},
                {"name": "Ahafo", "capital": "Goaso", "resource": "Cocoa & Gold"},
                {"name": "Western North", "capital": "Sefwi Wiawso", "resource": "Cocoa & Rubber"},
                {"name": "Oti", "capital": "Dambai", "resource": "Rice & Fishing"},
                {"name": "North East", "capital": "Nalerigu", "resource": "Shea & Livestock"},
                {"name": "Savannah", "capital": "Damongo", "resource": "Yams & Tourism"},
            ],
            "tasks": [
                "On a blank map of Ghana, label all 16 regions and their capitals.",
                "Colour-code regions by their main economic activity.",
                "Choose one region and write 5 facts about it.",
                "Identify which regions share borders with neighbouring countries.",
            ],
        },
        answer_guide="Check map labelling accuracy. See regions list for correct capitals and resources.",
    ),
    dict(
        title="Responsible Digital Citizenship",
        activity_type="scenario",
        level="b8",
        strand="citizenship",
        topic="Online Safety & Ethics",
        scenario_text=(
            "As more young people in Ghana gain access to the internet through "
            "smartphones and school computers, questions about responsible online "
            "behaviour become increasingly important. Digital citizenship means "
            "using technology safely, respectfully, and responsibly."
        ),
        content={
            "scenarios": [
                {
                    "title": "The Cyberbully",
                    "text": "Ama notices that classmates are posting mean comments about a quiet student on a WhatsApp group. Some students share embarrassing photos.",
                    "questions": ["What should Ama do?", "Why is cyberbullying harmful?", "What are the consequences under Ghanaian law?"],
                },
                {
                    "title": "The Pirated Movie",
                    "text": "Kofi finds a website offering free downloads of the latest Ghanaian movies. His friend says everyone does it.",
                    "questions": ["Is downloading pirated content legal?", "How does piracy affect the Ghanaian film industry?", "What are legal alternatives?"],
                },
                {
                    "title": "The Online Scam",
                    "text": "Adjoa receives a text message saying she has won GHS 5,000 and should send her bank details to claim it.",
                    "questions": ["Is this message likely genuine?", "What signs indicate it is a scam?", "What should Adjoa do?"],
                },
            ],
            "tasks": [
                "Create a poster about online safety tips for your school notice board.",
                "Role-play one of the scenarios with your group and present solutions.",
                "Write 5 rules for responsible internet use.",
            ],
        },
        answer_guide="Scenario-based. Assess awareness of online risks, ethical reasoning, and practical safety knowledge.",
    ),
    dict(
        title="Road to Independence \u2014 Ghana Timeline Activity",
        activity_type="timeline",
        level="b8",
        strand="governance",
        topic="Ghana Independence History",
        scenario_text=(
            "Ghana became the first sub-Saharan African country to gain independence "
            "from colonial rule on 6 March 1957. The journey to independence was "
            "long and involved many key figures and events."
        ),
        content={
            "events": [
                {"year": "1874", "event": "Gold Coast formally becomes a British Crown Colony."},
                {"year": "1897", "event": "Aborigines Rights Protection Society formed to protect land rights."},
                {"year": "1920", "event": "National Congress of British West Africa founded by Casely Hayford."},
                {"year": "1947", "event": "United Gold Coast Convention (UGCC) founded; Kwame Nkrumah invited as General Secretary."},
                {"year": "1948", "event": "28 February Riots \u2014 ex-servicemen march to Christiansborg; 3 killed, sparking widespread protests."},
                {"year": "1949", "event": "Nkrumah breaks from UGCC and founds the Convention People's Party (CPP)."},
                {"year": "1950", "event": "Positive Action campaign \u2014 strikes and boycotts; Nkrumah imprisoned."},
                {"year": "1951", "event": "CPP wins general election; Nkrumah released to become Leader of Government Business."},
                {"year": "1954", "event": "New constitution grants internal self-government."},
                {"year": "1956", "event": "Plebiscite in British Togoland \u2014 votes to join Gold Coast."},
                {"year": "1957", "event": "6 March \u2014 Ghana becomes independent with Nkrumah as Prime Minister."},
            ],
            "tasks": [
                "Create a timeline poster showing all the key events from 1874 to 1957.",
                "Write a short biography (150 words) of Kwame Nkrumah.",
                "Explain why the 1948 riots are considered a turning point.",
                "Compare the approaches of the UGCC and the CPP.",
            ],
        },
        answer_guide="Timeline accuracy is key. Assess understanding of cause-and-effect between events.",
    ),
]

created = 0
for item in citizen_data:
    obj, new = CitizenEdActivity.objects.get_or_create(
        profile=profile, title=item["title"], defaults=item,
    )
    if new:
        created += 1
        print(f"  + CitizenEd: {obj.title}")
    else:
        print(f"  = CitizenEd (exists): {obj.title}")
print(f"CitizenEd: {created} created\n")


# ── TVET Workshop (5) ───────────────────────────────────────────────────────

tvet_data = [
    dict(
        title="Build a Simple Wooden Bookshelf",
        project_type="project_plan",
        level="b8",
        strand="design",
        topic="Woodwork \u2014 Shelf Construction",
        description=(
            "In this project, students will design and build a simple two-shelf "
            "bookshelf using basic woodworking tools and techniques. The project "
            "develops measuring, cutting, joining, and finishing skills."
        ),
        content={
            "objectives": [
                "Measure and mark wood accurately using a ruler and try-square.",
                "Cut wood to size using a tenon saw.",
                "Join pieces using butt joints and wood glue.",
                "Sand and apply varnish for a smooth finish.",
            ],
            "materials": [
                "4 planks of wood (softwood, 60cm x 15cm x 1.5cm)",
                "Wood glue",
                "Sandpaper (80-grit and 120-grit)",
                "Varnish or wood stain",
                "Nails or screws (optional reinforcement)",
            ],
            "steps": [
                "Draw a labelled sketch of your bookshelf with dimensions.",
                "Measure and mark all pieces using a pencil and try-square.",
                "Clamp wood securely and cut using a tenon saw.",
                "Sand all surfaces smooth, starting with 80-grit then 120-grit.",
                "Apply wood glue to joints and assemble the frame.",
                "Use clamps to hold joints while glue dries (24 hours).",
                "Optional: reinforce joints with nails or screws.",
                "Sand assembled bookshelf again lightly.",
                "Apply two coats of varnish, allowing drying between coats.",
                "Inspect finished product and present to class.",
            ],
            "safety_notes": [
                "Always clamp wood before sawing \u2014 never hold with your hand.",
                "Wear safety goggles when sanding.",
                "Use varnish in a well-ventilated area.",
                "Report any tool damage to the teacher immediately.",
            ],
            "assessment": {
                "accuracy_of_measurement": 20,
                "quality_of_joints": 20,
                "surface_finish": 20,
                "safety_practices": 20,
                "presentation": 20,
            },
        },
        answer_key="Practical project \u2014 assess using rubric (total 100 marks).",
    ),
    dict(
        title="Workshop Safety \u2014 Do You Know the Rules?",
        project_type="safety_quiz",
        level="b7",
        strand="health_safety",
        topic="Health & Safety in the Workshop",
        description=(
            "This quiz tests students on essential workshop safety rules. "
            "Understanding and following safety procedures prevents accidents "
            "and ensures a productive learning environment."
        ),
        content={
            "questions": [
                {
                    "q": "What should you always wear to protect your eyes in the workshop?",
                    "options": ["Sunglasses", "Safety goggles", "Reading glasses", "Nothing"],
                    "answer": 1,
                    "explanation": "Safety goggles protect against flying debris, dust, and splashes.",
                },
                {
                    "q": "What is the first thing you should do if you cut yourself?",
                    "options": ["Continue working", "Tell a friend", "Report to the teacher and apply first aid", "Ignore it"],
                    "answer": 2,
                    "explanation": "Always report injuries immediately so proper first aid can be given.",
                },
                {
                    "q": "Why should loose clothing and jewellery be removed before using machines?",
                    "options": ["They get dirty", "They can get caught in moving parts", "The teacher said so", "It looks better"],
                    "answer": 1,
                    "explanation": "Loose items can be caught in rotating machinery, causing serious injury.",
                },
                {
                    "q": "Where should you store tools after use?",
                    "options": ["On the floor", "In your bag", "In the designated tool rack or cabinet", "On the workbench"],
                    "answer": 2,
                    "explanation": "Proper storage prevents damage to tools and tripping hazards.",
                },
                {
                    "q": "What does a fire extinguisher with a RED label contain?",
                    "options": ["Foam", "Water", "CO2", "Powder"],
                    "answer": 1,
                    "explanation": "Red-label extinguishers contain water, suitable for wood and paper fires.",
                },
                {
                    "q": "What should you do before plugging in an electrical tool?",
                    "options": ["Check the cable for damage", "Just plug it in", "Ask a classmate", "Test it on metal"],
                    "answer": 0,
                    "explanation": "Always inspect cables and plugs for damage before use to prevent electric shock.",
                },
                {
                    "q": "What is the correct way to carry a saw?",
                    "options": ["Blade facing up", "Blade pointing forward", "Blade pointing down, close to your body", "Over your shoulder"],
                    "answer": 2,
                    "explanation": "Carry saws with the blade pointing down to avoid injuring yourself or others.",
                },
                {
                    "q": "Why must you never run in the workshop?",
                    "options": ["You might get tired", "You could slip or bump into someone carrying tools", "The teacher might shout", "It wastes time"],
                    "answer": 1,
                    "explanation": "Running in workshops risks collisions with people handling sharp or heavy tools.",
                },
            ],
            "safety_rules_summary": [
                "Always wear appropriate PPE (goggles, apron, gloves).",
                "Never use a tool unless trained by the teacher.",
                "Keep your workspace clean and tidy.",
                "Report all accidents and broken tools immediately.",
                "No running, pushing, or horseplay in the workshop.",
                "Tie back long hair and remove jewellery.",
                "Know the location of fire extinguishers and first aid kits.",
                "Follow the teacher's instructions at all times.",
            ],
        },
        answer_key="1) B  2) C  3) B  4) C  5) B  6) A  7) C  8) B  (8 marks total)",
    ),
    dict(
        title="Know Your Tools \u2014 Woodwork Hand Tools",
        project_type="tool_id",
        level="b7",
        strand="tools",
        topic="Identification of Woodwork Tools",
        description=(
            "Students will learn to identify, name, and describe the function of "
            "common hand tools used in woodwork. Correct tool identification is "
            "essential for safety and efficiency in the workshop."
        ),
        content={
            "tools": [
                {
                    "name": "Tenon Saw",
                    "description": "A back saw with a rectangular blade stiffened by a metal or brass back.",
                    "purpose": "Making straight, accurate cuts in wood, especially for tenon joints.",
                    "safety": "Always use a bench hook or vice to hold the workpiece.",
                },
                {
                    "name": "Claw Hammer",
                    "description": "A hammer with a flat striking face and a curved claw on the back.",
                    "purpose": "Driving nails into wood and removing them with the claw.",
                    "safety": "Grip the handle near the end for better control. Never use a damaged handle.",
                },
                {
                    "name": "Smoothing Plane",
                    "description": "A hand plane with an adjustable blade used to shave thin layers of wood.",
                    "purpose": "Smoothing and flattening wood surfaces after sawing.",
                    "safety": "Always plane in the direction of the grain. Keep fingers away from the blade.",
                },
                {
                    "name": "Try Square",
                    "description": "An L-shaped measuring tool with a metal blade and wooden stock.",
                    "purpose": "Checking and marking 90-degree angles on wood.",
                    "safety": "Handle carefully \u2014 the metal edge can be sharp.",
                },
                {
                    "name": "Chisel",
                    "description": "A tool with a flat steel blade bevelled on one side.",
                    "purpose": "Cutting, shaping, and carving wood, especially for joints.",
                    "safety": "Always cut away from your body. Use a mallet, not a hammer.",
                },
                {
                    "name": "Marking Gauge",
                    "description": "A wooden device with an adjustable pin for scribing lines parallel to an edge.",
                    "purpose": "Marking consistent lines for cutting or planing.",
                    "safety": "Set the gauge carefully and lock it before use.",
                },
            ],
            "matching_exercise": {
                "instruction": "Match each tool to its primary purpose.",
                "pairs": [
                    {"tool": "Tenon Saw", "purpose": "Making straight cuts"},
                    {"tool": "Claw Hammer", "purpose": "Driving and removing nails"},
                    {"tool": "Smoothing Plane", "purpose": "Flattening surfaces"},
                    {"tool": "Try Square", "purpose": "Checking right angles"},
                    {"tool": "Chisel", "purpose": "Shaping and carving"},
                    {"tool": "Marking Gauge", "purpose": "Scribing parallel lines"},
                ],
            },
        },
        answer_key="Tenon Saw=Straight cuts, Claw Hammer=Nails, Smoothing Plane=Flattening, Try Square=Right angles, Chisel=Shaping, Marking Gauge=Parallel lines",
    ),
    dict(
        title="Tie-Dye Textile Design \u2014 Innovation Challenge",
        project_type="innovation",
        level="b8",
        strand="innovation",
        topic="Textile Design & Entrepreneurship",
        description=(
            "Students will design and create tie-dye fabric using traditional and "
            "modern techniques. This project combines creativity with practical "
            "skills and introduces basic entrepreneurship concepts."
        ),
        content={
            "objectives": [
                "Understand the history and cultural significance of tie-dye in Ghana.",
                "Learn at least three tying techniques (spiral, crumple, fold).",
                "Create a unique tie-dye design on white cotton fabric.",
                "Develop a simple business plan for selling tie-dye products.",
            ],
            "materials": [
                "White cotton fabric (1 metre per student)",
                "Fabric dyes (at least 3 colours)",
                "Rubber bands, string, or wax",
                "Plastic buckets for dye baths",
                "Rubber gloves and aprons",
                "Salt (to fix colour)",
                "Plastic sheets to protect surfaces",
            ],
            "techniques": [
                {"name": "Spiral", "description": "Pinch fabric at centre and twist into a flat disc. Secure with rubber bands in a star pattern."},
                {"name": "Crumple", "description": "Randomly scrunch the fabric into a ball and bind tightly with string."},
                {"name": "Fold & Bind", "description": "Fold fabric into an accordion pattern, then bind at intervals with rubber bands."},
                {"name": "Wax Resist (Batik)", "description": "Apply melted wax to areas you want to remain undyed, then dip in dye."},
            ],
            "steps": [
                "Pre-wash the cotton fabric to remove sizing.",
                "Choose a tying technique and prepare your fabric.",
                "Mix fabric dyes according to instructions.",
                "Wearing gloves, apply dye to the tied fabric.",
                "Let the fabric sit for 6-24 hours for colour absorption.",
                "Rinse in cold water until water runs clear.",
                "Remove ties and unfold to reveal the pattern.",
                "Iron the fabric to set the design.",
                "Display finished designs for class critique.",
                "Optional: sew a simple product (headband, bag, cushion cover).",
                "Create a pricing sheet for your products.",
                "Present your design and business plan to the class.",
            ],
            "entrepreneurship": {
                "tasks": [
                    "Calculate the cost of materials for one tie-dye cloth.",
                    "Set a selling price that covers costs and gives a fair profit.",
                    "Design a brand name and logo for your tie-dye business.",
                    "Write a 30-second sales pitch for your product.",
                ],
            },
        },
        answer_key="Practical project. Assess creativity, technique, finish quality, and business plan viability.",
    ),
    dict(
        title="Practical Skills Assessment \u2014 Basic Electrical Wiring",
        project_type="rubric",
        level="b9",
        strand="tools",
        topic="Electrical Installation Skills",
        description=(
            "This rubric assesses students on their ability to safely wire a simple "
            "electrical circuit. Students must demonstrate knowledge of components, "
            "correct wiring technique, and adherence to safety procedures."
        ),
        content={
            "rubric": [
                {
                    "criterion": "Component Identification",
                    "excellent": "Correctly identifies all components (switch, socket, fuse, cable, earth wire) and explains their function.",
                    "good": "Identifies most components with minor errors in explanation.",
                    "satisfactory": "Identifies basic components but cannot explain functions.",
                    "needs_improvement": "Cannot identify key components.",
                    "max_marks": 20,
                },
                {
                    "criterion": "Wiring Technique",
                    "excellent": "Wires stripped neatly, connections tight and secure, correct colour coding (brown=live, blue=neutral, green-yellow=earth).",
                    "good": "Mostly correct with one minor issue.",
                    "satisfactory": "Several loose connections or colour-coding errors.",
                    "needs_improvement": "Incorrect or unsafe wiring.",
                    "max_marks": 25,
                },
                {
                    "criterion": "Safety Procedures",
                    "excellent": "Follows all safety rules: checks circuit is dead, uses insulated tools, wears PPE.",
                    "good": "Follows most safety rules with one minor lapse.",
                    "satisfactory": "Needs reminders about safety procedures.",
                    "needs_improvement": "Ignores safety rules; creates hazards.",
                    "max_marks": 25,
                },
                {
                    "criterion": "Circuit Testing",
                    "excellent": "Uses multimeter correctly to test continuity and voltage. Circuit works first time.",
                    "good": "Tests circuit with minor guidance. Circuit works after small adjustment.",
                    "satisfactory": "Needs significant help to test. Circuit has issues.",
                    "needs_improvement": "Cannot test circuit. Circuit does not work.",
                    "max_marks": 15,
                },
                {
                    "criterion": "Neatness & Presentation",
                    "excellent": "Work area clean, wires tucked neatly, professional finish.",
                    "good": "Generally tidy with minor issues.",
                    "satisfactory": "Messy work area, cables untidy.",
                    "needs_improvement": "Very untidy, unsafe workspace.",
                    "max_marks": 15,
                },
            ],
            "total_marks": 100,
            "grade_boundaries": {
                "A": "80-100",
                "B": "65-79",
                "C": "50-64",
                "D": "40-49",
                "F": "Below 40",
            },
        },
        answer_key="Use rubric to assess. Total: 100 marks. Grade boundaries: A=80+, B=65-79, C=50-64, D=40-49, F<40.",
    ),
]

created = 0
for item in tvet_data:
    obj, new = TVETProject.objects.get_or_create(
        profile=profile, title=item["title"], defaults=item,
    )
    if new:
        created += 1
        print(f"  + TVET: {obj.title}")
    else:
        print(f"  = TVET (exists): {obj.title}")
print(f"TVET Workshop: {created} created\n")


# ── Final summary ───────────────────────────────────────────────────────────
lc = LiteracyExercise.objects.filter(profile=profile).count()
cc = CitizenEdActivity.objects.filter(profile=profile).count()
tc = TVETProject.objects.filter(profile=profile).count()
print(f"=== TOTALS for profile {profile} ===")
print(f"  LiteracyExercise : {lc}")
print(f"  CitizenEdActivity: {cc}")
print(f"  TVETProject      : {tc}")
print("Done!")
