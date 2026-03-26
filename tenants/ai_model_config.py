from django.conf import settings

from .models import PlatformSettings


def _fallback_provider():
    return str(getattr(settings, 'AI_PROVIDER', 'openai') or 'openai').strip().lower()


def _fallback_models():
    return {
        'general': f"openai:{str(getattr(settings, 'OPENAI_CHAT_MODEL', '') or 'gpt-5-mini').strip()}",
        'admissions': f"openai:{str(getattr(settings, 'OPENAI_CHAT_MODEL', '') or 'gpt-4o-mini').strip()}",
        'tutor': f"gemini:{str(getattr(settings, 'GEMINI_MODEL', '')).strip().replace('gemini:', '', 1)}" if _fallback_provider() == 'gemini' else f"openai:{str(getattr(settings, 'OPENAI_CHAT_MODEL', '') or 'gpt-5-nano').strip()}",
        'analytics': f"openai:{str(getattr(settings, 'OPENAI_CHAT_MODEL', '') or 'gpt-5-mini').strip()}",
    }


def get_platform_ai_provider():
    try:
        platform = PlatformSettings.get()
        provider = str(platform.ai_primary_provider or '').strip().lower()
        if provider in {'openai', 'gemini'}:
            return provider
    except Exception:
        pass
    return _fallback_provider()


def get_platform_model_config(category='general'):
    category = str(category or 'general').strip().lower()
    if category not in {'general', 'admissions', 'tutor', 'analytics'}:
        category = 'general'

    try:
        platform = PlatformSettings.get()
        return platform.get_ai_category_config(category)
    except Exception:
        model_ref = _fallback_models().get(category, _fallback_models()['general'])
        provider, model = PlatformSettings.parse_model_ref(model_ref, fallback_provider=_fallback_provider())
        return {
            'category': category,
            'provider': provider,
            'model': model,
            'model_ref': f'{provider}:{model}' if model else '',
        }


def get_platform_model_name(category='general'):
    return get_platform_model_config(category).get('model', '')
