import json, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.compiler import analyze_compile_support, compile_ir
from src.autocompiler.ir import validate_ir, load_ir

class IRCompilerTest(unittest.TestCase):
    def make_ir(self, root: Path, state_file: str):
        source, destination = root/"input", root/"output"
        source.mkdir()
        (source/"keep.txt").write_text("proof", encoding="utf-8")
        (source/"skip.pdf").write_text("skip", encoding="utf-8")
        return {
            "schema_version":"0.1","name":"b1","trigger":{"type":"manual"},
            "steps":[
                {"id":"scan","skill":"filesystem.scan","with":{"path":str(source),"glob":"*"},"permissions":[{"mode":"read","path":str(source)}]},
                {"id":"filter","skill":"filter.extension","with":{"from":"scan","extension":".txt"}},
                {"id":"copy","skill":"filesystem.copy","with":{"from":"filter","destination":str(destination)},"permissions":[{"mode":"write","path":str(destination)}]},
                {"id":"history","skill":"state.record","with":{"from":"copy"},"permissions":[{"mode":"write","path":"state"}]}
            ],"state":{"file":state_file}
        }

    def test_b1_same_ir_semantics_two_targets(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for target,state in (("python-sqlite","history.db"),("python-json","history.jsonl")):
                case=root/target; case.mkdir()
                ir=self.make_ir(case,state)
                validation=validate_ir(ir)
                self.assertIn("durable_state",validation.required_capabilities)
                out=case/"generated"
                manifest=compile_ir(ir,target,out)
                self.assertFalse(manifest["recurring_ai_required"])
                proc=subprocess.run([sys.executable,str(out/"automation.py")],capture_output=True,text=True,check=True)
                result=json.loads(proc.stdout)
                self.assertEqual(result["processed"],1)
                self.assertTrue((case/"output"/"keep.txt").exists())
                self.assertFalse((case/"output"/"skip.pdf").exists())
                generated = (out/"automation.py").read_text(encoding="utf-8").lower()
                self.assertNotIn("import autocompiler", generated)
                self.assertNotIn("from autocompiler", generated)
                self.assertFalse(result["autocompiler_runtime_used"])
                if target=="python-sqlite":
                    con = sqlite3.connect(out/"history.db")
                    try:
                        self.assertEqual(con.execute("select status from events").fetchone()[0],"ok")
                    finally:
                        con.close()
                else:
                    row=json.loads((out/"history.jsonl").read_text(encoding="utf-8").splitlines()[0])
                    self.assertEqual(row["status"],"ok")

    def test_schema_0_3_w01_instant_workflow_valid(self):
        w01_path = Path("examples/w01-instant-workflow.ir.json")
        ir = load_ir(w01_path)
        validation = validate_ir(ir)
        self.assertEqual(ir["schema_version"], "0.3")
        self.assertIsInstance(validation.required_capabilities, list)
        self.assertIn("webhook.receive", validation.required_capabilities)
        self.assertIn("notification.send", validation.required_capabilities)

    def test_schema_0_3_w10_persistent_workflow_valid(self):
        w10_path = Path("examples/w10-persistent-workflow.ir.json")
        ir = load_ir(w10_path)
        validation = validate_ir(ir)
        self.assertEqual(ir["schema_version"], "0.3")
        self.assertIn("durable_state", validation.required_capabilities)
        self.assertIn("wait", validation.required_capabilities)
        self.assertIn("continuation", validation.required_capabilities)
        self.assertIn("retry", validation.required_capabilities)
        self.assertIn("timeout", validation.required_capabilities)
        self.assertIn("fallback", validation.required_capabilities)
        self.assertIn("event.receive", validation.required_capabilities)
        step_types = [step.get("type") for step in ir["steps"]]
        self.assertIn("wait", step_types)
        self.assertIn("continue", step_types)

    def test_schedule_and_http_use_canonical_capability_vocabulary(self):
        ir = {
            "schema_version": "0.3",
            "name": "scheduled-http",
            "trigger": {"type": "schedule", "cron": "0 18 * * *"},
            "steps": [
                {"id": "fetch", "skill": "http.request", "with": {"url": "https://example.com"}},
            ],
        }
        validation = validate_ir(ir)
        self.assertIn("schedule", validation.required_capabilities)
        self.assertIn("http.request", validation.required_capabilities)
        self.assertNotIn("http.client", validation.required_capabilities)
        self.assertIn("trigger:schedule", validation.capability_sources["schedule"])

    def test_compiler_requires_a_materializable_resolved_http_provider(self):
        ir = {
            "schema_version": "0.3",
            "name": "http-only",
            "trigger": {"type": "manual"},
            "steps": [{"id": "fetch", "skill": "http.request", "with": {"url": "https://example.com"}}],
        }
        wrong = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {"capability": "http.request", "provider": "custom-http", "status": "resolved"}
            ],
        }
        support = analyze_compile_support(ir, "python-sqlite", wrong)
        self.assertFalse(support["supported"])
        self.assertEqual(support["provider_mismatches"][0]["capability"], "http.request")

        right = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {"capability": "http.request", "provider": "autocompiler.http_provider", "status": "resolved"}
            ],
        }
        self.assertTrue(analyze_compile_support(ir, "python-sqlite", right)["supported"])

    def test_xlsx_read_and_write_standalone_compilation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "generated"
            xlsx_write_path = root / "data.xlsx"

            ir = {
                "schema_version": "0.3",
                "name": "xlsx-flow",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "write",
                        "skill": "xlsx.write",
                        "with": {
                            "path": str(xlsx_write_path),
                            "rows": [{"col1": "val1", "col2": "val2"}],
                        },
                    },
                    {
                        "id": "read",
                        "skill": "xlsx.read",
                        "with": {"path": str(xlsx_write_path)},
                    },
                ],
            }

            resolved = {
                "requirements": [
                    {"capability": "xlsx.write", "provider": "python-stdlib-xlsx", "status": "resolved"},
                    {"capability": "xlsx.read", "provider": "python-stdlib-xlsx", "status": "resolved"},
                ]
            }

            support = analyze_compile_support(ir, "python-sqlite", resolved)
            self.assertTrue(support["supported"], support)

            compile_ir(ir, "python-sqlite", out, resolved_execution=resolved)
            proc = subprocess.run([sys.executable, str(out / "automation.py")], capture_output=True, text=True, check=True)
            res = json.loads(proc.stdout)
            self.assertTrue(res["ok"])
            read_ctx = res["context"]["read"]
            self.assertTrue(read_ctx["ok"])
            self.assertEqual(len(read_ctx["rows"]), 1)
            self.assertEqual(read_ctx["rows"][0], {"col1": "val1", "col2": "val2"})

    def test_schema_malformed_workflows_rejected(self):
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "99.0", "name": "bad", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "get"}]})

        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "get"}]})

        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {}, "steps": [{"id": "s1", "type": "get"}]})

        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {"type": "magic"}, "steps": [{"id": "s1", "type": "get"}]})

        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "unknown_primitive"}]})

if __name__=="__main__":
    unittest.main()
