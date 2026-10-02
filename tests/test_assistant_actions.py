import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.assistant_actions import (
    actions_status,
    execute_assistant_action,
    set_actions_enabled,
)


class AssistantActionsTests(unittest.TestCase):
    def tearDown(self):
        set_actions_enabled(False)

    def test_actions_are_disabled_by_default(self):
        set_actions_enabled(False)
        result = execute_assistant_action("browser_open", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "assistant_actions_disabled")

    @patch("autocompiler.assistant_actions.detect_browser")
    @patch("autocompiler.assistant_actions.subprocess.Popen")
    def test_browser_search_uses_detected_browser_without_shell(self, popen, detect):
        detect.return_value = SimpleNamespace(
            detected=True,
            path=r"C:\Browser\browser.exe",
            providers=[SimpleNamespace(name="Browser", path=r"C:\Browser\browser.exe")],
        )
        set_actions_enabled(True)
        result = execute_assistant_action("browser_search", {"query": "tradutor"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["function"], "browser_search")
        self.assertEqual(result["query"], "tradutor")
        self.assertFalse(result["shell_used"])
        args = popen.call_args.args[0]
        self.assertEqual(args[0], r"C:\Browser\browser.exe")
        self.assertIn("google.com/search", args[1])
        self.assertIn("tradutor", args[1])

    @patch("autocompiler.assistant_actions.detect_browser")
    @patch("autocompiler.assistant_actions.subprocess.Popen")
    def test_browser_open_launches_only_detected_browser(self, popen, detect):
        detect.return_value = SimpleNamespace(
            detected=True,
            path=r"C:\Browser\browser.exe",
            providers=[SimpleNamespace(name="Browser", path=r"C:\Browser\browser.exe")],
        )
        set_actions_enabled(True)
        result = execute_assistant_action("browser_open", {})
        self.assertTrue(result["ok"])
        self.assertEqual(popen.call_args.args[0], [r"C:\Browser\browser.exe"])

    def test_navigation_blocks_non_http_schemes(self):
        set_actions_enabled(True)
        for url in ("file:///C:/Windows/System32", "javascript:alert(1)", "powershell:whoami"):
            with self.subTest(url=url):
                result = execute_assistant_action("browser_navigate", {"url": url})
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "only_http_https_urls_are_allowed")

    def test_unknown_function_is_never_executed(self):
        set_actions_enabled(True)
        result = execute_assistant_action("shell_exec", {"command": "whoami"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "function_not_allowed")
        self.assertNotIn("shell_exec", actions_status()["allowed_functions"])


if __name__ == "__main__":
    unittest.main()
