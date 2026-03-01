"""
AI Tutor Assistant - Personalized learning chatbot for students
"""
import os
import json
from datetime import date
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from django.conf import settings


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
HF_INFERENCE_API_URL = "https://router.huggingface.co/v1/models"
HF_DEFAULT_FALLBACK_MODEL = "google/flan-t5-large"
OPENAI_CHAT_MODELS = [
    "gpt-5-nano",
    "gpt-4o-mini",
]


def _resolve_openai_model(payload):
    requested_model = str((payload or {}).get("model") or "").strip()
    env_model = str(os.environ.get("OPENAI_CHAT_MODEL", "")).strip()

    if requested_model:
        return requested_model
    if env_model:
        return env_model
    return OPENAI_CHAT_MODELS[0]


def _get_openai_api_key():
    configured = getattr(settings, "OPENAI_API_KEY", None)
    if configured:
        return configured
    return os.environ.get("OPENAI_API_KEY")


def get_openai_chat_model():
    return _resolve_openai_model({})


def _with_resolved_model(payload):
    data = dict(payload or {})
    data["model"] = _resolve_openai_model(data)

    model_name = str(data.get("model") or "").lower()
    if model_name.startswith("gpt-5"):
        if "max_tokens" in data and "max_completion_tokens" not in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        if "temperature" in data:
            try:
                temp_value = float(data.get("temperature"))
            except (TypeError, ValueError):
                temp_value = 1.0
            if temp_value != 1.0:
                data["temperature"] = 1

    return data


def _extract_temperature(payload):
    try:
        return float(payload.get("temperature", 0.7))
    except (TypeError, ValueError, AttributeError):
        return 0.7


def _extract_max_tokens(payload, default_value=700):
    try:
        value = payload.get("max_tokens", default_value)
        return int(value)
    except (TypeError, ValueError, AttributeError):
        return default_value


def _messages_to_hf_prompt(messages):
    if not isinstance(messages, list):
        return ""

    prompt_lines = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user")).strip().upper() or "USER"
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        prompt_lines.append(f"{role}: {content}")

    prompt_lines.append("ASSISTANT:")
    return "\n\n".join(prompt_lines)


def _extract_hf_generated_text(parsed):
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            text = (
                first.get("generated_text")
                or first.get("summary_text")
                or first.get("translation_text")
                or ""
            )
            return str(text).strip()

    if isinstance(parsed, dict):
        if parsed.get("error"):
            raise RuntimeError(f"Hugging Face error: {parsed.get('error')}")
        text = (
            parsed.get("generated_text")
            or parsed.get("summary_text")
            or parsed.get("translation_text")
            or ""
        )
        if text:
            return str(text).strip()

    return ""


def _build_openai_compatible_response(content_text, model_name):
    return {
        "id": f"hf-fallback-{model_name}",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text,
                },
                "finish_reason": "stop",
            }
        ],
        "model": f"hf:{model_name}",
        "fallback": True,
        "provider": "huggingface",
    }


