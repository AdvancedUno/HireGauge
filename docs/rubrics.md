# HireGauge rubrics — weights & grounding

This document is the rationale behind every agent's dimensions and weights. The weights
themselves live in `src/hiregauge/agents/*.py` and are deliberately declarative so they stay
**tunable and auditable** — this file explains *why* they're set the way they are, grounded
in how each domain actually hires, plus the deliberate modern-hiring calibrations we made.

> Weights are judgment calls informed by the sources at the bottom and by practitioner input.
> They are meant to be revised — open a PR (see CONTRIBUTING) and update this file with the
> reasoning. Validate changes with the `eval-calibrator` agent.

## How scoring works

- Each agent has 4–6 **dimensions**; their weights **sum to 100**.
- Each dimension is scored `0..weight`, **calibrated to the candidate's experience stage**
  (`--yoe` / `--level`); the overall score is the sum, mapped to a band.
- **Bands:** `Strong ≥ 80 · Competitive ≥ 60 · Developing ≥ 40 · Early < 40`.
- **Deterministic facts** (GitHub authenticity, fetched publications/portfolio) are computed in
  code and fed to the model as ground truth; the model scores each dimension with **cited
  evidence** from the dossier. A `*` in `hiregauge agents` marks dimensions whose score is blended
  with a deterministic, code-computed signal (GitHub / Scholar).
- **Fairness:** scores must not depend on name, gender, demographics, or location. School
  prestige and GPA count only where a domain's real bar defensibly uses them — never as the
  driver. Every score shows its evidence.

### Strictness: an anchored, real-world bar

HireGauge deliberately scores like a real screen, not a participation award — the goal is to tell a
candidate honestly where they stand so they know what to improve. Two mechanisms enforce this:

- **Anchored scale.** The evaluator prompt defines what each fraction of a dimension's max *means*
  and tells the model to default low and earn points only with verifiable evidence: `0–15%` no
  credible evidence · `20–35%` below/at bar or unverified · `40–55%` solidly meets the level's bar
  (where most real candidates land) · `60–75%` clearly above bar · `80–100%` exceptional/top-decile.
  Self-reported, vague, or unlinked claims are capped in the `20–35%` band.
- **Per-agent strictness tier** (`Agent.strictness`). `elite` agents (**quant, airesearch, bigtech**)
  emulate a top-firm screen where the bar is brutal and the whole scale shifts down; `standard`
  agents (**general, university**) use a strict but level-appropriate hiring bar.

### Positioning output

Beyond the score + band, each evaluation reports **where the candidate stands**:

- **Screen verdict** — derived from the band so it can't contradict the score: `Strong → yes`
  (likely to pass an initial screen), `Competitive → borderline`, `Developing`/`Early → no`.
- **Percentile** — the model's estimate (0–100) of the candidate vs. the realistic applicant pool
  for that role+level, kept consistent with its dimension scores.
- **Positioning line** — a one-sentence read of where they sit and against whom.

## Deterministic scoring & blend

Some dimensions are anchored to **code-computed ground truth**, not left entirely to the model. We compute
three `0..1` *strength* signals from fetched data and blend each into the relevant dimensions:
`final = max(LLM_score, (1 − blend)·LLM_score + blend·(strength · weight))` (clamped to `[0, weight]`). The
blend can only **lift** a dimension toward the ground-truth data — it never lowers a score the rest of the
dossier already justifies, so a candidate is never penalized for providing a real-but-sparse signal. The blend
% is shown in that dimension's evidence (e.g. `[auto: github=0.83, blended 35%]`). When the data isn't
available (e.g. no Scholar URL) or wouldn't raise the score, the blend is skipped and the dimension is scored
by the model alone.

| Signal | Source | `0..1` formula (thresholds in `analysis/deterministic.py`) |
|---|---|---|
| `github` | GitHub | `0.30·min(owned/12,1) + 0.25·min(recent/6,1) + 0.15·min(langs/6,1) + 0.30·min(max_stars/800,1)` — demanding thresholds (ordinary≈0.3, solid≈0.65); star count deliberately can't dominate |
| `publication` | Scholar | `0.6·min(papers/8,1) + 0.4·citation` |
| `citation` | Scholar | `max(min(h_index/20,1), min(citations/2000,1))` — early-career-friendly |

Per-dimension blends currently in effect:

| Agent · dimension | Signal | Blend |
|---|---|---:|
| quant · Low-Latency & Systems Engineering | github | 20% |
| quant · Research & Projects | github | 25% |
| airesearch · Publications | publication | 40% |
| airesearch · ML Engineering & Open Source | github | 35% |
| airesearch · Citation Impact | citation | 60% |
| bigtech · Project Quality | github | 35% |
| general · Project Quality & Originality | github | 35% |
| general · Open Source | github | 30% |
| university · Research Experience & Publications | publication | 40% |
| university · Technical Projects | github | 35% |

## Cross-cutting signals

