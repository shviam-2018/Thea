"""Interfaces and measurements shared by local model clients."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol


ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: ChatRole
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def _number(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    return value if type(value) is int and value >= 0 else None


@dataclass(frozen=True, slots=True)
class InferenceMetrics:
    """Ollama timing and token counters for one completed response."""

    wall_seconds: float
    first_content_seconds: float | None
    total_duration_ns: int | None
    load_duration_ns: int | None
    prompt_eval_count: int | None
    prompt_eval_duration_ns: int | None
    eval_count: int | None
    eval_duration_ns: int | None
    done_reason: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        wall_seconds: float,
        first_content_seconds: float | None,
    ) -> InferenceMetrics:
        reason = payload.get("done_reason")
        return cls(
            wall_seconds=max(0.0, wall_seconds),
            first_content_seconds=first_content_seconds,
            total_duration_ns=_number(payload, "total_duration"),
            load_duration_ns=_number(payload, "load_duration"),
            prompt_eval_count=_number(payload, "prompt_eval_count"),
            prompt_eval_duration_ns=_number(payload, "prompt_eval_duration"),
            eval_count=_number(payload, "eval_count"),
            eval_duration_ns=_number(payload, "eval_duration"),
            done_reason=reason if isinstance(reason, str) else None,
        )

    @staticmethod
    def seconds(nanoseconds: int | None) -> float | None:
        return nanoseconds / 1_000_000_000 if nanoseconds is not None else None

    @property
    def total_seconds(self) -> float | None:
        return self.seconds(self.total_duration_ns)

    @property
    def load_seconds(self) -> float | None:
        return self.seconds(self.load_duration_ns)

    @property
    def prompt_tokens_per_second(self) -> float | None:
        duration = self.seconds(self.prompt_eval_duration_ns)
        if not duration or self.prompt_eval_count is None:
            return None
        return self.prompt_eval_count / duration

    @property
    def generation_tokens_per_second(self) -> float | None:
        duration = self.seconds(self.eval_duration_ns)
        if not duration or self.eval_count is None:
            return None
        return self.eval_count / duration


@dataclass(frozen=True, slots=True)
class ChatStreamEvent:
    """One visible text fragment or the final metrics for a streamed chat."""

    content: str = ""
    metrics: InferenceMetrics | None = None


class ChatAdapter(Protocol):
    def ensure_available(self) -> None:
        """Raise a useful adapter error unless the configured model is ready."""

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return only the model's final assistant response."""

    def chat_stream(self, messages: Sequence[ChatMessage]) -> Iterator[ChatStreamEvent]:
        """Yield visible response fragments and one final metrics event."""

    def preload(self) -> None:
        """Load the model for the active session without generating text."""

    def unload(self) -> None:
        """Release a model loaded by this adapter when practical."""
