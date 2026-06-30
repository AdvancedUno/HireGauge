"""Guard: docs/rubrics.md must document every agent dimension + its current weight.

Keeps the published rubric grounding in sync with the code (the project's "auditable" claim).
"""

from __future__ import annotations

from pathlib import Path

from hiregauge.agents import all_agents

_ROOT = Path(__file__).resolve().parents[1]
_RUBRICS = _ROOT / "docs" / "rubrics.md"
_README = _ROOT / "README.md"


def test_rubrics_doc_covers_every_dimension_and_weight():
    text = _RUBRICS.read_text(encoding="utf-8")
    missing = []
    for agent in all_agents():
        for d in agent.dimensions:
            row = f"| {d.label} | {d.weight:g} |"
            if row not in text:
                missing.append(f"{agent.name}: {row}")
    assert not missing, "docs/rubrics.md out of sync with agent weights:\n" + "\n".join(missing)


def test_readme_is_not_truncated_and_credits_hiring_agent():
    """Guard against the README regressing to a mid-section truncation (issue #14)."""
    text = _README.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]

    # The Acknowledgements section (crediting hiring-agent) must be present...
    assert "## Acknowledgements" in text
    assert "interviewstreet/hiring-agent" in text

    # ...and the file must not end on a dangling/truncated bullet like the old "- e".
    last = lines[-1]
    assert not last.startswith("- "), f"README ends on a dangling bullet: {last!r}"
    assert len(last) > 15, f"README ends on a suspiciously short line: {last!r}"
