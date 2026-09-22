import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover


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


if __name__ == "__main__":
    unittest.main()
