import unittest
from unittest.mock import patch
from urllib.error import URLError

from solace.llm import ChatMessage
from solace.ollama import (
    OllamaChatAdapter,
    OllamaModelUnavailableError,
    OllamaResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


def make_adapter(**overrides):
    values = {
        "base_url": "http://127.0.0.1:11434",
        "model": "qwen3:4b",
        "keep_alive": "2m",
        "context_window": 4096,
        "max_output_tokens": 256,
        "request_timeout_seconds": 180.0,
    }
    values.update(overrides)
    return OllamaChatAdapter(**values)


class OllamaChatAdapterTests(unittest.TestCase):
    @patch("solace.ollama.urlopen", side_effect=URLError("connection refused"))
    def test_missing_ollama_has_a_useful_error(self, _urlopen):
        with self.assertRaisesRegex(OllamaUnavailableError, "Start Ollama"):
            make_adapter().ensure_available()

    def test_missing_model_has_a_useful_error(self):
        adapter = make_adapter()
        with patch.object(
            adapter,
            "_request_json",
            side_effect=[{"version": "test"}, {"models": [{"name": "another:4b"}]}],
        ):
            with self.assertRaisesRegex(OllamaModelUnavailableError, "ollama pull qwen3:4b"):
                adapter.ensure_available()

    @patch("solace.ollama.urlopen", side_effect=TimeoutError())
    def test_inference_timeout_is_not_reported_as_a_stopped_server(self, _urlopen):
        adapter = make_adapter()
        with self.assertRaisesRegex(OllamaTimeoutError, "did not finish within 180 seconds"):
            adapter.chat([ChatMessage("user", "hello")])

    def test_chat_separates_thinking_and_returns_only_final_content(self):
        adapter = make_adapter()
        response = {
            "message": {"content": "Final answer", "thinking": "private reasoning"},
        }
        with patch.object(adapter, "_request_json", return_value=response) as request:
            messages = [
                ChatMessage("system", "Be helpful"),
                ChatMessage("user", "hello"),
            ]
            result = adapter.chat(messages)

        self.assertEqual(result, "Final answer")
        payload = request.call_args.kwargs["payload"]
        self.assertIs(payload["think"], True)
        self.assertIs(payload["stream"], False)
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertEqual(payload["options"]["num_predict"], 256)
        self.assertEqual(payload["messages"][0]["content"], "Be helpful")
        self.assertEqual(messages[0].content, "Be helpful")
        self.assertNotIn("private reasoning", result)

    def test_thinking_is_not_used_when_final_content_is_missing(self):
        adapter = make_adapter()
        response = {"message": {"content": "", "thinking": "private reasoning"}}
        with patch.object(adapter, "_request_json", return_value=response):
            with self.assertRaisesRegex(OllamaResponseError, "no final response"):
                adapter.chat([ChatMessage("user", "hello")])

    def test_remote_ollama_url_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            make_adapter(base_url="https://example.com")


if __name__ == "__main__":
    unittest.main()
