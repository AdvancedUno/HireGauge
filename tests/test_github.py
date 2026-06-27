"""Tests for GitHub username extraction and deterministic authenticity signals."""

from __future__ import annotations

from hiregauge.analysis.github_authenticity import _is_recent, assess_github
from hiregauge.collectors.github import extract_username
from hiregauge.models import GitHubRepo, GitHubSignal


def test_extract_username_variants():
    assert extract_username("https://github.com/AdvancedUno") == "AdvancedUno"
    assert extract_username("github.com/janedoe/some-repo") == "janedoe"
    assert extract_username("@octocat") == "octocat"
    assert extract_username("octocat") == "octocat"
    assert extract_username("not a real handle!!") is None
    assert extract_username(None) is None


def test_assess_github_counts_owned_only():
    g = GitHubSignal(
        username="x",
        repos=[
            GitHubRepo(name="a", stars=10, forks=2, language="Python"),
            GitHubRepo(name="b", stars=0, forks=0, language="C++"),
            GitHubRepo(name="forked", stars=100, forks=0, language="Python", is_fork=True),
        ],
    )
    a = assess_github(g)
    assert a["owned_repos"] == 2
    assert a["forks_in_list"] == 1
    assert a["total_stars"] == 10
    assert a["total_forks"] == 2
    assert a["max_stars"] == 10
    assert a["fork_to_star_ratio"] == 0.2


def test_is_recent_tolerates_naive_and_bad_timestamps():
    # A timezone-naive timestamp must not raise on the aware/naive subtraction.
    assert _is_recent(None) is False
    assert _is_recent("not-a-date") is False
    assert _is_recent("2024-01-01T00:00:00") is False  # naive + old -> not recent, no crash


def test_assess_github_does_not_crash_on_naive_pushed_at():
    g = GitHubSignal(username="x", repos=[GitHubRepo(name="a", pushed_at="2024-01-01T00:00:00")])
    a = assess_github(g)  # must not raise (pushed_at lacks a 'Z'/offset)
    assert a["owned_repos"] == 1
