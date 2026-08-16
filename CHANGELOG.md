# Changelog

All notable changes to `dev-bricks/automizer-for-claude-desktop` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-08-16

### Added
- Created dedicated `SECURITY.md` defining local-first, zero-egress, process discrimination, and vulnerability disclosure policies.
- Implemented automated metadata, badge, and documentation parity test suite in `tests/test_metadata.py` covering version synchronization, badge integrity, `llms.txt` format, and UTF-8 encoding.
- Added comprehensive sibling tools and ecosystem navigation matrix (`dev-bricks`, `ellmos-ai`, `open-bricks`) across both `README.md` and `README_de.md`.
- Added `[tool.ruff]` and `[tool.ruff.lint]` configuration to `pyproject.toml`.

### Changed
- Synchronized Pytest test badges in `README.md` and `README_de.md` from 16 to 21 passed tests (100% green).
- Updated `llms.txt` AI/LLM context index timestamp to `2026-08-16` with 21 unit & metadata tests verified.

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
