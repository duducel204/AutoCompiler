import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.local_canvas import snapshot


class LocalCanvasTests(unittest.TestCase):
    def test_snapshot_reads_real_catalog_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            catalog = CapabilityCatalog(path)
            catalog.register_candidate(
                "demo.capability", "demo-provider", "1.0.0",
                ("tests.demo",), rollback="remove provider"
            )
            state = snapshot(path)
            self.assertEqual(len(state["catalog"]), 1)
            self.assertEqual(len(state["candidates"]), 1)
            self.assertEqual(state["candidates"][0]["capability"], "demo.capability")
            self.assertEqual(state["validated"], [])


if __name__ == "__main__":
    unittest.main()
