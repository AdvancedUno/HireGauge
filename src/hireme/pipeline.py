"""Orchestration: resolve identities (flag -> discovered), collect, evaluate, report.

The resume is the hub: identifiers not passed as flags are auto-discovered from it.
Collectors are fault-tolerant; a failed/missing source degrades the report (recorded
in ``collection_notes``) but never aborts the run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from .agents import Agent, get_agent
from .analysis import assess_github
from .cache import Cache
from .collectors import (
    collect_github,
    collect_kaggle,
    collect_publications,
    collect_resume,
    collect_web,
)
from .config import get_settings
from .evaluator import evaluate
from .llm.base import LLMProvider
from .llm.factory import build_provider
from .models import (
    CandidateProfile,
    DimensionScore,
    DiscoveredProfiles,
    Evaluation,
    ExperienceContext,
    Report,
    ResumeParsed,
)


@dataclass
class RunConfig:
    agent: str
    resume: str | None = None
    github: str | None = None
    scholar: str | None = None
    orcid: str | None = None
    arxiv: str | None = None
    codeforces: str | None = None
    leetcode: str | None = None
    kaggle: str | None = None
    site: str | None = None
    linkedin: str | None = None
    role: str | None = None
    jd: str | None = None
    experience: ExperienceContext = field(default_factory=ExperienceContext)
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    mode: str = "candidate"
    no_cache: bool = False


def _fallback_eval(agent: Agent, error: str) -> Evaluation:
    dims = [
        DimensionScore(
            key=d.key, label=d.label, score=0.0, max=d.weight, weight=d.weight,
            evidence="Not evaluated.", confidence=0.0,
        )
        for d in agent.dimensions
    ]
    return Evaluation(
        agent=agent.name, overall_score=0.0, band="Not evaluated",
        summary=f"Evaluation could not be completed: {error}",
        dimensions=dims, strengths=[], gaps=[], green_flags=[], red_flags=[], action_plan=[],
    )


_PARSE_SYSTEM = (
    "Extract a structured view of this resume as JSON matching the schema. Use the resume's own "
    "wording; do not invent, infer, or embellish. Omit any field you cannot find."
)


def _parse_resume(
    text: str, provider: LLMProvider, cache: Cache, model: str
) -> ResumeParsed | None:
    if not text.strip():
        return None
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    key = f"resume_parse:{digest}:{model}"
    cached = cache.get(key)
    if cached is not None:
        try:
            return ResumeParsed(**cached)
        except Exception:
            pass
    try:
        out = provider.complete_structured(
            system=_PARSE_SYSTEM, user=text[:12000], schema=ResumeParsed
        )
    except Exception:
        return None
    if not isinstance(out, ResumeParsed):
        return None
    cache.set(key, out.model_dump())
    return out


def run(cfg: RunConfig, *, provider: LLMProvider | None = None) -> Report:
    settings = get_settings()
    cache = Cache(settings.cache_dir, enabled=settings.cache_enabled and not cfg.no_cache)
    agent = get_agent(cfg.agent)
    notes: list[str] = []
    if provider is None:
        provider = build_provider(cfg.provider, cfg.model, settings)

    # --- resume (the hub) ---
    resume_sig = collect_resume(cfg.resume) if cfg.resume else None
    if cfg.resume and resume_sig is None:
        notes.append(f"Could not read resume: {cfg.resume}")
    if cfg.resume is None:
        notes.append("No resume provided — evaluating from flags/links only.")
    if resume_sig is not None:
        resume_sig.parsed = _parse_resume(resume_sig.text, provider, cache, cfg.model)
    discovered = resume_sig.discovered if resume_sig else DiscoveredProfiles()

    # Sources with no collector in this build (codeforces/leetcode/linkedin) are still
    # surfaced to the evaluator as identifiers and acknowledged in notes — not silently
    # dropped just because the CLI accepted the flag.
    manual = {
        k: v
        for k, v in {
            "codeforces": cfg.codeforces, "leetcode": cfg.leetcode, "linkedin": cfg.linkedin,
        }.items()
        if v
    }
    if manual:
        discovered = discovered.model_copy(update=manual)
        if resume_sig is not None:
            resume_sig.discovered = discovered
    for src in ("codeforces", "leetcode"):
        if manual.get(src):
            notes.append(
                f"{src}: handle '{manual[src]}' recorded but contest stats aren't fetched "
                "in this build — scored from resume text"
            )
    if cfg.linkedin:
        notes.append("linkedin: provided but not parsed (LinkedIn blocks automated access)")
    if cfg.jd:
        notes.append("jd: job-description matching isn't wired yet — using --role text instead")

    def resolve(flag: str | None, disc: str | None, label: str) -> str | None:
        if flag:
            return flag
        if disc:
            notes.append(f"{label}: auto-discovered from resume ({disc})")
            return disc
        return None

    # --- github ---
    github_sig = None
    if "github" in agent.signals:
        gh_id = resolve(cfg.github, discovered.github, "github")
        if gh_id:
            github_sig = collect_github(gh_id, settings=settings, cache=cache)
            if github_sig is None:
                notes.append(f"GitHub fetch failed for '{gh_id}'")
            else:
                github_sig.authenticity = assess_github(github_sig)

    # --- publications (Scholar best-effort) ---
    publications_sig = None
    if "publications" in agent.signals:
        s_url = cfg.scholar or discovered.scholar
        orcid = cfg.orcid or discovered.orcid
        arxiv = cfg.arxiv or discovered.arxiv
        if s_url or orcid or arxiv:
            publications_sig = collect_publications(
                scholar_url=s_url, orcid=orcid, arxiv=arxiv, cache=cache
            )
            if publications_sig is None:
                notes.append(
                    "publications: not fetched (needs a Google Scholar URL + `pip install "
                    "\"hireme[scholar]\"`) — scored from resume text"
                )

    # --- kaggle ---
    kaggle_sig = None
    if "kaggle" in agent.signals:
        k = cfg.kaggle or discovered.kaggle
        if k:
            kaggle_sig = collect_kaggle(k, settings=settings, cache=cache)
            notes.append(
                f"kaggle: profile stats are JS-rendered and not fetched — handle '{k}' recorded; "
                "medals/tier scored from resume text"
            )

    # --- web (portfolio / blog) ---
    web_sigs = []
    if "web" in agent.signals:
        urls: list[str] = []
        if cfg.site:
            urls.append(cfg.site)
        urls.extend(discovered.websites or [])
        for url in list(dict.fromkeys(urls))[:3]:
            w = collect_web(url, cache=cache)
            if w:
                web_sigs.append(w)
        if urls and not web_sigs:
            notes.append("web: could not fetch the portfolio/site page(s)")

    profile = CandidateProfile(
        experience=cfg.experience,
        target_role=cfg.role,
        resume=resume_sig,
        github=github_sig,
        publications=publications_sig,
        kaggle=kaggle_sig,
        web=web_sigs,
        collection_notes=notes,
    )

    try:
        evaluation = evaluate(agent, profile, provider)
    except Exception as exc:  # noqa: BLE001 - surface as a report note, don't crash the CLI
        evaluation = _fallback_eval(agent, f"{type(exc).__name__}: {exc}")

    return Report(
        agent=agent.name,
        mode=cfg.mode,
        model=cfg.model,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        profile=profile,
        evaluation=evaluation,
    )
