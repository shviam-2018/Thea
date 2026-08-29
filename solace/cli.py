"""Terminal adapter for the interface-independent companion engine."""

from __future__ import annotations

import sys
from collections.abc import Callable

from . import display_version
from .commands import HELP_TEXT, normalized_command
from .companion import Companion
from .config import SolaceConfig
from .ollama import OllamaChatAdapter, OllamaError
from .status import status_text
from .storage import ConversationStore, ConversationSummary


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def console_output(text: str) -> None:
    """Print without crashing when a legacy Windows code page lacks a glyph."""
    stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    safe_text = text.encode(encoding, errors="replace").decode(encoding)
    print(safe_text, file=stream)


def create_companion(config: SolaceConfig) -> Companion:
    model = OllamaChatAdapter.from_config(config)
    store = ConversationStore(config.conversations_dir)
    return Companion(
        model,
        store,
        context_limit=config.short_term_message_limit,
    )


def format_history(companion: Companion) -> str:
    lines = [
        f"Current conversation: {companion.conversation_id}",
        f"Current messages: {companion.message_count}",
    ]
    recent = companion.recent_conversations(limit=5)
    if not recent:
        lines.append("Recent conversations: none yet")
        return "\n".join(lines)
    lines.append("Recent conversations:")
    lines.extend(_summary_line(summary, companion.conversation_id) for summary in recent)
    return "\n".join(lines)


def _summary_line(summary: ConversationSummary, current_id: str) -> str:
    marker = " (current)" if summary.conversation_id == current_id else ""
    return (
        f"  {summary.conversation_id}{marker} - {summary.message_count} messages - "
        f"{summary.updated_at} - {summary.preview}"
    )


def run_chat(
    config: SolaceConfig,
    *,
    companion: Companion | None = None,
    input_fn: InputFunction | None = None,
    output_fn: OutputFunction | None = None,
    status_provider: Callable[[SolaceConfig], str] = status_text,
) -> int:
    active_companion = companion or create_companion(config)
    read = input_fn or input
    write = output_fn or console_output

    write(f"Solace {display_version()}")
    write("Private | Local | Yours")
    write("")
    try:
        active_companion.ensure_available()
    except OllamaError as exc:
        write(f"Unable to start local chat: {exc}")
        return 1

    write("Type /help for commands.")
    write("")
    while True:
        try:
            user_text = read("You > ")
        except (EOFError, KeyboardInterrupt):
            write("")
            write("Solace > Take care.")
            return 0

        if not user_text.strip():
            continue
        command = normalized_command(user_text)
        if command in {"/quit", "/exit"}:
            write("Solace > Take care.")
            return 0
        if command in {"/help", "/?"}:
            write(HELP_TEXT)
            continue
        if command == "/status":
            write(status_provider(config))
            continue
        if command == "/new":
            active_companion.new_conversation()
            write("Solace > Started a new conversation.")
            continue
        if command == "/history":
            write(format_history(active_companion))
            continue
        if command is not None:
            write(f"Unknown command: {user_text.strip()}. Type /help for commands.")
            continue

        try:
            response = active_companion.respond(user_text)
        except OllamaError as exc:
            write(f"Local model error: {exc}")
            return 1
        except KeyboardInterrupt:
            write("")
            write("Solace > Take care.")
            return 0
        write(f"Solace > {response}")
