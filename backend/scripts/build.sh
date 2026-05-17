#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$BACKEND_DIR/src"
BIN_DIR="$BACKEND_DIR/bin"
LIB_DIR="$BACKEND_DIR/lib"
PG_JAR="$LIB_DIR/postgresql.jar"
PG_VERSION="42.7.4"

mkdir -p "$BIN_DIR" "$LIB_DIR"

if [ ! -f "$PG_JAR" ]; then
  echo "Downloading PostgreSQL JDBC driver..."
  curl -fsSL "https://jdbc.postgresql.org/download/postgresql-${PG_VERSION}.jar" -o "$PG_JAR"
fi

javac -cp "$PG_JAR" -d "$BIN_DIR" \
  "$SRC_DIR/Database.java" \
  "$SRC_DIR/RentalService.java" \
  "$SRC_DIR/options.java" \
  "$SRC_DIR/main.java"

echo "Build successful."
