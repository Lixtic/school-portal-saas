
import os
import requests
import json
import time
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Configuration - should be in settings.py
HF_API_URL_WHISPER = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo" # Faster, good accuracy
HF_API_URL_LLM = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
HF_API_URL_TTS = "https://api-inference.huggingface.co/models/parler-tts/parler-tts-mini-v1" # Optimized for speed

def get_hf_headers():
    token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not token:
        # Fallback or error
        return {}
    return {"Authorization": f"Bearer {token}"}

def aura_voice_view(request):
    """Render the voice interface."""
    return render(request, 'students/aura_voice.html')

@csrf_exempt
def process_voice_interaction(request):
    """
    Orchestrate the S2S pipeline:
    Audio (Frontend) -> Whisper (API) -> Llama 3 (API) -> Parler-TTS (API) -> Audio Stream (Frontend)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)

        # 1. ASR - Whisper
        headers = get_hf_headers()
        response_asr = requests.post(
            HF_API_URL_WHISPER,
            headers=headers,
            data=audio_file.read()
        )
        
        if response_asr.status_code != 200:
            return JsonResponse({"error": f"ASR Error: {response_asr.text}"}, status=500)
            
        user_text = response_asr.json().get('text')
        if not user_text:
             return JsonResponse({"error": "Could not transcribe audio"}, status=500)

        # 2. LLM - Llama 3 (Streaming & Buffering)
        system_prompt = (
            "You are Aura, a helpful and friendly AI tutor. "
            "Keep answers concise (max 2 sentences), conversational, and no markdown."
        )
        
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        payload_llm = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "return_full_text": False,
                "temperature": 0.7,
            },
            "stream": True  # Enable streaming from LLM
        }

        # Generator function for streaming response
        def generate_audio_stream():
            try:
                # Use requests with stream=True for LLM
                response_llm_stream = requests.post(HF_API_URL_LLM, headers=headers, json=payload_llm, stream=True)
                
                buffer = ""
                sentence_endings = {'.', '!', '?'}
                
                for line in response_llm_stream.iter_lines():
                    if line:
                        # Parse SSE format "data: {...}"
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            try:
                                json_data = json.loads(decoded_line[5:])
                                token = json_data['token']['text']
                                buffer += token
                                
                                # Check for sentence end
                                if any(token.endswith(p) for p in sentence_endings) and len(buffer.strip()) > 5:
                                    # Send sentence to TTS
                                    # Note: Using fallback for speed/reliability in streaming chunks
                                    tts_payload = {"inputs": buffer.strip()}
                                    tts_resp = requests.post(HF_API_URL_TTS, headers=headers, json=tts_payload) 
                                    if tts_resp.status_code == 200:
                                        yield tts_resp.content
                                    buffer = "" # Reset buffer
                            except:
                                pass
                
                # Process remaining buffer
                if buffer.strip():
                     tts_resp = requests.post(HF_API_URL_TTS, headers=headers, json={"inputs": buffer.strip()})
                     if tts_resp.status_code == 200:
                         yield tts_resp.content

            except Exception as e:
                # Log error or yield slight silence
                pass

        # Return the generator as a stream
        return StreamingHttpResponse(generate_audio_stream(), content_type='audio/mpeg')



    except Exception as e:
        return JsonResponse({"error":str(e)}, status=500)
