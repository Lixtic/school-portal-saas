
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
    "openai/whisper-large-v3", # Main stable model
    "openai/whisper-large-v2", # Reliable fallback
    "distil-whisper/distil-large-v3", # Fast and good
    "openai/whisper-tiny", # Last resort
]

# Try new router endpoint first, then legacy API
HF_INFERENCE_URL_TEMPLATES = [
    "https://router.huggingface.co/hf-inference/models/{model_id}",
    "https://api-inference.huggingface.co/models/{model_id}",
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
    error_log = []
    if isinstance(model_urls, str):
        model_urls = [model_urls]
        
    for url in model_urls:
        response = None
        try:
            kwargs = {'headers': headers}
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
        if not headers:
            return JsonResponse({"error": "ASR Unavailable: Missing HUGGINGFACE_API_TOKEN"}, status=503)
        
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
                # 1. Try to find a working LLM stream
                response_llm_stream = None
                for llm_url in HF_LLM_MODELS:
                    try:
                        resp = requests.post(llm_url, headers=headers, json=payload_llm, stream=True)
                        if resp.status_code == 200:
                            response_llm_stream = resp
                            break
                    except:
                        continue
                
                if not response_llm_stream:
                    # All LLMs failed
                    return

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
                                    # Send sentence to TTS with fallback
                                    tts_payload = {"inputs": buffer.strip()}
                                    
                                    # Try TTS models
                                    for tts_url in HF_TTS_MODELS:
                                        try:
                                            tts_resp = requests.post(tts_url, headers=headers, json=tts_payload)
                                            if tts_resp.status_code == 200:
                                                yield tts_resp.content
                                                break
                                        except:
                                            continue
                                            
                                    buffer = "" # Reset buffer
                            except:
                                pass
                
                # Process remaining buffer
                if buffer.strip():
                     tts_payload = {"inputs": buffer.strip()}
                     for tts_url in HF_TTS_MODELS:
                        try:
                            tts_resp = requests.post(tts_url, headers=headers, json=tts_payload)
                            if tts_resp.status_code == 200:
                                yield tts_resp.content
                                break
                        except:
                            continue

            except Exception as e:
                # Log error or yield slight silence
                pass

        # Return the generator as a stream
        return StreamingHttpResponse(generate_audio_stream(), content_type='audio/mpeg')

    except Exception as e:
        return JsonResponse({"error":str(e)}, status=500)
