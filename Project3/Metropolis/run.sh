#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"

if [ ! -f "$BIN_DIR/main.class" ]; then
  echo "No build found. Run ./build.sh first."
  exit 1
fi

java -cp "$BIN_DIR:${CLASSPATH:-.}" main
