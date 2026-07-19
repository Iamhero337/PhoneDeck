<div align="center">
  <img src="assets/logo.jpg" alt="PhoneDeck Logo" width="150" height="150" style="border-radius: 24px;" />
  <h1>PhoneDeck</h1>
  <p><strong>Turn your Android phone into a wireless productivity controller for your computer.</strong></p>
  <p>Like a Stream Deck, but completely free, open-source, and customizable.</p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Platform: Android | Windows | macOS | Linux](https://img.shields.io/badge/Platforms-Android%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-blue)](https://github.com/iamhero337/PhoneDeck/releases)
  [![Version](https://img.shields.io/badge/Version-v1.3.0-green)](https://github.com/iamhero337/PhoneDeck/releases)
  [![Build Status](https://github.com/iamhero337/PhoneDeck/actions/workflows/android.yml/badge.svg)](https://github.com/iamhero337/PhoneDeck/actions)
</div>

---

## ✨ Features

- 🚀 **Zero Configuration:** Auto-discovery via mDNS. No manual IP entry needed.
- 💻 **Cross-Platform:** Works out-of-the-box on Linux, Windows, and macOS.
- 🛠️ **Fully Customizable:** Add, remove, reorder pages and tiles without recompiling.
- 🌐 **Dynamic Top Sites:** Add your favorite websites in the app to launch them on your desktop.
- 🔄 **Auto-Reconnect:** Automatically reconnects with exponential backoff if connection drops.
- ⚡ **Lightning Fast:** Local WebSockets for near-instant response.
- 🔋 **Lightweight:** Negligible impact on battery and system resources.
- 🖥️ **PC Power Control:** Restart, shutdown, logout, sleep, and hibernate remotely.
- 📱 **Haptic Feedback:** Tactile response when pressing tiles.
- 💾 **Backup & Restore:** Export/import your entire configuration as JSON.
- 🌙 **Dark Mode:** Beautiful dark theme optimized for low-light use.

---

## 🛠️ One-Time Setup

Nobody likes running servers in terminal windows. PhoneDeck is designed for a true "set and forget" experience.

### 1. The Phone App (Android)

**Option A - Pre-built APK (Recommended):**
Download the latest `PhoneDeck-v1.3.0.apk` from the [Releases](https://github.com/iamhero337/PhoneDeck/releases) tab and install it on your Android phone.

**Option B - Build from Source:**
```bash
cd Androiddeck
./gradlew assembleRelease
# APK will be at app/build/outputs/apk/release/app-release.apk
```

### 2. The Desktop Server (Windows / Linux / macOS)

#### For Windows (Automated Installer):
1. Download `install_windows.bat` from the [Releases](https://github.com/iamhero337/PhoneDeck/releases) tab.
2. Run it as **Administrator** (required for startup folder access).
3. It will install Python dependencies, build the server, and add it to Windows Startup.

#### For Linux (systemd Service - Recommended):
```bash
git clone https://github.com/iamhero337/PhoneDeck.git
cd PhoneDeck
chmod +x install_linux.sh
./install_linux.sh
```
This installs the companion server as a systemd **user service**. It starts on boot, restarts on failure, and stays out of your way!

**Manual Binary Option:**
Download `phonedeck-server-linux-v1.3.0` from [Releases](https://github.com/iamhero337/PhoneDeck/releases), make it executable (`chmod +x`), and run it.

#### For macOS (LaunchAgent):
```bash
git clone https://github.com/iamhero337/PhoneDeck.git
cd PhoneDeck
chmod +x install_macos.sh
./install_macos.sh
```
This creates a `launchd` user agent that starts at login.

**Manual Python Option:**
Ensure Python 3.10+ is installed, then:
```bash
pip3 install websockets zeroconf ifaddr
python3 companion/server.py
```

---

## 🚀 How to Use

1. Ensure your phone and computer are on the **same Wi-Fi network**.
2. Open the PhoneDeck app on your phone.
3. The app will **automatically find** your laptop using Zeroconf/mDNS.
4. Start tapping tiles to control your PC!

---

## 📦 Default Layout (All Customizable)

| Page | Included Tiles |
|------|----------------|
| **Prod** | VS Code, Terminal, Browser, Spotify |
| **Design** | Figma, Photoshop, Illustrator, Preview |
| **Media** | Volume Up/Down, Mute, Play/Pause, Next/Prev, Brightness +/- |
| **System** | Screenshot, Lock, Sleep, Browser, **Restart**, **Shutdown**, **Logout**, **Hibernate** |
| **Top Sites** | Add your own websites dynamically! |

### 🌐 Adding Top Sites
Navigate to the **Top Sites** page in the Android app and tap the `+` icon in the top right. Enter the site name and URL (e.g., `youtube.com`). It saves to your phone and launches seamlessly on your desktop's default browser.

### 🖥️ PC Power Control
PhoneDeck can remotely restart, shutdown, logout, sleep, or hibernate your computer. These commands are on the **System** page. Use responsibly!

### ⚙️ Customizing Pages & Tiles
Open **Settings** (gear icon) in the app:
- **Add Custom Page:** Create new pages with your own tiles
- **Edit Tiles:** Long-press any tile to edit label, icon, command, and colors
- **Reorder Pages:** Drag page tabs to reorder
- **Export/Import:** Backup your entire configuration as JSON

### 🎨 Tile Configuration
Each tile supports:
- **Command:** The action to send (e.g., `code`, `open_url:https://github.com`)
- **Icon:** Material Design icon name (e.g., `code`, `terminal`, `music_note`)
- **Colors:** Custom background and icon colors per tile

---

## 🏗️ Architecture

PhoneDeck uses a client-server architecture:

```mermaid
graph TD
    A[Android App (Jetpack Compose)] <--WebSockets--> B[Python Server]
    B -->|macOS Handlers| C[macOS (AppleScript / open)]
    B -->|Linux Handlers| D[Linux (subprocess / xdg / pactl / brightnessctl)]
    B -->|Windows Handlers| E[Windows (pywin32 / wmi / rundll32)]
```

### Android Client (Kotlin + Jetpack Compose)
- **Auto-Discovery:** Uses `NsdManager` for mDNS service discovery
- **Auto-Reconnect:** Exponential backoff (1s → 2s → 4s → 8s → 16s → 30s max)
- **Dynamic UI:** Pages and tiles loaded from local configuration
- **Haptic Feedback:** Optional vibration on tile press
- **Backup/Restore:** Full JSON import/export

### Desktop Server (Python)
- **WebSockets:** Persistent connections with heartbeat monitoring
- **Zeroconf:** Broadcasts presence via mDNS for auto-discovery
- **Smart IP Selection:** Uses `ifaddr` to filter out VPN/Docker/virtual adapters
- **Cross-Platform Commands:** OS-specific handlers for maximum compatibility
- **Auto-Update:** Checks GitHub releases and updates automatically (Linux/Windows)
- **Systemd/LaunchAgent:** Background service installation

---

## 🔧 Development

### Prerequisites
- **Android:** Android Studio, JDK 17, Android SDK 34
- **Desktop:** Python 3.10+, pip
- **Build:** PyInstaller (for executables)

### Building

**Android APK:**
```bash
cd Androiddeck
./gradlew assembleRelease
```

**Linux Executable:**
```bash
cd companion
pip install pyinstaller
pyinstaller --clean phonedeck-server-linux.spec
# Output: dist/phonedeck-server-linux
```

**Windows Executable:**
```bash
cd companion
pip install pyinstaller
pyinstaller --clean phonedeck-server-windows.spec
# Output: dist/phonedeck-server-windows.exe
```

### Project Structure
```
Androiddeck/
├── app/                    # Android App (Kotlin + Compose)
│   ├── src/main/java/com/phonedeck/android/
│   │   ├── data/           # Models, Repository (ConfigRepository)
│   │   ├── network/        # WebSocket client, mDNS scanner
│   │   ├── ui/             # Compose screens & components
│   │   ├── viewmodel/      # MainViewModel
│   │   └── MainActivity.kt
│   └── build.gradle.kts
├── companion/              # Python Desktop Server
│   ├── server.py           # Main server with all command handlers
│   ├── updater.py          # Auto-update logic
│   ├── requirements.txt
│   ├── *.spec              # PyInstaller specs
│   └── build scripts
├── .github/workflows/      # CI/CD (GitHub Actions)
├── install_linux.sh        # Linux systemd installer
├── install_macos.sh        # macOS launchd installer
├── install_windows.bat     # Windows startup installer
├── build.sh                # Unified build script
└── README.md
```

---

## 🔧 Extending Commands

### Adding Custom Commands (Android)
Edit `ConfigRepository.kt` or use the Settings UI to add tiles:
```kotlin
Tile("my1", "My App", "star", "my-custom-command", 0xFF2A2A3E, 0xFF4A90D9)
```

### Handling Commands (Python Server)
Add a new case in `server.py`:
```python
def execute_command(command: str) -> dict:
    if command == "my-custom-command":
        subprocess.Popen(["/path/to/my/app"])
        return {"status": "ok", "command": command}
    # ... rest of handlers
```

### Supported Commands by Default
| Command | Description |
|---------|-------------|
| `code` | Launch VS Code |
| `terminal` | Open terminal |
| `browser` | Open default browser |
| `spotify` | Launch Spotify (native or web) |
| `figma` / `photoshop` / `illustrator` / `preview` | Design apps |
| `volume_up` / `volume_down` / `mute` | System volume |
| `play_pause` / `next` / `prev` | Media playback |
| `brightness_up` / `brightness_down` | Screen brightness |
| `screenshot` | Take screenshot |
| `lock` / `sleep` | Lock/sleep computer |
| `restart` / `shutdown` / `logout` / `hibernate` | Power control |
| `open_url:<url>` | Open URL in default browser |

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution
- 🪟 Windows: More media keys, brightness control, app launchers
- 🍎 macOS: More native app support, shortcuts integration
- 🐧 Linux: Wayland support, more DE-specific tools
- 📱 Android: Widgets, Tasker integration, more tile types
- 📚 Documentation: Tutorials, translations, screenshots

---

## 📄 License

MIT License. Free to use, modify, and distribute.

---

## 👨‍💻 Credits

Built with ❤️ by [@iamhero337](https://github.com/iamhero337).

### Libraries & Tools
- **Android:** Jetpack Compose, OkHttp, Kotlin Coroutines, Kotlin Serialization
- **Desktop:** websockets, zeroconf, ifaddr, pywin32, wmi
- **Build:** Gradle, PyInstaller, GitHub Actions

---

<div align="center">
  <strong>If you find PhoneDeck useful, please ⭐ the repo!</strong>
</div>