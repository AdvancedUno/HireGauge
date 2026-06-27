"""Verification/analysis layered on top of collected signals."""

from __future__ import annotations

from .deterministic import (
    citation_strength,
    github_strength,
    publication_strength,
    signal_strengths,
)
from .github_authenticity import assess_github

__all__ = [
    "assess_github",
    "citation_strength",
    "github_strength",
    "publication_strength",
    "signal_strengths",
]
