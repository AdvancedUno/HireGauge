"""GitHub collector — profile + repositories + language/star/recency signals.

Two cached API calls (user + repos); never raises. Uses ``GITHUB_TOKEN`` when present
to lift the rate limit (60 -> 5000 requests/hour).
"""

from __future__ import annotations

import re
from collections import Counter

from ..cache import Cache
from ..config import Settings
from ..models import GitHubRepo, GitHubSignal
from .base import http_json

_API = "https://api.github.com"
_USERNAME_RE = re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})", re.IGNORECASE)
_BARE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")


def extract_username(identifier: str | None) -> str | None:
    if not identifier:
        return None
    s = identifier.strip()
    m = _USERNAME_RE.search(s)
    if m:
        return m.group(1)
    s = s.lstrip("@").strip("/")
    return s if _BARE_RE.match(s) else None


def _headers(settings: Settings) -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def _top_languages(repos: list[GitHubRepo], n: int = 6) -> list[str]:
    counts = Counter(r.language for r in repos if r.language and not r.is_fork)
    return [lang for lang, _ in counts.most_common(n)]


def collect_github(identifier: str, *, settings: Settings, cache: Cache) -> GitHubSignal | None:
    username = extract_username(identifier)
    if not username:
        return None
    headers = _headers(settings)

    profile = http_json(
        f"{_API}/users/{username}", cache=cache, cache_key=f"gh:user:{username}", headers=headers
    )
    if not isinstance(profile, dict) or "login" not in profile:
        return None

    repos_raw = http_json(
        f"{_API}/users/{username}/repos",
        cache=cache,
        cache_key=f"gh:repos:{username}",
        headers=headers,
        params={"sort": "updated", "per_page": 100, "type": "owner"},
    )
    repos: list[GitHubRepo] = []
    if isinstance(repos_raw, list):
        for r in repos_raw[:60]:
            repos.append(
                GitHubRepo(
                    name=r.get("name") or "",
                    description=r.get("description"),
                    url=r.get("html_url"),
                    homepage=(r.get("homepage") or None),
                    language=r.get("language"),
                    stars=r.get("stargazers_count", 0) or 0,
                    forks=r.get("forks_count", 0) or 0,
                    open_issues=r.get("open_issues_count", 0) or 0,
                    topics=r.get("topics") or [],
                    is_fork=bool(r.get("fork")),
                    archived=bool(r.get("archived")),
                    created_at=r.get("created_at"),
                    pushed_at=r.get("pushed_at"),
                )
            )

    return GitHubSignal(
        username=profile.get("login", username),
        name=profile.get("name"),
        bio=profile.get("bio"),
        company=profile.get("company"),
        location=profile.get("location"),
        blog=(profile.get("blog") or None),
        twitter_username=profile.get("twitter_username"),
        followers=profile.get("followers", 0) or 0,
        following=profile.get("following", 0) or 0,
        public_repos=profile.get("public_repos", 0) or 0,
        created_at=profile.get("created_at"),
        top_languages=_top_languages(repos),
        repos=repos,
    )
