# Progress and Changelog

This document tracks our recent fixes, improvements, and the current working state of PhoneDeck.

## What's Working (Core Features)

- **App UI & Navigation:** The Android application UI is fully complete using Jetpack Compose, featuring a gorgeous dark mode design, connection status badges, and tile grids.
- **Auto-Discovery:** mDNS (Zeroconf) server discovery works reliably. The app successfully finds the desktop server over local Wi-Fi without manual IP entry.
- **Auto-Reconnect:** The app automatically reconnects with exponential backoff if the connection drops.
- **WebSocket Communication:** Near instantaneous, two-way communication between the phone and the desktop, with heartbeat monitoring.
- **Cross-Platform Foundation:** The Python server runs effectively on Windows, macOS, and Linux, with proper daemonization/systemd background support on Linux and Windows.
- **Dynamic Top Sites:** Users can add websites dynamically in the Android app and have them immediately saved and mapped to the desktop's default browser.
- **PC Power Control:** Restart, shutdown, logout, sleep, and hibernate your computer remotely.

## What's New in v1.2.0

### Critical Bug Fixes

1. **WebSocket Connection Fixed:**
   - *Bug:* The Android app was connecting to `ws://host:9090/ws` but the server only listens on the root path `ws://host:9090`. **This made connection impossible.**
   - *Fix:* Removed the `/ws` path from the WebSocket URL. Also added OkHttp ping interval (15s) for connection keepalive.

2. **Auto-Reconnect Added:**
   - *Bug:* Previously, if the WebSocket connection dropped (server restart, network hiccup), the app would stay disconnected forever requiring manual reconnect.
   - *Fix:* Implemented automatic reconnection with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max). The app will continuously try to restore the connection.

3. **Missing `ifaddr` Dependency:**
   - *Bug:* The server used `ifaddr` for smart IP selection but it was never listed in `requirements.txt` or auto-installed.
   - *Fix:* Added `ifaddr>=0.2.0` to requirements and added auto-install logic in server.py.

### New Features

4. **PC Remote Power Control:**
   - Added `restart`, `shutdown`, `logout`, and `hibernate` commands
   - Works on Linux (systemctl), macOS (osascript), and Windows (shutdown.exe)
   - New tiles added to the System page with dedicated icons

5. **Improved systemd Installation:**
   - Install script now uses absolute paths instead of fragile `$(pwd)`
   - Creates a proper launcher script at `~/.local/bin/phonedeck-server`
   - Added `loginctl enable-linger` so user services start at boot
   - Changed restart policy from `on-failure` to `always` with 3s delay
   - Added `--install` flag for manual installation of PyInstaller builds

6. **Heartbeat Monitoring:**
   - Server pings all connected WebSocket clients every 30 seconds
   - Dead clients (no pong within 5s) are automatically cleaned up

7. **Command Feedback in App:**
   - Toast/snackbar notifications appear when commands are sent
   - Better visual feedback for user actions

8. **Semantic Version Comparison in Updater:**
   - Updater now compares versions numerically (e.g., v1.2.0 > v1.1.4)
   - Better handling of Linux updates for git vs PyInstaller builds

9. **Graceful Server Shutdown:**
   - Server properly handles SIGINT/SIGTERM signals
   - Cleans up mDNS registration on exit

### Technical Improvements

- **Windows PyInstaller spec:** Added `ifaddr` to hidden imports
- **Linux PyInstaller spec:** Added `ifaddr` to hidden imports
- **Version bumped to v1.2.0** across all components

## Recent Fixes (v1.1.4)

In our previous iteration, we tackled various critical bugs reported on the Linux environment:

1. **Top Sites Navigation Overflow:** Upgraded page tabs to be horizontally scrollable.
2. **Universal Browser Launching:** Using Python `webbrowser` library instead of OS-specific wrappers.
3. **Smart Spotify Launching:** Checks for native Spotify install, falls back to web version.
4. **Linux Screen Brightness:** Prioritizes user-level tools before attempting sysfs writes.
5. **Linux Screenshots:** Expanded toolchain to support spectacle, gnome-screenshot, grim, scrot, and import.
6. **IP Resolution:** Uses `ifaddr` to filter out VPN/Docker virtual adapters.

## Upcoming Improvements

- Expand Windows control sets (brightness, advanced media keys).
- Allow users to fully edit default pages and swap out application icons without recompiling the Android APK.
- Add screen mirroring/streaming capability.
