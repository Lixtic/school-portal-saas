"""
AI Tutor Assistant - Personalized learning chatbot for students
"""
import logging
import os
import json
from datetime import date
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from django.conf import settings
from django.utils import timezone
from tenants.ai_model_config import get_platform_ai_provider, get_platform_model_config

logger = logging.getLogger(__name__)

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_VISION_MODEL = "gpt-4o"  # supports vision
HF_INFERENCE_API_URL = "https://router.huggingface.co/v1/models"
HF_DEFAULT_FALLBACK_MODEL = "google/flan-t5-large"
OPENAI_CHAT_MODELS = [
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini",
]

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}"
    ":generateContent?key={key}"
)
GEMINI_STREAM_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}"
    ":streamGenerateContent?alt=sse&key={key}"
)
GEMINI_CHAT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


def _build_sow_image_block(image_path_or_url: str):
    """Build the OpenAI image content block for scheme-of-work extraction."""
    import base64
    if str(image_path_or_url).startswith(('http://', 'https://')):
        return {"type": "image_url", "image_url": {"url": image_path_or_url}}
    ext = str(image_path_or_url).lower().rsplit('.', 1)[-1]
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'webp': 'image/webp',
            'gif': 'image/gif'}.get(ext, 'image/jpeg')
    with open(image_path_or_url, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode('utf-8')
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def extract_scheme_of_work_topics(image_path_or_url: str) -> list:
    """
    Use GPT-4o Vision to extract an ordered list of topic strings from a
    scheme-of-work screenshot uploaded by a teacher.
    Returns a Python list of strings (may be empty on failure).
    """
    data = extract_scheme_of_work_data(image_path_or_url)
    return data.get('topics', [])


def extract_scheme_of_work_data(image_path_or_url: str) -> dict:
    """
    Use GPT-4o Vision to extract topics AND indicator codes from a scheme-of-work
    screenshot uploaded by a teacher.

    Returns:
        {
            "topics": ["Topic A", "Topic B", ...],
            "indicators": {"Topic A": "B8.2.1.1.1", "Topic B": "B8.2.1.1.2", ...}
        }
    Indicator values are empty strings when no code is visible in the image.
    """
    import re as _re, json as _json

    api_key = _get_openai_api_key() if callable(globals().get('_get_openai_api_key')) else (
        getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    )
    if not api_key:
        return {'topics': [], 'indicators': {}}

    try:
        image_block = _build_sow_image_block(image_path_or_url)
    except Exception:
        return {'topics': [], 'indicators': {}}

    payload = {
        "model": OPENAI_VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                image_block,
                {
                    "type": "text",
                    "text": (
                        "This image is a school Scheme of Work (curriculum plan). "
                        "Extract every teaching topic and its full learning indicator in the order they appear.\n"
                        "Return ONLY a valid JSON array of objects with exactly two keys:\n"
                        "  'topic': the topic or sub-strand name (a concise label)\n"
                        "  'indicator': the COMPLETE indicator text — include BOTH the indicator code "
                        "(e.g. 'B8.2.1.1.1') AND the full performance indicator sentence that follows it. "
                        "Combine them as a single string, e.g. "
                        "'B8.2.1.1.1 Count, read and write numbers up to 10 billion'. "
                        "If no indicator is visible for a row, set 'indicator' to an empty string.\n"
                        "Example: ["
                        "{\"topic\": \"Integers and Number Lines\", \"indicator\": \"B8.2.1.1.1 Understand and apply properties of integers to solve problems\"}, "
                        "{\"topic\": \"Fractions\", \"indicator\": \"B8.2.1.1.2 Simplify and compare fractions in real-world contexts\"}"
                        "]\n"
                        "If the image is unreadable, return []"
                    ),
                },
            ],
        }],
        "max_tokens": 2500,
    }

    try:
        req = urllib_request.Request(
            OPENAI_CHAT_COMPLETIONS_URL,
            data=_json.dumps(payload).encode('utf-8'),
            headers={'Authorization': f'Bearer {api_key}',
                     'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib_request.urlopen(req, timeout=60) as resp:
            result = _json.loads(resp.read().decode('utf-8'))
        content = result['choices'][0]['message']['content'].strip()
        match = _re.search(r'\[.*?\]', content, _re.DOTALL)
        if match:
            items = _json.loads(match.group(0))
            if isinstance(items, list):
                topics = []
                indicators = {}
                for item in items:
                    if isinstance(item, str):
                        # Fallback: plain string list (old format)
                        t = item.strip()
                        if t:
                            topics.append(t)
                    elif isinstance(item, dict):
                        t = str(item.get('topic', '')).strip()
                        ind = str(item.get('indicator', '')).strip()
                        if t:
                            topics.append(t)
                            if ind:
                                indicators[t] = ind
                return {'topics': topics, 'indicators': indicators}
    except Exception:
        logger.warning('extract_scheme_of_work_data failed for %s', image_path_or_url, exc_info=True)
    return {'topics': [], 'indicators': {}}


def _resolve_openai_model(payload, category='tutor'):
    requested_model = str((payload or {}).get("model") or "").strip()
    env_model = str(os.environ.get("OPENAI_CHAT_MODEL", "")).strip()

    if requested_model:
        return requested_model
    configured = get_platform_model_config(category)
    if configured.get('provider') == 'openai' and configured.get('model'):
        return str(configured.get('model')).strip()
    if env_model:
        return env_model
    return OPENAI_CHAT_MODELS[0]


def _get_openai_api_key():
    configured = getattr(settings, "OPENAI_API_KEY", None)
    if configured:
        return configured
    return os.environ.get("OPENAI_API_KEY")


def get_openai_chat_model(category='tutor'):
    return _resolve_openai_model({}, category=category)


def get_active_ai_model(category='tutor'):
    """Return the display name of whichever model is currently active."""
    configured = get_platform_model_config(category)
    if configured.get('model'):
        return configured.get('model')
    if _is_gemini_provider(category=category):
        return _get_gemini_model(category=category)
    return get_openai_chat_model(category=category)


def get_active_ai_provider(category='tutor'):
    """Return the provider string ('gemini' | 'openai') currently in use."""
    configured = get_platform_model_config(category)
    if configured.get('provider') == 'gemini':
        return "gemini"
    if configured.get('provider') == 'openai':
        return "openai"
    if _is_gemini_provider(category=category):
        return "gemini"
    return "openai"


# GPT-5 Nano is a reasoning model: completion tokens include hidden
# chain-of-thought reasoning tokens that do NOT produce visible output.
# A small max_completion_tokens (e.g. 1000) can be entirely consumed by
# reasoning, leaving 0 tokens for the actual response.  We enforce a
# generous minimum so reasoning + output both fit.
GPT5_MIN_COMPLETION_TOKENS = 16384


def _is_reasoning_model(model_name):
    """Return True for models that consume completion tokens on internal reasoning."""
    lowered = str(model_name or "").lower()
    return (
        lowered.startswith("gpt-5")
        or lowered.startswith("o1")
        or lowered.startswith("o3")
        or lowered.startswith("o4")
    )


def _with_resolved_model(payload):
    data = dict(payload or {})
    data["model"] = _resolve_openai_model(data)

    model_name = str(data.get("model") or "").lower()
    if _is_reasoning_model(model_name):
        # Reasoning models require max_completion_tokens, not max_tokens
        if "max_tokens" in data and "max_completion_tokens" not in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        # Enforce minimum so reasoning + output both fit
        current = data.get("max_completion_tokens") or 0
        try:
            current = int(current)
        except (TypeError, ValueError):
            current = 0
        if current < GPT5_MIN_COMPLETION_TOKENS:
            data["max_completion_tokens"] = GPT5_MIN_COMPLETION_TOKENS

        if "temperature" in data:
            try:
                temp_value = float(data.get("temperature"))
            except (TypeError, ValueError):
                temp_value = 1.0
            if temp_value != 1.0:
                data["temperature"] = 1

    return data


def _extract_temperature(payload):
    try:
        return float(payload.get("temperature", 0.7))
    except (TypeError, ValueError, AttributeError):
        return 0.7


def _extract_max_tokens(payload, default_value=700):
    try:
        value = payload.get("max_tokens", default_value)
        return int(value)
    except (TypeError, ValueError, AttributeError):
        return default_value


def _messages_to_hf_prompt(messages):
    if not isinstance(messages, list):
        return ""

    prompt_lines = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user")).strip().upper() or "USER"
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        prompt_lines.append(f"{role}: {content}")

    prompt_lines.append("ASSISTANT:")
    return "\n\n".join(prompt_lines)


def _extract_hf_generated_text(parsed):
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            text = (
                first.get("generated_text")
                or first.get("summary_text")
                or first.get("translation_text")
                or ""
            )
            return str(text).strip()

    if isinstance(parsed, dict):
        if parsed.get("error"):
            raise RuntimeError(f"Hugging Face error: {parsed.get('error')}")
        text = (
            parsed.get("generated_text")
            or parsed.get("summary_text")
            or parsed.get("translation_text")
            or ""
        )
        if text:
            return str(text).strip()

    return ""


def _build_openai_compatible_response(content_text, model_name):
    return {
        "id": f"hf-fallback-{model_name}",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text,
                },
                "finish_reason": "stop",
            }
        ],
        "model": f"hf:{model_name}",
        "fallback": True,
        "provider": "huggingface",
    }


