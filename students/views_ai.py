
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


def _build_student_context(student):
    """Build context-aware instruction string for a student."""
    parts = []
    
    if student.current_class:
        parts.append(f"The student is in {student.current_class.name}.")
        
        # Get subjects for this class
        from academics.models import ClassSubject
        subjects = ClassSubject.objects.filter(
            class_name=student.current_class
        ).select_related('subject').values_list('subject__name', flat=True)
        if subjects:
            parts.append(f"Their subjects are: {', '.join(subjects)}.")
    
    if student.curriculum:
        parts.append(f"They follow the {student.curriculum} curriculum.")
    
    if student.interests:
        interests = student.interests if isinstance(student.interests, list) else []
        if interests:
            parts.append(f"Their interests include: {', '.join(interests)}.")
    
    return " ".join(parts)


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
        try:
            from students.models import Student
            student = Student.objects.select_related('current_class').filter(user=request.user).first()
            if student:
                student_context = _build_student_context(student)
        except Exception:
            pass  # gracefully degrade — generic instructions still work
        
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
                    "modalities": ["text", "audio"],
                    "input_audio_transcription": {
                        "model": "gpt-4o-transcribe"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
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
            "student_context": student_context,
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
                    
                    prompt = (
                        f"You are a strict JSON generator. Generate a short educational trivia question for a {student.current_class.name} class. "
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
                    
                    system_prompt = "You are Aura-T, a helpful AI tutor for students. Do NOT use headings, phases, or labels like 'Phase A', 'Hook', or 'Nugget'. Use 'tiny scaffolds' (very short, single-step conversational hints). Keep answers fun, extremely concise, and under 3 sentences."
                    
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

