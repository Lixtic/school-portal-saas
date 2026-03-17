
import os
import re
import json
import random
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.db import connection
from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)


def get_openai_api_key():
    configured = getattr(settings, 'OPENAI_API_KEY', None)
    if configured:
        return configured
    return os.environ.get("OPENAI_API_KEY")


# ═══════════════════════════════════════════════════════════
# Allowed Realtime API models
# ═══════════════════════════════════════════════════════════
ALLOWED_REALTIME_MODELS = [
    'gpt-realtime',
    'gpt-realtime-mini',
    # Legacy names (mapped to GA equivalents)
    'gpt-4o-realtime-preview-2024-12-17',
    'gpt-4o-mini-realtime-preview-2024-12-17',
]

# Map legacy model names to GA equivalents
MODEL_MIGRATION_MAP = {
    'gpt-4o-realtime-preview-2024-12-17': 'gpt-realtime',
    'gpt-4o-mini-realtime-preview-2024-12-17': 'gpt-realtime-mini',
}

DEFAULT_REALTIME_MODEL = 'gpt-realtime'
VOICE_XP_TOKEN_SALT = 'students.voice_xp'
VOICE_XP_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 3
VOICE_XP_MIN_INTERVAL_SECONDS = 8
VOICE_XP_MAX_PER_SESSION = 350


def _client_ip(request):
    xff = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    return xff or (request.META.get('REMOTE_ADDR') or '0.0.0.0')


def _rate_limit(request, scope, limit=30, window_seconds=60):
    """Simple cache-backed limiter keyed by tenant + user + IP + scope."""
    schema = connection.tenant.schema_name
    uid = getattr(request.user, 'id', None) or 'anon'
    ip = _client_ip(request)
    key = f"{schema}:rl:{scope}:{uid}:{ip}"
    added = cache.add(key, 1, timeout=window_seconds)
    if added:
        return False
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window_seconds)
        count = 1
    if count > limit:
        logger.warning("rate_limited scope=%s uid=%s ip=%s count=%s", scope, uid, ip, count)
        return True
    return False


def _build_voice_xp_token(user_id, session_id):
    payload = {'uid': user_id, 'sid': str(session_id)}
    return signing.dumps(payload, salt=VOICE_XP_TOKEN_SALT)


def _voice_active_session_cache_key(user_id):
    schema = connection.tenant.schema_name
    return f"{schema}:voice_xp:active:{user_id}"


def _voice_ended_session_cache_key(user_id, session_id):
    schema = connection.tenant.schema_name
    return f"{schema}:voice_xp:ended:{user_id}:{session_id}"


def _map_class_to_cognitive_stage(class_name):
    """
    Map a class name to a cognitive/intellectual stage descriptor.
    Handles Ghana GES naming: Primary 1-6, Basic 1-9, JHS 1-3, SHS 1-3, Form N.
    Returns (stage_label, complexity_level, exam_context).
    complexity_level: 1 (youngest) → 6 (university prep)
    """
    if not class_name:
        return ("General Level", 3, "")

    name = class_name.strip().upper()

    # SHS / Form 4-6 → Senior High
    if any(x in name for x in ['SHS 3', 'FORM 6', 'SHS3', 'GRADE 12']):
        return ("Senior High School 3 — University Preparation", 6,
                "The student is preparing for WASSCE. Use exam-focused, analytical language.")
    if any(x in name for x in ['SHS 2', 'FORM 5', 'SHS2', 'GRADE 11']):
        return ("Senior High School 2 — Advanced Specialisation", 5, "")
    if any(x in name for x in ['SHS 1', 'FORM 4', 'SHS1', 'GRADE 10']):
        return ("Senior High School 1 — Subject Specialisation Entry", 5, "")

    # JHS / Basic 7-9 → Junior High
    if any(x in name for x in ['JHS 3', 'BASIC 9', 'FORM 3', 'GRADE 9', 'JHS3']):
        return ("JHS 3 / Basic 9 — Logic Stage Senior", 4,
                "The student may be preparing for BECE. Use exam-ready, analytical language.")
    if any(x in name for x in ['JHS 2', 'BASIC 8', 'FORM 2', 'GRADE 8', 'JHS2']):
        return ("JHS 2 / Basic 8 — Logic Stage Mid", 3, "")
    if any(x in name for x in ['JHS 1', 'BASIC 7', 'FORM 1', 'GRADE 7', 'JHS1']):
        return ("JHS 1 / Basic 7 — Logic Stage Entry", 3, "")

    # Upper Primary / Basic 4-6
    if any(x in name for x in ['PRIMARY 6', 'BASIC 6', 'GRADE 6']):
        return ("Primary 6 / Basic 6 — Upper Primary", 2, "")
    if any(x in name for x in ['PRIMARY 5', 'BASIC 5', 'GRADE 5']):
        return ("Primary 5 / Basic 5 — Upper Primary", 2, "")
    if any(x in name for x in ['PRIMARY 4', 'BASIC 4', 'GRADE 4']):
        return ("Primary 4 / Basic 4 — Mid Primary", 2, "")

    # Lower Primary
    if any(x in name for x in ['PRIMARY 3', 'BASIC 3', 'GRADE 3']):
        return ("Primary 3 / Basic 3 — Lower Primary", 1, "")
    if any(x in name for x in ['PRIMARY 2', 'BASIC 2', 'GRADE 2', 'PRIMARY 1', 'BASIC 1', 'GRADE 1']):
        return ("Primary 1-2 / Basic 1-2 — Foundation", 1, "")

    # Fallback — just return the raw name
    return (class_name, 3, "")


def _get_complexity_instruction(level):
    """Return sentence complexity and vocabulary guidance based on level 1-6."""
    guides = {
        1: "Use very short, simple sentences (5-8 words). Concrete nouns only. Avoid abstract ideas. Use pictures and physical examples in your descriptions.",
        2: "Use short to medium sentences (8-12 words). Mostly concrete examples. Introduce ONE new concept at a time. Use 'because', 'so that', 'for example' to build logic.",
        3: "Use medium sentences (10-15 words). Balance concrete and abstract. Use compound sentences. Introduce academic vocabulary with immediate plain-English definitions.",
        4: "Use medium-complex sentences. Blend concrete and abstract reasoning. Use academic language naturally. Introduce subject-specific terminology with brief explanations.",
        5: "Use complex, compound sentences. High use of abstract nouns and academic verbs (analyse, synthesise, evaluate). Introduce discipline vocabulary without always defining it.",
        6: "Use sophisticated, analytical prose. Assume strong academic vocabulary. Use critical thinking frameworks. Challenge with 'Analyse X', 'Evaluate the evidence for Y', 'Compare and contrast'.",
    }
    return guides.get(level, guides[3])


def _get_academic_performance_level(student):
    """
    Query recent grades to assess academic performance level.
    Returns (label, numeric_avg, guidance_note).
    """
    try:
        from students.models import Grade
        from academics.models import AcademicYear
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return ("Unknown", None, "")

        recent_grades = Grade.objects.filter(
            student=student,
            academic_year=current_year
        ).values_list('total_score', flat=True)[:10]

        if not recent_grades:
            return ("No recent grades", None, "")

        avg = float(sum(recent_grades) / len(recent_grades))

        if avg >= 80:
            return ("High Achiever", avg,
                    "Student is a HIGH achiever. Push them with advanced vocabulary, challenging follow-up questions, and 'Power Word' introductions.")
        elif avg >= 65:
            return ("Above Average", avg,
                    "Student is ABOVE AVERAGE. Balance accessibility with intellectual stretch. Introduce one advanced concept per exchange.")
        elif avg >= 50:
            return ("Average", avg,
                    "Student performs at AVERAGE level. Use clear foundations, then build upward. Check for understanding frequently.")
        else:
            return ("Needs Support", avg,
                    "Student may need extra support. Be extra patient, use more analogies, break down every step, and celebrate small wins loudly.")
    except Exception:
        return ("Unknown", None, "")


