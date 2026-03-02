
import os
import requests
import json
import time
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


OPENAI_AUDIO_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_WHISPER_MODEL = os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1")

# Configuration - should be in settings.py
# HF_API_URL_WHISPER = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo" # Faster, good accuracy -- 410 Error
# Use lists for fallbacks
HF_WHISPER_MODELS = [
    "openai/whisper-large-v3", # Main stable model
    "openai/whisper-large-v2", # Reliable fallback
    "distil-whisper/distil-large-v3", # Fast and good
    "openai/whisper-tiny", # Last resort
]

# Optional: dedicated HF Inference Endpoint URL (recommended if router returns 404)
HF_ASR_ENDPOINT = os.environ.get("HF_ASR_ENDPOINT")

# Try new router endpoint first, then legacy API
HF_INFERENCE_URL_TEMPLATES = [
    "https://router.huggingface.co/v1/models/{model_id}",
]

# Use a very reliable, open LLM for fallback (Zephyr or Mistral)
HF_LLM_MODELS = [
    "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
    "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
]

# Fallback TTS
HF_TTS_MODELS = [
    "https://api-inference.huggingface.co/models/parler-tts/parler-tts-mini-v1",
    "https://api-inference.huggingface.co/models/facebook/mms-tts-eng"
]


def get_openai_api_key():
    configured = getattr(settings, 'OPENAI_API_KEY', None)
    if configured:
        return configured
    return os.environ.get("OPENAI_API_KEY")


def transcribe_with_openai_whisper(audio_content, filename="recording.webm", content_type="audio/webm"):
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    files = {
        "file": (filename, audio_content, content_type or "audio/webm"),
    }
    data = {
        "model": OPENAI_WHISPER_MODEL,
        "response_format": "json",
    }

    response = requests.post(
        OPENAI_AUDIO_TRANSCRIPTIONS_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=120,
    )

    if response.status_code != 200:
        detail = response.text[:400]
        raise RuntimeError(f"OpenAI Whisper HTTP {response.status_code}: {detail}")

    parsed = response.json()
    return (parsed.get("text") or "").strip()

def get_hf_headers():
    token = os.environ.get("HUGGINGFACE_API_TOKEN") or getattr(settings, "HUGGINGFACE_API_TOKEN", None) or os.environ.get("HF_TOKEN")
    if not token:
        # Fallback or error
        return {}
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-Wait-For-Model": "true",
    }

def query_hf_inference(model_urls, headers, data=None, json_payload=None):
    """
    Helper to query HF Inference API with fallbacks.
    Args:
        model_urls (list or str): List of model URLs to try.
        headers (dict): Request headers.
        data (bytes, optional): Raw data for POST.
        json_payload (dict, optional): JSON data for POST.
    """
    last_error = None
    error_log = []
    if isinstance(model_urls, str):
        model_urls = [model_urls]
        
    for url in model_urls:
        response = None
        try:
            request_headers = dict(headers)
            if data is not None and "content-type" not in {k.lower() for k in request_headers}:
                request_headers["Content-Type"] = "application/octet-stream"
            kwargs = {'headers': request_headers}
            if data is not None:
                kwargs['data'] = data
            elif json_payload is not None:
                kwargs['json'] = json_payload

            url_candidates = [url]
            if not url.startswith("http"):
                url_candidates = [
                    template.format(model_id=url)
                    for template in HF_INFERENCE_URL_TEMPLATES
                ]

            for candidate_url in url_candidates:
                # Simple retry loop for 503 loading
                for attempt in range(3): # Increased retries
                    try:
                        response = requests.post(candidate_url, **kwargs)
                    except Exception as req_err:
                        last_error = f"Connection error for {candidate_url}: {str(req_err)}"
                        error_log.append(last_error)
                        continue

                    if response.status_code == 200:
                        return response
                    
                    if response.status_code == 503:
                        # Model loading, wait briefly
                        status_print = f"Model {candidate_url} loading (503), retrying..."
                        print(status_print)
                        time.sleep(5) # Increased wait
                        continue
                    else:
                        # Immediate failure (400, 401, 403, 404, 410, 500)
                        content_type = response.headers.get("content-type", "")
                        last_error = (
                            f"Error {response.status_code} from {candidate_url} "
                            f"(content-type={content_type}): {response.text[:200]}"
                        )
                        error_log.append(last_error)
                        break # Break inner loop, try next candidate
                
                # If loop finished naturally (503s exhausted) or break (other error)
                if response and response.status_code == 503:
                    last_error = f"Model {candidate_url} unavailable (503) after retries"
                    error_log.append(last_error)
                # Try next candidate URL for the same model id

        except Exception as e:
            last_error = f"Exception processing {url}: {str(e)}"
            error_log.append(last_error)
    
    # If all failed
    if last_error:
        recent_errors = " | ".join(error_log[-3:])
        raise Exception(f"All models failed. Last error: {last_error}. Recent: {recent_errors}")
    raise Exception("Unknown error in HF query")

