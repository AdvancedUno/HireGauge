## What & why
<!-- What does this change, and why? Link issues, e.g. "Closes #123". -->

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Collector / data source
- [ ] Agent / rubric change
- [ ] Docs / chore

## Checklist
- [ ] `pytest` passes
- [ ] `ruff check .` passes
- [ ] Any rubric weight/threshold traces to a cited source in `docs/rubrics.md` (no invented cutoffs)
- [ ] New/changed collectors don't hard-fail, cache external calls, and ship a test fixture
- [ ] Fairness respected — name/gender/demographics/location/institution don't drive scores beyond what research supports
- [ ] Updated `docs/TODO.md` (and other docs) if relevant
- [ ] Ran a `report-auditor` pass if this touches scoring or report templates

## Notes for reviewers
<!-- Anything that needs extra attention. -->
