from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NodeContextIndexTests(unittest.TestCase):
    def _run(self, output: Path) -> dict:
        result = subprocess.run(
            [sys.executable, "scripts/node_context_index.py", "--output", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_second_cycle_reuses_unchanged_file_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "node_context_graph.json"
            first = self._run(output)
            second = self._run(output)

            self.assertTrue(first["ok"])
            self.assertGreater(first["total_files"], 0)
            self.assertGreater(first["total_nodes"], 0)
            self.assertEqual(second["changed_files"], [])
            self.assertEqual(second["removed_files"], [])
            self.assertEqual(second["unchanged_files"], second["total_files"])

            graph = json.loads(output.read_text(encoding="utf-8"))
            kinds = {
                node["kind"]
                for record in graph["files"].values()
                for node in record["nodes"]
            }
            self.assertIn("file", kinds)
            self.assertIn("symbol", kinds)
            self.assertIn("semantic", kinds)
            self.assertIn("logic", kinds)


if __name__ == "__main__":
    unittest.main()
