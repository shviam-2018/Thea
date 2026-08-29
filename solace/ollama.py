"""Local-only Ollama chat adapter with streaming performance metrics."""

from __future__ import annotations

import ipaddress
import json
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import SolaceConfig
from .llm import ChatMessage, ChatStreamEvent, InferenceMetrics


class OllamaError(RuntimeError):
    """Base class for expected local Ollama failures."""


class OllamaUnavailableError(OllamaError):
    """The configured local Ollama server cannot be reached."""


class OllamaTimeoutError(OllamaError):
    """Local inference exceeded the configured response timeout."""


class OllamaModelUnavailableError(OllamaError):
    """The configured model is not installed in Ollama."""


class OllamaThinkingRequiredError(OllamaError):
    """The installed model artifact cannot generate without reasoning."""


class OllamaResponseError(OllamaError):
    """Ollama returned an invalid or unsuccessful response."""


class _OllamaHTTPError(OllamaError):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


@dataclass(frozen=True, slots=True)
class RunningModelInfo:
    name: str
    size: int | None
    size_vram: int | None
    context_length: int | None
    expires_at: str | None

    @property
    def processor(self) -> str:
        if self.size is None or self.size_vram is None or self.size <= 0:
            return "unknown"
        gpu_percent = round((self.size_vram / self.size) * 100)
        if gpu_percent <= 0:
            return "100% CPU"
        if gpu_percent >= 100:
            return "100% GPU"
        return f"{100 - gpu_percent}% CPU / {gpu_percent}% GPU"


