import tempfile
import unittest
from pathlib import Path

from src.autocompiler.canvas_projector import (
    MANAGED_NODE_PREFIX,
    managed_node_id,
    project_repository_map,
    semantic_snapshot,
)
from src.autocompiler.canvas_protocol import load_canvas, save_canvas


FAKE_DISCOVERY = {
    "schema_version": "test",
    "machine": {"os": "Windows", "release": "11", "architecture": "AMD64"},
    "summary": {"detected": 2, "checked": 3},
    "capabilities": [
        {
            "id": "git",
            "detected": True,
            "installed": "yes",
            "accessible": "yes",
            "authorized": "unknown",
            "usable": "untested",
            "path": "C:/Program Files/Git/bin/git.exe",
            "version": "git version test",
            "notes": None,
            "providers": [],
        },
        {
            "id": "python",
            "detected": True,
            "installed": "yes",
            "accessible": "yes",
            "authorized": "unknown",
            "usable": "untested",
            "path": "C:/Python/python.exe",
            "version": "Python test",
            "notes": None,
            "providers": [],
        },
        {
            "id": "ollama",
            "detected": False,
            "installed": "unknown",
            "accessible": "unknown",
            "authorized": "unknown",
            "usable": "untested",
            "path": None,
            "version": None,
            "notes": None,
            "providers": [],
        },
    ],
}


def build_repo(root: Path) -> None:
    (root / "src" / "autocompiler").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src" / "autocompiler" / "discover.py").write_text("pass\n", encoding="utf-8")
    (root / "src" / "autocompiler" / "engine.py").write_text("pass\n", encoding="utf-8")
    (root / "tests" / "test_engine.py").write_text("pass\n", encoding="utf-8")
    (root / ".github" / "workflows" / "trust-gate.yml").write_text("name: Trust Gate\n", encoding="utf-8")
    (root / "docs" / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    (root / "README.md").write_text("# AutoCompiler\n", encoding="utf-8")


class CanvasProjectorTests(unittest.TestCase):
    def test_snapshot_exposes_semantic_layers_and_complete_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "AutoCompiler"
            repo.mkdir()
            build_repo(repo)

            snapshot = semantic_snapshot(repo, discovery=FAKE_DISCOVERY)

            self.assertEqual(
                {item["path"] for item in snapshot["core"]},
                {"src/autocompiler/discover.py", "src/autocompiler/engine.py"},
            )
            self.assertEqual(
                [item["path"] for item in snapshot["workflows"]],
                [".github/workflows/trust-gate.yml"],
            )
            self.assertEqual(
                [item["path"] for item in snapshot["tests"]],
                ["tests/test_engine.py"],
            )
            repository_paths = {item["path"] for item in snapshot["repository"]}
            self.assertIn("README.md", repository_paths)
            self.assertIn("docs/ARCHITECTURE.md", repository_paths)

    def test_projection_creates_one_card_per_capability_and_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "AutoCompiler"
            repo.mkdir()
            build_repo(repo)
            canvas = Path(tmp) / "AutoCompiler-Map.canvas"

            result = project_repository_map(canvas, repo, discovery=FAKE_DISCOVERY)
            data = load_canvas(canvas)
            node_ids = {node["id"] for node in data["nodes"]}

            self.assertIn(managed_node_id("capability", "git"), node_ids)
            self.assertIn(managed_node_id("capability", "python"), node_ids)
            self.assertIn(managed_node_id("capability", "ollama"), node_ids)
            self.assertIn(
                managed_node_id("workflow", ".github/workflows/trust-gate.yml"),
                node_ids,
            )
            self.assertGreater(result["managed_nodes"], 0)
            self.assertGreater(result["managed_edges"], 0)

    def test_reprojection_preserves_human_graph_and_managed_card_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "AutoCompiler"
            repo.mkdir()
            build_repo(repo)
            canvas = Path(tmp) / "AutoCompiler-Map.canvas"

            save_canvas(
                canvas,
                {
                    "nodes": [
                        {
                            "id": "human-a",
                            "type": "text",
                            "text": "minha ideia",
                            "x": -500,
                            "y": -500,
                            "width": 300,
                            "height": 160,
                        },
                        {
                            "id": "human-b",
                            "type": "text",
                            "text": "outro ramo",
                            "x": -100,
                            "y": -500,
                            "width": 300,
                            "height": 160,
                        },
                    ],
                    "edges": [
                        {"id": "human-edge", "fromNode": "human-a", "toNode": "human-b"}
                    ],
                },
            )

            project_repository_map(canvas, repo, discovery=FAKE_DISCOVERY)
            first = load_canvas(canvas)
            git_id = managed_node_id("capability", "git")
            git_node = next(node for node in first["nodes"] if node["id"] == git_id)
            git_node["x"] = 9999
            git_node["y"] = 8888
            first["edges"].append(
                {"id": "human-to-git", "fromNode": "human-a", "toNode": git_id}
            )
            save_canvas(canvas, first)

            project_repository_map(canvas, repo, discovery=FAKE_DISCOVERY)
            second = load_canvas(canvas)

            human_ids = {node["id"] for node in second["nodes"] if not node["id"].startswith(MANAGED_NODE_PREFIX)}
            self.assertEqual(human_ids, {"human-a", "human-b"})
            self.assertTrue(any(edge["id"] == "human-edge" for edge in second["edges"]))
            self.assertTrue(any(edge["id"] == "human-to-git" for edge in second["edges"]))

            git_nodes = [node for node in second["nodes"] if node["id"] == git_id]
            self.assertEqual(len(git_nodes), 1)
            self.assertEqual(git_nodes[0]["x"], 9999)
            self.assertEqual(git_nodes[0]["y"], 8888)

            managed_ids = [
                node["id"] for node in second["nodes"]
                if node["id"].startswith(MANAGED_NODE_PREFIX)
            ]
            self.assertEqual(len(managed_ids), len(set(managed_ids)))


if __name__ == "__main__":
    unittest.main()
