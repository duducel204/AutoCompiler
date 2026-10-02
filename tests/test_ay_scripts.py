from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AYScriptsTests(unittest.TestCase):
    def _run(self, *args: str) -> dict:
        result = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_self_snapshot_emits_compact_structured_state(self):
        payload = self._run(
            "scripts/ay_self_snapshot.py",
            "--intent",
            "inspect current state",
        )
        self.assertEqual(payload["intent"], "inspect current state")
        self.assertIn("capabilities_available", payload)
        self.assertIn("constraints", payload)
        self.assertNotIn("api_key", json.dumps(payload).lower())

    def test_context_slice_returns_small_related_repo_subset(self):
        payload = self._run(
            "scripts/ay_context_slice.py",
            "trust_gate",
            "--limit",
            "5",
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["query"], "trust_gate")
        self.assertLessEqual(len(payload["seeds"]), 5)
        self.assertLessEqual(len(payload["paths"]), 15)
        self.assertLessEqual(len(payload["edges"]), 25)
        self.assertTrue(
            any("trust_gate" in path for path in payload["seeds"]),
            msg=payload,
        )


if __name__ == "__main__":
    unittest.main()
