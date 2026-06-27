"""Publications collector — best-effort Google Scholar via the optional ``scholarly`` lib.

Scholar has no official API and ``scholarly`` is rate-limited/blockable, so this is
strictly best-effort: if the lib is missing or the fetch fails, it returns ``None`` and
the resume text (which lists publications) still feeds the evaluator. Cached; never raises.
"""

from __future__ import annotations

import re

from ..cache import Cache
from ..models import Publication, PublicationSignal
from .base import cached_model

_SCHOLAR_USER = re.compile(r"[?&]user=([A-Za-z0-9_-]+)", re.IGNORECASE)


def _scholar_user_id(scholar_url: str | None) -> str | None:
    if not scholar_url:
        return None
    m = _SCHOLAR_USER.search(scholar_url)
    return m.group(1) if m else None


def collect_publications(
    *,
    scholar_url: str | None = None,
    orcid: str | None = None,
    arxiv: str | None = None,
    cache: Cache,
) -> PublicationSignal | None:
    user_id = _scholar_user_id(scholar_url)
    if not user_id:
        # Only the Scholar path is implemented; ORCID/arXiv stay resume-derived for now.
        return None

    key = f"scholar:{user_id}"
    cached = cached_model(cache, key, PublicationSignal)
    if cached is not None:
        return cached

    try:
        from scholarly import scholarly  # noqa: PLC0415 (optional dependency, lazy)

        author = scholarly.search_author_id(user_id)
        author = scholarly.fill(author, sections=["indices", "publications"])
    except Exception:
        return None

    try:
        pubs: list[Publication] = []
        for p in (author.get("publications") or [])[:25]:
            bib = p.get("bib", {}) or {}
            year_raw = str(bib.get("pub_year", ""))
            pubs.append(
                Publication(
                    title=(bib.get("title") or "")[:300],
                    venue=bib.get("venue") or bib.get("citation"),
                    year=int(year_raw) if year_raw.isdigit() else None,
                    citations=p.get("num_citations", 0) or 0,
                )
            )
        pubs.sort(key=lambda x: x.citations, reverse=True)
        sig = PublicationSignal(
            source="scholar",
            h_index=author.get("hindex"),
            total_citations=author.get("citedby"),
            publications=pubs,
        )
        cache.set(key, sig.model_dump())
        return sig
    except Exception:
        return None
