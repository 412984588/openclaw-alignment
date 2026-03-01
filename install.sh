#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[openclaw-alignment] Installing from source..."
exec "$ROOT_DIR/scripts/install_unix.sh" "$@"