def _get_cultural_context(student):
    """
    Build a cultural reference frame from the student's region and city.
    Returns a string of relevant local examples to use as teaching anchors.
    """
    region = (student.region or '').lower()
    city = (student.city or '').lower()
    location = f"{city} {region}".strip()

    # Ghana-specific cultural reference frames
    contexts = []

    if any(x in location for x in ['accra', 'greater accra', 'tema']):
        contexts = [
            "Use Accra traffic (e.g., Kwame Nkrumah Circle) to explain bottlenecks, flow, and efficiency.",
            "Use Makola Market for supply, demand, and trade concepts.",
            "Use Flagstaff House / Jubilee House for government and power.",
            "Use Accra Mall or the Accra skyline for modern development topics.",
            "Affirm with 'Chale' or 'Ayekoo!' naturally in conversation.",
        ]
    elif any(x in location for x in ['kumasi', 'ashanti', 'asante']):
        contexts = [
            "Use Kejetia Market to explain economic concepts like supply and demand.",
            "Use Kente weaving patterns to explain sequences, algorithms, or structure.",
            "Use the Asantehene and Manhyia Palace for history and governance topics.",
            "Use cocoa farming to explain biology, chemistry, or economics.",
            "Affirm with 'Ayekoo!' or 'Charlie, you dey!' naturally.",
        ]
    elif any(x in location for x in ['tamale', 'northern', 'dagbon']):
        contexts = [
            "Use Tamale's dry season/wet season cycle for biology and climate topics.",
            "Use Bolgatanga Market for economics and trade concepts.",
            "Use guinea corn farming and irrigation to explain biology or agriculture.",
            "Reference the Overlord of Dagbon for history and governance topics.",
        ]
    elif any(x in location for x in ['takoradi', 'western', 'sekondi']):
        contexts = [
            "Use Ghana's oil and gas industry (Jubilee Field) for energy and economics topics.",
            "Use cocoa and timber production for biology and economics.",
            "Use Cape Three Points lighthouse for navigation and direction concepts.",
        ]
    elif any(x in location for x in ['ho', 'volta', 'ewe']):
        contexts = [
            "Use Lake Volta (the world's largest artificial lake) for geography and engineering topics.",
            "Use Akosombo Dam for electricity, energy, and engineering concepts.",
            "Use kente from Kpetoe for art and culture references.",
        ]
    elif any(x in location for x in ['cape coast', 'central']):
        contexts = [
            "Use Cape Coast Castle for history topics.",
            "Use the University of Cape Coast (UCC) as an aspirational reference.",
            "Use fishing and the Atlantic Ocean for science and economics topics.",
        ]
    elif any(x in location for x in ['sunyani', 'brong', 'bono']):
        contexts = [
            "Use cocoa farming and the agriculture sector for science and economics.",
            "Use the Bono region's forests for environmental science topics.",
        ]

    # Fallbacks for non-Ghana or unknown locations
    if not contexts:
        if any(x in location for x in ['london', 'uk', 'england']):
            contexts = [
                "Use the London Underground (Tube) map for network/graph topics.",
                "Use Premier League football statistics for data and math topics.",
            ]
        elif any(x in location for x in ['nairobi', 'kenya']):
            contexts = [
                "Use the Nairobi matatu culture for flow and efficiency topics.",
                "Use the Maasai Mara for biology and ecology topics.",
            ]
        else:
            # Generic
            contexts = [
                "Use universally relatable references: football, cooking, building construction, farming.",
            ]

    return contexts


def _get_interest_anchors(interests):
    """Convert student interests into teaching metaphor suggestions."""
    if not interests:
        return []

    anchors = []
    interest_map = {
        'football': "Use football tactics, player stats, and match strategies as analogies for math, logic, and strategy.",
        'soccer': "Use football concepts as analogies for math, logic, and teamwork.",
        'music': "Use musical rhythm and structure to explain patterns, sequences, and fractions.",
        'highlife': "Use Highlife rhythm and song structure to explain patterns and sequences.",
        'afrobeats': "Use Afrobeats production and rhythm to explain waves, frequencies, and math patterns.",
        'technology': "Freely use technology metaphors: coding logic, circuits, app development.",
        'coding': "Use programming concepts (loops, functions, variables) as cross-subject analogies.",
        'science': "Lean into scientific curiosity — frame everything as an experiment or discovery.",
        'art': "Use visual art and composition to explain geometry, proportions, and colour theory (light).",
        'cooking': "Use cooking recipes to explain sequences, ratios, chemistry reactions.",
        'farming': "Use farming cycles, soil chemistry, and weather for biology, chemistry, and geography.",
        'fashion': "Use fabric, patterns, and design for geometry, measurement, and art topics.",
        'gaming': "Use video game mechanics (levels, scores, strategy) to explain math and logic.",
        'dance': "Use dance rhythm and choreography to explain patterns and sequences.",
        'reading': "Link topics to books, stories, and narratives the student might relate to.",
        'history': "Draw connections between current topics and historical events the student enjoys.",
    }

    for interest in (interests if isinstance(interests, list) else []):
        key = interest.strip().lower()
        for keyword, anchor in interest_map.items():
            if keyword in key:
                anchors.append(anchor)
                break
        else:
            # Generic anchor for unrecognised interest
            anchors.append(f"When possible, connect topics to the student's interest in {interest}.")

    return anchors


