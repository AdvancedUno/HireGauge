"""General software agent — broad, pragmatic software-hiring lens.

The default when a candidate isn't targeting a specialized track. Weights reward real
(non-tutorial) project work, skills breadth, experience, open-source contribution, and a
communicative portfolio.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="general",
    title="General Software",
    description="A broad software-hiring lens: real project quality, skills breadth, experience, "
    "open-source contribution, and portfolio/communication.",
    dimensions=(
        Dimension("project_quality", "Project Quality & Originality", 30,
                  description="Real, original projects that solve a problem (not tutorial clones)"),
        Dimension("skills_breadth", "Technical Skills Breadth", 20,
                  description="Languages, frameworks, tooling demonstrated in work/projects"),
        Dimension("experience", "Experience", 20,
                  description="Internships, full-time, founder/early-stage roles"),
        Dimension("open_source", "Open Source", 15, deterministic=True,
                  description="Genuine contributions to others' projects (not just personal repos)"),
        Dimension("portfolio_communication", "Portfolio & Communication", 15,
                  description="Portfolio/blog quality, documentation, technical writing"),
    ),
    signals=("resume", "github", "web"),
    green_flags=(
        "Original project with real users or clear real-world utility",
        "Merged contributions to third-party open-source projects",
        "Strong READMEs / docs / live demos",
        "Founder or early-stage engineer experience",
    ),
    red_flags=(
        "Only tutorial clones (todo, calculator, weather, basic CRUD)",
        "Projects with no links, demos, or evidence",
        "No activity in the last year",
    ),
    level_expectations=(
        LevelExpectation("student", "Projects + learning trajectory matter most; experience optional."),
        LevelExpectation("junior", "Expect at least one real project and some real-world experience."),
        LevelExpectation("senior", "Expect sustained impact, ownership, and depth — breadth alone isn't enough."),
    ),
    prompt_focus="Judge as a pragmatic software hiring manager. Reward original, real project work and "
    "genuine open-source contribution; discount tutorial clones and unlinked claims.",
)
