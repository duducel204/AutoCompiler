import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from autocompiler.standalone import compile_folder_watch

class StandaloneTests(unittest.TestCase):
    def test_generated_automation_runs_without_autocompiler(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); src=base/"in"; dst=base/"out"; gen=base/"generated"
            src.mkdir(); (src/"hello.txt").write_text("proof",encoding="utf-8")
            compile_folder_watch(str(src),str(dst),gen)
            # Generated program runs as a separate process and imports no AutoCompiler package.
            p=subprocess.run([sys.executable,str(gen/"automation.py")],cwd=str(gen),capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual((dst/"hello.txt").read_text(encoding="utf-8"),"proof")
            self.assertTrue((gen/"history.db").exists())
            with sqlite3.connect(gen/"history.db") as con:
                self.assertEqual(con.execute("select status from events").fetchone()[0],"ok")
            self.assertNotIn("autocompiler", (gen/"automation.py").read_text(encoding="utf-8").lower())

if __name__=="__main__":
    unittest.main()
