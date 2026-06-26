# Security Policy

## Supported versions
HireMe is pre-1.0 (alpha). Security fixes are applied to the latest `main` and the most recent release.

## Reporting a vulnerability
**Please do not open a public issue for security problems.**

Report privately via GitHub's
[security advisories](https://github.com/AdvancedUno/HireMe/security/advisories/new),
or email **ehlee8276@gmail.com**. We aim to acknowledge within 5 business days.

Please include: a description, steps to reproduce or a proof of concept, the affected
version/commit, and the impact.

## Handling secrets & personal data
HireMe is a local CLI that touches sensitive material — keep it that way:

- **API keys** (`ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, `GEMINI_API_KEY`,
  `KAGGLE_KEY`) live in `.env`, which is git-ignored. Never commit real keys; use
  `.env.example` as the template.
- **Personal data** (resumes, profile data) is processed locally and may be written to the
  `.hireme_cache/` directory and to generated `*.report.*` files — all git-ignored. Don't paste
  resumes, tokens, or cache contents into issues; redact before sharing logs.
- When filing a bug, run with `--verbose` but **scrub secrets and personal data** from the output.

## Dependencies & data egress
External calls (GitHub, Codeforces, Scholar, Kaggle, portfolio fetches) are made by collectors that
fail gracefully. Please report any case where a collector leaks a token or sends data to an
unexpected host.
