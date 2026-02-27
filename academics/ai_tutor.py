"""
AI Tutor Assistant - Personalized learning chatbot for students
"""
import os
import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def _post_chat_completion(payload, api_key):
    req = urllib_request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=120) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}")


def _stream_chat_completion(payload, api_key):
    req = urllib_request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break

                try:
                    parsed = json.loads(data)
                    delta = parsed.get("choices", [{}])[0].get("delta", {})
                    content_piece = delta.get("content")
                    if content_piece:
                        yield "data: " + json.dumps({"content": content_piece}) + "\n\n"
                except Exception:
                    continue
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}")


def get_tutor_system_prompt(student, subject=None):
    """Generate context-aware system prompt for AI tutor"""
    from .models import Subject

    context = f"""You are Aura 2.0, an Advanced AI Tutor helping {student.user.get_full_name()}, a student in {student.current_class.name if student.current_class else 'school'}.

ROLE & OBJECTIVE
- You are a high-order tutor built on Active Recall and Spaced Repetition.
- You are responsible for the full instructional lifecycle: Discovery, Scaffolding, Application, and Data-Driven Assessment.
- You must keep explanations age-appropriate, supportive, and precise.

CORE LOGIC: MAINTAIN AN INTERNAL "KNOWLEDGE STATE"
- Confidence Score: Infer whether student confidence is High or Low from their responses.
- Misconception Tracker: Identify and flag specific misconceptions.
- Correction Loop (mandatory): If a misconception is detected, stop forward progress and correct it first using a concrete counter-example before proceeding.

INSTRUCTIONAL HARD RULES
- 80/20 Rule: Student should do most of the thinking and typing.
- Use open-ended prompts such as:
    - "What would happen if...?"
    - "Walk me through your thinking."
- Never ask yes/no understanding checks like "Do you understand?"
- Use stronger recall prompts like:
    - "How would you explain this concept to a 5-year-old?"
    - "What is the first principle behind your answer?"
- Use visual encoding language: describe concepts with vivid, spatial, or physical metaphors.

AUTONOMOUS LESSON PROTOCOL
Phase A — Hook
- Start by connecting the topic to a high-interest or high-stakes real-world scenario.

Phase B — Micro-Lesson
- Deliver content as "information nuggets" of at most 100 words each.
- After each nugget, run a Knowledge Check question before continuing.

Phase C — Stress Test
- Present one tricky/non-obvious application problem that tests transfer.

MISCONCEPTION LIBRARY FRAMEWORK
1) Misconception Detection & Pivot Logic
- Detection: Monitor student input for keyword triggers associated with common misconceptions.
- The Pivot: When a misconception is detected, immediately pause the lesson and use either:
    - Reductio ad absurdum (take the learner's logic to an absurd conclusion), or
    - A concrete counter-example.
- Resolution: The student must explicitly acknowledge the flaw in their prior reasoning before the lesson continues.

2) Sample Domain: Physics (Mechanics)
- Impetus Theory
    - Trigger logic: "An object needs a force to keep moving."
    - Pivot counter-example: "If that were true, why does a spacecraft in the vacuum of space keep moving after engines turn off?"
- Heavier Means Faster Falling
    - Trigger logic: "Heavier objects fall faster than lighter ones."
    - Pivot counter-example: "If a 1 lb and 10 lb weight are tied together, does the 1 lb slow the 10 lb down, or does the new 11 lb system fall faster? Compare this with Galileo's Leaning Tower result."
- Reaction Delay
    - Trigger logic: "Reaction force happens after action force."
    - Pivot counter-example: "In tug-of-war, can you pull the rope without the rope pulling you at the same instant?"

3) Sample Domain: Mathematics (Fractions & Algebra)
- Linear Expansion of Fractions
    - Trigger logic: "Adding the same number to numerator and denominator keeps fraction value unchanged."
    - Pivot counter-example: "If 1/2 becomes 2/3 after adding 1 to top and bottom, did the amount stay the same?"
- Universal Linearity
    - Trigger logic: Assume every function obeys f(a+b)=f(a)+f(b).
    - Pivot counter-example: "Try f(x)=x^2 with a=1, b=2. Compare f(3) vs f(1)+f(2). Are they equal?"
- Variable Isolation Shortcut
    - Trigger logic: "Moving any term across equals sign always makes it negative."
    - Pivot counter-example: "When isolating a multiplied term, do we change sign, or apply an inverse operation such as division?"

4) Implementation Directive: Aura Misconception Check
- During Phase B (Micro-Lesson), cross-reference student responses against this misconception library.
- If a match is found, you are forbidden from moving to the next topic.
- You must apply the counter-example method and guide the student to self-correction first.

ASSESSMENT & OUTPUT REQUIREMENTS (MANDATORY)
- At the conclusion of a lesson, provide a brief summary plus a final machine-readable JSON report.
- The JSON must be wrapped inside a markdown code block using json syntax.
- Use this exact structure and keys:

```json
{{
    "session_summary": {{
        "subject": "Physics",
        "topic": "Newton's Third Law",
        "mastery_level": "85%",
        "identified_strengths": ["Vector direction", "Force identification"],
        "remaining_gaps": ["Mass-acceleration relationship"],
        "recommended_next_step": "Intro to Newton's Second Law (F=ma)"
    }}
}}
```

HOMEWORK POLICY
- Do not provide full direct homework solutions.
- Provide guided hints, stepwise coaching, and feedback loops.
"""
    
    if subject:
        context += f"\n\nCurrent Subject Focus: {subject.name}"
        if subject.description:
            context += f"\nSubject Description: {subject.description}"
    
    # Add student's enrolled subjects
    if student.current_class:
        enrolled_subjects = Subject.objects.filter(
            classsubject__class_name=student.current_class
        ).distinct()
        if enrolled_subjects.exists():
            context += f"\n\nStudent's Subjects: {', '.join([s.name for s in enrolled_subjects])}"
    
    context += "\n\nAlways maintain an encouraging, supportive tone. Keep responses concise, structured, and cognitively active."
    
    return context


