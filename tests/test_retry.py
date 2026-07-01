"""Provider retry/backoff tests (issue #20)."""

from __future__ import annotations

import pytest

from hiregauge.llm._retry import RETRYABLE_STATUS, call_with_retry
from hiregauge.llm.anthropic_provider import _is_retryable


class _Transient(Exception):
    """Stand-in for a transient SDK error."""


def _no_sleep(_attempt: int) -> None:  # keep tests fast
    pass


def test_retries_transient_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _Transient("503")
        return "ok"

    result = call_with_retry(flaky, is_retryable=lambda exc: True, sleep=_no_sleep)
    assert result == "ok"
    assert calls["n"] == 3  # failed twice, succeeded on the third attempt


def test_non_retryable_error_propagates_immediately():
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        raise ValueError("bad request")

    with pytest.raises(ValueError):
        call_with_retry(boom, is_retryable=lambda exc: False, sleep=_no_sleep)
    assert calls["n"] == 1  # not retried


def test_gives_up_after_max_attempts_and_raises_last():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise _Transient("overloaded")

    with pytest.raises(_Transient):
        call_with_retry(
            always_fails, is_retryable=lambda exc: True, max_attempts=4, sleep=_no_sleep
        )
    assert calls["n"] == 4


def test_backoff_sleeps_between_attempts():
    slept: list[int] = []
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _Transient()
        return 42

    call_with_retry(flaky, is_retryable=lambda exc: True, sleep=slept.append)
    assert slept == [0, 1]  # one sleep before each of the two retries


# --- Anthropic-specific exception classification ---


class _FakeStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


@pytest.mark.parametrize("status", RETRYABLE_STATUS)
def test_anthropic_retryable_statuses(status):
    assert _is_retryable(_FakeStatusError(status)) is True


def test_anthropic_non_retryable_status():
    assert _is_retryable(_FakeStatusError(400)) is False
    assert _is_retryable(ValueError("nope")) is False


def test_anthropic_connection_and_timeout_are_retryable():
    # Classified by class name so we don't need the real SDK exception types.
    APITimeoutError = type("APITimeoutError", (Exception,), {})
    APIConnectionError = type("APIConnectionError", (Exception,), {})
    assert _is_retryable(APITimeoutError()) is True
    assert _is_retryable(APIConnectionError()) is True


# --- end-to-end: the provider retries a transient overloaded error then succeeds ---


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]


class _Messages:
    """Fake messages API: 529-overloaded on the first call, then a valid response.
    Has no ``parse`` attribute, so the provider falls to the json_schema create path."""

    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise _FakeStatusError(529)
        return _Resp('{"value": "ok"}')


class _FakeClient:
    def __init__(self) -> None:
        self.messages = _Messages()


def test_anthropic_provider_retries_overloaded_then_succeeds(monkeypatch):
    monkeypatch.setattr("hiregauge.llm._retry.time.sleep", lambda _s: None)
    from pydantic import BaseModel

    from hiregauge.llm.anthropic_provider import AnthropicProvider

    class _Out(BaseModel):
        value: str

    provider = AnthropicProvider(model="claude-test", api_key="k")
    provider._client = _FakeClient()  # inject fake so no real SDK/network is touched

    out = provider.complete_structured(system="s", user="u", schema=_Out)
    assert out.value == "ok"
    assert provider._client.messages.calls == 2  # failed once, retried, then succeeded
