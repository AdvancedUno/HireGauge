"""Registry mapping agent names to their declarative ``Agent`` definitions."""

from __future__ import annotations

from .airesearch import AGENT as AIRESEARCH
from .base import Agent
from .bigtech import AGENT as BIGTECH
from .general import AGENT as GENERAL
from .quant import AGENT as QUANT
from .university import AGENT as UNIVERSITY

_AGENTS: dict[str, Agent] = {
    a.name: a for a in (QUANT, AIRESEARCH, BIGTECH, GENERAL, UNIVERSITY)
}


def all_agents() -> list[Agent]:
    return list(_AGENTS.values())


def get_agent(name: str) -> Agent:
    try:
        return _AGENTS[name]
    except KeyError as exc:  # pragma: no cover - guarded by CLI enum
        raise KeyError(f"Unknown agent '{name}'. Choose from: {', '.join(_AGENTS)}") from exc


def agent_names() -> list[str]:
    return list(_AGENTS)