### GitHub authenticity (`analysis/github_authenticity.py`)
Owned-vs-fork repo counts, total/max stars, **fork-to-star ratio**, and recent activity are
computed deterministically and supplied to the evaluator. Rationale: stars alone are a weak,
gameable signal — there are millions of suspected fake GitHub stars and they're cheap to buy,
so a healthy fork:star ratio + real activity + issues matter more than a raw star count.
Sources: [Six Million (Suspected) Fake Stars on GitHub](https://arxiv.org/html/2412.13459v2),
[How to tell a real GitHub star from a bought one](https://medium.com/@marc.bara.iniesta/how-to-tell-a-real-github-star-from-a-bought-one-edad3e4176f9),
[What recruiters actually see in your GitHub](https://dev.to/jsgurujobs/portfolio-code-that-gets-you-hired-what-recruiters-actually-see-in-your-github-h9n).

### Resume green/red flags
Green: quantified impact, working links/demos, steady growth, verifiable credentials.
Red: vague unquantified claims, no links/evidence, repeated <1-year tenure, unverifiable
publications/awards. These are surfaced per agent (and partly deterministically). Sources:
[6 red flags that keep good candidates from getting hired (HBR)](https://hbr.org/2025/10/6-red-flags-that-keep-good-candidates-from-getting-hired),
[Resume red flags 2025](https://www.frontlinesourcegroup.com/blog-resume-red-flags-what-not-to-include-on-your-resume-in-2025.html).

---

## quant — Quant Trading Firm

| Dimension | Weight | Rewards |
|---|---:|---|
| Math & Probability/Statistics | 25 | probability, statistics, linear algebra, mathematical rigor & modeling |
| Low-Latency & Systems Engineering | 20 | C++/Rust, performance, concurrency, memory/cache awareness, HFT-grade systems |
| Experience & Internships | 20 | tier-1 quant/SWE internships, production engineering |
| Research & Projects | 15 | quant research, ML-for-signals, substantial real projects |
| Algorithmic & Quant Problem-Solving | 15 | algorithmic/DSA skill, brainteasers, math-olympiad/contest background (any platform) |
| Pedigree | 5 | target-school signal (secondary, never the driver) |

**Calibration note (deliberate, 2026).** Elite firms (Jane Street, Citadel, HRT) historically
recruited heavily from IOI/ICPC/Codeforces top performers, and olympiad medalists remain
fast-tracked. **But** a Codeforces *profile* is rarely a submitted credential today, and a large
and growing share of quant hiring is quant-dev / HFT-systems / ML-quant, which weight
mathematical & statistical depth, low-latency systems, and research above raw contest rating.
We therefore **broadened "competitive programming" into "Algorithmic & Quant Problem-Solving"
and cut its weight 30 → 15**, reallocating to math/stats, low-latency systems, experience, and
research. Contest/olympiad background still counts here — it's just no longer the headline. (This
reflects user/practitioner input plus the sources below.)
Sources: [The Quant Kids of Trading](https://rupakghose.substack.com/p/the-quant-kids-of-trading),
[Jane Street Quant Interview Guide 2026](https://myntbit.com/blog/jane-street-quant-interview-guide-2026),
[HRT Internships 2027](https://www.getsmartresume.com/article/hrt-algorithm-development-software-engineering-intern),
[Citadel Quant Research & Trading Intern](https://www.getsmartresume.com/article/citadel-quant-research-trading-intern),
[Top quant trading firms 2026](https://www.quantvps.com/blog/top-quant-trading-firms),
[Interpreting Codeforces ratings](https://codeforces.com/blog/entry/68288).

---

## airesearch — AI Research Lab

| Dimension | Weight | Rewards |
|---|---:|---|
| Publications (first-author, top venue) | 30 | NeurIPS/ICML/ICLR/CVPR/ACL papers, first-authorship, venue quality |
| ML Engineering & Open Source | 25 | real ML systems, training/scaling, contributions to PyTorch/JAX/HF, strong repos |
| Research Experience & Agency | 15 | lab/industry research, paper reproductions, independent direction-setting |
| Research Taste & Communication | 15 | problem selection, clear technical writing, engagement with the frontier |
| Citation Impact | 10 | citations / h-index, adjusted for career stage & subfield (a noisy signal) |
| Kaggle / Benchmarks | 5 | applied-ML competition results, benchmark/leaderboard work |

**Calibration note.** First-author papers at top venues are still the headline signal for
research-scientist roles. We **raised ML Engineering & OSS to 25** (the research-engineer path is
a large fraction of lab hiring, and shipping/scaling real models is increasingly decisive) and
**lowered raw Citation Impact to 10** because h-index is discipline-dependent and noisy
early-career, and ignores authorship position. Anthropic's own guidance values demonstrable
research taste (writing "good enough to put in front of a senior researcher").
Sources: [How to get hired at OpenAI/Anthropic/DeepMind 2026](https://www.sundeepteki.org/advice/how-to-get-hired-at-openai-anthropic-and-google-deepmind-in-2026),
[ICLR/NeurIPS/ICML are the top AI venues](https://analyticsdrift.com/iclr-neurips-and-icml-are-top-three-publications-for-artificial-intelligence-according-to-googles-scholar-metrics-2022),
[The h-index: an indicator of research output (limitations)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10025721/),
[Hugging Face openings (OSS ML roles)](https://apply.workable.com/huggingface/?lng=en).

---

## bigtech — Big Tech SWE

| Dimension | Weight | Rewards |
|---|---:|---|
| Coding & DSA | 25 | algorithmic problem-solving (LeetCode-style), code quality, communication |
| System Design | 20 | architecture, scalability, trade-off reasoning (level-weighted) |
| Experience & Quantified Impact | 25 | internship/role pedigree, YoE, measurable outcomes |
| Project Quality (real vs tutorial) | 15 | original, non-trivial GitHub projects with engineering depth |
| Behavioral & Leadership | 10 | ownership, collaboration, leadership stories (e.g. Amazon LPs) |
| Pedigree / Referral | 5 | target-school or referral signal (secondary) |

**Calibration note.** Kept close to standard practice: DSA and system design remain the primary
technical screens, with quantified impact weighted equally to coding. Behavioral/leadership is
level-gated (decisive at senior+, light for interns) via the per-stage expectations. School
prestige is a declining, secondary signal; a **referral** materially raises hire probability
(commonly cited as several-fold), so it's noted but kept small. DSA/contest background is read
from the resume and project complexity — no contest profile required.
Sources: [Company-wise LeetCode questions 2026](https://www.dsaprep.dev/blog/company-wise-leetcode-questions),
[System design interview expectations by level](https://designgurus.substack.com/p/faang-system-design-interviews-by),
[Amazon Leadership Principles](https://igotanoffer.com/en/advice/amazon-leadership-principles),
[Referrals are far more likely to be hired](https://www.pinpointhq.com/insights/referrals-are-7x-more-likely-to-be-hired-than-job-board-candidates),
[Degree prestige & tech hiring 2025](https://bestjobsearchapps.com/articles/en/top-us-colleges-with-the-best-job-placement-rates-2026-rankings-and-career-outcomes).

---

## general — General Software

| Dimension | Weight | Rewards |
|---|---:|---|
| Project Quality & Originality | 30 | real, original projects that solve a problem (not tutorial clones) |
| Technical Skills Breadth | 20 | languages, frameworks, tooling demonstrated in work/projects |
| Experience | 20 | internships, full-time, founder/early-stage roles |
| Open Source | 15 | genuine contributions to *others'* projects (not just personal repos) |
| Portfolio & Communication | 15 | portfolio/blog quality, documentation, technical writing |

**Calibration note.** The default lens when no specialized track is chosen. Weighted toward
demonstrable, original work over credentials: real projects and genuine open-source contribution
beat tutorial clones and unlinked claims. "Open Source" specifically means contributions to other
people's projects — personal repos alone count under Project Quality, not here.
Sources: [What recruiters actually see in your GitHub](https://dev.to/jsgurujobs/portfolio-code-that-gets-you-hired-what-recruiters-actually-see-in-your-github-h9n),
[Evaluating candidates via GitHub profiles](https://www.linkedin.com/advice/3/what-most-effective-ways-evaluate-candidates-using-github-s864e).

---

## university — University Admissions (PhD / Masters)

| Dimension | Weight | Rewards |
|---|---:|---|
| Research Experience & Publications | 35 | first-author papers, research internships, sustained research work |
| Research Fit & Direction | 20 | specific research interests + advisor/lab fit (SOP/notes) |
| Academic Record | 15 | GPA, relevant coursework, academic awards |
| Letters / Recommenders | 10 | strength/relevance of recommenders (if provided) |
| Technical Projects | 10 | implementation skill via GitHub/projects |
| Breadth & Service | 10 | TA/mentoring, workshops, open-source, community involvement |

**Calibration note.** PhD admissions are driven by research readiness and fit far more than raw
metrics. Research experience + publications dominate (35), with research-fit/direction second
(20) — committees make fast first-pass decisions on clarity of interests and faculty alignment.
**GRE is de-emphasized** (many top programs have made it optional/eliminated it, 2025–26). Masters
admissions weight specialization fit, projects, and academics more, and value industry experience
— handled via the per-stage expectations.
Sources: [Graduate Admission FAQ — UCSD CSE (GRE not required)](https://cse.ucsd.edu/graduate/graduate-admissions-faq),
[How PhD admissions committees assess applications](https://alvinwan.com/how-phd-admissions-committees-assess-applications),
[PhD Admissions Guide 2025 — from a former professor](https://admit-lab.com/resources/phd-admissions-guide/),
[Letters of recommendation: who to ask](https://magoosh.com/gre/letter-of-recommendation-for-graduate-school/).

---

## Where to change weights

Edit the `Dimension(...)` weights in `src/hiregauge/agents/<agent>.py` (they must still sum to 100 —
`tests/test_agents.py` enforces it), update the matching table + rationale here, then run the
`eval-calibrator` agent on the golden profiles to confirm the change behaves as intended. See the
`hiregauge-rubric-authoring` skill for the full checklist.
