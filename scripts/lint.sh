#!/usr/bin/env bash
# Lint backend before push (same checks as CI). Run from repo root: ./scripts/lint.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

(
  cd backend
  uv sync --frozen --extra dev
)

echo "==> ruff check"
(
  cd backend
  uv run ruff check --fix .
)

echo "==> ruff format"
(
  cd backend
  uv run ruff format .
)

echo "OK"
