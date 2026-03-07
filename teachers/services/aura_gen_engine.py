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

YOU MUST INCLUDE ALL FOUR OF THESE IN EVERY PLAN — NO EXCEPTIONS:

① LOCALIZED HOOK — Phase 1 must open with a culturally grounded hook drawn from Ghana: Adinkra symbols,
  Kente weaving, Akosombo Dam, local market trading, BOST fuel pipelines, Tema Motorway engineering,
  Cocoa farming, Bolgatanga basketry, digital payments via MoMo, Nkrumah's scientific vision, etc.
  The hook must directly connect to {topic} — not just mention Ghana in passing.

② AI PULSE CHECK — Phase 1 must include a \"🔍 Pulse Check\" block: 3 targeted diagnostic questions
  (verbal or whiteboard). Students respond quickly. Teacher mentally logs who struggles — those
  students become the Data-Trigger targets in Phase 3.

③ TWO LEARNING PATHS — Phase 2 must split into:
  🟢 SUPPORT PATH — for students who hesitated during the Pulse Check. Concrete, scaffolded, step-by-step.
  🔵 EXTENSION PATH — for students who answered confidently. Deeper, cross-curricular, real-world or analytical.
  Both paths must be SUBSTANTIVELY DIFFERENT — not just "easier" vs "harder" versions of the same task.

④ DATA-TRIGGER — Phase 3 must contain a \"📊 DATA-TRIGGER\" block with specific teacher instructions:
  For each Pulse Check question, state exactly what the teacher should do if a student missed it
  (e.g., re-pair, reteach, assign a specific task). Also state how to leverage Extension Path students.

OUTPUT FORMAT (use these EXACT bold headers — no markdown tables):

**Subject:** {subject}
**Class:** {grade_level}
**Topic:** {topic}
**Duration:** 60 minutes
**Strand:** [appropriate strand from GES curriculum]
**Sub Strand:** [appropriate sub-strand]
**Content Standard:** [1–2 sentence GES-aligned content standard]
**Indicator:** [observable, measurable indicator]
**Performance Indicator:** [what mastery looks like in student action]
**Core Competencies:** Critical Thinking, Communication, Cultural Identity, Creativity and Innovation
**Key words:** [5 essential vocabulary terms for this topic]
**Reference:** [GES Curriculum document or standard textbook reference]

**PHASE 1: STARTER [15 mins]**
🌍 LOCALIZED HOOK:
[2–3 sentences grounding {topic} in a specific Ghanaian context. Name the real place, item, or practice.]

🔍 PULSE CHECK (AI-Integrated Diagnostic):
Q1: [Diagnostic question probing prerequisite knowledge]
Q2: [Diagnostic question on a common misconception about {topic}]
Q3: [Diagnostic question connecting {topic} to the hooks context above]
Teacher note: Mentally log students who hesitate or answer incorrectly — they are your Data-Trigger targets for Phase 3.

**PHASE 2: NEW LEARNING [30 mins]**
Class Introduction (all students):
[2–3 sentences that bridge the hook into the core concept and set context for both paths.]

🟢 SUPPORT PATH (for students who struggled in the Pulse Check):
Step 1: [Concrete, hands-on or visual scaffolded activity]
Step 2: [Guided practice with a worked example or sentence frame]
Step 3: [Paired or small-group practice with teacher monitoring]
Success marker: [How teacher knows this student is ready to move on]

🔵 EXTENSION PATH (for students who aced the Pulse Check):
Task 1: [Real-world application or local problem-solving using {topic}]
Task 2: [Cross-curricular or analytical challenge — connects to another subject or Ghana context]
Task 3: [Higher-order thinking: design, evaluate, or create using {topic}]
Success marker: [What a strong Extension Path product looks like]

**PHASE 3: REFLECTION [15 mins]**
Whole-class debrief:
[1–2 sentences for whole-class exit reflection or share-out.]

📊 DATA-TRIGGER (Teacher Action Guide — carry this into tomorrow's planning):
- Students who missed Pulse Check Q1: [Exact reteach or re-pairing action for next lesson]
- Students who missed Pulse Check Q2: [Exact reteach or re-pairing action for next lesson]
- Students who missed Pulse Check Q3: [Exact reteach or re-pairing action for next lesson]
- Students who completed the Extension Path: [How to leverage them — peer teaching, presentation, deeper task]

**Resources:** [List all materials: textbook pages, whiteboard, manipulatives, local objects if applicable]
**Homework:** [Clearly differentiated: one task for Support Path students, one for Extension Path students]
"""

        try:
            payload = {
                "model": get_openai_chat_model(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Generate the full Aura-T lesson plan for '{topic}' "
                        f"({grade_level}, {subject}). "
                        "Include every mandatory element: Localized Hook, Pulse Check, "
                        "Support Path, Extension Path, and Data-Trigger."
                    )}
                ],
                "temperature": 0.75,
                "max_tokens": 2000,
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
