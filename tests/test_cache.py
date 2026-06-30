"""Cache TTL + refresh tests (issue #18)."""

from __future__ import annotations

import json
import time

from hiregauge.cache import DEFAULT_MAX_AGE, Cache


def test_fresh_entry_is_a_hit(tmp_path):
    c = Cache(tmp_path)
    c.set("k", {"stars": 10})
    assert c.get("k") == {"stars": 10}


def test_entry_past_max_age_is_a_miss(tmp_path):
    c = Cache(tmp_path)
    c.set("k", {"stars": 10})
    # Default TTL: fresh now, stale when we ask for a 0-second max age.
    assert c.get("k", max_age=0) is None
    assert c.get("k", max_age=DEFAULT_MAX_AGE) == {"stars": 10}


def test_max_age_none_never_expires(tmp_path):
    c = Cache(tmp_path)
    c.set("k", {"v": 1})
    assert c.get("k", max_age=0) is None  # would be stale under a TTL
    assert c.get("k", max_age=None) == {"v": 1}  # ...but TTL disabled => hit


def test_stale_timestamp_is_refetched(tmp_path):
    c = Cache(tmp_path)
    c.set("k", {"v": 1})
    # Backdate the stored timestamp to two days ago.
    path = c._path("k")
    env = json.loads(path.read_text())
    env["fetched_at"] = time.time() - 2 * DEFAULT_MAX_AGE
    path.write_text(json.dumps(env))
    assert c.get("k") is None


def test_refresh_mode_misses_reads_but_still_writes(tmp_path):
    Cache(tmp_path).set("k", {"v": 1})  # pre-populate with a normal cache
    refreshing = Cache(tmp_path, refresh=True)
    assert refreshing.get("k") is None  # read bypassed -> forces a refetch
    refreshing.set("k", {"v": 2})  # ...and the fresh value is written back
    assert Cache(tmp_path).get("k") == {"v": 2}


def test_legacy_raw_entry_treated_as_stale_under_ttl(tmp_path):
    c = Cache(tmp_path)
    # Simulate a pre-TTL cache file: a raw value with no envelope.
    c._path("k").write_text(json.dumps({"stars": 5}))
    assert c.get("k") is None  # no timestamp -> stale under a TTL
    assert c.get("k", max_age=None) == {"stars": 5}  # ...but usable when TTL disabled


def test_disabled_cache_reads_and_writes_nothing(tmp_path):
    c = Cache(tmp_path, enabled=False)
    c.set("k", {"v": 1})
    assert c.get("k") is None
