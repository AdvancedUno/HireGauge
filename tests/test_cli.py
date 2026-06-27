"""CLI helper tests — model/provider resolution."""

from __future__ import annotations

from hiregauge.cli import _resolve_model
from hiregauge.config import Settings


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


def test_resolve_model_explicit_flag_wins():
    s = _settings(default_provider="gemini", default_model="gemini-2.5-flash")
    assert _resolve_model("claude-opus-4-8", "anthropic", s) == "claude-opus-4-8"


def test_resolve_model_default_applies_only_to_default_provider():
    # A configured DEFAULT_MODEL (a gemini id) must NOT leak onto another provider.
    s = _settings(default_provider="gemini", default_model="gemini-2.5-flash")
    assert _resolve_model(None, "gemini", s) == "gemini-2.5-flash"
    assert _resolve_model(None, "anthropic", s) == "claude-opus-4-8"


def test_resolve_model_falls_back_per_provider_when_default_unset():
    s = _settings(default_provider="gemini", default_model=None)
    assert _resolve_model(None, "anthropic", s) == "claude-opus-4-8"
    assert _resolve_model(None, "openai", s) == "gpt-4.1"
    assert _resolve_model(None, "gemini", s) == "gemini-2.5-flash"
