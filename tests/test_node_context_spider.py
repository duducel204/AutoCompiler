from __future__ import annotations

import json
import subprocess
import sys
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
            timeout=30,
        )
        payload = json.loads(result.stdout)
        return result.returncode, payload, result.stderr

    def test_spider_starts_from_exact_node_and_respects_limits(self):
        code, payload, stderr = self._run(
            "src/autocompiler/ay/state.py",
            "--depth", "2",
            "--max-nodes", "12",
            "--max-edges", "20",
            "--seed-limit", "3",
        )
        self.assertEqual(code, 0, msg=stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["seeds"], ["src/autocompiler/ay/state.py"])
        self.assertLessEqual(len(payload["nodes"]), 12)
        self.assertLessEqual(len(payload["edges"]), 20)
        self.assertTrue(any(node["seed"] for node in payload["nodes"]))
        self.assertTrue(all(node["hop"] <= 2 for node in payload["nodes"]))

    def test_spider_returns_empty_context_for_unknown_node(self):
        code, payload, stderr = self._run(
            "definitely-not-a-repository-node-xyz",
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
