# Progress and Changelog

This document tracks our recent fixes, improvements, and the current working state of PhoneDeck.

## What's Working (Core Features)

- **App UI & Navigation:** The Android application UI is fully complete using Jetpack Compose, featuring a gorgeous dark mode design, connection status badges, and tile grids.
- **Auto-Discovery:** mDNS (Zeroconf) server discovery works reliably. The app successfully finds the desktop server over local Wi-Fi without manual IP entry.
- **WebSocket Communication:** Near instantaneous, two-way communication between the phone and the desktop.
- **Cross-Platform Foundation:** The Python server runs effectively on Windows, macOS, and Linux, with proper daemonization/systemd background support on Linux and Windows.
- **Dynamic Top Sites:** Users can add websites dynamically in the Android app and have them immediately saved and mapped to the desktop's default browser.

## Recent Fixes (v1.1.4)

In our latest iterations, we tackled various critical bugs reported on the Linux environment:

1. **Top Sites Navigation Overflow:** 
   - *Bug:* The top tabs (Prod, Design, Media, System, Top Sites) were structured in a standard `Row`. This caused the tabs to overflow out of bounds on smaller screens.
   - *Fix:* Upgraded the `Row` to be horizontally scrollable `horizontalScroll(rememberScrollState())`, keeping all tabs cleanly accessible.

2. **Universal Browser Launching:**
   - *Bug:* Launching the default browser via the `browser` command failed because `xdg-open` on Linux requires a target URL argument, but it was being executed empty.
   - *Fix:* Removed OS-specific shell wrappers for the browser command. Now, the Python `webbrowser` library explicitly opens `https://google.com` (as a fallback URL). This guarantees the actual user's default browser (like Vivaldi, Chrome, Firefox) opens flawlessly on all platforms.

3. **Smart Spotify Launching:**
   - *Bug:* Tapping the Spotify tile didn't correctly account for whether Spotify was actually installed on the host computer, failing silently if missing.
   - *Fix:* Implemented a smart launcher. On Linux/Windows, it checks `PATH` for the native `spotify` binary. On macOS, it checks the `/Applications` folder. If native Spotify is found, it launches it; if not, it gracefully degrades and opens `https://open.spotify.com` in the default browser.

4. **Linux Screen Brightness Password Prompt:**
   - *Bug:* Adjusting screen brightness on Linux fell back to `pkexec`, which triggered a disruptive graphical password prompt every time the user tapped the tile.
   - *Fix:* Refactored Linux brightness handling to prioritize user-level tools like `brightnessctl` and `xbacklight`. If those fail, it attempts an unprivileged write directly to `/sys/class/backlight`.

5. **Linux Screenshots Improvement:**
   - *Bug:* Standard screenshots relying on `import` (ImageMagick) or `grim` were failing due to lack of standard desktop environment coverage.
   - *Fix:* Unified and expanded the screenshot toolchain to systematically test for: `spectacle` (KDE), `gnome-screenshot` (GNOME), `grim` (Wayland), `scrot` (X11), and `import`. Screenshots now save cleanly to `~/Pictures/Screenshots`.

6. **IP Resolution with Virtual Adapters:**
   - *Bug:* When connected to Cloudflare WARP or Docker virtual networks, standard IP resolution (socket connecting to 8.8.8.8) falsely returned the VPN tunnel's IP, breaking mDNS connection.
   - *Fix:* Moved IP resolution to use the `ifaddr` package. It iterates physical adapters, explicitly rejecting interfaces named `CloudflareWARP`, `docker`, `br-`, `tun`, and `wg`, ensuring the real local LAN IP is broadcasted to the Android app.

## Upcoming Improvements

- Expand Windows control sets (brightness, advanced media keys).
- Expand macOS handlers.
- Allow users to fully edit default pages and swap out application icons without recompiling the Android APK.
