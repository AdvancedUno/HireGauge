# HireMe — Specialized, Multi-Agent Candidate Evaluation

> This is the living design doc for HireMe. It mirrors the approved plan and is updated as the
> project evolves. See `TODO.md` (same folder) for the build checklist.

## Context

HireMe is a new open-source project, **inspired by — but not derived from** — HackerRank's
`interviewstreet/hiring-agent` (cloned read-only at `../hiring-agent/`, MIT © HackerRank). The
reference is a single-track, one-rubric pipeline: resume PDF → per-section LLM extraction → GitHub
enrichment → score against **one generic "Software Intern" rubric** (Open Source 35 / Self-Projects 30 /
Production 25 / Technical Skills 10 + ad-hoc bonus/deductions) → stdout + CSV, on Ollama/Gemini via
`python score.py <pdf>`.

HireMe's thesis: real companies evaluate candidates **very differently by domain**, look at **more than
a resume + GitHub**, and judge against **level-appropriate expectations**. HireMe ships **5 specialized
evaluator agents** — `quant`, `airesearch`, `bigtech`, `general`, `university` — each with its own
research-grounded rubric, signal weighting, thresholds, and red/green flags. It fuses multiple real data
sources, **verifies** signals instead of trusting claims, blends **deterministic API-grounded scoring with
LLM judgment**, calibrates to the candidate's **experience level / YoE**, and produces a **detailed
candidate report** with a prioritized "what to do next" plan.

**Locked decisions**
- **Audience:** candidate self-assessment (coaching tone, gap analysis, action plan). Engine is
  mode-agnostic so a `recruiter` mode can be added later cheaply.
- **LLM backend:** Claude-first, pluggable. Default `claude-opus-4-8`; pluggable Ollama (free/local),
  optional OpenAI/Gemini. Needs `ANTHROPIC_API_KEY` by default.
- **Data sources:** resume + GitHub (core) + publications + competitive programming + portfolio/blog +
  Kaggle — **each agent uses/weights them differently**.
- **Experience level:** users set `--yoe` and `--level` (and optional `--target-level`); evaluation is
  calibrated to the bar for that stage.
- **Build approach:** fresh, original `hireme/` package; no HackerRank source copied; std libs do the work.

## Differentiation vs. the reference (surface in README)
1. 5 domain-specialized agents vs one generic intern rubric.
2. Multi-source fusion (GitHub + Scholar/arXiv + Codeforces/LeetCode + Kaggle + portfolio) vs resume+GitHub.
3. Verification/authenticity layer (fake-star detection, commit authenticity, claim cross-checking) —
   targets the gaming/shallowness criticisms of HackerRank/HireVue/CodeSignal.
4. Deterministic ground-truth scoring blended with LLM judgment (not LLM-only).
5. **Experience-level calibration** (YoE/seniority/stage) — expectations differ for intern vs senior vs PhD.
6. Candidate-coaching report with a prioritized, concrete action plan.
7. Claude-first with structured outputs + adaptive thinking; transparent, evidence-cited, configurable weights.

## Repo layout (src/ layout, pip-installable)

```
hireme/
  pyproject.toml  README.md  LICENSE  CONTRIBUTING.md  .env.example  .gitignore
  docs/           PLAN.md (this file)  TODO.md  rubrics.md (later)
  src/hireme/
    __init__.py
    cli.py                  # Typer app + flags; thin — delegates to pipeline
    config.py               # Settings via pydantic-settings (.env / env vars)
    models.py               # Pydantic schemas incl. ExperienceContext, CandidateProfile, Evaluation, Report
    pipeline.py             # collect -> normalize -> analyze -> evaluate -> report
    cache.py                # on-disk JSON cache for API responses (dev cost control)
    collectors/             # resume, github, scholar, competitive, kaggle, web (fault-tolerant)
    analysis/               # github_authenticity, red_flags
    agents/                 # base + quant/airesearch/bigtech/general/university + registry
    llm/                    # base, anthropic_provider (default), ollama/openai/gemini, factory
    report/                 # renderer + templates (md/html/json, action_plan)
    prompts/                # shared fairness header + per-agent rubric jinja
  tests/                    # mocked-API fixtures + deterministic-scorer unit tests
  .github/workflows/ci.yml
  .claude/                  # (optional, polish phase) repo-local subagents + skills to aid development
```

## Experience-level calibration (new requirement)

`ExperienceContext` (in `models.py`) captures `yoe`, `stage`, `target_stage`, `current_title`, `notes`.
`CareerStage` enum spans industry + academia: `student, intern, new-grad, junior, mid, senior, staff,
principal, masters-applicant, phd-applicant, phd-student, postdoc`.

- **CLI:** `--yoe <float>`, `--level <stage>`, `--target-level <stage>`, `--title <str>`.
- **Effect:** each agent defines level-aware expectations; the rubric prompt is told "evaluate against the
  bar for a {stage} candidate with {yoe} YoE targeting {target_stage}". Examples: a `new-grad` bigtech
  candidate is lightly judged on system design; a `senior` one heavily, and its absence is a red flag. A
  `phd-applicant` without first-author papers is normal-to-borderline; a `postdoc` without them is a red flag.
- Deterministic thresholds also shift by stage where it matters (e.g., expected GitHub depth/impact).

## Pipeline (`pipeline.py`)
1. **Collect** — only the collectors for provided inputs + signals the chosen agent needs. Fault-tolerant
   (missing/failed source degrades the report, never aborts). Cached by source+identity.
