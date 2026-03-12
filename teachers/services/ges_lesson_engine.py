import json
import logging
from typing import Dict

from django.conf import settings
from django.utils import timezone

from academics.ai_tutor import _post_chat_completion, get_openai_chat_model

logger = logging.getLogger(__name__)


class GESLessonEngine:
    """
    Generates GES weekly lesson notes format (table-friendly structure).
    This is intentionally separate from Aura-T lesson generation.
    """

    @staticmethod
    def _extract_json_object(raw: str) -> Dict:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start:end + 1])
        return {}

    @staticmethod
    def _fallback(topic: str, subject: str, grade_level: str, week_number: int) -> Dict:
        return {
            'lesson_plan': {
                'objectives': (
                    f"Content Standard: Learners understand core ideas in {topic}.\n\n"
                    f"Indicator: Learners explain and apply {topic} in classroom and real-life contexts."
                ),
                'teaching_materials': 'Chalkboard, marker, learner notebook, chart paper, textbook',
                'introduction': (
                    'Guide learners to activate prior knowledge through a short recall activity.\n'
                    f'Ask two warm-up questions linked to {topic}.'
                ),
                'presentation': (
                    f"Model the main concept in {topic} step-by-step.\n"
                    'Use guided practice, pair discussion, and whole-class feedback.\n'
                    'Provide one scaffolded task and one challenge task.'
                ),
                'evaluation': (
                    'Ask oral checkpoint questions and use a short exit ticket to verify learning outcomes.\n'
                    'Record misconceptions for next lesson remediation.'
                ),
                'homework': f'Learners complete a short assignment on {topic} and prepare one question for review.',
                'remarks': 'Teacher reflection: Note misconceptions and pacing adjustments for the next lesson.',
            },
            'b7_meta': {
                'period': '1',
                'duration': '60 Minutes',
                'strand': subject,
                'sub_strand': topic,
                'class_size': '',
                'content_standard': f'Learners understand core concepts in {topic}.',
                'indicator': f'Learners explain and apply {topic} accurately.',
                'lesson_of': '1 of 3',
                'performance_indicator': 'Learners can explain and apply the concept in class activities.',
                'core_competencies': 'Critical Thinking, Communication, Collaboration',
                'references': f'National {subject} Curriculum',
                'keywords': topic,
                'generated_format': 'ges_weekly_notes',
                'generated_at': timezone.now().isoformat(),
                'week_number': week_number,
                'grade_level': grade_level,
            },
        }

    @staticmethod
    def generate_weekly_notes(topic: str, subject: str, grade_level: str, week_number: int = 1) -> Dict:
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return GESLessonEngine._fallback(topic, subject, grade_level, week_number)

        system_prompt = f"""You are a Ghana GES lesson planner.
Generate a weekly lesson notes draft for:
- Subject: {subject}
- Class: {grade_level}
- Topic/Sub-strand: {topic}
- Week Number: {week_number}

The output must match a traditional GES weekly lesson-notes table style and be concise, practical, and classroom-ready.

Return ONLY valid JSON with this exact schema:
{{
  "lesson_plan": {{
    "objectives": "content standard + indicator in plain text",
    "teaching_materials": "resources list",
    "introduction": "Phase 1 starter activities",
    "presentation": "Phase 2 new learning activities",
    "evaluation": "assessment/check for understanding",
    "homework": "homework task",
    "remarks": "teacher reflection note"
  }},
  "b7_meta": {{
    "period": "e.g. 1",
    "duration": "e.g. 60 Minutes",
    "strand": "main strand",
    "sub_strand": "sub strand/topic",
    "class_size": "optional",
    "content_standard": "single concise statement",
    "indicator": "single concise indicator statement",
    "lesson_of": "e.g. 1 of 3",
    "performance_indicator": "what learners can do",
    "core_competencies": "comma-separated competencies",
    "references": "curriculum references",
    "keywords": "comma-separated keywords"
  }}
}}
"""

        try:
            payload = {
                'model': get_openai_chat_model(),
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {
                        'role': 'user',
                        'content': (
                            f"Create a complete weekly lesson notes draft for Week {week_number}. "
                            'Use clear teacher actions, learner actions, and assessment steps.'
                        ),
                    },
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.5,
                'max_tokens': 1400,
            }

            response = _post_chat_completion(payload, api_key)
            content = response['choices'][0]['message']['content']
            parsed = GESLessonEngine._extract_json_object(content)
            if not parsed or 'lesson_plan' not in parsed:
                return GESLessonEngine._fallback(topic, subject, grade_level, week_number)

            parsed.setdefault('b7_meta', {})
            parsed['b7_meta'].setdefault('generated_format', 'ges_weekly_notes')
            parsed['b7_meta'].setdefault('generated_at', timezone.now().isoformat())
            parsed['b7_meta'].setdefault('week_number', week_number)
            parsed['b7_meta'].setdefault('grade_level', grade_level)
            return parsed
        except Exception as exc:
            logger.error('GES lesson generation failed: %s', exc)
            return GESLessonEngine._fallback(topic, subject, grade_level, week_number)
