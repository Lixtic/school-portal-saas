"""Semantic cache for AI-generated content.

Hashes (system_prompt, user_prompt, model, temperature) into a cache key.
On hit → return cached raw text (no API call, no credit cost).
On miss → call OpenAI, strip markdown fences, cache, return.

Uses Django's cache framework (Redis in production, LocMemCache in dev).
"""
import hashlib
import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache TTL: 7 days.  Identical prompts produce near-identical output,
# but we expire eventually so curriculum updates propagate.
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days

_PREFIX = 'ai:'


def _make_key(system: str, prompt: str, model: str, temperature: float) -> str:
    """Build a deterministic cache key from the full prompt signature."""
    blob = json.dumps(
        [system, prompt, model, str(temperature)],
        sort_keys=True,
        ensure_ascii=True,
    )
    digest = hashlib.sha256(blob.encode()).hexdigest()[:32]
    return f'{_PREFIX}{digest}'


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from AI output."""
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()


def get_cached(*, system: str, prompt: str, model: str = 'gpt-4o-mini',
               temperature: float = 0.7):
    """Check for a cached AI response. Returns raw_text or None."""
    key = _make_key(system, prompt, model, temperature)
    hit = cache.get(key)
    if hit is not None:
        logger.info('AI cache HIT  %s', key)
    return hit


def call_and_cache(*, system: str, prompt: str, model: str = 'gpt-4o-mini',
                   temperature: float = 0.7, max_tokens: int = 3000):
    """Call OpenAI, strip markdown fences, cache the result, and return raw text.

    Raises on API / network errors (caller should handle).
    """
    import openai
    from django.conf import settings

    key = _make_key(system, prompt, model, temperature)

    try:
        client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except openai.OpenAIError as exc:
        logger.error('OpenAI API error (model=%s): %s', model, exc)
        raise
    raw_text = _strip_fences(resp.choices[0].message.content.strip())

    cache.set(key, raw_text, CACHE_TTL)
    logger.info('AI cache MISS %s (stored)', key)

    return raw_text
