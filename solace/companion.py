"""Interface-independent Solace conversation engine."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from .llm import ChatAdapter, ChatMessage, InferenceMetrics
from .prompt import SYSTEM_PROMPT
from .storage import ConversationStore, ConversationSummary


class Companion:
    """Coordinate bounded model context with complete on-disk transcripts."""

    def __init__(
        self,
        model: ChatAdapter,
        store: ConversationStore,
        *,
        context_limit: int,
        system_prompt: str = SYSTEM_PROMPT,
        unload_on_close: bool = True,
    ) -> None:
        if context_limit <= 0:
            raise ValueError("context_limit must be positive")
        self._model = model
        self._store = store
        self._context_limit = context_limit
        self._system_message = ChatMessage("system", system_prompt.strip())
        self._unload_on_close = unload_on_close
        self._context: list[ChatMessage] = []
        self._conversation_id = store.new_conversation_id()
        self._message_count = 0
        self._last_metrics: InferenceMetrics | None = None

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def recent_context(self) -> tuple[ChatMessage, ...]:
        return tuple(self._context)

    @property
    def last_metrics(self) -> InferenceMetrics | None:
        return self._last_metrics

    def ensure_available(self) -> None:
        self._model.ensure_available()

    def preload(self) -> None:
        self._model.preload()

    def close(self) -> None:
        if self._unload_on_close:
            self._model.unload()

    def respond(self, user_text: str) -> str:
        return "".join(self.respond_stream(user_text))

    def respond_stream(self, user_text: str) -> Iterator[str]:
        """Yield visible text while persisting only the completed final reply."""
        if not isinstance(user_text, str) or not user_text.strip():
            raise ValueError("user_text must not be empty")
        content = user_text.strip()
        self._store.append(self._conversation_id, "user", content)
        self._message_count += 1
        self._append_context(ChatMessage("user", content))

        response_parts: list[str] = []
        self._last_metrics = None
        for event in self._model.chat_stream((self._system_message, *self._context)):
            if event.content:
                response_parts.append(event.content)
                yield event.content
            if event.metrics is not None:
                self._last_metrics = event.metrics

        response = "".join(response_parts)
        if not response.strip():
            raise ValueError("The model returned an empty response")
        self._store.append(self._conversation_id, "assistant", response)
        self._message_count += 1
        self._append_context(ChatMessage("assistant", response))

    def new_conversation(self) -> str:
        self._conversation_id = self._store.new_conversation_id()
        self._context.clear()
        self._message_count = 0
        return self._conversation_id

    def recent_conversations(self, limit: int = 5) -> Sequence[ConversationSummary]:
        return self._store.recent(limit=limit)

    def _append_context(self, message: ChatMessage) -> None:
        self._context.append(message)
        while len(self._context) > self._context_limit:
            self._context.pop(0)
        while self._context and self._context[0].role == "assistant":
            self._context.pop(0)
