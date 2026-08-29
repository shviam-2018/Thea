import io
import unittest
from unittest.mock import patch

from solace.__main__ import main
from solace.cli import console_output, run_chat
from solace.config import SolaceConfig
from solace.ollama import OllamaModelUnavailableError, OllamaUnavailableError
from solace.storage import ConversationSummary


class FakeCompanion:
    def __init__(self, *, ready_error=None):
        self.ready_error = ready_error
        self.conversation_id = "conversation-one"
        self.message_count = 0
        self.responses: list[str] = []
        self.new_calls = 0
        self.preload_calls = 0
        self.close_calls = 0

    def ensure_available(self):
        if self.ready_error is not None:
            raise self.ready_error

    def respond(self, text):
        self.responses.append(text)
        self.message_count += 2
        return "local reply"

    def respond_stream(self, text):
        self.responses.append(text)
        self.message_count += 2
        yield "local "
        yield "reply"

    def preload(self):
        self.preload_calls += 1

    def close(self):
        self.close_calls += 1

    def new_conversation(self):
        self.new_calls += 1
        self.conversation_id = "conversation-two"
        self.message_count = 0
        return self.conversation_id

    def recent_conversations(self, limit=5):
        return [
            ConversationSummary(
                conversation_id=self.conversation_id,
                updated_at="2026-08-29T18:30:00Z",
                message_count=self.message_count or 2,
                preview="hello",
            )
        ]


def sequence_input(*values):
    iterator = iter(values)
    return lambda _prompt: next(iterator)


class CliTests(unittest.TestCase):
    def test_console_output_tolerates_unsupported_unicode(self):
        raw_output = io.BytesIO()
        text_output = io.TextIOWrapper(raw_output, encoding="ascii", errors="strict")
        with patch("solace.cli.sys.stdout", text_output):
            console_output("hello 👋")
            text_output.flush()
        self.assertEqual(raw_output.getvalue().decode("ascii").strip(), "hello ?")

    @patch("solace.__main__.run_chat", return_value=0)
    def test_default_invocation_enters_chat_mode(self, run_chat):
        self.assertEqual(main([]), 0)
        run_chat.assert_called_once()

    @patch("solace.__main__.handle_slash_command", return_value="status")
    @patch("solace.__main__.run_chat")
    def test_explicit_status_does_not_enter_chat_mode(self, run_chat, handle_command):
        with patch("builtins.print") as output:
            self.assertEqual(main(["/status"]), 0)
        run_chat.assert_not_called()
        handle_command.assert_called_once()
        output.assert_called_once_with("status")

    def test_chat_responds_and_quits_cleanly(self):
        output = []
        companion = FakeCompanion()
        result = run_chat(
            SolaceConfig(),
            companion=companion,
            input_fn=sequence_input("hey", "/quit"),
            output_fn=output.append,
        )
        self.assertEqual(result, 0)
        self.assertEqual(companion.responses, ["hey"])
        self.assertIn("Solace > local reply", output)
        self.assertEqual(output[-1], "Solace > Take care.")
        self.assertEqual(companion.preload_calls, 1)
        self.assertEqual(companion.close_calls, 1)

    def test_chat_writes_stream_fragments_immediately(self):
        output = []
        streamed = []
        result = run_chat(
            SolaceConfig(),
            companion=FakeCompanion(),
            input_fn=sequence_input("hey", "/quit"),
            output_fn=output.append,
            stream_output_fn=streamed.append,
        )
        self.assertEqual(result, 0)
        self.assertEqual(streamed, ["Solace > ", "local ", "reply", "\n"])

    def test_new_starts_a_fresh_session(self):
        output = []
        companion = FakeCompanion()
        result = run_chat(
            SolaceConfig(),
            companion=companion,
            input_fn=sequence_input("/new", "/quit"),
            output_fn=output.append,
        )
        self.assertEqual(result, 0)
        self.assertEqual(companion.new_calls, 1)
        self.assertIn("Solace > Started a new conversation.", output)

    def test_history_is_compact(self):
        output = []
        result = run_chat(
            SolaceConfig(),
            companion=FakeCompanion(),
            input_fn=sequence_input("/history", "/quit"),
            output_fn=output.append,
        )
        self.assertEqual(result, 0)
        history = next(line for line in output if line.startswith("Current conversation:"))
        self.assertIn("Recent conversations:", history)
        self.assertIn("hello", history)

    def test_status_does_not_replace_the_conversation(self):
        output = []
        companion = FakeCompanion()
        result = run_chat(
            SolaceConfig(),
            companion=companion,
            input_fn=sequence_input("/status", "still here", "/quit"),
            output_fn=output.append,
            status_provider=lambda _config: "local status",
        )
        self.assertEqual(result, 0)
        self.assertEqual(companion.conversation_id, "conversation-one")
        self.assertEqual(companion.responses, ["still here"])
        self.assertIn("local status", output)

    def test_benchmark_command_is_compact_and_keeps_session(self):
        output = []
        companion = FakeCompanion()
        result = run_chat(
            SolaceConfig(),
            companion=companion,
            input_fn=sequence_input("/benchmark", "/quit"),
            output_fn=output.append,
            benchmark_provider=lambda _config: "small benchmark",
        )
        self.assertEqual(result, 0)
        self.assertIn("small benchmark", output)
        self.assertEqual(companion.conversation_id, "conversation-one")

    def test_eof_and_keyboard_interrupt_exit_cleanly(self):
        for error_type in (EOFError, KeyboardInterrupt):
            with self.subTest(error_type=error_type):
                output = []

                def interrupted_input(_prompt):
                    raise error_type

                result = run_chat(
                    SolaceConfig(),
                    companion=FakeCompanion(),
                    input_fn=interrupted_input,
                    output_fn=output.append,
                )
                self.assertEqual(result, 0)
                self.assertEqual(output[-1], "Solace > Take care.")

    def test_missing_ollama_exits_gracefully(self):
        output = []
        companion = FakeCompanion(
            ready_error=OllamaUnavailableError("Start Ollama and try again."),
        )
        result = run_chat(SolaceConfig(), companion=companion, output_fn=output.append)
        self.assertEqual(result, 1)
        self.assertIn("Start Ollama", output[-1])

    def test_missing_model_exits_gracefully(self):
        output = []
        companion = FakeCompanion(
            ready_error=OllamaModelUnavailableError("ollama pull qwen3:4b"),
        )
        result = run_chat(SolaceConfig(), companion=companion, output_fn=output.append)
        self.assertEqual(result, 1)
        self.assertIn("ollama pull qwen3:4b", output[-1])


if __name__ == "__main__":
    unittest.main()