def aura_voice_view(request):
    """Render the voice interface with Realtime API support."""
    return render(request, 'students/aura_voice.html')


@csrf_exempt
def create_realtime_session(request):
    """
    Create an ephemeral token for OpenAI Realtime API.
    Frontend will use this to establish WebSocket connection directly to OpenAI.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        voice = data.get('voice', 'coral')
        instructions = data.get('instructions', 
            "You are Aura, a helpful and friendly AI tutor. "
            "Keep answers concise and conversational. "
            "You're speaking to a student, so be encouraging and supportive.")
        
        import requests
        api_key = get_openai_api_key()
        
        if not api_key:
            return JsonResponse({"error": "OpenAI API key not configured"}, status=500)
        
        # Create ephemeral token for Realtime API
        # The client will use this to connect directly to OpenAI WebSocket
        response = requests.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": voice
            },
            timeout=30
        )
        
        if response.status_code != 200:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Realtime session API error {response.status_code}: {response.text[:500]}")
            return JsonResponse({
                "error": f"OpenAI API error ({response.status_code})",
                "detail": response.text[:300]
            }, status=response.status_code)
        
        session_data = response.json()
        client_secret = session_data.get("client_secret", {}).get("value", "")
        
        if not client_secret:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Realtime session response missing client_secret: {session_data}")
            return JsonResponse({
                "error": "No client_secret in response",
                "detail": str(session_data)[:300]
            }, status=500)
        
        return JsonResponse({
            "client_secret": client_secret,
            "model": session_data.get("model", "gpt-4o-realtime-preview-2024-12-17")
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Realtime Session Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def process_voice_interaction(request):
    """
    Orchestrate the S2S pipeline:
    Audio (Frontend) -> OpenAI Whisper (primary) / HF Whisper (fallback)
    -> GPT-4o-mini (LLM) -> OpenAI TTS-1 (with voice & speed settings) -> Audio Stream (Frontend)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)
        
        # Get voice settings from request (defaults: nova, 1.0)
        voice_type = request.POST.get('voice', 'nova')
        speech_speed = float(request.POST.get('speed', 1.0))
        
        # Validate voice type
        valid_voices = ['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar']
        if voice_type not in valid_voices:
            voice_type = 'coral'
        
        # Validate speed (0.25 to 4.0 per OpenAI docs, but we limit to 0.5-1.5 in UI)
        speech_speed = max(0.5, min(1.5, speech_speed))

        # 1. ASR - OpenAI Whisper (primary), Hugging Face Whisper (fallback)
        user_text = ""
        audio_content = audio_file.read()
        openai_error = None
        hf_error = None

        try:
            user_text = transcribe_with_openai_whisper(
                audio_content=audio_content,
                filename=getattr(audio_file, 'name', 'recording.webm') or 'recording.webm',
                content_type=getattr(audio_file, 'content_type', 'audio/webm') or 'audio/webm',
            )
        except Exception as e:
            openai_error = str(e)

        if not user_text:
            headers = get_hf_headers()
            if not headers:
                hf_error = "Missing HUGGINGFACE_API_TOKEN"
            else:
                try:
                    asr_urls = [HF_ASR_ENDPOINT] if HF_ASR_ENDPOINT else []
                    asr_urls.extend(HF_WHISPER_MODELS)
                    response_asr = query_hf_inference(asr_urls, headers, data=audio_content)
                    user_text = (response_asr.json().get('text') or '').strip()
                except Exception as e:
                    hf_error = str(e)

        if not user_text:
            return JsonResponse(
                {
                    "error": "ASR Unavailable: Could not transcribe audio",
                    "openai_error": openai_error,
                    "hf_error": hf_error,
                },
                status=503,
            )
        
        # 2. LLM - GPT-4o-mini for response generation
        system_prompt = (
            "You are Aura, a helpful and friendly AI tutor. "
            "Keep answers concise (max 2 sentences), conversational, and no markdown."
        )

        # Generator function for streaming response
        def generate_audio_stream():
            try:
                import openai
                client = openai.OpenAI(api_key=get_openai_api_key())

                # Step 2: Get LLM text response
                res = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_text}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                text_response = res.choices[0].message.content.strip()

                # Step 3: Stream OpenAI TTS with voice and speed settings
                if text_response:
                    tts_resp = client.audio.speech.create(
                        model='tts-1',
                        voice=voice_type,
                        input=text_response,
                        speed=speech_speed,
                        response_format='mp3'
                    )
                    
                    for chunk in tts_resp.iter_bytes():
                        if chunk:
                            yield chunk

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Aura Voice Stream Error: {str(e)}")
        
        # Get the text response for headers (run LLM once before streaming)
        import openai
        client = openai.OpenAI(api_key=get_openai_api_key())
        
        res = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        aura_text = res.choices[0].message.content.strip()
        
        # Create TTS stream
        def tts_audio_stream():
            try:
                tts_resp = client.audio.speech.create(
                    model='tts-1',
                    voice=voice_type,
                    input=aura_text,
                    speed=speech_speed,
                    response_format='mp3'
                )
                
                for chunk in tts_resp.iter_bytes():
                    if chunk:
                        yield chunk
                        
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"TTS Error: {str(e)}")
        
        # Return streaming response with transcript headers
        from urllib.parse import quote
        response = StreamingHttpResponse(
            tts_audio_stream(),
            content_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=\"aura.mp3\"",
                "X-User-Text": quote(user_text),
                "X-Aura-Text": quote(aura_text),
            },
        )
        return response

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Voice Interaction Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


