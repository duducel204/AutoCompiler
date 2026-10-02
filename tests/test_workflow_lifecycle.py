import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
            {"capability": "http.request", "provider": "stdlib-http", "state": "usable", "cost": "free"},
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
        self.assertFalse(plan["can_apply"])
        self.assertFalse(plan["compiler_support"]["supported"])
        self.assertFalse(plan["deployment_support"]["supported"])

    def test_plan_id_binds_provider_resolution(self):
        ir = w01_ir("./incoming", "./processed")
        plan_a = build_workflow_plan(ir, resource_graph=usable_graph("stdlib"))
        plan_b = build_workflow_plan(ir, resource_graph=usable_graph("python-stdlib-filesystem"))
        self.assertNotEqual(plan_a["plan_id"], plan_b["plan_id"])
        req_a = {x["capability"]: x["provider"] for x in plan_a["resolved_execution"]["requirements"]}
        req_b = {x["capability"]: x["provider"] for x in plan_b["resolved_execution"]["requirements"]}
        self.assertEqual(req_a["filesystem.read"], "stdlib")
        self.assertEqual(req_b["filesystem.read"], "python-stdlib-filesystem")

    def test_schedule_resolution_alone_does_not_claim_deployment_ready(self):
        ir = w01_ir("./incoming", "./processed")
        ir["trigger"] = {"type": "schedule", "cron": "0 9 * * *"}
        graph = usable_graph()
        graph["resources"].append({"capability": "schedule", "provider": "windows-task-scheduler", "state": "usable", "cost": "free"})
        plan = build_workflow_plan(ir, resource_graph=graph)
        self.assertEqual(plan["missing_capabilities"], [])
        self.assertTrue(plan["compiler_support"]["supported"])
        self.assertFalse(plan["deployment_support"]["supported"])
        self.assertFalse(plan["can_apply"])

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
