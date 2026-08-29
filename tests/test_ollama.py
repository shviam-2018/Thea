import unittest
from unittest.mock import patch
from urllib.error import URLError

from solace.llm import ChatMessage
from solace.ollama import (
    OllamaChatAdapter,
    OllamaModelUnavailableError,
    OllamaResponseError,
    OllamaThinkingRequiredError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


def make_adapter(**overrides):
    values = {
        "base_url": "http://127.0.0.1:11434",
        "model": "qwen3:4b",
        "keep_alive": "10m",
        "context_window": 4096,
        "max_output_tokens": 128,
        "request_timeout_seconds": 180.0,
    }
    values.update(overrides)
    return OllamaChatAdapter(**values)


def completed_response(*parts, thinking=""):
    events = [
        {"message": {"content": part, "thinking": thinking}, "done": False}
        for part in parts
    ]
    events.append(
        {
            "message": {"content": "", "thinking": ""},
            "done": True,
            "done_reason": "stop",
            "total_duration": 2_000_000_000,
            "load_duration": 10_000_000,
            "prompt_eval_count": 20,
            "prompt_eval_duration": 500_000_000,
            "eval_count": 10,
            "eval_duration": 1_000_000_000,
        }
    )
    return events


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

    def test_thinking_only_artifact_is_rejected_for_normal_chat(self):
        adapter = make_adapter()
        profile = {
            "model_info": {
                "general.finetune": "Thinking",
                "general.version": "2507",
            }
        }
        with patch.object(
            adapter,
            "_request_json",
            side_effect=[
                {"version": "test"},
                {"models": [{"name": "qwen3:4b"}]},
                profile,
            ],
        ):
            with self.assertRaisesRegex(OllamaThinkingRequiredError, "Thinking-2507"):
                adapter.ensure_available()

    @patch("solace.ollama.urlopen", side_effect=TimeoutError())
    def test_inference_timeout_is_not_reported_as_a_stopped_server(self, _urlopen):
        adapter = make_adapter()
        with self.assertRaisesRegex(OllamaTimeoutError, "did not finish within 180 seconds"):
            adapter.chat([ChatMessage("user", "hello")])

    def test_chat_stream_sends_non_thinking_performance_configuration(self):
        adapter = make_adapter()
        with patch.object(
            adapter,
            "_response_payloads",
            return_value=iter(completed_response("Final ", "answer")),
        ) as request:
            messages = [
                ChatMessage("system", "Be helpful"),
                ChatMessage("user", "hello"),
            ]
            events = list(adapter.chat_stream(messages))

        self.assertEqual("".join(event.content for event in events), "Final answer")
        self.assertIsNotNone(events[-1].metrics)
        payload = request.call_args.args[0]
        self.assertIs(payload["think"], False)
        self.assertIs(payload["stream"], True)
        self.assertEqual(payload["keep_alive"], "10m")
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertEqual(payload["options"]["num_predict"], 128)
        self.assertEqual(payload["options"]["temperature"], 0.7)
        self.assertEqual(payload["options"]["top_p"], 0.8)
        self.assertEqual(payload["options"]["top_k"], 20)
        self.assertEqual(payload["options"]["min_p"], 0.0)
        self.assertEqual(payload["messages"][0]["content"], "Be helpful")
        self.assertEqual(messages[0].content, "Be helpful")

    def test_structured_reasoning_is_never_yielded_as_content(self):
        adapter = make_adapter()
        response = [
            {"message": {"content": "", "thinking": "private reasoning"}, "done": False}
        ]
        with patch.object(adapter, "_response_payloads", return_value=iter(response)):
            with self.assertRaisesRegex(OllamaResponseError, "reasoning"):
                list(adapter.chat_stream([ChatMessage("user", "hello")]))

    def test_thinking_is_not_used_when_final_content_is_missing(self):
        adapter = make_adapter()
        response = [
            {
                "message": {"content": "", "thinking": ""},
                "done": True,
                "total_duration": 1,
            }
        ]
        with patch.object(adapter, "_response_payloads", return_value=iter(response)):
            with self.assertRaisesRegex(OllamaResponseError, "no final response"):
                adapter.chat([ChatMessage("user", "hello")])

    def test_preload_and_unload_use_configured_keep_alive_then_zero(self):
        adapter = make_adapter()
        with patch.object(adapter, "_request_json", return_value={}) as request:
            adapter.preload()
            adapter.unload()
        calls = request.call_args_list
        self.assertEqual(calls[0].kwargs["payload"]["keep_alive"], "10m")
        self.assertEqual(calls[1].kwargs["payload"]["keep_alive"], 0)

    def test_remote_ollama_url_is_rejected_without_cloud_fallback(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            make_adapter(base_url="https://example.com")


if __name__ == "__main__":
    unittest.main()
