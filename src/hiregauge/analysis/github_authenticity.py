"""Lightweight, deterministic GitHub authenticity / activity signals.

These are *facts* (counts, ratios, recency) fed to the evaluator as ground truth —
not opinions. Star/fork ratios and recency help spot inflated or abandoned profiles.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..models import GitHubSignal


def _is_recent(iso: str | None, days: int = 365) -> bool:
    if not iso:
        return False
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:  # a naive timestamp would crash the aware subtraction below
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).days <= days
    except (ValueError, TypeError):
        return False


def assess_github(github: GitHubSignal) -> dict:
    owned = [r for r in github.repos if not r.is_fork]
    total_stars = sum(r.stars for r in owned)
    total_forks = sum(r.forks for r in owned)
    return {
        "owned_repos": len(owned),
        "forks_in_list": sum(1 for r in github.repos if r.is_fork),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "max_stars": max((r.stars for r in owned), default=0),
        "fork_to_star_ratio": round(total_forks / total_stars, 3) if total_stars else None,
        "recently_active_repos": sum(1 for r in owned if _is_recent(r.pushed_at)),
        "repos_with_topics": sum(1 for r in owned if r.topics),
    }
