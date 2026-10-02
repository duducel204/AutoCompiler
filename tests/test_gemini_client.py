import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.gemini_client import GeminiAPIError, _classify_http_error, extract_function_calls, extract_text, probe


class GeminiClientTests(unittest.TestCase):
    def test_extract_text_reads_generate_content_response(self):
        payload = {
            "candidates": [
                {"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}
            ]
        }
        self.assertEqual(extract_text(payload), "OK")

    def test_extract_function_calls_reads_declared_tool_call(self):
        payload = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "Vou executar a ação pedida."},
                        {
                            "functionCall": {
                                "id": "call-1",
                                "name": "browser_search",
                                "args": {"query": "tradutor"},
                            }
                        },
                    ]
                }
            }]
        }
        calls = extract_function_calls(payload)
        self.assertEqual(calls, [{
            "id": "call-1",
            "name": "browser_search",
            "args": {"query": "tradutor"},
        }])

    def test_authentication_errors_are_classified_without_secret_material(self):
        body = json.dumps({
            "error": {
                "code": 401,
                "status": "UNAUTHENTICATED",
                "message": "Request had invalid authentication credentials.",
                "details": [{"reason": "ACCESS_TOKEN_TYPE_UNSUPPORTED"}],
            }
        })
        error = _classify_http_error(401, body)
        self.assertEqual(error.kind, "authentication")
        self.assertEqual(error.http_status, 401)
        self.assertEqual(error.provider_reason, "ACCESS_TOKEN_TYPE_UNSUPPORTED")
        self.assertNotIn("api_key", str(error).lower())

    def test_quota_error_is_distinct_from_authentication(self):
        error = _classify_http_error(
            429,
            json.dumps({"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota"}}),
        )
        self.assertEqual(error.kind, "quota")
        self.assertEqual(error.http_status, 429)

    @patch("autocompiler.gemini_client.generate_text")
    def test_probe_returns_public_diagnostic(self, generate):
        generate.side_effect = GeminiAPIError(
            kind="permission",
            message="permission denied",
            http_status=403,
            provider_code="PERMISSION_DENIED",
        )
        result = probe("secret-key", "gemini-3.8-flash")
        self.assertFalse(result["ok"])
        self.assertEqual(result["diagnostic"]["kind"], "permission")
        self.assertNotIn("secret-key", str(result))


if __name__ == "__main__":
    unittest.main()
