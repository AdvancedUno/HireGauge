"""Pydantic schemas for HireMe.

Layers:
- **Inputs / signals** — raw, per-source data produced by collectors.
- **Profile** — one normalized ``CandidateProfile`` aggregating all signals + the
  candidate's ``ExperienceContext`` (YoE / career stage).
- **Evaluation / report** — the scored output an agent produces and what gets rendered.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------


class AgentName(StrEnum):
    quant = "quant"
    airesearch = "airesearch"
    bigtech = "bigtech"
    general = "general"
    university = "university"


class Provider(StrEnum):
    anthropic = "anthropic"
    ollama = "ollama"
    openai = "openai"
    gemini = "gemini"


class OutputFormat(StrEnum):
    md = "md"
    json = "json"
    html = "html"


class Mode(StrEnum):
    candidate = "candidate"
    recruiter = "recruiter"


class CareerStage(StrEnum):
    """Self-identified career stage / seniority, spanning industry and academia."""

    student = "student"
    intern = "intern"
    new_grad = "new-grad"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    principal = "principal"
    masters_applicant = "masters-applicant"
    phd_applicant = "phd-applicant"
    phd_student = "phd-student"
    postdoc = "postdoc"


# --------------------------------------------------------------------------------------
# Experience context (the YoE / level feature)
# --------------------------------------------------------------------------------------


class ExperienceContext(BaseModel):
    """How the candidate frames their own experience — calibrates every agent's bar."""

    yoe: float | None = Field(None, description="Years of professional experience")
    stage: CareerStage | None = Field(None, description="Self-identified career stage")
    target_stage: CareerStage | None = Field(
        None, description="Aspirational stage/role the candidate is aiming for"
    )
    current_title: str | None = None
    notes: str | None = None

    def describe(self) -> str:
        """Human/LLM-readable one-liner used in rubric prompts and reports."""
        parts: list[str] = []
        if self.stage:
            parts.append(f"stage={self.stage.value}")
        if self.yoe is not None:
            parts.append(f"yoe={self.yoe:g}")
        if self.current_title:
            parts.append(f'title="{self.current_title}"')
        if self.target_stage:
            parts.append(f"target={self.target_stage.value}")
        return ", ".join(parts) if parts else "unspecified"


# --------------------------------------------------------------------------------------
# Signals (collector outputs)
# --------------------------------------------------------------------------------------


class ResumeSignal(BaseModel):
    path: str | None = None
    text: str = ""
    char_count: int = 0


class GitHubRepo(BaseModel):
    name: str
    description: str | None = None
    url: str | None = None
    homepage: str | None = None
    language: str | None = None
    languages: dict[str, int] = Field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    topics: list[str] = Field(default_factory=list)
    is_fork: bool = False
    archived: bool = False
    created_at: str | None = None
    pushed_at: str | None = None
    contributor_count: int = 0
    author_commits: int = 0
    total_commits: int = 0
    # "open_source" (multiple contributors) vs "self_project" (solo)
    project_type: str = "self_project"
    has_tests: bool | None = None
    has_ci: bool | None = None
    readme_excerpt: str | None = None


class GitHubSignal(BaseModel):
    username: str
    name: str | None = None
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    blog: str | None = None
    twitter_username: str | None = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at: str | None = None
    top_languages: list[str] = Field(default_factory=list)
    repos: list[GitHubRepo] = Field(default_factory=list)
    # Populated by analysis/github_authenticity.py
    authenticity: dict = Field(default_factory=dict)


class Publication(BaseModel):
    title: str
    venue: str | None = None
    year: int | None = None
    citations: int = 0
    first_author: bool | None = None
    authors: str | None = None
    url: str | None = None


class PublicationSignal(BaseModel):
    source: str = "manual"  # scholar | arxiv | orcid | manual
    h_index: int | None = None
    total_citations: int | None = None
    publications: list[Publication] = Field(default_factory=list)


class CompetitiveSignal(BaseModel):
    codeforces_handle: str | None = None
    codeforces_rating: int | None = None
    codeforces_max_rating: int | None = None
    codeforces_rank: str | None = None
    codeforces_contests: int | None = None
    leetcode_handle: str | None = None
    leetcode_solved: int | None = None
    leetcode_rating: float | None = None
    # Olympiad / contest mentions detected in the resume (IMO, IOI, ICPC, Putnam, ...)
    olympiad_mentions: list[str] = Field(default_factory=list)


class KaggleSignal(BaseModel):
    handle: str | None = None
    competitions_tier: str | None = None  # novice | contributor | expert | master | grandmaster
    competition_medals: dict[str, int] = Field(default_factory=dict)  # {"gold":n,"silver":n,...}
    notebooks_tier: str | None = None


class WebSignal(BaseModel):
    url: str
    kind: str = "site"  # site | blog | portfolio
    title: str | None = None
    text_excerpt: str | None = None
    word_count: int = 0


# --------------------------------------------------------------------------------------
# Candidate profile (normalized aggregate)
# --------------------------------------------------------------------------------------


class CandidateProfile(BaseModel):
    experience: ExperienceContext = Field(default_factory=ExperienceContext)
    target_role: str | None = None

    resume: ResumeSignal | None = None
    github: GitHubSignal | None = None
    publications: PublicationSignal | None = None
    competitive: CompetitiveSignal | None = None
    kaggle: KaggleSignal | None = None
    web: list[WebSignal] = Field(default_factory=list)

    # Human-readable notes about what was missing/failed during collection.
    collection_notes: list[str] = Field(default_factory=list)

    def available_sources(self) -> list[str]:
        out = []
        if self.resume:
            out.append("resume")
        if self.github:
            out.append("github")
        if self.publications:
            out.append("publications")
        if self.competitive:
            out.append("competitive")
        if self.kaggle:
            out.append("kaggle")
        if self.web:
            out.append("web")
        return out


# --------------------------------------------------------------------------------------
# Evaluation / report
# --------------------------------------------------------------------------------------


class DimensionScore(BaseModel):
    key: str
    label: str
    score: float = Field(description="Raw points awarded for this dimension (0..max)")
    max: float = Field(description="Maximum raw points for this dimension")
    weight: float = Field(description="Weight (0..100) this dimension contributes to the overall")
    evidence: str = Field(description="Concrete, signal-grounded justification for the score")
    confidence: float = Field(0.5, description="0..1 confidence given available data")


class ActionItem(BaseModel):
    priority: int = Field(description="1 = highest priority")
    dimension: str
    recommendation: str
    rationale: str


class Evaluation(BaseModel):
    agent: str
    overall_score: float = Field(description="0..100 weighted overall")
    band: str = Field(description="Strong | Competitive | Developing | Early")
    summary: str
    dimensions: list[DimensionScore] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    action_plan: list[ActionItem] = Field(default_factory=list)


class Report(BaseModel):
    agent: str
    mode: str
    model: str
    generated_at: str
    profile: CandidateProfile
    evaluation: Evaluation
