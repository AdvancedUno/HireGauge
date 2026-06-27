"""Data-source collectors (resume is the hub; others are flag/discovery-driven)."""

from __future__ import annotations

from .github import collect_github
from .kaggle import collect_kaggle
from .resume import collect_resume, discover_profiles
from .scholar import collect_publications
from .web import collect_web

__all__ = [
    "collect_github",
    "collect_kaggle",
    "collect_publications",
    "collect_resume",
    "collect_web",
    "discover_profiles",
]
