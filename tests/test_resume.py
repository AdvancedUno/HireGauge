"""Tests for the resume collector's deterministic link/identifier discovery."""

from __future__ import annotations

from hiregauge.collectors.resume import collect_resume, discover_profiles


def test_discovers_common_profiles_from_text_and_uris():
    text = (
        "Jane Doe  jane.doe@example.com\n"
        "github.com/janedoe | linkedin.com/in/jane-doe\n"
        "codeforces.com/profile/jdoe  https://jane.dev\n"
    )
    uris = ["https://kaggle.com/janedoe", "https://leetcode.com/janed"]
    d = discover_profiles(text, uris)

    assert d.github == "janedoe"
    assert d.linkedin == "jane-doe"
    assert d.codeforces == "jdoe"
    assert d.kaggle == "janedoe"
    assert d.leetcode == "janed"
    assert d.email == "jane.doe@example.com"
    assert any("jane.dev" in w for w in d.websites)


def test_embedded_links_take_priority_over_inline_text():
    # Inline text mentions a project repo; the embedded link is the real profile.
    text = "Built on github.com/torvalds/linux during an internship."
    uris = ["https://github.com/realcandidate"]
    assert discover_profiles(text, uris).github == "realcandidate"


def test_skips_reserved_github_paths():
    d = discover_profiles("see github.com/features then github.com/realuser", [])
    assert d.github == "realuser"


def test_github_prefers_bare_profile_over_referenced_repo():
    # A third-party repo is referenced before the candidate's own profile link.
    text = "Built on github.com/facebook/react. My code: github.com/janedoe"
    assert discover_profiles(text, []).github == "janedoe"


def test_twitter_regex_ignores_corporate_hosts_ending_in_x_com():
    # 'netflix.com' contains the substring 'x.com' but must not yield a Twitter handle,
    # and the URL must survive as a personal website (not be filtered as a social host).
    d = discover_profiles("Worked at https://netflix.com/jobs on streaming.", [])
    assert d.twitter is None
    assert any("netflix.com" in w for w in d.websites)


def test_real_twitter_handle_still_discovered():
    d = discover_profiles("Find me at https://x.com/janedoe", [])
    assert d.twitter == "janedoe"


def test_discovered_identifiers_excludes_websites():
    d = discover_profiles("me github.com/jane https://jane.dev jane@x.io", [])
    ids = d.identifiers()
    assert ids.get("github") == "jane"
    assert ids.get("email") == "jane@x.io"
    assert "websites" not in ids  # the websites list is rendered separately


def test_returns_empty_when_nothing_found():
    d = discover_profiles("no links here at all", [])
    assert d.github is None
    assert d.email is None
    assert d.websites == []


def test_missing_file_returns_none():
    assert collect_resume("does-not-exist-12345.pdf") is None


def test_collect_resume_from_text_file(tmp_path):
    p = tmp_path / "resume.txt"
    p.write_text(
        "Sam Park sam@x.io\nGitHub: https://github.com/sampark\nPortfolio: https://sampark.io\n",
        encoding="utf-8",
    )
    sig = collect_resume(str(p))
    assert sig is not None
    assert sig.char_count > 0
    assert sig.discovered.github == "sampark"
    assert sig.discovered.email == "sam@x.io"
    assert any("sampark.io" in w for w in sig.discovered.websites)
    assert "https://github.com/sampark" in sig.links
