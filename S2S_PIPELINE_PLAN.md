# Cascaded Speech-to-Speech (S2S) Implementation Plan

## Overview
This document outlines the architecture for a Django-integrated S2S pipeline (ASR -> LLM -> TTS) using specific models:
- **ASR**: OpenAI Whisper (Local or API)
- **LLM**: Meta Llama 3 (Quantized 8B or 70B via API)
- **TTS**: Parler-TTS (Text-to-Speech)

## Architecture Options

### Option A: Proxy to Dedicated Inference Server (Recommended for Production/Scale)
Since running 4-bit quantized LLMs and TTS models inside a standard Django view blocks the worker process and consumes massive VRAM/RAM, the best approach is a separate service.

**Components:**
1.  **Django Frontend**: 
    -   renders `templates/teachers/ai_sessions_list.html`
    -   JavaScript records audio chunks.
    -   Sends audio to Django View via WebSocket or HTTP POST.
2.  **Django Backend (Orchestrator)**:
    -   Authenticates user.
    -   Proxies request to **AI Inference Service**.
    -   Manages session history in PostgreSQL.
3.  **AI Inference Service (FastAPI / Ray Serve)**:
    -   Holds models in VRAM (persistent process).
    -   Exposes simple API: `/infer/s2s`.
    -   Stream output (Audio bytes) back to Django.

### Option B: Django View Orchestrating Remote APIs (Hugging Face Inference Endpoints)
If you do not have a GPU server, this is the only viable option.

**Flow:**
1.  **Django View** receives audio.
2.  **ASR**: Calls `openai-whisper` endpoint (HF or OpenAI).
3.  **LLM**: Calls Llama 3 Endpoint on HF (supports token streaming).
4.  **TTS**: Calls Parler-TTS Endpoint on HF.
5.  **Return**: Returns audio file or stream to user.

## Implementation Details (Option B - Django Orchestrator)

### 1. Prerequisites
-   `huggingface_hub` library.
-   `HUGGINGFACE_API_TOKEN` in `.env`.
-   Deployed Inference Endpoints for Llama 3 and Parler-TTS.

### 2. Python Libraries
```bash
pip install huggingface_hub requests soundfile numpy io
```

### 3. Service Layer (`teachers/services/s2s_pipeline.py`)

```python
import requests
import json
from django.conf import settings
from huggingface_hub import InferenceClient

class S2SPipeline:
    def __init__(self):
        self.hf_token = settings.HUGGINGFACE_API_TOKEN
        self.asr_url = settings.HF_ASR_ENDPOINT  # e.g., openai/whisper-large-v3
        self.llm_client = InferenceClient(model=settings.HF_LLM_ENDPOINT, token=self.hf_token) # e.g., meta-llama/Meta-Llama-3-8B-Instruct
        self.tts_url = settings.HF_TTS_ENDPOINT  # e.g., parler-tts/parler-tts-mini-v1

    def speech_to_text(self, audio_bytes):
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        response = requests.post(self.asr_url, headers=headers, data=audio_bytes)
        return response.json().get("text", "")

    def generate_text(self, prompt, context=""):
        # Llama 3 Format
        formatted_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{context}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        # Stream tokens if utilizing streaming response in Django
        return self.llm_client.text_generation(formatted_prompt, max_new_tokens=200)

    def text_to_speech(self, text):
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": text}
        response = requests.post(self.tts_url, headers=headers, json=payload)
        return response.content # Audio bytes
        
    def run_pipeline(self, audio_bytes, system_context="You are a helpful assistant."):
        # ASR
        text_prompt = self.speech_to_text(audio_bytes)
        if not text_prompt: return None
        
        # LLM
        llm_response = self.generate_text(text_prompt, context=system_context)
        
        # TTS
        audio_response = self.text_to_speech(llm_response)
        
        return {
            "user_text": text_prompt,
            "ai_text": llm_response,
            "audio": audio_response
        }
```

## Local 4-bit Quantization (GPU Required)

If running locally with a GPU (e.g., RTX 3090/4090), do **NOT** run this in the Django process.
Create a separate script `ai_server.py`:

```python
# ai_server.py
from fastapi import FastAPI, UploadFile
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

app = FastAPI()

# Load 4-bit Llama 3
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct", quantization_config=bnb_config)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")

@app.post("/process_audio")
async def process_audio(file: UploadFile):
    # 1. Whipser ASR (Load model globally too)
    # 2. Llama Invoke
    # 3. Parler TTS
    return {"audio": ..., "text": ...}
```

Run with: `uvicorn ai_server:app --port 8001 --reload`

## Streaming Optimization (Advanced)
For true "Talk to Aura" experience:
1.  **WebSocket**: Use Django Channels or FastAPI WebSockets.
2.  **Streaming TTS**: Parler-TTS is sequence-to-sequence. Streaming chunks of audio is difficult natively. 
    -   *Workaround*: Sentence-level buffering. Send each sentence from Llama 3 to TTS immediately.
    -   *Library*: `miniaudio` or `pyaudio` on client to play chunks.

## Recommendation for Portals
Start with **Option B (HF Endpoints)** via a Django View. It keeps the codebase simple and avoids managing complex GPU infrastructure/deployments.
1.  Add `huggingface_hub` to `requirements.txt`.
2.  Create `teachers/views_ai.py`.
3.  Add endpoint in `teachers/urls.py` path('api/aura/chat/', ...).
