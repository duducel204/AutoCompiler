import json
import tempfile
import unittest
from pathlib import Path

from autocompiler.capability_closure import CapabilityClosureService
from autocompiler.catalog import CapabilityCatalog
from autocompiler.planner import Requirement, plan


class CapabilityClosureServiceTests(unittest.TestCase):
    def test_inspect_gap_reports_absent_capability_as_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local_catalog = root / "capabilities.json"
            manifest = root / "environment_manifest.json"

            service = CapabilityClosureService(local_catalog, manifest)
            gap = service.inspect_gap("custom.data_transformer")

            self.assertFalse(gap["available"])
            self.assertEqual(gap["state"], "missing")

    def test_planning_is_read_only_and_does_not_mutate_environment_or_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local_catalog = root / "capabilities.json"
            manifest = root / "environment_manifest.json"
            install_dir = root / "installed"

            source = root / "tool.py"
            source.write_text("print('ok')", encoding="utf-8")

            service = CapabilityClosureService(local_catalog, manifest)
            closure_plan = service.create_closure_plan(
                capability="custom.data_transformer",
                provider="portable-transformer",
                source=source,
                install_dir=install_dir,
            )

            explanation = closure_plan.explain()
            self.assertFalse(explanation["mutates_environment"])
            self.assertTrue(explanation["would_modify_environment"])
            self.assertTrue(explanation["requires_authorization"])

            # Verify no side-effects on disk during planning
            self.assertFalse(local_catalog.exists())
            self.assertFalse(manifest.exists())
            self.assertFalse((install_dir / "tool.py").exists())

    def test_unauthorized_apply_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local_catalog = root / "capabilities.json"
            manifest = root / "environment_manifest.json"
            install_dir = root / "installed"

            source = root / "tool.py"
            source.write_text("print('ok')", encoding="utf-8")

            service = CapabilityClosureService(local_catalog, manifest)
            closure_plan = service.create_closure_plan(
                capability="custom.data_transformer",
                provider="portable-transformer",
                source=source,
                install_dir=install_dir,
            )

            result = service.apply_closure(closure_plan, authorized=False)
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "authorization_required")
            self.assertFalse((install_dir / "tool.py").exists())

    def test_apply_without_evidence_fails_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local_catalog = root / "capabilities.json"
            manifest = root / "environment_manifest.json"
            install_dir = root / "installed"

            source = root / "tool.py"
            source.write_text("print('ok')", encoding="utf-8")

            service = CapabilityClosureService(local_catalog, manifest)
            closure_plan = service.create_closure_plan(
                capability="custom.data_transformer",
                provider="portable-transformer",
                source=source,
                install_dir=install_dir,
            )

            result = service.apply_closure(closure_plan, authorized=True, evidence=())
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "verification_required")

            # Candidate exists, but is not promoted to validated
            catalog = CapabilityCatalog(local_catalog)
            self.assertEqual(len(catalog.validated()), 0)

    def test_successful_apply_and_promotion_enables_ordinary_planner_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local_catalog = root / "capabilities.json"
            manifest = root / "environment_manifest.json"
            install_dir = root / "installed"

            capability_id = "arbitrary.calculator"
            provider_id = "portable-calc"

            source = root / "calc.py"
            source.write_text("print('42')", encoding="utf-8")

            # 1. Verify planner initially sees capability as missing
            initial_plan = plan(
                "Calculate data",
                [Requirement(capability_id)],
                local_catalog_path=local_catalog,
            )
            self.assertIn(capability_id, initial_plan.missing)

            # 2. Plan and apply closure with evidence
            service = CapabilityClosureService(local_catalog, manifest)
            closure_plan = service.create_closure_plan(
                capability=capability_id,
                provider=provider_id,
                source=source,
                install_dir=install_dir,
                contract_tests=("tests/test_capability_closure_service.py",),
            )

            res = service.apply_closure(
                closure_plan,
                authorized=True,
                evidence=("trust-gate:closure-service:passed",),
            )
            self.assertTrue(res["ok"])
            self.assertEqual(res["status"], "validated")

            # 3. Verify installed binary exists
            installed_binary = install_dir / "calc.py"
            self.assertTrue(installed_binary.exists())

            # 4. Verify ordinary planner now resolves capability via reuse
            subsequent_plan = plan(
                "Calculate data second time",
                [Requirement(capability_id)],
                local_catalog_path=local_catalog,
            )
            self.assertEqual(subsequent_plan.missing, [])
            self.assertEqual(subsequent_plan.providers[capability_id], provider_id)
            self.assertIn(capability_id, subsequent_plan.bindings)
            self.assertEqual(
                subsequent_plan.bindings[capability_id]["executable"],
                str(installed_binary),
            )


if __name__ == "__main__":
    unittest.main()
