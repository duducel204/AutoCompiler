import unittest
from pathlib import Path
from unittest.mock import patch

from src.autocompiler.canvas_bridge import route


class CanvasBridgeTests(unittest.TestCase):
    @patch("src.autocompiler.canvas_bridge.discover")
    def test_routes_environment_to_real_discover(self, mocked):
        mocked.return_value = {
            "machine": {"os": "Windows", "release": "11", "architecture": "AMD64"},
            "summary": {"detected": 2, "checked": 3},
            "capabilities": [
                {"id": "filesystem", "detected": True, "path": "C:/Users/Test", "version": None, "notes": None},
            ],
        }
        output = route("Descubra o ambiente deste computador.", Path("."))
        self.assertIn("Windows 11", output)
        self.assertIn("filesystem", output)
        mocked.assert_called_once()

    def test_unknown_request_does_not_pretend_ai_was_used(self):
        output = route("invente algo novo", Path("."))
        self.assertIn("Nenhuma IA foi chamada", output)


if __name__ == "__main__":
    unittest.main()