def _build_student_context(student):
    """
    Build a rich Aura Linguistic Profile for this student.
    This is injected into the Realtime API system instructions to prime
    Aura's vocabulary, cultural references, and pedagogical approach.
    """
    lines = []

    student_name = student.user.get_full_name() or student.user.username

    # ── 1. Learner Identity ──────────────────────────────────────────
    lines.append(f"STUDENT: {student_name}")

    # ── 2. Class / Cognitive Stage ───────────────────────────────────
    if student.current_class:
        stage_label, complexity_level, exam_note = _map_class_to_cognitive_stage(student.current_class.name)
        lines.append(f"CLASS: {student.current_class.name} — {stage_label}")
        if exam_note:
            lines.append(f"EXAM CONTEXT: {exam_note}")
    else:
        complexity_level = 3

    # ── 3. Curriculum ────────────────────────────────────────────────
    if student.curriculum:
        lines.append(f"CURRICULUM: {student.curriculum}")

    # ── 4. Academic Performance (from grades) ────────────────────────
    perf_label, perf_avg, perf_guidance = _get_academic_performance_level(student)
    if perf_avg is not None:
        lines.append(f"ACADEMIC LEVEL: {perf_label} (avg {perf_avg:.1f}%)")
    if perf_guidance:
        lines.append(f"PERFORMANCE GUIDANCE: {perf_guidance}")

    # ── 5. Language & Accent ─────────────────────────────────────────
    lang = getattr(student, 'preferred_language', 'english')
    lang_display = dict([
        ('english', 'English'), ('twi', 'Twi/Akan'), ('hausa', 'Hausa'),
        ('ewe', 'Ewe'), ('ga', 'Ga'), ('dagbani', 'Dagbani'),
        ('french', 'French'), ('other', 'Other'),
    ]).get(lang, 'English')
    lines.append(f"LANGUAGE: {lang_display} — Speak West African Professional English: clear, warm, rhythmic. Pronounce technical terms slowly.")

    # ── 6. Subjects ──────────────────────────────────────────────────
    if student.current_class:
        try:
            from academics.models import ClassSubject
            subjects = list(ClassSubject.objects.filter(
                class_name=student.current_class
            ).select_related('subject').values_list('subject__name', flat=True))
            if subjects:
                lines.append(f"SUBJECTS: {', '.join(subjects)}")
        except Exception:
            pass

    # ── 7. Cultural / Geographic Context ────────────────────────────
    cultural_refs = _get_cultural_context(student)
    if cultural_refs:
        location = ' / '.join(filter(None, [student.city, student.region]))
        if location:
            lines.append(f"LOCATION: {location}")
        lines.append("CULTURAL REFERENCE FRAMES (use these as teaching anchors):")
        for ref in cultural_refs[:4]:  # cap to 4 to keep prompt lean
            lines.append(f"  • {ref}")

    # ── 8. Interest-Based Metaphors ──────────────────────────────────
    interest_anchors = _get_interest_anchors(student.interests)
    if interest_anchors:
        interests_str = ', '.join(student.interests[:5]) if isinstance(student.interests, list) else ''
        if interests_str:
            lines.append(f"INTERESTS: {interests_str}")
        lines.append("INTEREST ANCHORS (connect topics to these):")
        for anchor in interest_anchors[:3]:
            lines.append(f"  • {anchor}")

    # ── 9. Sentence Complexity Calibration ──────────────────────────
    lines.append(f"SENTENCE COMPLEXITY: {_get_complexity_instruction(complexity_level)}")

    # ── 10. Vygotsky ZPD Rule ────────────────────────────────────────
    lines.append(
        "VYGOTSKY ZPD RULE: Always speak ONE intellectual level above the student's apparent current mastery — "
        "stretch them upward without losing them. If they speak in simple sentences, use clear but slightly "
        "more complex sentences. If they use academic vocabulary, match and gently exceed their level."
    )

    # ── 11. Adaptive Vocabulary Protocol ────────────────────────────
    lines.append(
        "ADAPTIVE VOCABULARY PROTOCOL: Every 3 exchanges, silently assess the student's word complexity. "
        "If they struggle (very short answers, 'I don't understand', repetition) → simplify your next responses by 20%. "
        "If they excel (complex sentences, subject-specific terms, follow-up questions) → introduce 2 'Power Words' "
        "relevant to the topic with brief natural definitions. "
        "NEVER use jargon without an immediate plain-language definition in 10 words or fewer."
    )

    # ── 12. Engagement & Affirmation Style ──────────────────────────
    lines.append(
        "ENGAGEMENT STYLE: Be warm, enthusiastic, and encouraging. Celebrate correct answers genuinely. "
        "Use Ghanaian affirmations naturally when appropriate: 'Ayekoo!', 'Chale, that's sharp!', "
        "'You're thinking like a scholar!', 'Chale, you're on fire!', 'Ehen, that's it!', 'Exactly — that's the logic!'. "
        "Never be condescending. Frame mistakes as learning steps: 'Good try — let's refine it.'"
    )

    # ── 13. Whiteboard Rule ──────────────────────────────────────────
    lines.append(
        "WHITEBOARD RULE: When explaining a formula, equation, diagram, or step-by-step process, "
        "prefix it with [WHITEBOARD] on its own line, followed by the content. Use this for math, science formulas, "
        "and any structured multi-step explanation."
    )

    # ── 14. Teacher Notes for Aura ───────────────────────────────────
    aura_notes = getattr(student, 'aura_notes', '').strip()
    if aura_notes:
        lines.append(f"TEACHER NOTES: {aura_notes}")

    return "\n".join(lines)


@login_required
def aura_voice_view(request):
    """Render the voice interface — students only."""
    if request.user.user_type != 'student':
        messages.error(request, "Aura Voice is only available to students.")
        return redirect('dashboard')
    
    return render(request, 'students/aura_voice.html')


