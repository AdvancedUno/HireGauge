"""Allow running the CLI as ``python -m hireme`` (PATH-independent)."""

from __future__ import annotations

from .cli import app

if __name__ == "__main__":  # pragma: no cover
    app()
