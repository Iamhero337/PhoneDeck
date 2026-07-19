# PhoneDeck Architecture

PhoneDeck is built on a client-server architecture designed to be lightweight, incredibly fast, and platform-agnostic. The system consists of two primary components: an Android App (the client) and a Python Background Service (the server).

## 1. High-Level Overview

```mermaid
graph TD
    A[Android App (Jetpack Compose)] <-->|WebSockets (JSON)| B[Python Server]
    B -->|macOS Handlers| C[macOS (AppleScript / open)]
    B -->|Linux Handlers| D[Linux (subprocess / xdg / pactl / brightnessctl)]
    B -->|Windows Handlers| E[Windows (pywin32 / wmi / rundll32)]
```

## 2. Components

### The Android Client
The Android client is built natively using **Kotlin** and **Jetpack Compose** for a modern, responsive UI.

- **Auto-Discovery:** Uses `NsdManager` (Network Service Discovery) to automatically discover the desktop server on the local Wi-Fi network without requiring manual IP entry.
- **Auto-Reconnect:** Automatically reconnects with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max) if the connection drops, ensuring reliable operation.
- **Dynamic Configuration:** Pages and tiles are configured via a centralized `ConfigRepository`. The layout is dynamically built into a grid, grouped into horizontally scrollable page tabs.
- **Real-Time Communication:** Commands are sent over a persistent WebSocket connection ensuring near zero-latency execution.
- **Haptic Feedback:** Optional vibration on tile press for tactile confirmation.
- **State Management:** Uses `ViewModel` with `StateFlow` for reactive UI updates.
- **Persistence:** `SharedPreferences` with JSON serialization (via kotlinx.serialization) for pages, tiles, and settings.
- **Import/Export:** Full configuration backup/restore as JSON.

### The Desktop Server
The desktop server is a lightweight **Python** background script (`server.py`). It relies on:

- `websockets` for managing persistent connections from the Android app, including heartbeat monitoring to detect dead clients.
- `zeroconf` to broadcast its presence over mDNS, allowing the Android app to discover it automatically.
- `ifaddr` for smart IP selection that filters out VPN, Docker, and virtual adapters.
- `subprocess` to securely execute OS-level commands and scripts.
- Platform-specific libraries: `applescript` (macOS), `pactl`/`playerctl`/`brightnessctl` (Linux), `pywin32`/`wmi` (Windows).

## 3. Command Execution Flow

When you tap a tile in the Android app, a specific command string (e.g., `"browser"`, `"volume_up"`, or `"open_url:youtube.com"`) is transmitted to the server.

1. **Incoming Request:** The server receives the command via the active WebSocket connection.
2. **Global Commands:** Commands like opening URLs, restart/shutdown/logout, or launching web browsers are handled at the top level by Python's standard libraries to ensure cross-platform consistency.
3. **OS-Specific Routing:** If the command is OS-specific (like adjusting volume or launching an IDE), it routes to a dedicated handler:
   - `_macos_command()`: Uses AppleScript (`osascript`) to gracefully control applications and media on Macs.
   - `_linux_command()`: Utilizes binary checks (e.g., `which`, `brightnessctl`, `playerctl`, `gnome-screenshot`) and generic Linux utilities (`subprocess`) for wide desktop environment compatibility.
   - `_windows_command()`: Interfaces with `pywin32`, `wmi`, `rundll32`, and other native Windows utilities.
4. **Execution & Response:** The command is executed, and a JSON status dictionary (`{"status": "ok", "command": "..."}`) is returned to the client to confirm successful execution.

## 4. Automatic IP Selection

To circumvent issues with virtual interfaces (like VPNs, Cloudflare WARP, or Docker bridge networks), the Python server uses the `ifaddr` package to filter out virtual adapters, ensuring the IP broadcasted via mDNS is the actual LAN IP reachable by the phone.

## 5. Heartbeat & Connection Management

The server runs a background heartbeat task every 30 seconds that pings all connected WebSocket clients. Clients that fail to respond within 5 seconds are automatically removed from the connected clients set, ensuring stale connections don't accumulate.

## 6. Systemd Integration (Linux)

On Linux, the server can install itself as a systemd user service with:
- **Auto-start on boot** (via `loginctl enable-linger`)
- **Automatic restart** on failure (Restart=always with 3s delay)
- **Startup limiting** to prevent crash loops (5 attempts in 30s)

## 7. LaunchAgent Integration (macOS)

On macOS, the server installs as a user `launchd` agent (`~/Library/LaunchAgents/com.iamhero337.phonedeck.plist`) with:
- Run at load (login)
- Keep alive (restart on crash)
- Standard out/error logging to `/tmp/`

## 8. Startup Integration (Windows)

On Windows, the installer creates a shortcut in the user's Startup folder (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`) pointing to the PyInstaller-built executable, ensuring silent background startup on login.

## 9. Data Models

### Tile
```kotlin
data class Tile(
    val id: String,           // Unique identifier
    val label: String,        // Display text
    val icon: String,         // Material Design icon name
    val command: String,      // Command to send to server
    val color: Int = 0xFF2A2A3E,    // Background color (ARGB)
    val iconColor: Int = 0xFF4A90D9 // Icon color (ARGB)
)
```

### Page
```kotlin
data class Page(
    val id: String,           // Unique identifier
    val name: String,         // Display name (tab label)
    val tiles: List<Tile>     // Grid of tiles
)
```

## 10. Network Protocol

### WebSocket Messages

**Client → Server:**
```json
{
  "command": "volume_up"
}
```
Or for open_url:
```json
{
  "command": "open_url:https://github.com"
}
```

**Server → Client:**
```json
{
  "status": "ok",
  "command": "volume_up"
}
```

Error response:
```json
{
  "status": "error",
  "command": "volume_up",
  "message": "pactl not found"
}
```

### mDNS Service
- **Service Type:** `_phonedeck._tcp.local.`
- **Port:** 9090
- **Properties:** `version` (e.g., "1.3.1")

## 11. Security Considerations

- **Local Network Only:** Designed for trusted local networks only.
- **No Authentication:** Currently no auth; relies on network isolation.
- **Command Validation:** Server validates commands against known handlers.
- **Future:** Optional TLS + token auth planned.

## 12. Build & Distribution

### Android
- Gradle with Kotlin DSL
- Compose Compiler 1.5.11
- Min SDK 26, Target SDK 34
- Release APK signed with release keystore

### Desktop (PyInstaller)
- Linux: `phonedeck-server-linux.spec` → `dist/phonedeck-server-linux`
- Windows: `phonedeck-server-windows.spec` → `dist/phonedeck-server-windows.exe`
- Hidden imports: `websockets`, `zeroconf`, `ifaddr`, `updater`

### Local Build
- **Android:** `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew assembleRelease` → `app/build/outputs/apk/release/app-release.apk`
- **Linux Server:** `cd companion && pyinstaller --clean --noconfirm phonedeck-server-linux.spec` → `companion/dist/phonedeck-server-linux`
- **Unified:** `./build.sh` does both and copies artifacts to `downloads/`

---

*Architecture version: 1.3.1*