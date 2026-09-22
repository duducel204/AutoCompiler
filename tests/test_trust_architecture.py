import unittest
from src.autocompiler.acquisition import AcquisitionArtifact, Provenance
from src.autocompiler.change_plan import Change, ChangePlan, ApplyEngine
from src.autocompiler.trust import classify_failure, RepairLevel, may_auto_repair

class TrustArchitectureTests(unittest.TestCase):
    def test_plan_is_read_only_and_apply_requires_authorization(self):
        plan=ChangePlan("install capability",[Change("acquire","provider-x","missing capability",True)])
        explanation=plan.explain()
        self.assertFalse(explanation["mutates_environment"])
        self.assertTrue(explanation["would_modify_environment"])
        calls=[]
        engine=ApplyEngine(lambda c: calls.append(c) is None, lambda c: True)
        blocked=engine.apply(plan,authorized=False)
        self.assertEqual(blocked["status"],"authorization_required")
        self.assertEqual(calls,[])
        applied=engine.apply(plan,authorized=True)
        self.assertEqual(applied["status"],"verified")

    def test_acquisition_requires_provenance(self):
        artifact=AcquisitionArtifact("tool",("pdf.generate",),"portable",("install",),
            Provenance("https://example.invalid/tool","1.0","windows","x64",None,"MIT","user",False,"remove folder","tool --version"))
        with self.assertRaises(ValueError):
            artifact.validate()

    def test_repair_levels_fail_closed(self):
        known=classify_failure("ModuleNotFoundError: No module named 'src'")
        self.assertEqual(known.level,RepairLevel.DETERMINISTIC)
        self.assertTrue(may_auto_repair(known))
        unknown=classify_failure("semantic behavior changed")
        self.assertEqual(unknown.level,RepairLevel.ARCHITECTURAL)
        self.assertFalse(may_auto_repair(unknown))

if __name__=="__main__": unittest.main()
