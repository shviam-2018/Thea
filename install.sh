#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null; then
    echo "Python 3.12 is required." >&2
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then
    echo "Solace targets Python 3.12; create the environment with Python 3.12." >&2
    exit 1
fi

# Installs only the Solace Python package. Ollama models are always user-selected
# and must be pulled explicitly so setup never consumes several GB unexpectedly.
python3 -m pip install -e .

echo "Solace installed. Run: solace /status"
