from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
import requests
import os
from huggingface_hub import InferenceClient

# Initialize Inference Client (Assuming settings.HUGGINGFACE_API_TOKEN is set)
# If using dedicated endpoints, use the specific URL. If using free inference API, use model ID.
HF_TOKEN = getattr(settings, 'HUGGINGFACE_API_TOKEN', None)
OPENAI_AUDIO_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_WHISPER_MODEL = os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1")

# Model Endpoints (Replace with your actual Endpoint URLs for production speed)
ASR_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
LLM_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct" 
TTS_URL = "https://api-inference.huggingface.co/models/parler-tts/parler-tts-mini-v1"


def get_openai_api_key():
    configured = getattr(settings, 'OPENAI_API_KEY', None)
    if configured:
        return configured
    return os.environ.get("OPENAI_API_KEY")


def transcribe_with_openai_whisper(audio_data, filename="recording.webm", content_type="audio/webm"):
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    files = {
        "file": (filename, audio_data, content_type or "audio/webm"),
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
        raise RuntimeError(f"OpenAI Whisper HTTP {response.status_code}: {response.text[:400]}")

    return (response.json().get("text") or "").strip()

@login_required
def aura_interaction_view(request):
    """
    Render the Aura command center page.
    """
    return render(request, 'teachers/ai_sessions_list.html')

@csrf_exempt
@login_required
def process_audio_interaction(request):
    """
    Orchestrates the S2S pipeline:
    1. ASR: User Audio -> Text (OpenAI Whisper primary, HF Whisper fallback)
    2. LLM: Text -> AI Text (Llama 3)
    3. TTS: AI Text -> Audio (Parler-TTS)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # 1. Get Audio File from Request
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)

        # 2. ASR (Speech-to-Text)
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

        audio_data = audio_file.read()
        user_text = ""
        openai_error = None

        try:
            user_text = transcribe_with_openai_whisper(
                audio_data,
                filename=getattr(audio_file, 'name', 'recording.webm') or 'recording.webm',
                content_type=getattr(audio_file, 'content_type', 'audio/webm') or 'audio/webm',
            )
        except Exception as exc:
            openai_error = str(exc)

        if not user_text and HF_TOKEN:
            asr_response = requests.post(ASR_URL, headers=headers, data=audio_data)
            if asr_response.status_code == 200:
                user_text = (asr_response.json().get("text") or "").strip()

        if not user_text:
             return JsonResponse({"error": "Could not transcribe audio", "openai_error": openai_error}, status=500)

        # 3. LLM (Text Generation)
        # Using huggingface_hub InferenceClient for easier text generation
        client = InferenceClient(model=LLM_MODEL, token=HF_TOKEN)
        
        # Prompt Engineering for Llama 3
        messages = [
            {"role": "system", "content": "You are Aura, a helpful AI assistant for teachers."},
            {"role": "user", "content": user_text}
        ]
        
        # Generate Response
        llm_response_text = ""
        for token in client.chat_completion(messages, max_tokens=150, stream=True):
             content = token.choices[0].delta.content
             if content:
                 llm_response_text += content

        # 4. TTS (Text-to-Speech)
        # Call Parler-TTS
        # Note: Parler requires a description prompt often
        tts_payload = {
            "inputs": llm_response_text,
            # "options": {"wait_for_model": True}
        }
        
        tts_response = requests.post(TTS_URL, headers=headers, json=tts_payload)
        
        if tts_response.status_code != 200:
            # Fallback or error handling
            return JsonResponse({
                "user_text": user_text,
                "ai_text": llm_response_text,
                "audio_error": tts_response.text
            })

        # Return JSON with Audio as base64 or direct binary response?
        # Typically easier to return JSON with Base64 for frontend playback, or a URL to fetch.
        # But for streaming, we might want to return the audio bytes directly if possible.
        
        import base64
        audio_b64 = base64.b64encode(tts_response.content).decode('utf-8')

        return JsonResponse({
            "user_text": user_text,
            "ai_text": llm_response_text,
            "audio_base64": audio_b64
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
