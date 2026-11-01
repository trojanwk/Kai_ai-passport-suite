#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Create .venv and install requirements-dev.txt first." >&2; exit 1; }
"$PYTHON" -m unittest discover -s tests -v
"$PYTHON" skills/ai-hermes-self-evolve/scripts/validate_ai_routing.py
bash scripts/build_passport_suite.sh device
"$PYTHON" tools/package_firmware.py
