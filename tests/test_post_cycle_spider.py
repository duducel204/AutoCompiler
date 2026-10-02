from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostCycleSpiderTests(unittest.TestCase):
    def _run(self, graph: Path, report: Path, sha: str) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/post_cycle_spider.py",
                "--graph",
                str(graph),
                "--report",
                str(report),
                "--cycle-sha",
                sha,
                "--depth",
                "1",
                "--max-changed-files",
                "3",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=90,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_completed_cycle_builds_context_then_reuses_unchanged_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph = root / "node_context_graph.json"
            first_report = root / "cycle-1.json"
            second_report = root / "cycle-2.json"

            first = self._run(graph, first_report, "cycle-one")
            self.assertTrue(first["ok"])
            self.assertGreater(first["changed_files"], 0)
            self.assertTrue(first_report.is_file())

            payload = json.loads(first_report.read_text(encoding="utf-8"))
            self.assertEqual(payload["cycle"]["sha"], "cycle-one")
            self.assertLessEqual(len(payload["spider"]["files_read_from_delta"]), 3)
            self.assertIn("nodes", payload["spider"])
            self.assertIn("edges", payload["spider"])
            self.assertIn("semantic_labels", payload["spider"])
            self.assertIn("logic_nodes", payload["spider"])
            self.assertEqual(payload["index"]["cache_state"], "missing")
            self.assertEqual(len(payload["index"]["contract_fingerprint"]), 64)

            second = self._run(graph, second_report, "cycle-two")
            self.assertTrue(second["ok"])
            self.assertEqual(second["changed_files"], 0)
            self.assertEqual(second["context_nodes"], 0)
            self.assertEqual(second["context_edges"], 0)
            self.assertEqual(second["cache_state"], "reused")
            self.assertEqual(len(second["contract_fingerprint"]), 64)

            payload2 = json.loads(second_report.read_text(encoding="utf-8"))
            self.assertEqual(payload2["cycle"]["changed_files"], [])
            self.assertGreater(payload2["cycle"]["unchanged_files"], 0)


if __name__ == "__main__":
    unittest.main()