@login_required
def voice_board_generate(request):
    """
    POST { "user_text": "...", "aura_text": "..." }
    Calls gpt-4o-mini to decide whether a Mermaid diagram would help,
    and if so returns { "diagram": "mermaid_code", "title": "..." }.
    Returns { "diagram": null } if no diagram is needed.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)
    if _rate_limit(request, 'voice_board_generate', limit=18, window_seconds=60):
        return JsonResponse({'error': 'Too many requests'}, status=429)

    try:
        body = json.loads(request.body.decode('utf-8'))
        user_text = (body.get('user_text') or '').strip()[:600]
        aura_text = (body.get('aura_text') or '').strip()[:1200]
    except Exception:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not (user_text or aura_text):
        return JsonResponse({'diagram': None})

    api_key = get_openai_api_key()
    if not api_key:
        return JsonResponse({'diagram': None})

    system_prompt = (
        "You are a diagram generator for an AI tutoring assistant called Aura. "
        "Given a short tutor-student conversation, decide if a visual diagram would SIGNIFICANTLY "
        "help understanding. Only generate a diagram if it genuinely adds value — don't create one "
        "for casual chitchat, greetings, or simple factual answers.\n\n"
        "If a diagram is warranted, respond with ONLY a raw JSON object (no markdown fences, no prose):\n"
        '{"title": "Diagram title (max 40 chars)", "diagram": "<mermaid code here>"}\n\n'
        "STRICT MERMAID RULES:\n"
        "- Only use these diagram types: flowchart TD, sequenceDiagram, mindmap, timeline, classDiagram\n"
        "- Keep diagrams concise: ≤12 nodes or steps\n"
        "- flowchart: use --> for arrows, wrap labels with spaces in quotes e.g. A[\"Label\"]\n"
        "- mindmap: root title on first line, indent children with spaces (NOT tabs)\n"
        "- Do NOT use: xychart, sankey, pie, gitGraph, quadrantChart, erDiagram, gantt\n"
        "- Do NOT include ```mermaid fences — raw code only\n\n"
        "If NO diagram is needed, respond with ONLY: {\"title\": null, \"diagram\": null}"
    )

    user_prompt = f"Student said: {user_text}\n\nAura (tutor) replied: {aura_text}"

    try:
        import requests as http_requests
        resp = http_requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.3,
                'max_tokens': 600,
                'response_format': {'type': 'json_object'},
            },
            timeout=20,
        )
        if resp.status_code != 200:
            logger.warning('voice_board_generate API error %s', resp.status_code)
            return JsonResponse({'diagram': None})

        content = resp.json()['choices'][0]['message']['content']
        data = json.loads(content)
        diagram = (data.get('diagram') or '').strip()
        title = (data.get('title') or 'Visualization').strip()
        if not diagram or diagram.lower() == 'null':
            return JsonResponse({'diagram': None})
        # Strip any accidental fences
        diagram = diagram.strip('`').strip()
        if diagram.lower().startswith('mermaid'):
            diagram = diagram[7:].strip()
        return JsonResponse({'diagram': diagram, 'title': title})
    except Exception as e:
        logger.warning('voice_board_generate error: %s', e)
        return JsonResponse({'diagram': None})


@login_required
def create_realtime_session(request):
    """
    Create an ephemeral token for OpenAI Realtime API (WebRTC).
    Frontend uses this to establish a WebRTC peer connection directly to OpenAI.
    Requires authenticated student user.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    if request.user.user_type != 'student':
        return JsonResponse({"error": "Unauthorized"}, status=403)
    if _rate_limit(request, 'create_realtime_session', limit=10, window_seconds=60):
        return JsonResponse({"error": "Too many requests"}, status=429)
    
    try:
        data = json.loads(request.body) if request.body else {}
        voice = data.get('voice', 'coral')
        model = data.get('model', DEFAULT_REALTIME_MODEL)
        
        if model not in ALLOWED_REALTIME_MODELS:
            model = DEFAULT_REALTIME_MODEL
        
        # Migrate legacy model names to GA equivalents
        model = MODEL_MIGRATION_MAP.get(model, model)
        
        # Build context-aware instructions for this student
        student_context = ""
        system_instructions = ""
        try:
            from students.models import Student
            student = Student.objects.select_related('current_class', 'user').filter(user=request.user).first()
            if student:
                student_context = _build_student_context(student)
        except Exception:
            pass  # gracefully degrade — generic instructions still work

        # Build the full system instructions for the Realtime API
        # Voice-mode rules prepended to the full Aura 2.0 State-Machine prompt
        voice_prefix = (
            "VOICE MODE ADAPTATIONS (strictly apply these on top of all other rules):\n"
            "- This is a VOICE session. Keep EVERY spoken response to 2-3 sentences maximum.\n"
            "- Never read out long lists; speak them as natural sentences and offer to elaborate.\n"
            "- For spoken content, do NOT read out diagram code or token syntax aloud.\n"
            "- You HAVE a live Visualization Board the student can see. Use [WB_DIAGRAM] tokens\n"
            "  whenever a diagram, flowchart, timeline, or mind map would help explain a concept.\n"
            "  Emit the diagram token silently alongside your spoken explanation — keep diagrams brief.\n"
            "  Format: [WB_DIAGRAM: Title]<mermaid code>[/WB_DIAGRAM]\n"
            "  Only use these Mermaid diagram types: flowchart, sequenceDiagram, mindmap, timeline,\n"
            "  classDiagram. Do NOT use xychart, sankey, block, gitGraph, pie, quadrantChart,\n"
            "  or other types — they are not supported and will show an error to the student.\n"
            "- Do NOT emit [POWER_WORDS] tokens in voice mode.\n"
            "- DO emit [LESSON_STATE: X] tokens even in voice mode (they are silent to the student).\n"
            "- Emit [AWARD_XP: N] (N = 5–20) at the END of responses where the student demonstrates\n"
            "  clear understanding, answers a question correctly, or makes meaningful progress.\n"
            "  Only award XP once per response, silently — never read the token aloud.\n"
            "- Speak warmly and naturally — no robotic phrasing.\n"
            "- Pause naturally by ending the response; do not add filler like 'Ok so...' or 'Alright'.\n\n"
        )
        if student:
            try:
                from academics.ai_tutor import get_tutor_system_prompt
                system_instructions = voice_prefix + get_tutor_system_prompt(student)
            except Exception:
                system_instructions = (
                    voice_prefix +
                    "You are Aura, an intelligent AI tutor. Be warm and conversational. "
                    "Never lecture — ask one question per turn and wait for the student's response. "
                    + ("\n\n─── STUDENT PROFILE ───\n" + student_context if student_context else "")
                )

        # Create a TutorSession log row for this voice session
        db_session_id = None
        voice_xp_token = None
        if student:
            try:
                from academics.tutor_models import TutorSession
                _voice_session = TutorSession.objects.create(
                    student=student,
                    title='Voice Session',
                )
                db_session_id = str(_voice_session.id)
                voice_xp_token = _build_voice_xp_token(request.user.id, _voice_session.id)
                cache.set(
                    _voice_active_session_cache_key(request.user.id),
                    db_session_id,
                    VOICE_XP_TOKEN_MAX_AGE_SECONDS,
                )
            except Exception as ex:
                logger.warning('Voice TutorSession create failed: %s', ex)
        else:
            system_instructions = (
                voice_prefix +
                "You are Aura, an intelligent AI tutor. Be warm and conversational. "
                "Never lecture — ask one question per turn and wait for the student's response."
            )
        
        import requests as http_requests
        api_key = get_openai_api_key()
        
        if not api_key:
            return JsonResponse({"error": "OpenAI API key not configured"}, status=500)
        
        response = http_requests.post(
            "https://api.openai.com/v1/realtime/client_secrets",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "session": {
                    "type": "realtime",
                    "model": model,
                    "audio": {
                        "output": {
                            "voice": voice
                        }
                    }
                }
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Realtime session API error {response.status_code}: {response.text[:500]}")
            return JsonResponse({
                "error": "OpenAI session creation failed"
            }, status=502)
        
        session_data = response.json()
        # /v1/realtime/client_secrets returns {value, expires_at, session} at top level
        client_secret = session_data.get("value", "")
        
        if not client_secret:
            # Fallback: try nested client_secret.value format
            client_secret_obj = session_data.get("client_secret", {})
            if isinstance(client_secret_obj, dict):
                client_secret = client_secret_obj.get("value", "")
        
        if not client_secret:
            logger.error(f"Realtime client_secret response missing value: {session_data}")
            return JsonResponse({
                "error": "No client_secret in response",
                "detail": str(session_data)[:300]
            }, status=500)
        
        session_info = session_data.get("session", {})
        return JsonResponse({
            "client_secret": client_secret,
            "model": session_info.get("model", model),
            "voice": voice,
            "student_context": student_context,
            "system_instructions": system_instructions,
            "db_session_id": db_session_id,
            "voice_xp_token": voice_xp_token,
        })
        
    except Exception as e:
        logger.exception("Realtime Session Error")
        return JsonResponse({"error": "Unable to create realtime session"}, status=500)


# ═══════════════════════════════════════════════════════════
# AURA ARENA
# ═══════════════════════════════════════════════════════════

from academics.models import StudyGroupRoom, StudyGroupMessage, StudentXP

@login_required
def aura_arena_view(request):
    if request.user.user_type != 'student':
        messages.error(request, "Only students can enter the Aura Arena.")
        return redirect('dashboard')
    
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        messages.warning(request, "You must be assigned to a class to enter.")
        return redirect('dashboard')

    try:
        room, _ = StudyGroupRoom.objects.get_or_create(
            student_class=student.current_class,
            defaults={'name': f"{student.current_class.name} Arena"}
        )
    except Exception:
        # Table may not exist yet — run migration on-the-fly for this tenant
        from django.core.management import call_command
        from django.db import connection
        try:
            logger.warning(f"StudyGroupRoom table missing for schema {connection.schema_name}. Running migration...")
            call_command('migrate', 'academics', '--database=default', interactive=False)
            room, _ = StudyGroupRoom.objects.get_or_create(
                student_class=student.current_class,
                defaults={'name': f"{student.current_class.name} Arena"}
            )
        except Exception as mig_err:
            logger.error(f"Auto-migration failed: {mig_err}")
            messages.error(request, "Aura Arena is being set up. Please try again in a moment.")
            return redirect('dashboard')

    try:
        xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    except Exception:
        xp_profile = None

    # Class leaderboard — top 10 students in same class by total XP
    try:
        top_students = (
            StudentXP.objects
            .filter(student__current_class=student.current_class)
            .select_related('student__user')
            .order_by('-total_xp')[:10]
        )
    except Exception:
        top_students = []

    context = {
        'room': room,
        'student': student,
        'xp': xp_profile,
        'top_students': top_students,
    }
    return render(request, 'students/aura_arena.html', context)


@login_required
def aura_arena_api(request):
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET' and _rate_limit(request, 'aura_arena_api_get', limit=120, window_seconds=60):
        return JsonResponse({'error': 'Too many requests'}, status=429)
    if request.method == 'POST' and _rate_limit(request, 'aura_arena_api_post', limit=40, window_seconds=60):
        return JsonResponse({'error': 'Too many requests'}, status=429)
        
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        return JsonResponse({'error': 'No class assigned'}, status=400)
        
    room = StudyGroupRoom.objects.filter(student_class=student.current_class).first()
    if not room:
        return JsonResponse({'error': 'No room found'}, status=404)
        
    if request.method == 'GET':
        try:
            last_id = int(request.GET.get('last_id', 0))
        except (TypeError, ValueError):
            last_id = 0
        last_id = max(last_id, 0)
        msgs = StudyGroupMessage.objects.filter(room=room, id__gt=last_id).order_by('created_at')
        
        data = []
        for m in msgs:
            reply_data = None
            if m.reply_to_id:
                rt = m.reply_to
                if rt:
                    reply_data = {
                        'id': rt.id,
                        'sender': rt.sender.get_full_name() if rt.sender else 'Aura',
                        'content': rt.content[:120],
                    }
            data.append({
                'id': m.id,
                'content': m.content,
                'sender': m.sender.get_full_name() if m.sender else 'Aura',
                'is_aura': m.is_aura,
                'is_battle': m.is_battle_question,
                'battle_type': m.battle_type if m.is_battle_question else None,
                'battle_xp': m.battle_xp if m.is_battle_question else None,
                'battle_answered': m.battle_answered,
                'winner': m.battle_winner.get_full_name() if m.battle_winner else None,
                'time': m.created_at.strftime('%H:%M'),
                'is_me': m.sender == request.user if m.sender else False,
                'reply_to': reply_data,
            })

        from academics.gamification_models import StudentXP
        xp_profile = StudentXP.objects.filter(student=student).first()
        xp_snapshot = None
        if xp_profile:
            xp_snapshot = {
                'total_xp': xp_profile.total_xp,
                'level': xp_profile.level,
                'level_progress': xp_profile.level_progress,
                'xp_to_next_level': xp_profile.xp_to_next_level,
            }

        # Live leaderboard — top 10 for this room's class
        from students.models import Student as _Student
        top_raw = (
            StudentXP.objects
            .filter(student__current_class=student.current_class)
            .order_by('-total_xp')
            .select_related('student__user')[:10]
        )
        leaderboard = [
            {
                'name': e.student.user.get_full_name(),
                'initials': (e.student.user.first_name[:1] + e.student.user.last_name[:1]).upper(),
                'total_xp': e.total_xp,
                'streak': e.current_streak,
                'is_me': e.student == student,
            }
            for e in top_raw
        ]

        return JsonResponse({'messages': data, 'xp_snapshot': xp_snapshot, 'leaderboard': leaderboard})

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        raw_content = str(payload.get('content', ''))
        if len(raw_content) > 1000:
            return JsonResponse({'error': 'Message too long (max 1000 characters)'}, status=400)

        content = raw_content.strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
            
        # Bug fix: a battle is only "active" if it is unanswered AND was
        # created within the last 5 minutes — prevents stale DB rows from
        # permanently blocking new games.
        from django.utils import timezone as _tz
        _battle_window = _tz.now() - __import__('datetime').timedelta(minutes=5)
        active_battle = (
            StudyGroupMessage.objects
            .filter(room=room, is_battle_question=True, battle_answered=False,
                    created_at__gte=_battle_window)
            .last()
        )
        stale_battle = (
            StudyGroupMessage.objects
            .filter(room=room, is_battle_question=True, battle_answered=False,
                    created_at__lt=_battle_window)
            .last()
        )
        
        reply_to_id = payload.get('reply_to_id')
        reply_to_obj = None
        if reply_to_id:
            try:
                reply_to_obj = StudyGroupMessage.objects.get(id=int(reply_to_id), room=room)
            except (StudyGroupMessage.DoesNotExist, ValueError, TypeError):
                pass
        
        msg = StudyGroupMessage.objects.create(room=room, sender=request.user, content=content, reply_to=reply_to_obj)
        
        is_winner = False
        xp_earned = 0

        # ── Helper: award XP, check achievements, build snapshot ────────
        def _award_xp_and_snapshot(amount):
            from academics.gamification_models import StudentXP, check_and_unlock_achievements, StudentAchievement
            xp_profile, _ = StudentXP.objects.get_or_create(student=student)
            already_unlocked = set(
                StudentAchievement.objects.filter(student=student)
                .values_list('achievement__slug', flat=True)
            )
            xp_profile.add_xp(amount)
            xp_profile.update_streak()
            check_and_unlock_achievements(student, xp_profile)
            # Detect newly unlocked badges
            newly_unlocked = list(
                StudentAchievement.objects.filter(student=student)
                .exclude(achievement__slug__in=already_unlocked)
                .select_related('achievement')
                .values('achievement__name', 'achievement__icon', 'achievement__xp_reward')
            )
            return {
                'total_xp': xp_profile.total_xp,
                'level': xp_profile.level,
                'level_progress': xp_profile.level_progress,
                'xp_to_next_level': xp_profile.xp_to_next_level,
            }, newly_unlocked

        # ── Check active battle answer ──────────────────────────────────
        # Skip answer-check if the message itself is an @aura command so
        # that typing "@aura true or false" never accidentally wins a T/F battle.
        _is_aura_cmd = bool(re.search(r'@aura\s+\w', content, re.IGNORECASE))
        if active_battle and active_battle.battle_answer and not _is_aura_cmd:
            ans = (active_battle.battle_answer or '').strip().lower()
            msg_lower = content.lower()

            def _norm(txt):
                txt = str(txt or '').lower().strip()
                txt = re.sub(r'[^a-z0-9\.\-\s]', '', txt)
                txt = re.sub(r'\s+', ' ', txt)
                return txt

            ans_norm = _norm(ans)
            msg_norm = _norm(content)
            matched = False

            if active_battle.battle_type == 'truefalse':
                # Accept only "true" or "false" vote; any word match counts
                if ans_norm in msg_norm and ans_norm in ('true', 'false'):
                    matched = True
            elif active_battle.battle_type == 'math':
                # Exact number match — strip spaces and compare
                nums = re.findall(r'-?\d+\.?\d*', msg_lower)
                matched = any(_norm(n) == ans_norm for n in nums)
            else:
                # battle / riddle / scrabble — keyword must appear in message
                matched = ans_norm in msg_norm if ans_norm else False

            if matched:
                active_battle.battle_answered = True
                active_battle.battle_winner = request.user
                active_battle.save()

                award = active_battle.battle_xp
                snapshot, new_achievements = _award_xp_and_snapshot(award)
                is_winner = True
                xp_earned = award

                type_labels = {
                    'battle':    '⚡ Correct!',
                    'riddle':    '🧩 Solved!',
                    'math':      '🔢 Correct!',
                    'scrabble':  '🔤 Great word!',
                    'spell':     '🔤 Great word!',
                    'truefalse': '✅ Correct!',
                }
                label = type_labels.get(active_battle.battle_type, '⚡ Correct!')
                StudyGroupMessage.objects.create(
                    room=room,
                    is_aura=True,
                    content=(
                        f"{label} **{request.user.get_full_name()}** wins and earns +{award} XP! "
                        f"The answer was: **{active_battle.battle_answer.title()}**."
                    )
                )
                return JsonResponse({
                    'status': 'success',
                    'xp_earned': xp_earned,
                    'is_winner': True,
                    'xp_snapshot': snapshot,
                    'new_achievements': new_achievements,
                })

            # Give immediate feedback when an answer attempt is wrong so users
            # know the message was processed and the battle is still active.
            feedback_map = {
                'truefalse': "Not quite. For this challenge, type exactly: true or false.",
                'math': "Not quite. Enter only the final number (no extra words).",
                'battle': "Not quite. Try again — check the key term in the question.",
                'riddle': "Not quite. Try again — focus on the clue wording.",
                'scrabble': "Not quite. Try again — build the correct word from the tiles.",
                'spell': "Not quite. Try again — build the correct word from the tiles.",
            }
            return JsonResponse({
                'status': 'attempted',
                'xp_earned': 0,
                'is_winner': False,
                'battle_active': True,
                'battle_type': active_battle.battle_type,
                'feedback': feedback_map.get(active_battle.battle_type, "Not correct yet — try again."),
                'new_achievements': [],
            })

        # If user answers but the unresolved challenge has expired, close it
        # explicitly so the client does not appear stuck.
        if stale_battle and not _is_aura_cmd:
            stale_battle.battle_answered = True
            stale_battle.save(update_fields=['battle_answered'])
            StudyGroupMessage.objects.create(
                room=room,
                is_aura=True,
                content="⌛ That challenge expired. Start a fresh one with @aura battle, @aura riddle, @aura math, @aura scrabble, or @aura true or false."
            )
            return JsonResponse({
                'status': 'expired',
                'xp_earned': 0,
                'is_winner': False,
                'battle_active': False,
                'feedback': 'Challenge expired. Start a new one.',
                'new_achievements': [],
            })

        # ── Helper: build GPT client ────────────────────────────────────
        def _gpt_client():
            api_key = get_openai_api_key()
            if not api_key:
                return None
            import openai
            return openai.OpenAI(api_key=api_key)

        def _class_ctx():
            curriculum_note = f" ({student.curriculum} curriculum)" if getattr(student, 'curriculum', None) else ""
            region = getattr(student, 'region', 'West Africa') or 'West Africa'
            return student.current_class.name + curriculum_note, region

        cmd = content.lower()

        # ── Cooldown: prevent game-command spam ─────────────────────────
        COOLDOWN_SECS = 90
        _is_game_cmd = bool(re.search(r'@aura\s+(battle|riddle|math|scrabble|true|tf\b)', cmd))
        if _is_game_cmd and not active_battle:
            last_q = (
                StudyGroupMessage.objects
                .filter(room=room, is_battle_question=True)
                .order_by('-created_at').first()
            )
            if last_q:
                elapsed = (_tz.now() - last_q.created_at).total_seconds()
                if elapsed < COOLDOWN_SECS:
                    wait = int(COOLDOWN_SECS - elapsed)
                    StudyGroupMessage.objects.create(
                        room=room, is_aura=True,
                        content=f"⏳ Hold on! Next game starts in **{wait}s**. (Cooldown: {COOLDOWN_SECS}s between games)"
                    )
                    return JsonResponse({'status': 'cooldown', 'xp_earned': 0, 'is_winner': False, 'new_achievements': []})

        # ── @aura skip ──────────────────────────────────────────────
        if re.search(r'@aura\s+skip', cmd):
            # Find any unanswered battle (no time limit) and mark it closed
            stale = StudyGroupMessage.objects.filter(
                room=room, is_battle_question=True, battle_answered=False
            ).last()
            if stale:
                stale.battle_answered = True
                stale.save()
                StudyGroupMessage.objects.create(
                    room=room, is_aura=True,
                    content="⏭️ Challenge skipped. Start a new one whenever you're ready!"
                )
            else:
                StudyGroupMessage.objects.create(
                    room=room, is_aura=True,
                    content="ℹ️ No active challenge to skip."
                )

        # ── @aura hint ──────────────────────────────────────────────
        elif re.search(r'@aura\s+hint', cmd):
            if not active_battle:
                StudyGroupMessage.objects.create(
                    room=room, is_aura=True,
                    content="💡 No active challenge right now. Start one with `@aura battle`, `@aura riddle`, `@aura math`, `@aura scrabble`, or `@aura true or false`."
                )
            else:
                client = _gpt_client()
                if client:
                    try:
                        hint_prompt = (
                            f"A student is stuck on this question/challenge: '{active_battle.content}'. "
                            f"The correct answer is '{active_battle.battle_answer}' but DO NOT reveal it. "
                            "Give a single helpful hint in one sentence that nudges them in the right direction without giving away the answer."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': hint_prompt}],
                            temperature=0.5,
                            max_tokens=80
                        )
                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True,
                            content=f"💡 **Hint:** {res.choices[0].message.content.strip()}"
                        )
                    except Exception as e:
                        logger.error(f"Aura Hint Error: {e}")

        # ── @aura battle ───────────────────────────────────────────────
        elif re.search(r'@aura\s+battle', cmd):
            if active_battle:
                StudyGroupMessage.objects.create(
                    room=room, is_aura=True,
                    content="⏳ A challenge is already active! Answer it first, or type `@aura skip` to skip it."
                )
            else:
                client = _gpt_client()
                if not client:
                    StudyGroupMessage.objects.create(room=room, is_aura=True,
                        content="⚠️ Aura-T isn't connected right now. Ask your teacher to set up the AI key.")
                else:
                    try:
                        class_name, region = _class_ctx()
                        prompt = (
                            f"You are a strict JSON generator. Generate a short educational trivia question "
                            f"for a {class_name} class. Use culturally relevant examples where appropriate "
                            f"(region: {region}). "
                            "Return ONLY a valid JSON object with keys 'question' and 'answer'. No markdown, no other text."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': prompt}],
                            temperature=0.7, max_tokens=150
                        )
                        raw = res.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                        q = json.loads(raw)
                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True, is_battle_question=True,
                            battle_type='battle', battle_xp=20,
                            battle_answer=q.get('answer', ''),
                            content=f"🔴 **AURA BATTLE!** First to answer wins **+20 XP!**\n\n**Question:** {q.get('question', '')}"
                        )
                    except Exception as e:
                        logger.exception(f"Aura Battle Error: {e}")
                        StudyGroupMessage.objects.create(room=room, is_aura=True,
                            content="⚠️ Couldn't generate a question right now. Try again in a moment!")

        # ── @aura riddle ───────────────────────────────────────────────
        elif re.search(r'@aura\s+riddle', cmd):
            if active_battle:
                StudyGroupMessage.objects.create(room=room, is_aura=True,
                    content="⏳ There's already a challenge active! Answer it first, or type `@aura skip`.")
            else:
                client = _gpt_client()
                if not client:
                    StudyGroupMessage.objects.create(room=room, is_aura=True,
                        content="⚠️ Aura-T isn't connected right now.")
                else:
                    try:
                        class_name, region = _class_ctx()
                        prompt = (
                            f"Generate a short, fun riddle suitable for a {class_name} class. "
                            "Keep it school-appropriate and solvable. "
                            "Return ONLY a valid JSON object with keys 'riddle' and 'answer'. No markdown, no other text."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': prompt}],
                            temperature=0.8, max_tokens=150
                        )
                        raw = res.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                        q = json.loads(raw)
                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True, is_battle_question=True,
                            battle_type='riddle', battle_xp=15,
                            battle_answer=q.get('answer', ''),
                            content=f"🧩 **RIDDLE TIME!** First to crack it wins **+15 XP!**\n\n*{q.get('riddle', '')}*"
                        )
                    except Exception as e:
                        logger.exception(f"Aura Riddle Error: {e}")
                        StudyGroupMessage.objects.create(room=room, is_aura=True,
                            content="⚠️ Couldn't generate a riddle right now. Try again!")

        # ── @aura math ─────────────────────────────────────────────────
        elif re.search(r'@aura\s+math', cmd):
            if active_battle:
                StudyGroupMessage.objects.create(room=room, is_aura=True,
                    content="⏳ There's already a challenge active! Answer it first, or type `@aura skip`.")
            else:
                client = _gpt_client()
                if not client:
                    StudyGroupMessage.objects.create(room=room, is_aura=True,
                        content="⚠️ Aura-T isn't connected right now.")
                else:
                    try:
                        class_name, _ = _class_ctx()
                        prompt = (
                            f"Generate a mental arithmetic question suitable for a {class_name} class. "
                            "The answer must be a single number (integer or simple decimal). "
                            "Return ONLY a valid JSON object with keys 'question' and 'answer' (answer as a string number). "
                            "No markdown, no other text."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': prompt}],
                            temperature=0.6, max_tokens=100
                        )
                        raw = res.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                        q = json.loads(raw)
                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True, is_battle_question=True,
                            battle_type='math', battle_xp=10,
                            battle_answer=str(q.get('answer', '')).strip(),
                            content=f"🔢 **MATH CHALLENGE!** First correct answer wins **+10 XP!**\n\n**{q.get('question', '')}**"
                        )
                    except Exception as e:
                        logger.exception(f"Aura Math Error: {e}")
                        StudyGroupMessage.objects.create(room=room, is_aura=True,
                            content="⚠️ Couldn't generate a math problem right now. Try again!")

        # ── @aura scrabble ─────────────────────────────────────────────
        elif re.search(r'@aura\s+scrabble', cmd):
            if active_battle:
                StudyGroupMessage.objects.create(room=room, is_aura=True,
                    content="⏳ There's already a challenge active! Answer it first, or type `@aura skip`.")
            else:
                client = _gpt_client()
                if not client:
                    StudyGroupMessage.objects.create(room=room, is_aura=True,
                        content="⚠️ Aura-T isn't connected right now.")
                else:
                    try:
                        class_name, _ = _class_ctx()
                        prompt = (
                            f"Generate a Scrabble-style word challenge for a {class_name} class. "
                            "Pick one school-appropriate vocabulary word (3-10 letters, alphabetic only), and provide a short clue without revealing the word. "
                            "Return ONLY a valid JSON object with keys 'clue' and 'word'. No markdown, no other text."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': prompt}],
                            temperature=0.7, max_tokens=120
                        )
                        raw = res.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                        q = json.loads(raw)
                        answer_word = re.sub(r'[^a-z]', '', str(q.get('word', '')).lower())
                        if len(answer_word) < 3:
                            raise ValueError('Invalid scrabble word generated')

                        tiles = list(answer_word)
                        random.shuffle(tiles)
                        # Avoid showing tiles in original order for fairness.
                        if ''.join(tiles) == answer_word and len(tiles) > 1:
                            tiles = tiles[1:] + tiles[:1]
                        tiles_display = ' '.join(tiles)

                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True, is_battle_question=True,
                            battle_type='scrabble', battle_xp=15,
                            battle_answer=answer_word,
                            content=(
                                "🔤 **SCRABBLE ROUND!** Unscramble the tiles — first correct word wins **+15 XP!**\n\n"
                                f"*Clue:* {q.get('clue', '')}\n\n"
                                f"**Tiles:** `{tiles_display}`"
                            )
                        )
                    except Exception as e:
                        logger.exception(f"Aura Scrabble Error: {e}")
                        StudyGroupMessage.objects.create(room=room, is_aura=True,
                            content="⚠️ Couldn't generate a scrabble challenge right now. Try again!")

        # ── @aura true or false  (also: @aura tf / @aura t/f) ─────────
        elif re.search(r'@aura\s+(true\s*(or|\/)\s*false|tf\b)', cmd):
            if active_battle:
                StudyGroupMessage.objects.create(room=room, is_aura=True,
                    content="⏳ There's already a challenge active! Answer it first, or type `@aura skip`.")
            else:
                client = _gpt_client()
                if not client:
                    StudyGroupMessage.objects.create(room=room, is_aura=True,
                        content="⚠️ Aura-T isn't connected right now.")
                else:
                    try:
                        class_name, region = _class_ctx()
                        prompt = (
                            f"Generate a true-or-false educational statement for a {class_name} class "
                            f"(region: {region}). Make it thought-provoking but not too hard. "
                            "Return ONLY a valid JSON object with keys 'statement' and 'answer' "
                            "where answer is exactly 'true' or 'false'. No markdown, no other text."
                        )
                        res = client.chat.completions.create(
                            model='gpt-4o-mini',
                            messages=[{'role': 'user', 'content': prompt}],
                            temperature=0.6, max_tokens=120
                        )
                        raw = res.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                        q = json.loads(raw)
                        ans = q.get('answer', '').lower().strip()
                        StudyGroupMessage.objects.create(
                            room=room, is_aura=True, is_battle_question=True,
                            battle_type='truefalse', battle_xp=5,
                            battle_answer=ans,
                            content=(
                                f"❓ **TRUE OR FALSE?** Everyone earns **+5 XP** for the correct answer!\n\n"
                                f"*{q.get('statement', '')}*\n\nType `true` or `false`."
                            )
                        )
                    except Exception as e:
                        logger.exception(f"Aura TrueFalse Error: {e}")
                        StudyGroupMessage.objects.create(room=room, is_aura=True,
                            content="⚠️ Couldn't generate a T/F question right now. Try again!")

        # ── @aura (general AI tutor) ───────────────────────────────────
        # Only fires if NO other @aura sub-command matched above
        elif re.search(r'@aura', cmd) and not is_winner:
            client = _gpt_client()
            if client:
                user_msg = re.sub(r'@aura', '', content, flags=re.IGNORECASE).strip()
                try:
                    student_profile = _build_student_context(student)
                    system_prompt = (
                        f"You are Aura-T, a helpful AI tutor. {student_profile}\n"
                        "Do NOT use headings, phases, or labels like 'Phase A', 'Hook', or 'Nugget'. "
                        "Use 'tiny scaffolds' (very short, single-step conversational hints). "
                        "Keep answers fun, extremely concise, and under 3 sentences."
                    )
                    res = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_msg}
                        ],
                        temperature=0.7,
                        max_tokens=200
                    )
                    StudyGroupMessage.objects.create(
                        room=room, is_aura=True,
                        content=res.choices[0].message.content.strip()
                    )
                except Exception as e:
                    logger.error(f"Aura LLM Error: {e}")

        return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': is_winner, 'new_achievements': []})


    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ─── Voice XP Award ─────────────────────────────────────────────────────────
