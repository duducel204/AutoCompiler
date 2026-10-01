import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import json
import threading
from urllib.request import Request, urlopen

from autocompiler.catalog import CapabilityCatalog
from autocompiler.local_canvas import CanvasHandler, ThreadingHTTPServer, apply_git_acquisition, snapshot


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

    def test_workflow_endpoints_validate_save_load_compile_run(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), CanvasHandler)
        port = server.server_port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{port}"

            ir_w01 = {
                "schema_version": "0.1",
                "name": "W01 Canvas Test",
                "trigger": {"type": "manual"},
                "steps": [
                    {"id": "s1", "skill": "filesystem.scan", "with": {"path": ".", "glob": "*"}},
                    {"id": "s2", "skill": "filter.extension", "with": {"from": "s1", "extension": ".txt"}},
                    {"id": "s3", "skill": "filesystem.copy", "with": {"from": "s2", "destination": "./out"}},
                    {"id": "s4", "skill": "state.record", "with": {"from": "s3"}},
                ],
                "state": {"file": "history.db"},
            }

            # 0. /api/ai/draft
            req_ai = Request(f"{base_url}/api/ai/draft", data=json.dumps({"prompt": "Organizar PDFs na pasta ./processed_pdfs"}).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urlopen(req_ai) as resp:
                ai_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(ai_res["ok"])
            self.assertEqual(ai_res["ir"]["name"], "Organizar PDFs Recebidos")

            # 1. /api/workflow/validate
            req = Request(f"{base_url}/api/workflow/validate", data=json.dumps({"ir": ir_w01}).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urlopen(req) as resp:
                val_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(val_res["ok"])
            self.assertIn("filesystem.read", val_res["required_capabilities"])

            # 2. /api/workflow/save
            with tempfile.TemporaryDirectory() as td:
                wf_path = Path(td) / "workflow.ir.json"
                req = Request(f"{base_url}/api/workflow/save", data=json.dumps({"path": str(wf_path), "ir": ir_w01}).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urlopen(req) as resp:
                    save_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(save_res["ok"])
                self.assertTrue(wf_path.exists())

                # 3. /api/workflow/load
                with urlopen(f"{base_url}/api/workflow/load?path={wf_path}") as resp:
                    load_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(load_res["ok"])
                self.assertEqual(load_res["ir"]["name"], "W01 Canvas Test")

                # 4. /api/workflow/compile_and_run
                run_out_dir = Path(td) / "compiled"
                req = Request(f"{base_url}/api/workflow/compile_and_run", data=json.dumps({"ir": ir_w01, "target": "python-sqlite", "out_dir": str(run_out_dir)}).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urlopen(req) as resp:
                    run_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(run_res["ok"])
                self.assertTrue(run_res["compiled"])
                self.assertTrue(run_res["result"]["ok"])
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
