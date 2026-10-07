from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.acquisition import AcquisitionArtifact, Provenance
from src.autocompiler.capability_closure import CapabilityClosureService
from src.autocompiler.portable_provider import sha256
from src.autocompiler.provisioning import AcquisitionRecipe
from src.autocompiler.workflow_lifecycle import (
    WorkflowPlanStore,
    apply_workflow_plan,
    build_workflow_plan,
    replan_workflow,
)


def _provider_source(root: Path) -> Path:
    if sys.platform == "win32":
        path = root / "formatter.cmd"
        py = str(Path(sys.executable))
        path.write_text(
            '@echo off\r\n'
            f'"{py}" -c "import sys; print(\'FORMATTED:\'+sys.argv[1])" %*\r\n',
            encoding="utf-8",
        )
        return path

    path = root / "formatter"
    path.write_text("#!/bin/sh\nprintf 'FORMATTED:%s\\n' \"$1\"\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _installer_script(root: Path) -> Path:
    path = root / "install_provider.py"
    path.write_text(
        "from pathlib import Path\n"
        "import shutil, stat, sys\n"
        "source = Path(sys.argv[1])\n"
        "destination = Path(sys.argv[2])\n"
        "destination.parent.mkdir(parents=True, exist_ok=True)\n"
        "shutil.copy2(source, destination)\n"
        "if sys.platform != 'win32':\n"
        "    destination.chmod(destination.stat().st_mode | stat.S_IXUSR)\n",
        encoding="utf-8",
    )
    return path


def _ir(name: str, capability: str, value: str) -> dict:
    return {
        "schema_version": "0.3",
        "name": name,
        "trigger": {"type": "manual"},
        "steps": [
            {
                "id": "format",
                "skill": "act",
                "with": {
                    "capability": capability,
                    "args": [value],
                },
            }
        ],
    }


class CapabilityClosureE2ETests(unittest.TestCase):
    def test_a_closes_real_gap_resumes_and_b_reuses_without_reacquisition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog_path = root / "capabilities.json"
            source = _provider_source(root)
            installed = root / "installed" / source.name
            installer = _installer_script(root)

            capability = "custom.e2e.formatter"
            provider = "portable-e2e-formatter"
            runner_calls: list[list[str]] = []

            recipe = AcquisitionRecipe(
                capability=capability,
                provider=provider,
                artifact=AcquisitionArtifact(
                    provider=provider,
                    capabilities=(capability,),
                    strategy="portable",
                    command=(sys.executable, str(installer), str(source), str(installed)),
                    provenance=Provenance(
                        source=str(source),
                        version="1.0.0",
                        platform=sys.platform,
                        architecture="test-fixture",
                        checksum=sha256(source),
                        license="test-fixture",
                        install_scope="temporary-test-directory",
                        requires_admin=False,
                        rollback="remove installed provider fixture",
                        verification="execute installed provider and compare observed output",
                    ),
                ),
            )
            recipe.artifact.validate()

            def runner(command: list[str]) -> int:
                runner_calls.append(list(command))
                return subprocess.run(command, capture_output=True, text=True, check=False).returncode

            def verifier(cap: str, prov: str) -> bool:
                if cap != capability or prov != provider or not installed.is_file():
                    return False
                probe = subprocess.run(
                    [str(installed), "probe"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return probe.returncode == 0 and probe.stdout.strip() == "FORMATTED:probe"

            closure = CapabilityClosureService(
                local_catalog_path=catalog_path,
                recipes=[recipe],
                runner=runner,
                verifier=verifier,
            )

            # Automation A starts blocked by a genuine semantic capability gap.
            ir_a = _ir("Automation A", capability, "alpha")
            store = WorkflowPlanStore()
            initial_a = build_workflow_plan(
                ir_a,
                out_dir=root / "compiled_a",
                resource_graph={"resources": []},
            )
            self.assertIn(capability, initial_a["missing_capabilities"])
            self.assertFalse(initial_a["can_apply"])
            old_record = store.create(ir_a, initial_a)
            old_plan_id = old_record["plan"]["plan_id"]

            # Closure planning is read-only and selects the declared acquisition recipe.
            closure_plan = closure.plan_closure(
                capability,
                resource_graph={"resources": []},
                provider=provider,
                binding={"executable": str(installed)},
                contract_tests=("tests/test_capability_closure_e2e.py",),
                permissions=("process.execute",),
                rollback="remove installed provider fixture",
            )
            self.assertEqual(closure_plan.action, "acquire")
            self.assertEqual(closure_plan.status, "acquirable")
            self.assertFalse(installed.exists())

            blocked = closure.apply_closure(
                closure_plan,
                authorized=False,
                evidence=("cc04:e2e:provider-contract",),
            )
            self.assertFalse(blocked.ok)
            self.assertEqual(blocked.status, "authorization_required")
            self.assertFalse(installed.exists())
            self.assertEqual(runner_calls, [])

            # Authorized closure acquires a real provider, verifies it, and promotes validated memory.
            closed = closure.apply_closure(
                closure_plan,
                authorized=True,
                evidence=("cc04:e2e:provider-contract",),
            )
            self.assertTrue(closed.ok)
            self.assertEqual(closed.status, "validated")
            self.assertTrue(installed.is_file())
            self.assertEqual(len(runner_calls), 1)
            installed_digest = sha256(installed)

            # Resume the SAME stored workflow against fresh validated memory.
            replanned_record = store.replan(old_plan_id, local_catalog_path=catalog_path)
            self.assertIsNotNone(replanned_record)
            new_plan = replanned_record["plan"]
            self.assertNotEqual(old_plan_id, new_plan["plan_id"])
            self.assertEqual(new_plan["missing_capabilities"], [])
            self.assertEqual(new_plan["providers"][capability], provider)
            self.assertEqual(new_plan["bindings"][capability], {"executable": str(installed)})
            self.assertTrue(new_plan["can_apply"])
            self.assertFalse(replanned_record["authorized"])

            # Authorization never transfers from the obsolete plan to the fresh plan.
            unauthorized_a = apply_workflow_plan(replanned_record)
            self.assertFalse(unauthorized_a["ok"])
            self.assertEqual(unauthorized_a["status"], "authorization_required")

            authorized_a = store.authorize(new_plan["plan_id"])
            self.assertIsNotNone(authorized_a)
            applied_a = apply_workflow_plan(authorized_a)
            self.assertTrue(applied_a["ok"])
            self.assertEqual(applied_a["status"], "verified")
            self.assertEqual(applied_a["result"]["context"]["format"], "FORMATTED:alpha")
            self.assertFalse(applied_a["result"]["autocompiler_runtime_used"])
            self.assertFalse(applied_a["result"]["recurring_ai_used"])

            # Automation B asks for the same capability and must reuse it without reacquisition.
            ir_b = _ir("Automation B", capability, "beta")
            plan_b = replan_workflow(
                ir_b,
                out_dir=root / "compiled_b",
                local_catalog_path=catalog_path,
            )
            self.assertEqual(plan_b["missing_capabilities"], [])
            self.assertEqual(plan_b["providers"][capability], provider)
            self.assertTrue(plan_b["can_apply"])

            reuse = closure.plan_closure(capability)
            self.assertEqual(reuse.action, "reuse")
            self.assertEqual(reuse.status, "resolved")
            self.assertFalse(reuse.requires_authorization)

            self.assertEqual(len(runner_calls), 1)
            self.assertTrue(installed.is_file())
            self.assertEqual(sha256(installed), installed_digest)

            record_b = store.create(ir_b, plan_b)
            authorized_b = store.authorize(record_b["plan"]["plan_id"])
            self.assertIsNotNone(authorized_b)
            applied_b = apply_workflow_plan(authorized_b)
            self.assertTrue(applied_b["ok"])
            self.assertEqual(applied_b["status"], "verified")
            self.assertEqual(applied_b["result"]["context"]["format"], "FORMATTED:beta")
            self.assertFalse(applied_b["result"]["autocompiler_runtime_used"])
            self.assertFalse(applied_b["result"]["recurring_ai_used"])
            self.assertEqual(len(runner_calls), 1)


if __name__ == "__main__":
    unittest.main()
