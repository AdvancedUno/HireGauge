#!/usr/bin/env bash
# Apply branch-protection rules to `main` for AdvancedUno/HireMe.
#
# Requires the GitHub CLI (`gh auth login`) with admin rights on the repo.
# Run AFTER the CI workflow has been pushed so its status checks exist.
#
#   bash scripts/setup-branch-protection.sh
#
# Rules applied:
#   - require a PR with 1 approving review (stale reviews dismissed on new commits)
#   - require the CI checks `test (3.11)` and `test (3.12)` to pass, branch up to date
#   - require linear history; block force-pushes and branch deletion
#   - enforce all of the above for admins too (enforce_admins=true)
set -euo pipefail

REPO="${REPO:-AdvancedUno/HireMe}"
BRANCH="${BRANCH:-main}"

gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["test (3.11)", "test (3.12)"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 1, "dismiss_stale_reviews": true },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Branch protection applied to ${REPO}@${BRANCH}."

# ---------------------------------------------------------------------------
# SOLO-MAINTAINER ESCAPE HATCH
# With "1 required review" + enforce_admins=true you cannot merge your own PRs
# (GitHub blocks self-approval, and admin-enforce removes your bypass).
#
# To TEMPORARILY relax so you can self-merge, run:
#
#   gh api -X PUT "repos/AdvancedUno/HireMe/branches/main/protection" \
#     -H "Accept: application/vnd.github+json" --input - <<'JSON'
#   { "required_status_checks": { "strict": true, "contexts": ["test (3.11)", "test (3.12)"] },
#     "enforce_admins": false,
#     "required_pull_request_reviews": { "required_approving_review_count": 0 },
#     "restrictions": null, "required_linear_history": true,
#     "allow_force_pushes": false, "allow_deletions": false }
#   JSON
#
# Merge your PR, then re-run THIS script to re-tighten.
# ---------------------------------------------------------------------------
