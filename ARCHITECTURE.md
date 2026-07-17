# PhoneDeck Architecture

PhoneDeck is built on a client-server architecture designed to be lightweight, incredibly fast, and platform-agnostic. The system consists of two primary components: an Android App (the client) and a Python Background Service (the server).

## 1. High-Level Overview

```mermaid
graph TD
    A[Android App (Jetpack Compose)] <-->|WebSockets (plain text)| B[Python Server]
    B -->|macOS Handlers| C[macOS (AppleScript / open)]
    B -->|Linux Handlers| D[Linux (subprocess / xdg)]
    B -->|Windows Handlers| E[Windows (cmd / start)]
```

## 2. Components

### The Android Client
The Android client is built natively using **Kotlin** and **Jetpack Compose** for a modern, responsive UI. 
- **Auto-Discovery:** Uses `NsdManager` (Network Service Discovery) to automatically discover the desktop server on the local Wi-Fi network without requiring manual IP entry.
- **Auto-Reconnect:** Automatically reconnects with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max) if the connection drops, ensuring reliable operation.
- **Dynamic Configuration:** Pages and tiles are configured via a centralized `ConfigRepository`. The layout is dynamically built into a grid, grouped into horizontally scrollable page tabs.
- **Real-Time Communication:** Commands are sent over a persistent WebSocket connection ensuring near zero-latency execution.

### The Desktop Server
The desktop server is a lightweight **Python** background script (`server.py`). It relies on:
- `websockets` for managing persistent connections from the Android app, including heartbeat monitoring to detect dead clients.
- `zeroconf` to broadcast its presence over mDNS, allowing the Android app to discover it automatically.
- `ifaddr` for smart IP selection that filters out VPN, Docker, and virtual adapters.
- `subprocess` to securely execute OS-level commands and scripts.

## 3. Command Execution Flow

When you tap a tile in the Android app, a specific command string (e.g., `"browser"`, `"volume_up"`, or `"open_url:youtube.com"`) is transmitted to the server.

1. **Incoming Request:** The server receives the command via the active WebSocket connection.
2. **Global Commands:** Commands like opening URLs, restart/shutdown/logout, or launching web browsers are handled at the top level by Python's standard libraries to ensure cross-platform consistency.
3. **OS-Specific Routing:** If the command is OS-specific (like adjusting volume or launching an IDE), it routes to a dedicated handler:
   - `_macos_command()`: Uses AppleScript (`osascript`) to gracefully control applications and media on Macs.
   - `_linux_command()`: Utilizes binary checks (e.g., `which`, `brightnessctl`, `playerctl`, `gnome-screenshot`) and generic Linux utilities (`subprocess`) for wide desktop environment compatibility.
   - `_windows_command()`: Interfaces with `start`, `rundll32`, `pywin32`, and other native Windows utilities.
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
