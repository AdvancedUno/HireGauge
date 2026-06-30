"""Shared transient-error retry with exponential backoff + jitter.

Both providers wrap their network call with :func:`call_with_retry` so a transient
``429 / 500 / 503 / 529`` (overloaded) hiccup is retried rather than bubbling up into a
0/100 "Evaluation could not be completed" fallback report (issue #20). Each provider
supplies an ``is_retryable`` predicate over its own SDK's exception types.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

MAX_ATTEMPTS = 6
# HTTP statuses worth retrying: rate limit, server errors, and Anthropic's 529 overloaded.
RETRYABLE_STATUS = (429, 500, 503, 529)


def _default_sleep(attempt: int) -> None:
    # Exponential backoff capped at 8s, plus jitter to avoid synchronized retries.
    time.sleep(min(2**attempt, 8) + random.random())


def call_with_retry(
    fn: Callable[[], T],
    *,
    is_retryable: Callable[[BaseException], bool],
    max_attempts: int = MAX_ATTEMPTS,
    sleep: Callable[[int], None] = _default_sleep,
) -> T:
    """Call ``fn`` and return its result, retrying transient failures with backoff.

    A raised exception is retried only while ``is_retryable(exc)`` is true and attempts
    remain; otherwise it propagates unchanged. ``sleep`` is injectable so tests can run
    without real delays."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below unless retryable
            if attempt < max_attempts - 1 and is_retryable(exc):
                sleep(attempt)
                continue
            raise
    raise AssertionError("unreachable: loop always returns or raises")  # pragma: no cover
