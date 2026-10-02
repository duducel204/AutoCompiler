from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.capability_closure import CapabilityClosureService
from src.autocompiler.workflow_lifecycle import (
    WorkflowPlanStore,
    apply_workflow_plan,
    replan_workflow,
)


class CapabilityClosureE2ETests(unittest.TestCase):
    def test_a_closes_gap_and_b_reuses_same_validated_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = root / "capabilities.json"
            provider_script = root / "formatter_provider.py"
            invocation_log = root / "invocations.txt"
            provider_script.write_text(
                "import json, pathlib, sys\n"
                f"log = pathlib.Path({str(invocation_log)!r})\n"
                "value = sys.argv[1] if len(sys.argv) > 1 else ''\n"
                "with log.open('a', encoding='utf-8') as h: h.write(value + '\\n')\n"
                "print(json.dumps({'formatted': value.upper()}))\n",
                encoding="utf-8",
            )

            def ir(name: str, value: str) -> dict:
                return {
                    "schema_version": "0.3",
                    "name": name,
                    "trigger": {"type": "manual"},
                    "steps": [
                        {
                            "id": "format",
                            "skill": "act",
                            "with": {
                                "capability": "custom.formatter",
                                "args": [str(provider_script), value],
                            },
                        }
                    ],
                }

            automation_a = ir("automation-a", "alpha")
            automation_b = ir("automation-b", "beta")
            store = WorkflowPlanStore()

            initial = replan_workflow(
                automation_a,
                out_dir=root / "a",
                local_catalog_path=catalog,
            )
            self.assertFalse(initial["can_apply"])
            self.assertIn("custom.formatter", initial["missing_capabilities"])
            record_a0 = store.create(automation_a, initial)
            old_plan_id = record_a0["plan"]["plan_id"]

            service = CapabilityClosureService(
                local_catalog_path=catalog,
                verifier=lambda cap, provider: (
                    cap == "custom.formatter"
                    and provider == "portable-formatter"
                    and provider_script.is_file()
                ),
            )
            closure = service.plan_closure(
                "custom.formatter",
                provider="portable-formatter",
                binding={"executable": sys.executable},
                contract_tests=("tests/test_capability_closure_e2e.py",),
                rollback="remove portable formatter binding",
            )
            blocked = service.apply_closure(
                closure,
                authorized=False,
                evidence=("cc04:provider-script-present",),
            )
            self.assertFalse(blocked.ok)
            self.assertEqual(blocked.status, "authorization_required")

            closed = service.apply_closure(
                closure,
                authorized=True,
                evidence=("cc04:provider-script-present",),
            )
            self.assertTrue(closed.ok)
            self.assertEqual(closed.status, "validated")

            replanned_a = store.replan(old_plan_id, local_catalog_path=catalog)
            self.assertIsNotNone(replanned_a)
            self.assertFalse(replanned_a["authorized"])
            plan_a = replanned_a["plan"]
            self.assertTrue(plan_a["can_apply"])
            self.assertEqual(
                plan_a["providers"]["custom.formatter"],
                "portable-formatter",
            )
            self.assertEqual(
                plan_a["bindings"]["custom.formatter"],
                {"executable": sys.executable},
            )

            authorized_a = store.authorize(plan_a["plan_id"])
            self.assertIsNotNone(authorized_a)
            result_a = apply_workflow_plan(authorized_a)
            self.assertTrue(result_a["ok"], msg=result_a)
            self.assertEqual(
                result_a["result"]["context"]["format"],
                {"formatted": "ALPHA"},
            )
            self.assertFalse(result_a["result"]["autocompiler_runtime_used"])

            plan_b = replan_workflow(
                automation_b,
                out_dir=root / "b",
                local_catalog_path=catalog,
            )
            self.assertTrue(plan_b["can_apply"])
            self.assertEqual(plan_b["missing_capabilities"], [])
            self.assertEqual(
                plan_b["providers"]["custom.formatter"],
                "portable-formatter",
            )
            record_b = store.create(automation_b, plan_b)
            authorized_b = store.authorize(record_b["plan"]["plan_id"])
            result_b = apply_workflow_plan(authorized_b)
            self.assertTrue(result_b["ok"], msg=result_b)
            self.assertEqual(
                result_b["result"]["context"]["format"],
                {"formatted": "BETA"},
            )

            invocations = invocation_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(invocations, ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
