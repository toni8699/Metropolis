#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="$BACKEND_DIR/bin"
LIB_DIR="$BACKEND_DIR/lib"
PG_JAR="$LIB_DIR/postgresql.jar"

if [ ! -f "$BIN_DIR/main.class" ]; then
  echo "No build found. Run ./backend/scripts/build.sh first."
  exit 1
fi

if [ -f "$BACKEND_DIR/../.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$BACKEND_DIR/../.env"
  set +a
fi

java -cp "$BIN_DIR:$PG_JAR" main
