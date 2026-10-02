from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "development-cycle.yml"
TRUST_WORKFLOW = ROOT / ".github" / "workflows" / "trust-gate.yml"


class DevelopmentCycleWorkflowTests(unittest.TestCase):
    def test_dispatcher_runs_only_after_successful_main_spider_or_manual(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('workflows: ["Post-cycle Spider"]', text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", text)
        self.assertIn("workflow_dispatch:", text)

    def test_workflow_is_read_only_and_emits_dispatch_artifact(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("scripts/development_cycle_dispatch.py", text)
        self.assertIn("data/development_executors.json", text)
        self.assertIn("development_cycle_dispatch.json", text)
        self.assertIn("actions/upload-artifact@v4", text)

    def test_trust_gate_publishes_structured_failure_context(self):
        text = TRUST_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: failure()", text)
        self.assertIn(".autocompiler/ci_failure_context.json", text)
        self.assertIn("trust-gate-failure-", text)


if __name__ == "__main__":
    unittest.main()
