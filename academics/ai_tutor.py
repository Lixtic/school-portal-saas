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
    
    context = f"""You are an expert AI tutor helping {student.user.get_full_name()}, a student in {student.current_class.name if student.current_class else 'school'}.

Your role:
- Provide clear, age-appropriate explanations
- Break down complex topics into simple steps
- Ask guiding questions to help students think critically
- Offer encouragement and positive reinforcement
- Adapt explanations based on student's understanding level

Guidelines:
- Use simple language suitable for the student's grade level
- Include examples and analogies when explaining concepts
- Check for understanding before moving to next concepts
- Never give direct answers to homework - guide students to find answers themselves
- Be patient, supportive, and enthusiastic about learning
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
    
    context += "\n\nAlways maintain an encouraging, supportive tone. Make learning fun and engaging!"
    
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
