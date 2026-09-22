import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.intent import compile_intent


class IntentTests(unittest.TestCase):
    def test_portuguese_file_with_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("autocompiler.intent._desktop", return_value=Path(tmp)):
                result = compile_intent("crie um arquivo chamado teste.txt na minha Área de Trabalho com a data atual")
        self.assertTrue(result.understood)
        step = result.recipe["steps"][0]
        self.assertEqual(step["action"], "write_text")
        self.assertEqual(Path(step["args"]["path"]).name, "teste.txt")
        self.assertEqual(step["args"]["text"], "{CURRENT_DATE}")
        self.assertTrue(result.permissions[0].startswith("write:"))

    def test_unknown_intent_does_not_execute_guess(self):
        result = compile_intent("organize tudo para mim")
        self.assertFalse(result.understood)
        self.assertIsNone(result.recipe)


if __name__ == "__main__":
    unittest.main()
