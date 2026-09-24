import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.environment import build_resource_graph
from autocompiler.discover import discover
from autocompiler.whatsapp_automation import (
    SqliteConversationStore,
    WhatsAppBlueprint,
    WhatsAppFlowRuntime,
    runtime_status,
)

CSV = ROOT / "examples" / "whatsapp" / "atendimento_servicos_digitais.csv"


class WhatsAppAutomationTests(unittest.TestCase):
    def setUp(self):
        self.blueprint = WhatsAppBlueprint.load_csv(CSV)
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SqliteConversationStore(Path(self.tmp.name) / "state.db")
        self.runtime = WhatsAppFlowRuntime(self.blueprint, self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_blueprint_preserves_csv_structure(self):
        self.assertEqual(
            self.blueprint.summary(),
            {
                "configuracao": 4,
                "sequencia": 19,
                "logica": 17,
                "base_conhecimento": 17,
                "catalogo": 20,
            },
        )

    def test_local_environment_is_not_claimed_as_real_whatsapp_provider(self):
        status = runtime_status(
            self.blueprint,
            build_resource_graph(discover()),
        )
        by_capability = {
            item["capability"]: item["action"]
            for item in status["resolutions"]
        }
        self.assertEqual(by_capability["durable_state"], "reuse")
        self.assertEqual(by_capability["messaging.whatsapp.receive"], "unresolved")
        self.assertEqual(by_capability["messaging.whatsapp.send"], "unresolved")
        self.assertFalse(status["ready_for_real_whatsapp"])

    def test_demo_flow_advances_and_human_request_pauses(self):
        start = self.runtime.start("client-1")
        self.assertEqual(start.state_id, "AT-001")

        step = self.runtime.handle("client-1", "quero conhecer os serviços")
        self.assertEqual(step.state_id, "AT-002")

        human = self.runtime.handle("client-1", "quero falar com o Dudu")
        self.assertEqual(human.state_id, "AT-090")
        self.assertEqual(human.status, "human_pending")

        paused = self.runtime.handle("client-1", "oi?")
        self.assertEqual(paused.status, "human_pending")
        self.assertEqual(paused.response, "")

    def test_duplicate_message_is_ignored_once(self):
        self.runtime.start("client-2")
        first = self.runtime.handle(
            "client-2",
            "quero conhecer",
            message_id="wamid-001",
        )
        duplicate = self.runtime.handle(
            "client-2",
            "quero conhecer",
            message_id="wamid-001",
        )
        self.assertEqual(first.status, "ok")
        self.assertEqual(duplicate.status, "duplicate")
        self.assertEqual(duplicate.response, "")


if __name__ == "__main__":
    unittest.main()
