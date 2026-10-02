import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.assistant_chat import (
    assistant_status,
    chat_with_assistant,
    clear_assistant_configuration,
    configure_assistant,
    draft_from_conversation,
)


class AssistantChatTests(unittest.TestCase):
    def tearDown(self):
        clear_assistant_configuration()

    def test_status_does_not_expose_api_key(self):
        with patch.dict(os.environ, {
            "AUTOCOMPILER_CHAT_PROVIDER": "google-gemini",
            "AUTOCOMPILER_CHAT_API_KEY": "temporary-secret-key",
            "AUTOCOMPILER_CHAT_MODEL": "test-model",
        }, clear=False):
            status = assistant_status()
        self.assertTrue(status["configured"])
        self.assertEqual(status["provider"], "google-gemini")
        self.assertEqual(status["model"], "test-model")
        self.assertNotIn("temporary-secret-key", str(status))

    def test_runtime_configuration_is_memory_only_and_secret_is_not_returned(self):
        result = configure_assistant(
            api_key="AQ.temporary-secret-key",
            provider="google-gemini",
            model="gemini-3.8-flash",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["configured"])
        self.assertEqual(result["storage"], "process_memory_only")
        self.assertNotIn("AQ.temporary-secret-key", str(result))

        status = assistant_status()
        self.assertTrue(status["configured"])
        self.assertEqual(status["model"], "gemini-3.8-flash")
        self.assertNotIn("AQ.temporary-secret-key", str(status))

        cleared = clear_assistant_configuration()
        self.assertFalse(cleared["configured"])

    def test_unconfigured_chat_fails_closed(self):
        clear_assistant_configuration()
        with patch.dict(os.environ, {
            "AUTOCOMPILER_CHAT_API_KEY": "",
            "AUTOCOMPILER_CHAT_MODEL": "",
        }, clear=False):
            result = chat_with_assistant("Quero fazer backup")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "assistant_not_configured")

    @patch("autocompiler.assistant_chat._gemini_chat")
    def test_chat_can_edit_draft_but_cannot_mutate_machine_or_authorize(self, gemini):
        gemini.return_value = "Vamos definir a origem e o destino do backup."
        configure_assistant(
            api_key="AQ.temporary-secret-key",
            model="gemini-3.8-flash",
        )
        result = chat_with_assistant(
            "Quero fazer backup",
            history=[{"role": "user", "text": "Tenho uma pasta de trabalho"}],
            utilities=[{
                "user_title": "Backup automático",
                "status": "validation",
                "category": "Proteção",
                "outcome": "Copiar arquivos automaticamente.",
            }],
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["can_edit_draft"])
        self.assertFalse(result["can_mutate_machine"])
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["can_apply"])
        gemini.assert_called_once()

    @patch("autocompiler.assistant_chat.draft_intent_to_ir")
    def test_conversation_can_create_candidate_ir_with_configured_model(self, draft):
        draft.return_value = {
            "ok": True,
            "ir": {
                "schema_version": "0.1",
                "name": "Backup",
                "trigger": {"type": "manual"},
                "steps": [{"id": "s1", "skill": "filesystem.scan", "with": {"path": "."}}],
                "state": {"file": "history.db"},
            },
        }
        configure_assistant(
            api_key="AQ.temporary-secret-key",
            model="gemini-3.8-flash",
        )
        result = draft_from_conversation(
            history=[
                {"role": "user", "text": "Quero fazer backup da pasta trabalho."},
                {"role": "assistant", "text": "Qual destino?"},
                {"role": "user", "text": "Pasta backups."},
            ],
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["draft_only"])
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["can_apply"])
        _, kwargs = draft.call_args
        self.assertEqual(kwargs["provider"], "google-gemini")
        self.assertEqual(kwargs["model"], "gemini-3.8-flash")
        self.assertEqual(kwargs["api_key"], "AQ.temporary-secret-key")


if __name__ == "__main__":
    unittest.main()
