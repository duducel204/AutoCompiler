import os
import unittest
from unittest.mock import patch

from autocompiler.assistant_chat import assistant_status, chat_with_assistant


class AssistantChatTests(unittest.TestCase):
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

    def test_unconfigured_chat_fails_closed(self):
        with patch.dict(os.environ, {
            "AUTOCOMPILER_CHAT_API_KEY": "",
            "AUTOCOMPILER_CHAT_MODEL": "",
        }, clear=False):
            result = chat_with_assistant("Quero fazer backup")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "assistant_not_configured")

    @patch("autocompiler.assistant_chat._gemini_chat")
    def test_chat_is_advisory_only(self, gemini):
        gemini.return_value = "Você pode usar Backup automático."
        with patch.dict(os.environ, {
            "AUTOCOMPILER_CHAT_PROVIDER": "google-gemini",
            "AUTOCOMPILER_CHAT_API_KEY": "temporary-secret-key",
            "AUTOCOMPILER_CHAT_MODEL": "test-model",
        }, clear=False):
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
        self.assertFalse(result["can_mutate"])
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["can_apply"])
        gemini.assert_called_once()


if __name__ == "__main__":
    unittest.main()
