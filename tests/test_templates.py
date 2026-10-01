import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.templates import (
    STARTER_TEMPLATES,
    get_template,
    instantiate_template,
    list_templates,
)


class StarterTemplatesTests(unittest.TestCase):
    def test_list_templates_returns_all_starter_recipes(self):
        tmpl_list = list_templates()
        self.assertEqual(len(tmpl_list), len(STARTER_TEMPLATES))
        ids = [t["id"] for t in tmpl_list]
        self.assertIn("w01", ids)
        self.assertIn("w02", ids)
        self.assertIn("w03", ids)
        self.assertIn("w04", ids)
        self.assertIn("w05", ids)

    def test_get_template_returns_correct_definition(self):
        w01 = get_template("w01")
        self.assertEqual(w01["name"], "Organize Incoming PDFs")
        self.assertEqual(len(w01["parameters"]), 2)

        with self.assertRaises(ValueError):
            get_template("nonexistent_template")

    def test_instantiate_template_substitutes_parameters_and_plans_capabilities(self):
        params = {
            "source_folder": "./my_inputs",
            "target_folder": "./my_pdfs",
        }
        res = instantiate_template("w01", params)
        self.assertTrue(res["ir"])
        self.assertEqual(res["ir"]["steps"][0]["with"]["path"], "./my_inputs")
        self.assertEqual(res["ir"]["steps"][2]["with"]["destination"], "./my_pdfs")
        self.assertIn("filesystem.read", res["required_capabilities"])
        self.assertIn("filesystem.write", res["required_capabilities"])
        self.assertEqual(res["plan"]["executor"], "local")


if __name__ == "__main__":
    unittest.main()
