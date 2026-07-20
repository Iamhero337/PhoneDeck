# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-07-20

### Added
- **Desktop Config Web UI:** New web-based customization interface served by the Python server at http://localhost:9091
- **App Scanner:** Auto-detects installed applications on Linux (.desktop files), macOS (/Applications), and Windows (Start Menu)
- **Web UI Tile Management:** View, add, edit, and delete tiles from any browser
- **Web UI Page Management:** Create, rename, and delete pages from any browser
- **Real-Time Config Sync:** Push configuration from the desktop web UI to the phone instantly via WebSocket
- **Config Persistence on Desktop:** Server stores config in `~/.phonedeck/config.json`
- **Phone Config Upload:** Phone sends its current config to the server on first connect
- **Server Config Authority:** Phone defers to server-synced config after first sync (avoids overwrite conflicts)

### Changed
- **Design page removed** from Android default pages (customizable via web UI instead)
- **ConfigRepository** now supports full server-side config overrides via `serverConfig`
- **MainViewModel** handles `config_sync` WebSocket messages to apply desktop changes
- **Installer scripts** now work from both project root and release folder layouts
- **All installer scripts** show Config UI URL after installation

### Removed
- Hardcoded Design page (Figma, Photoshop tiles) from Android defaults

## [1.3.1] - 2026-07-19

### Fixed
- **Manual Connect UI completely overhauled:** Prominent connect/disconnect button with proper full-width layout in Settings screen; added "Connect to Desktop" button on main screen when disconnected
- **Update checker now uses semantic version comparison:** No more false "update available" dialog when local version is newer than GitHub release
- **Auto-connect toggle now respected:** Disabling auto-connect in settings prevents automatic connection on server discovery (IP is still shown for manual use)
- **build.sh rewritten:** Extracts version dynamically from `build.gradle.kts`, copies artifacts to `downloads/` folder, builds companion binary
- **Hardcoded versions updated:** Settings screen displays v1.3.1, config export uses correct version
- **Dead code removed:** Unreachable ConnectDialog in MainScreen replaced with working connect button
- **All documentation updated:** README, CHANGELOG, PROGRESS, RELEASE_RULES, ARCHITECTURE synced to v1.3.1

## [1.3.0] - 2026-07-19

### Added
- **Full Customization System:** Add, remove, reorder pages and tiles with custom colors and icons
- **Settings Screen:** Organized settings for Connection, Feedback, Pages & Tiles, Backup & Restore, About
- **Import/Export Configuration:** Backup and restore layouts as JSON (copy to clipboard or file)
- **Top Sites Management:** Add/remove dynamic website tiles with long-press delete
- **Haptic Feedback:** Optional vibration on tile press (configurable)
- **Export Dialog:** View and copy full JSON configuration
- **Import Dialog:** Paste JSON to restore configuration
- **Add Custom Page Dialog:** Create new pages from the Settings screen
- **Reset to Defaults:** One-tap reset with confirmation
- **macOS Install Script:** `install_macos.sh` creates LaunchAgent for auto-start
- **Windows Install Script:** `install_windows.bat` installs dependencies and creates startup shortcut
- **Unified Build Script:** `build.sh` builds Android APK + all desktop binaries
- **GitHub Actions CI/CD:** Automated builds for Android (APK) and Desktop (Linux/Windows/macOS)
- **PyInstaller Specs Updated:** Added `updater` to hidden imports
- **Version Flag:** `--version` argument for CI/CD version detection
- **Material 3 UI Overhaul:** Consistent theming, better icons, improved spacing
- **Connection Badge:** Live connection status indicator in main UI
- **Snackbar Notifications:** Toast feedback for commands and actions
- **Horizontal Scrollable Page Tabs:** Fixed overflow for many pages

### Changed
- **Android:** Upgraded to Kotlin 1.9.23, AGP 8.4.0, Compose BOM 2024.06.01
- **Dependencies:** Added kotlinx.serialization for type-safe JSON config
- **ConfigRepository:** Complete rewrite with JSON persistence, custom pages support
- **MainViewModel:** Added haptic feedback, import/export, page management functions
- **Server.py:** Modular command handlers, better error messages, cleaner shutdown
- **Windows Support:** Added sleep, brightness, screenshot via snippingtool
- **Linux Screenshots:** Added spectacle, grim, scrot as fallbacks
- **README:** Complete rewrite with installation instructions for all platforms
- **ARCHITECTURE.md:** Updated with new data models, network protocol, security notes
- **PROGRESS.md:** Comprehensive changelog and roadmap

### Fixed
- WebSocket path issue (removed `/ws` suffix)
- Auto-reconnect with exponential backoff
- Missing `ifaddr` dependency auto-install
- VPN/Docker IP filtering for mDNS broadcast
- Systemd service uses absolute paths and `loginctl enable-linger`

### Removed
- Hardcoded tile configuration from ConfigRepository (now dynamic)

## [1.2.0] - 2026-07-15

### Added
- PC Remote Power Control: Restart, Shutdown, Logout, Sleep, Hibernate
- Improved systemd Installation: Absolute paths, proper launcher script, `loginctl enable-linger`
- Heartbeat Monitoring: Server pings clients every 30s, cleans up dead connections
- Command Feedback: Toast/snackbar notifications in Android app
- Semantic Version Comparison: Updater now compares versions numerically (v1.2.0 > v1.1.4)
- Graceful Server Shutdown: SIGINT/SIGTERM handling with mDNS cleanup
- Windows PyInstaller Spec: Added `ifaddr` to hidden imports
- Linux PyInstaller Spec: Added `ifaddr` to hidden imports

### Fixed
- WebSocket Connection: Fixed `/ws` path mismatch preventing all connections
- Auto-Reconnect: Implemented exponential backoff reconnection logic
- Missing `ifaddr` Dependency: Added to requirements.txt and auto-install
- Top Sites Navigation: Horizontal scroll for page tabs
- Universal Browser Launching: Python `webbrowser` library
- Smart Spotify Launching: Native app check with web fallback
- Linux Screen Brightness: User-level tools before sysfs
- Linux Screenshots: Multiple tool support (spectacle, grim, gnome-screenshot, scrot, import)

## [1.1.4] - 2026-07-10

### Added
- Top Sites page with dynamic website adding
- Media page with volume, playback, brightness controls
- System page with screenshot, lock, sleep, browser
- Basic mDNS auto-discovery
- WebSocket communication with JSON commands

### Fixed
- Various Linux compatibility issues
- Initial Android UI implementation

## [1.0.0] - 2026-07-01

### Added
- Initial release
- Basic Android app with Jetpack Compose
- Python desktop server with WebSocket
- mDNS discovery via zeroconf
- Default pages: Prod, Design, Media, System
- Basic command execution (apps, media, system)