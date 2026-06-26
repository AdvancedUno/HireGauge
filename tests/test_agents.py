"""Smoke + invariant tests for the evaluator agent registry."""

from __future__ import annotations

import pytest

from hireme.agents import agent_names, all_agents, get_agent

EXPECTED = {"quant", "airesearch", "bigtech", "general", "university"}
VALID_SIGNALS = {"resume", "github", "publications", "competitive", "kaggle", "web"}


def test_registry_has_the_five_agents():
    assert set(agent_names()) == EXPECTED


def test_weights_sum_to_100():
    for a in all_agents():
        assert a.weight_total() == pytest.approx(100.0), (a.name, a.weight_total())


def test_dimension_keys_unique_and_nonempty():
    for a in all_agents():
        keys = [d.key for d in a.dimensions]
        assert keys, a.name
        assert len(keys) == len(set(keys)), a.name


def test_signals_are_known():
    for a in all_agents():
        assert set(a.signals) <= VALID_SIGNALS, a.name
        assert a.signals, a.name


def test_get_agent_roundtrips():
    for name in agent_names():
        assert get_agent(name).name == name


def test_get_agent_unknown_raises():
    with pytest.raises(KeyError):
        get_agent("does-not-exist")


def test_cli_imports():
    # The Typer app must import cleanly (catches broken option wiring early).
    from hireme.cli import app  # noqa: F401