@login_required
def voice_award_xp(request):
    """
    POST endpoint: award XP earned during an Aura Voice session.
    Called by the frontend when it detects a [AWARD_XP: N] token.

    Expected JSON:  { "amount": <int> }
    Returns:        { "xp_earned": N, "total_xp": T, "level": L }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)
    if _rate_limit(request, 'voice_award_xp', limit=45, window_seconds=60):
        return JsonResponse({'error': 'Too many requests'}, status=429)
    try:
        body = json.loads(request.body.decode('utf-8'))
        amount = int(body.get('amount', 0))
        session_id = str(body.get('session_id') or '').strip()
        xp_token = str(body.get('voice_xp_token') or '').strip()
    except (ValueError, TypeError, Exception):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not session_id or not xp_token:
        logger.warning('voice_xp_denied reason=missing_proof uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Missing session proof'}, status=400)

    try:
        token_payload = signing.loads(
            xp_token,
            salt=VOICE_XP_TOKEN_SALT,
            max_age=VOICE_XP_TOKEN_MAX_AGE_SECONDS,
        )
    except signing.SignatureExpired:
        logger.warning('voice_xp_denied reason=expired_token uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Voice token expired'}, status=403)
    except signing.BadSignature:
        logger.warning('voice_xp_denied reason=bad_token uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Invalid voice token'}, status=403)

    if str(token_payload.get('uid')) != str(request.user.id) or str(token_payload.get('sid')) != session_id:
        logger.warning('voice_xp_denied reason=token_mismatch uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Voice token mismatch'}, status=403)

    active_sid = str(cache.get(_voice_active_session_cache_key(request.user.id)) or '')
    if not active_sid or active_sid != session_id:
        logger.warning('voice_xp_denied reason=inactive_session uid=%s sid=%s active=%s', request.user.id, session_id, active_sid)
        return JsonResponse({'error': 'Voice session is no longer active'}, status=403)

    if cache.get(_voice_ended_session_cache_key(request.user.id, session_id)):
        logger.warning('voice_xp_denied reason=ended_session uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Voice session has ended'}, status=403)

    # Clamp to reasonable per-turn bounds
    amount = max(1, min(amount, 50))

    try:
        from students.models import Student
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        logger.warning('voice_xp_denied reason=no_student uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Student profile not found'}, status=404)

    try:
        from academics.tutor_models import TutorSession
        # Ensure XP can only be awarded for the student's own live voice session.
        TutorSession.objects.get(id=session_id, student=student)
    except TutorSession.DoesNotExist:
        logger.warning('voice_xp_denied reason=session_not_found uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'Voice session not found'}, status=404)

    schema = connection.tenant.schema_name
    cooldown_key = f"{schema}:voice_xp:last:{request.user.id}:{session_id}"
    if cache.get(cooldown_key):
        logger.info('voice_xp_denied reason=cooldown uid=%s sid=%s', request.user.id, session_id)
        return JsonResponse({'error': 'XP award cooldown active'}, status=429)
    cache.set(cooldown_key, 1, VOICE_XP_MIN_INTERVAL_SECONDS)

    total_key = f"{schema}:voice_xp:sum:{request.user.id}:{session_id}"
    awarded_total = int(cache.get(total_key, 0) or 0)
    if awarded_total >= VOICE_XP_MAX_PER_SESSION:
        logger.info('voice_xp_denied reason=session_cap uid=%s sid=%s total=%s', request.user.id, session_id, awarded_total)
        return JsonResponse({'error': 'Session XP cap reached'}, status=429)
    amount = min(amount, VOICE_XP_MAX_PER_SESSION - awarded_total)
    if amount <= 0:
        logger.info('voice_xp_denied reason=session_cap_zero uid=%s sid=%s total=%s', request.user.id, session_id, awarded_total)
        return JsonResponse({'error': 'Session XP cap reached'}, status=429)

    from academics.gamification_models import StudentXP, check_and_unlock_achievements
    xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    leveled_up = xp_profile.add_xp(amount)
    cache.set(total_key, awarded_total + amount, VOICE_XP_TOKEN_MAX_AGE_SECONDS)
    xp_profile.update_streak()  # keep voice streak in sync with text-chat streak
    check_and_unlock_achievements(student, xp_profile)
    if leveled_up:
        try:
            from announcements.models import Notification
            Notification.objects.create(
                recipient=request.user,
                message=f'⭐ Level Up! You reached Level {xp_profile.level} — your Aura voice sessions are paying off!',
                alert_type='general',
                link='../../students/aura-portfolio/',
            )
        except Exception:
            pass

    return JsonResponse({
        'xp_earned': amount,
        'total_xp': xp_profile.total_xp,
        'level': xp_profile.level,
        'current_streak': xp_profile.current_streak,
    })


@login_required
def voice_end_session(request):
    """Explicitly end a voice session so XP awards can no longer be replayed."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)

    try:
        body = json.loads(request.body.decode('utf-8')) if request.body else {}
        session_id = str(body.get('session_id') or '').strip()
        xp_token = str(body.get('voice_xp_token') or '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not session_id or not xp_token:
        return JsonResponse({'error': 'Missing session proof'}, status=400)

    try:
        token_payload = signing.loads(
            xp_token,
            salt=VOICE_XP_TOKEN_SALT,
            max_age=VOICE_XP_TOKEN_MAX_AGE_SECONDS,
        )
    except signing.SignatureExpired:
        return JsonResponse({'error': 'Voice token expired'}, status=403)
    except signing.BadSignature:
        return JsonResponse({'error': 'Invalid voice token'}, status=403)

    if str(token_payload.get('uid')) != str(request.user.id) or str(token_payload.get('sid')) != session_id:
        return JsonResponse({'error': 'Voice token mismatch'}, status=403)

    active_key = _voice_active_session_cache_key(request.user.id)
    active_sid = str(cache.get(active_key) or '')
    if active_sid == session_id:
        cache.delete(active_key)

    cache.set(
        _voice_ended_session_cache_key(request.user.id, session_id),
        1,
        VOICE_XP_TOKEN_MAX_AGE_SECONDS,
    )

    try:
        from academics.tutor_models import TutorSession
        TutorSession.objects.filter(id=session_id, student__user=request.user, ended_at__isnull=True).update(ended_at=dj_timezone.now())
    except Exception:
        pass

    return JsonResponse({'ok': True})


# ─── Power Word Logger ──────────────────────────────────────────────────────
@login_required
def log_power_words(request):
    """
    POST endpoint: record academic Power Words that Aura taught during a session.

    Expected JSON payload:
        {
            "words":        ["photosynthesis", "stomata", "chlorophyll"],
            "session_type": "voice" | "text",   // optional, default "text"
            "subject":      "Science"            // optional
        }

    Returns:
        { "logged": 3, "words": ["photosynthesis", "stomata", "chlorophyll"] }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Students only'}, status=403)

    if _rate_limit(request, 'log_power_words', limit=24, window_seconds=60):
        return JsonResponse({'error': 'Too many requests'}, status=429)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    words_raw = body.get('words') or []
    session_type = str(body.get('session_type') or 'text').strip().lower()
    if session_type not in ('voice', 'text'):
        session_type = 'text'
    subject = str(body.get('subject') or '').strip()

    if not isinstance(words_raw, list) or not words_raw:
        return JsonResponse({'error': 'words must be a non-empty list'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.select_related('current_class').get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)

    try:
        from academics.tutor_models import PowerWord
        results = PowerWord.log(student, words_raw, session_type=session_type, subject=subject)
    except Exception as e:
        logger.error('log_power_words error: %s', e)
        return JsonResponse({'error': str(e)}, status=500)

    logged_words = [obj.word for obj, _ in results]
    return JsonResponse({'logged': len(results), 'words': logged_words})
