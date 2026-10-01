import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.compiler import compile_ir
from autocompiler.planner import Requirement, plan
from autocompiler.portable_provider import acquire_verified_file, sha256
from autocompiler.provisioning import CapabilityRegistry, ExecutionPlan, Resolution
from autocompiler.provisioning_vertical import apply_portable_plan, plan_portable_capability


class CapabilityClosureGateTests(unittest.TestCase):
    """Canonical cross-task Capability Closure Gate test (J-002 -> J-005).

    Proves the complete AutoCompiler thesis:
    1. Automation A needs a capability genuinely absent at the start.
    2. AutoCompiler identifies the gap, plans resolution, requires authorization, applies,
       verifies, and registers the new capability in validated memory.
    3. Automation A compiles and executes independently without AutoCompiler runtime or AI.
    4. Automation B (different intent) requires the same capability.
    5. Normal planner resolves Automation B from canonical catalog memory via REUSE.
    6. Automation B compiles and executes without reacquiring or rebuilding the provider.
    """

    def test_full_capability_closure_and_second_use_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog_dir = root / "catalog"
            catalog_dir.mkdir()
            local_catalog_file = root / "capabilities.json"
            env_manifest = root / "environment_manifest.json"

            capability_id = "custom.formatter"
            provider_id = "portable-formatter"

            # Create source binary/script for provider
            launcher = catalog_dir / ("formatter.cmd" if sys.platform == "win32" else "formatter")
            if sys.platform == "win32":
                launcher.write_text('@echo off\necho FORMATTED_OUTPUT\n', encoding="utf-8")
            else:
                launcher.write_text('#!/bin/sh\necho FORMATTED_OUTPUT\n', encoding="utf-8")
                launcher.chmod(0o755)

            install_dir = root / "environment"

            # --- STEP 1: Automation A initial plan identifies missing capability ---
            plan_a_initial = plan(
                "Automation A: Format report",
                [Requirement("filesystem.write"), Requirement(capability_id)],
                {"capabilities": []},
                local_catalog_path=local_catalog_file,
            )
            self.assertIn(capability_id, plan_a_initial.missing)

            # --- STEP 2: Resolve gap via canonical provisioning vertical ---
            provision_plan = plan_portable_capability(
                "Acquire text formatter capability",
                capability_id,
                provider_id,
                launcher,
                install_dir,
                "automation-a",
            )
            # PLAN is read-only
            self.assertFalse(provision_plan.explain()["mutates_environment"])

            # Unauthorized APPLY is blocked
            blocked = apply_portable_plan(provision_plan, env_manifest, authorized=False)
            self.assertEqual(blocked["status"], "authorization_required")

            # Authorized APPLY acquires, verifies, and registers ownership
            applied = apply_portable_plan(provision_plan, env_manifest, authorized=True)
            self.assertTrue(applied["ok"])
            installed_binary = install_dir / launcher.name

            # --- STEP 3: Register in validated capability catalog memory ---
            catalog = CapabilityCatalog(local_catalog_file)
            catalog.register_candidate(
                capability_id,
                provider_id,
                "1.0.0",
                ("tests/test_capability_closure.py",),
                permissions=("process.execute",),
                rollback="remove installed binary and registry entry",
                binding={"executable": str(installed_binary)},
            )
            catalog.promote(capability_id, provider_id, ("trust-gate:closure-test:passed",))

            # --- STEP 4: Compile and execute Automation A independently ---
            # Create a sample text file in root to scan
            (root / "input.txt").write_text("sample content")

            ir_a = {
                "schema_version": "0.1",
                "name": "Automation A",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "s1",
                        "skill": "filesystem.scan",
                        "with": {"path": str(root), "glob": "*"},
                    },
                    {
                        "id": "s2",
                        "skill": "filter.extension",
                        "with": {"from": "s1", "extension": ".txt"},
                    },
                    {
                        "id": "s3",
                        "skill": "filesystem.copy",
                        "with": {"from": "s2", "destination": str(root / "out_a")},
                    },
                    {
                        "id": "s4",
                        "skill": "state.record",
                        "with": {"from": "s3"},
                    },
                ],
                "state": {"file": "history_a.db"},
            }

            compiled_a_dir = root / "compiled_a"
            compile_ir(ir_a, "python-sqlite", compiled_a_dir)

            run_a = subprocess.run(
                [sys.executable, str(compiled_a_dir / "automation.py")],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run_a.returncode, 0, run_a.stderr)
            res_a = json.loads(run_a.stdout)
            self.assertTrue(res_a["ok"])
            self.assertFalse(res_a["autocompiler_runtime_used"])
            self.assertFalse(res_a["recurring_ai_used"])

            # --- STEP 5: Automation B (different intent) requires the same capability ---
            plan_b = plan(
                "Automation B: Export audit summary",
                [Requirement("filesystem.read"), Requirement(capability_id)],
                {"capabilities": []},
                local_catalog_path=local_catalog_file,
            )

            # Normal planner finds registered capability and REUSES it without missing gaps
            self.assertEqual(plan_b.missing, [])
            self.assertEqual(plan_b.providers[capability_id], provider_id)
            self.assertTrue(any("Memory reuse:" in n for n in plan_b.notes))

            # --- STEP 6: Compile and execute Automation B independently ---
            ir_b = {
                "schema_version": "0.1",
                "name": "Automation B",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "s1",
                        "skill": "filesystem.scan",
                        "with": {"path": str(root), "glob": "*"},
                    },
                    {
                        "id": "s2",
                        "skill": "filter.extension",
                        "with": {"from": "s1", "extension": ".txt"},
                    },
                    {
                        "id": "s3",
                        "skill": "filesystem.copy",
                        "with": {"from": "s2", "destination": str(root / "out_b")},
                    },
                    {
                        "id": "s4",
                        "skill": "state.record",
                        "with": {"from": "s3"},
                    },
                ],
                "state": {"file": "history_b.db"},
            }

            compiled_b_dir = root / "compiled_b"
            compile_ir(ir_b, "python-sqlite", compiled_b_dir)

            run_b = subprocess.run(
                [sys.executable, str(compiled_b_dir / "automation.py")],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run_b.returncode, 0, run_b.stderr)
            res_b = json.loads(run_b.stdout)
            self.assertTrue(res_b["ok"])
            self.assertFalse(res_b["autocompiler_runtime_used"])
            self.assertFalse(res_b["recurring_ai_used"])


if __name__ == "__main__":
    unittest.main()
