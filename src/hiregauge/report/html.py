"""Render a Report to a self-contained, styled HTML document."""

from __future__ import annotations

import html

from ..models import Report
from ._common import VERDICT_LABEL, candidate_name

_BAND_COLOR = {
    "Strong": "#1a7f37",
    "Competitive": "#0969da",
    "Developing": "#9a6700",
    "Early": "#57606a",
    "Not evaluated": "#cf222e",
}

_CSS = (
    "*{box-sizing:border-box}"
    "body{font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
    "color:#1f2328;max-width:900px;margin:2rem auto;padding:0 1.25rem;background:#fff}"
    "h1{font-size:1.5rem;margin:0 0 .25rem}h2{font-size:1.05rem;margin:1.6rem 0 .5rem;"
    "border-bottom:1px solid #d0d7de;padding-bottom:.25rem}"
    ".meta{color:#57606a;font-size:.86rem;margin:.1rem 0}"
    ".badge{display:inline-block;color:#fff;border-radius:999px;padding:.2rem .7rem;font-weight:600;font-size:.95rem}"
    ".summary{background:#f6f8fa;border-left:4px solid #d0d7de;padding:.7rem 1rem;border-radius:6px;margin:.9rem 0}"
    "table{width:100%;border-collapse:collapse;font-size:.92rem}"
    "td{border-top:1px solid #eaeef2;padding:.55rem .5rem;vertical-align:top}"
    ".dim{font-weight:600;width:34%}.sc{width:120px}.ev{color:#3b414a}"
    ".bar{position:relative;background:#eaeef2;border-radius:6px;height:20px;min-width:110px}"
    ".fill{position:absolute;inset:0;width:0;background:#0969da;border-radius:6px;opacity:.25}"
    ".barlabel{position:absolute;inset:0;text-align:center;font-size:.8rem;line-height:20px;font-variant-numeric:tabular-nums}"
    "ul,ol{margin:.3rem 0 .3rem 1.1rem;padding:0}li{margin:.2rem 0}"
    ".tag{color:#57606a;font-size:.8rem}"
    ".flag-ok{color:#1a7f37}.flag-bad{color:#cf222e}"
    "footer{color:#57606a;font-size:.8rem;margin-top:2rem;border-top:1px solid #d0d7de;padding-top:.6rem}"
    "code{background:#f6f8fa;padding:.05rem .3rem;border-radius:4px}"
)


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _bar(score: float, mx: float) -> str:
    pct = 0 if not mx else max(0, min(100, round(score / mx * 100)))
    return (
        f'<div class="bar"><div class="fill" style="width:{pct}%"></div>'
        f'<span class="barlabel">{score:g}/{mx:g}</span></div>'
    )


def _ul(items: list[str], cls: str = "") -> str:
    if not items:
        return ""
    klass = f' class="{cls}"' if cls else ""
    return "<ul>" + "".join(f"<li{klass}>{_esc(i)}</li>" for i in items) + "</ul>"


def render_html(report: Report) -> str:
    e = report.evaluation
    p = report.profile
    color = _BAND_COLOR.get(e.band, "#57606a")

    out: list[str] = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>HireGauge — {_esc(report.agent)} evaluation</title>",
        "<style>", _CSS, "</style></head><body>",
        f"<h1>HireGauge — {_esc(report.agent)} evaluation</h1>",
        f"<p class='meta'><strong>{_esc(candidate_name(report))}</strong> · "
        f"{_esc(p.experience.describe())}</p>",
        f"<p><span class='badge' style='background:{color}'>{e.overall_score:g}/100 — "
        f"{_esc(e.band)}</span></p>",
    ]
    verdict = VERDICT_LABEL.get(e.screen_verdict)
    if verdict:
        pct = (
            f" · est. ~{e.percentile}th percentile of the applicant pool"
            if e.percentile is not None
            else ""
        )
        out.append(f"<p class='meta'><strong>Screen verdict:</strong> {_esc(verdict)}{_esc(pct)}</p>")
    out.append(
        f"<p class='meta'>backend: {_esc(report.model)} · mode: {_esc(report.mode)} · "
        f"{_esc(report.generated_at)}</p>"
    )
    if e.positioning:
        out.append(f"<div class='summary'><strong>Where you stand:</strong> {_esc(e.positioning)}</div>")
    if e.summary:
        out.append(f"<div class='summary'>{_esc(e.summary)}</div>")

    out.append("<h2>Scores</h2><table>")
    for d in e.dimensions:
        out.append(
            f"<tr><td class='dim'>{_esc(d.label)}</td>"
            f"<td class='sc'>{_bar(d.score, d.max)}</td>"
            f"<td class='ev'>{_esc(d.evidence)}</td></tr>"
        )
    out.append("</table>")

    if e.strengths:
        out.append("<h2>Strengths</h2>" + _ul(e.strengths))
    if e.gaps:
        out.append("<h2>Gaps</h2>" + _ul(e.gaps))
    if e.green_flags:
        out.append("<h2>Green flags</h2>" + _ul(e.green_flags, "flag-ok"))
    if e.red_flags:
        out.append("<h2>Red flags</h2>" + _ul(e.red_flags, "flag-bad"))
    if e.action_plan:
        out.append("<h2>What to do next</h2><ol>")
        for a in sorted(e.action_plan, key=lambda x: x.priority):
            out.append(
                f"<li><strong>{_esc(a.recommendation)}</strong> — <em>{_esc(a.rationale)}</em> "
                f"<span class='tag'>({_esc(a.dimension)})</span></li>"
            )
        out.append("</ol>")

    if p.resume:
        disc = p.resume.discovered.identifiers()
        if disc:
            out.append("<h2>Discovered from resume</h2><p class='meta'>")
            out.append(" · ".join(f"{_esc(k)}: <code>{_esc(v)}</code>" for k, v in disc.items()))
            out.append("</p>")
    if p.collection_notes:
        out.append("<h2>Notes</h2>" + _ul(p.collection_notes))

    out.append(
        "<footer>HireGauge scores demonstrated skills, projects, contributions, and experience — not "
        "demographics. Pedigree/GPA count only where a domain's real bar uses them. Evidence is shown "
        "per dimension.</footer></body></html>"
    )
    return "".join(out)
