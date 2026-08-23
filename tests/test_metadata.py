# -*- coding: utf-8 -*-
"""test_metadata.py - Metadata, badge, and documentation parity tests for automizer-for-claude-desktop."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_version_consistency():
    """Verify version parity across pyproject.toml, README.md, README_de.md, and CHANGELOG.md."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    assert version_match, "Version not found in pyproject.toml"
    version = version_match.group(1)

    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"Version: {version}" in readme_en or f"version-{version}" in readme_en

    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")
    assert f"Version: {version}" in readme_de or f"version-{version}" in readme_de

    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{version}]" in changelog


def test_badge_parity_and_status():
    """Verify README.md and README_de.md contain matching status badges and links."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    for keyword in [
        "actions/workflows/ci.yml",
        "python-3.8",
        "License-MIT",
        "Ecosystem-dev--bricks",
        "Umbrella-open--bricks",
        "Security-Local--First",
        "LLM%20Context-llms.txt",
    ]:
        assert keyword in readme_en, f"Badge keyword '{keyword}' missing in README.md"
        assert keyword in readme_de, f"Badge keyword '{keyword}' missing in README_de.md"


def test_mermaid_diagrams_syntax():
    """Verify README.md and README_de.md contain both flowchart and sequenceDiagram Mermaid definitions."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    for doc, name in [(readme_en, "README.md"), (readme_de, "README_de.md")]:
        assert "```mermaid\nflowchart TD" in doc, f"Flowchart diagram missing in {name}"
        assert "```mermaid\nsequenceDiagram" in doc, f"Sequence diagram missing in {name}"
        assert "queue_request.py" in doc
        assert "apply_pending_tasks.py" in doc
        assert "scheduled-tasks.json" in doc


def test_sibling_ecosystem_and_urls():
    """Verify sibling ecosystem tools and umbrella URLs are documented in both READMEs."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    sibling_repos = [
        "safe-start-for-codex",
        "companion-for-agy",
        "DevCenter",
        "CodeBox",
        "automation-master",
        "MethodenAnalyser",
        "coma",
        "workflowhooker",
        "memoryhooker",
    ]

    for repo in sibling_repos:
        assert repo in readme_en, f"Sibling repo '{repo}' missing in README.md"
        assert repo in readme_de, f"Sibling repo '{repo}' missing in README_de.md"


def test_llms_txt_integrity():
    """Verify llms.txt exists, contains required context, and has up-to-date timestamp."""
    llms_path = REPO_ROOT / "llms.txt"
    assert llms_path.is_file()
    content = llms_path.read_text(encoding="utf-8")

    assert "Last checked: 2026-08-23" in content
    assert "https://github.com/dev-bricks/automizer-for-claude-desktop" in content
    assert "tools/claude_desktop_paths.py" in content
    assert "tools/queue_request.py" in content
    assert "tools/apply_pending_tasks.py" in content
    assert "tools/install_merger_task.ps1" in content
    assert "tools/run_apply_pending_hidden.vbs" in content


def test_ci_workflow_integrity():
    """Verify GitHub Actions CI workflow exists, is valid YAML, and tests all target Python versions."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), "CI workflow .github/workflows/ci.yml not found"
    content = ci_path.read_text(encoding="utf-8")

    for py_ver in ["3.10", "3.11", "3.12", "3.13"]:
        assert py_ver in content, f"Python version {py_ver} missing in CI matrix"

    assert "actions/checkout@" in content
    assert "actions/setup-python@" in content
    assert "ruff check" in content
    assert "pytest" in content


def test_pyproject_metadata():
    """Verify pyproject.toml contains standard project URLs, keywords, and PEP 621 classifiers."""
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "Programming Language :: Python :: 3.13" in pyproject_text
    assert "Operating System :: Microsoft :: Windows" in pyproject_text
    assert "[project.urls]" in pyproject_text
    assert "Repository =" in pyproject_text
    assert "Issues =" in pyproject_text
    assert "Documentation =" in pyproject_text
    assert "Changelog =" in pyproject_text
    assert "Security =" in pyproject_text
    assert "Umbrella =" in pyproject_text
    assert "keywords =" in pyproject_text


def test_security_policy_and_offline_invariants():
    """Verify SECURITY.md contains security contacts, advisory links, supported versions, and zero-egress principles."""
    sec_path = REPO_ROOT / "SECURITY.md"
    assert sec_path.is_file()
    content = sec_path.read_text(encoding="utf-8")

    assert "security@ellmos.ai" in content
    assert "lukas@open-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "github.com/dev-bricks/automizer-for-claude-desktop/security/advisories" in content
    assert "Supported Versions" in content or "Unterstützte Versionen" in content
    assert "Zero External Network Connections" in content
    assert "Path-Based Process Discrimination" in content
    assert "Atomic Writes & Automated Backups" in content
    assert "Cross-Host Isolation" in content


def test_utf8_encoding_cleanliness():
    """Verify all text files in repository are valid UTF-8 without double-encoded mojibake or replacement chars."""
    # Bad double-encoded byte patterns (UTF-8 bytes wrongly interpreted as Windows-1252/Latin-1)
    mojibake_sequences = ["\xc3\xa4", "\xc3\xb6", "\xc3\xbc", "\xc3\x9f", "\xe2\x80\x93", "\xe2\x80\x94"]
    for pattern in ["*.md", "*.toml", "tools/*.py", "tests/*.py", "llms.txt"]:
        for file_path in REPO_ROOT.glob(pattern):
            if file_path.is_file() and file_path.name != "test_metadata.py":
                raw = file_path.read_bytes()
                # Ensure valid UTF-8 decoding
                decoded = raw.decode("utf-8")
                assert "\ufffd" not in decoded, f"Unicode replacement character found in {file_path.name}"
                for seq in mojibake_sequences:
                    assert seq not in decoded, f"Double-encoded sequence found in {file_path.name}"
