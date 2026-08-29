import json
import tempfile
import unittest
from pathlib import Path

from solace.companion import Companion
from solace.llm import ChatMessage
from solace.storage import ConversationStore


class FakeChatAdapter:
    def __init__(self):
        self.available_checks = 0
        self.calls: list[tuple[ChatMessage, ...]] = []

    def ensure_available(self):
        self.available_checks += 1

    def chat(self, messages):
        self.calls.append(tuple(messages))
        return f"reply {len(self.calls)}"


class CompanionTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.conversations_dir = Path(self.temporary_directory.name) / "conversations"
        ids = iter(("conversation-one", "conversation-two", "conversation-three"))
        self.store = ConversationStore(
            self.conversations_dir,
            id_factory=lambda: next(ids),
        )
        self.model = FakeChatAdapter()
        self.companion = Companion(
            self.model,
            self.store,
            context_limit=24,
            system_prompt="Test system prompt",
        )

    def test_respond_returns_model_text_and_persists_both_messages(self):
        reply = self.companion.respond(" hello ")
        self.assertEqual(reply, "reply 1")
        self.assertEqual(self.model.calls[0][0], ChatMessage("system", "Test system prompt"))

        path = self.store.conversation_path("conversation-one")
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([record["role"] for record in records], ["user", "assistant"])
        self.assertEqual([record["content"] for record in records], ["hello", "reply 1"])

    def test_model_context_is_bounded_but_complete_history_is_persisted(self):
        for index in range(20):
            self.companion.respond(f"message {index}")

        for call in self.model.calls:
            self.assertEqual(call[0].role, "system")
            recent_messages = call[1:]
            self.assertLessEqual(len(recent_messages), 24)
            self.assertEqual(recent_messages[0].role, "user")

        self.assertLessEqual(len(self.companion.recent_context), 24)
        path = self.store.conversation_path("conversation-one")
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 40)

    def test_new_conversation_clears_only_short_term_context(self):
        self.companion.respond("first session")
        previous_path = self.store.conversation_path(self.companion.conversation_id)

        new_id = self.companion.new_conversation()

        self.assertEqual(new_id, "conversation-two")
        self.assertEqual(self.companion.message_count, 0)
        self.assertEqual(self.companion.recent_context, ())
        self.assertTrue(previous_path.exists())
        self.assertFalse(self.store.conversation_path(new_id).exists())


if __name__ == "__main__":
    unittest.main()
