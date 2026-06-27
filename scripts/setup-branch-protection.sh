#!/usr/bin/env bash
# Apply branch-protection rules to `main` for AdvancedUno/HireGauge.
#
# Requires the GitHub CLI (`gh auth login`) with admin rights on the repo.
# Run AFTER the CI workflow has been pushed so its status checks exist.
#
#   bash scripts/setup-branch-protection.sh
#
# Default = SOLO-FRIENDLY profile (current maintainer setup):
#   - require a PR, but 0 approving reviews -> you can self-merge your own PRs
#   - require the CI checks `test (3.11)` and `test (3.12)` to pass, branch up to date
#   - require linear history; block force-pushes and branch deletion
#   - enforce_admins=false -> you keep an admin bypass for emergencies
#
# This keeps the guardrails that catch real accidents (broken CI, force-push,
# branch deletion) without blocking a solo maintainer on a non-existent reviewer.
set -euo pipefail

REPO="${REPO:-AdvancedUno/HireGauge}"
BRANCH="${BRANCH:-main}"

gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["test (3.11)", "test (3.12)"] },
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 0, "dismiss_stale_reviews": false },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Solo-friendly branch protection applied to ${REPO}@${BRANCH}."

# ---------------------------------------------------------------------------
# TIGHTEN FOR A TEAM
# Once you have collaborators (or a review bot), require an approving review
# and enforce the rules for admins too. Run:
#
#   gh api -X PUT "repos/AdvancedUno/HireGauge/branches/main/protection" \
#     -H "Accept: application/vnd.github+json" --input - <<'JSON'
#   { "required_status_checks": { "strict": true, "contexts": ["test (3.11)", "test (3.12)"] },
#     "enforce_admins": true,
#     "required_pull_request_reviews": { "required_approving_review_count": 1, "dismiss_stale_reviews": true },
#     "restrictions": null, "required_linear_history": true,
#     "allow_force_pushes": false, "allow_deletions": false }
#   JSON
#
# Note: with 1 required review + enforce_admins=true you cannot merge your own
# PRs (GitHub blocks self-approval), so only tighten once a second reviewer exists.
# ---------------------------------------------------------------------------
