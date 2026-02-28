
# Hybrid AI Architecture Plan for School Management System

## Overview
This document outlines the strategy for moving towards a hybrid AI architecture where:
1.  **Vercel Deployment (Production)**: Continues to use `students.views_ai.py` which calls Hugging Face Inference API (Serverless). This is cost-effective for low usage and requires no GPU management.
2.  **GPU Worker (Future/High Performance)**: A dedicated Python process running on a GPU server (e.g., RunPod, AWS g4dn) that loads models into VRAM for <500ms latency.

## New File Structure

```plaintext
/school-portal-saas
├── services/
│   ├── __init__.py
│   └── aura_worker.py      # <-- NEW: Local GPU implementation (Reference)
├── students/
│   ├── views_ai.py         # <-- EXISTING: API-based implementation (Production)
```

## `services/aura_worker.py`
This file contains a complete `transformers` pipeline implementation. It includes:
-   **ASR**: Whisper Large v3 (Turbo)
-   **LLM**: Llama 3 8B Instruct (4-bit Quantized)
-   **TTS**: Parler TTS Mini v1

### Dependencies for Worker
The worker has heavier dependencies than the main web app. Do *not* add these to the main `requirements.txt` to avoid bloating the Vercel slug size.
Create `requirements-gpu.txt`:
```txt
torch
transformers
accelerate
bitsandbytes
scipy
soundfile
fastapi
uvicorn
```

## Integration Strategy

### Step 1: Reference Implementation (Complete)
We have added `services/aura_worker.py` as a standalone script. It is independent of the Django WSGI application and does not import Django settings unless necessary.

### Step 2: Queue Interface (Future)
When the GPU worker is deployed, we will update `students/views_ai.py` to check for a worker availability or use a queue (Redis/Celery) instead of calling the HF API directly.

```python
# Future students/views_ai.py idea
if settings.USE_GPU_WORKER:
    # Push job to Redis
    job_id = queue.enqueue(process_voice_interaction, audio_file)
    return JsonResponse({'status': 'processing', 'job_id': job_id})
else:
    # Existing API call
    return call_hf_api(audio_file)
```

### Step 3: Deployment
Deploy `services/aura_worker.py` wrapped in a FastAPI app on a GPU provider.

## Next Steps
1.  Review `services/aura_worker.py` to ensure it matches your specific model requirements.
2.  Keep `requirements.txt` clean (only `huggingface_hub` and `requests`).
3.  Test the worker locally if you have an NVIDIA GPU.
