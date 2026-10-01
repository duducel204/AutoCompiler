import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.engine import execute
from src.autocompiler.providers import StateCheckProvider, StateUpdateProvider


class StateDeduplicationTests(unittest.TestCase):
    def test_state_check_and_update_providers(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "state.db"
            check_p = StateCheckProvider()
            update_p = StateUpdateProvider()

            # Unseen key
            c1 = check_p.execute({"db": str(db_path), "key": "item_123"})
            self.assertTrue(c1["ok"])
            self.assertFalse(c1["seen"])

            # Update key
            u1 = update_p.execute({"db": str(db_path), "key": "item_123", "val": "processed"})
            self.assertTrue(u1["ok"])
            self.assertTrue(u1["updated"])

            # Check key again
            c2 = check_p.execute({"db": str(db_path), "key": "item_123"})
            self.assertTrue(c2["ok"])
            self.assertTrue(c2["seen"])

    def test_engine_state_deduplication_flow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ir = {
                "schema_version": "0.1",
                "name": "State Deduplication Test",
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "check_step",
                        "skill": "state.check",
                        "with": {"key": "$event.item_id", "file": "dedup.db"},
                    },
                    {
                        "id": "update_step",
                        "skill": "state.update",
                        "with": {"key": "$event.item_id", "val": "processed", "file": "dedup.db"},
                    },
                ],
            }

            # First execution -> item_001
            res1 = execute(ir, {"item_id": "item_001"}, root, None)
            self.assertFalse(res1["context"]["check_step"]["seen"])
            self.assertTrue(res1["context"]["update_step"]["updated"])

            # Second execution -> item_001 again
            res2 = execute(ir, {"item_id": "item_001"}, root, None)
            self.assertTrue(res2["context"]["check_step"]["seen"])

            # Query database history
            db_file = root / "dedup.db"
            con = sqlite3.connect(db_file)
            try:
                rows = con.execute("SELECT item_key, val FROM seen_items").fetchall()
            finally:
                con.close()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "item_001")


if __name__ == "__main__":
    unittest.main()
