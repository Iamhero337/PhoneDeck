<div align="center">
  <img src="assets/logo.jpg" alt="PhoneDeck Logo" width="150" height="150" style="border-radius: 24px;" />
  <h1>PhoneDeck</h1>
  <p><strong>Turn your Android phone into a wireless productivity controller for your computer.</strong></p>
  <p>Like a Stream Deck, but completely free and open-source.</p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Platform: Android | Windows | macOS | Linux](https://img.shields.io/badge/Platforms-Android%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-blue)](#)
</div>

---

## ✨ Features

- 🚀 **Zero Configuration:** Auto-discovery via mDNS. No typing IPs manually.
- 💻 **Cross-Platform:** Works out-of-the-box on Linux, Windows, and macOS.
- 🛠️ **Fully Customizable:** Easily add your own custom commands or apps.
- 🌐 **Dynamic Top Sites:** Dynamically add your favorite websites directly in the Android app to launch them on your desktop!
- ⚡ **Lightning Fast:** Powered by local WebSockets for instantaneous response.
- 🔋 **Lightweight:** Negligible impact on battery life and system resources.

## 🛠️ One-Time Setup

Nobody likes running servers in terminal windows. PhoneDeck is designed for a true "set and forget" experience.

### 1. The Phone App (Android)
Download the latest `PhoneDeck.apk` from the [Releases](https://github.com/iamhero337/PhoneDeck/releases) tab and install it on your Android phone.

### 2. The Desktop Server (Windows / Linux / macOS)

**For Windows (Executable):**
1. Download `phonedeck-server-windows.exe` from the [Releases](https://github.com/iamhero337/PhoneDeck/releases) tab.
2. Press `Win + R`, type `shell:startup`, and hit Enter.
3. Place the `.exe` (or a shortcut to it) in the Startup folder. It will now run silently in the background every time you boot!

**For Linux:**
You have two options on Linux:
1. **Standalone Binary:** Download `phonedeck-server-linux` from the [Releases](https://github.com/iamhero337/PhoneDeck/releases) tab. Make it executable (`chmod +x phonedeck-server-linux`) and run it. You can add this to your desktop environment's autostart list.
2. **systemd Background Service (Recommended):**
   - Clone this repository or download the source.
   - Run the automated install script:
     ```bash
     chmod +x install_linux.sh
     ./install_linux.sh
     ```
   This installs the companion server as a systemd user service. It starts on boot, restarts on failure, and stays out of your way!

**For macOS (Background execution):**
1. Ensure Python 3 is installed.
2. Download the source and run `python3 companion/server.py`. (You can set this up as a Login Item or `launchd` service).

## 🚀 How to Use

1. Ensure your phone and computer are on the **same Wi-Fi network**.
2. Open the PhoneDeck app on your phone.
3. The app will **automatically find** your laptop using Zeroconf/mDNS.
4. Start tapping tiles to control your PC!

## 📦 What's Included? (Default Layout)

| Page | Included Tiles |
|------|-------|
| **Prod** | VS Code, Terminal, Browser, Spotify |
| **Design** | Figma, Photoshop, Illustrator, Preview |
| **Media** | Volume Up/Down, Mute, Play/Pause, Next/Prev |
| **System** | Brightness Up/Down, Screenshot, Lock, Sleep |
| **Top Sites** | Dynamically add your favorite websites in the app! |

### 🌐 Adding Top Sites
You can now dynamically add your favorite websites directly from the app! 
Navigate to the **Top Sites** page in the Android app and tap the `+` icon in the top right corner. Enter the site name and URL (e.g. `youtube.com`). It will automatically save to your phone and launch seamlessly on your desktop's default browser whenever you tap it!

### Adding Custom Commands
Want to add a macro, a script, or a new app? 
Edit `ConfigRepository.kt` in the Android app source to add new tiles:
```kotlin
Tile("my1", "My App", "star", "my-app-command")
```
Then update the `app_map` inside `companion/server.py` to route `"my-app-command"` to the desired system action!

## 🏗️ Architecture & Progress
Curious about how it works under the hood? Read our [Architecture Document](ARCHITECTURE.md).
Want to see what we've recently fixed and added? Check out our [Progress & Changelog](PROGRESS.md).

## 👨‍💻 Credits
Built with ❤️ by [@iamhero337](https://github.com/iamhero337).

## 📄 License
MIT License. Free to use, modify, and distribute.
