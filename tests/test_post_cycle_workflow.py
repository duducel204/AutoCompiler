from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "post-cycle-spider.yml"


class PostCycleSpiderWorkflowTests(unittest.TestCase):
    def test_workflow_runs_only_after_trusted_main_cycle_or_manual_dispatch(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_run:", text)
        self.assertIn('workflows: ["AutoCompiler Trust Gate"]', text)
        self.assertIn("types: [completed]", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)

    def test_workflow_restores_graph_runs_spider_and_publishes_next_cycle_context(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/cache/restore@v4", text)
        self.assertIn("node-context-main-v2-", text)
        self.assertIn("hashFiles('scripts/node_context_index.py', 'scripts/node_context_spider.py', 'scripts/post_cycle_spider.py')", text)
        self.assertIn("scripts/post_cycle_spider.py", text)
        self.assertIn(".autocompiler/node_context_graph.json", text)
        self.assertIn(".autocompiler/post_cycle_context.json", text)
        self.assertIn("actions/cache/save@v4", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("post-cycle-context-", text)
        self.assertIn("scripts/next_cycle_plan.py", text)
        self.assertIn(".autocompiler/next_cycle.json", text)
        self.assertIn(".autocompiler/next_cycle_run.json", text)


if __name__ == "__main__":
    unittest.main()
