# PhoneDeck Architecture

PhoneDeck is built with a distributed architecture focusing on low latency, seamless discovery, and a strict separation of concerns.

## High-Level Overview

```mermaid
graph LR
    subgraph Android Device
        A[PhoneDeck App]
        B[Service Discovery (mDNS)]
        C[WebSocket Client]
    end

    subgraph Desktop / Laptop
        D[Companion Server]
        E[mDNS Broadcaster]
        F[OS Specific Handlers]
    end

    B -.->|Resolves Server IP| E
    C <==>|Bi-directional Commands| D
    D -->|Executes| F
```

## 1. The Mobile Client (Android / Kotlin)

The mobile client acts strictly as the **presentation and networking layer**.

- **UI Framework:** Built using Jetpack Compose for a highly responsive, modern UI.
- **Service Discovery:** Uses Android's `NsdManager` (Network Service Discovery). The app listens for the `_phonedeck._tcp` service over the local network, drastically reducing user friction by eliminating the need to manually type IP addresses.
- **Networking:** Built on top of OkHttp's WebSocket implementation. The connection is maintained asynchronously using Kotlin Coroutines and Flows.
- **State Management:** Uses MVVM pattern. The ViewModel bridges the gap between the UI states (Connection state, current active page) and the Networking layer.

## 2. The Companion Server (Python 3)

The companion server is a lightweight Python script that acts as the **execution layer**.

- **Zero-Config Discovery:** Implements `zeroconf` to broadcast the `_phonedeck._tcp` mDNS service on the local network. 
- **WebSocket Server:** Uses the `websockets` package to handle asynchronous, non-blocking incoming connections.
- **OS Abstraction Layer:** The execution pipeline is divided by OS (`SYSTEM = platform.system()`).
  - **Linux:** Interacts heavily with DBUS, Wayland/X11 tools (`playerctl`, `ydotool`, `pactl`) to manage media and system states.
  - **Windows:** Relies on the Windows API (`pywin32`) for precise media key emulation and `subprocess` for application launching.
  - **macOS:** Primarily relies on AppleScript (`osascript`) for native application control and system automation.

## 3. Automation and Deployment

- **Windows/macOS:** A GitHub Actions workflow automatically compiles the `server.py` script into standalone native executables using `PyInstaller`. This eliminates the need for end-users to install Python or understand dependencies.
- **Linux:** Utilizes a standard `systemd` user service setup script, embracing standard Linux daemon paradigms to ensure the server gracefully restarts and persists across reboots.

## Security Considerations

PhoneDeck is designed to be run **strictly on trusted Local Area Networks (LAN)**. 
- The WebSocket server binds to `0.0.0.0` but does not implement TLS or authentication, as it's designed to be firewalled behind the user's local router.
- No sensitive data is transmitted; only abstract command strings (e.g., `play_pause`, `open_browser`).