2. **Normalize** → one `CandidateProfile` (incl. `ExperienceContext`).
3. **Analyze** → `analysis/` attaches verification facts (authenticity, flags).
4. **Evaluate** → `evaluator.py` runs the selected agent:
   - **Deterministic layer:** objective sub-scores in code from ground-truth signals (Codeforces tier,
     h-index bucket, GitHub authenticity, recency) — pure, unit-testable, stage-aware.
   - **LLM layer:** one `messages.parse()` call with the agent's rubric system prompt (prompt-cached) +
     normalized profile + deterministic facts + experience context → Pydantic `Evaluation`. Model
     `claude-opus-4-8`, `thinking={"type":"adaptive"}`, `output_config={"effort":"high"}`.
   - **Blend & calibrate:** combine per dimension by weights → overall score, band, strengths, gaps, flags,
     action plan.
5. **Report** → render per `--mode`/`--format`. Candidate mode leads with a prioritized "what to do next".

## Agents (the specialization)
Each declares weighted `dimensions`, consumed `signals`, numeric `thresholds`, domain `green/red flags`,
level expectations, and Jinja prompt fragments. Initial calibration from gathered research:
- **quant** — competitive programming (Codeforces/IOI/ICPC) & math olympiad (IMO/Putnam/USAMO) highest;
  CF tiers (~2400+ strong / 1900–2400 solid / <1600 weak); tier-1 internships; prob/stats + low-latency/
  C++/OCaml; pedigree secondary.
- **airesearch** — first-author NeurIPS/ICML/ICLR/CVPR/ACL; citations/h-index; GitHub ML depth + OSS to
  PyTorch/JAX/HF; Kaggle; paper reproductions; research taste (blog/X).
- **bigtech** — DSA/LeetCode; system design; internship pedigree; quantified impact; YoE/leveling; referral
  flag; behavioral/leadership (Amazon-LP style).
- **general** — GitHub project quality/originality (real vs tutorial), skills breadth, portfolio/comms, OSS.
- **university** — research experience & first-author pubs; letters/SOP/research-fit (if provided); GPA;
  undergrad institution; advisor-fit; GRE de-emphasized.

## LLM integration (Claude-first; verified vs claude-api skill)
- Default `claude-opus-4-8`; `claude-sonnet-4-6` as cheaper `--model`.
- Structured scoring via `client.messages.parse(..., output_format=Evaluation)` → `response.parsed_output`.
- `thinking={"type":"adaptive"}` + `output_config={"effort":"high"}`. No `budget_tokens`/`temperature`.
- Prompt-cache the large rubric system prompt (`cache_control:{type:"ephemeral"}`).
- Resume: default `pymupdf4llm` text extract (provider-agnostic); Anthropic may also attach the PDF as a
  `document` block for higher-fidelity parsing.
- Other providers implement the same `complete_structured` via JSON-schema/JSON-mode (quality caveat documented).

## Reusable *patterns* from the reference (re-implemented originally, not copied)
GitHub API usage shape (profile, `repos?sort=updated`, contributors, open-source-vs-self classification,
`GITHUB_TOKEN` rate-limit handling, fork filtering) — see `../hiring-agent/github.py` for the idea; extended
with languages, commit recency/authenticity, README sampling, fake-star checks. Plus standard Jinja
templating, Pydantic schemas, on-disk caching, `.env` config, provider factory.

## Rubric grounding (cited)
Bake researched signals into each agent's rubric prompt + thresholds and `docs/rubrics.md`. Keep weights in
config (tunable + auditable = transparency differentiator).

## Tech stack
Python 3.11+, `typer`+`rich`, `pydantic` v2 + `pydantic-settings`, `anthropic`, `httpx`/`requests`,
`pymupdf4llm`, `trafilatura`, `scholarly` (optional), `jinja2`, `pytest`. Optional: `ollama`, `openai`,
`google-genai`, `kaggle`.

## Build phases (tracked in TODO.md)
1. Skeleton & core (pyproject, config, models incl. ExperienceContext, cli flags, llm anthropic+factory, cache).
2. Collectors (resume + GitHub first, then competitive/scholar/kaggle/web). Fault-tolerant + cached.
3. Analysis (github_authenticity, red_flags).
4. Agents + evaluator (base, 5 agents, deterministic+LLM blend, rubric prompts, level calibration).
5. Report (Markdown primary, then JSON + HTML; candidate action plan).
6. Polish (README, CONTRIBUTING, LICENSE, docs/rubrics.md, tests, CI, .env.example, optional .claude agents/skills).

## Verification (end-to-end)
- `pip install -e .`; set `ANTHROPIC_API_KEY` (+ `GITHUB_TOKEN`).
- Smoke test with the user's own inputs in the repo (resume PDF + a real GitHub user), all 5 agents; confirm
  emphasis differs sensibly (quant penalizes missing CP/olympiad; airesearch penalizes missing publications).
- Confirm level calibration: same profile at `--level intern` vs `--level senior` shifts expectations.
- Unit tests for deterministic scorers (CF tier, h-index bucket, fork:star authenticity); collectors vs
  recorded JSON; `--provider ollama` offline path. Prompt-cache hit on second run.

## Open considerations
- LeetCode/LinkedIn have no stable official API — LeetCode best-effort unofficial; LinkedIn = manual PDF/export.
  `scholarly` is rate-limited — support manual `--scholar`/`--orcid`/`--arxiv` links.
- Exact per-agent dimension weights + per-stage expectations — start from research, expose in config, refine.
