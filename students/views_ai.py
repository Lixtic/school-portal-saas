
import os
import requests
import json
import time
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Configuration - should be in settings.py
# HF_API_URL_WHISPER = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo" # Faster, good accuracy -- 410 Error
# Use lists for fallbacks
HF_WHISPER_MODELS = [
    "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
    "https://api-inference.huggingface.co/models/distil-whisper/distil-large-v3",
]

HF_API_URL_LLM = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
# Alternative: "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"

HF_API_URL_TTS = "https://api-inference.huggingface.co/models/parler-tts/parler-tts-mini-v1" 
# Alternative: "https://api-inference.huggingface.co/models/facebook/mms-tts-eng"

def get_hf_headers():
    token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not token:
        # Fallback or error
        return {}
    return {"Authorization": f"Bearer {token}"}

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
    if isinstance(model_urls, str):
        model_urls = [model_urls]
        
    for url in model_urls:
        try:
            kwargs = {'headers': headers}
            if data is not None:
                kwargs['data'] = data
            elif json_payload is not None:
                kwargs['json'] = json_payload
            
            # Simple retry loop for 503 loading
            for attempt in range(2):
                response = requests.post(url, **kwargs)
                
                if response.status_code == 200:
                    return response
                
                if response.status_code == 503:
                    # Model loading, wait briefly
                    time.sleep(3)
                    continue
                else:
                    break
            
            # If we get here, it failed
            last_error = f"Status: {response.status_code}, Response: {response.text[:200]}"
            # Try next model
            
        except Exception as e:
            last_error = str(e)
    
    # If all failed
    if last_error:
        raise Exception(f"All models failed. Last error: {last_error}")
    raise Exception("Unknown error in HF query")

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
        
        try:
            # Read audio content for potential retries
            audio_content = audio_file.read()
            
            # Use list of models for reliability
            response_asr = query_hf_inference(HF_WHISPER_MODELS, headers, data=audio_content)
            user_text = response_asr.json().get('text')
        except Exception as e:
            return JsonResponse({"error": f"ASR Unavailable: {str(e)}"}, status=503)
        
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
