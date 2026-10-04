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

    def test_w05_compiled_standalone_execution(self):
        import subprocess, sys
        from src.autocompiler.compiler import compile_ir

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "input.csv"
            xlsx_path = root / "output.xlsx"
            csv_path.write_text("name,role\nAlice,admin\nBob,user\n", encoding="utf-8")

            ir = {
                "schema_version": "0.3",
                "name": "W05 Compiled Transform",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "step1",
                        "skill": "csv.read",
                        "with": {"path": str(csv_path)},
                    },
                    {
                        "id": "step2",
                        "skill": "xlsx.write",
                        "with": {"path": str(xlsx_path), "rows": "$step1.rows"},
                    },
                    {
                        "id": "step3",
                        "skill": "xlsx.read",
                        "with": {"path": str(xlsx_path)},
                    },
                ],
            }

            out_dir = root / "compiled_w05"
            compile_ir(ir, "python-sqlite", out_dir)

            proc = subprocess.run(
                [sys.executable, str(out_dir / "automation.py")],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            res = json.loads(proc.stdout)
            self.assertTrue(res["ok"])
            self.assertFalse(res["autocompiler_runtime_used"])
            self.assertEqual(
                res["context"]["step3"]["rows"],
                [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}],
            )

    def test_policy_cost_selection(self):
        from src.autocompiler.provisioning import CapabilityRegistry

        registry = CapabilityRegistry()
        resource_graph = {
            "resources": [
                {"capability": "http.request", "provider": "paid_provider", "state": "usable", "cost": "paid"},
                {"capability": "http.request", "provider": "free_provider", "state": "usable", "cost": "free"},
            ]
        }
        plan_out = registry.resolve(["http.request"], resource_graph)
        res = plan_out.resolutions[0]
        self.assertEqual(res.provider, "free_provider")
        self.assertIn("Selected among 2 candidates using lowest cost policy (free)", res.reason)

    def test_engine_fallback_execution(self):
        ir = {
            "schema_version": "0.3",
            "name": "Fallback Test",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "step1",
                    "skill": "filesystem.read",
                    "with": {"path": "/nonexistent_file_xyz_12345.txt"},
                    "error_policy": {
                        "retries": 0,
                        "fallback": {
                            "skill": "notify",
                            "with": {"title": "Fallback Triggered", "message": "Using fallback notification"},
                        },
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            res = execute(ir, {}, root)
            self.assertTrue(res["context"]["step1"]["fallback_executed"])
            self.assertTrue(res["context"]["step1"]["fallback_result"]["delivered"])


if __name__ == "__main__":
    unittest.main()
