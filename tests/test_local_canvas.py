import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.local_canvas import apply_git_acquisition, snapshot


class LocalCanvasTests(unittest.TestCase):
    def test_snapshot_reads_real_catalog_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            catalog = CapabilityCatalog(path)
            catalog.register_candidate(
                "demo.capability", "demo-provider", "1.0.0",
                ("tests.demo",), rollback="remove provider"
            )
            state = snapshot(path)
            self.assertEqual(len(state["catalog"]), 1)
            self.assertEqual(len(state["candidates"]), 1)
            self.assertEqual(state["candidates"][0]["capability"], "demo.capability")
            self.assertEqual(state["validated"], [])

    @patch("autocompiler.local_canvas.plan_git_capability")
    def test_git_acquisition_cannot_run_without_authorization(self, plan):
        plan.return_value = {
            "action": "acquire", "capability": "git", "provider": "Git.Git",
            "command": ["winget", "install", "--id", "Git.Git"],
        }
        result = apply_git_acquisition(authorized=False)
        self.assertEqual(result["status"], "authorization_required")

    @patch("autocompiler.local_canvas.subprocess.run")
    @patch("autocompiler.local_canvas.plan_git_capability")
    def test_authorized_git_acquisition_requires_post_install_reuse(self, plan, run):
        plan.side_effect = [
            {
                "action": "acquire", "capability": "git", "provider": "Git.Git",
                "command": ["winget", "install", "--id", "Git.Git"],
            },
            {
                "action": "reuse", "capability": "git", "provider": "git",
                "path": "git.exe", "version": "git version test",
            },
        ]
        run.return_value.returncode = 0
        run.return_value.stdout = "installed"
        run.return_value.stderr = ""
        result = apply_git_acquisition(authorized=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "provisioned")
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
