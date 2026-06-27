"""Render a Report to Markdown (the primary output format)."""

from __future__ import annotations

from ..models import Report
from ._common import VERDICT_LABEL, candidate_name


def render_markdown(report: Report) -> str:
    e = report.evaluation
    p = report.profile
    out: list[str] = []

    out.append(f"# HireGauge — {report.agent} evaluation")
    out.append("")
    out.append(f"**Candidate:** {candidate_name(report)}  ")
    out.append(f"**Experience:** {p.experience.describe()}  ")
    out.append(f"**Overall:** {e.overall_score:g}/100 — **{e.band}**  ")
    verdict = VERDICT_LABEL.get(e.screen_verdict)
    if verdict:
        pct = f" · est. ~{e.percentile}th percentile of the applicant pool" if e.percentile is not None else ""
        out.append(f"**Screen verdict:** {verdict}{pct}  ")
    out.append(f"*backend: {report.model} · mode: {report.mode} · {report.generated_at}*")
    out.append("")
    if e.positioning:
        out.append(f"**Where you stand:** {e.positioning.replace(chr(10), ' ')}")
        out.append("")
    if e.summary:
        out.append("> " + e.summary.replace("\n", " "))
        out.append("")

    out.append("## Scores")
    out.append("")
    out.append("| Dimension | Score | Evidence |")
    out.append("|---|---:|---|")
    for d in e.dimensions:
        ev = d.evidence.replace("\n", " ").replace("|", "\\|")
        if len(ev) > 300:
            ev = ev[:297] + "..."
        out.append(f"| {d.label} | {d.score:g}/{d.max:g} | {ev} |")
    out.append("")

    if e.strengths:
        out.append("## Strengths")
        out += [f"- {s}" for s in e.strengths]
        out.append("")
    if e.gaps:
        out.append("## Gaps")
        out += [f"- {g}" for g in e.gaps]
        out.append("")
    if e.green_flags:
        out.append("## Green flags")
        out += [f"- ✅ {g}" for g in e.green_flags]
        out.append("")
    if e.red_flags:
        out.append("## Red flags")
        out += [f"- 🚩 {r}" for r in e.red_flags]
        out.append("")
    if e.action_plan:
        out.append("## What to do next")
        for a in sorted(e.action_plan, key=lambda x: x.priority):
            out.append(f"{a.priority}. **{a.recommendation}** — _{a.rationale}_  ([{a.dimension}])")
        out.append("")

    if p.resume:
        disc = p.resume.discovered.identifiers()
        if disc:
            out.append("## Discovered from resume")
            out.append(", ".join(f"{k}: {v}" for k, v in disc.items()))
            out.append("")

    if p.collection_notes:
        out.append("## Notes")
        out += [f"- {n}" for n in p.collection_notes]
        out.append("")

    out.append("---")
    out.append(
        "*HireGauge scores demonstrated skills, projects, contributions, and experience — not demographics. "
        "Pedigree/GPA count only where a domain's real bar uses them. Evidence is shown per dimension.*"
    )
    return "\n".join(out)
