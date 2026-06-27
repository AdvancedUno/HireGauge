"""Quant trading firm agent (Jane Street, Citadel, Two Sigma, HRT, Jump, DE Shaw, ...).

Modern quant hiring (incl. quant-dev / HFT / ML-quant) weights mathematical and
statistical depth, low-latency systems engineering, research, and strong experience.
Algorithmic-contest skill is one supporting signal — not the headline, and not
Codeforces-specific. See docs/rubrics.md for the grounding.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="quant",
    title="Quant Trading Firm",
    description="Evaluates like a modern quant firm (incl. quant-dev / HFT / ML-quant): mathematical and "
    "statistical depth, low-latency systems engineering, research, and strong experience — with algorithmic "
    "problem-solving as one signal among several rather than the headline.",
    dimensions=(
        Dimension("math_quant_stats", "Math & Probability/Statistics", 25,
                  description="Probability, statistics, linear algebra, mathematical rigor and modeling"),
        Dimension("low_latency_systems", "Low-Latency & Systems Engineering", 20,
                  gt_signal="github", blend=0.2,
                  description="C++/Rust, performance, concurrency, memory/cache awareness, HFT-grade systems"),
        Dimension("experience_internships", "Experience & Internships", 20,
                  description="Tier-1 quant/SWE internships and production engineering experience"),
        Dimension("research_projects", "Research & Projects", 15,
                  gt_signal="github", blend=0.25,
                  description="Quant research, ML for signals, and substantial real-world projects"),
        Dimension("algo_problem_solving", "Algorithmic & Quant Problem-Solving", 15,
                  description="Algorithmic/DSA skill, brainteasers, math/olympiad or contest background (any platform)"),
        Dimension("pedigree", "Pedigree", 5,
                  description="Target-school signal (secondary, never the driver)"),
    ),
    signals=("resume", "github"),
    green_flags=(
        "Strong probability/statistics or applied-math depth (research, coursework, projects)",
        "Low-latency / performance engineering (C++/CUDA, concurrency, cache-aware design)",
        "ML or quantitative research with real results",
        "Prior internship at a tier-1 quant or top-tier tech firm",
        "Math olympiad / ICPC background (a plus, not required)",
    ),
    red_flags=(
        "No evidence of mathematical or statistical depth",
        "Motivation reads as 'just high pay' with no markets/math interest",
        "Only tutorial-level projects; no systems or research depth",
    ),
    level_expectations=(
        LevelExpectation("intern", "Intern bar: math/stats foundation + some systems or research project; "
                                   "limited production experience expected."),
        LevelExpectation("new-grad", "New-grad bar: solid math/stats, at least one strong systems or research "
                                     "project, and ideally a tier-1 internship."),
        LevelExpectation("senior", "Senior/experienced bar: production trading-systems or research impact is "
                                   "decisive; raw contest skill matters little."),
    ),
    prompt_focus="Judge against a modern quant bar (quant-dev / HFT / ML-quant). Weight mathematical & "
    "statistical depth, low-latency systems, research, and strong experience most; treat algorithmic-contest "
    "background as one supporting signal (not Codeforces-specific) and school pedigree as minor.",
    strictness="elite",
)
