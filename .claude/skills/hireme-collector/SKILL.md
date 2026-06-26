---
name: hireme-collector
description: How to add or modify a HireMe data-source collector — the Collector protocol, the never-hard-fail contract, the cache-key convention, recording API fixtures, and writing tests. Use whenever you create or edit a module under src/hireme/collectors/ or wire a new signal into the pipeline.
---

# Adding a HireMe collector

A collector turns an external identity into a typed `Signal` in `src/hireme/models.py`. Collectors are the
"ground truth" half of HireMe, so they must be robust and cached.

## The contract (non-negotiable)
1. **Never hard-fail.** Catch everything (network, 404, 403/429, parse errors, missing optional deps). Return
   `None`/empty and append a clear string to `CandidateProfile.collection_notes`. The run must still produce a report.
2. **Cache external calls** with `hireme.cache.Cache` — key = `f"{source}:{identity}:{params}"`. Honor `--no-cache`.
3. **Typed output** — return the source's Pydantic `Signal`; extend `models.py` with optional, backward-compatible fields.
4. **Config-driven secrets** — read tokens (`GITHUB_TOKEN`, `KAGGLE_*`) from `hireme.config.get_settings()`. Never hardcode.
5. **Lazy optional imports** — `trafilatura`, `scholarly`, `kaggle` import inside the function; degrade with a note if absent.

## Shape (follow `collectors/base.py` + `collectors/github.py`)
```python
def collect(identity: str, *, settings, cache) -> Signal | None:
    key = f"github:{identity}"
    cached = cache.get(key)
    if cached is not None:
        return GitHubSignal(**cached)
    try:
        ... # fetch (with timeouts + token + backoff), build the Signal
        cache.set(key, signal.model_dump())
        return signal
    except Exception as e:
        # caller records the note; return None
        return None
```

## Recording fixtures + tests
- Save a real, sanitized response under `tests/fixtures/<source>/<case>.json` (strip emails/secrets/PII).
- Write a pytest that mocks the HTTP layer (`respx` for httpx, `pytest-mock` otherwise) and asserts the parsed
  `Signal`. Add an edge case: 404 / rate-limit / empty → returns `None` + a note, never raises.
- Run `pytest -k <source>`, then a live smoke: `hireme --agent general --<source> <id>`.

## Source cheatsheet
- **GitHub**: `/users/{u}`, `/users/{u}/repos?sort=updated&per_page=100`, `/repos/{u}/{r}/contributors`,
  `/repos/{u}/{r}/languages`, `/repos/{u}/{r}/readme`. Token raises 60→5000/hr. Classify open-source vs self by
  contributor count; record stars/forks/pushed_at for authenticity + recency.
- **Codeforces**: `https://codeforces.com/api/user.info?handles=` and `user.rating` (rating, maxRating, rank, #contests).
- **Kaggle**: official API, needs `KAGGLE_USERNAME`/`KAGGLE_KEY`.
- **Scholar/arXiv/ORCID**: `scholarly` is fragile/rate-limited — always accept manual links.
- **LeetCode/LinkedIn**: no stable API → best-effort / manual export; guard hard.
- **Web**: `httpx.get(timeout=…)` → `trafilatura.extract`; fallback to a minimal tag-strip if trafilatura missing.

After adding a collector, wire it into `pipeline.py` (collect step) and the `signals` of agents that use it.
