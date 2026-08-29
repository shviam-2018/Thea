"""Configuration loading for the resource-conscious Solace baseline."""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CHAT_MODEL = "qwen3:4b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text:latest"
DEFAULT_EMBEDDING_DIMENSIONS = 768


def default_data_dir() -> Path:
    """Return a per-user, cross-platform data directory without creating it."""
    override = os.environ.get("SOLACE_DATA_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / "Solace" if base else Path.home() / "AppData" / "Local" / "Solace"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Solace"

    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base) if base else Path.home() / ".local" / "share") / "solace"


@dataclass(frozen=True, slots=True)
class SolaceConfig:
    """Runtime settings whose defaults fit a 16 GB CPU-first laptop."""

    chat_model: str = DEFAULT_CHAT_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    ollama_base_url: str = "http://127.0.0.1:11434"
    qdrant_url: str = "http://127.0.0.1:6333"
    memory_collection: str = "solace_memories"
    short_term_message_limit: int = 24
    ollama_keep_alive: str = "2m"
    ollama_context_window: int = 4096
    ollama_max_output_tokens: int = 256
    ollama_request_timeout_seconds: float = 180.0
    data_dir: Path | None = None

    @property
    def resolved_data_dir(self) -> Path:
        return (self.data_dir or default_data_dir()).expanduser().resolve()

    @property
    def conversations_dir(self) -> Path:
        return self.resolved_data_dir / "conversations"

    @property
    def qdrant_storage_dir(self) -> Path:
        return self.resolved_data_dir / "qdrant"


def _validated(raw: Mapping[str, Any]) -> SolaceConfig:
    known = {field.name for field in fields(SolaceConfig)}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ValueError(f"Unknown configuration field(s): {', '.join(unknown)}")

    values = dict(raw)
    if values.get("data_dir") is not None:
        if not isinstance(values["data_dir"], str):
            raise ValueError("data_dir must be a path string or null")
        values["data_dir"] = Path(values["data_dir"])
    config = SolaceConfig(**values)

    string_fields = {
        "chat_model": config.chat_model,
        "embedding_model": config.embedding_model,
        "ollama_base_url": config.ollama_base_url,
        "qdrant_url": config.qdrant_url,
        "memory_collection": config.memory_collection,
        "ollama_keep_alive": config.ollama_keep_alive,
    }
    if any(not isinstance(value, str) for value in string_fields.values()):
        raise ValueError("model, service, collection, and keep-alive settings must be strings")
    if any(not value.strip() for value in string_fields.values()):
        raise ValueError("model, service, collection, and keep-alive settings must not be empty")
    if type(config.embedding_dimensions) is not int or config.embedding_dimensions <= 0:
        raise ValueError("embedding_dimensions must be a positive integer")
    if type(config.short_term_message_limit) is not int or config.short_term_message_limit <= 0:
        raise ValueError("short_term_message_limit must be a positive integer")
    if type(config.ollama_context_window) is not int or config.ollama_context_window <= 0:
        raise ValueError("ollama_context_window must be a positive integer")
    if type(config.ollama_max_output_tokens) is not int or config.ollama_max_output_tokens <= 0:
        raise ValueError("ollama_max_output_tokens must be a positive integer")
    if (
        isinstance(config.ollama_request_timeout_seconds, bool)
        or not isinstance(config.ollama_request_timeout_seconds, (int, float))
        or config.ollama_request_timeout_seconds <= 0
    ):
        raise ValueError("ollama_request_timeout_seconds must be a positive number")
    if not config.ollama_base_url.startswith(("http://", "https://")):
        raise ValueError("ollama_base_url must be an HTTP(S) URL")
    if not config.qdrant_url.startswith(("http://", "https://")):
        raise ValueError("qdrant_url must be an HTTP(S) URL")
    return config


def load_config(path: str | Path | None = None) -> SolaceConfig:
    """Load JSON configuration, falling back to conservative local defaults."""
    selected = path or os.environ.get("SOLACE_CONFIG")
    if selected is None:
        return SolaceConfig()

    config_path = Path(selected).expanduser()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {config_path}: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Solace configuration must be a JSON object")
    return _validated(raw)
