# Solace v2

Solace is a private, local-first AI wellbeing companion. Version 2 is being rebuilt for modest laptop hardware and CPU-friendly inference; it does not require CUDA, an NVIDIA GPU, or an Internet service for resource reporting.

This branch contains the first v2 local-chat milestone: an interface-independent companion engine, local Ollama adapter, bounded context, JSONL conversation persistence, and resource reporting. The legacy Thea prototype remains in `code/` as reference and is not the v2 runtime.

The current Solace v2 prerelease is `0.2.0-alpha.1`. Python package tooling exposes the normalized PEP 440 version `0.2.0a1` from the same authoritative version value.

## Baseline hardware and models

The initial development target is a Ryzen 5 7530U laptop with 16 GB RAM and integrated Radeon graphics. The supported baseline is deliberately small:

- Chat: `qwen3:4b`
- Embeddings: `nomic-embed-text:latest` (768 dimensions)
- One chat model and one embedding model installed during normal development
- A bounded 24-message short-term context, with selective Mem0 retrieval planned for long-term memory

An 8B-class chat model may be configured on stronger hardware, but is not the default. Solace will not download models automatically. Before adding one, check its Ollama package size and available disk space. Models in the 14B, 30B, or 70B classes are outside this laptop's target profile.

The baseline models and limits are configuration-driven in [`config/solace.example.json`](config/solace.example.json). If the embedding model changes, its vector dimensions must also be verified and changed before creating or reusing a Qdrant collection.

## Run the current foundation

Solace targets Python 3.12. A globally installed Python 3.14 interpreter is not the project runtime and is not required. Create and activate the Windows development environment from the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Then run the test suite and start the companion inside the activated environment:

```powershell
python -m unittest discover -s tests -v
python -m solace
```

Status and version remain available without starting an interactive conversation:

```powershell
python -m solace /status
solace --version
```

The status command also accepts `status` for shell convenience:

```powershell
python -m solace status
```

No Python runtime dependencies are needed for `/status`. It uses standard operating-system APIs, queries the configured Ollama/Qdrant endpoints, and remains useful when those services are unavailable. When Ollama is running and the embedding model is installed, the command checks its reported native vector length against `embedding_dimensions` without loading the model for inference.

Interactive chat uses only the configured loopback Ollama server and `qwen3:4b`. It has no cloud or remote fallback and never downloads a model. If either Ollama or the configured model is missing, Solace exits with an actionable local error. The installed Qwen template ignores its non-thinking controls, so Solace uses Ollama's supported structured thinking mode and returns only `message.content`; `message.thinking` is never displayed or persisted. No reasoning text is parsed or stripped after generation.

## Chat commands

- `/help` lists available commands.
- `/status` shows live resource information without ending the conversation.
- `/new` starts a fresh session and clears only the in-memory short-term context.
- `/history` shows the current session and up to five compact recent summaries.
- `/quit` exits cleanly. Ctrl+C and Ctrl+D are also supported.

The core `Companion.respond(user_text)` API returns a reply string and has no terminal input/output dependency. This keeps future voice, desktop, and web clients separate from the conversation engine.

## Configuration

Pass a JSON file directly:

```powershell
python -m solace /status --config config/solace.example.json
```

Alternatively, set `SOLACE_CONFIG` to the JSON file path. `SOLACE_DATA_DIR` can override the platform data directory without changing the file. Defaults are:

- Windows: `%LOCALAPPDATA%\Solace`
- macOS: `~/Library/Application Support/Solace`
- Linux: `$XDG_DATA_HOME/solace` or `~/.local/share/solace`

Conversation and local Qdrant data live below that one directory so storage reporting is bounded and data is not duplicated by the application. Ollama manages model files separately.

Complete user and assistant messages are appended to one JSONL file per session under the platform data directory's `conversations/` folder. Each record contains an ISO 8601 timestamp, role, and content. Only the most recent 24 messages are sent back to Ollama; older messages remain on disk but do not expand the inference context. The default Ollama token context is separately capped at 4096 and each response at 256 tokens for this laptop profile.

## Resource policy

The v2 implementation should preserve these constraints as it grows:

- Inference must remain functional on CPU; GPU use is optional.
- Do not keep models loaded longer than useful (`ollama_keep_alive` defaults to `2m`).
- Do not compensate for memory design by using a huge context window.
- Store long-term memories selectively and retrieve only relevant items.
- Do not automatically pull a model or install multiple experimental LLMs.
- Keep all resource reporting local and tolerate missing services.

## Safety

Solace is not a licensed therapist, medical device, crisis service, or substitute for professional care. A production release will require explicit safety and crisis-response behavior beyond this infrastructure layer.

## License

This project is licensed under the [MIT License](LICENSE).
