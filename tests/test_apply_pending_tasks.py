import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPOSITORY_ROOT / "tools"


def load_merger_module():
    spec = importlib.util.spec_from_file_location(
        "apply_pending_tasks_under_test", TOOLS_DIR / "apply_pending_tasks.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class PermissionModeValidationTests(unittest.TestCase):
    def test_set_rejects_unknown_permission_mode_without_changing_registry(self):
        merger = load_merger_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"
            registry = {
                "scheduledTasks": [
                    {"id": "example-task", "permissionMode": "auto"}
                ]
            }
            request = {
                "pending": [
                    {
                        "op": "set",
                        "taskId": "example-task",
                        "fields": {"permissionMode": "unsafe-mode"},
                        "requestedBy": "regression-test",
                    }
                ]
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps(request), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--registry",
                    str(registry_path),
                    "--care-dir",
                    str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 0)
            self.assertIn("permissionMode 'unsafe-mode' unbekannt", stdout.getvalue())
            self.assertEqual(
                json.loads(registry_path.read_text(encoding="utf-8")), registry
            )
            self.assertEqual(
                json.loads(pending_path.read_text(encoding="utf-8")), {"pending": []}
            )


if __name__ == "__main__":
    unittest.main()
