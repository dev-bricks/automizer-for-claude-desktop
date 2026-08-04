# Changelog

All notable changes to `dev-bricks/automizer-for-claude-desktop` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `llms.txt` for machine-readable context and LLM agent integration.
- Added PEP 621 `pyproject.toml` configuration for Pytest test runner and module packaging.
- Added comprehensive Pytest suite `tests/test_automizer.py` for path resolution, queueing, and merger validation.
- Added `README_de.md` for German documentation parity.

### Changed
- Fixed unused `pytest` import in `tests/test_automizer.py` (`ruff check` 100% clean).
- Synchronized Pytest test badges in `README.md` & `README_de.md` (12/12 passed).
- Updated `llms.txt` verification timestamp to `2026-08-04`.
- Standardized `README.md` with Shields.io badges, GFM alert callout boxes, and Mermaid architecture diagram.
- Updated documentation and verification timestamps (`2026-08-01`).
- Aligned `README_de.md` layout, added missing banner graphic, and fixed section header typography.
- Verified 12/12 Pytest unit tests, ruff check & git status cleanliness.

## [1.0.0] - 2026-07-20
- Initial import and public repository setup.
