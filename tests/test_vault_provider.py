import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.vault_provider import CAPABILITIES, ObsidianVaultProvider


class ObsidianVaultProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".obsidian").mkdir()
        self.provider = ObsidianVaultProvider(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exposes_reusable_vault_capabilities(self):
        names = tuple(item.capability for item in self.provider.capabilities())
        self.assertEqual(names, CAPABILITIES)

    def test_write_read_and_search_stay_inside_vault(self):
        self.provider.write_text("Knowledge/note.md", "EurekAI bridge")
        self.assertEqual(
            self.provider.read_text("Knowledge/note.md"),
            "EurekAI bridge",
        )
        self.assertEqual(
            self.provider.search("EurekAI"),
            ["Knowledge\\note.md"] if sys.platform == "win32" else ["Knowledge/note.md"],
        )

    def test_path_escape_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.provider.write_text("../outside.md", "blocked")

    def test_verify_proves_write_reread_and_cleans_up(self):
        evidence = self.provider.verify()
        self.assertTrue(evidence["ok"])
        self.assertTrue(evidence["write_reread"])
        self.assertTrue(evidence["search_proof"])
        self.assertTrue(evidence["path_escape_blocked"])
        self.assertFalse((self.root / ".autocompiler").exists())


if __name__ == "__main__":
    unittest.main()
