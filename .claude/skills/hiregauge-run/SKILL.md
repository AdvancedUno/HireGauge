---
name: hiregauge-run
description: How to run HireGauge end-to-end and interpret/verify its output — CLI flags, providers, the golden-profile smoke matrix (5 agents x experience levels), and the prompt-cache check. Use when running, testing, demoing, or verifying the tool.
---

# Running & verifying HireGauge

HireGauge evaluates a candidate's resume + GitHub + extras through one of five domain agents, calibrated to the
candidate's experience level, and emits a coaching report.

## Setup
```bash
cd hiregauge
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash; or .venv/bin/activate on *nix
pip install -e ".[dev,gemini]"
cp .env.example .env   # set GEMINI_API_KEY (default provider), GITHUB_TOKEN (raises GH rate limit)
```

## Core usage
```bash
hiregauge --agent quant \
       --resume "../EunHo Lee Main Resume SWE.pdf" \
       --github <user> --codeforces <handle> --scholar <url> --kaggle <handle> --site <url> \
       --yoe 1 --level new-grad --target-level junior \
       --model gemini-2.5-flash --format md --out report.md
hiregauge agents          # list agents + the signals/dimensions each weights
hiregauge --help
```

Key flags: `--agent {quant,airesearch,bigtech,general,university}` (required); inputs
`--resume/--github/--scholar/--orcid/--arxiv/--codeforces/--leetcode/--kaggle/--site/--linkedin`;
**experience** `--yoe <float> --level <stage> --target-level <stage> --title <str>`
(stages: student, intern, new-grad, junior, mid, senior, staff, principal, masters-applicant, phd-applicant,
phd-student, postdoc); `--provider {gemini,anthropic,ollama,openai}` + `--model`; `--mode {candidate,recruiter}`;
`--format {md,json,html}` `--out`; `--no-cache` `--verbose`.

## Reading a report
Overall score + band (Strong / Competitive / Developing / Early); per-dimension score with **evidence** and
confidence; green/red flags; and (candidate mode) a prioritized **"what to do next"** action plan tied to the
weakest high-weight dimensions. Verification facts (e.g. "GitHub stars look organic: fork:star 0.18") appear
inline.

## Verify a change (golden smoke matrix)
- **Specialization:** run the *same* inputs through all 5 agents — emphasis must differ (quant penalizes
  missing CP/olympiad; airesearch penalizes missing publications).
- **Level calibration:** run the *same* profile at `--level intern` vs `--level senior` (and `phd-applicant`
  vs `postdoc` for `university`) — expectations and red flags must shift.
- **Determinism:** `pytest` — deterministic scorers (CF tier, h-index bucket, fork:star authenticity) and
  collector fixture tests pass.
- **Offline path:** `--provider ollama` produces a structurally valid report (lower judgment quality).
- **Prompt cache:** run twice with `--verbose`; the second run should report `cache_read_input_tokens > 0`.

## Cost notes
Default is Gemini `gemini-2.5-flash` (fast, low-cost). Use `--model gemini-2.5-pro` for higher-quality
judgment, or `--provider anthropic --model claude-opus-4-8` for Claude. Responses are cached on disk, so
repeated runs are cheap. For calibration sweeps, drive everything through the `eval-calibrator` agent.
