
import os
import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

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
                "error": f"OpenAI API error ({response.status_code})",
                "detail": response.text[:300]
            }, status=response.status_code)
        
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
        })
        
    except Exception as e:
        logger.error(f"Realtime Session Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


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
    
    context = {
        'room': room,
        'student': student,
        'xp': xp_profile
    }
    return render(request, 'students/aura_arena.html', context)


@login_required
def aura_arena_api(request):
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        return JsonResponse({'error': 'No class assigned'}, status=400)
        
    room = StudyGroupRoom.objects.filter(student_class=student.current_class).first()
    if not room:
        return JsonResponse({'error': 'No room found'}, status=404)
        
    if request.method == 'GET':
        last_id = int(request.GET.get('last_id', 0))
        msgs = StudyGroupMessage.objects.filter(room=room, id__gt=last_id).order_by('created_at')
        
        data = []
        for m in msgs:
            data.append({
                'id': m.id,
                'content': m.content,
                'sender': m.sender.get_full_name() if m.sender else 'Aura',
                'is_aura': m.is_aura,
                'is_battle': m.is_battle_question,
                'battle_answered': m.battle_answered,
                'winner': m.battle_winner.get_full_name() if m.battle_winner else None,
                'time': m.created_at.strftime('%H:%M'),
                'is_me': m.sender == request.user if m.sender else False
            })
        return JsonResponse({'messages': data})

    elif request.method == 'POST':
        payload = json.loads(request.body)
        content = payload.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
            
        active_battle = StudyGroupMessage.objects.filter(room=room, is_battle_question=True, battle_answered=False).last()
        
        msg = StudyGroupMessage.objects.create(room=room, sender=request.user, content=content)
        
        is_winner = False
        xp_earned = 0
        
        if active_battle and active_battle.battle_answer:
            ans = active_battle.battle_answer.lower()
            if ans in content.lower():
                active_battle.battle_answered = True
                active_battle.battle_winner = request.user
                active_battle.save()
                
                xp_profile, _ = StudentXP.objects.get_or_create(student=student)
                xp_profile.add_xp(20) 
                is_winner = True
                xp_earned = 20
                
                StudyGroupMessage.objects.create(
                    room=room,
                    is_aura=True,
                    content=f"⚡ Correct! **{request.user.get_full_name()}** wins the battle and earns +20 XP. The answer was: {ans.title()}."
                )
                return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': True})
                
        if "@aura battle" in content.lower() and not active_battle:
            api_key = get_openai_api_key()
            if api_key:
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    
                    curriculum_note = f" ({student.curriculum} curriculum)" if getattr(student, 'curriculum', None) else ""
                    prompt = (
                        f"You are a strict JSON generator. Generate a short educational trivia question for a {student.current_class.name}{curriculum_note} class. "
                        f"Use culturally relevant examples where appropriate (region: {getattr(student, 'region', 'West Africa') or 'West Africa'}). "
                        f"Return ONLY a valid JSON object with keys 'question' and 'answer'. No markdown, no other text."
                    )
                    
                    res = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{'role': 'user', 'content': prompt}],
                        temperature=0.7,
                        max_tokens=150
                    )
                    
                    text_response = res.choices[0].message.content.strip()
                    
                    # Basic cleanup in case it added markdown block
                    text_response = text_response.replace("```json", "").replace("```", "").strip()
                    q_data = json.loads(text_response)

                    StudyGroupMessage.objects.create(
                        room=room,
                        is_aura=True,
                        is_battle_question=True,
                        battle_answer=q_data.get('answer', ''),
                        content=f"🔴 **AURA BATTLE!** First to answer gets 20 XP!\n\n**Question:** {q_data.get('question', '')}"
                    )
                except Exception as e:
                    logger.error(f"Aura Battle Error: {str(e)}")
        elif "@aura" in content.lower() and not is_winner:
            api_key = get_openai_api_key()
            if api_key:
                user_msg = content.replace("@aura", "").replace("@Aura", "").strip()
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    
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
                    text_response = res.choices[0].message.content.strip()

                    StudyGroupMessage.objects.create(
                        room=room,
                        is_aura=True,
                        content=text_response
                    )
                except Exception as e:
                    logger.error(f"Aura LLM Error: {str(e)}")
        return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': is_winner})


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
    try:
        body = json.loads(request.body.decode('utf-8'))
        amount = int(body.get('amount', 0))
    except (ValueError, TypeError, Exception):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    # Clamp to reasonable per-turn bounds
    amount = max(1, min(amount, 50))

    try:
        from students.models import Student
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)

    from academics.gamification_models import StudentXP
    xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    xp_profile.add_xp(amount)

    return JsonResponse({
        'xp_earned': amount,
        'total_xp': xp_profile.total_xp,
        'level': xp_profile.level,
    })


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
