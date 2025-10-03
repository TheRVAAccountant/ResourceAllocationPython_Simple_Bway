#!/usr/bin/env bash
set -euo pipefail

# Generate a macOS .icns icon from a 1024×1024 PNG using built-in macOS tools.
# Requirements: macOS with `sips` and `iconutil` available.

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_PNG="$HERE/app_1024.png"
ICONSET_DIR="$HERE/icon.iconset"
OUT_ICNS="$HERE/app.icns"

if [[ ! -f "$SRC_PNG" ]]; then
  echo "error: $SRC_PNG not found. Place a 1024x1024 PNG there first." >&2
  exit 1
fi

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

sizes=(16 32 64 128 256 512)
for size in "${sizes[@]}"; do
  # 1x
  sips -z "$size" "$size" "$SRC_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
  # 2x (retina) except for 1024 (generated separately below)
  dbl=$((size*2))
  sips -z "$dbl" "$dbl" "$SRC_PNG" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
done

# 1024 x 1024 (1x for the 512x512@2x slot is already covered above)
sips -z 1024 1024 "$SRC_PNG" --out "$ICONSET_DIR/icon_1024x1024.png" >/dev/null

iconutil -c icns "$ICONSET_DIR" -o "$OUT_ICNS"
echo "Created $OUT_ICNS"

