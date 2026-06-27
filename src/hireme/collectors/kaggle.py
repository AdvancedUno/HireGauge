"""Kaggle collector.

Kaggle profile stats (medals/tiers) are rendered client-side and the official
``kaggle`` package exposes datasets/kernels, not a clean per-user medal summary — so
there is no reliable, key-free way to fetch them. This collector therefore records the
handle (so the report acknowledges the profile) and leaves medal/tier claims to the
resume text, which the evaluator reads. Cached; never raises. Kept as a clear seam for
a future authenticated implementation.
"""

from __future__ import annotations

from ..cache import Cache
from ..config import Settings
from ..models import KaggleSignal
from .base import cached_model


def collect_kaggle(handle: str, *, settings: Settings, cache: Cache) -> KaggleSignal | None:
    if not handle:
        return None
    key = f"kaggle:{handle}"
    cached = cached_model(cache, key, KaggleSignal)
    if cached is not None:
        return cached
    sig = KaggleSignal(handle=handle)
    cache.set(key, sig.model_dump())
    return sig
