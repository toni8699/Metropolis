#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

rm -rf "$BACKEND_DIR/.venv" "$BACKEND_DIR/__pycache__"
find "$BACKEND_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "Clean successful."
