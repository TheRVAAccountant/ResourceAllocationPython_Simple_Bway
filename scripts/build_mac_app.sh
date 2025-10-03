#!/usr/bin/env bash
set -euo pipefail

# Build a macOS .app bundle with PyInstaller using the high‑res app icon.
# Requires: pyinstaller (pip install pyinstaller) and app.icns present.

APP_NAME="Resource Management System"
IDENTIFIER="com.resourceallocation.app"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MAIN_MODULE="src/gui/main_window.py"
ICON_PATH="$BASE_DIR/assets/icons/app.icns"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "error: pyinstaller not found. Run: pip install pyinstaller" >&2
  exit 1
fi

if [[ ! -f "$ICON_PATH" ]]; then
  echo "warning: $ICON_PATH not found. Dock icon may default to Python."
fi

pyinstaller \
  --windowed \
  --name "$APP_NAME" \
  --icon "$ICON_PATH" \
  --osx-bundle-identifier "$IDENTIFIER" \
  --noconfirm \
  "$MAIN_MODULE"

echo "Built dist/$APP_NAME.app"

