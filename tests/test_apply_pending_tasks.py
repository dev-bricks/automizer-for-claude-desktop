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


def load_queue_module():
    spec = importlib.util.spec_from_file_location(
        "queue_request_under_test", TOOLS_DIR / "queue_request.py"
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


class FailClosedValidationTests(unittest.TestCase):
    def test_keeps_wish_for_task_of_other_host(self):
        """Ein set-Wunsch fuer eine hier unbekannte Aufgabe darf NICHT verworfen werden.

        pending-tasks.json wird ueber OneDrive von allen Hosts geteilt, die Registry liegt
        hostlokal. Ohne diesen Schutz loescht der erste Lauf auf dem falschen Host die
        Wuensche des anderen (belegt am 2026-08-01: 4 ASUS-Wuensche auf WORKSTATION-LG).
        """
        merger = load_merger_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"
            registry = {"scheduledTasks": [{"id": "local-task", "cronExpression": "0 9 * * *"}]}
            fremd = {
                "op": "set",
                "taskId": "task-of-other-host",
                "fields": {"cronExpression": "0 8 * * *"},
                "requestedBy": "regression-test",
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps({"pending": [fremd]}), encoding="utf-8")

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
            self.assertIn("UEBERGANGEN", stdout.getvalue())
            # Registry unberuehrt
            self.assertEqual(
                json.loads(registry_path.read_text(encoding="utf-8")), registry
            )
            # und der Wunsch steht noch da - das ist der Kern dieses Tests
            self.assertEqual(
                json.loads(pending_path.read_text(encoding="utf-8")), {"pending": [fremd]}
            )

    def test_rejects_non_dict_pending_root_fail_closed(self):
        merger = load_merger_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"

            registry = {"scheduledTasks": [{"id": "t1", "cronExpression": "* * * * *"}]}
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--registry", str(registry_path),
                    "--care-dir", str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 1)
            self.assertIn("FEHLER", stdout.getvalue())
            self.assertEqual(json.loads(registry_path.read_text(encoding="utf-8")), registry)

    def test_rejects_malformed_item_types_without_crashing(self):
        merger = load_merger_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"

            registry = {"scheduledTasks": [{"id": "t1", "cronExpression": "* * * * *"}]}
            pending_data = {
                "pending": [
                    "invalid-string-item",
                    {"op": "set", "taskId": 12345, "fields": {"enabled": False}},
                    {"op": "set", "taskId": "t1", "fields": "not-a-dict"},
                ]
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps(pending_data), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--registry", str(registry_path),
                    "--care-dir", str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("ABGELEHNT", output)
            self.assertEqual(json.loads(registry_path.read_text(encoding="utf-8")), registry)

    def test_queue_request_rejects_malformed_pending_json(self):
        queue = load_queue_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps(["invalid", "array"]), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "queue_request.py",
                    "set",
                    "t1",
                    "--cron", "0 12 * * *",
                    "--care-dir", str(care_dir),
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = queue.main()

            self.assertEqual(exit_code, 1)
            self.assertIn("FEHLER", stdout.getvalue())


class RollbackCommandTests(unittest.TestCase):
    def test_rollback_reverts_set_operation(self):
        merger = load_merger_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            applied_path = care_dir / "pending" / "applied-tasks.json"

            registry = {"scheduledTasks": [{"id": "t1", "cronExpression": "0 20 * * *", "enabled": True}]}
            applied_data = {
                "applied": [
                    {
                        "op": "set",
                        "taskId": "t1",
                        "fields": {"cronExpression": "0 20 * * *"},
                        "previousValues": {"cronExpression": "0 8 * * *"},
                        "requestedBy": "test-user",
                    }
                ]
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            applied_path.parent.mkdir(parents=True)
            applied_path.write_text(json.dumps(applied_data), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--rollback", "t1",
                    "--registry", str(registry_path),
                    "--care-dir", str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 0)
            self.assertIn("ROLLBACK ANGEWANDT", stdout.getvalue())
            updated_reg = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_reg["scheduledTasks"][0]["cronExpression"], "0 8 * * *")

    def test_rollback_rejects_create_operation(self):
        merger = load_merger_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            applied_path = care_dir / "pending" / "applied-tasks.json"

            registry = {"scheduledTasks": [{"id": "created-task", "cronExpression": "0 12 * * *"}]}
            applied_data = {
                "applied": [
                    {
                        "op": "create",
                        "taskId": "created-task",
                        "fields": {"cronExpression": "0 12 * * *"},
                        "previousValues": None,
                    }
                ]
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            applied_path.parent.mkdir(parents=True)
            applied_path.write_text(json.dumps(applied_data), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--rollback", "created-task",
                    "--registry", str(registry_path),
                    "--care-dir", str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 1)
            self.assertIn("Loeschen bleibt dem Menschen in der App vorbehalten", stdout.getvalue())


class PersistentReportTests(unittest.TestCase):
    def test_dry_run_report_is_written(self):
        merger = load_merger_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            registry_path = temporary_root / "scheduled-tasks.json"
            care_dir = temporary_root / "Scheduled" / "_care"
            pending_path = care_dir / "pending" / "pending-tasks.json"
            report_path = care_dir / "reports" / "dry-run-report.md"

            registry = {"scheduledTasks": [{"id": "t1", "cronExpression": "0 8 * * *"}]}
            pending_data = {
                "pending": [
                    {"op": "set", "taskId": "t1", "fields": {"cronExpression": "0 20 * * *"}, "requestedBy": "user1"}
                ]
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            pending_path.parent.mkdir(parents=True)
            pending_path.write_text(json.dumps(pending_data), encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "apply_pending_tasks.py",
                    "--dry-run",
                    "--report", str(report_path),
                    "--registry", str(registry_path),
                    "--care-dir", str(care_dir),
                    "--ignore-app-state",
                ],
            ), contextlib.redirect_stdout(stdout):
                exit_code = merger.main()

            self.assertEqual(exit_code, 0)
            self.assertTrue(report_path.exists())
            report_content = report_path.read_text(encoding="utf-8")
            self.assertIn("# Merger Dry-Run-Bericht", report_content)
            self.assertIn("DRY-RUN set t1", report_content)


if __name__ == "__main__":
    unittest.main()
