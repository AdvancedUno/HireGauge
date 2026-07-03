"""SSRF guard + response-size cap tests (issue #12)."""

from __future__ import annotations

import re

import httpx
import pytest
import respx

from hiregauge.cache import Cache
from hiregauge.collectors._safe_fetch import (
    MAX_BYTES,
    FetchResult,
    UnsafeURLError,
    safe_get,
    validate_url,
)
from hiregauge.collectors.web import collect_web

_PUBLIC = "93.184.216.34"


def _stub_resolver(monkeypatch, ips):
    monkeypatch.setattr(
        "hiregauge.collectors._safe_fetch.resolve_host", lambda host, port: ips
    )


# --- validate_url: scheme + address blocking ---


@pytest.mark.parametrize("url", ["ftp://x.dev", "file:///etc/passwd", "gopher://x", "//x.dev"])
def test_non_http_schemes_refused(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost/",  # resolves to loopback (real getaddrinfo)
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata (link-local)
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://[::1]/",
    ],
)
def test_internal_ip_literals_refused(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


def test_public_ip_literal_allowed():
    validate_url(f"http://{_PUBLIC}/")  # no raise


def test_hostname_resolving_to_internal_is_refused(monkeypatch):
    _stub_resolver(monkeypatch, ["10.1.2.3"])
    with pytest.raises(UnsafeURLError):
        validate_url("http://evil.example/")


def test_hostname_refused_if_any_resolved_ip_is_internal(monkeypatch):
    # Split-horizon trick: one public + one internal address must still be blocked.
    _stub_resolver(monkeypatch, [_PUBLIC, "127.0.0.1"])
    with pytest.raises(UnsafeURLError):
        validate_url("http://mixed.example/")


# --- safe_get: redirects re-validated, body capped ---


@respx.mock
def test_redirect_to_internal_is_blocked(monkeypatch):
    _stub_resolver(monkeypatch, [_PUBLIC])
    respx.get("https://public.example/").mock(
        return_value=httpx.Response(302, headers={"location": "http://169.254.169.254/"})
    )
    with pytest.raises(UnsafeURLError):
        safe_get("https://public.example/")


@respx.mock
def test_oversized_body_is_truncated_not_fully_loaded(monkeypatch):
    _stub_resolver(monkeypatch, [_PUBLIC])
    big = "a" * (MAX_BYTES + 5_000_000)  # well over the cap
    respx.get("https://public.example/").mock(
        return_value=httpx.Response(200, text=big, headers={"content-type": "text/html"})
    )
    result = safe_get("https://public.example/")
    assert isinstance(result, FetchResult)
    assert result.truncated is True
    assert len(result.text.encode("utf-8")) <= MAX_BYTES


# --- collector integration: blocked URL degrades to None, never raises ---


def test_collect_web_blocks_internal_url_and_returns_none():
    # No respx needed: the guard rejects before any network call.
    assert collect_web("http://169.254.169.254/latest/meta-data/", cache=Cache(enabled=False)) is None
    assert collect_web("http://localhost:8080/", cache=Cache(enabled=False)) is None


@respx.mock
def test_collect_web_caps_giant_page(monkeypatch):
    _stub_resolver(monkeypatch, [_PUBLIC])
    page = "<html><title>Big</title><body>" + ("x " * 5_000_000) + "</body></html>"
    respx.get(re.compile(r"https://huge\.example/?$")).mock(
        return_value=httpx.Response(200, text=page, headers={"content-type": "text/html"})
    )
    sig = collect_web("https://huge.example", cache=Cache(enabled=False))
    assert sig is not None  # still parses the capped prefix
    assert sig.title == "Big"
