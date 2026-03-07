import json
import logging
import random
import re
from typing import Dict, List, Optional
from django.utils import timezone
from django.conf import settings
from teachers.models import LessonPlan, Teacher
from academics.ai_tutor import _post_chat_completion, get_openai_chat_model

logger = logging.getLogger(__name__)

class AuraGenEngine:
    """
    Aura-T Generative Pedagogical Engine.
    Uses AI service to generate educational content.
    """

    @staticmethod
    def generate_assignment_package(lesson_plan: LessonPlan, topic_prompt: Optional[str] = None) -> Dict:
        """
        Generates a complete assignment package based on a lesson plan or topic using AI.
        """
        topic = topic_prompt if topic_prompt else lesson_plan.topic
        subject = lesson_plan.subject.name
        grade_level = lesson_plan.school_class.name
        
        # Build context from lesson plan if available
        lesson_context = ""
        if lesson_plan:
            lesson_context = f"""
            Objectives: {lesson_plan.objectives}
            Presentation: {lesson_plan.presentation}
            """

        system_prompt = f"""You are Aura-T, an expert pedagogical AI for teachers. 
        Your task is to generate a high-quality, differentiated assignment package for a {grade_level} class on the subject of {subject}.
        
        Topic: {topic}
        Context: {lesson_context}
        
        You must return a valid JSON object with the following structure:
        {{
            "assignment": {{
                "title": "Creative title for the assignment",
                "description": "Student-facing instructions",
                "content": {{
                    "visual_prompt": "Description of an image or diagram students should analyze",
                    "questions": ["Question 1", "Question 2", "Question 3"]
                }}
            }},
            "differentiation": {{
                "support": {{
                    "description": "How to support struggling learners",
                    "modifications": ["Modification 1", "Modification 2"]
                }},
                "standard": {{
                    "description": "Standard expectations",
                    "content": ["Standard Task 1", "Standard Task 2"]
                }},
                "challenge": {{
                    "description": "How to extend for advanced learners",
                    "modifications": ["Extension 1", "Extension 2"]
                }}
            }},
            "rubric": [
                {{
                    "criteria": "Criteria Name",
                    "weight": "Percentage",
                    "levels": {{
                        "excellent": "Description for top marks",
                        "proficient": "Description for passing",
                        "basic": "Description for partial credit",
                        "limited": "Description for minimum credit"
                    }}
                }}
            ]
        }}
        """

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a creative and educational assignment package for {topic}."}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            
            response = _post_chat_completion(payload, settings.OPENAI_API_KEY)
            content = response['choices'][0]['message']['content']
            data = AuraGenEngine._extract_json_object(content)

            # Add metadata
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
            # Fallback to mock if AI fails
            return AuraGenEngine._generate_mock_fallback(topic, subject, grade_level)

    @staticmethod
    def generate_lesson_plan(topic: str, subject: str, grade_level: str) -> Dict:
        """
        Generate a full structured lesson plan in the Aura-T format.
        Every plan MUST include: Localized Hook, AI Pulse Check, two Learning Paths,
        and a Data-Trigger. These are non-negotiable.
        """
        system_prompt = f"""You are Aura-T, an advanced pedagogical AI for Ghanaian teachers trained on the GES Competency-Based Curriculum.
Generate a rigorous, dynamic lesson plan for {grade_level} {subject} on "{topic}".

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
  Q1 probes prerequisite knowledge. Q2 targets the most common misconception about {topic}.
  Q3 connects {topic} to the hook context.
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

④ DATA-TRIGGER — Phase 3 MUST contain a "📊 DATA-TRIGGER" block:
  For EACH of the three Pulse Check questions, state the EXACT teacher action for students who missed it.
  Be specific: name the reteach method, re-pairing strategy, or micro-task for next lesson.
  Also state how to activate Extension Path students as resources (peer leaders, demonstrators, etc.).
  DATA-TRIGGER is a teacher planning tool — it must NOT appear in student-facing content.

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

**Subject:** {subject}
**Class:** {grade_level}
**Topic:** {topic}
**Duration:** 60 minutes
**Strand:** [GES-aligned strand]
**Sub Strand:** [GES-aligned sub-strand]
**Content Standard:** [1–2 sentence GES-aligned content standard]
**Indicator:** [observable, measurable indicator]
**Performance Indicator:** [what mastery looks like in student action]
**Core Competencies:** Critical Thinking, Communication, Cultural Identity, Creativity and Innovation
**Key words:** [5 essential vocabulary terms]
**Reference:** [GES Curriculum document or standard textbook]

**PHASE 1: STARTER [15 mins]**
🌍 LOCALIZED HOOK:
[2–3 sentences. Name the specific Ghanaian place, object, or practice. Make the link to {topic} explicit.]

🔍 PULSE CHECK (AI-Integrated Diagnostic):
Q1: [Prerequisite knowledge question]
Q2: [Common misconception about {topic}]
Q3: [Application question — must reference the SPECIFIC Ghanaian context you chose in the hook above, not a different or generic Ghanaian example]
Teacher note: Log students who hesitate or miss Q1/Q2/Q3 — they are your Data-Trigger targets.

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

**PHASE 3: REFLECTION [15 mins]**
Whole-class debrief:
[1–2 sentences. Whole-class question or share-out that consolidates {topic} for everyone.]

📊 DATA-TRIGGER (Teacher Planning Tool — DO NOT share with students):
- Students who missed Q1: [Exact reteach action for next lesson. Name the method.]
- Students who missed Q2: [Exact misconception-correction strategy for next lesson.]
- Students who missed Q3: [Exact application re-practice for next lesson.]
- Extension Path students: [How to activate them as peer resources in the next lesson.]

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
                        "Strictly enforce all six Homework Rules: "
                        "Support task is pen-and-paper only and easier than Extension; "
                        "Extension task is device-optional with a paper fallback; "
                        "no concept drift; cultural references include English meaning and a model sentence; "
                        "homework maps to specific Pulse Check gaps; "
                        "no teacher notes in the Homework field."
                    )}
                ],
                "temperature": 0.75,
                "max_tokens": 2500,
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
        Generate a slide deck outline with titles, bullets, and speaker notes.
        """
        system_prompt = f"""You are Aura-T, an expert teaching assistant.
Generate a slide deck outline for a lesson.
Return a JSON object with this structure:
{{
  "slides": [
    {{"title": "Slide title", "bullets": ["Point 1", "Point 2"], "notes": "Speaker notes"}}
  ],
  "activities": ["Short in-slide activity", "Quick check"]
}}
Rules:
- Return 6 to 8 slides.
- Every slide must include non-empty title, bullets (2-4 items), and notes.
- Keep bullets concise and student-friendly.
"""
        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create slides for '{topic}' for {grade_level} {subject}."}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
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
            bullets = bullets[:4]
            if len(bullets) < 2:
                bullets.append("Class reflection question")

            if not notes:
                notes = f"Explain {title.lower()} and connect it to the lesson objective."

            normalized.append({
                "title": title,
                "bullets": bullets,
                "notes": notes,
            })

        return normalized[:8]

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
                "title": f"Lesson Goal: {topic}",
                "bullets": [
                    f"What {topic} means in {subject}",
                    "Why this topic matters",
                    "Learning target for today",
                ],
                "notes": f"Set context for {grade_level} learners and share success criteria.",
            },
            {
                "title": "Prior Knowledge Check",
                "bullets": [
                    "Recall related ideas from previous lessons",
                    "Identify common misconceptions",
                    "Quick warm-up prompt",
                ],
                "notes": "Use 2-3 rapid questions to assess readiness.",
            },
            {
                "title": f"Core Concept: {topic}",
                "bullets": [
                    "Define the core concept",
                    "Show one clear example",
                    "Highlight key terms",
                ],
                "notes": "Model thinking aloud and emphasize vocabulary.",
            },
            {
                "title": "Guided Practice",
                "bullets": [
                    "Work through a sample problem together",
                    "Invite student reasoning",
                    "Correct errors in real time",
                ],
                "notes": "Pause after each step and ask checking questions.",
            },
            {
                "title": "Independent Practice",
                "bullets": [
                    "Assign a short individual task",
                    "Encourage peer comparison",
                    "Collect quick evidence of understanding",
                ],
                "notes": "Monitor and support learners who need scaffolding.",
            },
            {
                "title": "Exit Check",
                "bullets": [
                    "One concise recap question",
                    "One application question",
                    "Preview next lesson",
                ],
                "notes": "Use responses to plan follow-up interventions.",
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
    def generate_interactive_exercises(topic: str, subject: str, grade_level: str) -> Dict:
        """
        Generate interactive exercises (MCQ, short answer, group task).
        """
        system_prompt = """You are Aura-T, an expert teacher assistant.
Return a JSON object with:
{
  "exercises": [
        {"type": "mcq", "prompt": "...", "options": ["A","B","C","D"], "answer": "A", "dok_level": 1},
        {"type": "short_answer", "prompt": "...", "answer": "...", "dok_level": 2}
  ]
}
Rules:
- Create 5 to 10 questions total.
- Cover all DOK levels 1, 2, 3, and 4 at least once.
- Keep wording student-friendly.
"""
        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create interactive exercises for '{topic}' for {grade_level} {subject}."}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
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
