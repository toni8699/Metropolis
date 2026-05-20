#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

uv export \
  --frozen \
  --all-extras \
  --no-hashes \
  --no-emit-project \
  --output-file requirements.txt

echo "requirements.txt exported from uv.lock."
