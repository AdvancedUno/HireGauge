"""Report rendering (Markdown primary; JSON via Report.model_dump_json)."""

from __future__ import annotations

from .html import render_html
from .renderer import render_markdown

__all__ = ["render_html", "render_markdown"]
