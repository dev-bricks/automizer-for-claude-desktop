# Changelog

All notable changes to `dev-bricks/automizer-for-claude-desktop` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
