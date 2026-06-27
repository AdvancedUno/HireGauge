"""Declarative definition of an evaluator agent.

An ``Agent`` is mostly *data*: the dimensions it scores (with weights that sum to
100), which signals it consumes, its domain green/red flags, how the bar shifts by
experience level, and a short prompt focus used by the LLM rubric pass. Keeping it
declarative makes weights tunable and auditable (a core HireMe goal).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    weight: float  # contribution to the 0..100 overall; weights sum to 100 per agent
    description: str = ""
    # Optional deterministic blend: name of a 0..1 strength signal (github|publication|citation)
    # and how much it weighs against the LLM score for this dimension (0..1).
    gt_signal: str | None = None
    blend: float = 0.0

    @property
    def is_blended(self) -> bool:
        """True when this dimension's LLM score is anchored to a deterministic,
        code-computed ground-truth signal (shown as ``*`` in ``hireme agents``)."""
        return bool(self.gt_signal) and self.blend > 0


@dataclass(frozen=True)
class LevelExpectation:
    stage: str  # a CareerStage value, or "*" for a general note
    note: str


@dataclass(frozen=True)
class Agent:
    name: str
    title: str
    description: str
    dimensions: tuple[Dimension, ...]
    signals: tuple[str, ...]  # resume | github | publications | kaggle | web
    green_flags: tuple[str, ...] = ()
    red_flags: tuple[str, ...] = ()
    level_expectations: tuple[LevelExpectation, ...] = ()
    prompt_focus: str = ""
    # How brutal the scoring bar is. "elite" emulates a top-firm screen where the vast
    # majority of applicants don't clear the bar (quant / frontier-lab / FAANG-senior);
    # "standard" is a real, strict hiring screen calibrated to the candidate's level.
    strictness: str = "standard"  # "standard" | "elite"

    def weight_total(self) -> float:
        return round(sum(d.weight for d in self.dimensions), 3)

    def expectation_for(self, stage: str | None) -> str | None:
        if not stage:
            return None
        for le in self.level_expectations:
            if le.stage == stage:
                return le.note
        for le in self.level_expectations:
            if le.stage == "*":
                return le.note
        return None
