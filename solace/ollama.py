"""Local-only Ollama chat adapter."""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import SolaceConfig
from .llm import ChatMessage


class OllamaError(RuntimeError):
    """Base class for expected local Ollama failures."""


class OllamaUnavailableError(OllamaError):
    """The configured local Ollama server cannot be reached."""


class OllamaTimeoutError(OllamaError):
    """Local inference exceeded the configured response timeout."""


class OllamaModelUnavailableError(OllamaError):
    """The configured model is not installed in Ollama."""


class OllamaResponseError(OllamaError):
    """Ollama returned an invalid or unsuccessful response."""


class _OllamaHTTPError(OllamaError):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.context_window = context_window
        self.max_output_tokens = max_output_tokens
        self.request_timeout_seconds = request_timeout_seconds
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
        )

    def ensure_available(self) -> None:
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

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        request_body = {
            "model": self.model,
            "messages": [message.as_dict() for message in messages],
            "stream": False,
            "think": True,
            "keep_alive": self.keep_alive,
            "options": {
                "num_ctx": self.context_window,
                "num_predict": self.max_output_tokens,
            },
        }
        try:
            payload = self._request_json(
                "/api/chat",
                payload=request_body,
                timeout=self.request_timeout_seconds,
            )
        except _OllamaHTTPError as exc:
            if exc.status == 404:
                raise OllamaModelUnavailableError(
                    f"The configured model '{self.model}' is unavailable. "
                    f"Install it explicitly with: ollama pull {self.model}"
                ) from exc
            raise OllamaResponseError(f"Ollama request failed: {exc.detail}") from exc

        message = payload.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise OllamaResponseError("Ollama returned no final response content")
        return content.strip()

    def _request_json(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout: float,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"{self.base_url}{path}", data=data, headers=headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                decoded = json.load(response)
        except HTTPError as exc:
            detail = self._http_error_detail(exc)
            raise _OllamaHTTPError(exc.code, detail) from exc
        except TimeoutError as exc:
            raise self._timeout_error(timeout) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise self._timeout_error(timeout) from exc
            raise OllamaUnavailableError(
                f"Ollama is unavailable at {self.base_url}. Start Ollama and try again."
            ) from exc
        except OSError as exc:
            raise OllamaUnavailableError(
                f"Ollama is unavailable at {self.base_url}. Start Ollama and try again."
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise OllamaResponseError("Ollama returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise OllamaResponseError("Ollama returned an unexpected response")
        return decoded

    @staticmethod
    def _timeout_error(timeout: float) -> OllamaTimeoutError:
        return OllamaTimeoutError(
            f"Local inference did not finish within {timeout:g} seconds. "
            "The model may still be warming up or generating too slowly."
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
