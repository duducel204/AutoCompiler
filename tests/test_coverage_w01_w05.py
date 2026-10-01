import json
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.engine import execute


class WorkflowCoverageW01ToW05Tests(unittest.TestCase):
    """Verifies that representative workflows W-01 through W-05 execute successfully

    using common primitives without workflow-specific custom code.
    """

    def test_w01_organize_incoming_pdfs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdf_file = root / "sample.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n(Invoice #1001) Tj\n")
            target_dir = root / "processed_pdfs"

            ir = json.loads(Path("examples/w01-pdf-organizer.ir.json").read_text(encoding="utf-8"))
            event = {
                "file_path": str(pdf_file),
                "target_folder": str(target_dir),
            }

            res = execute(ir, event, root)
            self.assertTrue(res["context"]["detect_pdf"]["is_pdf"])
            self.assertTrue((target_dir / "sample.pdf").exists())

    def test_w02_scheduled_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "source"
            src_dir.mkdir()
            (src_dir / "file1.txt").write_text("file 1 content")
            (src_dir / "file2.txt").write_text("file 2 content")
            backup_dir = root / "backup"

            ir = json.loads(Path("examples/w02-scheduled-backup.ir.json").read_text(encoding="utf-8"))
            event = {
                "source_folder": str(src_dir),
                "backup_folder": str(backup_dir),
                "backup_id": "backup_2026_09_24",
            }

            res = execute(ir, event, root)
            self.assertTrue((backup_dir / "file1.txt").exists())
            self.assertTrue((backup_dir / "file2.txt").exists())
            self.assertEqual(res["context"]["record_backup"]["key"], "backup_2026_09_24")

    def test_w03_api_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_xlsx = root / "snapshot.xlsx"

            def mock_api_http(method, url, body, retries):
                return {
                    "items": [
                        {"id": "1", "product": "Widget A", "price": "10.00"},
                        {"id": "2", "product": "Widget B", "price": "20.00"},
                    ]
                }

            ir = json.loads(Path("examples/w03-api-snapshot.ir.json").read_text(encoding="utf-8"))
            event = {
                "api_url": "http://api.example.com/snapshot",
                "output_xlsx": str(out_xlsx),
                "snapshot_id": "snap_001",
            }

            res = execute(ir, event, root, mock_api_http)
            self.assertTrue(out_xlsx.exists())
            self.assertTrue(res["context"]["record_snapshot"]["updated"])

    def test_w04_change_monitor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def mock_change_http(method, url, body, retries):
                return {"hash": "v1_hash_abc"}

            ir = json.loads(Path("examples/w04-change-monitor.ir.json").read_text(encoding="utf-8"))
            event = {
                "monitor_key": "page_monitor_1",
                "target_url": "http://example.com/page",
            }

            # Run 1: initial state
            res1 = execute(ir, event, root, mock_change_http)
            self.assertFalse(res1["context"]["check_previous"]["seen"])
            self.assertEqual(res1["context"]["update_state"]["val"], "v1_hash_abc")

            # Run 2: seen
            res2 = execute(ir, event, root, mock_change_http)
            self.assertTrue(res2["context"]["check_previous"]["seen"])

    def test_w05_spreadsheet_transformation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "input.csv"
            xlsx_path = root / "output.xlsx"

            csv_path.write_text("name,role\nAlice,admin\nBob,user\n", encoding="utf-8")

            ir = json.loads(Path("examples/w05-spreadsheet-transform.ir.json").read_text(encoding="utf-8"))
            event = {
                "input_csv": str(csv_path),
                "output_xlsx": str(xlsx_path),
            }

            res = execute(ir, event, root)
            self.assertTrue(xlsx_path.exists())
            read_rows = res["context"]["read_back_xlsx"]["rows"]
            self.assertEqual(read_rows, [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}])


if __name__ == "__main__":
    unittest.main()
