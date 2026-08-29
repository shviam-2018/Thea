import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solace.commands import handle_slash_command
from solace.config import SolaceConfig
from solace.status import (
    DiskUsage,
    MemoryUsage,
    StatusSnapshot,
    directory_size,
    embedding_dimensions_state,
    format_bytes,
    format_status,
)


class StatusTests(unittest.TestCase):
    def test_directory_size_counts_nested_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "one.txt").write_bytes(b"123")
            (root / "nested" / "two.txt").write_bytes(b"4567")
            self.assertEqual(directory_size(root), 7)

    def test_byte_formatting(self):
        self.assertEqual(format_bytes(None), "unknown")
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1536), "1.5 KiB")

    def test_status_output_has_required_sections(self):
        snapshot = StatusSnapshot(
            version="0.2.0-alpha.test",
            cpu="Test CPU",
            memory=MemoryUsage(8 * 1024**3, 16 * 1024**3),
            disk=DiskUsage(80 * 1024**3, 238 * 1024**3),
            chat_model="qwen3:4b",
            embedding_model="nomic-embed-text:latest",
            embedding_dimensions="768 (verified)",
            ollama_state="running",
            mem0_state="ready",
            long_term_memories=12,
            qdrant_storage_bytes=1024,
            conversations_bytes=2048,
            solace_data_bytes=4096,
        )
        output = format_status(snapshot)
        for expected in (
            "Solace 0.2.0-alpha.test",
            "CPU: Test CPU",
            "Chat model: qwen3:4b",
            "Embedding model: nomic-embed-text:latest",
            "Embedding dimensions: 768 (verified)",
            "Long-term memories: 12",
            "Conversations: 2.0 KiB",
        ):
            self.assertIn(expected, output)

    def test_status_slash_command(self):
        output = handle_slash_command(" /STATUS ", SolaceConfig(), lambda _: "status")
        self.assertEqual(output, "status")

    def test_non_command_is_not_consumed(self):
        self.assertIsNone(handle_slash_command("hello", SolaceConfig()))

    @patch("solace.status._post_json")
    def test_embedding_dimensions_are_verified_from_model_metadata(self, post_json):
        post_json.return_value = {
            "model_info": {
                "general.architecture": "nomic-bert",
                "nomic-bert.embedding_length": 768,
            }
        }
        state = embedding_dimensions_state(SolaceConfig(), ollama_running=True)
        self.assertEqual(state, "768 (verified)")

    @patch("solace.status._post_json")
    def test_embedding_dimension_mismatch_is_visible(self, post_json):
        post_json.return_value = {
            "model_info": {
                "general.architecture": "custom",
                "custom.embedding_length": 384,
            }
        }
        state = embedding_dimensions_state(SolaceConfig(), ollama_running=True)
        self.assertIn("mismatch", state)


if __name__ == "__main__":
    unittest.main()
