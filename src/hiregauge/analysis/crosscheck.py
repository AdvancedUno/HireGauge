"""Deterministic cross-checks: resume claims vs fetched hard signals.

These are code-computed discrepancy detections that surface contradictions
between what the resume claims and what the collectors actually found.
Each check is best-effort (returns [] on any error/missing data).
Discrepancies are injected into both the dossier prompt (so the LLM must
account for them) and Evaluation.red_flags.
"""

from __future__ import annotations

import re

from ..models import CandidateProfile

# ---------------------------------------------------------------------------
# Star-inflation detection
# ---------------------------------------------------------------------------

# Patterns that signal a star-count claim in resume text.
# Matches things like "1000+ stars", "500 GitHub stars", "2K+ stargazers".
_STAR_CLAIM_RE = re.compile(
    r"(?i)"
    r"("
    r"(\d{1,4}(?:,\d{3})*(?:\.\d)?)"  # captured number (e.g. "1,000", "500", "2.5")
    r"\s*\+?\s*"
    r"(?:github\s+)?(?:stars?|stargazers?)"
    r"|"
    r"(?:github\s+)?(?:stars?|stargazers?)"
    r"\s*:?\s*"
    r"(\d{1,4}(?:,\d{3})*(?:\.\d)?)"  # captured number (e.g. "stars: 500")
    r"\s*\+?"
    r")"
)

# Commonly exaggerated star thresholds – claims above these are suspect.
_STAR_INFLATION_MULTIPLIER = 2.0
_STAR_INFLATION_ABSOLUTE = 10  # claim must exceed fetched by at least this many


def _parse_num(raw: str) -> float | None:
    """Parse a compact number like "1,000" or "2.5" into a float."""
    try:
        cleaned = raw.replace(",", "")
        # Handle "2.5K" — but K-suffixed numbers need the K stripped first.
        # We only get digit groups, so no K suffix in this pass.
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _check_star_inflation(profile: CandidateProfile) -> list[str]:
    """Check if the resume claims more stars than fetched data supports."""
    if not profile.resume or not profile.resume.text:
        return []
    gh = profile.github
    if not gh or not gh.authenticity:
        return []

    max_stars = gh.authenticity.get("max_stars")
    if max_stars is None:
        return []

    text = profile.resume.text
    matches = _STAR_CLAIM_RE.findall(text)
    if not matches:
        return []

    issues: list[str] = []
    for match_group in matches:
        # The regex alternation means one of the two groups is non-empty.
        raw_num = match_group[1] or match_group[2]
        if not raw_num:
            continue
        claimed = _parse_num(raw_num)
        if claimed is None or claimed <= 0:
            continue

        # Only flag if claim clearly exceeds fetched reality.
        if claimed > max(max_stars * _STAR_INFLATION_MULTIPLIER + _STAR_INFLATION_ABSOLUTE, 1):
            issues.append(
                f"Star-count inflation detected: resume claims {claimed:g}+ stars "
                f"but fetched GitHub data shows max_stars={max_stars:g} across owned repos."
            )

    return issues


# ---------------------------------------------------------------------------
# Phantom-publication detection
# ---------------------------------------------------------------------------

# Publication-venue keywords that strongly imply claimed publications.
_VENUE_KEYWORDS = re.compile(
    r"(?i)"
    r"(?:"
    # Top-tier venues
    r"NeurIPS|ICML|ICLR|CVPR|ICCV|ECCV|ACL|EMNLP|NAACL|EACL|"
    r"CoRL|RSS|IROS|ICRA|AAAI|IJCAI|KDD|WWW|SIGIR|"
    r"VLDB|SIGMOD|OSDI|SOSP|PLDI|POPL|STOC|FOCS|MOBICOM|"
    r"ISCA|MICRO|HPCA|SC|FAST|USENIX|SenSys|MobiSys|"
    r"CHI|UIST|VIS|SIGGRAPH|TOG|ISMAR|"
    r"arXiv|OpenReview|"
    # General publication indicators
    r"published in|published at|proceedings of|"
    r"first.author|co.author|coauthor|"
    r"preprint|manuscript|under review|accepted at|"
    r"IEEE|ACM|Springer|Elsevier|"
    r"journal of|transactios on|"
    r"[Pp]aper\s+(?:(?:titled|entitled|:)|My\s+(?:research|publication|paper))"
    r")"
)

# Minimum threshold: how many different venue keywords before we consider it a real claim.
_MIN_VENUE_HITS = 2


def _check_phantom_publications(profile: CandidateProfile) -> list[str]:
    """Check if the resume mentions publications while fetched data shows none."""
    if not profile.resume or not profile.resume.text:
        return []
    pub_signal = profile.publications
    if not pub_signal:
        return []

    # If the fetched data actually has publications, no phantom claim.
    if len(pub_signal.publications) > 0:
        return []

    text = profile.resume.text
    matches = _VENUE_KEYWORDS.findall(text)

    # Deduplicate to unique matches (lowercase).
    unique_matches = set(m.lower().strip() for m in matches if m and m.strip())

    if len(unique_matches) >= _MIN_VENUE_HITS:
        venues = ", ".join(sorted(unique_matches))
        return [
            f"Phantom-publication claim detected: resume references publications "
            f"(keywords: {venues}) but fetched publication profile returns zero papers "
            f"(source={pub_signal.source}, h_index={pub_signal.h_index or '?'})."
        ]

    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def crosscheck_claims(profile: CandidateProfile) -> list[str]:
    """Compare resume claims against fetched hard signals.

    Returns a list of human-readable discrepancy strings (best-effort,
    never raises, returns [] on any error or missing data).

    Currently checks:
    - Star-count inflation (resume claims vs fetched max_stars)
    - Phantom publications (resume references papers while fetched profile has none)
    """
    try:
        issues: list[str] = []
        issues.extend(_check_star_inflation(profile))
        issues.extend(_check_phantom_publications(profile))
        return issues
    except Exception:
        return []
