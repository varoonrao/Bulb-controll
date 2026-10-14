#!/data/data/com.termux/files/usr/bin/bash
# Start the bulb web app (Termux on Android, or any Linux/macOS shell).
cd "$(dirname "$0")"
command -v termux-wake-lock >/dev/null && termux-wake-lock   # keep Termux alive with the screen off
echo "Open http://localhost:8000 in Chrome on this phone"
exec python web.py
