"""Tiny on-disk JSON cache for external API responses.

Keeps iteration cheap (and avoids hammering rate-limited APIs) during development.
Keys are arbitrary strings — collectors use ``"{source}:{identity}:{params}"``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class Cache:
    def __init__(self, directory: str | Path = ".hireme_cache", enabled: bool = True) -> None:
        self.dir = Path(directory)
        self.enabled = enabled
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

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        try:
            self._path(key).write_text(
                json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except (OSError, TypeError):
            # Caching is best-effort; never raise.
            pass
