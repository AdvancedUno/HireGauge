"""Deterministic 0..1 strength signals, computed in code from fetched data.

These are blended into the LLM's per-dimension scores (see ``evaluator``) so dimensions
backed by hard data (GitHub activity, fetched h-index/citations) are anchored to ground
truth rather than left entirely to the model. Thresholds are documented in docs/rubrics.md.
"""

from __future__ import annotations

from ..models import CandidateProfile, GitHubSignal, PublicationSignal


def github_strength(gh: GitHubSignal | None) -> float | None:
    """Composite 0..1 from owned-repo breadth, recent activity, language breadth, and a
    standout-project (max-stars) bonus. Deliberately does NOT let raw star count dominate.

    Thresholds are deliberately demanding (an ordinary student profile lands ~0.3, a solid
    one ~0.65, and only a genuinely strong profile approaches 1.0) so the deterministic blend
    can't inflate the model's score for a middling GitHub. See docs/rubrics.md."""
    if gh is None:
        return None
    a = gh.authenticity or {}
    owned = a.get("owned_repos")
    if owned is None:
        owned = sum(1 for r in gh.repos if not r.is_fork)
    max_stars = a.get("max_stars")
    if max_stars is None:
        max_stars = max((r.stars for r in gh.repos if not r.is_fork), default=0)
    recent = a.get("recently_active_repos", 0)
    langs = len(gh.top_languages)
    s = (
        0.30 * min(owned / 12, 1.0)
        + 0.25 * min(recent / 6, 1.0)
        + 0.15 * min(langs / 6, 1.0)
        + 0.30 * min(max_stars / 800, 1.0)
    )
    return round(min(s, 1.0), 3)


def citation_strength(pub: PublicationSignal | None) -> float | None:
    """0..1 from h-index / total citations (early-career-friendly buckets)."""
    if pub is None or (pub.h_index is None and pub.total_citations is None):
        return None
    h = pub.h_index or 0
    cites = pub.total_citations or 0
    return round(max(min(h / 20, 1.0), min(cites / 2000, 1.0)), 3)


def publication_strength(pub: PublicationSignal | None) -> float | None:
    """0..1 from paper count blended with citation quality."""
    if pub is None:
        return None
    n = len(pub.publications)
    if n == 0 and pub.h_index is None:
        return None
    cs = citation_strength(pub) or 0.0
    return round(0.6 * min(n / 8, 1.0) + 0.4 * cs, 3)


def signal_strengths(profile: CandidateProfile) -> dict[str, float | None]:
    """All deterministic strengths for a profile, keyed by ``Dimension.gt_signal`` name."""
    return {
        "github": github_strength(profile.github),
        "publication": publication_strength(profile.publications),
        "citation": citation_strength(profile.publications),
    }
