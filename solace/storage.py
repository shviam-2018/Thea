"""Append-only local conversation persistence."""

from __future__ import annotations

import json
import re
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Role = Literal["user", "assistant"]
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    timestamp: str
    role: Role
    content: str

    def as_dict(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "role": self.role,
            "content": self.content,
        }


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    conversation_id: str
    updated_at: str
    message_count: int
    preview: str


class ConversationStore:
    """Persist complete user/assistant transcripts as one JSONL file per session."""

    def __init__(
        self,
        conversations_dir: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.conversations_dir = conversations_dir
        self._clock = clock
        self._id_factory = id_factory
        self._write_lock = threading.Lock()

    def new_conversation_id(self) -> str:
        if self._id_factory is not None:
            conversation_id = self._id_factory()
        else:
            prefix = self._clock().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            conversation_id = f"{prefix}-{uuid.uuid4().hex[:8]}"
        self._validate_id(conversation_id)
        return conversation_id

    def conversation_path(self, conversation_id: str) -> Path:
        self._validate_id(conversation_id)
        return self.conversations_dir / f"{conversation_id}.jsonl"

    def append(self, conversation_id: str, role: Role, content: str) -> ConversationRecord:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        if not isinstance(content, str) or not content:
            raise ValueError("Conversation content must be a non-empty string")

        record = ConversationRecord(
            timestamp=_timestamp(self._clock()),
            role=role,
            content=content,
        )
        line = json.dumps(record.as_dict(), ensure_ascii=False, separators=(",", ":"))
        path = self.conversation_path(conversation_id)
        with self._write_lock:
            self.conversations_dir.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(f"{line}\n")
        return record

    def recent(self, limit: int = 5) -> list[ConversationSummary]:
        if limit <= 0 or not self.conversations_dir.exists():
            return []
        try:
            paths = sorted(
                self.conversations_dir.glob("*.jsonl"),
                key=lambda path: path.stat().st_mtime_ns,
                reverse=True,
            )[:limit]
        except OSError:
            return []
        summaries = [summary for path in paths if (summary := self._summarize(path))]
        return summaries

    def _summarize(self, path: Path) -> ConversationSummary | None:
        message_count = 0
        preview = ""
        updated_at = "unknown"
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if not isinstance(record, dict):
                        continue
                    content = record.get("content")
                    role = record.get("role")
                    timestamp = record.get("timestamp")
                    if role not in {"user", "assistant"} or not isinstance(content, str):
                        continue
                    message_count += 1
                    if role == "user" and not preview:
                        preview = " ".join(content.split())[:72]
                    if isinstance(timestamp, str):
                        updated_at = timestamp
        except OSError:
            return None
        if message_count == 0:
            return None
        return ConversationSummary(
            conversation_id=path.stem,
            updated_at=updated_at,
            message_count=message_count,
            preview=preview or "(no user message)",
        )

    @staticmethod
    def _validate_id(conversation_id: str) -> None:
        if not isinstance(conversation_id, str) or not _SAFE_ID.fullmatch(conversation_id):
            raise ValueError("Invalid conversation ID")
