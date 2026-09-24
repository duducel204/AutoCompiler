import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.provisioning import CapabilityRegistry


class CapabilityCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.catalog = CapabilityCatalog(Path(self.tmp.name) / "catalog.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_candidate_is_not_reusable_before_validation(self):
        self.catalog.register_candidate(
            "messaging.whatsapp.receive",
            "whatsapp-cloud-api",
            "1.0.0",
            ("tests/contracts/test_whatsapp_receive.py",),
            rollback="remove provider registration",
        )
        self.assertEqual(self.catalog.validated(), [])
        plan = CapabilityRegistry().resolve(
            ["messaging.whatsapp.receive"],
            self.catalog.resource_graph(),
        )
        self.assertEqual(plan.resolutions[0].action, "unresolved")

    def test_validated_candidate_becomes_reusable_provider(self):
        self.catalog.register_candidate(
            "messaging.whatsapp.receive",
            "whatsapp-cloud-api",
            "1.0.0",
            ("tests/contracts/test_whatsapp_receive.py",),
            permissions=("network.whatsapp",),
            rollback="remove provider registration",
        )
        self.catalog.promote(
            "messaging.whatsapp.receive",
            "whatsapp-cloud-api",
            ("github-actions:contract-tests:passed",),
        )
        plan = CapabilityRegistry().resolve(
            ["messaging.whatsapp.receive"],
            self.catalog.resource_graph(),
        )
        resolution = plan.resolutions[0]
        self.assertEqual(resolution.action, "reuse")
        self.assertEqual(resolution.provider, "whatsapp-cloud-api")

    def test_validated_resource_binding_is_persisted_and_exported(self):
        self.catalog.register_candidate(
            "vault.write",
            "obsidian-local-vault",
            "0.1.0",
            ("tests/test_vault_provider.py",),
            permissions=("filesystem.vault",),
            rollback="remove local registration",
            binding={"root": "C:/Vault"},
        )
        self.catalog.promote(
            "vault.write",
            "obsidian-local-vault",
            ("local:binding:verified",),
        )
        resource = self.catalog.resource_graph()["resources"][0]
        self.assertEqual(resource["binding"], {"root": "C:/Vault"})
        resolution = CapabilityRegistry().resolve(
            ["vault.write"],
            self.catalog.resource_graph(),
        ).resolutions[0]
        self.assertEqual(resolution.binding, {"root": "C:/Vault"})

    def test_promotion_without_evidence_is_rejected(self):
        self.catalog.register_candidate(
            "example.capability",
            "example-provider",
            "1.0.0",
            ("tests/contracts/test_example.py",),
            rollback="remove registration",
        )
        with self.assertRaises(ValueError):
            self.catalog.promote("example.capability", "example-provider", ())

    def test_validated_capability_requires_rollback(self):
        self.catalog.register_candidate(
            "example.capability",
            "example-provider",
            "1.0.0",
            ("tests/contracts/test_example.py",),
        )
        with self.assertRaises(ValueError):
            self.catalog.promote(
                "example.capability",
                "example-provider",
                ("ci:passed",),
            )


if __name__ == "__main__":
    unittest.main()
