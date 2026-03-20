#!/usr/bin/env bash
# Rigenera resources/ami.icns da resources/ami.png (macOS: sips + iconutil).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/resources/ami.png"
SET="${TMPDIR:-/tmp}/ami.iconset.$$"
OUT="$ROOT/resources/ami.icns"
[[ -f "$SRC" ]] || { echo "Missing $SRC"; exit 1; }
rm -rf "$SET"
mkdir -p "$SET"
sips -z 16 16     "$SRC" --out "$SET/icon_16x16.png"       >/dev/null
sips -z 32 32     "$SRC" --out "$SET/icon_16x16@2x.png"    >/dev/null
sips -z 32 32     "$SRC" --out "$SET/icon_32x32.png"      >/dev/null
sips -z 64 64     "$SRC" --out "$SET/icon_32x32@2x.png"    >/dev/null
sips -z 128 128   "$SRC" --out "$SET/icon_128x128.png"    >/dev/null
sips -z 256 256   "$SRC" --out "$SET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "$SRC" --out "$SET/icon_256x256.png"    >/dev/null
sips -z 512 512   "$SRC" --out "$SET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "$SRC" --out "$SET/icon_512x512.png"    >/dev/null
sips -z 1024 1024 "$SRC" --out "$SET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$SET" -o "$OUT"
rm -rf "$SET"
echo "OK: $OUT"
