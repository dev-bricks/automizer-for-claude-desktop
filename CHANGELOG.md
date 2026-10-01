# Changelog

All notable changes to `dev-bricks/automizer-for-claude-desktop` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 18-Point bilingual quick navigation architecture across `README.md` and `README_de.md` with symmetrical dual reciprocal HTML anchors (`<a id="sec-01"></a>` to `<a id="sec-18"></a>`).
- Target Personas and high-intent SEO query architecture in Section 06 across four technical operator profiles (`[PERSONA-01]` to `[PERSONA-04]`).
- 10-Dimensional comparative matrix in Section 07 contrasting Automizer against native Claude in-app UI, direct JSON file edits, Windows Task Scheduler, and daemon loops mapped to invariants `INV-LOCAL-01` through `INV-SLA-10`.
- Canonical open-source `NOTICE` attribution file in repository root recognizing Lukas Geiger, `dev-bricks`, and `open-bricks`.
- Level 1 SBOM plain-text companion `THIRD_PARTY_LICENSES.txt` with complete invariant verification matrix and permissive license inventory.
- Statutory disclaimer according to German gratuitous service law (§ 521 BGB Gefälligkeitsrecht) and 48-hour security response SLA in Section 18 of both READMEs.
- Local marketing, SEO, and discoverability governance register `MARKETING-LOG.txt`.
- Expanded automated contract test suite in `tests/test_metadata.py` from 27 to 34 tests covering 18-point navigation anchors, personas, matrix, § 521 BGB notice, NOTICE file, and SBOM companion.

### Changed
- Saturated GitHub repository topics via `gh repo edit` to platform maximum of 20/20 topics.
- Aligned `keywords` in `pyproject.toml` to 20 saturated remote topics and expanded `project.urls` with `Notice`, `Third-Party Licenses`, `Level 1 SBOM`, `LLM Ready`, and `Marketing Log`.
- Hardened `license-files` in `pyproject.toml` to declare `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`, and `THIRD_PARTY_LICENSES.txt`.
- Synchronized test badges to 34 passed tests (100% green) across documentation and updated `llms.txt` timestamp to `2026-10-01`.

## [1.0.4] - 2026-09-21

### Added
- Standardized `TODO.md` with structured `## STATUS` verification table (8 functional categories) and formalized open task tracking (`TASK-ACD-01` .. `TASK-ACD-04`).
- Comprehensive Software Bill of Materials (SBOM) and PEP 639 license inventory in `THIRD_PARTY_LICENSES.md`, formally verifying the Zero External Runtime Dependencies invariant (`INV-ACD-02`).
- Contract tests in `tests/test_metadata.py` verifying license inventory integrity, `.gitignore` mandatory entries, and release gate readiness (27 passing tests, 100% green).
- Canonical module manifest `ellmos-module.v2.json` in repository root for catalog integration and Plan-D parity.

### Changed
- Hardened `.gitignore` to satisfy automated release gate requirements (`*.pyc`, `.env`, `*.db`, `.idea/`, `.vscode/`, `data/`), added credential/secret defense patterns, and removed `TODO.md` from ignore list.
- Declared PEP 639 `license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]` in `pyproject.toml`.
- Synchronized version to `1.0.4` and test badges to 27 tests across `README.md`, `README_de.md`, and `llms.txt`.
- Successfully verified all 10 automated release gates via `final_gate_check.py` (10 PASS, 0 FAIL, 0 WARN).

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
