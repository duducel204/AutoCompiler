import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover


class CapabilityDiscoveryTests(unittest.TestCase):
    def test_discovery_has_stable_shape(self):
        result = discover()
        self.assertEqual(result["schema_version"], "0.1")
        self.assertEqual(result["experiment"], "E-003")
        self.assertEqual(result["summary"]["checked"], len(result["capabilities"]))
        self.assertTrue(any(c["id"] == "filesystem" and c["available"] for c in result["capabilities"]))
        self.assertTrue(any(c["id"] == "sqlite" and c["available"] for c in result["capabilities"]))


if __name__ == "__main__":
    unittest.main()
