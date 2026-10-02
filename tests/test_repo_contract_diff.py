from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepoContractDiffTests(unittest.TestCase):
    def test_contract_diff_is_structured_and_deterministic(self):
        result = subprocess.run(
            [sys.executable, "scripts/repo_contract_diff.py", "--target", "python-sqlite"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["target"], "python-sqlite")
        self.assertIn("accepted_not_materialized", payload)
        self.assertIn("materialized_not_accepted", payload)
        self.assertEqual(
            payload["coverage"]["covered"],
            len(set(payload["accepted_skills"]) & set(payload["materialized_skills"])),
        )


if __name__ == "__main__":
    unittest.main()
