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
- Keep Qwen reasoning in Ollama's structured thinking field and persist only final replies.
- Preserve the historical `v0.1.0` version line by starting Solace v2 at `0.2.0-alpha.1`.

## 0.1.0

Historical Thea release. This version predates the Solace v2 architecture.