from django.contrib.auth.decorators import login_required
from academics.models import StudyGroupRoom, StudyGroupMessage, StudentXP

@login_required
def aura_arena_view(request):
    if request.user.user_type != 'student':
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Only students can enter the Aura Arena.")
        return redirect('dashboard')
    
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        from django.contrib import messages
        from django.shortcuts import redirect
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
        import logging
        logger = logging.getLogger(__name__)
        try:
            logger.warning(f"StudyGroupRoom table missing for schema {connection.schema_name}. Running migration...")
            call_command('migrate', 'academics', '--database=default', interactive=False)
            room, _ = StudyGroupRoom.objects.get_or_create(
                student_class=student.current_class,
                defaults={'name': f"{student.current_class.name} Arena"}
            )
        except Exception as mig_err:
            logger.error(f"Auto-migration failed: {mig_err}")
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Aura Arena is being set up. Please try again in a moment.")
            return redirect('dashboard')

    try:
        xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    except Exception:
        xp_profile = None
    
    from django.shortcuts import render
    context = {
        'room': room,
        'student': student,
        'xp': xp_profile
    }
    return render(request, 'students/aura_arena.html', context)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def aura_arena_api(request):
    import json
    from django.http import JsonResponse
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
                    import logging
                    logger = logging.getLogger(__name__)
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
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Aura LLM Error: {str(e)}")
        return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': is_winner})


    return JsonResponse({'error': 'Method not allowed'}, status=405)

