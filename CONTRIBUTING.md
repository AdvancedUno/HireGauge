# Contributing to HireGauge

Thanks for helping make HireGauge a genuinely useful, fair, and accurate tool.

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,web]"
cp .env.example .env
pytest
ruff check .
```

## Project map
- `src/hiregauge/collectors/` — turn an identity (GitHub user, Codeforces handle, …) into a typed `Signal`.
- `src/hiregauge/analysis/` — verification (authenticity, red/green flags) on top of collected signals.
- `src/hiregauge/agents/` — the 5 domain rubrics (dimensions, weights, thresholds, level expectations, prompts).
- `src/hiregauge/evaluator.py` — deterministic scoring + LLM rubric pass, blended and level-calibrated.
- `src/hiregauge/report/` — render Markdown / JSON / HTML + the candidate action plan.
- `docs/rubrics.md` — cited rubric grounding (weights, calibration notes, and sources).

## Working with the repo's Claude Code helpers
This repo ships dev helpers under `.claude/` (used automatically when you work here with Claude Code):
- **skills**: `hiregauge-rubric-authoring`, `hiregauge-collector`, `hiregauge-run`.
- **subagents**: `rubric-researcher`, `collector-builder`, `eval-calibrator`, `report-auditor`.

## Principles
1. **Ground claims in citations.** Any threshold/weight a rubric uses must trace to a real source in
   `docs/rubrics.md`. No invented cutoffs.
2. **Collectors never hard-fail.** Missing/broken sources degrade the report; they don't abort the run.
   Always cache external calls and record a test fixture.
3. **Deterministic where a ground truth exists**; reserve the LLM for judgment that needs reading.
4. **Fairness.** Don't let name, gender, demographics, location, or institution/GPA drive a score beyond what
   the research defensibly supports.
5. **Calibrate to experience level.** Expectations differ for intern vs senior vs PhD.

## Adding things
- **A data source** → follow the `hiregauge-collector` skill; add a fixture + test; wire into `pipeline.py`.
- **An agent / rubric change** → follow the `hiregauge-rubric-authoring` skill; validate with the
  `eval-calibrator` subagent; update `docs/rubrics.md`.
- Run a `report-auditor` pass before sending a PR that touches scoring or templates.

## PRs
Keep changes focused, add/adjust tests, and run `pytest` + `ruff` (update `docs/rubrics.md` if you change weights).

## Code of Conduct
By participating, you agree to abide by our [Code of Conduct](.github/CODE_OF_CONDUCT.md).
