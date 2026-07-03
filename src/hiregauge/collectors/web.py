"""Portfolio / blog / personal-site collector — fetch a URL and extract main text.

Uses ``trafilatura`` for clean main-text extraction when installed; otherwise falls
back to a crude tag-strip so the collector still works on a core install. Cached;
never raises.

The URL is untrusted (auto-discovered from a resume), so the fetch goes through
``_safe_fetch.safe_get`` — SSRF-guarded (no private/loopback/link-local targets, even via
redirect) and body-size-capped. See issue #12.
"""

from __future__ import annotations

import re

from ..cache import WEB_MAX_AGE, Cache
from ..models import WebSignal
from ._safe_fetch import safe_get
from .base import cached_model

_UA = {"User-Agent": "Mozilla/5.0 (compatible; HireGauge/0.1; +https://github.com/AdvancedUno/HireGauge)"}
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_SCRIPT_STYLE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _extract(html: str) -> tuple[str | None, str]:
    m = _TITLE.search(html)
    title = _WS.sub(" ", _TAG.sub(" ", m.group(1))).strip() if m else None
    try:
        import trafilatura  # noqa: PLC0415 (optional dependency, lazy)

        text = trafilatura.extract(html) or ""
    except Exception:
        cleaned = _SCRIPT_STYLE.sub(" ", html)
        text = _WS.sub(" ", _TAG.sub(" ", cleaned)).strip()
    return title, text


def collect_web(url: str, *, cache: Cache, kind: str = "site") -> WebSignal | None:
    if not url:
        return None
    key = f"web:{url}"
    cached = cached_model(cache, key, WebSignal, max_age=WEB_MAX_AGE)
    if cached is not None:
        return cached
    try:
        resp = safe_get(url, headers=_UA, timeout=12.0)
    except Exception:
        # Never raise out of a collector — an unsafe/blocked URL or transport error just
        # degrades this source (the pipeline records a "could not fetch" note).
        return None
    if resp.status_code != 200 or "html" not in resp.headers.get("content-type", "").lower():
        return None
    title, text = _extract(resp.text)
    sig = WebSignal(
        url=url,
        kind=kind,
        title=title,
        text_excerpt=(text[:1500] or None) if text else None,
        word_count=len(text.split()) if text else 0,
    )
    cache.set(key, sig.model_dump())
    return sig
