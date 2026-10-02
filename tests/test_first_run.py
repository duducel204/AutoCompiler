import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.first_run import MachinePreparationStore, build_machine_preflight
from autocompiler.windows_provisioner import plan_windows_preparation


def windows_inventory(schedule_usable: bool = True):
    return {
        "machine": {
            "os": "Windows",
            "release": "10",
            "architecture": "AMD64",
        },
        "summary": {"detected": 1, "checked": 1},
        "capabilities": [
            {
                "id": "native_scheduler",
                "detected": True,
                "installed": "yes",
                "accessible": "yes",
                "authorized": "unknown",
                "usable": "yes" if schedule_usable else "no",
                "path": r"C:\Windows\System32\schtasks.exe",
            }
        ],
    }


class FirstRunTests(unittest.TestCase):
    def test_verified_windows_baseline_releases_canvas(self):
        preflight, plan = build_machine_preflight(inventory=windows_inventory(True))
        self.assertTrue(preflight["supported_platform"])
        self.assertTrue(preflight["automation_ready"])
        self.assertEqual(preflight["phase"], "ready")
        self.assertEqual(preflight["readiness_summary"]["missing"], 0)
        self.assertIsNotNone(plan)
        self.assertTrue(plan.automation_ready_before)

    def test_unverified_required_gap_blocks_without_validated_recipe(self):
        preflight, plan = build_machine_preflight(inventory=windows_inventory(False))
        self.assertFalse(preflight["automation_ready"])
        self.assertEqual(preflight["phase"], "blocked")
        self.assertIn("schedule", preflight["missing_required"])
        self.assertFalse(preflight["preparation"]["can_apply"])
        self.assertIn("schedule", preflight["preparation"]["unresolved_capabilities"])
        self.assertIsNotNone(plan)

    def test_complete_recipe_plan_can_be_authorized_once(self):
        recipes = {
            "schedule": {
                "provider": "verified-scheduler",
                "source": "provider.bin",
                "target_path": "environment/provider.bin",
                "sha256": "abc",
                "version": "1.0.0",
            }
        }
        plan = plan_windows_preparation(
            inventory=windows_inventory(False),
            acquisition_recipes=recipes,
        )
        self.assertTrue(plan.can_apply)
        store = MachinePreparationStore()
        created = store.create(plan)
        plan_id = created["plan_id"]
        authorized = store.authorize(plan_id)
        self.assertIsNotNone(authorized)
        self.assertTrue(authorized["authorized"])
        store.mark_applied(plan_id)
        self.assertIsNone(store.authorize(plan_id))

    def test_non_windows_fails_closed_for_windows_mvp(self):
        inventory = {
            "machine": {"os": "Linux", "release": "test", "architecture": "x86_64"},
            "summary": {"detected": 0, "checked": 0},
            "capabilities": [],
        }
        preflight, plan = build_machine_preflight(inventory=inventory)
        self.assertFalse(preflight["supported_platform"])
        self.assertFalse(preflight["automation_ready"])
        self.assertEqual(preflight["phase"], "blocked")
        self.assertIsNone(plan)


if __name__ == "__main__":
    unittest.main()
