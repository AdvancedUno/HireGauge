"""Smoke tests: the package and its core modules import cleanly.

Keeps CI meaningful before the full test suite (Phase 6) lands.
"""

import importlib

import hireme


def test_version_exposed():
    assert hireme.__version__


def test_core_modules_import():
    for mod in ("hireme.models", "hireme.config", "hireme.cache"):
        assert importlib.import_module(mod) is not None
