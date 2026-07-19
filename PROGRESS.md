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
- **Custom Pages & Tiles:** Full UI for creating, editing, reordering, and deleting custom pages and tiles.
- **Import/Export Configuration:** Backup and restore entire layout as JSON.
- **Haptic Feedback:** Optional vibration on tile press.
- **Settings Screen:** Comprehensive settings for connection, feedback, pages, backup, and about.

## What's New in v1.3.0

### Major Features

1. **Complete Settings Screen:**
   - Connection settings (auto-connect, server port)
   - Feedback settings (haptic feedback toggle)
   - Page management (add custom pages, reset to defaults)
   - Backup & Restore (export/import JSON configuration)
   - About section with GitHub link

2. **Full Customization System:**
   - Add unlimited custom pages with custom names
   - Add/edit/delete tiles on any custom page
   - Per-tile customization: label, icon, command, background color, icon color
   - Drag-to-reorder pages (in settings)
   - Long-press tiles for context menu (edit/delete)

3. **Configuration Persistence:**
   - All custom pages and tiles saved to SharedPreferences
   - Top Sites persisted separately
   - Default pages protected from deletion
   - JSON export/import for sharing layouts

4. **Enhanced Python Server:**
   - Modular command handling with clear OS separation
   - Added brightness control for Windows (via WMI)
   - Added sleep command for Windows
   - Improved screenshot detection (spectacle, grim, scrot, gnome-screenshot, import)
   - Better error messages for missing dependencies
   - Version flag (`--version`) for CI/CD
   - Cleaner shutdown handling

5. **Build System & CI/CD:**
   - GitHub Actions workflow for multi-platform builds (Linux, Windows, macOS)
   - Automated release asset uploads
   - Unified build script (`build.sh`)
   - Updated PyInstaller specs with all hidden imports

6. **Installation Scripts:**
   - Linux: `install_linux.sh` (systemd user service with linger)
   - macOS: `install_macos.sh` (LaunchAgent)
   - Windows: `install_windows.bat` (Startup shortcut + dependency install)

7. **UI/UX Improvements:**
   - Material 3 design with consistent theming
   - Connection badge with live status
   - Snackbar notifications for commands
   - Add Top Site dialog with validation
   - Settings dialog with organized sections
   - Export dialog with copy-to-clipboard
   - Import dialog with JSON validation

### Critical Bug Fixes (v1.2.0)

1. **WebSocket Connection Fixed:**
   - *Bug:* The Android app was connecting to `ws://host:9090/ws` but the server only listens on the root path `ws://host:9090`. **This made connection impossible.**
   - *Fix:* Removed the `/ws` path from the WebSocket URL. Also added OkHttp ping interval (15s) for connection keepalive.

2. **Auto-Reconnect Added:**
   - *Bug:* Previously, if the WebSocket connection dropped (server restart, network hiccup), the app would stay disconnected forever requiring manual reconnect.
   - *Fix:* Implemented automatic reconnection with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max). The app will continuously try to restore the connection.

3. **Missing `ifaddr` Dependency:**
   - *Bug:* The server used `ifaddr` for smart IP selection but it was never listed in `requirements.txt` or auto-installed.
   - *Fix:* Added `ifaddr>=0.2.0` to requirements and added auto-install logic in server.py.

### Technical Improvements

- **Android:** Upgraded to Compose BOM 2024.06.01, Kotlin 1.9.23, AGP 8.4.0
- **Dependencies:** Added kotlinx.serialization for type-safe JSON config
- **Python:** Added `updater` to hidden imports for PyInstaller
- **Version:** Bumped to v1.3.0 across all components

## Recent Fixes (v1.1.4)

In our previous iteration, we tackled various critical bugs reported on the Linux environment:

1. **Top Sites Navigation Overflow:** Upgraded page tabs to be horizontally scrollable.
2. **Universal Browser Launching:** Using Python `webbrowser` library instead of OS-specific wrappers.
3. **Smart Spotify Launching:** Checks for native Spotify install, falls back to web version.
4. **Linux Screen Brightness:** Prioritizes user-level tools before attempting sysfs writes.
5. **Linux Screenshots:** Expanded toolchain to support spectacle, gnome-screenshot, grim, scrot, and import.
6. **IP Resolution:** Uses `ifaddr` to filter out VPN/Docker virtual adapters.

## Upcoming Improvements

- [ ] Expand Windows control sets (brightness, advanced media keys, app launchers)
- [ ] Allow users to fully edit default pages and swap out application icons without recompiling the Android APK
- [ ] Add screen mirroring/streaming capability
- [ ] Add plugin system for custom commands
- [ ] Add support for multiple simultaneous connections
- [ ] Add authentication/encryption option for WebSocket
- [ ] Create F-Droid and Play Store listings
- [ ] Add Tile templates for common applications
- [ ] Implement dark/light theme toggle
- [ ] Add keyboard shortcuts display on long-press

---

*Last Updated: July 2026 - v1.3.0*