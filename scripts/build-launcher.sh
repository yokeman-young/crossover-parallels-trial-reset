#!/bin/bash
# Build a tiny .app that runs: trialreset launch <key>
# usage: ./build-launcher.sh <key> [output.app]
set -euo pipefail
KEY="${1:?usage: build-launcher.sh <key> [out.app]}"
OUT="${2:-$HOME/Applications/$(echo "$KEY" | awk '{print toupper(substr($0,1,1)) substr($0,2)}') (Trial Reset).app}"
TMP="$(mktemp -d)"
PYTHON="$(command -v python3)"
sed -e "s|__APP_KEY__|$KEY|" -e "s|__PYTHON__|$PYTHON|" "$(dirname "$0")/launcher.swift.in" > "$TMP/main.swift"
swiftc -O -o "$TMP/launcher" "$TMP/main.swift" -framework AppKit
rm -rf "$OUT"; mkdir -p "$OUT/Contents/MacOS"
cp "$TMP/launcher" "$OUT/Contents/MacOS/launcher"
cat > "$OUT/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIdentifier</key><string>local.trialreset.launcher.$KEY</string>
  <key>CFBundleName</key><string>$(basename "$OUT" .app)</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>LSUIElement</key><true/>
</dict></plist>
PLIST
codesign --force --sign - "$OUT" >/dev/null 2>&1
echo "built: $OUT"
