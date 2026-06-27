"""Tests for the deterministic 0..1 strength scorers."""

from __future__ import annotations

from hireme.analysis.deterministic import (
    citation_strength,
    github_strength,
    publication_strength,
    signal_strengths,
)
from hireme.models import (
    CandidateProfile,
    GitHubRepo,
    GitHubSignal,
    Publication,
    PublicationSignal,
)


def test_github_strength_bounds_and_monotonic():
    assert github_strength(None) is None

    weak = GitHubSignal(username="x", top_languages=["Python"], repos=[GitHubRepo(name="a")])
    weak.authenticity = {"owned_repos": 1, "max_stars": 0, "recently_active_repos": 0}

    # A "solid" profile is genuinely good but, under the demanding curve, must NOT max out —
    # it should sit comfortably below 1.0 so the blend can't inflate a middling GitHub.
    solid = GitHubSignal(
        username="y",
        top_languages=["Python", "C++", "Go", "Rust", "JS"],
        repos=[GitHubRepo(name=f"r{i}", stars=50, language="Python") for i in range(10)],
    )
    solid.authenticity = {"owned_repos": 10, "max_stars": 150, "recently_active_repos": 5}

    # Only a genuinely elite profile (broad, very active, with a standout high-star project)
    # approaches the ceiling.
    elite = GitHubSignal(
        username="z",
        top_languages=["Python", "C++", "Go", "Rust", "JS", "TS"],
        repos=[GitHubRepo(name=f"r{i}", stars=300, language="Python") for i in range(15)],
    )
    elite.authenticity = {"owned_repos": 15, "max_stars": 1000, "recently_active_repos": 8}

    sw, ssolid, se = github_strength(weak), github_strength(solid), github_strength(elite)
    assert 0.0 <= sw <= 1.0
    assert sw < ssolid < se <= 1.0
    assert ssolid < 0.8  # a solid-but-ordinary profile no longer maxes out
    assert se == 1.0  # only an elite profile reaches the ceiling


def test_citation_strength():
    assert citation_strength(None) is None
    assert citation_strength(PublicationSignal()) is None  # no h-index / citations
    assert citation_strength(PublicationSignal(h_index=20, total_citations=2000)) == 1.0
    assert 0.0 < citation_strength(PublicationSignal(h_index=5)) < 1.0


def test_publication_strength():
    assert publication_strength(None) is None
    assert publication_strength(PublicationSignal()) is None
    full = PublicationSignal(
        h_index=20, total_citations=2000,
        publications=[Publication(title=f"p{i}") for i in range(8)],
    )
    assert publication_strength(full) == 1.0
    partial = PublicationSignal(h_index=5, total_citations=100, publications=[Publication(title="p")])
    assert 0.0 < publication_strength(partial) < 1.0


def test_signal_strengths_keys_and_empty_profile():
    s = signal_strengths(CandidateProfile())
    assert set(s) == {"github", "publication", "citation"}
    assert all(v is None for v in s.values())
