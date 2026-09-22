import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.provisioning_vertical import plan_portable_capability, apply_portable_plan, compile_independent_consumer

class RealProvisioningVerticalTests(unittest.TestCase):
    def test_missing_capability_plan_apply_verify_compile_independent_run(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog=root/"catalog"
            catalog.mkdir()
            # A portable provider is a single executable launcher. It needs no adjacent payload.
            launcher=catalog/("provider.cmd" if sys.platform=="win32" else "provider")
            if sys.platform=="win32":
                launcher.write_text('@echo off\necho CAPABILITY_OK\n',encoding="utf-8")
            else:
                launcher.write_text('#!/bin/sh\necho CAPABILITY_OK\n',encoding="utf-8")
                launcher.chmod(0o755)

            install=root/"environment"/launcher.name
            manifest=root/"environment.json"
            plan=plan_portable_capability(
                "make demo capability available","demo.echo","portable-echo",
                launcher,install.parent,"demo-automation"
            )

            # PLAN is read-only.
            self.assertFalse(plan.explain()["mutates_environment"])
            self.assertTrue(plan.explain()["would_modify_environment"])
            self.assertFalse(install.exists())

            # APPLY is blocked until authorization.
            blocked=apply_portable_plan(plan,manifest,authorized=False)
            self.assertEqual(blocked["status"],"authorization_required")
            self.assertFalse(install.exists())

            # Authorized APPLY must acquire and verify.
            applied=apply_portable_plan(plan,manifest,authorized=True)
            self.assertTrue(applied["ok"])
            if sys.platform!="win32":
                install.chmod(0o755)
            self.assertTrue(install.exists())

            # Ownership and consumer are durable state.
            env=json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(env["providers"]["portable-echo"]["installed_by"],"autocompiler")
            self.assertIn("demo-automation",env["providers"]["portable-echo"]["consumers"])

            # Generated consumer runs without importing AutoCompiler.
            artifact=compile_independent_consumer(install,root/"generated")
            run=subprocess.run([sys.executable,str(artifact)],text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(run.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["provider_output"],"CAPABILITY_OK")
            self.assertFalse(result["autocompiler_runtime_used"])
            self.assertFalse(result["recurring_ai_used"])

if __name__=="__main__":
    unittest.main()
