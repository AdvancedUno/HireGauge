# HireMe — Build TODO

Living checklist. Keep in sync as we build. See `PLAN.md` for the full design.

## Phase 0 — Planning ✅
- [x] Study the HackerRank reference (`../hiring-agent/`).
- [x] Research real-world hiring signals (quant / AI research / big tech / general / university), cited.
- [x] Approve plan; write `docs/PLAN.md`.

## Phase 1 — Scaffold & dev helpers  ✅ (installs + runs)
- [x] `docs/TODO.md` (this file).
- [x] Repo-local Claude Code helpers:
  - [x] `.claude/agents/rubric-researcher.md`
  - [x] `.claude/agents/collector-builder.md`
  - [x] `.claude/agents/eval-calibrator.md`
  - [x] `.claude/agents/report-auditor.md`
  - [x] `.claude/skills/hireme-rubric-authoring/SKILL.md`
  - [x] `.claude/skills/hireme-collector/SKILL.md`
  - [x] `.claude/skills/hireme-run/SKILL.md`
- [x] Project meta: `pyproject.toml`, `.gitignore`, `.env.example`, `README.md`, `LICENSE`, `CONTRIBUTING.md`.
- [x] Core: `src/hireme/{__init__,config,cache}.py`.
- [x] `src/hireme/models.py` — incl. `ExperienceContext` (yoe/stage/target_stage) + `CareerStage` enum.
- [x] `src/hireme/llm/{base,anthropic_provider,factory}.py` (anthropic default; lazy imports; ollama/openai/gemini stubbed).
- [x] `src/hireme/agents/{base,registry}.py` + 5 agent specs (quant/airesearch/bigtech/general/university).
- [x] `src/hireme/cli.py` — flags incl. `--yoe`/`--level`/`--target-level`; `hireme --help` / `agents` / run-preview work.
- [x] Verified: `pip install -e .` succeeds; `hireme agents` lists all 5 rubrics (weights sum to 100).

## Phase 2 — Collectors  (fault-tolerant + cached + fixtures)
- [ ] `collectors/base.py` — `Collector` protocol + never-hard-fail contract.
- [ ] `collectors/resume.py` — pymupdf4llm text; optional native-PDF block for Anthropic.
- [ ] `collectors/github.py` — profile, repos, languages, stars/forks, contributors, recency, README sampling.
- [ ] `collectors/competitive.py` — Codeforces API; LeetCode (best-effort); olympiad mentions.
- [ ] `collectors/scholar.py` — scholarly + arXiv/ORCID + manual links.
- [ ] `collectors/kaggle.py` — Kaggle API.
- [ ] `collectors/web.py` — portfolio/blog fetch + main-text extraction (trafilatura, graceful fallback).

## Phase 3 — Analysis
- [ ] `analysis/github_authenticity.py` — fake-star (fork:star ratio, stargazer sampling), commit authenticity, tutorial-vs-real.
- [ ] `analysis/red_flags.py` — universal + per-domain green/red flags.

## Phase 4 — Agents + evaluator
- [ ] Per-agent rubric prompts under `prompts/templates/` + level expectations.
- [ ] `evaluator.py` — deterministic scoring + LLM `messages.parse()` blend; level calibration.
- [ ] `pipeline.py` — collect → normalize → analyze → evaluate → report.

## Phase 5 — Report
- [ ] `report/renderer.py` + templates: Markdown (primary), JSON, HTML.
- [ ] Candidate "what to do next" prioritized action plan.

## Phase 6 — Quality & polish
- [~] Tests: agent-registry invariants done (`tests/test_agents.py`, ruff clean). TODO: deterministic scorers
      (CF tier, h-index bucket, fork:star authenticity); collectors vs recorded JSON; ollama offline path.
- [x] CI: `.github/workflows/ci.yml` (ruff + pytest, py3.11/3.12) + `.github/CODE_OF_CONDUCT.md` present.
- [ ] `docs/rubrics.md` — cited per-agent signals & weights.
- [ ] README polish (differentiation + "inspired-by-not-copied").

## Verify (end-to-end)
- [ ] Smoke matrix: 5 agents × {intern, senior} on the bundled resume + a real GitHub user.
- [ ] Level calibration shifts expectations (intern vs senior; phd-applicant vs postdoc).
- [ ] Prompt-cache hit on 2nd run (`usage.cache_read_input_tokens > 0`).

## Open questions / parking lot
- LeetCode/LinkedIn lack stable APIs → best-effort / manual export.
- Final per-agent dimension weights & per-stage expectations — refine with `eval-calibrator`.
