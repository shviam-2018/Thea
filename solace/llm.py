"""Interface shared by local language-model adapters and conversation clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence


ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: ChatRole
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class ChatAdapter(Protocol):
    def ensure_available(self) -> None:
        """Raise a useful adapter error unless the configured model is ready."""

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return only the model's final assistant response."""
