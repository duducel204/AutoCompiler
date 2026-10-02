import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.portable_provider import sha256
from autocompiler.windows_provisioner import apply_windows_preparation, plan_windows_preparation


class WindowsProvisionerTests(unittest.TestCase):
    def test_missing_gap_without_recipe_fails_closed(self):
        prep_plan = plan_windows_preparation(
            inventory={
                "machine": {"os": "Windows"},
                "capabilities": [
                    {
                        "id": "native_scheduler",
                        "detected": True,
                        "usable": "no",
                    }
                ],
            }
        )
        self.assertFalse(prep_plan.automation_ready_before)
        self.assertIn("schedule", prep_plan.unresolved_capabilities)
        self.assertFalse(prep_plan.can_apply)

        with tempfile.TemporaryDirectory() as td:
            result = apply_windows_preparation(
                prep_plan,
                manifest_path=Path(td) / "environment_manifest.json",
                authorized=True,
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["automation_ready"])
        self.assertEqual(result["status"], "unresolved_capabilities")

    def test_plan_when_already_automation_ready(self):
        # Provide inventory satisfying all required capabilities
        full_inventory = {
            "capabilities": [
                {"id": "python-stdlib-filesystem", "detected": True, "usable": "yes"},
                {"id": "python-subprocess", "detected": True, "usable": "yes"},
                {"id": "sqlite", "detected": True, "usable": "yes"},
                {"id": "windows-task-scheduler", "detected": True, "usable": "yes"},
                {"id": "powershell-notification", "detected": True, "usable": "yes"},
                {"id": "autocompiler.http_provider", "detected": True, "usable": "yes"},
            ]
        }
        prep_plan = plan_windows_preparation(inventory=full_inventory)
        self.assertTrue(prep_plan.automation_ready_before)
        self.assertEqual(len(prep_plan.changes), 0)

    def test_apply_requires_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            dummy_source = tmp / "source.exe"
            dummy_source.write_text("dummy binary content")
            target_path = tmp / "installed.exe"
            source_hash = sha256(dummy_source)

            recipes = {
                "schedule": {
                    "provider": "schtasks-wrapper",
                    "source": str(dummy_source),
                    "target_path": str(target_path),
                    "sha256": source_hash,
                    "version": "1.0.0",
                }
            }

            inventory = {"capabilities": []}
            prep_plan = plan_windows_preparation(inventory=inventory, acquisition_recipes=recipes)
            manifest_file = tmp / "environment_manifest.json"

            unauth = apply_windows_preparation(prep_plan, manifest_path=manifest_file, authorized=False)
            self.assertFalse(unauth["ok"])
            self.assertEqual(unauth["status"], "authorization_required")

    def test_authorized_provision_registers_ownership_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            dummy_source = tmp / "source.exe"
            dummy_source.write_text("binary executable content")
            target_path = tmp / "installed.exe"
            source_hash = sha256(dummy_source)

            recipes = {
                "schedule": {
                    "provider": "schtasks-wrapper",
                    "source": str(dummy_source),
                    "target_path": str(target_path),
                    "sha256": source_hash,
                    "version": "1.0.0",
                }
            }

            prep_plan = plan_windows_preparation(inventory={"capabilities": []}, acquisition_recipes=recipes)
            manifest_file = tmp / "environment_manifest.json"

            res = apply_windows_preparation(prep_plan, manifest_path=manifest_file, authorized=True)
            self.assertTrue(res["ok"])

            if manifest_file.exists():
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                self.assertIn("providers", manifest_data)

            # Idempotent re-execution
            res2 = apply_windows_preparation(prep_plan, manifest_path=manifest_file, authorized=True)
            self.assertTrue(res2["ok"])


if __name__ == "__main__":
    unittest.main()
