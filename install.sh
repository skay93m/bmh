#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# bmh Installer with Architecture Detection
# -----------------------------------------------------------------------------
OS="$(uname -s)"
ARCH="$(uname -m)"
BMH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BMH_SOURCE="${BMH_DIR}/bin/bmh"
TARGET_DIR="${HOME}/.local/bin"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧠 Basic Memory Helper (bmh) Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Architecture & Platform Detection
case "$OS" in
  Darwin)
    case "$ARCH" in
      arm64|aarch64)
        echo "🍏 Platform: macOS (Apple Silicon - arm64)"
        ;;
      x86_64)
        echo "🖥️  Platform: macOS (Intel - x86_64)"
        ;;
      *)
        echo "🍎 Platform: macOS (${ARCH})"
        ;;
    esac
    ;;
  Linux)
    echo "🐧 Platform: Linux (${ARCH})"
    ;;
  *)
    echo "💻 Platform: ${OS} (${ARCH})"
    ;;
esac

# 2. Ensure target directory exists
mkdir -p "$TARGET_DIR"

# 3. Create symlink
echo "🔗 Installing symlink: ${TARGET_DIR}/bmh -> ${BMH_SOURCE}"
ln -sf "$BMH_SOURCE" "${TARGET_DIR}/bmh"
chmod +x "$BMH_SOURCE"

# 4. Verify Dependencies
echo "🔍 Checking dependencies..."

has_jq=true
has_bm=true

if ! command -v jq >/dev/null 2>&1; then
  has_jq=false
  echo "⚠️  'jq' was not found in PATH."
  if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
      echo "   To install on Apple Silicon: brew install jq"
    else
      echo "   To install on Intel Mac:     brew install jq (or nix-env -iA nixpkgs.jq)"
    fi
  else
    echo "   To install on Linux:         sudo apt-get install jq (or your distro package manager)"
  fi
fi

if ! command -v bm >/dev/null 2>&1; then
  has_bm=false
  echo "⚠️  'bm' (Basic Memory) was not found in PATH."
  echo "   Make sure basic-memory is installed and available in your shell."
fi

# 5. PATH Verification
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
  echo ""
  echo "⚠️  Notice: ${TARGET_DIR} is not in your current PATH."
  echo "   Add it by running:"
  if [[ -f "$HOME/.zshrc" || "$SHELL" == *"zsh"* ]]; then
    echo "     echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
  else
    echo "     echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
  fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ "$has_jq" == "true" ]]; then
  echo "✨ Installation complete! Run 'bmh' to launch."
else
  echo "⚠️  Installation finished, but please install 'jq' to run bmh."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
