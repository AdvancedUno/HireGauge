"""Tests for the deterministic resume-claim cross-check module."""

from __future__ import annotations

from hiregauge.analysis.crosscheck import crosscheck_claims
from hiregauge.models import (
    CandidateProfile,
    GitHubRepo,
    GitHubSignal,
    Publication,
    PublicationSignal,
    ResumeSignal,
)


def _profile_with_resume(text: str) -> CandidateProfile:
    return CandidateProfile(
        resume=ResumeSignal(text=text, char_count=len(text)),
    )


def _profile_with_github(text: str, max_stars: int = 10) -> CandidateProfile:
    gh = GitHubSignal(
        username="test",
        repos=[GitHubRepo(name="r1", stars=max_stars)],
    )
    gh.authenticity = {"max_stars": max_stars, "owned_repos": 1, "recently_active_repos": 0}
    return CandidateProfile(
        resume=ResumeSignal(text=text, char_count=len(text)),
        github=gh,
    )


def _profile_with_pubs(
    text: str, n_pubs: int = 0, source: str = "scholar", h_index: int | None = 5
) -> CandidateProfile:
    return CandidateProfile(
        resume=ResumeSignal(text=text, char_count=len(text)),
        publications=PublicationSignal(
            source=source,
            h_index=h_index,
            publications=[Publication(title=f"p{i}") for i in range(n_pubs)],
        ),
    )

# ---------------------------------------------------------------------------
# Star-inflation tests
# ---------------------------------------------------------------------------


def test_no_resume_returns_empty():
    assert crosscheck_claims(CandidateProfile()) == []


def test_no_star_mention_returns_empty():
    profile = _profile_with_resume("I build web apps with React and Django.")
    profile.github = GitHubSignal(username="test")
    profile.github.authenticity = {"max_stars": 100}
    assert crosscheck_claims(profile) == []


def test_honest_star_claim_not_flagged():
    # Resume claims 50 stars, fetched shows 100 — claim is lower, no flag.
    profile = _profile_with_github(
        "My project has 50+ stars on GitHub.", max_stars=100
    )
    assert crosscheck_claims(profile) == []


def test_star_inflation_flagged():
    # Resume claims 1000+ stars, fetched shows max_stars=12 — clearly inflated.
    profile = _profile_with_github(
        "My open-source project has over 1,000+ stars!", max_stars=12
    )
    issues = crosscheck_claims(profile)
    assert len(issues) == 1
    assert "Star-count inflation" in issues[0]
    assert "1000" in issues[0]
    assert "12" in issues[0]


def test_star_inflation_variant_formats():
    # "stars: 500" format
    profile = _profile_with_github(
        "stars: 500 on my most popular repo", max_stars=8
    )
    assert len(crosscheck_claims(profile)) == 1


def test_no_github_signal_returns_empty():
    profile = _profile_with_resume("My repo has 1000 stars!")
    assert crosscheck_claims(profile) == []


def test_no_authenticity_data_returns_empty():
    gh = GitHubSignal(username="test")
    profile = _profile_with_resume("My repo has 1000 stars!")
    profile.github = gh
    # No authenticity dict set
    assert crosscheck_claims(profile) == []

# ---------------------------------------------------------------------------
# Phantom-publication tests
# ---------------------------------------------------------------------------


def test_no_publication_mention_returns_empty():
    profile = _profile_with_resume("I build web apps with React and Django.")
    profile.publications = PublicationSignal(source="scholar", publications=[])
    assert crosscheck_claims(profile) == []


def test_phantom_publication_flagged():
    profile = _profile_with_pubs(
        "I published a first-author paper at NeurIPS and another at ICML.",
        n_pubs=0,
    )
    issues = crosscheck_claims(profile)
    assert len(issues) == 1
    assert "Phantom-publication claim" in issues[0]
    assert "NeurIPS" in issues[0] or "neurips" in issues[0]
    assert "ICML" in issues[0] or "icml" in issues[0]


def test_real_publications_not_flagged():
    # Resume mentions publications and fetched data confirms them.
    profile = _profile_with_pubs(
        "I published at NeurIPS and ICML.",
        n_pubs=2,
    )
    assert crosscheck_claims(profile) == []


def test_single_venue_not_enough():
    # Only one venue keyword should not trigger the flag before _MIN_VENUE_HITS.
    profile = _profile_with_pubs(
        "I am interested in NeurIPS papers.",
        n_pubs=0,
    )
    assert crosscheck_claims(profile) == []


def test_no_publication_signal_returns_empty():
    profile = _profile_with_resume("My first-author paper was at CVPR.")
    assert crosscheck_claims(profile) == []


def test_phantom_with_generic_indicator():
    profile = _profile_with_pubs(
        "I have a published paper titled 'AI for Good' in the proceedings of IEEE."
        " It was co-authored with my advisor.",
        n_pubs=0,
    )
    issues = crosscheck_claims(profile)
    assert len(issues) == 1
    assert "Phantom-publication claim" in issues[0]

# ---------------------------------------------------------------------------
# Integration: both checks together
# ---------------------------------------------------------------------------


def test_both_checks_fire_independently():
    text = (
        "My project has over 5,000 GitHub stars! "
        "I also published a first-author paper at ICML."
    )
    gh = GitHubSignal(
        username="test",
        repos=[GitHubRepo(name="r1", stars=3)],
    )
    gh.authenticity = {"max_stars": 3, "owned_repos": 1}
    profile = CandidateProfile(
        resume=ResumeSignal(text=text, char_count=len(text)),
        github=gh,
        publications=PublicationSignal(
            source="scholar", h_index=None, publications=[]
        ),
    )
    issues = crosscheck_claims(profile)
    assert len(issues) == 2


def test_exception_returns_empty():
    # Passing something that would cause an error should return [].
    assert crosscheck_claims(CandidateProfile()) == []
