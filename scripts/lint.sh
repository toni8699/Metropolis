#!/usr/bin/env bash
# Lint backend before push (same checks as CI). Run from repo root: ./scripts/lint.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v ruff >/dev/null 2>&1; then
  echo "Install ruff: cd backend && uv sync --extra dev   (or: pip install 'ruff>=0.6,<0.8')"
  exit 1
fi

echo "==> ruff check"
(
  cd backend
  ruff check --fix metropolis tests scripts
)
ruff check tests

echo "==> ruff format"
(
  cd backend
  ruff format metropolis tests scripts
)
ruff format tests

echo "OK"
