"""Evaluator + pipeline tests using a fake LLM provider (no API, no network)."""

from __future__ import annotations

from typing import Any

from hireme.agents import get_agent
from hireme.evaluator import _assemble, _RubricDimension, _RubricOutput
from hireme.pipeline import RunConfig, run


class FakeProvider:
    """Implements the LLMProvider protocol; returns a canned structured output."""

    name = "fake"
    model = "fake-1"

    def __init__(self, scores: dict[str, float] | None = None, raise_exc: bool = False) -> None:
        self.scores = scores or {}
        self.raise_exc = raise_exc

    def complete_structured(self, *, system: str, user: str, schema: type[Any], **_: Any) -> Any:
        if self.raise_exc:
            raise RuntimeError("boom")
        dims = [
            {"key": k, "score": v, "evidence": "evidence", "confidence": 0.9}
            for k, v in self.scores.items()
        ]
        return schema.model_validate(
            {
                "summary": "ok",
                "dimensions": dims,
                "strengths": ["s"],
                "gaps": ["g"],
                "green_flags": [],
                "red_flags": [],
                "action_plan": [],
            }
        )


def test_assemble_weighted_overall_and_band():
    agent = get_agent("general")
    out = _RubricOutput(
        summary="x",
        dimensions=[
            _RubricDimension(key=d.key, score=d.weight, evidence="e", confidence=1.0)
            for d in agent.dimensions
        ],
        strengths=[], gaps=[], green_flags=[], red_flags=[], action_plan=[],
    )
    ev = _assemble(agent, out)
    assert ev.overall_score == 100.0
    assert ev.band == "Strong"
    assert len(ev.dimensions) == len(agent.dimensions)


def test_assemble_clamps_and_handles_missing():
    agent = get_agent("general")
    dims = list(agent.dimensions)
    out = _RubricOutput(
        summary="x",
        dimensions=[_RubricDimension(key=dims[0].key, score=999.0, evidence="e", confidence=2.0)],
        strengths=[], gaps=[], green_flags=[], red_flags=[], action_plan=[],
    )
    ev = _assemble(agent, out)
    by = {d.key: d for d in ev.dimensions}
    assert by[dims[0].key].score == dims[0].weight  # clamped to the dimension max
    assert by[dims[0].key].confidence == 1.0  # clamped to [0,1]
    assert by[dims[-1].key].score == 0.0  # missing key -> 0
    assert ev.overall_score == dims[0].weight


def test_blend_never_lowers_score_below_llm():
    # A real-but-sparse signal (weak GitHub) must not drag down a high LLM score —
    # providing data can only help, never penalize.
    agent = get_agent("general")
    pq = next(d for d in agent.dimensions if d.gt_signal == "github")
    out = _RubricOutput(
        summary="x",
        dimensions=[_RubricDimension(key=pq.key, score=pq.weight, evidence="e", confidence=0.9)],
        strengths=[], gaps=[], green_flags=[], red_flags=[], action_plan=[],
    )
    ev = _assemble(agent, out, {"github": 0.2, "publication": None, "citation": None})
    by = {d.key: d for d in ev.dimensions}
    assert by[pq.key].score == pq.weight  # unchanged, not lowered


def test_blend_lifts_low_score_toward_strong_signal():
    agent = get_agent("general")
    pq = next(d for d in agent.dimensions if d.gt_signal == "github")
    out = _RubricOutput(
        summary="x",
        dimensions=[_RubricDimension(key=pq.key, score=pq.weight * 0.4, evidence="e", confidence=0.5)],
        strengths=[], gaps=[], green_flags=[], red_flags=[], action_plan=[],
    )
    ev = _assemble(agent, out, {"github": 1.0, "publication": None, "citation": None})
    by = {d.key: d for d in ev.dimensions}
    assert by[pq.key].score > pq.weight * 0.4  # lifted by the strong signal
    assert "[auto: github=" in by[pq.key].evidence


def test_pipeline_full_marks_offline(tmp_path):
    agent = get_agent("general")
    scores = {d.key: d.weight for d in agent.dimensions}
    resume = tmp_path / "r.txt"
    resume.write_text("Jane Doe  jane@example.com  Senior engineer, 6 yoe.", encoding="utf-8")
    cfg = RunConfig(agent="general", resume=str(resume), no_cache=True)
    report = run(cfg, provider=FakeProvider(scores))
    assert report.evaluation.overall_score == 100.0
    assert report.evaluation.band == "Strong"
    assert report.profile.resume is not None
    assert report.profile.resume.discovered.email == "jane@example.com"


def test_pipeline_provider_error_falls_back(tmp_path):
    resume = tmp_path / "r.txt"
    resume.write_text("Jane Doe jane@example.com", encoding="utf-8")
    cfg = RunConfig(agent="general", resume=str(resume), no_cache=True)
    report = run(cfg, provider=FakeProvider(raise_exc=True))
    assert report.evaluation.band == "Not evaluated"
    assert report.evaluation.overall_score == 0.0


def test_pipeline_records_uncollected_flags(tmp_path):
    # Flags with no collector must be acknowledged + surfaced, not silently dropped.
    resume = tmp_path / "r.txt"
    resume.write_text("Jane Doe jane@example.com", encoding="utf-8")
    scores = {d.key: d.weight for d in get_agent("general").dimensions}
    cfg = RunConfig(
        agent="general", resume=str(resume), no_cache=True,
        codeforces="tourist", leetcode="lee", linkedin="jane-doe", jd="jd.txt",
    )
    report = run(cfg, provider=FakeProvider(scores))
    notes = " ".join(report.profile.collection_notes)
    assert "tourist" in notes  # codeforces handle acknowledged in the report
    assert "jd" in notes
    disc = report.profile.resume.discovered
    assert disc.codeforces == "tourist"  # merged so the evaluator sees it
    assert disc.leetcode == "lee"
    assert disc.linkedin == "jane-doe"
