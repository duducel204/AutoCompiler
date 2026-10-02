import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import detect_native_scheduler, discover


class CapabilityDiscoveryTests(unittest.TestCase):
    def test_discovery_has_stable_shape(self):
        result = discover()
        self.assertEqual(result["schema_version"], "0.2-experimental")
        self.assertEqual(result["experiment"], "E-003")
        self.assertEqual(result["summary"]["checked"], len(result["capabilities"]))
        self.assertTrue(any(c["id"] == "filesystem" and c["detected"] for c in result["capabilities"]))
        self.assertTrue(any(c["id"] == "sqlite" and c["detected"] for c in result["capabilities"]))

    def test_capability_lifecycle_is_explicit(self):
        result = discover()
        for capability in result["capabilities"]:
            self.assertIn("detected", capability)
            self.assertIn("installed", capability)
            self.assertIn("accessible", capability)
            self.assertIn("authorized", capability)
            self.assertIn("usable", capability)

    def test_detection_does_not_imply_authorization(self):
        result = discover()
        filesystem = next(c for c in result["capabilities"] if c["id"] == "filesystem")
        self.assertTrue(filesystem["detected"])
        self.assertEqual(filesystem["authorized"], "unknown")

    @patch("autocompiler.discover.platform.system", return_value="Windows")
    @patch("autocompiler.discover.shutil.which")
    @patch("autocompiler.discover.subprocess.run")
    def test_windows_scheduler_requires_read_only_probe_before_usable(self, run, which, system):
        which.return_value = r"C:\Windows\System32\schtasks.exe"
        run.return_value = Mock(returncode=0)
        scheduler = detect_native_scheduler()
        self.assertTrue(scheduler.detected)
        self.assertEqual(scheduler.accessible, "yes")
        self.assertEqual(scheduler.authorized, "unknown")
        self.assertEqual(scheduler.usable, "yes")
        run.assert_called_once()

    @patch("autocompiler.discover.platform.system", return_value="Windows")
    @patch("autocompiler.discover.shutil.which")
    @patch("autocompiler.discover.subprocess.run")
    def test_windows_scheduler_probe_failure_does_not_claim_usable(self, run, which, system):
        which.return_value = r"C:\Windows\System32\schtasks.exe"
        run.return_value = Mock(returncode=1)
        scheduler = detect_native_scheduler()
        self.assertTrue(scheduler.detected)
        self.assertEqual(scheduler.usable, "no")


if __name__ == "__main__":
    unittest.main()
