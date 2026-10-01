import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.providers import (
    CSVReadProvider,
    CSVWriteProvider,
    XLSXReadProvider,
    XLSXWriteProvider,
    ScheduleProvider,
    FilesystemReadProvider,
    FilesystemWriteProvider,
    PDFDetectProvider,
    PDFBasicTextProvider,
    TextMatchProvider,
    TextParseProvider,
    NotificationSendProvider,
    ProcessExecuteAuthorizedProvider,
    ContinuationProvider,
    WaitProvider,
    get_provider_for_capability,
)
from autocompiler.provisioning import CapabilityRegistry


class CapabilityContractsTests(unittest.TestCase):
    def test_filesystem_read_write_providers(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            write_prov = FilesystemWriteProvider()
            read_prov = FilesystemReadProvider()

            file_path = tmp / "test.txt"
            res = write_prov.execute({"action": "write", "path": str(file_path), "content": "Hello World"})
            self.assertTrue(res["ok"])

            res = read_prov.execute({"action": "read", "path": str(file_path)})
            self.assertTrue(res["ok"])
            self.assertEqual(res["content"], "Hello World")

            res = read_prov.execute({"action": "exists", "path": str(file_path)})
            self.assertTrue(res["exists"])

    def test_csv_read_write_providers(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            csv_path = tmp / "data.csv"
            w_prov = CSVWriteProvider()
            r_prov = CSVReadProvider()

            rows = [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}]
            res = w_prov.execute({"path": str(csv_path), "rows": rows})
            self.assertTrue(res["ok"])

            res = r_prov.execute({"path": str(csv_path)})
            self.assertTrue(res["ok"])
            self.assertEqual(res["rows"], rows)

    def test_xlsx_read_write_providers(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xlsx_path = tmp / "data.xlsx"
            w_prov = XLSXWriteProvider()
            r_prov = XLSXReadProvider()

            rows = [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}]
            res = w_prov.execute({"path": str(xlsx_path), "rows": rows})
            self.assertTrue(res["ok"])

            res = r_prov.execute({"path": str(xlsx_path)})
            self.assertTrue(res["ok"])
            self.assertEqual(res["rows"], rows)

    def test_schedule_provider(self):
        prov = ScheduleProvider()
        health = prov.health_check()
        self.assertTrue(health["ok"])

        res = prov.execute({"name": "TestTask", "python_bin": "python3", "script_path": "main.py"})
        self.assertTrue(res["ok"])
        self.assertIn("schtasks.exe", res["windows_task_command"])
        self.assertIn("0 9 * * *", res["cron_line"])

    def test_registry_policy_selection(self):
        registry = CapabilityRegistry()
        graph = {
            "resources": [
                {"capability": "http.request", "provider": "custom_http", "state": "usable", "cost": "free"},
                {"capability": "http.request", "provider": "premium_http", "state": "usable", "cost": "paid"},
            ]
        }
        res_default = registry.resolve(["http.request"], graph)
        self.assertEqual(res_default.resolutions[0].provider, "custom_http")

        res_pref = registry.resolve(["http.request"], graph, constraints={"prefer_provider": "premium_http"})
        self.assertEqual(res_pref.resolutions[0].provider, "premium_http")

    def test_pdf_detect_provider(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            pdf_path = tmp / "doc.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%...\n")
            txt_path = tmp / "doc.txt"
            txt_path.write_text("not a pdf")

            prov = PDFDetectProvider()
            self.assertTrue(prov.execute({"path": str(pdf_path)})["is_pdf"])
            self.assertFalse(prov.execute({"path": str(txt_path)})["is_pdf"])

    def test_text_parse_and_match_providers(self):
        parse_prov = TextParseProvider()
        match_prov = TextMatchProvider()

        parsed = parse_prov.execute({"text": "line1\nline2", "mode": "lines"})
        self.assertEqual(parsed["result"], ["line1", "line2"])

        matched = match_prov.execute({"text": "hello 123 world", "pattern": r"\d+", "mode": "regex"})
        self.assertTrue(matched["matched"])
        self.assertEqual(matched["matches"], ["123"])

    def test_process_execute_authorized_provider(self):
        prov = ProcessExecuteAuthorizedProvider()
        unauth = prov.execute({"command": [sys.executable, "-c", "print('hi')"]})
        self.assertFalse(unauth["ok"])
        self.assertEqual(unauth["status"], "authorization_required")

        auth = prov.execute({"command": [sys.executable, "-c", "print('hi')"], "authorized": True})
        self.assertTrue(auth["ok"])
        self.assertIn("hi", auth["stdout"])

    def test_continuation_provider(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            state_file = tmp / "continuation.json"
            prov = ContinuationProvider()

            res = prov.execute({"action": "save", "file": str(state_file), "state": {"step": 2, "user": "test"}})
            self.assertTrue(res["ok"])

            res = prov.execute({"action": "load", "file": str(state_file)})
            self.assertTrue(res["ok"])
            self.assertEqual(res["state"]["step"], 2)

    def test_registry_explain_capability(self):
        registry = CapabilityRegistry()
        graph = {
            "resources": [
                {"capability": "filesystem.read", "provider": "python-stdlib-filesystem", "state": "usable"},
                {"capability": "browser", "provider": "chrome", "state": "detected"},
            ]
        }

        usable_exp = registry.explain_capability("filesystem.read", graph)
        self.assertTrue(usable_exp["available"])
        self.assertEqual(usable_exp["state"], "usable")

        detected_exp = registry.explain_capability("browser", graph)
        self.assertFalse(detected_exp["available"])
        self.assertEqual(detected_exp["state"], "detected")

        builtin_exp = registry.explain_capability("csv.read", graph)
        self.assertTrue(builtin_exp["available"])
        self.assertEqual(builtin_exp["provider"], "python-stdlib-csv")

        missing_exp = registry.explain_capability("nonexistent.capability", graph)
        self.assertFalse(missing_exp["available"])
        self.assertEqual(missing_exp["state"], "missing")


if __name__ == "__main__":
    unittest.main()
