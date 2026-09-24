import tempfile
import unittest
from pathlib import Path

from src.autocompiler.canvas_protocol import append_response, interaction_for, load_canvas, save_canvas


class CanvasProtocolTests(unittest.TestCase):
    def test_reads_parents_and_appends_connected_response(self):
        data = {
            "nodes": [
                {"id": "a", "type": "text", "text": "origem", "x": 0, "y": 0, "width": 400, "height": 200},
                {"id": "b", "type": "text", "text": "teste", "x": 500, "y": 0, "width": 400, "height": 200},
            ],
            "edges": [{"id": "e1", "fromNode": "a", "toNode": "b"}],
        }
        interaction = interaction_for(data, "b")
        self.assertEqual(interaction.text, "teste")
        self.assertEqual(interaction.parent_ids, ("a",))
        response_id = append_response(data, "b", "recebido", node_id="r1")
        self.assertEqual(response_id, "r1")
        self.assertTrue(any(n.get("id") == "r1" and n.get("text") == "recebido" for n in data["nodes"]))
        self.assertTrue(any(e.get("fromNode") == "b" and e.get("toNode") == "r1" for e in data["edges"]))

    def test_round_trip_json_canvas(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lab.canvas"
            data = {"nodes": [], "edges": []}
            save_canvas(path, data)
            self.assertEqual(load_canvas(path), data)


if __name__ == "__main__":
    unittest.main()
