import json
import platform
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.deployment import remove_windows_schedule
from autocompiler.templates import instantiate_template
from autocompiler.workflow_lifecycle import (
    WorkflowPlanStore,
    apply_workflow_plan,
    build_workflow_plan,
)


def usable_graph(filesystem_provider: str = "stdlib"):
    return {
        "resources": [
            {"capability": "filesystem.read", "provider": filesystem_provider, "state": "usable", "cost": "free"},
            {"capability": "filesystem.write", "provider": filesystem_provider, "state": "usable", "cost": "free"},
            {"capability": "durable_state", "provider": "sqlite", "state": "usable", "cost": "free"},
            {"capability": "http.request", "provider": "autocompiler.http_provider", "state": "usable", "cost": "free"},
            {"capability": "csv.read", "provider": "python-stdlib-csv", "state": "usable", "cost": "free"},
            {"capability": "xlsx.write", "provider": "python-stdlib-xlsx", "state": "usable", "cost": "free"},
            {"capability": "state.check", "provider": "sqlite", "state": "usable", "cost": "free"},
            {"capability": "state.update", "provider": "sqlite", "state": "usable", "cost": "free"},
        ]
    }


def w01_ir(source: str, destination: str):
    return {
        "schema_version": "0.1",
        "name": "J012 Lifecycle W01",
        "trigger": {"type": "manual"},
        "steps": [
            {"id": "s1", "skill": "filesystem.scan", "with": {"path": source, "glob": "*"}},
            {"id": "s2", "skill": "filter.extension", "with": {"from": "s1", "extension": ".txt"}},
            {"id": "s3", "skill": "filesystem.copy", "with": {"from": "s2", "destination": destination}},
            {"id": "s4", "skill": "state.record", "with": {"from": "s3"}},
        ],
        "state": {"file": "history.db"},
    }


