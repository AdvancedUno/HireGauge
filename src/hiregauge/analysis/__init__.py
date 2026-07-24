"""Verification/analysis layered on top of collected signals."""

from __future__ import annotations

from .crosscheck import crosscheck_claims
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
    "crosscheck_claims",
    "github_strength",
    "publication_strength",
    "signal_strengths",
]
