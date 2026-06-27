"""Smoke tests: the package and its core modules import cleanly.

Keeps CI meaningful before the full test suite (Phase 6) lands.
"""

import importlib

import hiregauge


def test_version_exposed():
    assert hiregauge.__version__


def test_core_modules_import():
    for mod in ("hiregauge.models", "hiregauge.config", "hiregauge.cache"):
        assert importlib.import_module(mod) is not None
