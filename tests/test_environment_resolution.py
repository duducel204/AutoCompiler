import tempfile
import unittest
from pathlib import Path
from src.autocompiler.environment import build_resource_graph
from src.autocompiler.acquisition import AcquisitionArtifact, Provenance
from src.autocompiler.provisioning import AcquisitionRecipe, CapabilityRegistry, Provisioner
from src.autocompiler.environment_manifest import register

def recipe(capability="run_python", provider="portable-python"):
    provenance=Provenance("https://example.invalid/provider","1.0","test","test","sha256:test","MIT","user",False,"remove provider","provider --version")
    artifact=AcquisitionArtifact(provider,(capability,),"portable",("install-test-provider",),provenance)
    return AcquisitionRecipe(capability,provider,artifact)

class EnvironmentResolutionTests(unittest.TestCase):
    def test_reuse_before_acquire_and_gap_resolution(self):
        inventory={"capabilities":[{"id":"filesystem","detected":True,"usable":"yes"},{"id":"python","detected":False}]}
        graph=build_resource_graph(inventory)
        plan=CapabilityRegistry([recipe()]).resolve(["filesystem.read","run_python"],graph,{"zero_cost":True,"no_admin":True})
        self.assertEqual([x.action for x in plan.resolutions],["reuse","acquire"])
        self.assertEqual(plan.permissions,["environment.modify"])

    def test_provisioning_is_authorized_verified_and_owned(self):
        plan=CapabilityRegistry([recipe("pdf.generate","test-pdf")]).resolve(["pdf.generate"],{"resources":[]})
        provisioner=Provisioner(lambda cmd:0,lambda capability,provider: True)
        self.assertEqual(provisioner.apply(plan)["status"],"authorization_required")
        result=provisioner.apply(plan,authorized=True)
        self.assertTrue(result["ok"])
        with tempfile.TemporaryDirectory() as td:
            manifest=register(Path(td)/"environment.json","test-pdf","pdf.generate","autocompiler","demo")
            self.assertEqual(manifest["providers"]["test-pdf"]["installed_by"],"autocompiler")
            self.assertIn("demo",manifest["providers"]["test-pdf"]["consumers"])

    def test_detected_resource_does_not_bypass_usable_state(self):
        graph={
            "resources":[
                {
                    "capability":"schedule",
                    "provider":"native_scheduler",
                    "state":"detected",
                }
            ]
        }
        plan=CapabilityRegistry().resolve(["schedule"],graph)
        self.assertEqual(plan.resolutions[0].action,"unresolved")

    def test_unknown_gap_fails_closed(self):
        plan=CapabilityRegistry().resolve(["unknown.capability"],{"resources":[]})
        self.assertEqual(plan.resolutions[0].action,"unresolved")

if __name__=="__main__": unittest.main()
