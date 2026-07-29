# -*- coding: utf-8 -*-
"""test_automizer.py - Unit tests for automizer-for-claude-desktop."""

import os
import json
import tempfile
import pytest

import claude_desktop_paths as pfade


def test_platform_check():
    """Verify platform detection helper functions return booleans."""
    win = pfade.ist_windows()
    mac = pfade.ist_macos()
    assert isinstance(win, bool)
    assert isinstance(mac, bool)


def test_directory_helpers():
    """Verify directory construction with custom base paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sched = pfade.scheduled_verzeichnis(basis=tmpdir)
        care = pfade.care_verzeichnis(basis=tmpdir)

        assert sched == os.path.join(tmpdir, "Claude", "Scheduled")
        assert care == os.path.join(tmpdir, "Claude", "Scheduled", "_care")


def test_queue_request_data_structure():
    """Test generating and serializing pending task request structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        care_dir = os.path.join(tmpdir, "_care")
        pending_dir = os.path.join(care_dir, "pending")
        os.makedirs(pending_dir, exist_ok=True)

        pending_file = os.path.join(pending_dir, "pending-tasks.json")

        req = {
            "op": "set",
            "taskId": "test-task",
            "fields": {
                "cronExpression": "0 8 * * *",
                "enabled": True
            },
            "reason": "unit-test",
            "requestedBy": "pytest-suite",
            "requestedAt": "2026-07-29T02:00:00"
        }

        data = {"pending": [req]}
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        assert os.path.exists(pending_file)
        with open(pending_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert len(loaded["pending"]) == 1
        assert loaded["pending"][0]["taskId"] == "test-task"
        assert loaded["pending"][0]["fields"]["cronExpression"] == "0 8 * * *"


def test_registry_file_structure():
    """Test parsing and valid structure of scheduled-tasks.json format."""
    mock_registry = {
        "version": 1,
        "scheduledTasks": [
            {
                "id": "daily-report",
                "name": "Daily Report",
                "description": "Generate summary",
                "cronExpression": "0 9 * * *",
                "enabled": True,
                "model": "claude-3-5-sonnet",
                "permissionMode": "auto"
            }
        ]
    }

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as tmp:
        json.dump(mock_registry, tmp)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            read_back = json.load(f)

        assert "scheduledTasks" in read_back
        tasks = read_back["scheduledTasks"]
        assert len(tasks) == 1
        assert tasks[0]["id"] == "daily-report"
        assert tasks[0]["cronExpression"] == "0 9 * * *"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
