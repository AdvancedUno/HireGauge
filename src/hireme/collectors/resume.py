"""Resume collector — the hub of HireMe.

Most users submit only a resume PDF. This module extracts the resume text *and*
its embedded hyperlinks, then auto-discovers the candidate's external identifiers
(GitHub, LinkedIn, portfolio, Scholar/ORCID/arXiv, Codeforces, LeetCode, Kaggle,
email). Discovery is deterministic (no API key required); CLI flags override it.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from ..models import DiscoveredProfiles, ResumeSignal

# Paths under these hosts are not usernames.
_GITHUB_RESERVED = {
    "sponsors", "features", "about", "pricing", "marketplace", "topics", "collections",
    "login", "join", "settings", "orgs", "enterprise", "contact", "security", "apps",
    "explore", "notifications", "new", "search", "readme", "site",
}
_LEETCODE_RESERVED = {
    "problems", "problemset", "contest", "discuss", "explore", "u", "accounts", "tag",
    "study-plan", "subscribe",
}
_KAGGLE_RESERVED = {
    "competitions", "datasets", "code", "discussions", "learn", "models", "organizations",
    "notebooks",
}
_TWITTER_RESERVED = {"home", "search", "explore", "i", "intent", "share", "hashtag"}

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_URL = re.compile(r"https?://[^\s)>\]\"'}]+", re.IGNORECASE)
_GITHUB = re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})", re.IGNORECASE)
# A bare profile URL (owner not followed by another path segment) is far more likely to
# be the candidate's own account than a referenced third-party repo (github.com/org/repo).
_GITHUB_PROFILE = re.compile(
    r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/?(?![A-Za-z0-9/-])", re.IGNORECASE
)
_LINKEDIN = re.compile(r"linkedin\.com/(?:in|pub)/([A-Za-z0-9\-_%]+)", re.IGNORECASE)
_CODEFORCES = re.compile(r"codeforces\.com/profile/([A-Za-z0-9_\-]+)", re.IGNORECASE)
_LEETCODE = re.compile(r"leetcode\.com/(?:u/)?([A-Za-z0-9_\-]+)", re.IGNORECASE)
_KAGGLE = re.compile(r"kaggle\.com/([A-Za-z0-9_\-]+)", re.IGNORECASE)
_SCHOLAR = re.compile(r"scholar\.google\.[A-Za-z.]+/citations\?[^\s)>\]\"']+", re.IGNORECASE)
_ORCID = re.compile(r"orcid\.org/([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9Xx])", re.IGNORECASE)
_ARXIV = re.compile(r"arxiv\.org/a/([A-Za-z0-9_\-]+)", re.IGNORECASE)
# \b prevents the bare "x.com" alternative from matching inside hosts like netflix.com.
_TWITTER = re.compile(r"\b(?:twitter|x)\.com/([A-Za-z0-9_]{1,15})", re.IGNORECASE)

_KNOWN_HOSTS = (
    "github.com", "linkedin.com", "codeforces.com", "leetcode.com", "kaggle.com",
    "orcid.org", "arxiv.org", "twitter.com", "x.com",
)


def _is_known_host(url: str) -> bool:
    """True if the URL points at a social/academic profile host handled by a dedicated
    extractor — so it must not be mistaken for a personal site/blog. Matches on the parsed
    host (not a raw substring), so e.g. ``netflix.com`` is no longer caught by ``x.com``."""
    host = urlsplit(url if "://" in url else "//" + url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("scholar.google"):  # scholar.google.<tld> varies by country
        return True
    return any(host == kh or host.endswith("." + kh) for kh in _KNOWN_HOSTS)


def _find(pattern: re.Pattern[str], sources: list[str], reserved: set[str] | None = None, group: int = 1) -> str | None:
    for s in sources:
        for m in pattern.finditer(s):
            val = m.group(group)
            if reserved and val.lower() in reserved:
                continue
            return val
    return None


def _extract_text_and_links(pdf_path: str) -> tuple[str, list[str]]:
    import pymupdf
    import pymupdf4llm

    doc = pymupdf.open(pdf_path)
    try:
        try:
            text = pymupdf4llm.to_markdown(doc)
        except Exception:
            text = "\n".join(page.get_text() for page in doc)
        uris: list[str] = []
        for page in doc:
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    uris.append(uri)
    finally:
        doc.close()
    return text, uris


def _collect_links(text: str, uris: list[str]) -> list[str]:
    """De-duplicated URL list: embedded PDF link annotations first, then inline-text URLs."""
    return list(dict.fromkeys([*uris, *_URL.findall(text)]))


def discover_profiles(
    text: str, uris: list[str], all_links: list[str] | None = None
) -> DiscoveredProfiles:
    """Deterministically pull identifiers from resume text + embedded link URIs.

    Embedded link annotations are searched first: a resume's clickable "GitHub" /
    "LinkedIn" almost always points at the candidate's own profile. ``all_links`` may be
    passed in (by ``collect_resume``) to avoid recomputing the URL list.
    """
    sources = ["\n".join(uris), text]  # prefer embedded links over inline text

    if all_links is None:
        all_links = _collect_links(text, uris)
    websites = [u.rstrip(".,);]>\"'") for u in all_links if not _is_known_host(u)]

    return DiscoveredProfiles(
        github=(
            _find(_GITHUB_PROFILE, sources, _GITHUB_RESERVED)
            or _find(_GITHUB, sources, _GITHUB_RESERVED)
        ),
        linkedin=_find(_LINKEDIN, sources),
        codeforces=_find(_CODEFORCES, sources),
        leetcode=_find(_LEETCODE, sources, _LEETCODE_RESERVED),
        kaggle=_find(_KAGGLE, sources, _KAGGLE_RESERVED),
        scholar=_find(_SCHOLAR, sources, group=0),
        orcid=_find(_ORCID, sources),
        arxiv=_find(_ARXIV, sources),
        twitter=_find(_TWITTER, sources, _TWITTER_RESERVED),
        email=_find(_EMAIL, sources, group=0),
        websites=list(dict.fromkeys(websites)),
    )


def collect_resume(path: str) -> ResumeSignal | None:
    """Parse a resume file (PDF or text) into a ``ResumeSignal``. Returns ``None`` on failure."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        if p.suffix.lower() == ".pdf":
            text, uris = _extract_text_and_links(str(p))
        else:
            text, uris = p.read_text(encoding="utf-8", errors="ignore"), []
    except Exception:
        return None

    all_links = _collect_links(text, uris)
    return ResumeSignal(
        path=str(p),
        text=text,
        char_count=len(text),
        links=all_links,
        discovered=discover_profiles(text, uris, all_links),
    )
