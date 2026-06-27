"""AI research lab agent (Anthropic, OpenAI, DeepMind, Google Research, FAIR).

Reviewed for modern hiring (2025-26): first-author publications still matter most, but
the bar increasingly rewards real ML engineering and open-source impact (the research-
engineer path is a large share of hiring), demonstrated research taste/agency, and
shipping — while raw citation count / h-index is a noisier, secondary signal (especially
early-career). Weights reflect that shift. See docs/rubrics.md for grounding.
"""

from __future__ import annotations

from .base import Agent, Dimension, LevelExpectation

AGENT = Agent(
    name="airesearch",
    title="AI Research Lab",
    description="Evaluates like a frontier AI lab across research-scientist and research-engineer paths: "
    "first-author papers at top venues, real ML engineering and open-source impact, research experience "
    "and agency, research taste, and (secondarily) citation impact.",
    dimensions=(
        Dimension("publications", "Publications (first-author, top venue)", 30,
                  gt_signal="publication", blend=0.4,
                  description="NeurIPS/ICML/ICLR/CVPR/ACL papers, first-authorship, venue quality"),
        Dimension("ml_engineering", "ML Engineering & Open Source", 25,
                  gt_signal="github", blend=0.35,
                  description="Real ML systems, training/scaling, contributions to PyTorch/JAX/HF, strong repos"),
        Dimension("research_experience", "Research Experience & Agency", 15,
                  description="Lab/industry research, paper reproductions, independent direction-setting"),
        Dimension("research_taste", "Research Taste & Communication", 15,
                  description="Problem selection, clear technical writing, blog/X engagement with the frontier"),
        Dimension("research_impact", "Citation Impact", 10,
                  gt_signal="citation", blend=0.6,
                  description="Citations / h-index, adjusted for career stage and subfield (a noisy signal)"),
        Dimension("competitions", "Kaggle / Benchmarks", 5,
                  description="Applied-ML competition results (Kaggle medals/tier), benchmark/leaderboard work"),
    ),
    signals=("resume", "github", "publications", "kaggle", "web"),
    green_flags=(
        "First-author paper at NeurIPS/ICML/ICLR/CVPR/ACL",
        "Merged, non-trivial contributions to PyTorch / JAX / Hugging Face",
        "Trained/scaled real models, or a faithful reproduction of a SOTA paper (with code)",
        "Evident research taste: thoughtful writing, well-chosen problems",
    ),
    red_flags=(
        "Claims publications without verifiable links/venues",
        "No ML code on GitHub for a research-engineer claim",
        "Only coursework-level ML projects; no shipping or research depth",
    ),
    level_expectations=(
        LevelExpectation("phd-applicant", "Research-readiness over a long record; one strong first-author OR "
                                          "strong ML engineering + research experience is excellent."),
        LevelExpectation("phd-student", "Expect ≥1 first-author submission/paper and real ML engineering."),
        LevelExpectation("postdoc", "A first-author top-venue record is expected; its absence is a red flag."),
        LevelExpectation("new-grad", "Research-engineer path: strong ML GitHub/OSS + a paper or reproduction; "
                                     "publications helpful but not mandatory."),
    ),
    prompt_focus="Judge against a frontier-lab bar spanning research-scientist and research-engineer paths. "
    "Weight first-author top-venue publications and real ML engineering/OSS most; reward research taste and "
    "agency; treat raw citation count as a secondary, career-stage-adjusted signal. Verify publication and "
    "code claims against the provided links.",
    strictness="elite",
)
