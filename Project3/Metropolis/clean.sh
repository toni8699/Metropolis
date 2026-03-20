#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"

rm -rf "$BIN_DIR"
echo "Clean successful."
