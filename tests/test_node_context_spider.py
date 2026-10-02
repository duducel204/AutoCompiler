from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NodeContextSpiderTests(unittest.TestCase):
    def _run(self, *args: str) -> tuple[int, dict, str]:
        result = subprocess.run(
            [sys.executable, "scripts/node_context_spider.py", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
        payload = json.loads(result.stdout)
        return result.returncode, payload, result.stderr

    def test_spider_uses_derived_nodes_and_respects_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "node_context_graph.json"
            code, payload, stderr = self._run(
                "state.py",
                "--graph", str(graph),
                "--refresh",
                "--depth", "2",
                "--max-nodes", "12",
                "--max-edges", "20",
                "--seed-limit", "3",
            )
        self.assertEqual(code, 0, msg=stderr)
        self.assertTrue(payload["ok"])
        self.assertLessEqual(len(payload["nodes"]), 12)
        self.assertLessEqual(len(payload["edges"]), 20)
        self.assertTrue(payload["seeds"])
        self.assertTrue(any(node["seed"] for node in payload["nodes"]))
        self.assertTrue(all(node["hop"] <= 2 for node in payload["nodes"]))
        self.assertTrue(any("state.py" in source for source in payload["sources"]))

    def test_spider_can_start_from_semantic_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "node_context_graph.json"
            code, payload, stderr = self._run(
                "schedule",
                "--graph", str(graph),
                "--refresh",
                "--depth", "1",
            )
        self.assertEqual(code, 0, msg=stderr)
        self.assertTrue(payload["ok"])
        self.assertTrue(
            any("semantic:capability:schedule" == seed for seed in payload["seeds"]),
            msg=payload,
        )

    def test_spider_returns_empty_context_for_unknown_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "node_context_graph.json"
            code, payload, stderr = self._run(
                "definitely-not-a-repository-node-xyz",
                "--graph", str(graph),
                "--refresh",
                "--depth", "1",
            )
        self.assertEqual(code, 0, msg=stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["seeds"], [])
        self.assertEqual(payload["nodes"], [])
        self.assertEqual(payload["edges"], [])

    def test_spider_rejects_negative_depth(self):
        code, payload, _ = self._run("state.py", "--depth", "-1")
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertIn("depth", payload["error"])


if __name__ == "__main__":
    unittest.main()
