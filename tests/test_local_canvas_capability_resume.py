from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

import src.autocompiler.local_canvas as canvas
from src.autocompiler.catalog import CapabilityCatalog
from src.autocompiler.local_canvas import (
    CanvasHandler,
    ThreadingHTTPServer,
    replan_stored_workflow,
    workflow_gap_resolution,
)
from src.autocompiler.workflow_lifecycle import WorkflowPlanStore, build_workflow_plan


def custom_ir(capability: str) -> dict:
    return {
        "schema_version": "0.1",
        "name": "Capability Resume Product Seam",
        "trigger": {"type": "manual"},
        "steps": [
            {
                "id": "s1",
                "skill": "act",
                "with": {
                    "capability": capability,
                    "args": ["hello"],
                },
            }
        ],
    }


class CapabilityResumeProductSeamTests(unittest.TestCase):
    def test_gap_inspection_is_read_only_and_reports_current_missing_capability(self):
        store = WorkflowPlanStore()
        capability = "custom.product_seam_gap"
        ir = custom_ir(capability)
        plan = build_workflow_plan(ir, resource_graph={"resources": []})
        store.create(ir, plan)

        with tempfile.TemporaryDirectory() as td, patch.object(canvas, "WORKFLOW_PLANS", store):
            catalog_path = Path(td) / "capabilities.json"
            self.assertFalse(catalog_path.exists())

            result = workflow_gap_resolution(plan["plan_id"], catalog_path)

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "capability_gap")
            self.assertTrue(result["blocked"])
            self.assertEqual(result["missing_capabilities"], [capability])
            self.assertEqual(result["closure_plans"][0]["capability"], capability)
            self.assertEqual(result["closure_plans"][0]["action"], "unresolved")
            self.assertFalse(result["mutated"])
            self.assertFalse(catalog_path.exists())

    def test_replan_uses_fresh_validated_memory_and_never_inherits_authorization(self):
        store = WorkflowPlanStore()
        capability = "custom.product_seam_reuse"
        provider = "portable-product-seam"
        ir = custom_ir(capability)
        initial = build_workflow_plan(ir, resource_graph={"resources": []})
        store.create(ir, initial)
        store.authorize(initial["plan_id"])

        with tempfile.TemporaryDirectory() as td, patch.object(canvas, "WORKFLOW_PLANS", store):
            catalog_path = Path(td) / "capabilities.json"
            catalog = CapabilityCatalog(catalog_path)
            catalog.register_candidate(
                capability,
                provider,
                "1.0.0",
                ("tests/test_local_canvas_capability_resume.py",),
                rollback="remove portable test provider",
                binding={"executable": str(Path(td) / "provider")},
            )
            catalog.promote(capability, provider, ("test:evidence:validated",))

            result = replan_stored_workflow(initial["plan_id"], catalog_path)

            self.assertTrue(result["ok"])
            self.assertNotEqual(result["old_plan_id"], result["new_plan_id"])
            self.assertEqual(result["missing_capabilities"], [])
            self.assertFalse(result["authorization_inherited"])
            self.assertFalse(result["authorized"])
            self.assertEqual(result["plan"]["providers"][capability], provider)
            self.assertEqual(
                result["plan"]["bindings"][capability],
                {"executable": str(Path(td) / "provider")},
            )

            old_record = store.get(initial["plan_id"])
            self.assertTrue(old_record["authorized"])

    def test_http_gap_and_replan_endpoints_preserve_plan_authorization_boundary(self):
        store = WorkflowPlanStore()
        capability = "custom.http_resume_gap"
        provider = "portable-http-resume"
        ir = custom_ir(capability)
        initial = build_workflow_plan(ir, resource_graph={"resources": []})
        store.create(ir, initial)
        store.authorize(initial["plan_id"])

        with tempfile.TemporaryDirectory() as td, \
             patch.object(canvas, "WORKFLOW_PLANS", store), \
             patch.object(canvas, "DEFAULT_CATALOG", Path(td) / "capabilities.json"):
            catalog_path = Path(td) / "capabilities.json"
            server = ThreadingHTTPServer(("127.0.0.1", 0), CanvasHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                gap_req = Request(
                    f"{base}/api/workflow/gaps",
                    data=json.dumps({"plan_id": initial["plan_id"]}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(gap_req) as response:
                    gap = json.loads(response.read().decode("utf-8"))
                self.assertTrue(gap["ok"])
                self.assertEqual(gap["status"], "capability_gap")
                self.assertEqual(gap["missing_capabilities"], [capability])

                catalog = CapabilityCatalog(catalog_path)
                catalog.register_candidate(
                    capability,
                    provider,
                    "1.0.0",
                    ("tests/test_local_canvas_capability_resume.py",),
                    rollback="remove portable test provider",
                    binding={"executable": str(Path(td) / "provider")},
                )
                catalog.promote(capability, provider, ("test:evidence:http",))

                replan_req = Request(
                    f"{base}/api/workflow/replan",
                    data=json.dumps({"plan_id": initial["plan_id"]}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(replan_req) as response:
                    replanned = json.loads(response.read().decode("utf-8"))

                self.assertTrue(replanned["ok"])
                self.assertNotEqual(replanned["old_plan_id"], replanned["new_plan_id"])
                self.assertEqual(replanned["missing_capabilities"], [])
                self.assertFalse(replanned["authorization_inherited"])
                self.assertFalse(replanned["authorized"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
