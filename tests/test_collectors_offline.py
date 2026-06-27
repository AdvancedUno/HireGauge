"""Offline collector tests — GitHub + web, with the HTTP layer mocked via respx."""

from __future__ import annotations

import re

import httpx
import respx

from hireme.cache import Cache
from hireme.collectors.base import cached_model
from hireme.collectors.github import collect_github
from hireme.collectors.web import collect_web
from hireme.config import Settings
from hireme.models import WebSignal


@respx.mock
def test_collect_github_offline():
    user = {
        "login": "octocat", "name": "The Octocat", "public_repos": 2,
        "followers": 100, "following": 5, "bio": "bio", "blog": "https://x.dev",
        "created_at": "2015-01-01T00:00:00Z",
    }
    repos = [
        {
            "name": "r1", "stargazers_count": 50, "forks_count": 10, "language": "Python",
            "fork": False, "archived": False, "topics": ["x"], "open_issues_count": 2,
            "html_url": "https://github.com/octocat/r1", "pushed_at": "2026-01-01T00:00:00Z",
        },
        {"name": "fork1", "stargazers_count": 999, "forks_count": 0, "language": "C", "fork": True},
    ]
    respx.get(re.compile(r"https://api\.github\.com/users/octocat$")).mock(
        return_value=httpx.Response(200, json=user)
    )
    respx.get(re.compile(r"https://api\.github\.com/users/octocat/repos")).mock(
        return_value=httpx.Response(200, json=repos)
    )

    sig = collect_github("octocat", settings=Settings(_env_file=None), cache=Cache(enabled=False))
    assert sig is not None
    assert sig.username == "octocat"
    assert sig.public_repos == 2
    assert len(sig.repos) == 2
    assert "Python" in sig.top_languages
    assert "C" not in sig.top_languages  # the fork is excluded from owned-language stats


@respx.mock
def test_collect_github_404_returns_none():
    respx.get(re.compile(r"https://api\.github\.com/users/nope")).mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    sig = collect_github("nope", settings=Settings(_env_file=None), cache=Cache(enabled=False))
    assert sig is None


@respx.mock
def test_collect_web_offline_extracts_title_and_strips_script():
    page = (
        "<html><head><title>My Site</title></head><body>"
        "<script>danger()</script><h1>Hi</h1>"
        "<p>Hello world from the portfolio</p></body></html>"
    )
    respx.get(re.compile(r"https://jane\.dev/?$")).mock(
        return_value=httpx.Response(200, text=page, headers={"content-type": "text/html; charset=utf-8"})
    )
    sig = collect_web("https://jane.dev", cache=Cache(enabled=False))
    assert sig is not None
    assert sig.title == "My Site"
    assert "Hello world from the portfolio" in (sig.text_excerpt or "")
    assert "danger()" not in (sig.text_excerpt or "")  # <script> stripped


def test_cached_model_tolerates_corrupt_entry(tmp_path):
    # A drifted/corrupt cache entry must degrade to a miss (None), not raise — so the
    # collector refetches instead of crashing the run.
    cache = Cache(tmp_path, enabled=True)
    cache.set("bad", {"unexpected": "shape"})  # missing required `url`
    assert cached_model(cache, "bad", WebSignal) is None
    assert cached_model(cache, "absent", WebSignal) is None  # plain miss
    cache.set("ok", WebSignal(url="https://x.io").model_dump())
    got = cached_model(cache, "ok", WebSignal)
    assert got is not None and got.url == "https://x.io"


@respx.mock
def test_collect_web_non_html_returns_none():
    respx.get(re.compile(r"https://api\.example\.com")).mock(
        return_value=httpx.Response(200, json={"x": 1}, headers={"content-type": "application/json"})
    )
    assert collect_web("https://api.example.com", cache=Cache(enabled=False)) is None
