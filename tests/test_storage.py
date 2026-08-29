import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from solace.storage import ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "conversations"
        self.store = ConversationStore(
            self.root,
            clock=lambda: datetime(2026, 8, 29, 18, 30, tzinfo=timezone.utc),
            id_factory=lambda: "test-conversation",
        )

    def test_new_conversation_does_not_create_an_empty_file(self):
        conversation_id = self.store.new_conversation_id()
        self.assertEqual(conversation_id, "test-conversation")
        self.assertFalse(self.store.conversation_path(conversation_id).exists())

    def test_records_are_appended_as_jsonl(self):
        conversation_id = self.store.new_conversation_id()
        self.store.append(conversation_id, "user", "hello")
        self.store.append(conversation_id, "assistant", "Hey :) What's up?")

        lines = (
            self.store.conversation_path(conversation_id)
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertEqual(
            [json.loads(line) for line in lines],
            [
                {
                    "timestamp": "2026-08-29T18:30:00Z",
                    "role": "user",
                    "content": "hello",
                },
                {
                    "timestamp": "2026-08-29T18:30:00Z",
                    "role": "assistant",
                    "content": "Hey :) What's up?",
                },
            ],
        )

    def test_recent_returns_summaries_not_full_transcripts(self):
        conversation_id = self.store.new_conversation_id()
        self.store.append(conversation_id, "user", "A private opening message")
        self.store.append(conversation_id, "assistant", "A private answer")

        summaries = self.store.recent(limit=1)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].conversation_id, conversation_id)
        self.assertEqual(summaries[0].message_count, 2)
        self.assertEqual(summaries[0].preview, "A private opening message")

    def test_conversation_id_cannot_escape_storage_directory(self):
        with self.assertRaisesRegex(ValueError, "Invalid conversation ID"):
            self.store.conversation_path("../outside")


if __name__ == "__main__":
    unittest.main()
