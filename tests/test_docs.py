"""Guard: docs/rubrics.md must document every agent dimension + its current weight.

Keeps the published rubric grounding in sync with the code (the project's "auditable" claim).
"""

from __future__ import annotations

from pathlib import Path

from hireme.agents import all_agents

_RUBRICS = Path(__file__).resolve().parents[1] / "docs" / "rubrics.md"


def test_rubrics_doc_covers_every_dimension_and_weight():
    text = _RUBRICS.read_text(encoding="utf-8")
    missing = []
    for agent in all_agents():
        for d in agent.dimensions:
            row = f"| {d.label} | {d.weight:g} |"
            if row not in text:
                missing.append(f"{agent.name}: {row}")
    assert not missing, "docs/rubrics.md out of sync with agent weights:\n" + "\n".join(missing)
