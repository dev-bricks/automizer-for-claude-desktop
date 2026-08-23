# Changelog

All notable changes to `dev-bricks/automizer-for-claude-desktop` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-08-23

### Added
- Interactive End-to-End Task Lifecycle sequence diagram (`sequenceDiagram` in Mermaid) illustrating agent request staging, process discrimination, atomic backups, registry merging, and verification across `README.md` and `README_de.md`.
- Structured Quick Navigation jump tables across English and German documentation.
- Comprehensive Key Capabilities and Safety Invariants architecture matrix detailing process isolation, atomic snapshots, anti-disabling guards, and zero-egress properties.
- Enhanced bilingual `SECURITY.md` with direct security contacts (`security@ellmos.ai`, `lukas@open-bricks.org`, `support@lukasgeiger.com`), GitHub Security Advisories integration, and supported versions matrix.
- Extended automated contract test suite in `tests/test_metadata.py` covering Mermaid syntax integrity, sibling ecosystem URLs, security invariants, and PEP 621 classifiers (25 passed tests, 100% green).
- Expanded PEP 621 metadata in `pyproject.toml` with `Changelog`, `Security`, and `Umbrella` project URLs as well as Windows OS and administration classifiers.

### Changed
- Synchronized Shields.io status badges across `README.md` and `README_de.md` (CI status, Python 3.8-3.13, Platform Windows, Security Local-First, Version 1.0.3, and Pytest 25 passed | 100%).
- Updated `llms.txt` AI/LLM context index timestamp to `2026-08-23` and test status to 25 verified tests.

## [1.0.2] - 2026-08-21

### Added
- Multi-version GitHub Actions CI workflow (`.github/workflows/ci.yml`) with test matrix across Python 3.10, 3.11, 3.12, and 3.13 on Ubuntu and Windows runners.
- Explicit PEP 621 classifiers for Python 3.13, project discovery keywords, and `[project.urls]` metadata (Homepage, Repository, Issues, Documentation) in `pyproject.toml`.
- Expanded automated metadata test suite in `tests/test_metadata.py` with CI workflow verification and `pyproject.toml` metadata contract tests (23 passed tests, 100% green).
- Dedicated `SECURITY.md` defining local-first, zero-egress, process discrimination, and vulnerability disclosure policies.
- Sibling tools and ecosystem navigation matrix (`dev-bricks`, `ellmos-ai`, `open-bricks`) across both `README.md` and `README_de.md`.
- `[tool.ruff]` and `[tool.ruff.lint]` configuration in `pyproject.toml`.

### Changed
- Added GitHub Actions CI status badge to `README.md` and `README_de.md`.
- Synchronized Pytest test badges in `README.md` and `README_de.md` to 23 passed tests (100% green).
- Updated `llms.txt` AI/LLM context index timestamp to `2026-08-21` with 23 unit and metadata tests verified.

## [1.0.1] - 2026-08-14


### Added
- Expanded unit test suite `tests/test_automizer.py` with test coverage for `claude_desktop_paths.diagnose()` and `_app_daten_wurzeln()`, reaching 16 total unit tests (100% pass rate).
- Full English canonical `README.md` and complete German `README_de.md` documentation parity with bilingual language switchers, updated Shields.io status badges, GFM callout boxes, and architecture Mermaid diagrams.

### Changed
- Synchronized Pytest test badges in `README.md` and `README_de.md` from 12 to 16 passed tests.
- Updated `llms.txt` AI/LLM context index timestamp to `2026-08-14`, including canonical repository URLs, keyword index, and test verification count.
- Added version badges (`v1.0.1`) across documentation files.

## [1.0.0] - 2026-07-20
- Initial import and public repository setup.
