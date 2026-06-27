<h1 align="center">HireMe</h1>

<p align="center"><strong>Know exactly how a quant firm, an AI research lab, big tech, or a PhD committee
would actually read your resume, GitHub, and portfolio — and what to fix next.</strong></p>

<p align="center">
  <a href="https://github.com/AdvancedUno/HireMe/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/AdvancedUno/HireMe/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue.svg">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg">
  <img alt="LLM" src="https://img.shields.io/badge/LLM-Claude%20(pluggable)-8A2BE2.svg">
</p>

---

HireMe is an open-source CLI that evaluates a candidate's **resume + GitHub + publications + competitive
programming + Kaggle + portfolio** through one of **five domain-specialized agents**, calibrated to the
candidate's **experience level**, and produces a detailed, evidence-cited report with a prioritized
*"what to do next"* plan.

It is **inspired by — but contains no code copied from** — HackerRank's open-source
[`hiring-agent`](https://github.com/interviewstreet/hiring-agent). HireMe is deliberately different and more
advanced: domain specialization, multi-source signal fusion, signal *verification* (not blind trust),
experience-level calibration, and a coaching report.

## The five agents

| `--agent`     | Evaluates like…              | Leans hardest on |
| ------------- | ---------------------------- | ---------------- |
| `quant`       | Jane Street / Citadel / HRT  | math & probability/statistics, low-latency systems, research, experience (algorithmic problem-solving = one signal) |
| `airesearch`  | Anthropic / OpenAI / DeepMind| first-author papers (NeurIPS/ICML/ICLR), citations/h-index, ML GitHub + OSS, Kaggle |
| `bigtech`     | Google / Meta / Amazon       | DSA/LeetCode, system design, internship pedigree, quantified impact, leadership |
| `general`     | broad software hiring        | real (vs tutorial) GitHub projects, skills breadth, portfolio, communication |
| `university`  | CS/ML PhD & Masters admissions | research experience & first-author pubs, research-fit, GPA (GRE de-emphasized) |

Each agent uses the same data sources but **weights them differently**, with thresholds and red/green flags
grounded in how these places actually hire (see `docs/rubrics.md`).

## What makes it different
1. **5 specialized agents** instead of one generic rubric.
2. **Multi-source fusion** — GitHub + Scholar/arXiv + Codeforces/LeetCode + Kaggle + portfolio.
3. **Verification layer** — fake-star detection, commit-history authenticity, resume-claim cross-checking.
4. **Deterministic ground-truth scoring blended with LLM judgment** (e.g. Codeforces rating → tier in code).
5. **Experience-level calibration** — the same profile is judged differently at intern vs senior vs PhD.
6. **Coaching report** with a concrete, prioritized action plan.
7. **Pluggable LLM** — Gemini by default; switch to Claude / OpenAI / local Ollama with `--provider`.

## Install
```bash
git clone <repo> && cd hireme
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev,gemini]"
cp .env.example .env      # set GEMINI_API_KEY  (and GITHUB_TOKEN for higher GitHub limits)
```

## Quickstart
```bash
hireme --agent quant \
       --resume resume.pdf \
       --github your-handle --codeforces your-handle --scholar <url> --site <url> \
       --yoe 1 --level new-grad --target-level junior \
       --format md --out report.md

hireme agents     # list agents and the signals each weights
hireme --help
```

### Key flags
- `--agent {quant,airesearch,bigtech,general,university}` (required)
- inputs: `--resume --github --scholar/--orcid/--arxiv --codeforces/--leetcode --kaggle --site --linkedin`
- experience: `--yoe <float> --level <stage> --target-level <stage> --title <str>`
  (stages: `student, intern, new-grad, junior, mid, senior, staff, principal, masters-applicant, phd-applicant, phd-student, postdoc`)
- model: `--provider {gemini,anthropic,ollama,openai}` `--model` (default `gemini-2.5-flash`)
- output: `--format {md,json,html}` `--out` · `--mode {candidate,recruiter}` · `--no-cache` `--verbose`

## How it works
`collect` (fault-tolerant, cached; auto-discovers links from the resume) → `analyze` (GitHub authenticity +
deterministic strength signals) → `evaluate` (a structured-output LLM rubric pass **blended** with the
deterministic signals, level-calibrated) → `report` (Markdown / JSON / HTML). The resume is also parsed into
structured fields. The cited rubric weights live in `docs/rubrics.md` (or run `hireme agents`).

## Privacy & fairness
HireMe scores on demonstrated skills, projects, contributions, and experience — not on name, gender, or
demographics. Pedigree/GPA only count where a domain's real hiring bar defensibly uses them (and never as the
driver). Reports show the evidence behind every score.

## Acknowledgements
HireMe was **inspired by HackerRank's open-source [`hiring-agent`](https://github.com/interviewstreet/hiring-agent)**
— the project that showed a resume-to-score LLM pipeline could work. HireMe takes that idea much further (five
domain-specialized agents, multi-source signal fusion + verification, experience-level calibration, and
deterministic-plus-LLM scoring) as an **independent, original implementation — no code is copied from it**.

## License
[MIT](LICENSE) · An independent project, inspired by but not derived from HackerRank's `hiring-agent`.
