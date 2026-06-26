"""University admissions agent (CS/ML PhD & Masters).

Weights reflect that PhD admissions are driven by research experience & first-author
publications and research-fit/direction, with academic record, letters, technical
projects, and breadth/service rounding it out. GRE is de-emphasized (2025 norm).
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="university",
    title="University Admissions (PhD/Masters)",
    description="Evaluates like a CS/ML admissions committee: research experience & first-author "
    "publications, research-fit, academic record, letters, projects, and service.",
    dimensions=(
        Dimension("research_publications", "Research Experience & Publications", 35, deterministic=True,
                  description="First-author papers, research internships, sustained research work"),
        Dimension("research_fit_direction", "Research Fit & Direction", 20,
                  description="Clear, specific research interests and advisor/lab fit (SOP/notes)"),
        Dimension("academic_record", "Academic Record", 15,
                  description="GPA, relevant coursework, academic awards"),
        Dimension("letters", "Letters / Recommenders", 10,
                  description="Strength/relevance of recommenders (if provided)"),
        Dimension("technical_projects", "Technical Projects", 10,
                  description="Implementation skill demonstrated via GitHub/projects"),
        Dimension("breadth_service", "Breadth & Service", 10,
                  description="TA/mentoring, workshops, open-source, community involvement"),
    ),
    signals=("resume", "github", "publications", "web"),
    green_flags=(
        "First-author paper at a recognized venue",
        "Research internship at a strong lab",
        "Specific, well-articulated research direction with named potential advisors",
        "Letters from researchers in the target subfield",
    ),
    red_flags=(
        "Vague research interests ('I love AI') with no specifics",
        "No research experience for a competitive PhD program",
        "Unfunded PhD offer reliance / no funding awareness",
    ),
    level_expectations=(
        LevelExpectation("masters-applicant", "Research not required; specialization fit, projects, and "
                                              "academics carry more weight; industry experience is a plus."),
        LevelExpectation("phd-applicant", "Research readiness + fit are decisive; one strong first-author or "
                                          "solid research experience is excellent; GRE de-emphasized."),
    ),
    prompt_focus="Judge like a PhD/Masters admissions committee. Weight research experience, first-author "
    "publications, and research-fit most; de-emphasize GRE; treat school prestige as secondary.",
)
