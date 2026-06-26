"""AI research lab agent (Anthropic, OpenAI, DeepMind, Google Research, FAIR).

Weights reflect that research hiring is dominated by first-author publications at top
venues and demonstrable ML engineering depth (real code + OSS), with citations/h-index,
research experience, and communication/taste rounding it out.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="airesearch",
    title="AI Research Lab",
    description="Evaluates like a frontier AI lab: first-author papers at top venues, ML "
    "engineering depth and OSS, citations/h-index, research experience, and research taste.",
    dimensions=(
        Dimension("publications", "Publications (first-author, top venue)", 35, deterministic=True,
                  description="NeurIPS/ICML/ICLR/CVPR/ACL papers, first-authorship"),
        Dimension("research_impact", "Citations & h-index", 15, deterministic=True,
                  description="Citation count and h-index, discipline-adjusted"),
        Dimension("ml_engineering", "ML Engineering & OSS (GitHub)", 20,
                  description="Real ML projects; contributions to PyTorch/JAX/HF; reproductions"),
        Dimension("research_experience", "Research Experience", 15,
                  description="Lab/industry research roles, mentored work, paper reproductions"),
        Dimension("competitions", "Kaggle / Competitions", 5, deterministic=True,
                  description="Kaggle medals/tier; applied ML competition signal"),
        Dimension("communication_taste", "Communication & Research Taste", 10,
                  description="Blog/X engagement, clear technical writing, problem selection"),
    ),
    signals=("resume", "github", "publications", "kaggle", "web"),
    green_flags=(
        "First-author paper at NeurIPS/ICML/ICLR/CVPR/ACL",
        "Merged contributions to PyTorch / JAX / Hugging Face",
        "Faithful reproduction of a SOTA paper (with code)",
        "h-index unusually high for career stage",
    ),
    red_flags=(
        "Claims publications without verifiable links/venues",
        "No ML code on GitHub for a research-engineer claim",
        "Only coursework-level ML projects",
    ),
    level_expectations=(
        LevelExpectation("phd-applicant", "Research-readiness over a long publication record; one strong "
                                          "first-author or solid research experience is excellent."),
        LevelExpectation("phd-student", "Expect ≥1 first-author submission/paper and real ML engineering."),
        LevelExpectation("postdoc", "A first-author top-venue record is expected; its absence is a red flag."),
        LevelExpectation("new-grad", "Research-engineer path: strong ML GitHub + a paper or reproduction."),
    ),
    prompt_focus="Judge against a frontier-lab research bar. Weight first-author top-venue publications and "
    "demonstrable ML engineering most; verify publication and code claims against the provided links.",
)