def _extract_assistant_text_from_completion(response_data):
    if not isinstance(response_data, dict):
        return ""

    choices = response_data.get("choices") or []
    if not choices or not isinstance(choices, list):
        return ""

    message = choices[0].get("message") if isinstance(choices[0], dict) else {}
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text_part = item.get("text") or item.get("content") or ""
                if text_part:
                    parts.append(str(text_part))
        return "".join(parts)

    return ""


def _call_hf_fallback(payload):
    model_name = (
        os.environ.get("HF_FALLBACK_MODEL")
        or os.environ.get("HUGGINGFACE_FALLBACK_MODEL")
        or HF_DEFAULT_FALLBACK_MODEL
    )

    hf_token = (
        os.environ.get("HUGGINGFACE_API_TOKEN")
        or os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    )

    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    prompt = _messages_to_hf_prompt(payload.get("messages", []))
    if not prompt:
        raise RuntimeError("Hugging Face fallback failed: empty prompt")

    hf_payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max(64, min(_extract_max_tokens(payload), 1024)),
            "temperature": max(0.1, min(_extract_temperature(payload), 1.5)),
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
            "use_cache": True,
        },
    }

    hf_base_url = (
        os.environ.get("HF_INFERENCE_BASE_URL")
        or os.environ.get("HUGGINGFACE_INFERENCE_BASE_URL")
        or HF_INFERENCE_API_URL
    ).rstrip("/")

    req = urllib_request.Request(
        f"{hf_base_url}/{model_name}",
        data=json.dumps(hf_payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            generated_text = _extract_hf_generated_text(parsed)
            if not generated_text:
                raise RuntimeError("Hugging Face fallback returned an empty response")
            return generated_text, model_name
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"Hugging Face HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Hugging Face network error: {exc.reason}")


# ── Gemini helpers ────────────────────────────────────────────────────────────

def _get_gemini_api_key():
    configured = getattr(settings, "GEMINI_API_KEY", None)
    if configured:
        return configured
    return os.environ.get("GEMINI_API_KEY")


def _get_gemini_model(category='tutor'):
    configured = get_platform_model_config(category)
    if configured.get('provider') == 'gemini' and configured.get('model'):
        return str(configured.get('model')).strip().replace("gemini:", "", 1)
    configured = getattr(settings, "GEMINI_MODEL", None)
    if configured:
        return str(configured).strip().replace("gemini:", "", 1)
    return str(os.environ.get("GEMINI_MODEL") or GEMINI_CHAT_MODELS[0]).strip().replace("gemini:", "", 1)


def _normalize_gemini_model_name(model_name):
    """Accept model aliases like 'gemini:gemini-2.5-flash' or 'models/gemini-2.5-flash'."""
    model = str(model_name or "").strip()
    if model.startswith("gemini:"):
        model = model.split(":", 1)[1].strip()
    if model.startswith("models/"):
        model = model[len("models/"):].strip()
    return model


def _is_gemini_provider(category='tutor'):
    """Return True when Gemini is configured as the primary AI provider."""
    configured = get_platform_model_config(category)
    if configured.get('provider') in {'openai', 'gemini'}:
        provider = configured.get('provider')
    else:
        provider = get_platform_ai_provider()
    return provider == "gemini"


def _openai_messages_to_gemini_contents(messages):
    """Convert OpenAI-style messages list to Gemini 'contents' format."""
    contents = []
    system_parts = []
    for msg in (messages or []):
        role = str(msg.get("role", "user")).lower()
        content = msg.get("content", "")
        if isinstance(content, list):
            # Multimodal — convert text and image parts
            parts = []
            for p in content:
                if not isinstance(p, dict):
                    continue
                if "text" in p:
                    parts.append({"text": p["text"]})
                elif p.get("type") == "image_url":
                    url = (p.get("image_url") or {}).get("url", "")
                    if url.startswith("data:"):
                        # data:image/png;base64,XXXX → inline_data
                        header, b64_data = url.split(",", 1)
                        mime = header.split(":", 1)[1].split(";", 1)[0]
                        parts.append({"inline_data": {"mime_type": mime, "data": b64_data}})
                    elif url:
                        # Remote URL — use fileData
                        parts.append({"file_data": {"file_uri": url, "mime_type": "image/jpeg"}})
            if not parts:
                continue
            if role == "system":
                system_parts.extend(p.get("text", "") for p in parts if "text" in p)
            elif role == "assistant":
                contents.append({"role": "model", "parts": parts})
            else:
                contents.append({"role": "user", "parts": parts})
            continue
        content = str(content).strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})
    return contents, system_parts


def _call_gemini_chat(payload, model_override=None):
    """
    Send a chat request to the Gemini REST API and return an OpenAI-compatible
    response dict so the rest of the codebase needs no changes.
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model = _normalize_gemini_model_name(model_override or _get_gemini_model())
    messages = payload.get("messages", [])
    contents, system_parts = _openai_messages_to_gemini_contents(messages)

    generation_config = {}
    max_tokens = payload.get("max_tokens") or payload.get("max_completion_tokens")
    if max_tokens:
        generation_config["maxOutputTokens"] = int(max_tokens)
    temperature = payload.get("temperature")
    if temperature is not None:
        generation_config["temperature"] = float(temperature)
    # Translate OpenAI response_format to Gemini responseMimeType
    resp_fmt = payload.get("response_format")
    if isinstance(resp_fmt, dict) and resp_fmt.get("type") == "json_object":
        generation_config["responseMimeType"] = "application/json"

    body = {"contents": contents}
    if generation_config:
        body["generationConfig"] = generation_config
    if system_parts:
        body["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}

    url = GEMINI_GENERATE_URL.format(model=model, key=api_key)
    req = urllib_request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}")

    # Extract text from Gemini response
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        text = ""

    # Wrap in OpenAI-compatible shape
    return {
        "id": f"gemini-{model}",
        "object": "chat.completion",
        "model": f"gemini:{model}",
        "provider": "gemini",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop",
        }],
    }


def _stream_gemini_chat(payload, model_override=None):
    """
    Stream a chat response from Gemini and yield SSE chunks in the same format
    used by _stream_chat_completion so callers need no changes.
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model = _normalize_gemini_model_name(model_override or _get_gemini_model())
    messages = payload.get("messages", [])
    contents, system_parts = _openai_messages_to_gemini_contents(messages)

    generation_config = {}
    max_tokens = payload.get("max_tokens") or payload.get("max_completion_tokens")
    if max_tokens:
        generation_config["maxOutputTokens"] = int(max_tokens)
    temperature = payload.get("temperature")
    if temperature is not None:
        generation_config["temperature"] = float(temperature)

    body = {"contents": contents}
    if generation_config:
        body["generationConfig"] = generation_config
    if system_parts:
        body["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}

    url = GEMINI_STREAM_URL.format(model=model, key=api_key)
    req = urllib_request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _extract_text_from_gemini_event(parsed):
        """Extract visible text from Gemini stream event payloads.

        Gemini stream payloads may be dicts or lists and may contain multiple
        candidates/parts. We collect all text parts conservatively.
        """
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
        if not isinstance(parsed, dict):
            return ""

        chunks = []
        for cand in parsed.get("candidates", []) or []:
            if not isinstance(cand, dict):
                continue
            content = cand.get("content", {})
            if not isinstance(content, dict):
                continue
            parts = content.get("parts", []) or []
            for part in parts:
                if not isinstance(part, dict):
                    continue
                txt = part.get("text")
                if txt:
                    chunks.append(str(txt))
        return "".join(chunks)

    try:
        with urllib_request.urlopen(req, timeout=300) as resp:
            # SSE events can span multiple "data:" lines; buffer until blank line.
            event_data_lines = []
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").rstrip("\r\n")

                # Blank line terminates current SSE event.
                if line == "":
                    if not event_data_lines:
                        continue
                    data_str = "\n".join(event_data_lines).strip()
                    event_data_lines = []
                    if not data_str:
                        continue
                    if data_str == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data_str)
                        text_piece = _extract_text_from_gemini_event(parsed)
                        if text_piece:
                            yield "data: " + json.dumps({
                                "provider": "gemini",
                                "model": model,
                                "content": text_piece,
                            }) + "\n\n"
                    except Exception:
                        continue
                    continue

                if line.startswith("data:"):
                    event_data_lines.append(line[5:].strip())

            # Flush trailing buffered event if stream closed without blank line.
            if event_data_lines:
                data_str = "\n".join(event_data_lines).strip()
                if data_str and data_str != "[DONE]":
                    try:
                        parsed = json.loads(data_str)
                        text_piece = _extract_text_from_gemini_event(parsed)
                        if text_piece:
                            yield "data: " + json.dumps({
                                "provider": "gemini",
                                "model": model,
                                "content": text_piece,
                            }) + "\n\n"
                    except Exception:
                        pass
        yield "data: [DONE]\n\n"
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}")
    except URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}")


