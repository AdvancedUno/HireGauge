"""Report rendering tests (HTML escaping + structure; Markdown smoke)."""

from __future__ import annotations

from hiregauge.models import (
    CandidateProfile,
    DimensionScore,
    Evaluation,
    GitHubSignal,
    Report,
    ResumeParsed,
    ResumeSignal,
)
from hiregauge.report import render_html, render_markdown
from hiregauge.report._common import candidate_name


def _report() -> Report:
    e = Evaluation(
        agent="general",
        overall_score=72.0,
        band="Competitive",
        summary="Solid <b>candidate</b> & strong work.",
        dimensions=[
            DimensionScore(
                key="x", label="Project Quality", score=15.0, max=20.0, weight=20.0,
                evidence="great work | with a pipe", confidence=0.8,
            )
        ],
        strengths=["ships real projects"],
        gaps=["needs more OSS"],
        green_flags=["original project"],
        red_flags=["no tests"],
        action_plan=[],
    )
    return Report(
        agent="general", mode="candidate", model="gemini-2.5-flash",
        generated_at="2026-06-26T00:00:00", profile=CandidateProfile(), evaluation=e,
    )


def test_render_html_structure_and_escaping():
    out = render_html(_report())
    assert out.startswith("<!doctype html>")
    assert out.rstrip().endswith("</html>")
    assert "Competitive" in out
    assert "Project Quality" in out
    # raw HTML in model text must be escaped, not injected
    assert "<b>candidate</b>" not in out
    assert "&lt;b&gt;candidate&lt;/b&gt;" in out


def test_render_markdown_has_scores_table():
    md = render_markdown(_report())
    assert "# HireGauge — general evaluation" in md
    assert "| Project Quality | 15/20 |" in md
    assert "72/100 — **Competitive**" in md


def test_candidate_name_prefers_parsed_resume_name():
    r = _report()
    r.profile = CandidateProfile(
        resume=ResumeSignal(parsed=ResumeParsed(name="Jane Parsed")),
        github=GitHubSignal(username="jgh", name="GH Name"),
    )
    assert candidate_name(r) == "Jane Parsed"  # parsed name beats the GitHub display name
