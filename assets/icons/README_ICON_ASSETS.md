High‑Resolution Icon Assets (macOS)

To get a crisp Dock icon on macOS, provide a high‑resolution app icon set.

Recommended files:
- app_1024.png: 1024×1024 PNG (source artwork)
- app.icns: Compiled multi‑size icon for macOS Dock and Finder

Generate app.icns from a 1024 PNG on macOS:
1) Place your 1024×1024 PNG at: assets/icons/app_1024.png
2) Run: assets/icons/generate_icns.sh
   - This creates assets/icons/icon.iconset/ and assets/icons/app.icns
3) Restart the app; the Dock icon should become sharp.

Notes:
- If app.icns is missing, the app falls back to app_1024.png; if both are missing, it falls back to the existing .ico (blurrier).
- For best results, use a 1024×1024 source with transparent background (PNG).

