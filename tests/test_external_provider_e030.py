import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.external_provider import jq_182_release, plan_external_release, apply_external_plan, remove_external_provider, compile_jq_consumer

class ExternalProviderE030Tests(unittest.TestCase):
    def test_real_jq_acquire_verify_consume_remove(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=root/"environment.json"
            release=jq_182_release()
            plan=plan_external_release("query JSON with a real external provider",release,root/"providers","e030-demo")
            target=Path(plan.changes[0].target)

            self.assertFalse(target.exists())
            self.assertFalse(plan.explain()["mutates_environment"])
            self.assertTrue(plan.explain()["would_modify_environment"])
            blocked=apply_external_plan(plan,manifest,authorized=False)
            self.assertEqual(blocked["status"],"authorization_required")
            self.assertFalse(target.exists())

            applied=apply_external_plan(plan,manifest,authorized=True)
            self.assertTrue(applied["ok"])
            self.assertTrue(target.exists())

            state=json.loads(manifest.read_text(encoding="utf-8"))
            entry=state["providers"]["jq-1.8.2"]
            self.assertEqual(entry["installed_by"],"autocompiler")
            self.assertIn("json.query",entry["capabilities"])
            self.assertIn("e030-demo",entry["consumers"])

            artifact=compile_jq_consumer(target,root/"generated")
            run=subprocess.run([sys.executable,str(artifact)],text=True,capture_output=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(run.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"],"[2,4,6]")
            self.assertFalse(result["autocompiler_runtime_used"])
            self.assertFalse(result["recurring_ai_used"])

            removed=remove_external_provider(plan,manifest,"e030-demo")
            self.assertEqual(removed["status"],"removed")
            self.assertFalse(target.exists())

if __name__=="__main__": unittest.main()
