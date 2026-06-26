"""Big tech SWE agent (Google, Meta, Amazon, Microsoft, Apple).

Weights reflect that big-tech hiring balances DSA/coding, system design (heavily
level-dependent), and demonstrated experience/impact, with project quality and
behavioral/leadership signal, plus a small pedigree/referral nudge.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="bigtech",
    title="Big Tech SWE",
    description="Evaluates like FAANG-style SWE hiring: DSA/coding, system design, quantified "
    "impact and experience, project quality, and behavioral/leadership signal.",
    dimensions=(
        Dimension("coding_dsa", "Coding & DSA", 25, deterministic=True,
                  description="LeetCode/CP signal and algorithmic depth in projects"),
        Dimension("system_design", "System Design", 20,
                  description="Architecture, scalability, trade-off reasoning (level-weighted)"),
        Dimension("experience_impact", "Experience & Quantified Impact", 25,
                  description="Internship pedigree, YoE, measurable outcomes"),
        Dimension("project_quality", "Project Quality (real vs tutorial)", 15,
                  description="Original, non-trivial GitHub projects with engineering depth"),
        Dimension("behavioral_leadership", "Behavioral & Leadership", 10,
                  description="Ownership, collaboration, leadership stories (e.g. Amazon LPs)"),
        Dimension("pedigree_referral", "Pedigree / Referral", 5,
                  description="Target-school or referral signal (secondary)"),
    ),
    signals=("resume", "github", "competitive"),
    green_flags=(
        "Prior FAANG / top-startup internship or full-time role",
        "Quantified impact (e.g. 'cut latency 40%', 'scaled to 10M users')",
        "Clear system-design experience for the target level",
        "Employee referral available",
    ),
    red_flags=(
        "No internship or substantive project for a junior candidate",
        "All accomplishments vague with no metrics",
        "Senior candidate with no system-design or leadership signal",
    ),
    level_expectations=(
        LevelExpectation("intern", "DSA + one solid project decisive; system design lightly weighted."),
        LevelExpectation("new-grad", "DSA + internship/project; light system design."),
        LevelExpectation("senior", "System design and quantified impact are decisive; their absence is a "
                                   "red flag; expect leadership signal."),
        LevelExpectation("staff", "Broad technical leadership and architecture ownership expected."),
    ),
    prompt_focus="Judge against a big-tech SWE bar calibrated to the candidate's level. Reward quantified "
    "impact and (at senior+) system design and leadership; don't over-penalize juniors for missing them.",
)