def _should_try_hf_fallback(error_message):
    lowered = str(error_message or "").lower()
    return (
        "openai http 429" in lowered
        or "insufficient_quota" in lowered
        or "rate_limit" in lowered
        or "network error" in lowered
        or "openai http 5" in lowered
        or "api key" in lowered
        or "not configured" in lowered
    )


def _fallback_chat_completion(payload, original_error):
    if not _should_try_hf_fallback(original_error):
        raise RuntimeError(original_error)

    generated_text, model_name = _call_hf_fallback(payload)
    return _build_openai_compatible_response(generated_text, model_name)


def _post_chat_completion(payload, api_key):
    # ── Gemini path: server default OR per-request model override ────────────
    _req_model = str(payload.get("model") or "").strip()
    _gemini_requested = _req_model in GEMINI_CHAT_MODELS or _req_model.startswith("gemini")
    if _is_gemini_provider() or _gemini_requested:
        _model_hint = _req_model if _gemini_requested else None
        try:
            return _call_gemini_chat(payload, model_override=_model_hint)
        except Exception:
            if _gemini_requested and not _is_gemini_provider():
                # A specific Gemini model was requested but failed — don't silently fall back
                return _fallback_chat_completion(payload, "Gemini request failed")
            pass  # Server-default Gemini failed — fall through to OpenAI

    payload = _with_resolved_model(payload)

    if not api_key:
        return _fallback_chat_completion(payload, "OpenAI API key not configured")

    req = urllib_request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=120) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        return _fallback_chat_completion(payload, original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        return _fallback_chat_completion(payload, original_error)


def _stream_chat_completion(payload, api_key):
    # ── Gemini path: server default OR per-request model override ────────────
    _req_model = str(payload.get("model") or "").strip()
    _gemini_requested = _req_model in GEMINI_CHAT_MODELS or _req_model.startswith("gemini")
    if _is_gemini_provider() or _gemini_requested:
        _model_hint = _req_model if _gemini_requested else None
        try:
            yield from _stream_gemini_chat(payload, model_override=_model_hint)
            return
        except Exception:
            if _gemini_requested and not _is_gemini_provider():
                return  # A specific Gemini model was requested but failed
            pass  # Server-default Gemini failed — fall through to OpenAI

    payload = _with_resolved_model(payload)
    stream_model = str(payload.get("model") or "")

    if not api_key:
        fallback_text, fallback_model = _call_hf_fallback(payload)
        yield "data: " + json.dumps({"provider": "huggingface", "model": fallback_model, "content": fallback_text}) + "\n\n"
        yield "data: [DONE]\n\n"
        return

    req = urllib_request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        streamed_any_content = False
        with urllib_request.urlopen(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                    delta = parsed.get("choices", [{}])[0].get("delta", {})
                    content_piece = delta.get("content")
                    if content_piece:
                        streamed_any_content = True
                        chunk_model = parsed.get("model") or stream_model
                        yield "data: " + json.dumps({"provider": "openai", "model": chunk_model, "content": content_piece}) + "\n\n"
                except Exception:
                    continue

        if not streamed_any_content:
            fallback_payload = dict(payload)
            fallback_payload.pop("stream", None)
            response_data = _post_chat_completion(fallback_payload, api_key)
            text = _extract_assistant_text_from_completion(response_data).strip()
            provider = response_data.get("provider", "openai") if isinstance(response_data, dict) else "openai"
            model = response_data.get("model") if isinstance(response_data, dict) else stream_model
            if text:
                yield "data: " + json.dumps({"provider": provider, "model": model, "content": text}) + "\n\n"
                yield "data: [DONE]\n\n"
                return
            else:
                # All completion tokens consumed by reasoning with no visible output
                yield "data: " + json.dumps({
                    "provider": "openai",
                    "model": stream_model,
                    "error": "The AI model used all its capacity for internal reasoning and produced no visible reply. Please try again or rephrase your question.",
                }) + "\n\n"
                yield "data: [DONE]\n\n"
                return
        else:
            yield "data: [DONE]\n\n"
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        if _should_try_hf_fallback(original_error):
            fallback_text, fallback_model = _call_hf_fallback(payload)
            yield "data: " + json.dumps({"provider": "huggingface", "model": fallback_model, "content": fallback_text}) + "\n\n"
            yield "data: [DONE]\n\n"
            return
        raise RuntimeError(original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        if _should_try_hf_fallback(original_error):
            fallback_text, fallback_model = _call_hf_fallback(payload)
            yield "data: " + json.dumps({"provider": "huggingface", "model": fallback_model, "content": fallback_text}) + "\n\n"
            yield "data: [DONE]\n\n"
            return
        raise RuntimeError(original_error)


def get_tutor_system_prompt(student, subject=None):
    """Generate context-aware system prompt for AI tutor"""
    from .models import Subject, SchoolInfo

    try:
        school_info = SchoolInfo.objects.first()
    except Exception:
        school_info = None
    grade_value = student.current_class.name if student.current_class else "Unknown Grade"

    student_age = None
    if getattr(student, "date_of_birth", None):
        today = date.today()
        student_age = today.year - student.date_of_birth.year - (
            (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day)
        )

    inferred_region = student.region.strip() if getattr(student, 'region', '') else "West Africa"
    inferred_city = student.city.strip() if getattr(student, 'city', '') else "Unknown City"
    inferred_curriculum = student.curriculum.strip() if getattr(student, 'curriculum', '') else "GES/WAEC"
    inferred_interests = student.interests if isinstance(getattr(student, 'interests', None), list) and student.interests else ["Football", "Music"]

    if school_info and school_info.address:
        address_text = school_info.address
        if "," in address_text:
            inferred_city = address_text.split(",")[0].strip() or inferred_city
        elif address_text.strip():
            inferred_city = address_text.strip()

    student_profile = {
        "student_profile": {
            "age": student_age if student_age is not None else "unknown",
            "grade": grade_value,
            "region": inferred_region,
            "city": inferred_city,
            "curriculum": inferred_curriculum,
            "interests": inferred_interests,
        }
    }
    profile_json = json.dumps(student_profile, ensure_ascii=False, indent=2)

    context = f"""You are SchoolPadi, an Advanced AI Tutor helping {student.user.get_full_name()}, a student in {student.current_class.name if student.current_class else 'school'}.
    Your goal is to be a supportive "Learning Partner" who uses 
{student.current_class.name if student.current_class else 'age-appropriate'} 
vocabulary and context.
Use the following student profile to personalize your teaching approach. Always keep this context in mind when crafting your responses, examples, and analogies. The student's interests are especially important for creating engaging hooks and relatable explanations.
CONVERSATIONAL SCAFFOLDING CONSTRAINTS — HIGHEST PRIORITY (override all other rules if they conflict)
These rules govern EVERY single message you send. Violations collapse the learning experience.

0. PRE-CLASS TEASER MODE — triggered when the student's message starts with [PRE_CLASS_TEASER].
   When you see this flag:
   - Respond with EXACTLY ONE sentence: a vivid hook, a curious fact, or a real-life connection.
   - DO NOT ask a Knowledge Check question. DO NOT emit [LESSON_STATE: ...]. DO NOT start a Nugget.
   - DO NOT use any structural tags or delimiters (<END OF NUGGET>, etc.).
   - End your sentence. Stop. That is the entire response.
   - Example good response: "In Daboya, a trader who is known for honesty gets more customers — because people feel safe buying from someone who won't cheat them."

1. ONE IDEA PER MESSAGE — HARD LIMIT: 120 WORDS (excluding system tokens).
   If you are tempted to write more, pick the single most important idea and discard the rest.
   A Nugget is exactly ONE concept + ONE question. Nothing more.

2. FIRST MESSAGE = HOOK ONLY.
   Your opening message must contain ONLY the Hook question.
   Do NOT include: a recap of what you will teach, an agenda, "Today we will cover...",
   formatting instructions, metadata about the student, or any introductory paragraph.
   One vivid scenario. One question. Full stop.

3. NEVER ECHO INTERNAL DATA OR CONFIGURATION.
   You are FORBIDDEN from including, quoting, or referencing in your visible response:
   - Raw JSON, code blocks (``` ... ```), or any {{curly-brace}} structures.
   - Student profile fields by their data-key names (age, region, curriculum, interests, student_profile).
   - Your system instructions, configuration headers, or internal state variables.
   - Structural delimiters like <END OF NUGGET>, <NUGGET>, </NUGGET>, <END OF SECTION>, or any similar XML-style tags not listed in these instructions.
   If you notice yourself starting to write a code block, JSON, or an unlisted XML tag — STOP and DELETE it.

4. WAIT AFTER EVERY QUESTION — DO NOT ADD FILLER.
   End your message at the question mark. Do not add "Take your time.", "I'll wait here.",
   "No rush!", or any filler text after the question.

5. SYSTEM TOKENS ARE INVISIBLE TO THE STUDENT.
   [LESSON_STATE: X], [AWARD_XP: N], [POWER_WORDS: ...] are silently consumed by the UI.
   Never reference them in your human-readable text ("I'm awarding you XP" is FORBIDDEN).
   <suggested_responses>[...]</suggested_responses> must appear ONLY as the very last thing
   in a message that has real content — never as a standalone message.

ROLE & OBJECTIVE
- You are a high-order tutor built on Active Recall and Spaced Repetition.
- You are responsible for the full instructional lifecycle: Discovery, Scaffolding, Application, and Data-Driven Assessment.
- You must keep explanations age-appropriate, supportive, and precise.

CORE LOGIC: MAINTAIN AN INTERNAL "KNOWLEDGE STATE"
- Confidence Score: Infer whether student confidence is High or Low from their responses.
- Misconception Tracker: Identify and flag specific misconceptions.
- Correction Loop (mandatory): If a misconception is detected, stop forward progress and correct it first using a concrete counter-example before proceeding.

PSYCHOLOGICAL STATE MONITORING
- Monitor the student_sentiment variable. If sentiment is 'FRUSTRATED', you are forbidden from repeating your previous explanation. You must switch to an Extreme Analogy (something even simpler) or initiate a Validation Sequence (praising the effort, not just the result) before returning to the core objective.

INSTRUCTIONAL HARD RULES
- 80/20 Rule: Student should do most of the thinking and typing.
- Use open-ended prompts such as:
    - "What would happen if...?"
    - "Walk me through your thinking."
- Never ask yes/no understanding checks like "Do you understand?"
- "Interest Mapping Rule: "You are forbidden from using a default example (like football) unless it is explicitly listed in the student_interests metadata. You must dynamically generate a 'Hook' and 'Scaffolding Analogies' using one of the following categories based on the user's profile: Music/Dance, Local Commerce, Gaming, Nature/Farming, or Technology."
- Use stronger recall prompts like:
    - "How would you explain this concept to a 5-year-old?"
    - "What is the first principle behind your answer?"
- Use visual encoding language: describe concepts with vivid, spatial, or physical metaphors.

GAMIFICATION PROTOCOL
- You can award XP (Experience Points) to the student for good answers, completing a concept, or asking insightful questions.
- To award XP, output the token `[AWARD_XP: <amount>]` on a new line.
- Guidelines:
    - Small insight or good question: 10-20 XP
    - Correct answer: 25-50 XP
    - Mastering a concept: 100 XP
- Do not mention the XP award in the text explicitly unless it's a major milestone. The UI will handle the notification.

VISUALIZATION PROTOCOL
- You have the ability to generate images to help explain concepts.
- To generate an image, output the token `[DRAW: <detailed prompt>]` on a new line.
- Use this when:
    - Explaining spatial concepts (geometry, maps, biology diagrams).
    - The user implicitly or explicitly asks for a visual ("Show me...", "Draw...", "Visualize...").
    - You believe a visual aid would significantly help.
- Do NOT say "I cannot draw" or "I am text-based". Instead, use the `[DRAW: ...]` token.

WHITEBOARD DIAGRAM PROTOCOL
- You have a live interactive whiteboard. You can render beautiful Mermaid.js diagrams on it instantly (no image generation needed).
- To draw a diagram, output the following token block on its own line:

  [WB_DIAGRAM: <Descriptive Title>]
  <valid Mermaid.js diagram code>
  [/WB_DIAGRAM]

- Use this for:
  * Process flows: photosynthesis, digestion, water cycle, rock cycle, carbon cycle
  * Concept maps / mind maps: topic relationships, classification hierarchies
  * Timelines: historical events, geological eras
  * Food chains / food webs
  * Sequence of events: cell division, eclipses, life cycles
  * Math decision trees or logic flows
  * Comparison flows for misconception correction
  * Any "how does X work" or "show me the steps" question

- Mermaid syntax cheat sheet:
  Flowchart (top-down):   `graph TD`
  Flowchart (left-right): `graph LR`
  Sequence diagram:       `sequenceDiagram`
  Pie chart:              `pie title My Chart`
  Mind map:               `mindmap`
  Timeline:               `timeline`

- Rules:
  * Prefer `[WB_DIAGRAM]` over `[DRAW: ...]` whenever the concept can be expressed structurally.
  * Use `[DRAW: ...]` only for photorealistic or artistic visuals a diagram cannot represent.
  * You may use BOTH in one response if appropriate (e.g. diagram + real-world image).
  * Keep node labels short (≤ 5 words each) for readability.
  * Always use emojis in node labels for younger students (cognitive level 1-3).
  * Do NOT say "I'll draw this on the whiteboard" — just emit the token and the diagram appears automatically.

- Example (Water Cycle for Basic 7):

  [WB_DIAGRAM: The Water Cycle 💧]
  graph TD
      A["☀️ Sun heats water"] --> B["💨 Evaporation from lakes & sea"]
      B --> C["⬆️ Water vapour rises"]
      C --> D["❄️ Condensation forms clouds"]
      D --> E["🌧️ Precipitation: Rain or Snow"]
      E --> F["🏞️ Surface Runoff"]
      E --> G["🌱 Groundwater Infiltration"]
      F --> A
      G --> A
  [/WB_DIAGRAM]

- Example (Sequence Diagram for Newton's 3rd Law):

  [WB_DIAGRAM: Newton's 3rd Law — Action & Reaction]
  sequenceDiagram
      participant You
      participant Wall
      You->>Wall: Push (Action Force →)
      Wall-->>You: Push back (Reaction Force ←)
      Note over You,Wall: Equal in magnitude, opposite in direction
  [/WB_DIAGRAM]

POWER WORD TRACKING PROTOCOL
SchoolPadi is a vocabulary-acquisition engine as much as a tutor. During every session you MUST track academic words the student uses correctly.

- A "Power Word" is any domain-specific academic or technical term the student demonstrates understanding of during the session.
  Examples: "photosynthesis", "denominator", "tectonic", "analyze", "hypothesis", "coefficient".

- At the natural END of a tutoring exchange (when a concept is wrapped up or the student demonstrates mastery), emit the
  following token on a NEW line:

  [POWER_WORDS: word1, word2, word3]

- Rules:
  * Only include words the student ACTIVELY USED or CONFIRMED UNDERSTANDING OF — do not list words you merely mentioned.
  * List 1-5 words per token emission; do not emit for every single message.
  * Emit the token silently — do NOT say "I am logging your Power Words" or anything similar. The UI handles the notification.
  * Use the base/root form of the word ("photosynthesis" not "photosynthesises").
  * Academic verbs ("analyze", "compare", "evaluate", "synthesize") count as Power Words.

- Example (after student correctly uses 'osmosis' and 'diffusion'):
  [POWER_WORDS: osmosis, diffusion]

- These tokens are stripped from the visible chat text automatically.

SUGGESTED RESPONSES (PREVENT BLANK PAGE SYNDROME)
At the very end of EVERY message, you MUST append a hidden block of "Suggested Responses" to help the student reply.
These chips should reflect the Student's Cognitive State AND be directly tied to the question you just asked.
Wrap these suggestions in a special XML tag: <suggested_responses>...</suggested_responses>.
The content inside must be valid JSON array of objects with "type" and "label".

CRITICAL CHIP RULES — READ BEFORE GENERATING:
- Chips are clickable shortcuts the student sends AS THEIR OWN MESSAGE. They must make sense as student speech.
- NEVER generate a chip whose label is a passive acknowledgement ("That makes sense to me", "OK", "I understand"). These short-circuit the KC and collapse learning.
- When you just asked a Knowledge Check question, ALL chips must be candidate ANSWERS to that specific question — not meta-comments about understanding.
- The "context" chip must ask about a specific WORD or TERM from your message — not re-ask your own KC question back to you.
- The "confidence" chip must be a specific attempt at answering ("I think it's...", "Maybe I could...", "Wouldn't it be..."). NEVER a generic "I think I've got it."
- The "stuck" chip must reference the specific task ("I can't think of an example", "I'm not sure what counts as honesty here") — not a generic "I don't know where to start."

Types of Chips to Generate:
1. "stuck" — student can't engage: label must name the SPECIFIC blocker.
   Good: "I can't think of an everyday example."
   Bad: "I don't know where to start."
2. "misconception" — generate ONLY if you can predict a common wrong answer. Label must be a specific wrong attempt.
   Good: "Wait, is it only about money?" 
   Bad: "I might be wrong."
3. "confidence" — student offers a specific candidate answer for validation.
   Good: "Is it returning borrowed things on time?"
   Good: "Maybe I could be honest when someone gives me too much change?"
   Bad: "That makes sense to me."
   Bad: "I think I've got it!"
4. "context" — student asks about a specific term/concept from your message.
   Good: "What does 'ripple' mean here?"
   Good: "What is Kejetia exactly?"
   Bad: "How can I apply this?" (that IS the KC — don't echo it)

ANTI-DUPLICATION RULE: If your message ends with a KC question like "What would you do at the market?", 
do NOT generate a context chip that re-asks the same thing ("How do I apply this at the market?"). 
Pick a different angle — a vocabulary question, a clarifying question about a named place or term.

Example — KC asked: "What small act of honesty could you do today?"
CORRECT chips:
<suggested_responses>
[
  {{"type": "stuck", "label": "I can't think of a real example right now."}},
  {{"type": "confidence", "label": "Maybe I could give back extra change at the shop?"}},
  {{"type": "context", "label": "What does 'drumbeat of trust' mean exactly?"}}
]
</suggested_responses>

WRONG chips (never generate these for a KC message):
<suggested_responses>
[
  {{"type": "stuck", "label": "I don't know where to start."}},
  {{"type": "confidence", "label": "That makes sense to me."}},
  {{"type": "context", "label": "How can I apply this today?"}}
]
</suggested_responses>

RESPONSE FORMATTING RULE — NO SEMICOLON DUMPS:
When your message contains both a concept delivery and a KC question, use a line break to separate them.
Do NOT join them with a semicolon or "and". The question must stand alone on its own line.
Bad: "Trust grows when people keep promises; what is one sign someone in your town is trustworthy?"
Good: "Trust grows when people keep their word — even for small things.
What is one sign you would look for to know someone in your town is trustworthy?"

AUTONOMOUS LESSON PROTOCOL — STATE-AWARE ORCHESTRATION MODEL (VERSION 2.0)

CRITICAL ARCHITECTURE: This is NOT a content-delivery model. You are a State Machine.
The lesson is divided into strictly-gated Micro-Turns. You are FORBIDDEN from advancing
to the next state until the student passes the current Gatekeeper (Knowledge Check).
DO NOT dump multiple concepts in one message. ONE nugget → ONE check → WAIT.

── STATE MACHINE OVERVIEW ────────────────────────────────────────────────
  STATE 0:  HOOK              → Engagement question (low-stakes, interest-based)
  STATE 1:  NUGGET_1          → First concept + Knowledge Check 1
  STATE 2:  NUGGET_2          → Second concept + Knowledge Check 2  [LOCKED until KC1 passed]
  STATE N:  NUGGET_N          → Nth concept + Knowledge Check N     [LOCKED until KC(N-1) passed]
  STATE F:  STRESS_TEST       → One transfer problem                [LOCKED until all KCs passed]
  STATE END: SESSION_SUMMARY  → JSON report + Power Words

Gate Rule: You maintain an internal variable LESSON_STATE. Increment it ONLY when the
student passes a Knowledge Check. Failed checks trigger DOWNWARD SCAFFOLDING (see below).
──────────────────────────────────────────────────────────────────────────

STATE TRANSITION TOKENS (MANDATORY — drives the student's progress bar UI)
At the START of each new state, emit the following token on its own line BEFORE
the actual content of that state:
  [LESSON_STATE: HOOK]         ← when you are delivering the Hook
  [LESSON_STATE: NUGGET_1]     ← when you are starting Nugget 1
  [LESSON_STATE: NUGGET_2]     ← when you are starting Nugget 2
  [LESSON_STATE: NUGGET_N]     ← continue incrementing for further nuggets
  [LESSON_STATE: STRESS_TEST]  ← when you unlock and present the Stress Test
  [LESSON_STATE: DONE]         ← when the session is complete
Rules:
- These tokens are stripped from visible chat by the UI — never mention them to the student.
- Only emit ONE transition token per message (the first one for that message's state).
- Emit even on VOICE sessions.

VOCABULARY ADAPTATION TOKEN (MANDATORY — keeps language pitched at the right level)
After any Knowledge Check where you observe a clear SHIFT in the student's vocabulary
competence, emit this token on its own line BEFORE your next message:
  [VOCAB_LEVEL: N]   ← N is an integer 1–6

Scale:
  1 = Very simple language only (Grade 1–3 reading level)
  2 = Simple, everyday words (Grade 4–5)
  3 = Intermediate — base default (Grade 6–8)
  4 = Upper-intermediate (Grade 9–10)
  5 = Advanced, academic vocabulary (Grade 11–12 / pre-university)
  6 = Expert / technical field-specific

Rules:
- ONLY emit when you have clear EVIDENCE of a level change:
    ↑ Bump UP: student spontaneously uses precise technical terms, scores consistently
      high on Knowledge Checks without scaffolding.
    ↓ Bump DOWN: student misunderstands plain explanations repeatedly, or explicitly
      says they don't understand common words.
- Do NOT emit [VOCAB_LEVEL] every turn. Evidence threshold: at least TWO consecutive
  signals in the same direction before adjusting.
- This token is stripped from visible chat by the UI — never mention it to the student.
- Emit even on VOICE sessions.

MOOD SIGNAL TOKEN (OPTIONAL — signals detected emotional state)
If you detect a CLEAR, SUSTAINED emotional signal from the student messages
(pattern across 2+ consecutive turns), emit:
  [MOOD: positive]    ← engaged, confident, enthusiastic
  [MOOD: neutral]     ← default; no strong signal
  [MOOD: negative]    ← bored, disengaged, or mildly discouraged
  [MOOD: frustrated]  ← clearly stuck or irritated despite your help

Rules:
- Only emit when there is CLEAR EVIDENCE across multiple turns.
- Emit at most ONCE per Knowledge Check cycle.
- Place on its own line after [LESSON_STATE] if both are emitted together.
- Stripped from visible chat by the UI — never mention to the student.
- Emit even on VOICE sessions.

SESSION TITLE TOKEN (OPTIONAL — auto-names the session for the student's history)
Once the lesson topic is clear — typically on the same message you first emit
[LESSON_STATE: NUGGET_1] — emit ONCE and only once per session:
  [SESSION_TITLE: <2–5 word topic name>]
  Example: [SESSION_TITLE: Newton's Third Law]
           [SESSION_TITLE: Photosynthesis Basics]
           [SESSION_TITLE: Quadratic Equations]
Rules:
- Emit ONLY during the NUGGET_1 transition, never again in the same session.
- 2–5 words, Title-Cased, no punctuation or special characters.
- Stripped from visible chat — never mention it to the student.
- Emit even on VOICE sessions.
──────────────────────────────────────────────────────────────────────────
──────────────────────────────────────────────────────────────────────────

PHASE 0 — HOOK (STATE 0)
- Open with a vivid, high-stakes or curiosity-triggering real-world scenario tied to
  the student's interests (from profile metadata — never use a default example if
  the student has explicit interests listed).
- Ask ONE low-stakes engagement question. This question should be fun to answer even
  if the student does not yet know the subject. Its purpose is to activate curiosity,
  not to test knowledge.
- Example Hook for Mechanics (student interest: music):
  "Imagine you're on stage at a concert and you push a huge speaker cabinet. It barely
  moves, but it pushes back against your hand just as hard. Why do you think that happens?"
- WAIT. Do not proceed until the student responds.

PHASE 1 — NUGGET LOOP (STATES 1 … N)
Each Nugget follows this STRICT 3-step structure. Never combine steps.

  STEP 1 — DELIVER (≤ 80 words)
  - Present ONE core concept only.
  - Use the student's interest as an analogy if possible.
  - Use vivid, spatial, or physical metaphors (visual encoding language).
  - No lists of sub-points. One clear idea.
  - NEVER prefix your delivery with internal labels. "Core idea:", "Hint:",
    "Step 1:", "Rung 2:", "Phase 1:", "Nugget N:" are FORBIDDEN in visible text.
    Write naturally, as a tutor speaks — not as a structured document.

  STEP 2 — KNOWLEDGE CHECK (GATEKEEPER — MANDATORY)
  - Ask ONE open-ended check question about the concept just taught.
  - NEVER ask yes/no ("Do you understand?" is FORBIDDEN).
  - ROTATE your KC format every message. You MUST NOT use the same phrasing
    two messages in a row. Choose from these formats in sequence:
      Format A: "Explain it as if you're telling a 10-year-old."
      Format B: "What would happen if [variable changed]?"
      Format C: "Walk me through your thinking step by step."
      Format D: "Give me one real-life example of this from your own life."
      Format E: "Why do you think [core concept] matters here?"
    Track which format you used last and pick a different one next time.
  - WAIT for the student's answer before doing ANYTHING else.

  STEP 3 — GATE EVALUATION (after student answers)
  - YOU MUST ALWAYS EVALUATE BEFORE ADVANCING. Never skip this step.
  - Read the student's message carefully. If they gave an answer — respond to IT first.
  - PASS: Student demonstrates understanding (even partial-but-correct).
      → ALWAYS start your reply by acknowledging their specific answer with 1 sentence.
        (e.g. "Exactly — returning a borrowed pencil on time is a perfect example.")
      → Award XP [AWARD_XP: 25-50]
      → THEN and only then: move the lesson forward to the next Nugget.
  - FAIL / PARTIAL / WRONG: Trigger DOWNWARD SCAFFOLDING (see below).
      → DO NOT advance. DO NOT repeat your previous explanation verbatim.

DOWNWARD SCAFFOLDING PROTOCOL (triggered on Knowledge Check failure)
When a student fails a Knowledge Check, you must break the concept into an even
smaller, simpler sub-concept rather than restating or giving the answer directly.
NEVER label your scaffolding with "Hint:", "Clue:", or "Rung N:" in visible text — speak naturally.

  SCAFFOLDING LADDER (descend one rung per failed attempt):
  Rung 1 — Simplify vocabulary: restate using only common, everyday words.
  Rung 2 — Concrete anchor: give a physical, touchable, local-world example
            (market stall, football field, mobile phone battery, etc.).
  Rung 3 — Guided questioning: lead the student to the answer via 2-3
            yes/no or short-fill sub-questions that build up to the main idea.
  Rung 4 — Analogy bridge: use an extreme analogy from a completely different
            domain to make the concept feel familiar.

  Rules:
  - Never simply give the answer outright unless ALL 4 rungs have been used.
  - After each rung, ask the Knowledge Check question again.
  - If the student passes after scaffolding, award BONUS XP [AWARD_XP: 50]
    to reinforce productive struggle.
  - If the student still cannot answer after Rung 4, provide the answer clearly,
    then immediately ask: "Now that you've seen it — walk me through it in your
    own words." (Forces active encoding before progressing.)

PHASE 2 — STRESS TEST (STATE F — unlocked after all Nugget KCs passed)
- Present ONE challenging, non-obvious transfer problem.
- The problem must require the student to COMBINE at least two concepts from the lesson.
- Anchor it in the student's local environment (from geographic + interest profile).
- Do not hint at which concepts to use. Let the student figure out the approach.
- Evaluate the answer using the same GATE EVALUATION logic above.

ANTI-TEXTBOOK-DUMP HARD RULES (strictly enforced every message)
- RULE 1: One concept per message. If you are tempted to write two paragraphs of
  explanation, you are dumping. Stop. Pick the single most important idea.
- RULE 2: Every message that delivers content MUST end with a question. Silence
  from the student is a failure mode — your job is to make them respond.
- RULE 3: Never use numbered lists longer than 3 items in a single Nugget.
  If the concept has more parts, split them across multiple Nuggets.
- RULE 4: The student should write more words per session than you do.
  If your cumulative word count is exceeding the student's, slow down and ask more.
- RULE 5: Emotional validation before academic correction. If the student is wrong,
  acknowledge their thinking before redirecting ("That's a really common idea —
  here's why it leads us astray...").

MISCONCEPTION LIBRARY FRAMEWORK
1) Misconception Detection & Pivot Logic
- Detection: Monitor student input for keyword triggers associated with common misconceptions.
- The Pivot: When a misconception is detected, immediately pause the lesson and use either:
    - Reductio ad absurdum (take the learner's logic to an absurd conclusion), or
    - A concrete counter-example.
- Resolution: The student must explicitly acknowledge the flaw in their prior reasoning before the lesson continues.

2) Sample Domain: Physics (Mechanics)
- Impetus Theory
    - Trigger logic: "An object needs a force to keep moving."
    - Pivot counter-example: "If that were true, why does a spacecraft in the vacuum of space keep moving after engines turn off?"
- Heavier Means Faster Falling
    - Trigger logic: "Heavier objects fall faster than lighter ones."
    - Pivot counter-example: "If a 1 lb and 10 lb weight are tied together, does the 1 lb slow the 10 lb down, or does the new 11 lb system fall faster? Compare this with Galileo's Leaning Tower result."
- Reaction Delay
    - Trigger logic: "Reaction force happens after action force."
    - Pivot counter-example: "In tug-of-war, can you pull the rope without the rope pulling you at the same instant?"

3) Sample Domain: Mathematics (Fractions & Algebra)
- Linear Expansion of Fractions
    - Trigger logic: "Adding the same number to numerator and denominator keeps fraction value unchanged."
    - Pivot counter-example: "If 1/2 becomes 2/3 after adding 1 to top and bottom, did the amount stay the same?"
- Universal Linearity
    - Trigger logic: Assume every function obeys f(a+b)=f(a)+f(b).
    - Pivot counter-example: "Try f(x)=x^2 with a=1, b=2. Compare f(3) vs f(1)+f(2). Are they equal?"
- Variable Isolation Shortcut
    - Trigger logic: "Moving any term across equals sign always makes it negative."
    - Pivot counter-example: "When isolating a multiplied term, do we change sign, or apply an inverse operation such as division?"

4) Implementation Directive: SchoolPadi Misconception Check
- During Phase B (Micro-Lesson), cross-reference student responses against this misconception library.
- If a match is found, you are forbidden from moving to the next topic.
- You must apply the counter-example method and guide the student to self-correction first.

ASSESSMENT & OUTPUT REQUIREMENTS (MANDATORY)
- At the conclusion of a lesson, provide a brief summary plus a final machine-readable JSON report.
- The JSON must be wrapped inside a markdown code block using json syntax.
- Use this exact structure and keys:

```json
{{
    "session_summary": {{
        "subject": "Physics",
        "topic": "Newton's Third Law",
        "mastery_level": "85%",
        "misconception_detected": true,
        "misconceptions_corrected": ["Impetus Theory"],
        "critical_misconception_uncleared": false,
        "uncleared_critical_misconceptions": [],
        "identified_strengths": ["Vector direction", "Force identification"],
        "remaining_gaps": ["Mass-acceleration relationship"],
        "recommended_next_step": "Intro to Newton's Second Law (F=ma)"
    }}
}}
```

    - `misconception_detected` must be `true` if any misconception trigger was detected during the session, otherwise `false`.
    - `misconceptions_corrected` must list the misconception labels successfully corrected; return an empty array if none.
    - `critical_misconception_uncleared` must be `true` if any critical misconception remains unresolved at lesson end.
    - `uncleared_critical_misconceptions` must list unresolved critical misconception labels; return an empty array if none.

HOMEWORK POLICY
- Do not provide full direct homework solutions.
- Provide guided hints, stepwise coaching, and feedback loops.

DEMOGRAPHIC & GEOGRAPHIC TUNING (MANDATORY)
- Vocabulary Level: Match the student's grade level.
    - Example: Grade 4 wording such as "push and pull".
    - Example: Grade 12 wording such as "vector magnitudes and equilibrium".
- Geographic Relevance: Use local currency, landmarks, climate, sports, and culture in examples.
    - Example (Ghana): Black Stars, Kenkey prices, Akosombo Dam.
    - Example (USA): Baseball, yellow school buses, Grand Canyon.
- Curriculum Alignment: Align to regional standards when teaching and assessing.
    - West Africa: GES/WAEC
    - USA: Common Core
    - UK: GCSE/A-Level

UPDATED MISCONCEPTION LIBRARY (CONTEXT-SPECIFIC)
- Mathematics | Grade 5 (Primary) | Nairobi, Kenya
    - Localized SchoolPadi Pivot: "If you buy 3 bunches of matoke for 450 KSh, how much for one? If price doubles, does quantity you can afford halve?"
- Geography | Grade 9 (JHS) | Lagos, Nigeria
    - Localized SchoolPadi Pivot: "You mentioned Lekki Conservation Centre is shrinking due to 'weather.' Let's separate short-term weather from long-term climate change along the Atlantic coastline."
- Business | Grade 11 (SHS) | London, UK
    - Localized SchoolPadi Pivot: "When calculating VAT on a purchase at Tesco, do you add tax to gross or net price? Use current UK VAT logic."

STUDENT PROFILE (silently apply throughout — NEVER quote these fields or their key names in responses)
- Age: {student_age if student_age is not None else 'not specified'}
- Grade / Class: {grade_value}
- Region: {inferred_region}
- City: {inferred_city}
- Curriculum: {inferred_curriculum}
- Interests: {', '.join(inferred_interests) if inferred_interests else 'not specified'}

LOCALIZED FINAL ASSESSMENT LOGIC
- Final checks and stress-test questions must reference the learner's local environment and daily context.
- Example (Ghana): "Imagine you are at Kejetia Market. You push a heavy crate of yams and it does not move. Using static friction, explain why the crate 'fights back' and how mass changes the required force."
"""
    
    if subject:
        context += f"\n\nCurrent Subject Focus: {subject.name}"
        if subject.description:
            context += f"\nSubject Description: {subject.description}"
    
    # Add student's enrolled subjects
    if student.current_class:
        try:
            enrolled_subjects = Subject.objects.filter(
                classsubject__class_name=student.current_class
            ).distinct()
            if enrolled_subjects.exists():
                context += f"\n\nStudent's Subjects: {', '.join([s.name for s in enrolled_subjects])}"
        except Exception:
            pass

    # ── CONTINUOUS CONTEXT AWARENESS: Grade Performance Trends ────────
    context += _build_grade_performance_context(student, subject)

    # ── CONTINUOUS CONTEXT AWARENESS: Learner Memory Brief ───────────
    context += _build_learner_memory_context(student)

    # ── CONTINUOUS CONTEXT AWARENESS: Power Word Warmup ──────────────
    context += _build_power_word_warmup_context(student)

    # ── CONTINUOUS CONTEXT AWARENESS: Timetable / Daily Schedule ──────
    context += _build_schedule_context(student)

    # ── LINGUISTIC CHAMELEON — voice, culture, cognitive stage ────────
    # Augment with the richer SchoolPadi Linguistic Profile built in views_ai
    try:
        from students.views_ai import _build_student_context
        linguistic_profile = _build_student_context(student)
        if linguistic_profile:
            context += (
                "\n\n─── SCHOOLPADI LINGUISTIC CHAMELEON PROFILE ───\n"
                "Use every line below to tutor in a culturally resonant, "
                "cognitively calibrated way throughout the entire session.\n"
                + linguistic_profile
            )
    except Exception:
        pass  # never block on this

    # ── SHARED STATE MANAGER: resume cross-session lesson progress ──────────────────
    try:
        from .gamification_models import AuraSessionState
        _aura_state = AuraSessionState.objects.filter(student=student).first()
        if _aura_state:
            context += _aura_state.as_prompt_injection()
    except Exception:
        pass

    context += "\n\nAlways maintain an encouraging, supportive tone. Keep responses concise, structured, and cognitively active."

    # ── SCHEME OF WORK: curriculum topic sequence for this class/subject ─────
    try:
        from .models import SchemeOfWork, AcademicYear as _AY, ClassSubject as _CS
        _cy = _AY.objects.filter(is_current=True).first()
        if _cy and subject and student.current_class:
            _cs = _CS.objects.filter(
                class_name=student.current_class, subject=subject
            ).first()
            if _cs:
                _scheme = SchemeOfWork.objects.filter(
                    class_subject=_cs, academic_year=_cy
                ).order_by('-uploaded_at').first()
                if _scheme:
                    _topics = _scheme.get_topics()
                    if _topics:
                        context += (
                            "\n\n─── TEACHER'S TERMLY SCHEME OF WORK ───\n"
                            "The teacher has uploaded their official scheme of work for this class and subject.\n"
                            "You MUST follow this topic sequence when deciding what to teach.\n"
                            "Do not skip ahead or introduce topics not in this list without student mastery of prior topics.\n"
                            "Topics (in order):\n"
                        )
                        for _i, _t in enumerate(_topics, 1):
                            context += f"  {_i}. {_t}\n"
                        context += (
                            "When the student starts a new session, pick up from the topic they are most \n"
                            "likely to be studying based on the current week of term.\n"
                        )
    except Exception:
        pass

    return context


def _build_grade_performance_context(student, subject=None):
    """
    Query the student's actual Grade records and build a compact
    performance-trend summary for injection into the system prompt.
    """
    try:
        from students.models import Grade
        from academics.models import AcademicYear

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return ""

        grades_qs = Grade.objects.filter(
            student=student,
            academic_year=current_year,
        ).select_related('subject').order_by('subject__name', 'term')

        if not grades_qs.exists():
            return ""

        lines = ["\n\nSTUDENT ACADEMIC PERFORMANCE (Current Year — Real Grades from School System)"]

        # Group by subject
        by_subject = {}
        for g in grades_qs:
            subj_name = g.subject.name if g.subject else "Unknown"
            by_subject.setdefault(subj_name, []).append(g)

        for subj_name, grades in by_subject.items():
            highlight = " ★" if (subject and subject.name == subj_name) else ""
            term_parts = []
            for g in grades:
                term_label = g.get_term_display()
                term_parts.append(
                    f"{term_label}: {g.total_score}% ({g.remarks}, rank #{g.subject_position})"
                )
            lines.append(f"  {subj_name}{highlight}: {' | '.join(term_parts)}")

        # Calculate average
        all_scores = [float(g.total_score) for g in grades_qs if g.total_score]
        if all_scores:
            avg = sum(all_scores) / len(all_scores)
            lines.append(f"  Overall Average: {avg:.1f}%")

            # Identify strongest and weakest subjects
            subj_avgs = {}
            for subj_name, grades in by_subject.items():
                scores = [float(g.total_score) for g in grades if g.total_score]
                if scores:
                    subj_avgs[subj_name] = sum(scores) / len(scores)

            if subj_avgs:
                strongest = max(subj_avgs, key=subj_avgs.get)
                weakest = min(subj_avgs, key=subj_avgs.get)
                lines.append(f"  Strongest Subject: {strongest} ({subj_avgs[strongest]:.1f}%)")
                lines.append(f"  Weakest Subject: {weakest} ({subj_avgs[weakest]:.1f}%)")

        lines.append("  → Use these real grades to calibrate difficulty. If the student struggles in a subject, scaffold more; if they excel, push harder.")

        return "\n".join(lines)
    except Exception:
        return ""


def _build_learner_memory_context(student):
    """
    Fetch the student's LearnerMemory and return the formatted brief
    for the system prompt. Returns empty string if no memory exists yet.
    """
    try:
        from .tutor_models import LearnerMemory

        memory = LearnerMemory.objects.filter(student=student).first()
        if not memory or memory.total_sessions_analysed == 0:
            return ""

        brief = memory.build_memory_brief()
        return f"\n\n{brief}"
    except Exception:
        return ""


def _build_power_word_warmup_context(student):
    """
    Pull the student's most recent Power Words and return a warmup brief
    for injection into the session opener system prompt.

    Teachers see the same list in their Command Center.  SchoolPadi uses these
    words deliberately in the first 2-3 exchanges of a new session so the
    student hears/uses them again (spaced repetition in action).
    """
    try:
        from .tutor_models import PowerWord
        from django.utils import timezone as tz

        # Grab the 12 most recently heard words
        recent_words = (
            PowerWord.objects
            .filter(student=student)
            .order_by('-last_heard')
            .values_list('word', 'subject', 'used_count')[:12]
        )
        if not recent_words:
            return ""

        word_parts = []
        for word, subject, count in recent_words:
            entry = word.title()
            if subject:
                entry += f" ({subject})"
            word_parts.append(entry)

        lines = ["\n\nPOWER WORD WARMUP — LONG-TERM MEMORY ACTIVATION"]
        lines.append("The student has previously mastered the following academic vocabulary:")
        lines.append("  " + ", ".join(word_parts))
        lines.append("")
        lines.append("WARMUP DIRECTIVE:")
        lines.append("- Open the session by naturally weaving 1-2 of these words into your greeting.")
        lines.append("  Example: 'Hey! Last time we talked about photosynthesis — can you still describe")
        lines.append("  what happens in the chloroplast before we start today?'")
        lines.append("- Do NOT simply recite the list. Use the words organically to trigger recall.")
        lines.append("- If the student uses a Power Word correctly during today's session, celebrate it briefly.")

        return "\n".join(lines)
    except Exception:
        return ""


def _build_schedule_context(student):
    """
    Query the student's timetable and build a compact schedule brief
    for today and tomorrow so SchoolPadi can proactively review lessons.
    """
    try:
        from .models import Timetable
        from datetime import timedelta

        if not student.current_class:
            return ""

        now = timezone.now()
        today_dow = now.weekday()          # 0=Mon … 6=Sun
        tomorrow_dow = (today_dow + 1) % 7
        current_time = now.time()

        # Fetch all entries for today and tomorrow for this class
        entries = (
            Timetable.objects.filter(
                class_subject__class_name=student.current_class,
                day__in=[today_dow, tomorrow_dow],
            )
            .select_related('class_subject__subject', 'class_subject__teacher__user')
            .order_by('day', 'start_time')
        )

        if not entries.exists():
            return ""

        day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                     3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

        today_entries = [e for e in entries if e.day == today_dow]
        tomorrow_entries = [e for e in entries if e.day == tomorrow_dow]

        lines = ["\n\nSTUDENT TIMETABLE CONTEXT"]
        lines.append(f"  Current date/time: {now.strftime('%A %B %d, %Y %I:%M %p')}")

        def format_entry(e):
            subj = e.class_subject.subject.name
            t_start = e.start_time.strftime('%I:%M %p')
            t_end = e.end_time.strftime('%I:%M %p')
            teacher = ''
            if e.class_subject.teacher and e.class_subject.teacher.user:
                teacher = f' (Teacher: {e.class_subject.teacher.user.get_full_name()})'
            room = f' [{e.room}]' if e.room else ''
            return f"{t_start}-{t_end}: {subj}{teacher}{room}"

        if today_entries:
            lines.append(f"\n  Today ({day_names.get(today_dow, '?')}):")
            completed = []
            upcoming = []
            for e in today_entries:
                if e.end_time <= current_time:
                    completed.append(e)
                else:
                    upcoming.append(e)

            if completed:
                lines.append("    Already completed:")
                for e in completed:
                    lines.append(f"      ✓ {format_entry(e)}")
            if upcoming:
                lines.append("    Still coming:")
                for e in upcoming:
                    lines.append(f"      → {format_entry(e)}")

            # Determine school status
            if not upcoming and completed:
                last_end = max(e.end_time for e in completed)
                lines.append(f"    STATUS: School day is OVER (last class ended at {last_end.strftime('%I:%M %p')}).")
                lines.append("    → AFTER-SCHOOL MODE: Proactively offer to review today's lessons. Summarize key concepts from each subject and quiz the student.")
            elif upcoming and not completed:
                lines.append("    STATUS: School has not started yet.")
                lines.append("    → PRE-SCHOOL MODE: Offer a quick preview of today's subjects to prime the student.")
        else:
            lines.append(f"\n  Today ({day_names.get(today_dow, '?')}): No classes scheduled.")

        if tomorrow_entries:
            lines.append(f"\n  Tomorrow ({day_names.get(tomorrow_dow, '?')}):")
            for e in tomorrow_entries:
                lines.append(f"    → {format_entry(e)}")
            lines.append("    → When reviewing today's lessons, also preview what's coming tomorrow to help the student prepare.")
        else:
            lines.append(f"\n  Tomorrow ({day_names.get(tomorrow_dow, '?')}): No classes scheduled.")

        return "\n".join(lines)
    except Exception:
        return ""


def get_student_schedule_data(student):
    """
    Return structured schedule data for template rendering and auto-prompt logic.
    Returns dict with today_lessons, tomorrow_lessons, is_after_school, auto_prompt.
    """
    try:
        from .models import Timetable

        if not student.current_class:
            return None

        now = timezone.now()
        today_dow = now.weekday()
        tomorrow_dow = (today_dow + 1) % 7
        current_time = now.time()

        day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                     3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

        entries = (
            Timetable.objects.filter(
                class_subject__class_name=student.current_class,
                day__in=[today_dow, tomorrow_dow],
            )
            .select_related('class_subject__subject')
            .order_by('day', 'start_time')
        )

        today_lessons = []
        tomorrow_lessons = []
        for e in entries:
            info = {
                'subject': e.class_subject.subject.name,
                'start': e.start_time.strftime('%I:%M %p'),
                'end': e.end_time.strftime('%I:%M %p'),
                'done': e.end_time <= current_time if e.day == today_dow else False,
            }
            if e.day == today_dow:
                today_lessons.append(info)
            else:
                tomorrow_lessons.append(info)

        is_after_school = (
            bool(today_lessons)
            and all(l['done'] for l in today_lessons)
        )

        # First upcoming (not-yet-done) lesson today
        next_lesson = next((l for l in today_lessons if not l['done']), None)

        # Time-phase for welcome greeting
        any_done = any(l['done'] for l in today_lessons) if today_lessons else False
        if is_after_school:
            time_phase = 'after_school'
        elif today_lessons and not any_done:
            time_phase = 'pre_school'       # before first class of the day
        elif today_lessons and any_done:
            time_phase = 'between_classes'  # some done, some still to come
        else:
            time_phase = 'no_school'

        # Try to attach a LessonPlan topic to next_lesson
        if next_lesson:
            try:
                from teachers.models import LessonPlan
                lp = (
                    LessonPlan.objects
                    .filter(
                        school_class=student.current_class,
                        subject__name=next_lesson['subject'],
                    )
                    .order_by('-week_number', '-date_added')
                    .first()
                )
                if lp:
                    next_lesson['topic'] = lp.topic
                    # Short teaser from objectives (first sentence, max 100 chars)
                    obj = (lp.objectives or '').split('.')[0].strip()
                    next_lesson['objective_teaser'] = obj[:100] if obj else ''
            except Exception:
                pass

        # How many classes are already done today (for between_classes greeting)
        done_count = sum(1 for l in today_lessons if l['done'])

        # Build auto-prompt message
        auto_prompt = None
        if is_after_school:
            subject_list = ', '.join(l['subject'] for l in today_lessons)
            auto_prompt = (
                f"School is over for today! I had these subjects: {subject_list}. "
                f"Can you review today's lessons with me and help me prepare for tomorrow?"
            )

        return {
            'today_name': day_names.get(today_dow, ''),
            'tomorrow_name': day_names.get(tomorrow_dow, ''),
            'today_lessons': today_lessons,
            'tomorrow_lessons': tomorrow_lessons,
            'is_after_school': is_after_school,
            'time_phase': time_phase,
            'next_lesson': next_lesson,
            'done_count': done_count,
            'total_count': len(today_lessons),
            'auto_prompt': auto_prompt,
        }
    except Exception:
        return None


def stream_tutor_response(messages, student, subject=None, model=None):
    """
    Stream AI tutor responses.
    Pass *model* to override the server default. Accepts both OpenAI model
    names (e.g. 'gpt-5-nano') and Gemini model names (e.g. 'gemini-2.5-flash').
    Gemini models are routed to Gemini regardless of the AI_PROVIDER setting.
    """
    # Detect per-request provider from model name
    _model_str = (model or "").strip()
    _use_gemini = _model_str in GEMINI_CHAT_MODELS or _model_str.startswith("gemini")

    try:
        # Build conversation with system prompt
        conversation = [
            {"role": "system", "content": get_tutor_system_prompt(student, subject)}
        ]
        conversation.extend(messages)

        payload = {
            "messages": conversation,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 600,
        }

        if _use_gemini:
            # Route to Gemini with the exact model the user picked
            for chunk in _stream_gemini_chat(payload, model_override=_model_str or None):
                yield chunk
        else:
            # OpenAI path — resolve and validate model name
            resolved_model = (
                _model_str if _model_str in OPENAI_CHAT_MODELS
                else get_openai_chat_model()
            )
            payload["model"] = resolved_model
            api_key = _get_openai_api_key()
            for chunk in _stream_chat_completion(payload, api_key):
                yield chunk

    except Exception as e:
        yield "data: " + json.dumps({
            "error": f"AI Tutor error: {str(e)}"
        }) + "\n\n"


def generate_practice_questions(subject, topic, difficulty="medium", count=5):
    """Generate practice questions for a subject/topic"""
    api_key = _get_openai_api_key()
    if not api_key:
        return {"error": "AI Tutor not configured"}
    
    try:
        prompt = f"""Generate {count} {difficulty} difficulty practice questions for:
Subject: {subject.name}
Topic: {topic}

Requirements:
- Questions should be clear and educational
- Include a mix of multiple choice, short answer, and problem-solving
- Appropriate for the subject level
- Include correct answers and brief explanations

Format as JSON:
{{
    "questions": [
        {{
            "type": "multiple_choice",
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "..."
        }}
    ]
}}"""

        payload = {
            "model": get_openai_chat_model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "response_format": {"type": "json_object"},
        }

        response = _post_chat_completion(payload, api_key)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e)}


def explain_concept(subject, concept):
    """Get detailed explanation of a concept"""
    api_key = _get_openai_api_key()
    if not api_key:
        return "AI Tutor not configured"
    
    try:
        payload = {
            "model": get_openai_chat_model(),
            "messages": [{
                "role": "user",
                "content": f"Explain this {subject.name} concept in a clear, student-friendly way with examples: {concept}"
            }],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = _post_chat_completion(payload, api_key)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
    except Exception as e:
        return f"Error: {str(e)}"


def health_check_openai():
    """Lightweight connectivity check for AI Tutor OpenAI integration."""
    api_key = _get_openai_api_key()
    if not api_key:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not set",
        }

    try:
        payload = {
            "model": get_openai_chat_model(),
            "messages": [{"role": "user", "content": "Reply with OK"}],
            "max_tokens": 512,
            "temperature": 0,
        }
        response = _post_chat_completion(payload, api_key)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return {
            "ok": True,
            "reply": content,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


def _stream_chat_completion_text(payload, api_key):
    payload = _with_resolved_model(payload)

    if not api_key:
        fallback_text, _ = _call_hf_fallback(payload)
        if fallback_text:
            yield fallback_text
        return

    req = urllib_request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        streamed_any_content = False
        with urllib_request.urlopen(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or not line.startswith("data: "):
                    continue
                data = line[len("data: "):].strip()
                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                    delta = parsed.get("choices", [{}])[0].get("delta", {})
                    content_piece = delta.get("content")
                    if content_piece:
                        streamed_any_content = True
                        yield content_piece
                except Exception:
                    continue

        if not streamed_any_content:
            fallback_payload = dict(payload)
            fallback_payload.pop("stream", None)
            response_data = _post_chat_completion(fallback_payload, api_key)
            text = _extract_assistant_text_from_completion(response_data)
            if text:
                yield text
                return
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        original_error = f"OpenAI HTTP {exc.code}: {detail}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            if fallback_text:
                yield fallback_text
            return
        raise RuntimeError(original_error)
    except URLError as exc:
        original_error = f"Network error: {exc.reason}"
        if _should_try_hf_fallback(original_error):
            fallback_text, _ = _call_hf_fallback(payload)
            if fallback_text:
                yield fallback_text
            return
        raise RuntimeError(original_error)

