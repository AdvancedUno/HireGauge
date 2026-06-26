"""Runtime settings, loaded from environment variables and an optional ``.env``.

Field names match the conventional UPPERCASE env var names case-insensitively
(e.g. the field ``anthropic_api_key`` is populated from ``ANTHROPIC_API_KEY``).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- secrets / endpoints ---
    anthropic_api_key: str | None = None
    github_token: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    kaggle_username: str | None = None
    kaggle_key: str | None = None
    ollama_host: str = "http://localhost:11434"

    # --- defaults (overridable by CLI flags) ---
    default_provider: str = "anthropic"
    default_model: str = "claude-opus-4-8"

    # --- cache ---
    cache_enabled: bool = True
    cache_dir: str = ".hireme_cache"


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()
