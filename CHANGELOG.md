# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses semantic versioning for public releases.

## [Unreleased]

### Fixed

- Treat cache entries as expired when they reach the requested TTL boundary,
  including `max_age=0`.

## [0.1.0] - 2026-07-03

### Added

- Initial HireGauge CLI with five specialized evaluation agents: quant, AI research,
  big tech, general software engineering, and university admissions.
- Resume-centered signal collection across GitHub, publications, Kaggle,
  portfolio/web pages, and competitive-programming identifiers.
- Deterministic signal grounding for GitHub authenticity, cached collectors, and
  rubric-backed scoring.
- Markdown, JSON, and HTML report rendering with verdict, percentile estimate,
  cited evidence, strengths, gaps, and prioritized next steps.
- Development, testing, and contribution documentation.
