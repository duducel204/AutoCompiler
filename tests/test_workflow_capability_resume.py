from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.autocompiler.catalog import CapabilityCatalog
from src.autocompiler.workflow_lifecycle import (
    WorkflowPlanStore,
    build_workflow_plan,
    replan_workflow,
)


class WorkflowCapabilityResumeTests(unittest.TestCase):
    def setUp(self):
        self.sample_ir = {
            "schema_version": "0.1",
            "name": "Resource Bound Vault Workflow",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "filesystem.scan",
                    "with": {"path": ".", "glob": "*"},
                },
                {
                    "id": "s2",
                    "skill": "act",
                    "with": {"capability": "vault.read", "path": "notes/todo.md"},
                },
            ],
            "state": {"file": "history.db"},
        }

    def test_blocked_plan_exposes_capability_gap_and_can_apply_false(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            plan = replan_workflow(self.sample_ir, local_catalog_path=catalog_file)

            self.assertFalse(plan["can_apply"])
            self.assertIn("vault.read", plan["missing_capabilities"])

    def test_original_ir_preserved_in_store(self):
        store = WorkflowPlanStore()
        plan = build_workflow_plan(self.sample_ir, resource_graph={"resources": []})
        record = store.create(self.sample_ir, plan)

        self.assertEqual(record["ir"]["name"], self.sample_ir["name"])
        self.assertFalse(record["authorized"])
        self.assertFalse(record["applied"])

    def test_replan_after_external_catalog_update_resolves_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            store = WorkflowPlanStore()

            # 1. Initial blocked plan because vault.read is resource-bound and unbound locally
            initial_plan = replan_workflow(self.sample_ir, local_catalog_path=catalog_file)
            self.assertFalse(initial_plan["can_apply"])
            self.assertIn("vault.read", initial_plan["missing_capabilities"])

            initial_record = store.create(self.sample_ir, initial_plan)
            old_plan_id = initial_record["plan"]["plan_id"]

            # Authorize initial plan (even though blocked)
            store.authorize(old_plan_id)
            self.assertTrue(store.get(old_plan_id)["authorized"])

            # 2. Update catalog externally with a validated resource binding (simulating CC-01 closure service)
            catalog = CapabilityCatalog(catalog_file)
            catalog.register_candidate(
                "vault.read",
                "obsidian-local-vault",
                "0.1.0",
                ("tests/test_vault_provider.py",),
                rollback="remove binding",
                binding={"vault_path": "/tmp/vault"},
            )
            catalog.promote("vault.read", "obsidian-local-vault", ("local-real:vault-contract:write-reread=true",))

            # 3. Replan stored workflow
            replanned_record = store.replan(old_plan_id, local_catalog_path=catalog_file)
            self.assertIsNotNone(replanned_record)

            new_plan = replanned_record["plan"]
            new_plan_id = new_plan["plan_id"]

            # Plan ID changes because resolved_execution changed
            self.assertNotEqual(old_plan_id, new_plan_id)

            # Workflow missing_capabilities is now resolved
            self.assertEqual(new_plan["missing_capabilities"], [])
            self.assertEqual(new_plan["providers"].get("vault.read"), "obsidian-local-vault")
            self.assertEqual(new_plan["bindings"].get("vault.read"), {"vault_path": "/tmp/vault"})

            # Prior authorization is NOT inherited
            self.assertFalse(replanned_record["authorized"])
            self.assertFalse(replanned_record["applied"])

    def test_replan_remains_blocked_if_gap_still_exists(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            store = WorkflowPlanStore()

            initial_plan = replan_workflow(self.sample_ir, local_catalog_path=catalog_file)
            initial_record = store.create(self.sample_ir, initial_plan)
            old_plan_id = initial_record["plan"]["plan_id"]

            # Replan without adding capability binding to catalog
            replanned_record = store.replan(old_plan_id, local_catalog_path=catalog_file)
            self.assertIsNotNone(replanned_record)

            self.assertFalse(replanned_record["plan"]["can_apply"])
            self.assertIn("vault.read", replanned_record["plan"]["missing_capabilities"])


if __name__ == "__main__":
    unittest.main()
