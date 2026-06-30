"""CLI helper tests — model/provider resolution and pre-flight validation."""

from __future__ import annotations

import pytest
import typer

from hiregauge.cli import _provider_or_exit, _resolve_model
from hiregauge.config import Settings
from hiregauge.pipeline import RunConfig


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


def test_missing_api_key_fails_fast_with_nonzero_exit():
    # Issue #19: a missing provider key must abort before any collection, not emit a
    # 0/100 "success" report and exit 0.
    s = _settings(default_provider="gemini", gemini_api_key=None)
    cfg = RunConfig(agent="general", provider="gemini", model="gemini-2.5-flash")
    with pytest.raises(typer.Exit) as exc:
        _provider_or_exit(cfg, s)
    assert exc.value.exit_code == 2


def test_unimplemented_provider_fails_fast_with_nonzero_exit():
    s = _settings()
    cfg = RunConfig(agent="general", provider="openai", model="gpt-4.1")
    with pytest.raises(typer.Exit) as exc:
        _provider_or_exit(cfg, s)
    assert exc.value.exit_code == 2
