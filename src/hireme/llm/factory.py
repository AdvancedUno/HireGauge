"""Provider selection + per-provider default models.

Gemini and Anthropic are implemented; OpenAI/Ollama are planned (see TODO).
"""

from __future__ import annotations

from ..config import Settings
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4.1",
    "ollama": "gemma3:4b",
}


def default_model_for(provider: str) -> str:
    """The default model id for a provider (falls back to the Gemini default)."""
    return DEFAULT_MODELS.get((provider or "").lower(), DEFAULT_MODELS["gemini"])


def build_provider(provider: str, model: str, settings: Settings) -> LLMProvider:
    provider = (provider or settings.default_provider or "gemini").lower()

    if provider == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider(model=model, api_key=settings.gemini_api_key)

    if provider == "anthropic":
        return AnthropicProvider(model=model, api_key=settings.anthropic_api_key)

    if provider in {"ollama", "openai"}:
        raise NotImplementedError(
            f"Provider '{provider}' is planned but not yet implemented in this build. "
            "Use --provider gemini (default) or --provider anthropic for now."
        )

    raise ValueError(f"Unknown provider '{provider}'. Choose: gemini, anthropic, ollama, openai.")
