#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$BACKEND_DIR/.." && pwd)"

cd "$BACKEND_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

if [ -f "uv.lock" ]; then
  uv sync --frozen --extra dev >/dev/null
else
  uv sync --extra dev >/dev/null
fi

export FLASK_APP=run:app
export PORT="${PORT:-8080}"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a
fi

exec uv run --no-sync flask run --host 0.0.0.0 --port "$PORT"
