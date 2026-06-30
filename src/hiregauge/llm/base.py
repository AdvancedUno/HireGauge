"""LLM provider protocol.

A provider turns a (system, user[, pdf]) prompt into a validated Pydantic object.
The Anthropic provider is the default; others implement the same surface.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    model: str

    def preflight(self) -> None:
        """Validate the provider is usable (package installed + key present) without
        making a network call. Raise a clear, actionable error if it is not, so the CLI
        can fail fast before running a full collection pass."""
        ...

    def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        pdf_path: str | None = None,
        max_tokens: int = 16000,
    ) -> T:
        """Return an instance of ``schema`` produced by the model."""
        ...