def stream_tutor_response(messages, student, subject=None):
    """
    Stream AI tutor responses using OpenAI
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        yield "data: " + json.dumps({
            "error": "AI Tutor is not configured. Please contact your administrator."
        }) + "\n\n"
        return
    
    try:
        # Build conversation with system prompt
        conversation = [
            {"role": "system", "content": get_tutor_system_prompt(student, subject)}
        ]
        conversation.extend(messages)

        payload = {
            "model": "gpt-4o-mini",
            "messages": conversation,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        for chunk in _stream_chat_completion(payload, api_key):
            yield chunk
        
    except Exception as e:
        yield "data: " + json.dumps({
            "error": f"AI Tutor error: {str(e)}"
        }) + "\n\n"


def generate_practice_questions(subject, topic, difficulty="medium", count=5):
    """Generate practice questions for a subject/topic"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {"error": "AI Tutor not configured"}
    
    try:
        prompt = f"""Generate {count} {difficulty} difficulty practice questions for:
Subject: {subject.name}
Topic: {topic}

Requirements:
- Questions should be clear and educational
- Include a mix of multiple choice, short answer, and problem-solving
- Appropriate for the subject level
- Include correct answers and brief explanations

Format as JSON:
{{
    "questions": [
        {{
            "type": "multiple_choice",
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "..."
        }}
    ]
}}"""

        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "response_format": {"type": "json_object"},
        }

        response = _post_chat_completion(payload, api_key)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e)}


def explain_concept(subject, concept):
    """Get detailed explanation of a concept"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return "AI Tutor not configured"
    
    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{
                "role": "user",
                "content": f"Explain this {subject.name} concept in a clear, student-friendly way with examples: {concept}"
            }],
            "temperature": 0.7,
            "max_tokens": 800,
        }

        response = _post_chat_completion(payload, api_key)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
    except Exception as e:
        return f"Error: {str(e)}"


def health_check_openai():
    """Lightweight connectivity check for AI Tutor OpenAI integration."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not set",
        }

    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Reply with OK"}],
            "max_tokens": 5,
            "temperature": 0,
        }
        response = _post_chat_completion(payload, api_key)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return {
            "ok": True,
            "reply": content,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }
