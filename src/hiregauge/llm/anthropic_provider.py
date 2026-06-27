"""Anthropic (Claude) provider — the default backend.

Uses structured outputs via ``messages.parse`` when available, with graceful
fallbacks for older SDKs. The large rubric system prompt is sent in a cache-control
block so repeated runs read it cheaply. ``anthropic`` is imported lazily so the rest
of HireGauge works without it installed.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Models that accept adaptive thinking (claude-4.6+ family). Others fall back to plain calls.
_ADAPTIVE_THINKING = ("opus-4-6", "opus-4-7", "opus-4-8", "sonnet-4-6", "fable-5", "mythos-5")


def _supports_adaptive(model: str) -> bool:
    return any(tag in model for tag in _ADAPTIVE_THINKING)


def _first_text(resp: Any) -> str:
    parts = []
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Grab the outermost JSON object if there's surrounding prose.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key
        self._client: Any | None = None

    def _client_or_raise(self) -> Any:
        if self._client is None:
            try:
                import anthropic  # noqa: PLC0415 (lazy on purpose)
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "The 'anthropic' package is required for the Claude provider. "
                    "Install it with: pip install anthropic"
                ) from exc
            self._client = (
                anthropic.Anthropic(api_key=self._api_key)
                if self._api_key
                else anthropic.Anthropic()
            )
        return self._client

    def _user_content(self, user: str, pdf_path: str | None) -> list[dict]:
        content: list[dict] = []
        if pdf_path:
            try:
                data = base64.standard_b64encode(Path(pdf_path).read_bytes()).decode("ascii")
                content.append(
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": data,
                        },
                    }
                )
            except OSError:
                pass  # fall back to text-only if the PDF can't be read
        content.append({"type": "text", "text": user})
        return content

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
        system_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        messages = [{"role": "user", "content": self._user_content(user, pdf_path)}]
        base_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": messages,
        }
        if _supports_adaptive(self.model):
            base_kwargs["thinking"] = {"type": "adaptive"}

        # 1) Preferred: structured-output parse helper.
        parse = getattr(client.messages, "parse", None)
        if callable(parse):
            try:
                resp = parse(output_format=schema, **base_kwargs)
                parsed = getattr(resp, "parsed_output", None)
                if parsed is not None:
                    return parsed
            except Exception:  # noqa: BLE001 - fall through to robust fallbacks
                pass

        # 2) output_config json_schema on a normal create.
        try:
            resp = client.messages.create(
                output_config={
                    "format": {"type": "json_schema", "schema": schema.model_json_schema()}
                },
                **base_kwargs,
            )
            return schema.model_validate_json(_first_text(resp))
        except Exception:  # noqa: BLE001
            pass

        # 3) Plain create + lenient JSON extraction (relies on the prompt asking for JSON).
        resp = client.messages.create(**base_kwargs)
        text = _extract_json(_first_text(resp))
        return schema.model_validate(json.loads(text))
