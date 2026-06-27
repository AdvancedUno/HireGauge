"""Shared helpers for the Markdown and HTML report renderers."""

from __future__ import annotations

from ..models import Report

# Screen verdict -> human-readable label. Derived from the band in the evaluator, so it
# can never contradict the score.
VERDICT_LABEL = {
    "yes": "Likely to pass an initial screen",
    "borderline": "Borderline — could go either way",
    "no": "Unlikely to pass an initial screen as-is",
}


def candidate_name(report: Report) -> str:
    """Best available display name: parsed resume name -> GitHub name -> resume email ->
    @handle -> 'Candidate'."""
    p = report.profile
    if p.resume and p.resume.parsed and p.resume.parsed.name:
        return p.resume.parsed.name
    gh = p.github
    if gh and gh.name:
        return gh.name
    if p.resume and p.resume.discovered.email:
        return p.resume.discovered.email
    if gh:
        return f"@{gh.username}"
    return "Candidate"
