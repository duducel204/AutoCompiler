import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.workflow_installations import WorkflowInstallationRegistry


class WorkflowInstallationRegistryTests(unittest.TestCase):
    def test_manual_installation_persists_runs_and_removes_owned_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            generated = root / "generated"
            artifact = generated / "manual-proof"
            artifact.mkdir(parents=True)
            (artifact / "automation.py").write_text(
                "import json\n"
                "from datetime import datetime, timezone\n"
                "from pathlib import Path\n"
                "root=Path(__file__).resolve().parent\n"
                "event={'ts':datetime.now(timezone.utc).isoformat(),'status':'ok','processed':1}\n"
                "with (root/'run-history.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\\n')\n"
                "print(json.dumps({'ok':True,'processed':1}))\n",
                encoding="utf-8",
            )
            (artifact / "manifest.json").write_text("{}", encoding="utf-8")

            registry = WorkflowInstallationRegistry(root / "state" / "installations.json", generated)
            record = registry.record(
                plan_id="plan-1",
                ir={"name": "Manual Proof", "trigger": {"type": "manual"}},
                plan={"out_dir": str(artifact), "target": "python-sqlite"},
                result={"status": "verified", "deployment": {"ok": True, "status": "not_required"}},
            )
            self.assertEqual(record["status"], "ready")
            self.assertTrue(record["artifact_exists"])

            run = registry.run(record["installation_id"])
            self.assertTrue(run["ok"])
            history = registry.history(record["installation_id"])
            self.assertEqual(history["count"], 1)
            self.assertEqual(history["events"][0]["processed"], 1)

            disabled = registry.disable(record["installation_id"])
            self.assertTrue(disabled["ok"])
            self.assertEqual(disabled["installation"]["status"], "disabled")
            blocked = registry.run(record["installation_id"])
            self.assertEqual(blocked["status"], "installation_disabled")

            enabled = registry.enable(record["installation_id"])
            self.assertTrue(enabled["ok"])
            self.assertEqual(enabled["installation"]["status"], "ready")

            removed = registry.remove(record["installation_id"])
            self.assertTrue(removed["ok"])
            self.assertFalse(artifact.exists())
            self.assertEqual(registry.list(), [])

    @patch("autocompiler.workflow_installations.run_windows_schedule")
    @patch("autocompiler.workflow_installations.remove_windows_schedule")
    @patch("autocompiler.workflow_installations.enable_windows_schedule")
    @patch("autocompiler.workflow_installations.disable_windows_schedule")
    def test_scheduled_installation_controls_real_deployment_adapter(self, disable, enable, remove, run):
        disable.return_value = {"ok": True, "status": "disabled", "task_name": "AutoCompiler-Proof"}
        enable.return_value = {"ok": True, "status": "enabled", "task_name": "AutoCompiler-Proof"}
        remove.return_value = {"ok": True, "status": "removed", "task_name": "AutoCompiler-Proof"}
        run.return_value = {"ok": True, "status": "triggered", "task_name": "AutoCompiler-Proof"}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            generated = root / "generated"
            artifact = generated / "scheduled-proof"
            artifact.mkdir(parents=True)
            (artifact / "automation.py").write_text("print('{}')", encoding="utf-8")
            (artifact / "manifest.json").write_text("{}", encoding="utf-8")
            registry = WorkflowInstallationRegistry(root / "installations.json", generated)

            record = registry.record(
                plan_id="plan-2",
                ir={"name": "Scheduled Proof", "trigger": {"type": "schedule", "cron": "0 9 * * *"}},
                plan={"out_dir": str(artifact), "target": "python-sqlite"},
                result={
                    "status": "verified",
                    "deployment": {
                        "ok": True,
                        "status": "installed_verified",
                        "task_name": "AutoCompiler-Proof",
                        "provider": "windows-task-scheduler",
                    },
                },
            )
            iid = record["installation_id"]
            self.assertEqual(record["status"], "active")
            self.assertTrue(registry.run(iid)["ok"])
            self.assertTrue(registry.disable(iid)["ok"])
            self.assertEqual(registry.get(iid)["status"], "disabled")
            self.assertTrue(registry.enable(iid)["ok"])
            self.assertEqual(registry.get(iid)["status"], "active")
            self.assertTrue(registry.remove(iid)["ok"])
            run.assert_called_once_with("AutoCompiler-Proof")
            disable.assert_called_once_with("AutoCompiler-Proof")
            enable.assert_called_once_with("AutoCompiler-Proof")
            remove.assert_called_once_with("AutoCompiler-Proof")

    def test_registry_rejects_artifacts_outside_generated_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            generated = root / "generated"
            generated.mkdir()
            outside = root / "outside"
            outside.mkdir()
            registry = WorkflowInstallationRegistry(root / "installations.json", generated)
            with self.assertRaises(ValueError):
                registry.record(
                    plan_id="plan-x",
                    ir={"name": "Escape", "trigger": {"type": "manual"}},
                    plan={"out_dir": str(outside), "target": "python-sqlite"},
                    result={"status": "verified", "deployment": {}},
                )


if __name__ == "__main__":
    unittest.main()