class WorkflowLifecycleTests(unittest.TestCase):
    def test_plan_exposes_user_facing_impact_without_mutation(self):
        ir = w01_ir("./incoming", "./processed")
        plan = build_workflow_plan(
            ir,
            out_dir="./generated/test",
            source="template",
            resource_graph=usable_graph(),
        )

        self.assertTrue(plan["can_apply"])
        self.assertTrue(plan["protected_mutation"])
        self.assertEqual(plan["workflow"]["source"], "template")
        self.assertIn("write", plan["permissions"])
        self.assertTrue(any(x["path"] == "./incoming" and x["mode"] == "read" for x in plan["filesystem"]))
        self.assertTrue(any(x["path"] == "./processed" and x["mode"] == "write" for x in plan["filesystem"]))
        self.assertEqual(plan["network"], [])
        self.assertFalse(plan["ai"]["runtime"])
        self.assertEqual(plan["recurring_cost"]["amount"], 0)
        self.assertFalse(plan["schedule"]["background"])
        self.assertIn("filesystem.read", plan["providers"])
        self.assertTrue(plan["compiler_support"]["supported"])
        self.assertTrue(plan["deployment_support"]["supported"])
        self.assertEqual(plan["resolved_execution"]["target"], "python-sqlite")

    def test_plan_makes_build_time_ai_and_schedule_visible_but_not_ready(self):
        ir = {
            "schema_version": "0.1",
            "name": "Scheduled API snapshot",
            "trigger": {"type": "schedule", "cron": "0 18 * * *"},
            "steps": [
                {"id": "s1", "skill": "http.request", "with": {"url": "https://example.com/data", "method": "GET"}},
                {"id": "s2", "skill": "state.record_jsonl", "with": {"value": "$s1", "file": "events.jsonl"}},
            ],
            "state": {"file": "history.db"},
        }
        graph = usable_graph()
        graph["resources"].append({"capability": "schedule", "provider": "windows-task-scheduler", "state": "usable", "cost": "free"})
        plan = build_workflow_plan(
            ir,
            source="ai",
            build_time_ai=True,
            ai_provider="google-gemini",
            resource_graph=graph,
        )

        self.assertTrue(plan["ai"]["build_time"])
        self.assertEqual(plan["ai"]["build_provider"], "google-gemini")
        self.assertFalse(plan["ai"]["runtime"])
        self.assertTrue(plan["schedule"]["background"])
        self.assertEqual(plan["schedule"]["cron"], "0 18 * * *")
        self.assertEqual(plan["external_services"], ["example.com"])
        self.assertFalse(plan["recurring_cost"]["known"])
        self.assertTrue(plan["can_apply"])
        self.assertTrue(plan["compiler_support"]["supported"])
        self.assertTrue(plan["deployment_support"]["supported"])
        self.assertEqual(plan["deployment_support"]["provider"], "windows-task-scheduler")

    def test_plan_id_binds_provider_resolution(self):
        ir = w01_ir("./incoming", "./processed")
        plan_a = build_workflow_plan(ir, resource_graph=usable_graph("stdlib"))
        plan_b = build_workflow_plan(ir, resource_graph=usable_graph("python-stdlib-filesystem"))
        self.assertNotEqual(plan_a["plan_id"], plan_b["plan_id"])
        req_a = {x["capability"]: x["provider"] for x in plan_a["resolved_execution"]["requirements"]}
        req_b = {x["capability"]: x["provider"] for x in plan_b["resolved_execution"]["requirements"]}
        self.assertEqual(req_a["filesystem.read"], "stdlib")
        self.assertEqual(req_b["filesystem.read"], "python-stdlib-filesystem")

    def test_schedule_resolution_becomes_deployable_only_for_supported_windows_contract(self):
        ir = w01_ir("./incoming", "./processed")
        ir["trigger"] = {"type": "schedule", "cron": "0 9 * * *"}
        graph = usable_graph()
        graph["resources"].append({"capability": "schedule", "provider": "windows-task-scheduler", "state": "usable", "cost": "free"})
        plan = build_workflow_plan(ir, resource_graph=graph)
        self.assertEqual(plan["missing_capabilities"], [])
        self.assertTrue(plan["compiler_support"]["supported"])
        self.assertTrue(plan["deployment_support"]["supported"])
        self.assertEqual(plan["deployment_support"]["windows_schedule"]["schedule"], "DAILY")
        self.assertTrue(plan["can_apply"])

        ir["trigger"] = {"type": "schedule", "cron": "0 9 * * MON"}
        unsupported = build_workflow_plan(ir, resource_graph=graph)
        self.assertFalse(unsupported["deployment_support"]["supported"])
        self.assertFalse(unsupported["can_apply"])

    def test_apply_is_blocked_before_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ir = w01_ir(str(root / "incoming"), str(root / "processed"))
            plan = build_workflow_plan(
                ir,
                out_dir=root / "compiled",
                resource_graph=usable_graph(),
            )
            store = WorkflowPlanStore()
            record = store.create(ir, plan)
            result = apply_workflow_plan(record)
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "authorization_required")
            self.assertFalse((root / "compiled").exists())

    def test_authorized_plan_applies_and_verifies_real_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "demo.txt").write_text("hello", encoding="utf-8")
            processed = root / "processed"
            compiled = root / "compiled"
            ir = w01_ir(str(incoming), str(processed))
            plan = build_workflow_plan(
                ir,
                out_dir=compiled,
                resource_graph=usable_graph(),
            )
            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])
            self.assertIsNotNone(record)

            result = apply_workflow_plan(record)
            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "verified")
            self.assertTrue(result["verification"]["ir_matches_authorized_plan"])
            self.assertTrue(result["verification"]["manifest_matches_authorized_plan"])
            self.assertTrue(result["verification"]["resolution_matches_authorized_plan"])
            self.assertTrue(result["verification"]["execution_ok"])
            self.assertFalse(result["verification"]["recurring_ai_used"])
            self.assertTrue((processed / "demo.txt").exists())
            self.assertEqual(
                result["manifest"]["resolved_execution_digest"],
                result["result"]["resolved_execution_digest"],
            )

    def test_w03_template_consumes_resolved_http_provider_in_independent_artifact(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = json.dumps({"items": [{"id": 1, "name": "alpha"}], "source": "local-proof"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                url = f"http://127.0.0.1:{server.server_address[1]}/snapshot"
                instantiated = instantiate_template(
                    "w03",
                    {"api_url": url, "output_file": "snapshots.jsonl"},
                )
                ir = instantiated["ir"]
                compiled = root / "compiled"
                plan = build_workflow_plan(
                    ir,
                    out_dir=compiled,
                    source="template",
                    resource_graph=usable_graph(),
                )

                self.assertTrue(plan["can_apply"])
                resolved = {
                    x["capability"]: x["provider"]
                    for x in plan["resolved_execution"]["requirements"]
                }
                self.assertEqual(resolved["http.request"], "autocompiler.http_provider")

                store = WorkflowPlanStore()
                store.create(ir, plan)
                record = store.authorize(plan["plan_id"])
                result = apply_workflow_plan(record)

                self.assertTrue(result["ok"])
                self.assertTrue(result["verification"]["resolution_matches_authorized_plan"])
                self.assertFalse(result["result"]["autocompiler_runtime_used"])
                row = json.loads((compiled / "snapshots.jsonl").read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual(row["source"], "local-proof")
                self.assertEqual(row["items"][0]["name"], "alpha")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_scheduled_workflow_deploys_artifact_instead_of_running_it_immediately(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "demo.txt").write_text("hello", encoding="utf-8")
            ir = w01_ir(str(incoming), str(root / "backup"))
            ir["trigger"] = {"type": "schedule", "cron": "0 9 * * *"}
            graph = usable_graph()
            graph["resources"].append({
                "capability": "schedule",
                "provider": "windows-task-scheduler",
                "state": "usable",
                "cost": "free",
            })
            plan = build_workflow_plan(ir, out_dir=root / "compiled", resource_graph=graph)
            self.assertTrue(plan["can_apply"])

            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])

            deployment = {
                "ok": True,
                "status": "installed_verified",
                "task_name": plan["deployment_support"]["task_name"],
                "provider": "windows-task-scheduler",
            }
            with patch("autocompiler.workflow_lifecycle.deploy_windows_schedule", return_value=deployment) as deploy_mock, \
                 patch("autocompiler.workflow_lifecycle.subprocess.run") as direct_run:
                result = apply_workflow_plan(record)

            self.assertTrue(result["ok"])
            self.assertEqual(result["verification"]["operational_mode"], "deployed")
            self.assertTrue(result["verification"]["deployment_ok"])
            self.assertIsNone(result["verification"]["execution_ok"])
            direct_run.assert_not_called()
            deploy_mock.assert_called_once()

    def test_w05_template_converts_csv_to_real_xlsx_in_independent_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "input.csv"
            output = root / "output.xlsx"
            source.write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")

            instantiated = instantiate_template(
                "w05",
                {"input_csv": str(source), "output_xlsx": str(output)},
            )
            ir = instantiated["ir"]
            compiled = root / "compiled"
            plan = build_workflow_plan(
                ir,
                out_dir=compiled,
                source="template",
                resource_graph=usable_graph(),
            )
            self.assertTrue(plan["can_apply"])
            resolved = {
                x["capability"]: x["provider"]
                for x in plan["resolved_execution"]["requirements"]
            }
            self.assertEqual(resolved["csv.read"], "python-stdlib-csv")
            self.assertEqual(resolved["xlsx.write"], "python-stdlib-xlsx")

            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])
            result = apply_workflow_plan(record)

            self.assertTrue(result["ok"])
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            self.assertFalse(result["result"]["autocompiler_runtime_used"])

    @unittest.skipUnless(platform.system() == "Windows", "real Task Scheduler acceptance runs only on Windows")
    def test_w02_real_windows_scheduler_runs_compiled_backup_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            backup = root / "backup"
            source.mkdir()
            (source / "proof.txt").write_text("scheduled-proof", encoding="utf-8")

            instantiated = instantiate_template(
                "w02",
                {"source_folder": str(source), "backup_folder": str(backup)},
            )
            ir = instantiated["ir"]
            graph = usable_graph()
            graph["resources"].append({
                "capability": "schedule",
                "provider": "native_scheduler",
                "state": "usable",
                "cost": "free",
            })
            plan = build_workflow_plan(
                ir,
                out_dir=root / "compiled",
                source="template",
                resource_graph=graph,
            )
            self.assertTrue(plan["can_apply"])

            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])
            applied = apply_workflow_plan(record)
            task_name = applied.get("deployment", {}).get("task_name")

            try:
                self.assertTrue(applied["ok"])
                self.assertTrue(task_name)
                fired = subprocess.run(
                    ["schtasks.exe", "/Run", "/TN", task_name],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(fired.returncode, 0, fired.stderr)

                deadline = time.time() + 15
                target = backup / "proof.txt"
                while time.time() < deadline and not target.exists():
                    time.sleep(0.25)
                self.assertTrue(target.exists(), "scheduled artifact did not copy the proof file")
                self.assertEqual(target.read_text(encoding="utf-8"), "scheduled-proof")
            finally:
                if task_name:
                    removed = remove_windows_schedule(task_name)
                    self.assertTrue(removed["ok"], removed)

    def test_w04_composes_http_and_state_to_record_only_real_changes(self):
        payload = {"value": 1}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                url = f"http://127.0.0.1:{server.server_address[1]}/state"
                instantiated = instantiate_template(
                    "w04",
                    {"monitor_key": "proof", "target_url": url},
                )
                ir = instantiated["ir"]
                graph = usable_graph()
                graph["resources"].append({
                    "capability": "schedule",
                    "provider": "windows-task-scheduler",
                    "state": "usable",
                    "cost": "free",
                })
                compiled = root / "compiled"
                plan = build_workflow_plan(
                    ir,
                    out_dir=compiled,
                    source="template",
                    resource_graph=graph,
                )
                self.assertTrue(plan["can_apply"])

                store = WorkflowPlanStore()
                store.create(ir, plan)
                record = store.authorize(plan["plan_id"])
                deployment = {
                    "ok": True,
                    "status": "installed_verified",
                    "task_name": plan["deployment_support"]["task_name"],
                    "provider": "windows-task-scheduler",
                }
                with patch("autocompiler.workflow_lifecycle.deploy_windows_schedule", return_value=deployment):
                    applied = apply_workflow_plan(record)
                self.assertTrue(applied["ok"])

                artifact = compiled / "automation.py"

                first = subprocess.run([sys.executable, str(artifact)], capture_output=True, text=True, check=True)
                first_result = json.loads(first.stdout)
                self.assertTrue(first_result["context"]["s3"]["changed"])
                self.assertTrue(first_result["context"]["s3"]["updated"])

                second = subprocess.run([sys.executable, str(artifact)], capture_output=True, text=True, check=True)
                second_result = json.loads(second.stdout)
                self.assertFalse(second_result["context"]["s2"]["changed"])
                self.assertFalse(second_result["context"]["s3"]["changed"])
                self.assertFalse(second_result["context"]["s3"]["updated"])

                payload["value"] = 2
                third = subprocess.run([sys.executable, str(artifact)], capture_output=True, text=True, check=True)
                third_result = json.loads(third.stdout)
                self.assertTrue(third_result["context"]["s2"]["changed"])
                self.assertTrue(third_result["context"]["s3"]["changed"])
                self.assertTrue(third_result["context"]["s3"]["updated"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_all_ready_templates_close_through_the_same_planner_and_compiler(self):
        graph = usable_graph()
        graph["resources"].append({
            "capability": "schedule",
            "provider": "windows-task-scheduler",
            "state": "usable",
            "cost": "free",
        })
        params_by_template = {
            "w01": {"source_folder": "./in", "target_folder": "./out"},
            "w02": {"source_folder": "./in", "backup_folder": "./backup"},
            "w03": {"api_url": "http://127.0.0.1:9999/data", "output_file": "snapshots.jsonl"},
            "w04": {"monitor_key": "proof", "target_url": "http://127.0.0.1:9999/state"},
            "w05": {"input_csv": "input.csv", "output_xlsx": "output.xlsx"},
            "w11": {
                "source_folder": "./Downloads",
                "documents_folder": "./Downloads/Documentos",
                "spreadsheets_folder": "./Downloads/Planilhas",
                "images_folder": "./Downloads/Imagens",
            },
            "w12": {"source_folder": "./in", "extension": ".pdf", "backup_folder": "./backup/pdf"},
            "w13": {"api_url": "http://127.0.0.1:9999/daily", "output_file": "daily.jsonl"},
            "w14": {"input_csv": "daily.csv", "output_xlsx": "daily.xlsx"},
            "w15": {"source_folder": "./inbox", "target_folder": "./archive"},
        }
        for template_id, params in params_by_template.items():
            with self.subTest(template_id=template_id):
                ir = instantiate_template(template_id, params)["ir"]
                plan = build_workflow_plan(
                    ir,
                    out_dir=f"./generated/{template_id}",
                    source="template",
                    resource_graph=graph,
                )
                self.assertTrue(plan["compiler_support"]["supported"], plan["compiler_support"])
                self.assertTrue(plan["deployment_support"]["supported"], plan["deployment_support"])
                self.assertEqual(plan["missing_capabilities"], [])
                self.assertTrue(plan["can_apply"])

    def test_w11_organize_downloads_moves_files_in_independent_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "Downloads"
            docs = root / "Documentos"
            sheets = root / "Planilhas"
            images = root / "Imagens"
            source.mkdir()
            (source / "report.pdf").write_text("pdf", encoding="utf-8")
            (source / "table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (source / "book.xlsx").write_text("xlsx", encoding="utf-8")
            (source / "photo.jpg").write_text("jpg", encoding="utf-8")
            (source / "image.png").write_text("png", encoding="utf-8")
            (source / "keep.txt").write_text("keep", encoding="utf-8")

            ir = instantiate_template(
                "w11",
                {
                    "source_folder": str(source),
                    "documents_folder": str(docs),
                    "spreadsheets_folder": str(sheets),
                    "images_folder": str(images),
                },
            )["ir"]
            compiled = root / "compiled"
            plan = build_workflow_plan(
                ir,
                out_dir=compiled,
                source="template",
                resource_graph=usable_graph(),
            )
            self.assertTrue(plan["can_apply"])
            self.assertTrue(any(x["reason"] == "move destination" for x in plan["filesystem"]))

            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])
            result = apply_workflow_plan(record)

            self.assertTrue(result["ok"])
            self.assertTrue((docs / "report.pdf").exists())
            self.assertTrue((sheets / "table.csv").exists())
            self.assertTrue((sheets / "book.xlsx").exists())
            self.assertTrue((images / "photo.jpg").exists())
            self.assertTrue((images / "image.png").exists())
            self.assertTrue((source / "keep.txt").exists())
            self.assertFalse((source / "report.pdf").exists())
            self.assertEqual(result["result"]["processed"], 5)
            self.assertTrue((compiled / "run-history.jsonl").exists())

    def test_failed_execution_is_not_reported_as_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ir = w01_ir(str(root / "incoming"), str(root / "processed"))
            plan = build_workflow_plan(
                ir,
                out_dir=root / "compiled",
                resource_graph=usable_graph(),
            )
            store = WorkflowPlanStore()
            store.create(ir, plan)
            record = store.authorize(plan["plan_id"])

            failed = Mock(returncode=1, stdout="", stderr="boom")
            with patch("autocompiler.workflow_lifecycle.subprocess.run", return_value=failed):
                result = apply_workflow_plan(record)

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "verification_failed")
            self.assertFalse(result["verification"]["execution_ok"])

    def test_plan_id_binds_ir_and_output_scope(self):
        ir_a = w01_ir("./incoming", "./processed")
        ir_b = w01_ir("./incoming", "./different")
        plan_a = build_workflow_plan(ir_a, out_dir="./a", resource_graph=usable_graph())
        plan_b = build_workflow_plan(ir_b, out_dir="./a", resource_graph=usable_graph())
        plan_c = build_workflow_plan(ir_a, out_dir="./b", resource_graph=usable_graph())

        self.assertNotEqual(plan_a["plan_id"], plan_b["plan_id"])
        self.assertNotEqual(plan_a["plan_id"], plan_c["plan_id"])


if __name__ == "__main__":
    unittest.main()
