"""Terminal adapter for the interface-independent companion engine."""

from __future__ import annotations

import sys
from collections.abc import Callable

from . import display_version
from .benchmark import format_benchmark, run_local_benchmark
from .commands import HELP_TEXT, normalized_command
from .companion import Companion
from .config import SolaceConfig
from .ollama import OllamaChatAdapter, OllamaError
from .status import status_text
from .storage import ConversationStore, ConversationSummary


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]
StreamOutputFunction = Callable[[str], None]


def console_output(text: str) -> None:
    """Print without crashing when a legacy Windows code page lacks a glyph."""
    stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    safe_text = text.encode(encoding, errors="replace").decode(encoding)
    print(safe_text, file=stream)


def console_stream_output(text: str) -> None:
    """Write a token fragment immediately using the active console encoding."""
    stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    safe_text = text.encode(encoding, errors="replace").decode(encoding)
    print(safe_text, end="", file=stream, flush=True)


def create_companion(config: SolaceConfig) -> Companion:
    model = OllamaChatAdapter.from_config(config)
    store = ConversationStore(config.conversations_dir)
    return Companion(
        model,
        store,
        context_limit=config.short_term_message_limit,
        unload_on_close=config.ollama_unload_on_exit,
    )


def benchmark_text(config: SolaceConfig, *, unload_when_done: bool = True) -> str:
    return format_benchmark(
        run_local_benchmark(config, unload_when_done=unload_when_done)
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
    stream_output_fn: StreamOutputFunction | None = None,
    status_provider: Callable[[SolaceConfig], str] = status_text,
    benchmark_provider: Callable[[SolaceConfig], str] | None = None,
) -> int:
    active_companion = companion or create_companion(config)
    read = input_fn or input
    write = output_fn or console_output
    stream_write = stream_output_fn
    if stream_write is None and output_fn is None:
        stream_write = console_stream_output
    run_benchmark = benchmark_provider or (
        lambda selected: benchmark_text(selected, unload_when_done=False)
    )

    write(f"Solace {display_version()}")
    write("Private | Local | Yours")
    write("")
    try:
        try:
            active_companion.ensure_available()
            if config.ollama_preload_on_start:
                active_companion.preload()
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
            if command == "/benchmark":
                try:
                    write(run_benchmark(config))
                except OllamaError as exc:
                    write(f"Benchmark error: {exc}")
                continue
            if command is not None:
                write(f"Unknown command: {user_text.strip()}. Type /help for commands.")
                continue

            try:
                if stream_write is None:
                    response = "".join(active_companion.respond_stream(user_text))
                    write(f"Solace > {response}")
                else:
                    stream_write("Solace > ")
                    for fragment in active_companion.respond_stream(user_text):
                        stream_write(fragment)
                    stream_write("\n")
            except OllamaError as exc:
                if stream_write is not None:
                    stream_write("\n")
                write(f"Local model error: {exc}")
                return 1
            except KeyboardInterrupt:
                if stream_write is not None:
                    stream_write("\n")
                write("")
                write("Solace > Take care.")
                return 0
    finally:
        try:
            active_companion.close()
        except OllamaError as exc:
            write(f"Warning: could not unload local model: {exc}")
