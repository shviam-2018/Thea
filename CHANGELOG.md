# Changelog

All notable Solace changes will be recorded here.

## 0.2.0-alpha.1 - 2026-08-29

First Solace v2 prerelease foundation.

- Target Python 3.12 for development and package installation.
- Add configuration-driven CPU-friendly model defaults.
- Add local `/status` reporting for system, AI, memory, and storage state.
- Add interface-independent local chat through `qwen3:4b` and Ollama.
- Add bounded short-term context and append-only JSONL conversation history.
- Add `/help`, `/status`, `/new`, `/history`, and `/quit` interactive commands.
- Add streamed local responses through the interface-independent companion API.
- Send `think: false` for normal chat and reject thinking-only artifacts instead of exposing reasoning.
- Add cold/warm `/benchmark` timing, token throughput, RAM, and processor reporting.
- Tune the laptop profile to a 4096 context, 128 response tokens, 10-minute keep-alive, and documented Qwen non-thinking sampling.
- Preload once per active session and explicitly unload on normal exit.
- Extend `/status` with thinking, streaming, context, response limit, keep-alive, and model-load state.
- Preserve the historical `v0.1.0` version line by starting Solace v2 at `0.2.0-alpha.1`.

## 0.1.0

Historical Thea release. This version predates the Solace v2 architecture.
