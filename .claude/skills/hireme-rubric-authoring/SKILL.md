---
name: hireme-rubric-authoring
description: Conventions and a checklist for authoring or calibrating a HireMe evaluator agent — dimension design, weight normalization, the deterministic-vs-LLM split, experience-level (YoE/stage) expectations, grounding claims with citations, and prompt-fragment structure. Use whenever you add or edit an agent under src/hireme/agents/ or its rubric prompt/weights.
---

# Authoring a HireMe evaluator agent

A HireMe agent encodes how one domain (`quant`, `airesearch`, `bigtech`, `general`, `university`) actually
evaluates candidates, calibrated to the candidate's experience level. Keep it **declarative, grounded, and
auditable**.

## Anatomy of an agent (`src/hireme/agents/<name>.py`)
Subclass the base `Agent` and declare:
- `name`, `description`.
- `dimensions`: a list of `(key, label, weight, max, deterministic?)`. **Weights sum to 100.** `max` is the
  raw per-dimension ceiling; the evaluator normalizes to the weight.
- `signals`: which collected sources this agent consumes (resume, github, publications, competitive, kaggle, web).
- `thresholds`: numeric, ground-truth cut points (e.g. Codeforces tiers, h-index buckets, first-author counts).
- `level_expectations`: per `CareerStage`, which dimensions de/emphasize and which absences become red flags.
- `green_flags` / `red_flags`: domain-specific detectors (deterministic where possible).
- prompt fragments (Jinja under `src/hireme/prompts/templates/`): the domain criteria appended to the shared
  fairness/anti-bias header.

## Rules
1. **Deterministic where a ground truth exists.** If an API gives a number (CF rating, h-index, stars, fork
   ratio), score it in code (pure function, unit-tested) and feed the LLM the *fact*, not the raw blob. Reserve
   the LLM for judgment that needs reading (project complexity, research taste, impact, communication).
2. **Ground every threshold in a citation.** Mirror it into `docs/rubrics.md` with the source. No made-up cutoffs.
3. **Calibrate to level.** State expectations per stage. Don't fault an intern for missing senior signals, or a
   `phd-applicant` for a `postdoc`-level record. Make the absence a red flag only at the stage where it should be.
4. **Fairness first.** Never let name, gender, demographics, location, or institution/GPA drive a score beyond
   what the research defensibly supports (pedigree may be a *secondary* signal, e.g. quant — never the driver).
   Keep the shared anti-bias header in the system prompt.
5. **Specificity.** Evidence and flags must point at a real signal, not generic phrasing.
6. **Keep weights in config/data, not buried in prose** — so they're tunable and reviewable.

## Checklist before committing an agent
- [ ] Weights sum to 100; bands map to sane score ranges.
- [ ] Each deterministic threshold has a cited source in `docs/rubrics.md`.
- [ ] `level_expectations` cover the realistic stages for this domain.
- [ ] Green/red flags are domain-specific and mostly deterministic.
- [ ] Prompt fragment includes the shared fairness header + concrete, cited criteria.
- [ ] Validated with the `eval-calibrator` agent (specialization + level shifts behave correctly).

When in doubt about *what* a domain weights, dispatch the `rubric-researcher` agent first.
