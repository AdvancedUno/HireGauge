<h1 align="center">HireGauge</h1>

<p align="center"><strong>Know exactly how a quant firm, an AI research lab, big tech, or a PhD committee
would actually read your resume, GitHub, and portfolio — and what to fix next.</strong></p>

<p align="center">
  <a href="https://github.com/AdvancedUno/HireGauge/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/AdvancedUno/HireGauge/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue.svg">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg">
  <img alt="LLM" src="https://img.shields.io/badge/LLM-Gemini%20default%20·%20pluggable-8A2BE2.svg">
</p>

---

HireGauge is an open-source CLI that evaluates a candidate's **resume + GitHub + publications + competitive
programming + Kaggle + portfolio** through one of **five domain-specialized agents**, calibrated to the
candidate's **experience level**, and scored against a **strict, anchored bar** that mirrors a real screen.
It returns an evidence-cited report with a screen verdict, an estimated applicant-pool percentile, and a
prioritized *"what to do next"* plan.

It is **inspired by — but contains no code copied from** — HackerRank's open-source
[`hiring-agent`](https://github.com/interviewstreet/hiring-agent). HireGauge is deliberately different and more
advanced: domain specialization, multi-source signal fusion, signal *verification* (not blind trust),
experience-level calibration, strict anti-inflation scoring, and a coaching report.

## The five agents

| `--agent`     | Evaluates like…              | Bar | Leans hardest on |
| ------------- | ---------------------------- | --- | ---------------- |
| `quant`       | Jane Street / Citadel / HRT  | elite | math & probability/statistics, low-latency systems, research, experience (algorithmic problem-solving = one signal) |
| `airesearch`  | Anthropic / OpenAI / DeepMind| elite | first-author papers (NeurIPS/ICML/ICLR), citations/h-index, ML GitHub + OSS, Kaggle |
| `bigtech`     | Google / Meta / Amazon       | elite | DSA/LeetCode, system design, internship pedigree, quantified impact, leadership |
| `general`     | broad software hiring        | standard | real (vs tutorial) GitHub projects, skills breadth, portfolio, communication |
| `university`  | CS/ML PhD & Masters admissions | standard | research experience & first-author pubs, research-fit, GPA (GRE de-emphasized) |

Each agent uses the same data sources but **weights them differently**, with thresholds and red/green flags
grounded in how these places actually hire (see `docs/rubrics.md`). The three **elite** agents emulate a
top-tier screen where most real applicants don't clear the bar; the two **standard** agents apply a strict
but ordinary hiring screen.

## What makes it different
1. **5 specialized agents** instead of one generic rubric.
2. **Multi-source fusion** — GitHub + Scholar/arXiv + Codeforces/LeetCode + Kaggle + portfolio.
3. **Verification layer** — fake-star detection, commit-history authenticity, resume-claim cross-checking.
4. **Deterministic ground-truth scoring blended with LLM judgment** — hard signals (GitHub activity, fetched
   h-index/citations) anchor the model's per-dimension scores rather than being left to the LLM.
5. **Strict, anchored scoring** — every dimension is scored as a fraction of its max against a defined scale
   that *defaults low without evidence*, so polished-but-empty résumés don't get inflated.
6. **Experience-level calibration** — the same profile is judged differently at intern vs senior vs PhD.
7. **Coaching report** with a screen verdict, percentile estimate, and a concrete, prioritized action plan.
8. **Pluggable LLM** — Gemini by default; switch to Claude / OpenAI / local Ollama with `--provider`.

## What the report tells you
- **Overall score (0–100) + band** — `Strong` (≥80), `Competitive` (≥60), `Developing` (≥40), or `Early`.
- **Screen verdict** — `yes` (Strong), `borderline` (Competitive), or `no`, derived from the band so it can
  never contradict the score.
- **Estimated percentile** vs. the realistic applicant pool for the role+level.
- **Where you stand** — a positioning line against that pool.
- **Per-dimension scores with cited evidence**, plus strengths, gaps, green/red flags, and a prioritized
  action plan. `--mode recruiter` reframes the same evaluation for a hiring reader.

## Install
```bash
git clone <repo> && cd hiregauge
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev,gemini]"
cp .env.example .env      # set GEMINI_API_KEY  (and GITHUB_TOKEN for higher GitHub limits)
```

Optional extras: `web` (portfolio extraction), `scholar` (Google Scholar), `kaggle`, `anthropic`/`openai`/
`ollama` providers, or `all`. Example: `pip install -e ".[dev,gemini,web,scholar]"`.

## Quickstart
```bash
hiregauge --agent quant \
       --resume resume.pdf \
       --github your-handle --scholar <url> --site <url> \
       --yoe 1 --level new-grad --target-level junior \
       --format md --out report.md

hiregauge agents     # list agents and the dimensions/weights each scores
hiregauge --help
```
The resume is the hub: identifiers you don't pass as flags (github, linkedin, site, scholar, etc.) are
auto-discovered from it. If you omit `--agent`, it defaults to `general`.

### Key flags
- `--agent {quant,airesearch,bigtech,general,university}` (defaults to `general`)
- inputs: `--resume --github --scholar/--orcid/--arxiv --codeforces/--leetcode --kaggle --site --linkedin`
- caching: external signals (GitHub/Scholar/web) are cached for ~24h. `--refresh` refetches
  them and rewrites the cache (the resume parse is kept); `--no-cache` bypasses the cache entirely.
- e