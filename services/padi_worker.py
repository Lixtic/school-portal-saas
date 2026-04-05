"""
Dedicated GPU Worker for Padi-T (Teacher Assistant)
---------------------------------------------------
This script is intended to run on a separate GPU-enabled server (e.g., RunPod, Lambda Labs, local RTX 3090/4090).
It implements the full Speech-to-Speech (S2S) pipeline locally using Hugging Face Transformers,
avoiding API latency and costs.

Architecture:
1.  Speech-to-Text (ASR): OpenAI Whisper (Tiny/Distil)
2.  LLM Inference: Meta-Llama-3-8B-Instruct (4-bit Quantized)
3.  Text-to-Speech (TTS): Parler-TTS (Mini v1)

Usage:
    Do NOT run this on Vercel or standard web servers (CPU-only).
    Run: `python -m services.padi_worker`
    Dependencies: `pip install torch transformers accelerate bitsandbytes scipy soundfile`
"""

import sys
import logging
import time

logger = logging.getLogger(__name__)

# Conditional imports to prevent crashes on non-GPU environments
try:
    import torch
    from transformers import pipeline
except ImportError:
    torch = None
    logger.warning("GPU dependencies not found. SchoolPadi Worker will not function properly.")

class PadiPipeline:
    def __init__(self, device="cuda:0"):
        if not torch or not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU is required for this worker.")
        
        self.device = device
        logger.info(f"Initializing SchoolPadi Pipeline on {device}...")

        # 1. LOAD THE EARS (ASR)
        logger.info("Loading ASR (Whisper)...")
        # Use 'distil-whisper' for speed if available
        # But 'tiny' is safer for smaller VRAM
        self.asr_pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny.en",
            device=device
        )

        # 2. LOAD THE BRAIN (LLM)
        logger.info("Loading LLM (Llama 3)...")
        # Use 4-bit quantization to fit on consumer GPUs
        try:
            self.llm_pipe = pipeline(
                "text-generation",
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                model_kwargs={"load_in_4bit": True},
                device_map="auto"
            )
        except Exception as e:
            logger.error(f"Failed to load LLM (bitsandbytes installed?): {e}")
            raise e

        # 3. LOAD THE VOICE (TTS)
        logger.info("Loading TTS (Parler)...")
        self.tts_pipe = pipeline(
            "text-to-speech",
            model="parler-tts/parler-tts-mini-v1",
            device=device
        )
        logger.info("SchoolPadi Pipeline Ready.")

    def talk_to_padi(self, audio_file):
        """
        Full S2S pipeline:
        Audio input -> ASR -> Text -> LLM -> Text -> TTS -> Audio output
        """
        # Step A: Transcribe
        user_text = ""
        try:
            asr_out = self.asr_pipe(audio_file)
            user_text = asr_out["text"].strip()
            logger.info(f"Learner said: {user_text}")
        except Exception as e:
            logger.error(f"ASR Failed: {e}")
            return None

        if not user_text:
            return None

        # Step B: Think (Prompt for brevity)
        messages = [
            {"role": "system", "content": "You are SchoolPadi. Reply in 1 sentence."},
            {"role": "user", "content": user_text},
        ]
        
        padi_text = ""
        try:
            llm_out = self.llm_pipe(
                messages, 
                max_new_tokens=50,
                return_full_text=False
            )
            # Depending on pipeline output format, extract text
            # Usually: [{'generated_text': '...'}] if return_full_text=False
            if isinstance(llm_out, list) and len(llm_out) > 0:
                 padi_text = llm_out[0]["generated_text"]
            else:
                 padi_text = str(llm_out)
                 
            logger.info(f"SchoolPadi Reply: {padi_text}")
        except Exception as e:
            logger.error(f"LLM Failed: {e}")
            return None

        # Step C: Speak
        try:
            audio_out = self.tts_pipe(padi_text)
            return audio_out
        except Exception as e:
            logger.error(f"TTS Failed: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        # Check for GPU
        if torch and torch.cuda.is_available():
            print("Starting SchoolPadi Pipeline...")
            padi = PadiPipeline()
            print("Pipeline Ready. (Mocking input for demo)")
            # In real usage: padi.talk_to_padi("path/to/audio.wav")
        else:
            print("Skipping initialization: No GPU detected.")
    except Exception as e:
        print(f"Startup Failed: {e}")
