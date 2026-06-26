"""Quant trading firm agent (Jane Street, Citadel, Two Sigma, HRT, Jump, DE Shaw, ...).

Weights reflect that elite quant pipelines are dominated by competitive-programming and
math-olympiad signal, with prob/stats fluency and tier-1 internships close behind. See
docs/rubrics.md for the cited grounding.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="quant",
    title="Quant Trading Firm",
    description="Evaluates like a top quant firm: competitive programming, math olympiads, "
    "probability/stats, low-latency engineering, and tier-1 internships.",
    dimensions=(
        Dimension("competitive_programming", "Competitive Programming", 30, deterministic=True,
                  description="Codeforces/AtCoder rating, ICPC, contest depth"),
        Dimension("math_olympiad", "Math / Olympiad", 20, deterministic=True,
                  description="IMO/USAMO/Putnam medals; strong math background"),
        Dimension("quant_fundamentals", "Probability, Stats & Low-Latency", 15,
                  description="Probability/stats reasoning, C++/OCaml, performance-aware systems"),
        Dimension("experience_internships", "Experience & Internships", 20,
                  description="Tier-1 quant/SWE internships and production work"),
        Dimension("systems_projects", "Systems & Projects", 10,
                  description="Non-trivial engineering projects (perf, concurrency, data)"),
        Dimension("pedigree", "Pedigree", 5,
                  description="Target-school signal (secondary, never the driver)"),
    ),
    signals=("resume", "github", "competitive"),
    green_flags=(
        "Codeforces Grandmaster (≥2400) or ICPC World Finalist",
        "IMO/IOI medal or Putnam Fellow",
        "Prior internship at a tier-1 quant firm (Jane Street, HRT, Citadel, Five Rings)",
        "OCaml / C++ with performance-aware code",
    ),
    red_flags=(
        "No competitive-programming or olympiad signal at all",
        "Motivation reads as 'just high pay' with no math/markets interest",
        "Only tutorial-level projects",
    ),
    level_expectations=(
        LevelExpectation("intern", "Intern bar: contest rating + math are decisive; little production "
                                   "experience expected."),
        LevelExpectation("new-grad", "New-grad bar: expect strong CP/olympiad and at least one serious "
                                     "internship or systems project."),
        LevelExpectation("senior", "Senior/experienced bar: production trading-systems or research impact "
                                   "matters more; pure contest rating matters less."),
    ),
    prompt_focus="Judge against an elite quant bar. Reward verifiable competitive-programming and "
    "olympiad achievement and prob/stats depth; treat school pedigree as a minor secondary signal.",
)
