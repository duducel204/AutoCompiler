import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.windows_base import WINDOWS_AUTOMATION_BASE_MANIFEST, inspect_windows_automation_base


class WindowsAutomationBaseTests(unittest.TestCase):
    def test_inspect_windows_automation_base_structure(self):
        result = inspect_windows_automation_base(inventory={"capabilities": []})
        self.assertIn("automation_ready", result)
        self.assertIn("statuses", result)
        self.assertIn("missing_required", result)
        self.assertEqual(result["target_os"], "windows")

    def test_inspect_returns_status_per_required_capability(self):
        inventory = {
            "capabilities": [
                {"id": "python", "detected": True, "usable": "yes"},
                {"id": "native_scheduler", "detected": True, "usable": "yes"},
                {"id": "powershell", "detected": True, "usable": "yes"},
            ]
        }
        result = inspect_windows_automation_base(inventory=inventory)
        required_caps = {r["capability"] for r in WINDOWS_AUTOMATION_BASE_MANIFEST["required_capabilities"]}
        inspected_caps = {s["capability"] for s in result["statuses"]}
        self.assertEqual(required_caps, inspected_caps)

        # Check formatting: capability -> provider -> usable or missing -> resolution plan
        for status in result["statuses"]:
            if status["status"] == "usable":
                self.assertTrue(status["provider"])
            else:
                self.assertTrue(status["resolution_plan"])

    def test_manifest_contains_provenance_metadata(self):
        provenance = WINDOWS_AUTOMATION_BASE_MANIFEST.get("provenance", {})
        self.assertIn("python", provenance)
        self.assertIn("sqlite", provenance)
        self.assertIn("powershell", provenance)
        self.assertIn("windows-task-scheduler", provenance)


if __name__ == "__main__":
    unittest.main()
