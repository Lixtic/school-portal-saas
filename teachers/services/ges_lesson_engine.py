import json
import logging
import re
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

    _ACTION_VERBS = (
        'identify', 'explain', 'describe', 'demonstrate', 'apply', 'solve',
        'construct', 'compare', 'analyze', 'analyse', 'classify', 'evaluate',
        'justify', 'create', 'write', 'calculate', 'interpret', 'present',
    )

    _STOP_WORDS = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'onto', 'about',
        'their', 'they', 'them', 'will', 'shall', 'should', 'must', 'can', 'able',
        'learners', 'students', 'pupils', 'lesson', 'topic', 'indicator', 'using',
        'through', 'across', 'each', 'every', 'when', 'where', 'which', 'whose',
    }

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
    def _indicator_keywords(indicator: str):
        tokens = re.findall(r"[a-zA-Z]{4,}", (indicator or '').lower())
        keywords = [t for t in tokens if t not in GESLessonEngine._STOP_WORDS]
        return list(dict.fromkeys(keywords))[:8]

    @staticmethod
    def _has_action_verb(text: str) -> bool:
        text_l = (text or '').lower()
        return any(v in text_l for v in GESLessonEngine._ACTION_VERBS)

    @staticmethod
    def _indicator_linked(text: str, indicator: str) -> bool:
        text_l = (text or '').lower()
        if not text_l.strip():
            return False
        kws = GESLessonEngine._indicator_keywords(indicator)
        if not kws:
            return True
        hits = sum(1 for kw in kws if kw in text_l)
        # 1 strong keyword hit for short indicators, 2 for longer ones.
        threshold = 1 if len(kws) <= 3 else 2
        return hits >= threshold

    @staticmethod
    def _is_indicator_aligned(parsed: Dict, indicator: str) -> bool:
        lesson = parsed.get('lesson_plan') or {}
        objectives = lesson.get('objectives', '')
        presentation = lesson.get('presentation', '')
        evaluation = lesson.get('evaluation', '')
        homework = lesson.get('homework', '')

        return (
            GESLessonEngine._indicator_linked(objectives, indicator)
            and GESLessonEngine._indicator_linked(presentation, indicator)
            and GESLessonEngine._indicator_linked(evaluation, indicator)
            and GESLessonEngine._indicator_linked(homework, indicator)
            and GESLessonEngine._has_action_verb(evaluation)
            and GESLessonEngine._has_action_verb(homework)
        )

    @staticmethod
    def _build_payload(system_prompt: str, user_prompt: str) -> Dict:
        return {
            'model': get_openai_chat_model(),
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'response_format': {'type': 'json_object'},
            'temperature': 0.5,
            'max_tokens': 1400,
        }

    @staticmethod
    def _fallback(topic: str, indicator: str, subject: str, grade_level: str, week_number: int) -> Dict:
        return {
            'lesson_plan': {
                'objectives': (
                    f"Content Standard: Learners develop understanding around {topic}.\n\n"
                    f"Indicator: {indicator}"
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
                'indicator': indicator,
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
    def generate_weekly_notes(topic: str, indicator: str, subject: str, grade_level: str, week_number: int = 1) -> Dict:
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return GESLessonEngine._fallback(topic, indicator, subject, grade_level, week_number)

        system_prompt = f"""You are a Ghana GES lesson planner.
Generate a weekly lesson notes draft for:
- Subject: {subject}
- Class: {grade_level}
- Topic/Sub-strand: {topic}
- Target Indicator (must be achieved): {indicator}
- Week Number: {week_number}

The output must match a traditional GES weekly lesson-notes table style and be concise, practical, and classroom-ready.
Every activity, assessment, and homework item must directly align to and measure the target indicator.

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
            user_prompt = (
                f"Create a complete weekly lesson notes draft for Week {week_number}. "
                f"The lesson must achieve this indicator exactly: {indicator}. "
                'Use clear teacher actions, learner actions, and assessment steps.'
            )
            payload = GESLessonEngine._build_payload(system_prompt, user_prompt)

            response = _post_chat_completion(payload, api_key)
            content = response['choices'][0]['message']['content']
            parsed = GESLessonEngine._extract_json_object(content)
            if not parsed or 'lesson_plan' not in parsed:
                return GESLessonEngine._fallback(topic, indicator, subject, grade_level, week_number)

            # Auto-regenerate once if the draft is not strongly aligned to the target indicator.
            if not GESLessonEngine._is_indicator_aligned(parsed, indicator):
                strict_user_prompt = (
                    f"Regenerate this as a strict indicator-aligned weekly notes plan for Week {week_number}. "
                    f"Indicator: {indicator}. "
                    'REQUIRED: evaluation and homework must each include at least one observable action verb '
                    '(e.g., explain, apply, solve, demonstrate) and explicitly assess the same indicator. '
                    'Do not drift to generic topic-only objectives.'
                )
                strict_payload = GESLessonEngine._build_payload(system_prompt, strict_user_prompt)
                strict_response = _post_chat_completion(strict_payload, api_key)
                strict_content = strict_response['choices'][0]['message']['content']
                strict_parsed = GESLessonEngine._extract_json_object(strict_content)
                if strict_parsed and strict_parsed.get('lesson_plan'):
                    parsed = strict_parsed

            parsed.setdefault('b7_meta', {})
            parsed['b7_meta'].setdefault('generated_format', 'ges_weekly_notes')
            parsed['b7_meta'].setdefault('generated_at', timezone.now().isoformat())
            parsed['b7_meta'].setdefault('week_number', week_number)
            parsed['b7_meta'].setdefault('grade_level', grade_level)
            parsed['b7_meta']['indicator'] = parsed['b7_meta'].get('indicator') or indicator
            return parsed
        except Exception as exc:
            logger.error('GES lesson generation failed: %s', exc)
            return GESLessonEngine._fallback(topic, indicator, subject, grade_level, week_number)
