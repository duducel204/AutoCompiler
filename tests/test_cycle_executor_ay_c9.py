from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.cycle_executors.ay_c9 import execute


class AYCycleExecutorC9Tests(unittest.TestCase):
    def test_executor_creates_only_bounded_proof_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = {
                "source_cycle": {"sha": "abcdef1234567890"},
                "selected": {"id": "AY-C9"},
            }
            result = execute(plan, repo_root=root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["work_item"], "AY-C9")
            self.assertEqual(result["changed"], ["docs/evidence/AUTOMATED_DEVELOPMENT_CYCLE.md"])
            target = root / "docs" / "evidence" / "AUTOMATED_DEVELOPMENT_CYCLE.md"
            self.assertTrue(target.is_file())
            content = target.read_text(encoding="utf-8")
            self.assertIn("abcdef1234567890", content)
            self.assertIn("Direct mutation of main: forbidden", content)

    def test_executor_rejects_other_work_item(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                execute(
                    {"source_cycle": {"sha": "abcdef1"}, "selected": {"id": "AY-CX"}},
                    repo_root=Path(td),
                )


if __name__ == "__main__":
    unittest.main()
