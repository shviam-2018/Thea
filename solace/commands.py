"""Slash commands shared by the eventual interactive clients."""

from __future__ import annotations

from collections.abc import Callable

from .config import SolaceConfig
from .status import status_text


HELP_TEXT = """Commands
  /help     Show this help
  /status   Show local system and service status
  /new      Start a new conversation
  /history  Show compact recent conversation information
  /quit     Exit Solace"""


def normalized_command(text: str) -> str | None:
    normalized = text.strip().lower()
    return normalized if normalized.startswith("/") else None


def handle_slash_command(
    command: str,
    config: SolaceConfig,
    status_provider: Callable[[SolaceConfig], str] = status_text,
) -> str | None:
    """Return slash-command output, or None when input is normal conversation."""
    normalized = normalized_command(command)
    if normalized is None:
        return None
    if normalized == "/status":
        return status_provider(config)
    if normalized in {"/help", "/?"}:
        return HELP_TEXT
    return f"Unknown command: {command.strip()}"
