import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.planner import Requirement, plan
from autocompiler.runtime import execute


class PlannerRuntimeTests(unittest.TestCase):
    def test_provider_fallback_without_git(self):
        inventory = {"capabilities": [
            {"id": "python", "detected": True},
            {"id": "powershell", "detected": True},
            {"id": "git", "detected": False},
        ]}
        result = plan("obtain repository", [Requirement("repository")], inventory)
        self.assertEqual(result.providers["repository"], "http_download")
        self.assertFalse(result.recurring_ai_required)

    def test_deterministic_recipe_runs_without_ai(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "proof.txt"
            db = Path(td) / "state.db"
            recipe = {
                "name": "proof",
                "steps": [{"id": "write", "action": "write_text", "args": {"path": str(target), "text": "ok"}}],
            }
            result = execute(recipe, str(db))
            self.assertEqual(target.read_text(encoding="utf-8"), "ok")
            self.assertFalse(result["recurring_ai_used"])


if __name__ == "__main__":
    unittest.main()
