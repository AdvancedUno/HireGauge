"""Google Gemini provider (via the ``google-genai`` SDK).

Uses Gemini structured output (``response_schema`` + ``application/json``) to return
a validated Pydantic object. ``google-genai`` is imported lazily so the rest of
HireGauge works without it installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ._retry import RETRYABLE_STATUS, call_with_retry

T = TypeVar("T", bound=BaseModel)


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key
        self._client: Any | None = None

    def _client_or_raise(self) -> Any:
        if self._client is None:
            try:
                from google import genai  # noqa: PLC0415 (lazy on purpose)
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "The 'google-genai' package is required for the Gemini provider. "
                    'Install it with: pip install "hiregauge[gemini]"'
                ) from exc
            if not self._api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. Add it to your environment or .env file."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def preflight(self) -> None:
        """Fail fast if the key is missing or the SDK isn't installed (no network call)."""
        if not self._api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your environment or .env file."
            )
        self._client_or_raise()

    def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        pdf_path: str | None = None,
        max_tokens: int = 16000,
    ) -> T:
        client = self._client_or_raise()
        from google.genai import types  # noqa: PLC0415 (lazy on purpose)

        contents: Any = user
        if pdf_path:
            try:
                pdf_part = types.Part.from_bytes(
                    data=Path(pdf_path).read_bytes(), mime_type="application/pdf"
                )
                contents = [pdf_part, user]
            except OSError:
                contents = user

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=max_tokens,
        )
        from google.genai import errors as genai_errors  # noqa: PLC0415 (lazy on purpose)

        def _retryable(exc: BaseException) -> bool:
            return (
                isinstance(exc, genai_errors.APIError)
                and getattr(exc, "code", None) in RETRYABLE_STATUS
            )

        resp = call_with_retry(
            lambda: client.models.generate_content(
                model=self.model, contents=contents, config=config
            ),
            is_retryable=_retryable,
        )

        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        if isinstance(parsed, dict):
            return schema.model_validate(parsed)
        text = getattr(resp, "text", None)
        if text:
            return schema.model_validate_json(text)
        raise RuntimeError("Gemini returned no parseable structured content.")