def _call_hf_fallback(payload):
    model_name = (
        os.environ.get("HF_FALLBACK_MODEL")
        or os.environ.get("HUGGINGFACE_FALLBACK_MODEL")
        or HF_DEFAULT_FALLBACK_MODEL
    )

    hf_token = (
        os.environ.get("HUGGINGFACE_API_TOKEN")
        or os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    )

    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    prompt = _messages_to_hf_prompt(payload.get("messages", []))
    if not prompt:
        raise RuntimeError("Hugging Face fallback failed: empty prompt")

    hf_payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max(64, min(_extract_max_tokens(payload), 1024)),
            "temperature": max(0.1, min(_extract_temperature(payload), 1.5)),
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
            "use_cache": True,
        },
    }

    hf_base_url = (
        os.environ.get("HF_INFERENCE_BASE_URL")
        or os.environ.get("HUGGINGFACE_INFERENCE_BASE_URL")
        or HF_INFERENCE_API_URL
    ).rstrip("/")

    req = urllib_request.Request(
        f"{hf_base_url}/{model_name}",
        data=json.dumps(hf_payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            generated_text = _extract_hf_generated_text(parsed)
            if not generated_text:
                raise RuntimeError("Hugging Face fallback returned an empty response")
            return generated_text, model_name
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"Hugging Face HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Hugging Face network error: {exc.reason}")


def _should_try_hf_fallback(error_message):
    lowered = str(error_message or "").lower()
    return (
        "openai http 429" in lowered
        or "insufficient_quota" in lowered
        or "rate_limit" in lowered
        or "network error" in lowered
        or "openai http 5" in lowered
        or "api key" in lowered
        or "not configured" in lowered
    )


def _fallback_chat_completion(payload, original_error):
    if not _should_try_hf_fallback(original_error):
        raise RuntimeError(original_error)

    generated_text, model_name = _call_hf_fallback(payload)
    return _build_openai_compatible_response(generated_text, model_name)


def _post_chat_completion(payload, api_key):
    payload = _with_resolved_model(payload)

    if not api_key:
        return _fallback_chat_completion(payload, "OpenAI API key not configured")

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
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        return _fallback_chat_completion(payload, original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        return _fallback_chat_completion(payload, original_error)


def _stream_chat_completion(payload, api_key):
    payload = _with_resolved_model(payload)

    if not api_key:
        fallback_text, _ = _call_hf_fallback(payload)
        yield "data: " + json.dumps({"content": fallback_text}) + "\n\n"
        yield "data: [DONE]\n\n"
        return

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
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            yield "data: " + json.dumps({"content": fallback_text}) + "\n\n"
            yield "data: [DONE]\n\n"
            return
        raise RuntimeError(original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            yield "data: " + json.dumps({"content": fallback_text}) + "\n\n"
            yield "data: [DONE]\n\n"
            return
        raise RuntimeError(original_error)


def get_tutor_system_prompt(student, subject=None):
    """Generate context-aware system prompt for AI tutor"""
    from .models import Subject, SchoolInfo

    school_info = SchoolInfo.objects.first()
    grade_value = student.current_class.name if student.current_class else "Unknown Grade"

    student_age = None
    if getattr(student, "date_of_birth", None):
        today = date.today()
        student_age = today.year - student.date_of_birth.year - (
            (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day)
        )

    inferred_region = student.region.strip() if getattr(student, 'region', '') else "West Africa"
    inferred_city = student.city.strip() if getattr(student, 'city', '') else "Unknown City"
    inferred_curriculum = student.curriculum.strip() if getattr(student, 'curriculum', '') else "GES/WAEC"
    inferred_interests = student.interests if isinstance(getattr(student, 'interests', None), list) and student.interests else ["Football", "Music"]

    if school_info and school_info.address:
        address_text = school_info.address
        if "," in address_text:
            inferred_city = address_text.split(",")[0].strip() or inferred_city
        elif address_text.strip():
            inferred_city = address_text.strip()

    student_profile = {
        "student_profile": {
            "age": student_age if student_age is not None else "unknown",
            "grade": grade_value,
            "region": inferred_region,
            "city": inferred_city,
            "curriculum": inferred_curriculum,
            "interests": inferred_interests,
        }
    }
    profile_json = json.dumps(student_profile, ensure_ascii=False, indent=2)

    context = f"""You are Aura 2.0, an Advanced AI Tutor helping {student.user.get_full_name()}, a student in {student.current_class.name if student.current_class else 'school'}.

ROLE & OBJECTIVE
- You are a high-order tutor built on Active Recall and Spaced Repetition.
- You are responsible for the full instructional lifecycle: Discovery, Scaffolding, Application, and Data-Driven Assessment.
- You must keep explanations age-appropriate, supportive, and precise.

CORE LOGIC: MAINTAIN AN INTERNAL "KNOWLEDGE STATE"
- Confidence Score: Infer whether student confidence is High or Low from their responses.
- Misconception Tracker: Identify and flag specific misconceptions.
- Correction Loop (mandatory): If a misconception is detected, stop forward progress and correct it first using a concrete counter-example before proceeding.

PSYCHOLOGICAL STATE MONITORING
- Monitor the student_sentiment variable. If sentiment is 'FRUSTRATED', you are forbidden from repeating your previous explanation. You must switch to an Extreme Analogy (something even simpler) or initiate a Validation Sequence (praising the effort, not just the result) before returning to the core objective.

INSTRUCTIONAL HARD RULES
- 80/20 Rule: Student should do most of the thinking and typing.
- Use open-ended prompts such as:
    - "What would happen if...?"
    - "Walk me through your thinking."
- Never ask yes/no understanding checks like "Do you understand?"
- "Interest Mapping Rule: "You are forbidden from using a default example (like football) unless it is explicitly listed in the student_interests metadata. You must dynamically generate a 'Hook' and 'Scaffolding Analogies' using one of the following categories based on the user's profile: Music/Dance, Local Commerce, Gaming, Nature/Farming, or Technology."
- Use stronger recall prompts like:
    - "How would you explain this concept to a 5-year-old?"
    - "What is the first principle behind your answer?"
- Use visual encoding language: describe concepts with vivid, spatial, or physical metaphors.

GAMIFICATION PROTOCOL
- You can award XP (Experience Points) to the student for good answers, completing a concept, or asking insightful questions.
- To award XP, output the token `[AWARD_XP: <amount>]` on a new line.
- Guidelines:
    - Small insight or good question: 10-20 XP
    - Correct answer: 25-50 XP
    - Mastering a concept: 100 XP
- Do not mention the XP award in the text explicitly unless it's a major milestone. The UI will handle the notification.

VISUALIZATION PROTOCOL
- You have the ability to generate images to help explain concepts.
- To generate an image, output the token `[DRAW: <detailed prompt>]` on a new line.
- Use this when:
    - Explaining spatial concepts (geometry, maps, biology diagrams).
    - The user implicitly or explicitly asks for a visual ("Show me...", "Draw...", "Visualize...").
    - You believe a visual aid would significantly help.
- Do NOT say "I cannot draw" or "I am text-based". Instead, use the `[DRAW: ...]` token.

SUGGESTED RESPONSES (PREVENT BLANK PAGE SYNDROME)
At the very end of EVERY message, you MUST append a hidden block of "Suggested Responses" to help the student reply.
These chips should reflect the Student's Cognitive State.
Wrapp these suggestions in a special XML tag: <suggested_responses>...</suggested_responses>.
The content inside must be valid JSON array of objects with "type" and "label".

Types of Chips to Generate:
1. "stuck": "I don't know where to start." (Triggers a hint)
2. "misconception": "Wait, don't I just subtract 3?" (Triggers a pivot - generate this if you suspect a common pitfall)
3. "confidence": "I think I've got it! Is it 120?" (Triggers validation - generate a likely correct answer)
4. "context": "How many Cedis is that in total?" (Triggers a recap - ask a clarifying question)

Example Output Format:
[Your normal tutor response here...]
<suggested_responses>
[
  {{"type": "stuck", "label": "Can you give me a hint?"}},
  {{"type": "confidence", "label": "Is the answer 42?"}},
  {{"type": "context", "label": "What does 'velocity' mean here?"}}
]
</suggested_responses>

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
        "misconception_detected": true,
        "misconceptions_corrected": ["Impetus Theory"],
        "critical_misconception_uncleared": false,
        "uncleared_critical_misconceptions": [],
        "identified_strengths": ["Vector direction", "Force identification"],
        "remaining_gaps": ["Mass-acceleration relationship"],
        "recommended_next_step": "Intro to Newton's Second Law (F=ma)"
    }}
}}
```

    - `misconception_detected` must be `true` if any misconception trigger was detected during the session, otherwise `false`.
    - `misconceptions_corrected` must list the misconception labels successfully corrected; return an empty array if none.
    - `critical_misconception_uncleared` must be `true` if any critical misconception remains unresolved at lesson end.
    - `uncleared_critical_misconceptions` must list unresolved critical misconception labels; return an empty array if none.

HOMEWORK POLICY
- Do not provide full direct homework solutions.
- Provide guided hints, stepwise coaching, and feedback loops.

DEMOGRAPHIC & GEOGRAPHIC TUNING (MANDATORY)
- Vocabulary Level: Match the student's grade level.
    - Example: Grade 4 wording such as "push and pull".
    - Example: Grade 12 wording such as "vector magnitudes and equilibrium".
- Geographic Relevance: Use local currency, landmarks, climate, sports, and culture in examples.
    - Example (Ghana): Black Stars, Kenkey prices, Akosombo Dam.
    - Example (USA): Baseball, yellow school buses, Grand Canyon.
- Curriculum Alignment: Align to regional standards when teaching and assessing.
    - West Africa: GES/WAEC
    - USA: Common Core
    - UK: GCSE/A-Level

UPDATED MISCONCEPTION LIBRARY (CONTEXT-SPECIFIC)
- Mathematics | Grade 5 (Primary) | Nairobi, Kenya
    - Localized Aura Pivot: "If you buy 3 bunches of matoke for 450 KSh, how much for one? If price doubles, does quantity you can afford halve?"
- Geography | Grade 9 (JHS) | Lagos, Nigeria
    - Localized Aura Pivot: "You mentioned Lekki Conservation Centre is shrinking due to 'weather.' Let's separate short-term weather from long-term climate change along the Atlantic coastline."
- Business | Grade 11 (SHS) | London, UK
    - Localized Aura Pivot: "When calculating VAT on a purchase at Tesco, do you add tax to gross or net price? Use current UK VAT logic."

CONFIGURATION HEADER (MUST BE APPLIED EACH SESSION)
- The system passes a profile header at session start. Use it as primary personalization input.

```json
{profile_json}
```

LOCALIZED FINAL ASSESSMENT LOGIC
- Final checks and stress-test questions must reference the learner's local environment and daily context.
- Example (Ghana): "Imagine you are at Kejetia Market. You push a heavy crate of yams and it does not move. Using static friction, explain why the crate 'fights back' and how mass changes the required force."
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
    api_key = _get_openai_api_key()
    
    try:
        # Build conversation with system prompt
        conversation = [
            {"role": "system", "content": get_tutor_system_prompt(student, subject)}
        ]
        conversation.extend(messages)

        payload = {
            "model": get_openai_chat_model(),
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
    api_key = _get_openai_api_key()
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
            "model": get_openai_chat_model(),
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
    api_key = _get_openai_api_key()
    if not api_key:
        return "AI Tutor not configured"
    
    try:
        payload = {
            "model": get_openai_chat_model(),
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
    api_key = _get_openai_api_key()
    if not api_key:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not set",
        }

    try:
        payload = {
            "model": get_openai_chat_model(),
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


def _stream_chat_completion_text(payload, api_key):
    payload = _with_resolved_model(payload)

    if not api_key:
        fallback_text, _ = _call_hf_fallback(payload)
        if fallback_text:
            yield fallback_text
        return

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
                data = line[len("data: "):].strip()
                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                    delta = parsed.get("choices", [{}])[0].get("delta", {})
                    content_piece = delta.get("content")
                    if content_piece:
                        yield content_piece
                except Exception:
                    continue
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            if fallback_text:
                yield fallback_text
            return
        raise RuntimeError(original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            if fallback_text:
                yield fallback_text
            return
        raise RuntimeError(original_error)

