"""Builds AI providers from settings and caches one instance per provider name.

Provider choice is "preferred OR whatever is configured": if EMBEDDING_PROVIDER /
CHAT_PROVIDER points at a provider with no API key, we fall back to the other
one. So setting only GEMINI_API_KEY (or only OPENAI_API_KEY) just works.
"""

import logging

from app.ai.base import AIProvider
from app.config import ProviderName, get_settings
from app.errors import ProviderNotConfiguredError

logger = logging.getLogger(__name__)

ALL_PROVIDERS: list[ProviderName] = ["openai", "gemini"]

_providers: dict[str, AIProvider] = {}


def _api_key_for(name: ProviderName) -> str:
    settings = get_settings()
    return settings.openai_api_key if name == "openai" else settings.gemini_api_key


def _is_configured(name: ProviderName) -> bool:
    return name in _providers or bool(_api_key_for(name))


def _build(name: ProviderName) -> AIProvider:
    settings = get_settings()
    api_key = _api_key_for(name)
    if not api_key:
        raise ProviderNotConfiguredError(f"{name} is not configured. Set {name.upper()}_API_KEY in backend/.env.")

    # Imported lazily so a missing SDK for an unused provider doesn't break startup.
    if name == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key, settings.openai_chat_model, settings.openai_embedding_model)

    from app.ai.gemini_provider import GeminiProvider

    return GeminiProvider(api_key, settings.gemini_chat_model, settings.gemini_embedding_model)


def resolve_provider(preferred: ProviderName) -> ProviderName:
    """Use `preferred` if it has a key, otherwise the first provider that does."""
    if _is_configured(preferred):
        return preferred

    for name in ALL_PROVIDERS:
        if _is_configured(name):
            logger.info("preferred provider has no API key, falling back", extra={"preferred": preferred, "using": name})
            return name

    raise ProviderNotConfiguredError(
        "No AI provider is configured. Set OPENAI_API_KEY or GEMINI_API_KEY in backend/.env and restart the server."
    )


def get_provider(name: ProviderName) -> AIProvider:
    if name not in _providers:
        _providers[name] = _build(name)
    return _providers[name]


def get_embedding_provider() -> AIProvider:
    return get_provider(resolve_provider(get_settings().embedding_provider))


def get_chat_provider(name: ProviderName | None = None) -> AIProvider:
    """An explicitly requested provider (from the UI switch) is used as-is;
    otherwise the configured default, with fallback."""
    if name:
        return get_provider(name)
    return get_provider(resolve_provider(get_settings().chat_provider))


def available_providers() -> list[ProviderName]:
    return [name for name in ALL_PROVIDERS if _is_configured(name)]
