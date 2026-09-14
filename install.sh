#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${HOME}/.local/bin"
BMH_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bin/bmh"

mkdir -p "$TARGET_DIR"

echo "Installing bmh symlink to ${TARGET_DIR}/bmh..."
ln -sf "$BMH_SOURCE" "${TARGET_DIR}/bmh"

echo "Done! 'bmh' is installed at ${TARGET_DIR}/bmh."
echo "Run 'bmh --help' or 'bmh' to test."
