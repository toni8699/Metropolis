#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

if [ -f "uv.lock" ]; then
  uv sync --frozen --extra dev
else
  uv sync --extra dev
fi

echo "Python dependencies synced with uv project."
