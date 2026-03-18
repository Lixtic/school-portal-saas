import json
import logging
import random
import re
from typing import Dict, List, Optional
from django.utils import timezone
from django.conf import settings
from teachers.models import LessonPlan, Teacher
from academics.ai_tutor import (
    _get_openai_api_key,
    _post_chat_completion,
    get_active_ai_model,
    get_openai_chat_model,
)

logger = logging.getLogger(__name__)

class AuraGenEngine:
    """
    Aura-T Generative Pedagogical Engine.
    Uses AI service to generate educational content.
    """

    @staticmethod
    def generate_assignment_package(lesson_plan: LessonPlan, topic_prompt: Optional[str] = None) -> Dict:
        """
        Generates a complete differentiated assignment package grounded in the
        Aura-T lesson plan. Applies Ghana cultural contexts, GES CBC alignment,
        Support/Extension split, and device-equity rules.
        """
        topic       = topic_prompt if topic_prompt else lesson_plan.topic
        subject     = lesson_plan.subject.name
        grade_level = lesson_plan.school_class.name

        # Extract Aura-T plan context for richer prompting
        intro_text  = lesson_plan.introduction  or ""
        present_text = lesson_plan.presentation or ""
        eval_text   = lesson_plan.evaluation    or ""
        obj_text    = lesson_plan.objectives    or ""

        # Pull the Ghanaian hook context used in the plan (first 300 chars of intro)
        hook_snippet = intro_text[:300].strip()
        # Pull Support and Extension path content
        sp_snippet = ""
        ex_snippet = ""
        if "SUPPORT PATH" in present_text:
            sp_start = present_text.find("SUPPORT PATH")
            ex_start = present_text.find("EXTENSION PATH")
            sp_snippet = present_text[sp_start: ex_start if ex_start > sp_start else sp_start + 600].strip()[:400]
            ex_snippet = present_text[ex_start: ex_start + 600].strip()[:400] if ex_start != -1 else ""
        # Pull Data-Trigger gaps
        dt_snippet = ""
        if "DATA-TRIGGER" in eval_text:
            dt_start = eval_text.find("DATA-TRIGGER")
            dt_snippet = eval_text[dt_start: dt_start + 500].strip()[:400]

        system_prompt = f"""You are Aura-T, an advanced pedagogical AI for Ghanaian teachers.
Generate a DIFFERENTIATED assignment package for {grade_level} {subject} on \"{topic}\".

═══════════════════════════════════════════════════════
LESSON CONTEXT (from the Aura-T lesson plan)
═══════════════════════════════════════════════════════
GES Indicator / Objectives: {obj_text[:300]}
Ghanaian Hook used in this lesson: {hook_snippet}
Support Path (what struggling students did in class): {sp_snippet}
Extension Path (what advanced students did in class): {ex_snippet}
Data-Trigger gaps identified: {dt_snippet}

USE THIS CONTEXT to make every task CONTINUOUS with what was done in class.
The Ghanaian hook context must appear in at least one question per tier.
The Data-Trigger gaps must be directly addressed in the Support task.

═══════════════════════════════════════════════════════
FIVE HARD RULES
═══════════════════════════════════════════════════════
RULE 1 — TWO TIERS, GENUINELY DIFFERENT:
  support_task   = pen-and-paper only, structured, addresses the Data-Trigger gap, DOK 1-2
  extension_task = higher-order (DOK 3-4), builds on Extension Path, device-OPTIONAL
  "Device-optional" means: write the task as two versions:
    \"If you have a phone/computer: [digital version]. If not: [paper version].\"

RULE 2 — NO CONCEPT DRIFT:
  Both tiers must stay on the SINGLE concept of \"{topic}\". No related sub-topics.

RULE 3 — GHANA CULTURAL GROUNDING:
  Use the SAME Ghanaian context from the lesson hook above in at least one question per tier.
  Name the specific place, organisation, or practice. Do NOT use a generic or new context.

RULE 4 — RUBRIC IS CRITERION-REFERENCED:
  Each rubric row must describe observable STUDENT BEHAVIOUR — not the teacher's opinion.
  Use verbs: \"Student accurately identifies...\", \"Student constructs...\", \"Student justifies...\"

RULE 5 — CULTURAL SCAFFOLD:
  If using a proverb, Adinkra symbol, or Ghanaian idiom, always provide:
  - English meaning in brackets
  - A model sentence starter so students know the expected form

═══════════════════════════════════════════════════════
JSON SCHEMA — return EXACTLY this structure
═══════════════════════════════════════════════════════
{{
  "assignment": {{
    "title": "Engaging, topic-specific title",
    "ges_indicator": "GES CBC indicator code e.g. B7.2.2.1.1",
    "ghana_context": "One-sentence statement of the Ghanaian context used",
    "description": "Brief teacher-facing overview of the package"
  }},
  "support_task": {{
    "title": "Short descriptive title for the support task",
    "gap_targeted": "Which Data-Trigger gap or Pulse Check miss this addresses",
    "instructions": "Student-facing instructions. Pen-and-paper only. DOK 1-2. Structured steps.",
    "ghana_context_link": "How the Ghana context appears in this task (1 sentence)",
    "estimated_time": "e.g. 20 minutes"
  }},
  "extension_task": {{
    "title": "Short descriptive title for the extension task",
    "builds_on": "Which Extension Path class activity this continues",
    "instructions_digital": "Version for students with a phone or computer",
    "instructions_paper": "Version for students without a device",
    "ghana_context_link": "How the Ghana context appears in this task (1 sentence)",
    "estimated_time": "e.g. 25-30 minutes"
  }},
  "rubric": [
    {{
      "criteria": "Criterion name",
      "weight": "Percentage as integer e.g. 30",
      "levels": {{
        "excellent": "Observable behaviour at mastery",
        "proficient": "Observable behaviour at competency",
        "basic": "Observable behaviour at partial credit",
        "limited": "Observable behaviour at minimum engagement"
      }}
    }}
  ]
}}
"""

        try:
            payload = {
                "model": get_active_ai_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Generate the full differentiated assignment package for '{topic}' "
                        f"({grade_level}, {subject}). "
                        "Apply all five rules strictly. "
                        "Support task: pen-and-paper, DOK 1-2, addresses the Data-Trigger gap. "
                        "Extension task: DOK 3-4, device-optional with paper fallback, continues the class Extension Path. "
                        "Both tasks use the SAME Ghanaian context from the hook — no new contexts."
                    )}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            response = _post_chat_completion(payload, _get_openai_api_key())
            content = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content)

            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                **data
            }

        except Exception as e:
            logger.error("AI assignment generation failed: %s", e)
            return AuraGenEngine._generate_mock_fallback(topic, subject, grade_level)

    @staticmethod
    def generate_lesson_plan(topic: str, subject: str, grade_level: str, sub_strand: str = '', indicator: str = '') -> Dict:
        """
        Generate a full structured lesson plan in the Aura-T format.
        Every plan MUST include: Localized Hook, AI Pulse Check, two Learning Paths,
        and a Data-Trigger. These are non-negotiable.
        """
        # Build context line for sub-strand and indicator
        sub_strand_ctx = f'\nSub-strand: "{sub_strand}"' if sub_strand else ''
        indicator_ctx = f'\nTarget Indicator: {indicator}' if indicator else ''

        system_prompt = f"""You are Aura-T, an advanced pedagogical AI for Ghanaian teachers trained on the GES Competency-Based Curriculum.
Generate a rigorous, dynamic lesson plan for {grade_level} {subject} on "{topic}".{sub_strand_ctx}{indicator_ctx}
The lesson MUST be tailored specifically to the sub-strand and indicator provided — every activity, assessment, and homework must directly address and measure the target indicator.

═══════════════════════════════════════════════════════
CONTEXT PILLARS — ANALYZE THESE BEFORE DRAFTING THE PLAN
═══════════════════════════════════════════════════════
Before writing a single instructional line, lock in all three pillars.
The plan's depth, hook, Pulse Check questions, paths, and homework must
be shaped by this analysis — not lifted from a generic template.

┌─────────────────────────────────────────────────────┐
│ PILLAR 1 — LEARNER DNA                              │
└─────────────────────────────────────────────────────┘
Mastery baseline for {grade_level} students on {topic} in {subject}:
  · Assume roughly 60 % are at grade level, 25 % need scaffolding, 15 % are ready to extend.
  · Identify the ONE prior concept that 30–40 % of students have NOT yet internalized.
    This gap drives your SUPPORT PATH and Q1 of the Pulse Check.
  · Enumerate the 2–3 most frequent misconceptions or procedural errors students make
    when first encountering {topic}. These shape Q2 of the Pulse Check and DATA-TRIGGER.

Common stuck-point patterns (use whichever apply to {topic}):
  — Confusing correlation with causation in data tasks
  — Reversing input/output roles in functions and processes
  — Overgeneralizing a rule from the last lesson to an unrelated context
  — Skipping intermediate steps when they have seen the answer format before
  — Translating real-world contexts into abstract notation (or vice versa)
  — Misreading scale or units in graphs, maps, and measurement tasks
  — Surface-feature matching: treating problems as identical because they look similar

Top regional interests — weave at least ONE into the lesson (hook, example, or homework):
  • Azonto dance and its geometric, rhythmic, and call-and-response patterns
  • Cocoa, cashew, and yam farming cycles — seasonality, soil, yield, and income
  • Digital Trading: MoMo transfers, airtime resale, Jumia deliveries, Tonaton listings
  • Football academies and performance analytics (Right to Dream, Asante Kotoko SC)
  • Jollof, waakye, and kenkey — measurement, chemistry, and cultural identity in cooking
  • Kente and batik micro-enterprise — weaving geometry, dyeing chemistry, pricing
  • Susu savings groups and rotating credit — financial mathematics in community life
  • Nollywood/Ghallywood storytelling — narrative structure, editing, marketing
  • Krobo beadwork and Bolgatanga pottery — craft geometry, symmetry, cultural heritage
  • Informal tech economy — phone repair, charging stations, SIM-card micro-trade
  • School choral festivals and concert band culture — rhythm, notation, teamwork
  • Community health campaigns — NHIS enrolment, malaria nets, vaccination data
  • Timber and furniture carpentry workshops in Kumasi and Cape Coast
  • Canoe fishing, trawlers, and cold-chain storage in Takoradi and Keta
  • Shea butter and groundnut oil processing in the Northern and Upper Regions
  • Radio and TV broadcasting — GBC, Adom FM, UTV — media literacy and persuasion
  • Nkrumah Circle, Oguaa Fetu Ahoolie, and Homowo festival logistics and organization

┌─────────────────────────────────────────────────────┐
│ PILLAR 2 — GES STANDARDS MAPPING                   │
└─────────────────────────────────────────────────────┘
Every plan MUST map to an EXACT GES CBC indicator code.
Format: B[grade].[strand].[sub-strand].[content-standard].[indicator]

COMPUTING / ICT:
  B7.1.1.1.1 — Identify and describe hardware components and their functions
  B7.1.1.1.2 — Distinguish between input, processing, output, and storage devices
  B7.1.2.1.1 — Apply file management: create, save, rename, and organize folders
  B7.1.2.2.1 — Use word processing tools to type, format, and print documents
  B7.1.3.1.1 — Identify internet safety, netiquette, and responsible digital citizenship
  B7.2.1.1.1 — Create basic spreadsheets; apply SUM, AVERAGE, and simple formulas
  B7.2.2.1.1 — Use presentation software to organize and present information with slides
  B8.1.1.1.1 — Describe types of software: system, application, and programming languages
  B8.1.2.1.1 — Apply advanced word processing: tables, headers, footers, mail merge
  B8.1.2.2.1 — Create and format spreadsheets with conditional formulas (IF, COUNT, MAX)
  B8.1.3.1.1 — Design a basic web page using HTML structure and semantic tags
  B8.2.1.1.1 — Demonstrate email, cloud tools, and online collaboration safely
  B8.2.2.1.1 — Create multimedia presentations integrating images, audio, and transitions
  B9.1.1.1.1 — Differentiate programming paradigms; design algorithms using flowcharts
  B9.1.2.1.1 — Write basic programs using sequence, selection, and iteration constructs
  B9.1.3.1.1 — Evaluate digital security threats: phishing, malware, and identity theft
  B9.2.1.1.1 — Analyze and visualize data using charts and graphs in spreadsheet software
  B9.2.2.1.1 — Design and critically evaluate a complete digital project (website, app, or database)

MATHEMATICS:
  B7.1.1.1.1 — Classify and operate on whole numbers, integers, and fractions
  B7.1.2.1.1 — Apply properties of ratio and proportion in real-life contexts
  B7.1.3.1.1 — Solve problems involving percentages, profit, and loss
  B7.2.1.1.1 — Identify and classify 2D shapes; calculate perimeter and area
  B7.2.2.1.1 — Collect, organize, and represent data using tables, bar charts, and pie charts
  B7.3.1.1.1 — Use algebraic expressions to model and solve word problems
  B8.1.1.1.1 — Extend operations to rational and irrational numbers
  B8.1.2.1.1 — Apply percentage applications: discount, commission, tax, simple interest
  B8.2.1.1.1 — Calculate surface area and volume of 3D solids
  B8.2.2.1.1 — Interpret and analyze data from frequency tables and histograms
  B8.3.1.1.1 — Solve linear equations and simultaneous equations in two variables
  B9.1.1.1.1 — Operate on indices, surds, and standard form
  B9.1.2.1.1 — Apply Pythagoras' theorem and basic trigonometric ratios (sin, cos, tan)
  B9.2.1.1.1 — Compute probability of single and combined events
  B9.2.2.1.1 — Construct and interpret scatter graphs; calculate mean, median, mode, range
  B9.3.1.1.1 — Solve quadratic equations by factorisation and the quadratic formula

ENGLISH LANGUAGE:
  B7.1.1.1.1 — Demonstrate active listening and responding strategies in academic discussions
  B7.2.1.1.1 — Apply reading comprehension: inference, main idea, context vocabulary
  B7.3.1.1.1 — Write structured paragraphs with topic, supporting, and concluding sentences
  B7.3.2.1.1 — Identify and use nouns, pronouns, verbs, and adjectives correctly
  B7.4.1.1.1 — Deliver short oral presentations using clear pronunciation and body language
  B8.1.1.1.1 — Distinguish fact from opinion in spoken and written texts
  B8.2.1.1.1 — Analyze literary devices: simile, metaphor, personification, alliteration
  B8.3.1.1.1 — Write narrative, expository, and argumentative essays
  B8.3.2.1.1 — Apply grammar: tense consistency, subject-verb agreement, punctuation
  B9.1.1.1.1 — Evaluate persuasive techniques in speech and writing
  B9.2.1.1.1 — Compare texts across genres; analyze author's purpose and audience
  B9.3.1.1.1 — Produce extended writing: reports, formal letters, and creative fiction
  B9.4.1.1.1 — Conduct and present research using credible primary and secondary sources

SCIENCE:
  B7.1.1.1.1 — Identify characteristics and classify living and non-living things
  B7.1.2.1.1 — Describe cell structure and function; compare plant and animal cells
  B7.2.1.1.1 — Investigate properties of matter: states, particle model, and changes of state
  B7.2.2.1.1 — Classify pure substances and mixtures; describe separation methods
  B7.3.1.1.1 — Describe forces: gravity, friction, and magnetic force and their effects
  B7.3.2.1.1 — Investigate forms of energy: light, heat, sound, electrical, and kinetic
  B8.1.1.1.1 — Describe nutrition, the digestive system, and balanced diet in humans
  B8.1.2.1.1 — Investigate reproduction in plants and animals; explain pollination and fertilization
  B8.2.1.1.1 — Explain chemical changes: reactants, products, and indicators of reaction
  B8.3.1.1.1 — Apply work, power, and simple machines: levers, pulleys, inclined planes, gears
  B9.1.1.1.1 — Analyze ecosystems: food chains, food webs, energy flow, and biodiversity
  B9.2.1.1.1 — Describe atomic structure, elements, compounds, and the Periodic Table
  B9.3.1.1.1 — Apply Ohm's Law: investigate voltage, current, and resistance in circuits
  B9.3.2.1.1 — Investigate the solar system, Earth's rotation, revolution, and the seasons

SOCIAL STUDIES:
  B7.1.1.1.1 — Describe Ghana's physical features: relief, drainage, climate, and vegetation zones
  B7.1.2.1.1 — Analyze population distribution and settlement patterns in Ghana
  B7.2.1.1.1 — Explain Ghana's pre-colonial history and formation of major states
  B7.3.1.1.1 — Describe Ghana's governance structure and the functions of the three arms
  B8.1.1.1.1 — Analyze the impact of colonialism and Ghana's independence struggle
  B8.2.1.1.1 — Apply map-reading skills: scale, coordinates, direction, and conventional symbols
  B8.3.1.1.1 — Describe West African integration: ECOWAS, AU, and key global institutions
  B9.1.1.1.1 — Evaluate environmental issues: deforestation, galamsey, and coastal erosion
  B9.2.1.1.1 — Analyze Ghana's economic sectors: agriculture, mining, manufacturing, services
  B9.3.1.1.1 — Discuss democracy, elections, human rights, and civic responsibility in Ghana

FRENCH:
  B7.1.1.1.1 — Use basic greetings, introductions, and classroom vocabulary in French
  B7.2.1.1.1 — Apply être and avoir in present tense; describe people and objects
  B8.1.1.1.1 — Use regular -er, -ir, -re verbs and reflexive verbs in conversational context
  B8.2.1.1.1 — Describe daily routines using time expressions and frequency adverbs
  B9.1.1.1.1 — Write and respond to short formal and informal letters in French
  B9.2.1.1.1 — Use passé composé and imparfait to narrate and describe past events

RELIGIOUS & MORAL EDUCATION (RME):
  B7.1.1.1.1 — Describe the nature and attributes of God in Christianity, Islam, and African Religion
  B7.2.1.1.1 — Apply moral virtues: honesty, respect, responsibility, compassion, and tolerance
  B8.1.1.1.1 — Analyze rites of passage: birth, puberty, marriage, and death across three religions
  B9.1.1.1.1 — Evaluate the role of religion in national development and peaceful coexistence

PHYSICAL EDUCATION (PE):
  B7.1.1.1.1 — Demonstrate fundamental movement skills: locomotor, non-locomotor, manipulative
  B7.2.1.1.1 — Apply rules and team strategies in invasion games: football, basketball, handball
  B8.1.1.1.1 — Execute athletics skills: sprint start, relay baton-passing, long jump approach
  B9.1.1.1.1 — Design a personal fitness plan targeting cardiovascular endurance and flexibility

MATCH {topic} in {subject} for {grade_level} to the MOST SPECIFIC code above.
If the match is not exact, adapt the nearest code and note the adaptation in one clause.
The plan header MUST show the real code in format B7.2.2.1.1 — NOT a vague description.

┌─────────────────────────────────────────────────────┐
│ PILLAR 3 — CORE COMPETENCIES MAPPING               │
└─────────────────────────────────────────────────────┘
For EVERY plan, tag the exact PHASE and ACTIVITY where each competency is developed.

GES CBC CORE COMPETENCIES:
  🧠 Critical Thinking & Problem Solving — Where students analyse, compare, infer, or solve
  💡 Creativity & Innovation — Where students design, produce, or invent something original
  🗣️ Communication & Collaboration — Where students discuss, present, peer-teach, or debate
  💻 Digital Literacy — Where technology is used, modelled, or critically examined
  🌍 Cultural Identity & Global Citizenship — Where Ghanaian context, values, or global links appear
  🏆 Personal Development & Leadership — Students show self-management, initiative, or peer leadership
  💰 Financial Literacy — Money decisions, budgeting, pricing, or economic reasoning featured

MINIMUM REQUIREMENT — EVERY PLAN:
  💻 Digital Literacy    — MUST appear. No exceptions.
  🧠 Critical Thinking   — MUST appear. No exceptions.
  🌍 Cultural Identity   — MUST appear. No exceptions (this is always the hook + paths).
  Add any others that are genuinely triggered — do NOT manufacture connections.

═══════════════════════════════════════════════════════
FOUR NON-NEGOTIABLE REQUIREMENTS — EVERY PLAN, NO EXCEPTIONS
═══════════════════════════════════════════════════════

① LOCALIZED HOOK — Phase 1 must open with a culturally grounded hook drawn from Ghana.

  ══ HOOK DIVERSITY RULE — READ CAREFULLY ══
  You have a known bias toward "a trader in [market] uses [device]…" — this pattern is BANNED.
  Do NOT write a hook where a market trader, market stall owner, or market vendor is the protagonist.
  Do NOT use Kumasi Central Market, Makola Market, Kejetia, Kaneshie, or any market setting.
  Do NOT describe someone selling, pricing, or buying goods as the hook scenario.
  These patterns are overused and no longer relevant or novel for students.

  INSTEAD, choose one of the following rich Ghanaian contexts that is ACTUALLY RELEVANT to {topic}:

  SCIENCE & ENGINEERING contexts:
  - Akosombo Dam hydroelectric turbines and electrical generation
  - BOST (Bulk Oil Storage and Transportation) fuel pipeline network
  - Tema Motorway construction and road engineering
  - Ghana Space Science and Technology Institute (GSSTI) satellite imaging
  - Tema Shipyard dry-dock mechanics
  - Bauxite/gold mining operations in Obuasi or Tarkwa
  - Cocoa fermentation and drying science on a farm in Ashanti Region

  ARTS, CULTURE & LANGUAGE contexts:
  - Adinkra symbol printing on cloth in Ntonso, near Kumasi
  - Kente strip weaving on a hand loom in Bonwire
  - Kpanlogo drumming pattern structures in Accra
  - Larabanga Mosque architectural symmetry (oldest mosque in Ghana)
  - Nkyinkyim movement in Ghanaian dance (adaptability)

  DIGITAL & INNOVATION contexts:
  - MoMo (Mobile Money) transaction flow and digital security
  - Zipline drone delivery network in the Upper West Region
  - mPedigree medicine-authentication SMS system
  - MEST incubator startup pitches in Accra
  - GhanaPostGPS digital address system

  CIVIC & ENVIRONMENTAL contexts:
  - Volta River Authority water management decisions
  - Savannah tree-planting initiatives in the Northern Region
  - Bolgatanga basketry cooperative and sustainable materials
  - Fishing communities and seasonal patterns in Elmina or Keta
  - National Service Scheme deployment logistics

  HISTORICAL & INTELLECTUAL contexts:
  - Nkrumah's Atoms for Peace nuclear vision and GAEC founding
  - J.B. Danquah's legal writing and argument structure
  - Efua Sutherland's storytelling architecture in drama
  - The Manhyia Palace oral archive and record-keeping

  SELECTION RULE: Pick the ONE context from the list above that creates the most natural,
  specific, and intellectually honest bridge to {topic}. Do not force a weak connection.
  If the topic is about slides/presentations, use a context where someone in Ghana actually
  communicates structured information visually — e.g. GSSTI analysts presenting satellite data,
  a Zipline operations briefing, an Akosombo engineer's maintenance diagram, NOT a trader.

  The hook MUST name a specific Ghanaian place, organisation, role, or object.
  Make the conceptual link to {topic} explicit in 2–3 sentences — do not let students guess it.

② AI PULSE CHECK — Phase 1 must include a "🔍 PULSE CHECK" block: exactly 3 diagnostic questions
  delivered verbally or on the whiteboard. Students respond quickly (hands up / slate / verbal).
  Q1 = a TRUE/FALSE STATEMENT that probes prerequisite knowledge about {topic}.
       MUST be phrased as a declarative statement students can answer True or False — NOT a "What is..." or "How..." question.
       Example format: "{topic} is [a clear factual claim] — True or False?"
  Q2 = a TRUE/FALSE STATEMENT that targets the most common misconception about {topic}.
       MUST be phrased as a statement containing a common wrong belief — the correct answer should be False.
       Example format: "Students often believe [misconception]. True or false? If false, correct it."
  Q3 = an OPEN APPLICATION QUESTION that connects {topic} to the hook context (Ghanaian setting).
       This is the only open-ended question — no True/False required.
  Teacher mentally logs which students hesitate or answer Q1/Q2/Q3 incorrectly.
  Those specific gaps drive the Phase 3 DATA-TRIGGER.

③ TWO LEARNING PATHS — Phase 2 MUST split into two substantively different pathways:

  🟢 SUPPORT PATH — for students who struggled in the Pulse Check.
     RULES FOR SUPPORT PATH:
     - Lowest possible cognitive load entry point. Start with what they already know.
     - Use sentence frames, partially completed examples, matching tasks, or visual diagrams.
     - Teacher or a peer stays close. Short, checkable steps.
     - NEVER require prior mastery or abstract thinking to begin.

  🔵 EXTENSION PATH — for students who answered the Pulse Check confidently.
     RULES FOR EXTENSION PATH:
     - Must demand higher-order thinking (analysis, evaluation, creation — Bloom's levels 4–6).
     - Must connect {topic} to a real-world Ghanaian application OR another subject area.
     - Should be executable independently, without the teacher hovering.
     - MUST be substantively different from Support Path — not just the same task made harder.

  Both paths MUST stay on the single concept of "{topic}". No concept drift into related sub-topics.

④ CHECKPOINT QUESTIONS — Phase 2 MUST end with a "🔲 CHECKPOINT QUESTIONS" block:
  Three short, convergent questions embedded immediately AFTER both learning paths.
  These are live active-assessment probes the teacher reads aloud or posts on the board
  while students hold up whiteboards or tap a response on their device.
  - CQ1 = Foundational: Did everyone get the core idea? (closed, recall-level)
  - CQ2 = Process: Can students apply {topic} in a structured context? (one-step)
  - CQ3 = Transfer: Can they connect {topic} to the real world? (requires reasoning)
  Each CQ must include a HEATMAP NOTE: the teacher action for Red / Amber / Green students.
  These triggers feed the Mastery Heatmap on the teacher's Command Center.

⑤ DATA-TRIGGER — Phase 3 MUST contain a "📊 DATA-TRIGGER" block:
  For EACH of the three Pulse Check questions, state the EXACT teacher action for students who missed it.
  Be specific: name the reteach method, re-pairing strategy, or micro-task for next lesson.
  Also state how to activate Extension Path students as resources (peer leaders, demonstrators, etc.).
  DATA-TRIGGER is a teacher planning tool — it must NOT appear in student-facing content.

⑥ MASTERY SPRINT — Phase 3 MUST include a "🏁 MASTERY SPRINT" Exit Ticket block:
  Three focused questions students answer SOLO — no hints, no discussion, no prompting.
  MS1 = Recall (no scaffolding — tests if the concept stuck)
  MS2 = Concept (tests understanding of the WHY or HOW, not just the WHAT)
  MS3 = Application (new scenario — not the same Ghanaian example used in the hook or Extension Path)
  Each question must be answerable in 2–4 sentences maximum.
  This is student-facing — write it as a direct question, no teacher notes embedded.

⑦ TEACHER INSIGHT — Phase 3 MUST include a "🤖 TEACHER INSIGHT" block immediately after DATA-TRIGGER:
  Output a JSON object predicting which student groups need 1-on-1 help tomorrow.
  Format EXACTLY:
  {{
    "at_risk_profile": "[2 sentences: describe the student(s) who likely struggled — based on Q1/Q2 Pulse Check patterns]",
    "tomorrow_action": "[Exact 1-on-1 intervention the teacher should run in the first 5 mins of the next lesson]",
    "monitor_signals": ["[Observable classroom signal 1]", "[Observable classroom signal 2]"],
    "peer_resource": "[How to deploy Extension Path students as peer instructors or demonstrators]"
  }}
  This block is teacher-only — never share with students.

═══════════════════════════════════════════════════════
SIX HOMEWORK RULES — ENFORCE STRICTLY
═══════════════════════════════════════════════════════

RULE 1 — DIFFICULTY ORDER IS FIXED:
  Support homework = EASIER, more structured, shorter, requires no prior mastery.
  Extension homework = HARDER, more open-ended, demands higher-order thinking.
  Never reverse this. A 3-day diary with reflective writing is harder than a one-page poster.

RULE 2 — SUPPORT HOMEWORK MUST BE DEVICE-FREE:
  The Support task must be fully completable with pen, paper, and memory only.
  Do NOT require a phone, computer, camera, printer, or internet access.
  Ghana Basic 7 students may not have devices or reliable electricity at home.
  "Bring a photo" or "create a digital poster" are BANNED for the Support task.

RULE 3 — EXTENSION HOMEWORK IS DEVICE-OPTIONAL:
  The Extension task may suggest using a device but must include a pen-and-paper fallback.
  Write it as: "If you have a phone/computer: [digital version]. If not: [paper version]."

RULE 4 — NO CONCEPT DRIFT:
  Both homework tasks must stay on the SAME concept taught in this lesson: {topic}.
  Do not pivot to a related sub-topic, a broader theme, or a different aspect of the subject.
  A lesson on ergonomics generates ergonomics homework. A lesson on MoMo generates MoMo homework.

RULE 5 — CULTURAL REFERENCES NEED A SCAFFOLD:
  If using Adinkra symbols, proverbs, Sankofa, or Ghanaian idioms, ALWAYS provide:
  - The English meaning in brackets, AND
  - A model sentence or sentence starter so students know what form is expected.
  Example: 'Use the Sankofa idea ("look back to go forward") — complete this sentence:
  "One thing I now know I should have done earlier is ____."'
  Never ask students to "write a Sankofa-inspired line" without this scaffold.

RULE 6 — HOMEWORK MAPS TO PULSE CHECK GAPS:
  The Support homework task must directly address the most common Pulse Check miss
  (typically Q1 or Q2 — the prerequisite or misconception question).
  The Extension homework task must build on the Extension Path class activity.
  State which Pulse Check question each task targets, in ONE short parenthetical:
  e.g., "(Targets Q1 gap: ...)" or "(Extends the class Extension Path task on ...)"

RULE 7 — TEACHER NOTES STAY OUT OF HOMEWORK:
  Homework text is STUDENT-FACING. Write it as instructions to the student ("You will...", "Draw...", "List...").
  All teacher planning notes, diagnostic observations, and action items belong ONLY in the DATA-TRIGGER block.
  Never append "Notes for the teacher:" to the Homework field.

═══════════════════════════════════════════════════════
OUTPUT FORMAT — USE THESE EXACT BOLD HEADERS
═══════════════════════════════════════════════════════

**🧠 CONTEXT PILLARS ANALYSIS**
Learner DNA: [2 sentences: mastery baseline for this class on {topic}, the ONE prior-concept gap most likely to surface, and the specific misconception that shapes Q2.]
GES Standards: [Exact strand name → sub-strand name → indicator code e.g. B7.2.2.1.1. If adapted, state why in one clause.]
Core Competencies Active:
  💻 Digital Literacy — [Phase and specific activity where it appears]
  🧠 Critical Thinking — [Phase and specific activity where it appears]
  🌍 Cultural Identity — [Phase and specific activity — always the hook and its echoes]
  [Add others that are genuinely triggered, each with phase/activity. Omit if not present.]

**Subject:** {subject}
**Class:** {grade_level}
**Topic:** {topic}
**Duration:** 60 minutes
**Strand:** [Exact GES strand name]
**Sub Strand:** [Exact GES sub-strand name]
**Indicator Code:** [e.g., B7.2.2.1.1]
**Content Standard:** [1–2 sentence GES-aligned content standard]
**Indicator:** [observable, measurable indicator statement]
**Performance Indicator:** [what mastery looks like in student action]
**Core Competencies:**
  💻 Digital Literacy: [specific moment in this lesson where it is explicitly developed]
  🧠 Critical Thinking: [specific moment — Pulse Check, Extension Path, or debrief]
  🌍 Cultural Identity: [specific moment — hook, paths, or homework cultural reference]
  [Add 💡 Creativity | 🗣️ Communication | 🏆 Personal Development | 💰 Financial Literacy if triggered]
**Key words:** [5 essential vocabulary terms with one-line definitions]
**Reference:** [GES CBC code + document name + page, e.g., "GES CBC B7 ICT Curriculum (2019), B7.2.2.1.1, p. 24"]

**PHASE 1: STARTER [15 mins]**
🌍 LOCALIZED HOOK:
[2–3 sentences. Name the specific Ghanaian place, object, or practice. Make the link to {topic} explicit.]

🔍 PULSE CHECK (AI-Integrated Diagnostic):
Q1: [TRUE/FALSE STATEMENT — prerequisite knowledge. Phrased as a declarative claim students answer True or False. E.g. "{topic} is [factual claim about prerequisite] — True or False?"]
Q2: [TRUE/FALSE STATEMENT — common misconception. Phrase the misconception as a statement; correct answer should be False. E.g. "[Misconception about {topic}]. True or false? If false, give a quick example that contradicts this."]
Q3: [OPEN QUESTION — Application. Must reference the SPECIFIC Ghanaian context from the hook above. Not a True/False — students give a short verbal or written response.]
Teacher note: Log students who hesitate or miss Q1/Q2/Q3 — they are your Data-Trigger targets.

CRITICAL RULE FOR Q1 AND Q2 — DECLARATIVE STATEMENTS ONLY:
Q1 and Q2 MUST be declarative statements, NOT questions.
FORBIDDEN STARTERS: "What", "How", "Why", "Who", "When", "Where", "Name", "List", "Describe", "Explain", "Define", "Give", "Identify"
A student must be able to answer Q1 and Q2 with ONLY "True" or "False".
CORRECT format: "[Claim about {topic}] — True or False?"
EXAMPLE for a Robotics lesson: "A sensor in a robot collects information from the environment — True or False?"
WRONG: "What is one basic part of a robot?" ← this is a question, FORBIDDEN for Q1/Q2.

**PHASE 2: NEW LEARNING [30 mins]**
Class Introduction (all students, 5 mins):
[2–3 sentences bridging the hook to the core concept. Set context for both paths.]

🟢 SUPPORT PATH (students who struggled in the Pulse Check):
Step 1: [Entry-level activity — visual, matching, or hands-on. No prior mastery needed.]
Step 2: [Guided practice with a sentence frame or partially completed example.]
Step 3: [Paired practice. Teacher nearby to check understanding.]
Success marker: [Observable behaviour that shows this student is ready. One sentence.]

🔵 EXTENSION PATH (students who aced the Pulse Check):
Task 1: [Real-world application of {topic} — must use the SAME Ghanaian context as the hook, not a different one. Be specific: name the organisation, location, or role.]
Task 2: [Cross-curricular or analytical challenge — state the second subject explicitly.]
Task 3: [Higher-order creation, evaluation, or design task.]
Success marker: [What a strong finished product looks like. One sentence.]

🔲 CHECKPOINT QUESTIONS (Active Assessment — Mastery Heatmap Triggers):
CQ1: [Foundational — short closed question. Can everyone recall the core idea of {topic}?]
Heatmap: 🔴 [Teacher action for students who cannot answer] | 🟡 [Action for partial answers] | 🟢 [Action for confident answers]
CQ2: [Process — one-step application. Can students use {topic} in a structured context?]
Heatmap: 🔴 [Reteach action] | 🟡 [Prompt/support action] | 🟢 [Extend action]
CQ3: [Transfer — reasoning or real-world connection. Can students generalise {topic}?]
Heatmap: 🔴 [Reteach action] | 🟡 [Support action] | 🟢 [Activate as peer resource]

CRITICAL FORMAT RULE: Labels MUST be exactly "CQ1:", "CQ2:", "CQ3:" — NO extra words or spaces before the question text.
FORBIDDEN: "CQ1 Foundational:", "CQ1: Foundational:", "CQ1 Process:", "CQ1: Process:", "CQ1 Transfer:", "CQ1: Transfer:"
CORRECT: "CQ1: What is ..."
Do NOT generate a \"Student Nugget\", \"Junior Innovator\", or any other sub-header inside the Extension Path or after it. The Extension Path contains Task 1 / Task 2 / Task 3 and Success marker ONLY.

**PHASE 3: REFLECTION [15 mins]**
Whole-class debrief:
[1–2 sentences. Whole-class question or share-out that consolidates {topic} for everyone.]

🏁 MASTERY SPRINT (Exit Ticket — Students work SOLO. No hints. No discussion.):
MS1: [Closed recall question. Write ONLY the question — do NOT start with "Recall:" or any type label.]
MS2: [Concept question testing the WHY or HOW. Write ONLY the question — do NOT start with "Concept:".]
MS3: [Application question in a new context. Write ONLY the question — do NOT start with "Application:".]

📊 DATA-TRIGGER (Teacher Planning Tool — DO NOT share with students):
- Students who missed Q1: [Exact reteach action for next lesson. Name the method.]
- Students who missed Q2: [Exact misconception-correction strategy for next lesson.]
- Students who missed Q3: [Exact application re-practice for next lesson.]
- Extension Path students: [How to activate them as peer resources in the next lesson.]

🤖 TEACHER INSIGHT (JSON Summary — Teacher Mobile App Only):
{{
  "at_risk_profile": "[2 sentences describing the student group predicted to need 1-on-1 — based on Q1/Q2 patterns]",
  "tomorrow_action": "[Exact first-5-minute intervention for the next lesson]",
  "monitor_signals": ["[Observable signal 1]", "[Observable signal 2]"],
  "peer_resource": "[How to deploy Extension Path students tomorrow]"
}}

**Resources:** [All materials needed: textbook pages, whiteboard, manipulatives, local objects]

**Homework:**
🟢 Support task (targets Q[1 or 2] gap — [name the gap]):
[Student-facing instructions only. Pen-and-paper. No device required. Structured, short, achievable in 20 mins.]

🔵 Extension task (builds on class Extension Path — [name what it extends]):
[Student-facing instructions only. Device-optional — include paper fallback. Higher-order, 25–30 mins.
If any cultural reference (proverb, symbol) is used, include its English meaning AND a model sentence starter.]
"""

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Generate the full Aura-T lesson plan for '{topic}' "
                        f"({grade_level}, {subject}). "
                        + (f"Sub-strand: '{sub_strand}'. " if sub_strand else '')
                        + (f"Target Indicator: {indicator}. " if indicator else '')
                        + "STEP 1 — Context Pillars: Analyse Learner DNA (mastery baseline, prior-concept gap, top misconception), "
                        "map the exact GES CBC indicator code, and tag the three mandatory core competencies with phase/activity. "
                        "Output this as the 🧠 CONTEXT PILLARS ANALYSIS block at the top. "
                        "STEP 2 — Plan: Draft the full plan shaped by that analysis. "
                        "Tailor all phases, activities, and assessments to directly address the sub-strand and indicator. "
                        "Enforce all seven Homework Rules strictly: "
                        "Support task pen-and-paper only and easier; Extension device-optional with paper fallback; "
                        "no concept drift; cultural references include English meaning + model sentence starter; "
                        "homework maps to specific Pulse Check gaps; no teacher notes in Homework field."
                    )}
                ],
                "temperature": 0.75,
                "max_tokens": 3200,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                "lesson_plan": content
            }
        except Exception as e:
            logger.error("Lesson plan generation failed: %s", e)
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                "lesson_plan": None,
                "error": str(e)
            }

    @staticmethod
    def generate_slides_outline(topic: str, subject: str, grade_level: str) -> Dict:
        """
        Generate a full, presentation-ready slide deck with rich content:
        definitions, examples, scenarios, key terms, and assessment.
        """
        system_prompt = f"""You are Aura-T, an expert Ghanaian classroom teaching assistant who creates rich, presentation-ready slide decks.

Generate a complete teaching slide deck for {grade_level} {subject} on the topic: "{topic}".

Return a JSON object with EXACTLY this structure:
{{
  "slides": [
    {{"title": "...", "bullets": ["...", "..."], "notes": "...", "emoji": "..."}}
  ],
  "activities": ["...", "..."]
}}

Each slide MUST include an "emoji" field — a single emoji character that visually represents the slide content.
Examples: 🎯 for objectives, 📖 for definitions, 🔬 for experiments, 🧮 for maths, ❓ for questions, ✅ for summaries.

═══════════════════════════════════════════════════════
SLIDE STRUCTURE — 8 SLIDES (MANDATORY)
═══════════════════════════════════════════════════════

SLIDE 1 — TITLE & HOOK
- Title: an engaging title for the lesson (not just the topic name)
- Bullets: the topic, the learning objective, and a thought-provoking question that connects to students' lives
- Notes: a brief local/Ghanaian hook the teacher can use to introduce the lesson

SLIDE 2 — KEY VOCABULARY / KEY TERMS
- Title: "Key Terms & Definitions"
- Bullets: 3-4 essential terms with clear, student-friendly definitions
  Format each bullet as: "Term — Definition in simple words"
- Notes: pronunciation tips or memory tricks the teacher can share

SLIDE 3 — CORE CONCEPT EXPLAINED
- Title: a clear heading that names the concept
- Bullets: break the concept into 3-4 digestible points, each explaining one aspect
  Write FULL SENTENCES, not fragments. Each bullet should teach something concrete.
- Notes: analogies or simplified explanations the teacher can use verbally

SLIDE 4 — WORKED EXAMPLE
- Title: "Worked Example" or a specific example title
- Bullets: walk through a step-by-step example (3-4 steps)
  Each bullet is one step: "Step 1: ...", "Step 2: ...", etc.
  Use a realistic, relatable scenario (preferably Ghanaian context)
- Notes: common mistakes to watch for and how to address them

SLIDE 5 — REAL-WORLD SCENARIO / APPLICATION
- Title: a scenario title (e.g., "Case Study: ..." or "In Practice: ...")
- Bullets: present a real-world scenario and show how the concept applies
  Include: the situation, how the concept is used, and the outcome
- Notes: discussion prompts the teacher can pose to the class

SLIDE 6 — VISUAL COMPARISON / DID YOU KNOW?
- Title: comparison or interesting facts heading
- Bullets: use comparisons, contrasts, or surprising facts to deepen understanding
  Format: "X vs Y", "Myth vs Fact", or "Did you know: ..."
- Notes: how the teacher can use this slide to correct misconceptions

SLIDE 7 — PRACTICE QUESTIONS / CHECK YOUR UNDERSTANDING
- Title: "Check Your Understanding"
- Bullets: 3-4 practice questions or tasks of increasing difficulty
  Q1: recall/definition level
  Q2: application level
  Q3: analysis/reasoning level
  Q4 (optional): create/evaluate level
- Notes: expected answers and marking guidance for the teacher

SLIDE 8 — SUMMARY & TAKEAWAYS
- Title: "Key Takeaways"
- Bullets: 3-4 concise summary statements that capture the main ideas
  Start each with an action verb: "Remember that...", "Always...", "The key difference is..."
- Notes: preview of next lesson and homework suggestion

═══════════════════════════════════════════════════════
CONTENT QUALITY RULES
═══════════════════════════════════════════════════════
- Write FULL, MEANINGFUL content — not outlines or placeholders
- Bullets must be complete thoughts that a student can read and learn from
- Definitions must be accurate and age-appropriate for {grade_level}
- Examples must use concrete numbers, names, or scenarios — never "e.g., ..."
- Every slide must have 3-4 bullets (not fewer)
- Speaker notes are for the TEACHER: include delivery tips, expected answers, time cues
- Use Ghanaian context where natural (local names, currency, places, practices)
- Activities must be specific and actionable (not generic "discuss" or "think about")
"""

        user_prompt = (
            f"Create a complete, content-rich presentation on '{topic}' "
            f"for {grade_level} {subject}. "
            "Fill every slide with real definitions, worked examples, scenarios, "
            "and practice questions — not just outlines. "
            "The slides should be ready to present in a classroom as-is."
        )

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.65,
                "max_tokens": 2800,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content)

            slides = AuraGenEngine._normalize_slides(data.get("slides"), topic)
            activities = AuraGenEngine._normalize_activities(data.get("activities"))

            if not slides:
                slides = AuraGenEngine._fallback_slides_outline(topic, subject, grade_level).get("slides", [])
            if not activities:
                activities = AuraGenEngine._fallback_slides_outline(topic, subject, grade_level).get("activities", [])

            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                "slides": slides,
                "activities": activities,
            }
        except Exception as e:
            logger.error("Slides generation failed: %s", e)
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                **AuraGenEngine._fallback_slides_outline(topic, subject, grade_level)
            }

    @staticmethod
    def generate_slides_from_document(document_text: str, filename: str = '') -> Dict:
        """
        Generate a slide deck from extracted document text (PDF/Word).
        Truncates to 12,000 chars to stay within token limits.
        """
        text_excerpt = document_text.strip()[:12000]
        if not text_excerpt:
            return AuraGenEngine._fallback_slides_outline(filename or 'Document', 'General', 'General')

        title_hint = (
            filename.rsplit('.', 1)[0]
            .replace('_', ' ').replace('-', ' ')
        ) if filename else 'Document'

        system_prompt = (
            "You are Aura-T, an expert teaching assistant.\n"
            "Given the content of an educational document, create a PRESENTATION-READY teaching slide deck.\n"
            "Return a JSON object with EXACTLY this structure:\n"
            "{\n"
            '  "slides": [\n'
            '    {"title": "...", "bullets": ["...", "..."], "notes": "...", "emoji": "..."}\n'
            "  ],\n"
            '  "activities": ["Activity 1", "Activity 2"]\n'
            "}\n\n"
            "Each slide MUST include an \"emoji\" field — a single emoji representing the slide content.\n"
            "Examples: 🎯 for goals, 📖 for definitions, 🔬 for experiments, ❓ for questions, ✅ for summaries.\n\n"
            "SLIDE STRUCTURE (8 slides):\n"
            "- Slide 1: Title & overview — introduce the topic, state what students will learn\n"
            "- Slide 2: Key Terms & Definitions — 3-4 essential terms with clear definitions\n"
            "- Slides 3-5: Core content slides — each explains ONE key concept from the document\n"
            "  Write FULL SENTENCES in bullets, not fragments. Include definitions, examples, specifics.\n"
            "- Slide 6: Worked Example or Case Study — step-by-step application of a concept\n"
            "- Slide 7: Check Your Understanding — 3-4 practice questions (recall → apply → analyse)\n"
            "- Slide 8: Key Takeaways — summary statements students can use for revision\n\n"
            "CONTENT RULES:\n"
            "- Rewrite content in clear, student-friendly language — do NOT copy text verbatim\n"
            "- Every bullet must be a COMPLETE THOUGHT that teaches something specific\n"
            "- Include concrete examples, numbers, and real scenarios — not vague statements\n"
            "- Every slide needs: non-empty title, 3-4 bullet points, speaker notes\n"
            "- Speaker notes should include delivery tips and expected student responses\n"
            "- Focus on the most important concepts and discard irrelevant details\n"
            "- Activities must be specific and classroom-actionable\n"
        )

        user_prompt = (
            f"Document title hint: {title_hint}\n\n"
            f"Document content:\n{text_excerpt}\n\n"
            "Create a presentation-ready slide deck with full definitions, "
            "examples, and practice questions from the above content."
        )

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.6,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content)

            slides = AuraGenEngine._normalize_slides(data.get("slides"), title_hint)
            activities = AuraGenEngine._normalize_activities(data.get("activities"))

            if not slides:
                slides = AuraGenEngine._fallback_slides_outline(title_hint, 'General', 'General').get("slides", [])
            if not activities:
                activities = []

            return {
                "meta": {
                    "topic": title_hint,
                    "source": "document",
                    "generated_at": timezone.now().isoformat(),
                },
                "slides": slides,
                "activities": activities,
            }
        except Exception as e:
            logger.error("Document slides generation failed: %s", e)
            return {
                "meta": {
                    "topic": title_hint,
                    "source": "document",
                    "generated_at": timezone.now().isoformat(),
                },
                **AuraGenEngine._fallback_slides_outline(title_hint, 'General', 'General'),
            }

    @staticmethod
    def generate_slides_from_lesson_plan(plan: dict) -> Dict:
        """
        Generate a learning-guide slide deck from a LessonPlan's fields.
        Prioritizes topic + indicator + objectives while still using plan activities.
        Produces presentation-ready content with definitions, examples, and scenarios.
        """
        topic = str(plan.get('topic') or 'Lesson').strip()
        subject = str(plan.get('subject') or 'General').strip()
        class_name = str(plan.get('class_name') or 'General').strip()
        objectives = str(plan.get('objectives') or '').strip()
        indicator = str(plan.get('indicator') or '').strip()
        introduction = str(plan.get('introduction') or '').strip()
        presentation_text = str(plan.get('presentation') or '').strip()
        evaluation = str(plan.get('evaluation') or '').strip()
        homework = str(plan.get('homework') or '').strip()
        demographic_context = str(plan.get('demographic_context') or '').strip()

        system_prompt = (
            "You are Aura-T, an expert Ghanaian classroom teaching assistant.\n"
            "Create a PRESENTATION-READY learning-guide slide deck from a lesson plan.\n"
            "The deck must be anchored in TOPIC + INDICATOR + OBJECTIVES.\n\n"
            "Return JSON with EXACT structure:\n"
            "{\n"
            "  \"slides\": [\n"
            "    {\"title\": \"...\", \"bullets\": [\"...\"], \"notes\": \"...\", \"emoji\": \"...\"}\n"
            "  ],\n"
            "  \"activities\": [\"...\"]\n"
            "}\n\n"
            "Each slide MUST include an \"emoji\" field — a single emoji representing the slide content.\n"
            "Examples: 🎯 for goals, 📖 for definitions, 🔬 for experiments, ❓ for questions, ✅ for summaries.\n\n"
            "═══════════════════════════════════════════════════════\n"
            "SLIDE SEQUENCE — 8 TO 9 SLIDES\n"
            "═══════════════════════════════════════════════════════\n\n"
            "SLIDE 1 — HOOK & LEARNING GOAL\n"
            "- Engaging title tied to school/community context when available\n"
            "- Bullets: the topic, the learning indicator in student-friendly words, what success looks like\n"
            "- Notes: 'Teacher Cue: [local hook or story]\\nStudent Notes: [topic + objective summary]'\n\n"
            "SLIDE 2 — KEY VOCABULARY\n"
            "- Title: 'Key Terms & Definitions'\n"
            "- Bullets: 3-4 essential terms with clear definitions\n"
            "  Format: 'Term — definition in simple words'\n"
            "- Notes: 'Teacher Cue: [pronunciation/memory tips]\\nStudent Notes: [terms to copy into notebooks]'\n\n"
            "SLIDE 3 — CORE CONCEPT\n"
            "- Title naming the concept clearly\n"
            "- Bullets: 3-4 FULL SENTENCES explaining the concept (not fragments)\n"
            "- Notes: 'Teacher Cue: [analogies to use]\\nStudent Notes: [concept summary in simple words]'\n\n"
            "SLIDE 4 — WORKED EXAMPLE\n"
            "- Title: 'Worked Example' or specific example title\n"
            "- Bullets: step-by-step walkthrough (Step 1, Step 2, Step 3...)\n"
            "  Use a realistic Ghanaian scenario with concrete details\n"
            "- Notes: 'Teacher Cue: [common mistakes to watch for]\\nStudent Notes: [copy this example into your notebook]'\n\n"
            "SLIDE 5 — REAL-WORLD APPLICATION\n"
            "- Present a scenario showing how the concept applies in real life\n"
            "- Include: the situation, how the concept is used, and the outcome\n"
            "- Notes: 'Teacher Cue: [discussion prompts]\\nStudent Notes: [application summary]'\n\n"
            "SLIDE 6 — DEEPER UNDERSTANDING\n"
            "- Comparisons, contrasts, myths vs facts, or 'Did You Know' items\n"
            "- Bullets that challenge surface-level understanding\n"
            "- Notes: 'Teacher Cue: [misconception correction]\\nStudent Notes: [key distinctions to remember]'\n\n"
            "SLIDE 7 — PRACTICE QUESTIONS\n"
            "- Title: 'Check Your Understanding'\n"
            "- Bullets: 3-4 questions of increasing difficulty (recall → apply → analyse)\n"
            "- Notes: 'Teacher Cue: [expected answers and marking tips]\\nStudent Notes: [attempt all questions in your exercise book]'\n\n"
            "SLIDE 8 — SAMPLE STUDY NOTES\n"
            "- Title: 'Sample Study Notes'\n"
            "- Bullets: compact revision notes a student can copy directly\n"
            "  Include: definition, key formula/rule, one example, one common mistake\n"
            "- Notes: 'Teacher Cue: [model note-taking format]\\nStudent Notes: [rewrite these notes in your own words]'\n\n"
            "SLIDE 9 — SUMMARY & TAKEAWAYS\n"
            "- Title: 'Key Takeaways'\n"
            "- Bullets: 3-4 concise summary statements + self-check question\n"
            "- Notes: 'Teacher Cue: [preview next lesson, assign homework]\\nStudent Notes: [core ideas to review tonight]'\n\n"
            "═══════════════════════════════════════════════════════\n"
            "CONTENT QUALITY RULES\n"
            "═══════════════════════════════════════════════════════\n"
            "- Write FULL, MEANINGFUL content — never placeholders or outlines\n"
            "- Definitions must be accurate and age-appropriate\n"
            "- Examples must use concrete numbers, names, or scenarios\n"
            "- Every slide needs 3-4 bullets minimum\n"
            "- Notes MUST have 'Teacher Cue:' then 'Student Notes:' labels\n"
            "- Use the lesson-plan sections as source material to enrich slides\n"
            "- Ghanaian context where natural (local names, GH₵, places)\n"
            "- Activities must be specific and actionable"
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Subject: {subject}\n"
            f"Class: {class_name}\n"
            f"Week: {plan.get('week', '')}\n"
            f"Learning Indicator: {indicator or 'Not provided'}\n"
            f"Learning Objectives: {objectives or 'Not provided'}\n"
            f"School / Demographic Context: {demographic_context or 'Not provided'}\n\n"
            "Lesson-plan content to draw from:\n"
            f"Introduction/Hook: {introduction or 'N/A'}\n"
            f"Main Presentation: {presentation_text or 'N/A'}\n"
            f"Evaluation: {evaluation or 'N/A'}\n"
            f"Homework: {homework or 'N/A'}\n\n"
            "Build a content-rich, presentation-ready learning-guide deck. "
            "Fill every slide with real definitions, worked examples, scenarios, "
            "and practice questions — not just outlines."
        )

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.55,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content)

            slides = AuraGenEngine._normalize_slides(data.get("slides"), topic)
            activities = AuraGenEngine._normalize_activities(data.get("activities"))

            normalized_with_split_notes = []
            for slide in slides:
                notes_text = str(slide.get("notes") or "").strip()
                if "Teacher Cue:" in notes_text and "Student Notes:" in notes_text:
                    normalized_with_split_notes.append(slide)
                    continue

                bullets = slide.get("bullets") or []
                student_line = bullets[0] if bullets else f"Key idea: {topic}"
                slide["notes"] = (
                    "Teacher Cue: Emphasize the link between the topic, indicator, and objective with one local example.\n"
                    f"Student Notes: {student_line}"
                )
                normalized_with_split_notes.append(slide)
            slides = normalized_with_split_notes

            # Guarantee a student-shareable notes anchor even if model misses it.
            has_notes_slide = any('sample study notes' in s.get('title', '').lower() for s in slides)
            if slides and not has_notes_slide:
                slides.append({
                    "title": "Sample Study Notes",
                    "bullets": [
                        "Define the topic in one clear sentence",
                        "Write the indicator in learner-friendly words",
                        "Add one worked example from class",
                        "List one common mistake to avoid",
                    ],
                    "notes": (
                        "Teacher Cue: Model a compact note format and ask students to rewrite it in their own words.\n"
                        "Student Notes: Topic meaning, indicator in simple words, one example, one mistake to avoid."
                    ),
                })

            if slides:
                slides = slides[:10]
            if not slides:
                slides = AuraGenEngine._fallback_slides_outline(topic, subject, class_name).get("slides", [])
            if not activities:
                activities = [
                    "Pair-share: explain the indicator in your own words.",
                    "Mini-check: solve one question and justify each step.",
                    "Exit note: write two key takeaways and one confusion.",
                ]

            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": class_name,
                    "indicator": indicator,
                    "generated_at": timezone.now().isoformat(),
                },
                "slides": slides,
                "activities": activities,
            }
        except Exception as e:
            logger.error("Lesson-plan slide generation failed: %s", e)
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": class_name,
                    "indicator": indicator,
                    "generated_at": timezone.now().isoformat(),
                },
                **AuraGenEngine._fallback_slides_outline(topic, subject, class_name),
            }

    @staticmethod
    def suggest_slide_layouts(slides_data: list) -> Dict:
        """
        AI assigns the most appropriate layout to each slide based on its title/content.
        slides_data = [{'slide_id': N, 'order': N, 'title': '...', 'content': '...'}, ...]
        Returns: {'updates': [{'slide_id': N, 'layout': '...'}, ...]}
        """
        from django.conf import settings
        if not slides_data:
            return {'updates': []}

        system_prompt = (
            'You are an expert instructional designer.\n'
            'Given a list of presentation slides, assign the best layout for each.\n'
            'Available layouts:\n'
            '  title    \u2014 Opening or section-break slide (first slide of deck)\n'
            '  bullets  \u2014 Standard bullet points (default for most slides)\n'
            '  two_col  \u2014 Two-column comparison or contrast\n'
            '  big_stat \u2014 Highlight a single number or key statistic\n'
            '  quote    \u2014 Feature a notable quote or memorable statement\n'
            '  summary  \u2014 Recap / conclusion (last slide)\n'
            '  image    \u2014 Visual-heavy slide centred on an image\n'
            '\n'
            'Rules: first slide \u2192 title; last slide \u2192 summary; single-stat slides \u2192 big_stat;\n'
            'quote slides \u2192 quote; comparison slides \u2192 two_col; rest \u2192 bullets.\n'
            'Return JSON: {"updates": [{"slide_id": N, "layout": "..."}, ...]}'
        )
        slides_text = '\n'.join(
            '[id={}] #{}: {} | {}'.format(
                s['slide_id'], s.get('order', i) + 1,
                s['title'], (s.get('content') or '')[:100]
            )
            for i, s in enumerate(slides_data)
        )
        try:
            payload = {
                'model': get_openai_chat_model(),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': slides_text},
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.15,
                'max_tokens': 400,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            data = AuraGenEngine._extract_json_object(
                response['choices'][0]['message']['content']
            )
            return {'updates': data.get('updates', [])}
        except Exception:
            return {'updates': []}

    @staticmethod
    def harmonize_deck(slides_data: list) -> Dict:
        """
        Reviews the full slide deck for terminology, tone, and style consistency.
        Returns: {'updates': [{'slide_id': N, 'title': '...', 'content': '...'}, ...], 'summary': '...'}
        Only slides that need changes are included in updates.
        """
        from django.conf import settings
        if not slides_data:
            return {'updates': [], 'summary': 'No slides to harmonize.'}

        system_prompt = (
            'You are Aura-T, an expert teaching assistant and content editor.\n'
            'Review the slide deck below for these inconsistencies:\n'
            '  - Mixed capitalisation in parallel headings\n'
            '  - Inconsistent verb tenses\n'
            '  - Shifting tone (formal \u2194 informal)\n'
            '  - Repetitive or redundant phrasing\n'
            '  - Terminology that differs across slides for the same concept\n'
            '\n'
            'For EACH slide that needs improvement, return an updated version.\n'
            'Only include slides that actually have issues. Keep facts unchanged.\n'
            'Bullets in content should remain one per line.\n'
            'Return JSON:\n'
            '{"summary": "Brief description of changes",\n'
            ' "updates": [{"slide_id": N, "title": "...", "content": "line1\\nline2\\n..."}, ...]}\n'
            'If already consistent: {"summary": "Deck is consistent.", "updates": []}'
        )
        slides_text = '\n---\n'.join(
            'slide_id={}\ntitle: {}\ncontent:\n{}'.format(
                s['slide_id'], s['title'], s.get('content', '')
            )
            for s in slides_data
        )
        try:
            payload = {
                'model': get_openai_chat_model(),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': slides_text},
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.25,
                'max_tokens': 1400,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            data = AuraGenEngine._extract_json_object(
                response['choices'][0]['message']['content']
            )
            return {
                'updates': data.get('updates', []),
                'summary': data.get('summary', 'Analysis complete.'),
            }
        except Exception:
            return {'updates': [], 'summary': 'Could not analyse deck.'}

    @staticmethod
    def suggest_slide_bullets(title: str, subject: str = 'General') -> Dict:
        """
        Given a slide title, return 3-5 concise bullet points.
        Returns: {'bullets': ['...', ...]}
        """
        from django.conf import settings
        system_prompt = (
            'You are an expert teacher. Given a slide title, return 3-5 concise, '
            'student-friendly bullet points as JSON.\n'
            'Format: {"bullets": ["...", ...]}\n'
            'Keep each bullet under 12 words. Be specific, educational, and age-appropriate.'
        )
        try:
            payload = {
                'model': get_openai_chat_model(),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': f'Slide title: "{title}" | Subject: {subject}'},
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.7,
                'max_tokens': 300,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            data = AuraGenEngine._extract_json_object(
                response['choices'][0]['message']['content']
            )
            return {'bullets': data.get('bullets', [])}
        except Exception:
            return {'bullets': []}

    @staticmethod
    def refine_slide(slide_data: dict, instruction: str = '', subject: str = 'General') -> Dict:
        """
        Improve a single slide's title and content while retaining the same topic.
        Returns: {'title': '...', 'content': '...'}
        """
        from django.conf import settings
        current_title   = slide_data.get('title', '')
        current_content = slide_data.get('content', '')
        layout          = slide_data.get('layout', 'bullets')
        instruct_str    = f'Specific instruction: {instruction}\n' if instruction else ''
        system_prompt = (
            'You are an expert teacher improving a single classroom presentation slide. '
            'Return a better version that is clearer, more engaging, and age-appropriate '
            '(primary/secondary school). For bullet-style slides keep each bullet under '
            '12 words and use no more than 6 bullets. Preserve the same topic. '
            'Return ONLY JSON: {"title": "...", "content": "..."}'
        )
        user_msg = (
            f'Subject: {subject}\n'
            f'Layout: {layout}\n'
            f'{instruct_str}'
            f'Current title: {current_title}\n'
            f'Current content:\n{current_content}'
        )
        try:
            payload = {
                'model': get_openai_chat_model(),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_msg},
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.75,
                'max_tokens': 500,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            data = AuraGenEngine._extract_json_object(
                response['choices'][0]['message']['content']
            )
            return {
                'title':   data.get('title',   current_title)   or current_title,
                'content': data.get('content', current_content) or current_content,
            }
        except Exception:
            return {'title': current_title, 'content': current_content}

    @staticmethod
    def generate_study_guide(slides_data: list) -> Dict:
        """
        Given a list of slide dicts (title, bullets/content, layout, speaker_notes),
        generate a structured AI study guide: key concepts, revision questions, activities.
        """
        lines = []
        for i, s in enumerate(slides_data, 1):
            title = s.get('title', '').strip()
            raw = s.get('content') or ''
            bullets = [b.strip() for b in raw.split('\n') if b.strip()]
            if s.get('bullets') and isinstance(s['bullets'], list):
                bullets = s['bullets']
            if title:
                lines.append(f"Slide {i} ({s.get('layout', 'bullets')}): {title}")
            for b in bullets[:6]:
                lines.append(f"  • {b}")
            notes = (s.get('speaker_notes') or '').strip()
            if notes:
                lines.append(f"  [notes: {notes[:120]}]")
        deck_text = '\n'.join(lines)[:9000]

        system_prompt = (
            "You are Aura-T, an expert teaching assistant.\n"
            "Given a teaching presentation outline, create a structured student revision guide.\n"
            "Return a JSON object with EXACTLY this structure:\n"
            "{\n"
            '  "summary": "2-3 sentence overview of the whole topic",\n'
            '  "key_concepts": [{"term": "...", "description": "one-sentence explanation"}],\n'
            '  "revision_questions": [\n'
            '    {"type": "short", "question": "...", "answer": "..."},\n'
            '    {"type": "mcq",   "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A"},\n'
            '    {"type": "true_false", "question": "...", "answer": "True"}\n'
            "  ],\n"
            '  "activities": ["Activity description 1", "Activity description 2"]\n'
            "}\n"
            "Rules:\n"
            "- 5-8 key_concepts drawn directly from slide content\n"
            "- 8-10 revision_questions: at least 3 short-answer, 3 MCQ (A/B/C/D), 1-2 true/false\n"
            "- Questions should test understanding and application, not just rote recall\n"
            "- 2-3 hands-on classroom or homework activities\n"
            "- Use student-friendly language throughout\n"
        )

        user_prompt = (
            f"Presentation slides:\n{deck_text}\n\n"
            "Generate a comprehensive student study guide from the above deck."
        )

        try:
            payload = {
                "model": get_active_ai_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.55,
            }
            response = _post_chat_completion(payload, _get_openai_api_key())
            content_raw = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content_raw)
            return {
                'ok':                True,
                'summary':           data.get('summary', ''),
                'key_concepts':      data.get('key_concepts', []),
                'revision_questions': data.get('revision_questions', []),
                'activities':        data.get('activities', []),
            }
        except Exception as exc:
            logger.error("Study guide generation failed: %s", exc)
            return {'ok': False, 'error': str(exc)}

    @staticmethod
    def _extract_json_object(raw_content: str) -> Dict:
        content = (raw_content or '').strip()
        if not content:
            return {}

        if content.startswith('```'):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end >= start:
            content = content[start:end + 1]

        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _normalize_slides(slides: Optional[List], topic: str) -> List[Dict]:
        normalized = []
        if not isinstance(slides, list):
            return normalized

        for idx, slide in enumerate(slides, start=1):
            if isinstance(slide, str):
                title = slide.strip() or f"Slide {idx}: {topic}"
                bullets = [f"Key point about {topic}", "Brief explanation", "Class discussion prompt"]
                notes = f"Guide learners through {topic} using this slide."
            elif isinstance(slide, dict):
                title = str(slide.get("title") or slide.get("heading") or f"Slide {idx}: {topic}").strip()
                raw_bullets = slide.get("bullets")
                if isinstance(raw_bullets, str):
                    raw_bullets = [piece.strip() for piece in re.split(r'\n|;', raw_bullets) if piece.strip()]
                if not isinstance(raw_bullets, list):
                    raw_bullets = []
                bullets = [str(item).strip() for item in raw_bullets if str(item).strip()]
                notes = str(slide.get("notes") or slide.get("speaker_notes") or "").strip()
            else:
                continue

            if not bullets:
                bullets = [f"Core idea of {topic}", "Worked example", "Quick student check"]
            bullets = bullets[:5]
            if len(bullets) < 2:
                bullets.append("Class reflection question")

            if not notes:
                notes = f"Explain {title.lower()} and connect it to the lesson objective."

            # Extract or auto-assign emoji
            emoji = ''
            if isinstance(slide, dict):
                emoji = str(slide.get('emoji') or '').strip()
            if not emoji:
                _EMOJI_MAP = {
                    0: '🎯', 1: '📖', 2: '💡', 3: '📝', 4: '🌍',
                    5: '🔍', 6: '❓', 7: '📋', 8: '✅', 9: '🎓',
                }
                emoji = _EMOJI_MAP.get(idx - 1, '📌')

            normalized.append({
                "title": title,
                "bullets": bullets,
                "notes": notes,
                "emoji": emoji,
            })

        return normalized[:10]

    @staticmethod
    def _normalize_activities(activities: Optional[List]) -> List[str]:
        if isinstance(activities, str):
            activities = [piece.strip() for piece in re.split(r'\n|;', activities) if piece.strip()]
        if not isinstance(activities, list):
            return []

        cleaned = [str(item).strip() for item in activities if str(item).strip()]
        return cleaned[:6]

    @staticmethod
    def _fallback_slides_outline(topic: str, subject: str, grade_level: str) -> Dict:
        slides = [
            {
                "title": f"Today's Lesson: {topic}",
                "bullets": [
                    f"Topic: {topic} in {subject}",
                    f"By the end of this lesson you will understand the key concepts of {topic}",
                    "Let's start with what you already know!",
                ],
                "notes": f"Set context for {grade_level} learners. Ask: 'Who can tell me one thing about {topic}?'",
                "emoji": "\ud83c\udfaf",
            },
            {
                "title": "Key Terms & Definitions",
                "bullets": [
                    f"Term 1 — a key concept related to {topic} (to be defined in class)",
                    f"Term 2 — another important term in {subject} (to be defined in class)",
                    f"Term 3 — a supporting concept for understanding {topic}",
                ],
                "notes": "Write these terms on the board. Have students copy them into their notebooks.",
                "emoji": "\ud83d\udcd6",
            },
            {
                "title": f"Understanding {topic}",
                "bullets": [
                    f"{topic} is a core concept in {subject} that students need to master",
                    "Break the concept into smaller parts for easier understanding",
                    "Connect the idea to something students already know",
                ],
                "notes": "Use an analogy from everyday life to explain the concept. Model thinking aloud.",
                "emoji": "\ud83d\udca1",
            },
            {
                "title": "Worked Example",
                "bullets": [
                    f"Step 1: Identify what we need to know about {topic}",
                    "Step 2: Apply the concept or rule we just learned",
                    "Step 3: Check our answer and explain our reasoning",
                ],
                "notes": "Walk through each step slowly. Ask students to predict the next step before showing it.",
                "emoji": "\ud83d\udcdd",
            },
            {
                "title": "Real-World Application",
                "bullets": [
                    f"How {topic} is used in everyday life",
                    "A practical scenario students can relate to",
                    "Why this matters beyond the classroom",
                ],
                "notes": "Use a local Ghanaian context. Ask: 'Where have you seen this in your community?'",
                "emoji": "\ud83c\udf0d",
            },
            {
                "title": "Check Your Understanding",
                "bullets": [
                    f"Q1: What is the definition of [key term from {topic}]?",
                    f"Q2: Apply what you learned to solve this problem about {topic}",
                    "Q3: Explain in your own words why this concept matters",
                ],
                "notes": "Give students 5 minutes to attempt. Walk around and check work.",
                "emoji": "\u2753",
            },
            {
                "title": "Sample Study Notes",
                "bullets": [
                    f"Define {topic} in one clear sentence",
                    "Write the key rule or formula",
                    "Include one worked example from class",
                    "Note one common mistake to avoid",
                ],
                "notes": "Model the note-taking format on the board. Have students copy into their notebooks.",
                "emoji": "\ud83d\udccb",
            },
            {
                "title": "Key Takeaways",
                "bullets": [
                    f"Remember: {topic} is essential for understanding {subject}",
                    "Always check your work against the definition and key rules",
                    "Preview: next lesson we will build on this with more examples",
                ],
                "notes": "Use exit ticket responses to plan follow-up interventions.",
                "emoji": "\u2705",
            },
        ]

        return {
            "slides": slides,
            "activities": [
                "Think-Pair-Share: Explain one key idea to a partner.",
                "Quick check: 3-item mini quiz.",
                "Exit ticket: one thing learned, one question remaining.",
            ],
        }

    @staticmethod
    def generate_interactive_exercises(topic: str, subject: str, grade_level: str,
                                       pulse_check_gaps: str = "",
                                       ghana_context: str = "",
                                       ges_indicator: str = "") -> Dict:
        """
        Generate a tiered set of interactive exercises grounded in Ghana context,
        Pulse Check gaps, and GES CBC indicators.
        Support tier: DOK 1-2, pen-and-paper friendly, addresses identified gaps.
        Extension tier: DOK 3-4, higher-order, Ghana real-world application.
        """
        context_line = f"Ghanaian lesson context: {ghana_context}" if ghana_context else ""
        gaps_line    = f"Pulse Check gaps to target: {pulse_check_gaps}" if pulse_check_gaps else ""
        ges_line     = f"GES CBC Indicator: {ges_indicator}" if ges_indicator else ""

        system_prompt = f"""You are Aura-T, an advanced pedagogical AI for Ghanaian teachers.
Generate a TIERED set of interactive exercises for {grade_level} {subject} on \"{topic}\".

{context_line}
{gaps_line}
{ges_line}

═══════════════════════════════════════════════════════
EXERCISE RULES
═══════════════════════════════════════════════════════

TOTAL: exactly 10 exercises.
  • 5 SUPPORT exercises (DOK 1-2): recall, comprehension, structured application.
    - Pen-and-paper friendly — no device required to answer.
    - At least one exercise must directly address the Pulse Check gap (if provided).
    - At least one MCQ must use the most COMMON MISCONCEPTION about {topic} as a distractor
      (students who hold the misconception will pick it; mark clearly which option it is).
  • 5 EXTENSION exercises (DOK 3-4): analysis, evaluation, creation.
    - At least one must use the SAME Ghanaian context as the lesson hook (if provided),
      naming the specific organisation, place, or role.
    - At least one must be cross-curricular (name the second subject explicitly).
    - At least one must be open-ended (no single correct answer).

EXERCISE TYPES ALLOWED: mcq | short_answer | true_false | matching | open_ended
  • mcq: 4 options (A/B/C/D), one correct. Include a \"misconception_distractor\" field
    (the option letter that corresponds to the most common misconception).
  • short_answer: 1-3 sentence expected response.
  • true_false: statement + justification expected (not just T/F).
  • matching: list of 4-6 pairs.
  • open_ended: no single answer; include a \"success_markers\" list of what a strong
    response contains.

FOR EVERY EXERCISE include:
  - \"tier\": \"support\" or \"extension\"
  - \"dok_level\": integer 1-4
  - \"ghana_context_used\": true | false
  - \"gap_targeted\": the specific Pulse Check question (e.g. \"Q1\") or \"none\"

═══════════════════════════════════════════════════════
JSON SCHEMA
═══════════════════════════════════════════════════════
{{
  "exercises": [
    {{
      "id": 1,
      "tier": "support",
      "type": "mcq",
      "dok_level": 1,
      "prompt": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "misconception_distractor": "B",
      "explanation": "Why the correct answer is right and why the distractor is wrong",
      "ghana_context_used": false,
      "gap_targeted": "Q1"
    }},
    {{
      "id": 6,
      "tier": "extension",
      "type": "open_ended",
      "dok_level": 4,
      "prompt": "...",
      "success_markers": ["Marker 1", "Marker 2", "Marker 3"],
      "ghana_context_used": true,
      "gap_targeted": "none"
    }}
  ]
}}
"""
        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Generate exactly 10 tiered exercises for '{topic}' ({grade_level}, {subject}): "
                        "5 Support (DOK 1-2, pen-and-paper, target Pulse Check gaps) and "
                        "5 Extension (DOK 3-4, Ghana context, cross-curricular). "
                        "Every exercise must include tier, dok_level, ghana_context_used, and gap_targeted."
                    )}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
                "max_tokens": 2500,
            }
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = json.loads(content)
            exercises = data.get("exercises") or []
            if not exercises:
                exercises = AuraGenEngine._mock_exercises(topic)
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                "exercises": exercises
            }
        except Exception as e:
            logger.error("Exercise generation failed: %s", e)
            return {
                "meta": {
                    "topic": topic,
                    "subject": subject,
                    "grade": grade_level,
                    "generated_at": timezone.now().isoformat()
                },
                "exercises": AuraGenEngine._mock_exercises(topic)
            }

    @staticmethod
    def _mock_exercises(topic: str) -> List[Dict]:
        """Fallback exercises when AI output is empty."""
        return [
            {
                "type": "mcq",
                "prompt": f"Which statement best describes {topic}?",
                "options": [
                    "It is a core concept taught in class",
                    "It is unrelated to the subject",
                    "It is only used in advanced courses",
                    "It is a historical event"
                ],
                "answer": "It is a core concept taught in class",
                "dok_level": 1
            },
            {
                "type": "short",
                "prompt": f"Explain {topic} in your own words.",
                "answer": "A clear explanation of the concept with an example.",
                "dok_level": 2
            },
            {
                "type": "mcq",
                "prompt": f"Pick a real-world use of {topic}.",
                "options": [
                    "Everyday problem solving",
                    "Only theoretical research",
                    "Unrelated classroom rules",
                    "None of the above"
                ],
                "answer": "Everyday problem solving",
                "dok_level": 1
            },
            {
                "type": "short",
                "prompt": f"Compare {topic} with a related concept you learned before.",
                "answer": "A comparison that shows similarities and differences.",
                "dok_level": 3
            },
            {
                "type": "short",
                "prompt": f"Design a mini project that applies {topic} in a new situation.",
                "answer": "A project outline with steps and expected outcome.",
                "dok_level": 4
            }
        ]

    @staticmethod
    def _generate_mock_fallback(topic: str, subject: str, grade_level: str) -> Dict:
        """
        Mock implementation as fallback.
        """
        
        base_assignment = {
            "title": f"{topic}: Apply & Analyze (Offline Mode)",
            "description": f"Based on our lesson on {topic}, complete the following tasks.",
            "learning_objectives": ["Understand core concepts"],
            "estimated_time": "30-45 minutes"
        }

        # 1. Instant Content Generation (Multimodal simulation)
        content = {
            "visual_prompt": f"Create a diagram showing the relationship between {topic} and daily life.",
            "questions": [
                f"Explain the concept of {topic} in your own words.",
                f"List three key features of {topic} discussed in class.",
                f"How does {topic} apply to the real-world scenario we discussed?"
            ]
        }

        # 2. Adaptive Differentiation
        differentiation = AuraGenEngine._generate_differentiation(topic, content)

        # 3. Rubric Co-Design
        rubric = AuraGenEngine._generate_rubric(topic)

        return {
            "meta": {
                "topic": topic,
                "subject": subject,
                "grade": grade_level,
                "generated_at": timezone.now().isoformat()
            },
            "assignment": {
                **base_assignment,
                "content": content
            },
            "differentiation": differentiation,
            "rubric": rubric
        }

    @staticmethod
    def _generate_differentiation(topic: str, base_content: Dict) -> Dict:
        """
        Creates 3 tiered versions of the assignment.
        """
        return {
            "support": {
                "label": "Support (Scaffolded)",
                "description": "Includes sentence starters and vocabulary banks.",
                "modifications": [
                    "Vocabulary Bank: [Key Term 1], [Key Term 2], [Key Term 3]",
                    "Sentence Starter: 'The most important thing about " + topic + " is...'",
                    "Matching exercise instead of open-ended definition."
                ]
            },
            "standard": {
                "label": "Standard (Core)",
                "description": "The standard assignment aligned with grade-level expectations.",
                "content": base_content["questions"]
            },
            "challenge": {
                "label": "Challenge (Extension)",
                "description": "Adds critical thinking and cross-disciplinary analysis.",
                "modifications": [
                    f"Research how {topic} intersects with [Related Field].",
                    "Design an experiment to test the principles of " + topic + ".",
                    "Write a critique of the current understanding of " + topic + "."
                ]
            }
        }

    @staticmethod
    def _generate_rubric(topic: str) -> List[Dict]:
        """
        Generates a grading rubric with success criteria.
        """
        return [
            {
                "criteria": "Conceptual Understanding",
                "weight": "40%",
                "levels": {
                    "excellent": f"Demonstrates deep understanding of {topic} with no errors.",
                    "proficient": f"Demonstrates solid understanding of {topic} with minor errors.",
                    "basic": f"Shows partial understanding of {topic}.",
                    "limited": "Struggles to define key concepts."
                }
            },
            {
                "criteria": "Application & Analysis",
                "weight": "40%",
                "levels": {
                    "excellent": "Applies concepts to new scenarios effectively and creatively.",
                    "proficient": "Applies concepts to standard scenarios correctly.",
                    "basic": "Can apply concepts with guidance.",
                    "limited": "Unable to apply concepts."
                }
            },
            {
                "criteria": "Communication",
                "weight": "20%",
                "levels": {
                    "excellent": "Clear, precise, and well-organized response.",
                    "proficient": "Generally clear response.",
                    "basic": "Response is understandable but lacks clarity.",
                    "limited": "Response is confusing or illegible."
                }
            }
        ]
