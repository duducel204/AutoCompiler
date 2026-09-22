import json, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path
from src.autocompiler.compiler import compile_ir
from src.autocompiler.ir import validate_ir

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
                    with sqlite3.connect(out/"history.db") as con:
                        self.assertEqual(con.execute("select status from events").fetchone()[0],"ok")
                else:
                    row=json.loads((out/"history.jsonl").read_text(encoding="utf-8").splitlines()[0])
                    self.assertEqual(row["status"],"ok")

if __name__=="__main__":
    unittest.main()
