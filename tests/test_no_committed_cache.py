"""Guard: cache directories must never be committed (issue #16).

Cache dirs (.hiregauge_cache/, the legacy .hireme_cache/, any future *_cache/) hold
fetched candidate data — resumes, GitHub dumps, portfolios — i.e. real PII. This test
fails if any such file is tracked in git, mirroring the CI guard so a stray
``git add`` is caught locally on ``pytest`` before it ever reaches a push.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_no_cache_directories_are_tracked():
    try:
        out = subprocess.run(
            ["git", "ls-files", "--", "*_cache/*"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available or not a git checkout")

    tracked = [line for line in out.stdout.splitlines() if line.strip()]
    assert not tracked, (
        "Cache directories must never be committed — they may contain candidate PII (#16). "
        f"Tracked cache files: {tracked}"
    )
