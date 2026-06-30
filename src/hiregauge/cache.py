"""Tiny on-disk JSON cache for external API responses.

Keeps iteration cheap (and avoids hammering rate-limited APIs) during development.
Keys are arbitrary strings — collectors use ``"{source}:{identity}:{params}"``.

Each entry is wrapped in a small envelope that records ``fetched_at`` so reads can
enforce a **max age (TTL)**: external signals (GitHub stars, h-index, portfolios)
change over time, so an entry past its TTL is treated as a miss and refetched instead
of being scored silently. ``max_age=None`` opts an entry out of expiry (used for the
resume parse, which is keyed by content digest and never goes stale).

Three modes, set at construction:
- ``enabled=False`` — no reads, no writes (``--no-cache``).
- ``refresh=True`` — reads always miss but writes still happen, so the run refetches
  fresh data and rewrites the cache (``--refresh``).
- default — read fresh entries, refetch expired ones.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

# Default time-to-live for cached external data (24h). Tunable per-call via ``max_age``.
DEFAULT_MAX_AGE = 24 * 60 * 60

# Envelope marker + version so we can tell a wrapped entry from a raw legacy value
# (and from an API payload that happens to contain a ``fetched_at`` key).
_ENVELOPE_KEY = "_hg_cache"
_ENVELOPE_VERSION = 1


class Cache:
    def __init__(
        self,
        directory: str | Path = ".hiregauge_cache",
        enabled: bool = True,
        refresh: bool = False,
    ) -> None:
        self.dir = Path(directory)
        self.enabled = enabled
        # refresh = force every read to miss, but keep writing fresh values back.
        self.refresh = refresh
        if self.enabled:
            try:
                self.dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we can't create the cache dir, silently disable caching
                # rather than break the run.
                self.enabled = False

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]
        return self.dir / f"{digest}.json"

    @staticmethod
    def _unwrap(raw: Any) -> tuple[float | None, Any, bool]:
        """Return ``(fetched_at, value, is_enveloped)``. Legacy entries written before
        TTL support are raw values with no envelope, reported as ``is_enveloped=False``."""
        if (
            isinstance(raw, dict)
            and raw.get(_ENVELOPE_KEY) == _ENVELOPE_VERSION
            and "value" in raw
        ):
            return raw.get("fetched_at"), raw["value"], True
        return None, raw, False

    def get(self, key: str, *, max_age: float | None = DEFAULT_MAX_AGE) -> Any | None:
        """Return the cached value, or ``None`` on a miss / expiry.

        ``max_age`` is the maximum age in seconds; ``None`` disables expiry. A legacy
        entry without a timestamp is only honored when expiry is disabled, otherwise it
        is treated as stale so it self-heals into the timestamped format on refetch."""
        if not self.enabled or self.refresh:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        fetched_at, value, is_enveloped = self._unwrap(raw)
        if not is_enveloped:
            return value if max_age is None else None
        if max_age is not None and fetched_at is not None:
            if (time.time() - fetched_at) > max_age:
                return None
        return value

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        envelope = {
            _ENVELOPE_KEY: _ENVELOPE_VERSION,
            "fetched_at": time.time(),
            "value": value,
        }
        try:
            self._path(key).write_text(
                json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except (OSError, TypeError):
            # Caching is best-effort; never raise.
            pass
