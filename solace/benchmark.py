"""Small, local Ollama latency benchmark for the laptop inference profile."""

from __future__ import annotations

from dataclasses import dataclass

from .config import SolaceConfig
from .llm import ChatMessage, InferenceMetrics
from .ollama import OllamaChatAdapter, RunningModelInfo
from .prompt import SYSTEM_PROMPT
from .status import MemoryUsage, format_bytes, memory_usage


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    label: str
    metrics: InferenceMetrics


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    model: str
    thinking_disabled: bool
    context_window: int
    response_limit: int
    results: tuple[BenchmarkResult, ...]
    thinking_only_artifact: bool
    memory_before: MemoryUsage
    memory_loaded: MemoryUsage
    running_model: RunningModelInfo | None

    @property
    def ram_impact(self) -> int | None:
        if self.memory_before.used is None or self.memory_loaded.used is None:
            return None
        return self.memory_loaded.used - self.memory_before.used


BENCHMARK_CASES = (
    ("Cold simple", "Hey. Reply with one short, friendly sentence."),
    ("Warm simple", "Hi again. Reply with one short, natural sentence."),
    (
        "Warm medium",
        "I had a busy day and finally have a quiet evening. Respond naturally in two or three sentences.",
    ),
)


def run_local_benchmark(
    config: SolaceConfig,
    *,
    adapter: OllamaChatAdapter | None = None,
    unload_when_done: bool = True,
) -> BenchmarkReport:
    """Measure one cold and two warm requests without storing their text."""
    model = adapter or OllamaChatAdapter.from_config(config)
    model.ensure_installed()
    profile = model.model_profile()
    thinking_only = model.is_thinking_only_profile(profile)
    model.unload(force=True)
    before = memory_usage()
    results: list[BenchmarkResult] = []
    loaded_memory = before
    running: RunningModelInfo | None = None
    try:
        for label, prompt in BENCHMARK_CASES:
            messages = (
                ChatMessage("system", SYSTEM_PROMPT),
                ChatMessage("user", prompt),
            )
            for _event in model.chat_stream(messages):
                pass
            if model.last_metrics is None:
                raise RuntimeError(f"Ollama returned no metrics for {label}")
            results.append(BenchmarkResult(label, model.last_metrics))
            if len(results) == 1:
                loaded_memory = memory_usage()
                running = model.running_model()
        return BenchmarkReport(
            model=model.model,
            thinking_disabled=not model.thinking,
            context_window=model.context_window,
            response_limit=model.max_output_tokens,
            results=tuple(results),
            thinking_only_artifact=thinking_only,
            memory_before=before,
            memory_loaded=loaded_memory,
            running_model=running,
        )
    finally:
        if unload_when_done:
            model.unload(force=True)


def _seconds(value: float | None) -> str:
    return f"{value:.3f} s" if value is not None else "unknown"


def _rate(value: float | None) -> str:
    return f"{value:.1f} tok/s" if value is not None else "unknown"


def format_benchmark(report: BenchmarkReport) -> str:
    lines = [
        "Local inference benchmark",
        f"Model: {report.model}",
        f"Thinking request: {'disabled' if report.thinking_disabled else 'enabled'}",
        f"Context: {report.context_window}",
        f"Response limit: {report.response_limit}",
    ]
    if report.thinking_only_artifact:
        lines.extend(
            (
                "Compatibility: FAIL - installed artifact is thinking-only",
                "Note: first-content timing below is reasoning content and is not safe to show as a reply.",
            )
        )
    for result in report.results:
        metrics = result.metrics
        lines.extend(
            (
                "",
                f"{result.label}:",
                f"Load: {_seconds(metrics.load_seconds)}",
                f"First content: {_seconds(metrics.first_content_seconds)}",
                f"Total: {_seconds(metrics.total_seconds or metrics.wall_seconds)}",
                f"Prompt: {_rate(metrics.prompt_tokens_per_second)}",
                f"Generation: {_rate(metrics.generation_tokens_per_second)}",
                f"Tokens: prompt {metrics.prompt_eval_count or 0} / generated {metrics.eval_count or 0}",
                f"Stop: {metrics.done_reason or 'unknown'}",
            )
        )
    lines.extend(("", f"Approx. system RAM change while loaded: {format_bytes(report.ram_impact)}"))
    if report.running_model is not None:
        lines.append(
            "Ollama model allocation: "
            f"{format_bytes(report.running_model.size)} ({report.running_model.processor})"
        )
    return "\n".join(lines)
