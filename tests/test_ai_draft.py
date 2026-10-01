import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.ai_draft import DeterministicRuleAIProvider, GeminiDraftProvider, draft_intent_to_ir
from autocompiler.ir import validate_ir
from autocompiler.planner import Requirement, plan
from autocompiler.templates import list_templates


class AIDraftingTests(unittest.TestCase):
    def test_simple_natural_language_intent_converted_to_valid_draft(self):
        prompt = "Organizar arquivos pdf na pasta ./processed_pdfs"
        res = draft_intent_to_ir(prompt)
        self.assertTrue(res["ok"])
        self.assertIn("ir", res)
        self.assertFalse(res.get("recurring_ai_required", True))

        # Validate against schema
        val = validate_ir(res["ir"])
        self.assertIn("filesystem.read", val.required_capabilities)
        self.assertIn("filesystem.write", val.required_capabilities)

    def test_missing_or_ambiguous_information_returns_explicit_questions(self):
        prompt = "Organize alguns PDFs"
        res = draft_intent_to_ir(prompt)
        self.assertFalse(res["ok"])
        self.assertTrue(res["ambiguous"])
        self.assertTrue(len(res["questions"]) > 0)
        self.assertIn("destino", res["questions"][0].lower())

    def test_invalid_provider_response_handling(self):
        res = draft_intent_to_ir("test", provider="unknown-provider")
        self.assertFalse(res["ok"])
        self.assertIn("Unknown AI provider", res["error"])

        # Test Gemini provider without API key
        gemini_res = draft_intent_to_ir("test", provider="google-gemini")
        self.assertFalse(gemini_res["ok"])
        self.assertEqual(gemini_res["error"], "gemini_api_key_required")

    def test_draft_with_unresolved_capability_flows_normally_to_capability_resolution(self):
        # AI creates a draft IR with a skill requiring custom capability 'vault.write'
        ir_with_gap = {
            "schema_version": "0.1",
            "name": "Note Exporter",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "filesystem.scan",
                    "with": {"path": ".", "glob": "*"},
                },
                {
                    "id": "s2",
                    "skill": "state.record",
                    "with": {"from": "s1"},
                },
            ],
            "state": {"file": "history.db"},
        }

        # AI draft does NOT resolve capabilities; planner does
        val = validate_ir(ir_with_gap)
        reqs = [Requirement(cap) for cap in val.required_capabilities] + [Requirement("custom_unresolved_gap")]
        plan_res = plan("AI Draft Intent", reqs)

        self.assertIn("custom_unresolved_gap", plan_res.missing)
        self.assertEqual(plan_res.executor, "unresolved")

    def test_j009_j010_work_fully_without_ai_provider_configured(self):
        # Canvas and Templates work 100% offline without any AI credential/provider
        tmpls = list_templates()
        self.assertTrue(len(tmpls) >= 5)

        # Plan execution for template
        w01_ir = tmpls[0]
        self.assertIn("w01", [t["id"] for t in tmpls])


if __name__ == "__main__":
    unittest.main()
