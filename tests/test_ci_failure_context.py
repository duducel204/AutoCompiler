from __future__ import annotations

import unittest

from scripts.ci_failure_context import build_failure_context


class CIFailureContextTests(unittest.TestCase):
    def test_unknown_failure_becomes_bounded_executor_handoff(self):
        payload = build_failure_context(
            'File "src/autocompiler/compiler.py", line 10\nAssertionError: unexpected\n',
            check="tests.test_example",
            stage="trust_gate",
            exit_code=1,
            source_sha="abc",
        )
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["next_action"], "NEED_EXECUTOR")
        self.assertFalse(payload["safe_repair_available"])
        self.assertEqual(len(payload["error_signature"]), 64)
        self.assertIn("src/autocompiler/compiler.py", payload["affected_files"])
        self.assertTrue(payload["policy"]["unknown_failure_must_not_be_guessed"])

    def test_known_deterministic_failure_can_request_bounded_repair(self):
        payload = build_failure_context(
            "ModuleNotFoundError: No module named 'src'",
            check="import",
            stage="trust_gate",
            exit_code=1,
        )
        self.assertEqual(payload["next_action"], "AUTO_REPAIR")
        self.assertTrue(payload["safe_repair_available"])


if __name__ == "__main__":
    unittest.main()
