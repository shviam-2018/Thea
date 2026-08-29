import json
import tempfile
import unittest
from pathlib import Path

from solace.config import SolaceConfig, load_config


class ConfigTests(unittest.TestCase):
    def test_cpu_friendly_defaults(self):
        config = SolaceConfig()
        self.assertEqual(config.chat_model, "qwen3:4b")
        self.assertEqual(config.embedding_model, "nomic-embed-text:latest")
        self.assertEqual(config.embedding_dimensions, 768)
        self.assertLessEqual(config.short_term_message_limit, 24)

    def test_loads_override(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"chat_model": "custom:4b"}), encoding="utf-8")
            self.assertEqual(load_config(path).chat_model, "custom:4b")

    def test_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"surprise": true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown configuration"):
                load_config(path)

    def test_rejects_invalid_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"embedding_dimensions": 0}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive integer"):
                load_config(path)

    def test_rejects_wrong_setting_types(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"chat_model": 4}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be strings"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
