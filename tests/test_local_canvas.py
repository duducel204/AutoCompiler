import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from autocompiler.catalog import CapabilityCatalog
from autocompiler.local_canvas import CanvasHandler, ThreadingHTTPServer, apply_git_acquisition, snapshot


class LocalCanvasTests(unittest.TestCase):
    @patch("autocompiler.local_canvas.build_unified_resource_graph")
    def test_snapshot_reads_catalog_and_exposes_planner_resources(self, graph):
        graph.return_value = {
            "resources": [
                {
                    "capability": "filesystem.read",
                    "provider": "python-stdlib-filesystem",
                    "state": "usable",
                    "source": "canonical",
                    "cost": "free",
                }
            ]
        }
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
            self.assertEqual(state["resources"][0]["capability"], "filesystem.read")
            self.assertEqual(state["resources"][0]["provider"], "python-stdlib-filesystem")
            graph.assert_called_once_with(local_catalog_path=path)

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

    @patch("autocompiler.local_canvas.build_machine_preflight")
    def test_workflow_endpoints_require_plan_authorize_apply_verify(self, preflight):
        preflight.return_value = (
            {
                "automation_ready": True,
                "supported_platform": True,
                "phase": "ready",
                "machine": {"os": "Windows"},
                "readiness_summary": {"required": 7, "usable": 7, "missing": 0},
                "statuses": [],
                "missing_required": [],
                "preparation": {"can_apply": False, "changes": [], "unresolved_capabilities": []},
            },
            None,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), CanvasHandler)
        port = server.server_port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{port}"

            with urlopen(f"{base_url}/api/preflight") as resp:
                preflight_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(preflight_res["ok"])
            self.assertTrue(preflight_res["automation_ready"])

            with urlopen(f"{base_url}/api/utilities") as resp:
                utilities_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(utilities_res["ok"])
            self.assertTrue(any(u["user_title"] == "Organizar PDFs" and u["status"] == "ready" for u in utilities_res["utilities"]))
            self.assertTrue(any(u["user_title"] == "Organizar Downloads" and u["status"] == "planned" for u in utilities_res["utilities"]))

            with urlopen(f"{base_url}/favicon.ico") as resp:
                self.assertEqual(resp.status, 204)

            with tempfile.TemporaryDirectory() as td:
                source = Path(td) / "incoming"
                source.mkdir()
                (source / "demo.txt").write_text("hello", encoding="utf-8")
                destination = Path(td) / "out"
                run_out_dir = Path(td) / "compiled"

                ir_w01 = {
                    "schema_version": "0.1",
                    "name": "W01 Canvas Test",
                    "trigger": {"type": "manual"},
                    "steps": [
                        {"id": "s1", "skill": "filesystem.scan", "with": {"path": str(source), "glob": "*"}},
                        {"id": "s2", "skill": "filter.extension", "with": {"from": "s1", "extension": ".txt"}},
                        {"id": "s3", "skill": "filesystem.copy", "with": {"from": "s2", "destination": str(destination)}},
                        {"id": "s4", "skill": "state.record", "with": {"from": "s3"}},
                    ],
                    "state": {"file": "history.db"},
                }

                # J-011 remains available but produces only an editable draft.
                req_ai = Request(
                    f"{base_url}/api/ai/draft",
                    data=json.dumps({"prompt": "Organizar PDFs na pasta ./processed_pdfs"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req_ai) as resp:
                    ai_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(ai_res["ok"])

                # Existing validation/save/load remains functional.
                req = Request(
                    f"{base_url}/api/workflow/validate",
                    data=json.dumps({"ir": ir_w01}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req) as resp:
                    val_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(val_res["ok"])
                self.assertIn("filesystem.read", val_res["required_capabilities"])

                wf_path = Path(td) / "workflow.ir.json"
                req = Request(
                    f"{base_url}/api/workflow/save",
                    data=json.dumps({"path": str(wf_path), "ir": ir_w01}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req) as resp:
                    save_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(save_res["ok"])

                with urlopen(f"{base_url}/api/workflow/load?path={wf_path}") as resp:
                    load_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(load_res["ok"])

                # Old direct execution path is closed.
                direct = Request(
                    f"{base_url}/api/workflow/compile_and_run",
                    data=json.dumps({"ir": ir_w01}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as direct_error:
                    urlopen(direct)
                self.assertEqual(direct_error.exception.code, 403)

                # 1. PLAN
                req = Request(
                    f"{base_url}/api/workflow/plan",
                    data=json.dumps({
                        "ir": ir_w01,
                        "target": "python-sqlite",
                        "out_dir": str(run_out_dir),
                        "source": "canvas",
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req) as resp:
                    plan_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(plan_res["ok"])
                plan_id = plan_res["plan"]["plan_id"]
                self.assertTrue(plan_res["plan"]["protected_mutation"])

                # APPLY before AUTHORIZE is blocked and produces no compiled artifact.
                req = Request(
                    f"{base_url}/api/workflow/apply",
                    data=json.dumps({"plan_id": plan_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as unauthorized_error:
                    urlopen(req)
                self.assertEqual(unauthorized_error.exception.code, 403)
                self.assertFalse(run_out_dir.exists())

                # 2. AUTHORIZE exact stored plan
                req = Request(
                    f"{base_url}/api/workflow/authorize",
                    data=json.dumps({"plan_id": plan_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req) as resp:
                    auth_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(auth_res["authorized"])

                # 3. APPLY + VERIFY
                req = Request(
                    f"{base_url}/api/workflow/apply",
                    data=json.dumps({"plan_id": plan_id, "ir": {"name": "ignored-tampering"}}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req) as resp:
                    apply_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(apply_res["ok"])
                self.assertEqual(apply_res["status"], "verified")
                self.assertTrue(apply_res["verification"]["ir_matches_authorized_plan"])
                self.assertTrue(apply_res["verification"]["execution_ok"])
                self.assertTrue((destination / "demo.txt").exists())

                # Authorization is one-shot; the same plan cannot be replayed silently.
                replay = Request(
                    f"{base_url}/api/workflow/apply",
                    data=json.dumps({"plan_id": plan_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as replay_error:
                    urlopen(replay)
                self.assertEqual(replay_error.exception.code, 403)
        finally:
            server.shutdown()

    @patch("autocompiler.local_canvas.build_machine_preflight")
    def test_workflow_authorization_is_blocked_when_machine_is_not_ready(self, preflight):
        preflight.return_value = (
            {
                "automation_ready": False,
                "supported_platform": True,
                "phase": "blocked",
                "missing_required": ["schedule"],
            },
            None,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), CanvasHandler)
        port = server.server_port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = Request(
                f"http://127.0.0.1:{port}/api/workflow/authorize",
                data=json.dumps({"plan_id": "anything"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(req)
            self.assertEqual(error.exception.code, 409)
            body = json.loads(error.exception.read().decode("utf-8"))
            self.assertEqual(body["status"], "machine_not_automation_ready")
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
