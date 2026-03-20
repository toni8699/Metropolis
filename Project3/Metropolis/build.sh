#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
BIN_DIR="$SCRIPT_DIR/bin"

mkdir -p "$BIN_DIR"
javac -d "$BIN_DIR" "$SRC_DIR/main.java" "$SRC_DIR/options.java"
echo "Build successful."
