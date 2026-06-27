"""Shared collector utilities.

Collectors turn an external identity into a typed ``Signal``. They must never raise
out to the pipeline — on any failure they return ``None``/empty and let the caller
record a note. External calls are cached.
"""

from __future__ import annotations

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from ..cache import Cache

DEFAULT_TIMEOUT = 12.0

T = TypeVar("T", bound=BaseModel)


def cached_model(cache: Cache, key: str, model: type[T]) -> T | None:
    """Rehydrate a cached value into ``model``. Returns ``None`` on a miss OR when the
    cached JSON no longer matches the schema (drift/corruption) — so a collector degrades
    to a refetch instead of raising, honoring the never-hard-fail contract."""
    data = cache.get(key)
    if data is None:
        return None
    try:
        return model.model_validate(data)
    except Exception:
        return None


def http_json(
    url: str,
    *,
    cache: Cache,
    cache_key: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any | None:
    """GET JSON with caching. Returns parsed JSON on HTTP 200, else ``None``. Never raises."""
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(
            url, headers=headers, params=params, timeout=timeout, follow_redirects=True
        )
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    cache.set(cache_key, data)
    return data
