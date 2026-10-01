import json
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.engine import execute


class ReliabilityTests(unittest.TestCase):
    def test_controlled_failure_retries_and_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            attempts = {"count": 0}

            def flakey_http(method, url, body, retries):
                attempts["count"] += 1
                if attempts["count"] < 3:
                    raise RuntimeError("Transient network failure")
                return {"status": 200, "data": "ok"}

            ir = {
                "schema_version": "0.1",
                "name": "Flakey Request Test",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "fetch",
                        "skill": "http.request",
                        "with": {"url": "http://example.com/api"},
                        "error_policy": {
                            "retries": 3,
                            "backoff_sec": 0.001,
                        },
                    }
                ],
            }

            res = execute(ir, {}, root, flakey_http)
            self.assertEqual(attempts["count"], 3)
            self.assertEqual(res["context"]["fetch"]["data"], "ok")

    def test_failure_exhausts_retries_and_executes_fallback_and_notify(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def failing_http(method, url, body, retries):
                raise RuntimeError("Persistent 500 Internal Server Error")

            ir = {
                "schema_version": "0.1",
                "name": "Fallback Test",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "failing_fetch",
                        "skill": "http.request",
                        "with": {"url": "http://example.com/fail"},
                        "error_policy": {
                            "retries": 2,
                            "backoff_sec": 0.001,
                            "fallback": {"action": "use_cache"},
                            "notify_on_error": True,
                        },
                    }
                ],
            }

            res = execute(ir, {}, root, failing_http)
            fetch_res = res["context"]["failing_fetch"]
            self.assertTrue(fetch_res["fallback_executed"])
            self.assertIn("Persistent 500", fetch_res["error"])

            trace_steps = [t["step"] for t in res["trace"]]
            self.assertIn("failing_fetch", trace_steps)
            self.assertIn("failing_fetch_fallback", trace_steps)


if __name__ == "__main__":
    unittest.main()
