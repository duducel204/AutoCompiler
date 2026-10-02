from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autocompiler.acquisition import AcquisitionArtifact, Provenance
from autocompiler.capability_closure import CapabilityClosureService
from autocompiler.catalog import CapabilityCatalog
from autocompiler.planner import Requirement, plan
from autocompiler.provisioning import AcquisitionRecipe


class CapabilityClosureServiceTests(unittest.TestCase):
    def test_absent_capability_reported_as_unresolved_or_acquirable(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            service = CapabilityClosureService(local_catalog_path=catalog_file)

            # Completely unknown capability -> unresolved
            plan_unresolved = service.plan_closure("custom.unknown_cap")
            self.assertEqual(plan_unresolved.action, "unresolved")
            self.assertEqual(plan_unresolved.status, "unresolved")
            self.assertFalse(plan_unresolved.requires_authorization)

            # Specified provider -> acquirable
            plan_acquirable = service.plan_closure("custom.unknown_cap", provider="portable-unknown")
            self.assertEqual(plan_acquirable.action, "acquire")
            self.assertEqual(plan_acquirable.status, "acquirable")
            self.assertTrue(plan_acquirable.requires_authorization)

    def test_planning_does_not_mutate_environment_or_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            recipe = AcquisitionRecipe(
                capability="custom.tool",
                provider="portable-tool",
                artifact=AcquisitionArtifact(
                    provider="portable-tool",
                    capabilities=("custom.tool",),
                    strategy="system",
                    command=("echo", "install"),
                    provenance=Provenance(
                        source="http://example.com/tool",
                        version="1.0.0",
                        platform="any",
                        architecture="any",
                        checksum=None,
                        license="MIT",
                        install_scope="user",
                        requires_admin=False,
                        rollback="uninstall",
                        verification="echo ok",
                    ),
                ),
            )
            service = CapabilityClosureService(local_catalog_path=catalog_file, recipes=[recipe])

            # Inspect closure plan
            p = service.plan_closure("custom.tool")
            self.assertEqual(p.action, "acquire")
            self.assertEqual(p.status, "acquirable")

            # Verify catalog file was NOT created or mutated during planning
            self.assertFalse(catalog_file.exists())

    def test_unauthorized_apply_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            service = CapabilityClosureService(local_catalog_path=catalog_file)

            closure_plan = service.plan_closure("custom.formatter", provider="portable-formatter")

            # Apply without authorization
            result = service.apply_closure(closure_plan, authorized=False)
            self.assertFalse(result.ok)
            self.assertEqual(result.status, "authorization_required")
            self.assertFalse(catalog_file.exists())

    def test_failed_verification_cannot_promote_to_validated(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"

            # Custom verifier that always fails
            def failing_verifier(cap: str, prov: str) -> bool:
                return False

            service = CapabilityClosureService(
                local_catalog_path=catalog_file,
                verifier=failing_verifier,
            )

            closure_plan = service.plan_closure("custom.formatter", provider="portable-formatter")

            # Apply with authorization, but failing verification
            result = service.apply_closure(closure_plan, authorized=True)
            self.assertFalse(result.ok)
            self.assertEqual(result.status, "verification_failed")

            # Ensure catalog remains empty or candidate unpromoted
            catalog = CapabilityCatalog(catalog_file)
            self.assertEqual(len(catalog.validated()), 0)

    def test_successful_apply_promotes_validated_record_and_enables_planner_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"

            def dummy_runner(cmd: list[str]) -> int:
                return 0

            def dummy_verifier(cap: str, prov: str) -> bool:
                return True

            service = CapabilityClosureService(
                local_catalog_path=catalog_file,
                runner=dummy_runner,
                verifier=dummy_verifier,
            )

            cap_id = "custom.dynamic_capability_xyz"
            prov_id = "portable-provider-xyz"

            # 1. Initial planner check: capability is missing
            plan_initial = plan("Process intent", [Requirement(cap_id)], local_catalog_path=catalog_file)
            self.assertIn(cap_id, plan_initial.missing)

            # 2. Plan closure
            closure_plan = service.plan_closure(
                cap_id,
                provider=prov_id,
                binding={"executable": "/bin/true"},
            )
            self.assertEqual(closure_plan.action, "acquire")

            # 3. Apply closure with authorization and verification evidence
            evidence = ("verification-evidence-123",)
            result = service.apply_closure(closure_plan, authorized=True, evidence=evidence)
            self.assertTrue(result.ok)
            self.assertEqual(result.status, "validated")
            self.assertIsNotNone(result.record)

            # 4. Verify catalog record
            catalog = CapabilityCatalog(catalog_file)
            validated = catalog.validated()
            self.assertEqual(len(validated), 1)
            self.assertEqual(validated[0].capability, cap_id)
            self.assertEqual(validated[0].provider, prov_id)
            self.assertEqual(validated[0].evidence, evidence)

            # 5. Subsequent planner pass resolves capability through ordinary memory REUSE
            plan_subsequent = plan("Process intent again", [Requirement(cap_id)], local_catalog_path=catalog_file)
            self.assertEqual(plan_subsequent.missing, [])
            self.assertEqual(plan_subsequent.providers.get(cap_id), prov_id)
            self.assertEqual(plan_subsequent.bindings.get(cap_id), {"executable": "/bin/true"})

    def test_dynamic_capability_names_no_hardcoding(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_file = Path(td) / "capabilities.json"
            service = CapabilityClosureService(local_catalog_path=catalog_file)

            # Arbitrary dynamic capability names
            caps = ["domain.custom_alpha", "domain.custom_beta", "domain.custom_gamma"]

            for cap in caps:
                p = service.plan_closure(cap, provider=f"prov-{cap}")
                res = service.apply_closure(p, authorized=True, evidence=(f"ev-{cap}",))
                self.assertTrue(res.ok)

            catalog = CapabilityCatalog(catalog_file)
            validated_caps = [r.capability for r in catalog.validated()]
            self.assertEqual(sorted(validated_caps), sorted(caps))


if __name__ == "__main__":
    unittest.main()
