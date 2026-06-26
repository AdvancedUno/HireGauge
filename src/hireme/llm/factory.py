"""Provider selection. Anthropic is implemented; others are planned (see TODO)."""

from __future__ import annotations

from ..config import Settings
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider


def build_provider(provider: str, model: str, settings: Settings) -> LLMProvider:
    provider = (provider or "anthropic").lower()

    if provider == "anthropic":
        return AnthropicProvider(model=model, api_key=settings.anthropic_api_key)

    if provider in {"ollama", "openai", "gemini"}:
        raise NotImplementedError(
            f"Provider '{provider}' is planned but not yet implemented in this build. "
            "Use --provider anthropic (default) for now."
        )

    raise ValueError(f"Unknown provider '{provider}'. Choose: anthropic, ollama, openai, gemini.")
