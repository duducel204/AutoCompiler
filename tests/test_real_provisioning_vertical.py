import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.provisioning_vertical import plan_portable_capability, apply_portable_plan, compile_independent_consumer

class RealProvisioningVerticalTests(unittest.TestCase):
    def test_missing_capability_plan_apply_verify_compile_independent_run(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/"catalog"/"provider.py"
            source.parent.mkdir()
            source.write_text("#!/usr/bin/env python3\nprint('CAPABILITY_OK')\n",encoding="utf-8")
            # Use a platform-neutral executable launcher so CI proves the same semantic flow on Windows/Linux.
            launcher=root/"catalog"/("provider.cmd" if sys.platform=="win32" else "provider")
            if sys.platform=="win32":
                launcher.write_text(f'@echo off\n"{sys.executable}" "{source}"\n',encoding="utf-8")
            else:
                launcher.write_text(f'#!/bin/sh\n"{sys.executable}" "{source}"\n',encoding="utf-8")
                launcher.chmod(0o755)
            install=root/"environment"/launcher.name
            manifest=root/"environment.json"
            # The acquired provider is the launcher; keep its payload adjacent so the portable unit is self-contained.\n            payload_installed=root/"environment"/source.name\n            payload_installed.parent.mkdir(parents=True,exist_ok=True)\n            payload_installed.write_bytes(source.read_bytes())\n            plan=plan_portable_capability("make demo capability available","demo.echo","portable-echo",launcher,install.parent,"demo-automation")
            self.assertFalse(plan.explain()["mutates_environment"])
            self.assertFalse(install.exists())
            blocked=apply_portable_plan(plan,manifest,authorized=False)
            self.assertEqual(blocked["status"],"authorization_required")
            self.assertFalse(install.exists())
            applied=apply_portable_plan(plan,manifest,authorized=True)
            self.assertTrue(applied["ok"])
            if sys.platform!="win32": install.chmod(0o755)
            self.assertTrue(install.exists())
            env=json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(env["providers"]["portable-echo"]["installed_by"],"autocompiler")
            artifact=compile_independent_consumer(install,root/"generated")
            run=subprocess.run([sys.executable,str(artifact)],text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(run.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["provider_output"],"CAPABILITY_OK")
            self.assertFalse(result["autocompiler_runtime_used"])
            self.assertFalse(result["recurring_ai_used"])

if __name__=="__main__": unittest.main()
