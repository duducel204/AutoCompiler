import json, tempfile, unittest
from pathlib import Path
from src.autocompiler.engine import execute
from src.autocompiler.triggers import cron_line, windows_task_command

class B2B3Tests(unittest.TestCase):
    def test_b2_schedule_http_transform_store_with_retry_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            ir=json.loads(Path("examples/b2-schedule-http.ir.json").read_text())
            calls=[]
            def fake_http(method,url,body,retries):
                calls.append((method,url,retries)); return {"value": 42}
            result=execute(ir,{"url":"http://example.invalid/data"},root,fake_http)
            self.assertEqual(result["context"]["mapped"]["value"],42)
            self.assertEqual(calls,[("GET","http://example.invalid/data",2)])
            self.assertEqual(json.loads((root/"events.jsonl").read_text().splitlines()[0])["source"],"scheduled-http")
            self.assertIn("schtasks.exe",windows_task_command("AutoCompiler-B2","python","automation.py"))
            self.assertIn("0 9 * * *",cron_line("python","automation.py"))

    def test_b3_webhook_condition_branch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            ir=json.loads(Path("examples/b3-webhook-branch.ir.json").read_text())
            no_http=lambda *args: self.fail("B3 should not call HTTP")
            high=execute(ir,{"amount":150},root,no_http)
            normal=execute(ir,{"amount":20},root,no_http)
            self.assertEqual(high["context"]["decision"]["route"],"high")
            self.assertEqual(normal["context"]["decision"]["route"],"normal")
            rows=[json.loads(x) for x in (root/"webhook-events.jsonl").read_text().splitlines()]
            self.assertEqual([r["route"] for r in rows],["high","normal"])

if __name__=="__main__":
    unittest.main()
