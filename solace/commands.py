"""Slash commands shared by the eventual interactive clients."""

from __future__ import annotations

from collections.abc import Callable

from .config import SolaceConfig
from .status import status_text


def handle_slash_command(
    command: str,
    config: SolaceConfig,
    status_provider: Callable[[SolaceConfig], str] = status_text,
) -> str | None:
    """Return slash-command output, or None when input is normal conversation."""
    normalized = command.strip().lower()
    if not normalized.startswith("/"):
        return None
    if normalized == "/status":
        return status_provider(config)
    if normalized in {"/help", "/?"}:
        return "Available commands: /status, /help"
    return f"Unknown command: {command.strip()}"
