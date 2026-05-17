#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BIN_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)/bin"

rm -rf "$BIN_DIR"
echo "Clean successful."
