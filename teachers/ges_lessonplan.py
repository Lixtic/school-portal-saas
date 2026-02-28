from dataclasses import dataclass
from typing import List, Dict
import re


@dataclass
class LessonPlanTemplate:
    """Template matching the B8-CAD-WK9.pdf format exactly"""

    institution_name: str = "Educational Institution"
    phone_numbers: str = "0000000000/0000000000"
    term: str = "FIRST TERM"
    lesson_plan_title: str = "WEEKLY LESSON PLAN"
    week: str = "WEEK 1"
    week_ending: str = ""
    day: str = ""

    subject: str = ""
    duration: str = "60MINS"
    strand: str = ""
    sub_strand: str = ""
    class_level: str = ""
    class_size: str = ""

    content_standard: str = ""
    indicator: str = ""
    lesson_number: str = "1 of 1"

    performance_indicator: str = ""
    core_competencies: str = ""
    key_words: str = ""
    reference: str = ""

    phase_1_starter: str = ""
    phase_2_new_learning: str = ""
    phase_3_reflection: str = ""

    resources: str = ""


@dataclass
class FormattedLessonPlan:
    """Enhanced lesson plan that matches the exact PDF format"""

    institution_name: str
    contact_info: str
    term: str
    week: str
    week_ending: str
    day: str

    subject: str
    duration: str
    strand: str
    sub_strand: str
    class_level: str
    class_size: str

    content_standard: str
    indicator: str
    lesson_number: str
    performance_indicator: str
    core_competencies: str
    key_words: List[str]
    reference: str

    starter_activities: str
    new_learning_activities: str
    reflection_activities: str
    resources: str

    assessment_methods: List[str]
    success_criteria: List[str]

    differentiation_strategies: str
    homework_assignment: str
    notes: str


def create_formatted_lesson_plan_template() -> str:
    """Returns a template string that matches the B8-CAD-WK9.pdf format."""
    template = """
{institution_name} {contact_info}
{term}
{lesson_plan_title} – {class_level}
{week}

Week Ending: {week_ending} DAY: {day} Subject: {subject}
Duration: {duration} Strand: {strand}
Sub Strand: {sub_strand}
Class: {class_level} Class Size: {class_size}

Content Standard: Indicator:
{content_standard} {indicator}
Lesson:
{lesson_number}

Performance Indicator: Core Competencies:
{performance_indicator} {core_competencies}

Key words
Reference: {reference}

Phase/Duration Learners Activities Resources

PHASE 1: STARTER {phase_1_starter}

PHASE 2: NEW {phase_2_new_learning} {resources}
LEARNING

PHASE 3: {phase_3_reflection}
REFLECTION
"""
    return template


def format_reflection_questions() -> str:
    """Standard reflection questions from the PDF format."""
    return (
        "Ask learners to do the following by ways of reflecting on the lesson:\n"
        "1. Tell the class what you learnt during the lesson.\n"
        "2. Tell the class how you will use the knowledge they acquire during the lesson.\n"
        "3. Which aspects of the lesson did you not understand?"
    )


CORE_COMPETENCIES_MAP: Dict[str, str] = {
    "PL5.2": "Personal Learning and Self-Development",
    "PL6.1": "Critical thinking and Problem Solving",
    "CG5.4": "Communication and Collaboration",
    "PL6.2": "Creativity and Innovation",
    "DL5.3": "Digital Literacy",
}


LESSON_PHASES_TEMPLATE: Dict[str, str] = {
    "starter": (
        "Recap of previous lesson using RCA technique.\n"
        "Draw learner's attention to the new lesson's content standard and indicator(s)."
    ),
    "reflection": format_reflection_questions(),
}


def render_ges_lesson_plan(template_data: LessonPlanTemplate) -> str:
    """Renders a LessonPlanTemplate into the printable GES lesson-note text format."""
    return create_formatted_lesson_plan_template().format(
        institution_name=template_data.institution_name,
        contact_info=template_data.phone_numbers,
        term=template_data.term,
        lesson_plan_title=template_data.lesson_plan_title,
        class_level=template_data.class_level,
        week=template_data.week,
        week_ending=template_data.week_ending,
        day=template_data.day,
        subject=template_data.subject,
        duration=template_data.duration,
        strand=template_data.strand,
        sub_strand=template_data.sub_strand,
        class_size=template_data.class_size,
        content_standard=template_data.content_standard,
        indicator=template_data.indicator,
        lesson_number=template_data.lesson_number,
        performance_indicator=template_data.performance_indicator,
        core_competencies=template_data.core_competencies,
        reference=template_data.reference,
        phase_1_starter=template_data.phase_1_starter,
        phase_2_new_learning=template_data.phase_2_new_learning,
        resources=template_data.resources,
        phase_3_reflection=template_data.phase_3_reflection,
    ).strip()


def parse_ges_lesson_text(text: str) -> Dict[str, str]:
    """Best-effort parser that extracts key fields from a GES-formatted lesson text."""
    if not text:
        return {}

    compact_text = text.replace("\r\n", "\n")
    compact_text = re.sub(r"[*_`#]", "", compact_text)
    compact_text = re.sub(r"\n{3,}", "\n\n", compact_text)

    def _search(pattern, flags=re.IGNORECASE | re.DOTALL):
        match = re.search(pattern, compact_text, flags)
        return match.group(1).strip() if match else ""

    week_number = _search(r"WEEK\s*(\d+)")
    subject = _search(r"(?:Subject|SUBJECT)\s*:\s*(.+?)(?:\n|$)")
    class_level = _search(r"(?:Class|Class Level)\s*:\s*([^\n]+?)(?:\s+Class Size:|\n|$)")
    content_standard = _search(r"Content Standard\s*:\s*(.+?)(?:\n|Indicator:|$)")
    indicator = _search(r"Indicator\s*:\s*(.+?)(?:\n|Lesson:|$)")
    performance_indicator = _search(r"Performance Indicator\s*:\s*(.+?)(?:\n|Core Competencies:|$)")
    phase_1_starter = _search(r"PHASE\s*1\s*:\s*STARTER\s*(.+?)(?:\n\s*PHASE\s*2|$)")
    phase_2_new = _search(r"PHASE\s*2\s*:\s*NEW\s*(.+?)(?:\n\s*PHASE\s*3|\n\s*LEARNING|$)")
    phase_3_reflection = _search(r"PHASE\s*3\s*:\s*(.+?)(?:\n\s*REFLECTION|$)")
    reference = _search(r"Reference:\s*(.+?)(?:\n|$)")

    if not phase_1_starter:
        phase_1_starter = _search(r"Starter\s*(?:\(.*?\))?\s*:\s*(.+?)(?:\n|$)")
    if not phase_2_new:
        phase_2_new = _search(r"(?:New Learning|Presentation|Activity)\s*(?:\(.*?\))?\s*:\s*(.+?)(?:\n|$)")
    if not phase_3_reflection:
        phase_3_reflection = _search(r"(?:Reflection|Assessment|Evaluation)\s*(?:\(.*?\))?\s*:\s*(.+?)(?:\n|$)")

    topic = indicator or subject or "GES AI Draft Lesson"
    objectives = performance_indicator or ""

    return {
        "week_number": week_number,
        "subject": subject,
        "class_level": class_level,
        "content_standard": content_standard,
        "indicator": indicator,
        "topic": topic,
        "objectives": objectives,
        "introduction": phase_1_starter,
        "presentation": phase_2_new,
        "evaluation": phase_3_reflection,
        "teaching_materials": reference,
    }
