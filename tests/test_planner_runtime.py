import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.planner import Requirement, plan
from autocompiler.runtime import execute


class PlannerRuntimeTests(unittest.TestCase):
    def test_canonical_memory_is_reused_without_manual_provider_list(self):
        with tempfile.TemporaryDirectory() as td:
            local_catalog = Path(td) / "capabilities.json"
            result = plan(
                "run a local deterministic automation",
                [Requirement("run_python"), Requirement("durable_state")],
                {"capabilities": []},
                local_catalog_path=local_catalog,
            )
        self.assertEqual(result.providers["run_python"], "python")
        self.assertEqual(result.providers["durable_state"], "sqlite")
        self.assertEqual(result.missing, [])
        self.assertTrue(any("Memory reuse:" in note for note in result.notes))

    def test_legacy_state_name_resolves_to_canonical_durable_state(self):
        with tempfile.TemporaryDirectory() as td:
            result = plan(
                "persist state",
                [Requirement("state")],
                {"capabilities": []},
                local_catalog_path=Path(td) / "none.json",
            )
        self.assertEqual(result.providers["state"], "sqlite")
        self.assertEqual(result.missing, [])

    def test_resource_bound_capability_requires_validated_local_binding(self):
        with tempfile.TemporaryDirectory() as td:
            catalog_path = Path(td) / "capabilities.json"
            unbound = plan(
                "write a vault note",
                [Requirement("vault.write")],
                {"capabilities": []},
                local_catalog_path=catalog_path,
            )
            self.assertEqual(unbound.missing, ["vault.write"])

            catalog = CapabilityCatalog(catalog_path)
            catalog.register_candidate(
                "vault.write",
                "obsidian-local-vault",
                "0.1.0",
                ("tests/test_vault_provider.py",),
                permissions=("filesystem.vault",),
                rollback="remove local capability registration; never delete vault content",
            )
            catalog.promote(
                "vault.write",
                "obsidian-local-vault",
                ("local:contract-only:verified",),
            )

            contract_only = plan(
                "write a vault note",
                [Requirement("vault.write")],
                {"capabilities": []},
                local_catalog_path=catalog_path,
            )
            self.assertEqual(contract_only.missing, ["vault.write"])

            vault_root = str(Path(td) / "vault")
            catalog.register_candidate(
                "vault.write",
                "obsidian-local-vault",
                "0.1.0",
                ("tests/test_vault_provider.py",),
                permissions=("filesystem.vault",),
                rollback="remove local capability registration; never delete vault content",
                binding={"root": vault_root},
            )
            catalog.promote(
                "vault.write",
                "obsidian-local-vault",
                ("local:test-binding:verified",),
            )

            bound = plan(
                "write a vault note",
                [Requirement("vault.write")],
                {"capabilities": []},
                local_catalog_path=catalog_path,
            )
        self.assertEqual(bound.providers["vault.write"], "obsidian-local-vault")
        self.assertEqual(bound.bindings["vault.write"]["root"], vault_root)
        self.assertEqual(bound.missing, [])

    def test_detected_but_unvalidated_scheduler_is_not_reused(self):
        inventory = {
            "capabilities": [
                {
                    "id": "native_scheduler",
                    "detected": True,
                    "usable": "untested",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            result = plan(
                "schedule something",
                [Requirement("schedule")],
                inventory,
                local_catalog_path=Path(td) / "none.json",
            )
        self.assertEqual(result.missing, ["schedule"])
        self.assertNotIn("schedule", result.providers)

    def test_provider_fallback_without_git_remains_noncanonical(self):
        inventory = {"capabilities": [
            {"id": "python", "detected": True},
            {"id": "powershell", "detected": True},
            {"id": "git", "detected": False},
        ]}
        with tempfile.TemporaryDirectory() as td:
            result = plan(
                "obtain repository",
                [Requirement("repository")],
                inventory,
                local_catalog_path=Path(td) / "none.json",
            )
        self.assertEqual(result.providers["repository"], "http_download")
        self.assertFalse(result.recurring_ai_required)
        self.assertTrue(any("legacy acquisition fallback" in note for note in result.notes))

    def test_deterministic_recipe_runs_without_ai(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "proof.txt"
            db = Path(td) / "state.db"
            recipe = {
                "name": "proof",
                "steps": [{"id": "write", "action": "write_text", "args": {"path": str(target), "text": "ok"}}],
            }
            result = execute(recipe, str(db))
            self.assertEqual(target.read_text(encoding="utf-8"), "ok")
            self.assertFalse(result["recurring_ai_used"])


if __name__ == "__main__":
    unittest.main()
