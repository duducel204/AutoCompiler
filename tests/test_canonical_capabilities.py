import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.canonical_capabilities import (
    canonical_resource_graph,
    load_canonical_capabilities,
    resource_bound_capabilities,
    validate_contract_paths,
)
from autocompiler.provisioning import CapabilityRegistry


EXPECTED = {
    "environment.discover",
    "repository.inspect",
    "intent.compile",
    "filesystem.read",
    "filesystem.write",
    "durable_state",
    "run_python",
    "automation.compile",
    "automation.execute",
    "canvas.project",
    "vault.read",
    "vault.write",
    "vault.search",
}


class CanonicalCapabilitiesTests(unittest.TestCase):
    def test_registry_contains_only_audited_general_capabilities(self):
        payload = load_canonical_capabilities()
        names = {item["capability"] for item in payload["capabilities"]}
        self.assertEqual(names, EXPECTED)
        self.assertFalse(any(name.startswith("messaging.whatsapp") for name in names))
        validate_contract_paths(payload, ROOT)

    def test_builtin_capabilities_are_reusable(self):
        graph = canonical_resource_graph()
        names = {item["capability"] for item in graph["resources"]}
        self.assertEqual(
            names,
            EXPECTED - {"vault.read", "vault.write", "vault.search"},
        )
        plan = CapabilityRegistry().resolve(
            ["environment.discover", "filesystem.write", "automation.compile"],
            graph,
        )
        self.assertEqual([item.action for item in plan.resolutions], ["reuse", "reuse", "reuse"])

    def test_resource_bound_contracts_require_local_binding(self):
        bound = resource_bound_capabilities()
        self.assertEqual(
            {item["capability"] for item in bound},
            {"vault.read", "vault.write", "vault.search"},
        )
        graph = canonical_resource_graph()
        plan = CapabilityRegistry().resolve(["vault.write"], graph)
        self.assertEqual(plan.resolutions[0].action, "unresolved")


if __name__ == "__main__":
    unittest.main()
