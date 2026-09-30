import json, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.compiler import compile_ir
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

    def test_schema_0_3_w10_persistent_workflow_valid(self):
        w10_path = Path("examples/w10-persistent-workflow.ir.json")
        ir = load_ir(w10_path)
        validation = validate_ir(ir)
        self.assertEqual(ir["schema_version"], "0.3")
        self.assertIn("durable_state", validation.required_capabilities)
        step_types = [step.get("type") for step in ir["steps"]]
        self.assertIn("wait", step_types)
        self.assertIn("continue", step_types)

    def test_schema_malformed_workflows_rejected(self):
        # Unsupported schema version
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "99.0", "name": "bad", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "get"}]})

        # Missing name
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "get"}]})

        # Missing trigger type
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {}, "steps": [{"id": "s1", "type": "get"}]})

        # Unsupported trigger type
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {"type": "magic"}, "steps": [{"id": "s1", "type": "get"}]})

        # Unsupported skill/type in step
        with self.assertRaises(ValueError):
            validate_ir({"schema_version": "0.3", "name": "bad", "trigger": {"type": "manual"}, "steps": [{"id": "s1", "type": "unknown_primitive"}]})

if __name__=="__main__":
    unittest.main()
