import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.workspace import repository_snapshot


class WorkspaceTests(unittest.TestCase):
    def test_snapshot_exposes_repository_tree_without_git_internals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "AutoCompiler"
            (root / "src" / "autocompiler").mkdir(parents=True)
            (root / ".git").mkdir()
            (root / "README.md").write_text("# demo", encoding="utf-8")
            (root / "src" / "autocompiler" / "engine.py").write_text("pass", encoding="utf-8")
            state = repository_snapshot(root)
            paths = {entry["path"] for entry in state["entries"]}
            self.assertIn("README.md", paths)
            self.assertIn("src/autocompiler/engine.py", paths)
            self.assertNotIn(".git", paths)
            self.assertEqual(state["name"], "AutoCompiler")

    def test_snapshot_can_be_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                (root / f"{i}.txt").write_text("x", encoding="utf-8")
            state = repository_snapshot(root, max_entries=2)
            self.assertEqual(len(state["entries"]), 2)
            self.assertTrue(state["truncated"])


if __name__ == "__main__":
    unittest.main()