class OllamaChatAdapter:
    """Call Ollama's native API without any network fallback."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        keep_alive: str,
        context_window: int,
        max_output_tokens: int,
        request_timeout_seconds: float,
        thinking: bool = False,
        streaming: bool = True,
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 20,
        min_p: float = 0.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.context_window = context_window
        self.max_output_tokens = max_output_tokens
        self.request_timeout_seconds = request_timeout_seconds
        self.thinking = thinking
        self.streaming = streaming
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.min_p = min_p
        self.last_metrics: InferenceMetrics | None = None
        self._used_model = False
        self._validate_local_url(self.base_url)

    @classmethod
    def from_config(cls, config: SolaceConfig) -> OllamaChatAdapter:
        return cls(
            base_url=config.ollama_base_url,
            model=config.chat_model,
            keep_alive=config.ollama_keep_alive,
            context_window=config.ollama_context_window,
            max_output_tokens=config.ollama_max_output_tokens,
            request_timeout_seconds=config.ollama_request_timeout_seconds,
            thinking=config.ollama_thinking,
            streaming=config.ollama_streaming,
            temperature=config.ollama_temperature,
            top_p=config.ollama_top_p,
            top_k=config.ollama_top_k,
            min_p=config.ollama_min_p,
        )

    def ensure_installed(self) -> None:
        self._request_json("/api/version", timeout=2.0)
        payload = self._request_json("/api/tags", timeout=3.0)
        models = payload.get("models")
        installed: set[str] = set()
        if isinstance(models, list):
            for item in models:
                if not isinstance(item, dict):
                    continue
                for key in ("name", "model"):
                    value = item.get(key)
                    if isinstance(value, str):
                        installed.add(value)
        if self.model not in installed:
            raise OllamaModelUnavailableError(
                f"The configured model '{self.model}' is not installed. "
                f"Install it explicitly with: ollama pull {self.model}"
            )

    def ensure_available(self) -> None:
        self.ensure_installed()
        if self.thinking:
            return
        profile = self.model_profile()
        if self.is_thinking_only_profile(profile):
            metadata = profile.get("model_info") if isinstance(profile, dict) else None
            version = metadata.get("general.version") if isinstance(metadata, dict) else None
            suffix = f"-{version}" if isinstance(version, str) and version else ""
            raise OllamaThinkingRequiredError(
                f"The installed '{self.model}' artifact is Qwen3 Thinking{suffix}, "
                "which cannot disable reasoning. Solace will not expose that reasoning or "
                "download a replacement automatically. Configure a non-thinking-capable "
                "local model before starting chat."
            )

    def model_profile(self) -> dict[str, Any]:
        return self._request_json(
            "/api/show",
            payload={"model": self.model, "verbose": False},
            timeout=3.0,
        )

    @staticmethod
    def is_thinking_only_profile(profile: dict[str, Any]) -> bool:
        metadata = profile.get("model_info")
        if not isinstance(metadata, dict):
            return False
        finetune = metadata.get("general.finetune")
        return isinstance(finetune, str) and finetune.strip().lower() == "thinking"

    def preload(self) -> None:
        """Load the configured model once and retain it for the active session."""
        self._used_model = True
        try:
            self._request_json(
                "/api/generate",
                payload={
                    "model": self.model,
                    "stream": False,
                    "keep_alive": self.keep_alive,
                },
                timeout=self.request_timeout_seconds,
            )
        except _OllamaHTTPError as exc:
            self._raise_response_error(exc)

    def unload(self, *, force: bool = False) -> None:
        """Release this model, but do not disturb it if this adapter never used it."""
        if not force and not self._used_model:
            return
        try:
            self._request_json(
                "/api/generate",
                payload={"model": self.model, "stream": False, "keep_alive": 0},
                timeout=30.0,
            )
        except _OllamaHTTPError as exc:
            self._raise_response_error(exc)
        finally:
            self._used_model = False

    def running_model(self) -> RunningModelInfo | None:
        payload = self._request_json("/api/ps", timeout=2.0)
        models = payload.get("models")
        if not isinstance(models, list):
            return None
        for item in models:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if name != self.model:
                continue
            return RunningModelInfo(
                name=name,
                size=self._nonnegative_int(item.get("size")),
                size_vram=self._nonnegative_int(item.get("size_vram")),
                context_length=self._nonnegative_int(item.get("context_length")),
                expires_at=item.get("expires_at")
                if isinstance(item.get("expires_at"), str)
                else None,
            )
        return None

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        content = "".join(event.content for event in self.chat_stream(messages))
        if not content.strip():
            raise OllamaResponseError("Ollama returned no final response content")
        return content.strip()

    def chat_stream(self, messages: Sequence[ChatMessage]) -> Iterator[ChatStreamEvent]:
        request_body = self._chat_request(messages)
        started = time.perf_counter()
        first_content_seconds: float | None = None
        visible_content = False
        final_received = False
        self.last_metrics = None
        self._used_model = True

        try:
            payloads = self._response_payloads(request_body)
            for payload in payloads:
                error = payload.get("error")
                if isinstance(error, str) and error:
                    raise OllamaResponseError(f"Ollama request failed: {error}")
                message = payload.get("message")
                if isinstance(message, dict):
                    thinking = message.get("thinking")
                    if not self.thinking and isinstance(thinking, str) and thinking:
                        raise OllamaResponseError(
                            "Ollama generated reasoning even though thinking was disabled"
                        )
                    content = message.get("content")
                    if isinstance(content, str) and content:
                        if first_content_seconds is None:
                            first_content_seconds = time.perf_counter() - started
                        visible_content = True
                        yield ChatStreamEvent(content=content)
                if payload.get("done") is True:
                    if not visible_content:
                        raise OllamaResponseError("Ollama returned no final response content")
                    final_received = True
                    metrics = InferenceMetrics.from_payload(
                        payload,
                        wall_seconds=time.perf_counter() - started,
                        first_content_seconds=first_content_seconds,
                    )
                    self.last_metrics = metrics
                    yield ChatStreamEvent(metrics=metrics)
        except _OllamaHTTPError as exc:
            self._raise_response_error(exc)
        if not final_received:
            raise OllamaResponseError("Ollama ended the stream without completion metrics")

    def _chat_request(self, messages: Sequence[ChatMessage]) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [message.as_dict() for message in messages],
            "stream": self.streaming,
            "think": self.thinking,
            "keep_alive": self.keep_alive,
            "options": {
                "num_ctx": self.context_window,
                "num_predict": self.max_output_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "min_p": self.min_p,
            },
        }

    def _response_payloads(self, request_body: dict[str, Any]) -> Iterator[dict[str, Any]]:
        if self.streaming:
            yield from self._stream_json(
                "/api/chat",
                payload=request_body,
                timeout=self.request_timeout_seconds,
            )
            return
        yield self._request_json(
            "/api/chat",
            payload=request_body,
            timeout=self.request_timeout_seconds,
        )

    def _stream_json(
        self,
        path: str,
        *,
        payload: dict[str, Any],
        timeout: float,
    ) -> Iterator[dict[str, Any]]:
        request = self._request(path, payload)
        try:
            with urlopen(request, timeout=timeout) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    decoded = json.loads(raw_line)
                    if not isinstance(decoded, dict):
                        raise OllamaResponseError("Ollama returned an unexpected stream event")
                    yield decoded
        except HTTPError as exc:
            raise _OllamaHTTPError(exc.code, self._http_error_detail(exc)) from exc
        except TimeoutError as exc:
            raise self._timeout_error(timeout) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise self._timeout_error(timeout) from exc
            raise self._unavailable_error() from exc
        except OSError as exc:
            raise self._unavailable_error() from exc
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise OllamaResponseError("Ollama returned invalid streaming JSON") from exc

    def _request_json(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout: float,
    ) -> dict[str, Any]:
        request = self._request(path, payload)
        try:
            with urlopen(request, timeout=timeout) as response:
                decoded = json.load(response)
        except HTTPError as exc:
            raise _OllamaHTTPError(exc.code, self._http_error_detail(exc)) from exc
        except TimeoutError as exc:
            raise self._timeout_error(timeout) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise self._timeout_error(timeout) from exc
            raise self._unavailable_error() from exc
        except OSError as exc:
            raise self._unavailable_error() from exc
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise OllamaResponseError("Ollama returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise OllamaResponseError("Ollama returned an unexpected response")
        return decoded

    def _request(self, path: str, payload: dict[str, Any] | None) -> Request:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        return Request(f"{self.base_url}{path}", data=data, headers=headers)

    def _raise_response_error(self, error: _OllamaHTTPError) -> None:
        if error.status == 404:
            raise OllamaModelUnavailableError(
                f"The configured model '{self.model}' is unavailable. "
                f"Install it explicitly with: ollama pull {self.model}"
            ) from error
        raise OllamaResponseError(f"Ollama request failed: {error.detail}") from error

    @staticmethod
    def _nonnegative_int(value: Any) -> int | None:
        return value if type(value) is int and value >= 0 else None

    @staticmethod
    def _timeout_error(timeout: float) -> OllamaTimeoutError:
        return OllamaTimeoutError(
            f"Local inference did not finish within {timeout:g} seconds. "
            "The model may still be warming up or generating too slowly."
        )

    def _unavailable_error(self) -> OllamaUnavailableError:
        return OllamaUnavailableError(
            f"Ollama is unavailable at {self.base_url}. Start Ollama and try again."
        )

    @staticmethod
    def _http_error_detail(error: HTTPError) -> str:
        try:
            decoded = json.loads(error.read().decode("utf-8"))
            detail = decoded.get("error") if isinstance(decoded, dict) else None
            if isinstance(detail, str) and detail:
                return detail
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        return f"HTTP {error.code}"

    @staticmethod
    def _validate_local_url(base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("ollama_base_url must be a valid local HTTP(S) URL")
        try:
            is_loopback = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            is_loopback = parsed.hostname.lower() == "localhost"
        if not is_loopback:
            raise ValueError("Solace only permits a loopback Ollama server")
