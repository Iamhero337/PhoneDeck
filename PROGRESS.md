# Progress and Changelog

This document tracks our recent fixes, improvements, and the current working state of PhoneDeck.

## What's Working (Core Features)

- **App UI & Navigation:** The Android application UI is fully complete using Jetpack Compose, featuring a gorgeous dark mode design, connection status badges, and tile grids.
- **Auto-Discovery:** mDNS (Zeroconf) server discovery works reliably. The app successfully finds the desktop server over local Wi-Fi without manual IP entry.
- **Auto-Reconnect:** The app automatically reconnects with exponential backoff if the connection drops.
- **WebSocket Communication:** Near instantaneous, two-way communication between the phone and the desktop, with heartbeat monitoring.
- **Cross-Platform Foundation:** The Python server runs effectively on Windows, macOS, and Linux, with proper daemonization/systemd background support on Linux and Windows.
- **Desktop Config Web UI:** Browser-based tile and page editor at http://localhost:9091 with app scanning.
- **Real-Time Config Sync:** Push configuration from desktop web UI to phone instantly.
- **Dynamic Top Sites:** Users can add websites dynamically in the Android app and have them immediately saved and mapped to the desktop's default browser.
- **PC Power Control:** Restart, shutdown, logout, sleep, and hibernate your computer remotely.
- **Custom Pages & Tiles:** Full UI for creating, editing, reordering, and deleting custom pages and tiles.
- **Import/Export Configuration:** Backup and restore entire layout as JSON.
- **Haptic Feedback:** Optional vibration on tile press.
- **Settings Screen:** Comprehensive settings for connection, feedback, pages, backup, and about.

## v1.4.0 - Desktop Config Web UI

### New Features
1. **Desktop Config Web UI:**
   - Built-in HTTP server on port 9091 serves a full customization interface
   - View all pages and tiles with live preview
   - Add, edit, and delete tiles directly from the browser
   - Create, rename, and delete pages
   - Dark theme matching the Android app

2. **App Scanner:**
   - Auto-detects installed applications on Linux (parses .desktop files)
   - Auto-detects installed applications on macOS (scans /Applications)
   - Auto-detects installed applications on Windows (scans Start Menu)
   - One-click add: pick an app and it becomes a tile instantly

3. **Real-Time Config Sync:**
   - "Sync to Phone" button pushes config to all connected devices
   - Phone receives config_sync via WebSocket and updates immediately
   - Server persists config to ~/.phonedeck/config.json
   - Phone defers to server-synced config after first sync (no overwrite conflicts)

4. **Phone Config Upload:**
   - Phone sends its current pages to server on first connection
   - Server serves phone's config to the web UI

### Changes
- Design page removed from Android defaults (Figma, Photoshop tiles)
- ConfigRepository supports full server-side config overrides
- MainViewModel handles config_sync WebSocket messages
- Installer scripts work from both project root and release folder layouts
- Installers display Config UI URL after installation

### Removed
- Hardcoded Design page from default pages (now customizable via web UI)

## v1.3.1 Fixes

### Manual Connect
- Full-width layout in Settings with prominent Connect/Disconnect buttons
- "Connect to Desktop" FilledTonalButton on main screen when disconnected
- Auto-detected IP shown with WiFi icon
- Connect dialog from main screen lets you enter IP and connect directly

### Update Checker
- Now uses semantic version comparison (`isNewerVersion`)
- Only shows dialog when GitHub release is actually newer than local version
- No more false "update available" when local dev version exceeds latest release

### Auto-Connect
- Toggle in Settings is now respected by the discovery service
- Server IP is still discovered and displayed for manual use
- Connection only happens automatically when toggle is enabled

### Build System
- `build.sh` extracts version dynamically from `build.gradle.kts`
- APK copied to `downloads/PhoneDeck-v{VERSION}.apk`
- Linux binary built and copied to `downloads/phonedeck-server-linux-v{VERSION}`
- Old artifacts cleaned before build

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

5. **Installation Scripts:**
   - Linux: `install_linux.sh` (systemd user service with linger)
   - macOS: `install_macos.sh` (LaunchAgent)
   - Windows: `install_windows.bat` (Startup shortcut + dependency install)

6. **UI/UX Improvements:**
   - Material 3 design with consistent theming
   - Connection badge with live status
   - Snackbar notifications for commands
   - Add Top Site dialog with validation
   - Settings dialog with organized sections
   - Export dialog with copy-to-clipboard
   - Import dialog with JSON validation

### Critical Bug Fixes (v1.2.0)

1. **WebSocket Connection Fixed:** Removed `/ws` path mismatch. Added OkHttp ping interval (15s) for connection keepalive.

2. **Auto-Reconnect Added:** Exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max).

3. **Missing `ifaddr` Dependency:** Added to requirements and auto-install logic.

---

*Last Updated: July 2026 - v1.4.0*
