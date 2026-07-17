#!/usr/bin/env python3
"""
PhoneDeck Desktop Companion Server
Run this on your desktop to receive commands from the PhoneDeck Android app.
"""

import asyncio
import glob
import json
import logging
import os
import platform
import socket
import subprocess
import shutil
import time
import updater

try:
    import websockets
except ImportError:
    try:
        subprocess.check_call(["pip3", "install", "websockets"])
    except subprocess.CalledProcessError:
        subprocess.check_call(["pip3", "install", "websockets", "--break-system-packages"])
    import websockets

try:
    from zeroconf import ServiceInfo, Zeroconf
except ImportError:
    try:
        subprocess.check_call(["pip3", "install", "zeroconf"])
    except subprocess.CalledProcessError:
        subprocess.check_call(["pip3", "install", "zeroconf", "--break-system-packages"])
    from zeroconf import ServiceInfo, Zeroconf

logging.basicConfig(level=logging.INFO, format="[PhoneDeck] %(message)s")
log = logging.getLogger("phonedeck")

SYSTEM = platform.system()


def _check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def execute_command(command: str) -> dict:
    log.info(f"Executing: {command}")
    try:
        if SYSTEM == "Darwin":
            return _macos_command(command)
        elif SYSTEM == "Linux":
            return _linux_command(command)
        elif SYSTEM == "Windows":
            return _windows_command(command)
        return {"status": "error", "message": f"Unsupported OS: {SYSTEM}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── macOS ──────────────────────────────────────────────────────────

def _macos_command(command: str) -> dict:
    try:
        import applescript
        cmds = {
            "code": 'tell application "Visual Studio Code" to activate',
            "terminal": 'tell application "Terminal" to activate',
            "browser": 'tell application "Safari" to activate',
            "spotify": 'tell application "Spotify" to activate',
            "figma": 'tell application "Figma" to activate',
            "photoshop": 'tell application "Adobe Photoshop" to activate',
            "illustrator": 'tell application "Adobe Illustrator" to activate',
            "preview": 'tell application "Preview" to activate',
            "screenshot": 'tell application "System Events" to keystroke "3" using {command down, shift down}',
            "lock": 'tell application "System Events" to keystroke "q" using {command down, control down}',
            "sleep": 'tell application "Finder" to sleep',
            "volume_up": 'set volume output volume (output volume of (get volume settings) + 10)',
            "volume_down": 'set volume output volume (output volume of (get volume settings) - 10)',
            "mute": 'set volume output muted not (output muted of (get volume settings))',
            "play_pause": 'tell application "System Events" to key code 16',
            "next": 'tell application "System Events" to key code 17',
            "prev": 'tell application "System Events" to key code 18',
        }
        script = cmds.get(command)
        if script:
            applescript.AppleScript(script).run()
            return {"status": "ok", "command": command}
        subprocess.run(["open", "-a", command], capture_output=True)
        return {"status": "ok", "command": command}
    except ImportError:
        return {"status": "error", "message": "pip3 install applescript on macOS"}


# ─── Linux (Wayland + X11 compatible) ──────────────────────────────

def _linux_command(command: str) -> dict:
    app_map = {
        "code": "code",
        "terminal": _find_terminal(),
        "browser": "xdg-open",
        "spotify": "spotify",
        "figma": "figma-linux",
        "photoshop": None,
        "illustrator": None,
        "preview": "gwenview",
        "screenshot": _screenshot_cmd(),
        "lock": _lock_cmd(),
        "sleep": _sleep_cmd(),
        "volume_up": None,
        "volume_down": None,
        "mute": None,
        "play_pause": None,
        "next": None,
        "prev": None,
        "brightness_up": None,
        "brightness_down": None,
    }

    # Media keys via pactl
    if command == "volume_up":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])
        return {"status": "ok", "command": command}
    if command == "volume_down":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])
        return {"status": "ok", "command": command}
    if command == "mute":
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        return {"status": "ok", "command": command}

    # Media playback via playerctl (if available) or send key via wtype/wlrctl
    if command in ("play_pause", "next", "prev"):
        return _linux_media_playback(command)

    # Brightness via sysfs
    if command in ("brightness_up", "brightness_down"):
        return _linux_brightness(command)

    # Screenshot
    if command == "screenshot":
        return _linux_screenshot()

    # Lock / Sleep
    if command == "lock":
        subprocess.run(["loginctl", "lock-session"])
        return {"status": "ok", "command": command}
    if command == "sleep":
        subprocess.run(["systemctl", "suspend"])
        return {"status": "ok", "command": command}

    # Launch app
    app = app_map.get(command, command)
    if app is None:
        return {"status": "error", "message": f"No mapping for: {command}"}
    subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"status": "ok", "command": command}


def _find_terminal() -> str:
    for term in ["gnome-terminal", "konsole", "xfce4-terminal", "kitty", "alacritty", "foot", "xterm"]:
        if _check_tool(term):
            return term
    return "x-terminal-emulator"


def _screenshot_cmd() -> str:
    if _check_tool("gnome-screenshot"):
        return "gnome-screenshot"
    if _check_tool("grim"):
        return "grim"
    if _check_tool("import"):
        return "import"
    return "gnome-screenshot"


def _lock_cmd() -> str:
    if _check_tool("loginctl"):
        return "loginctl"
    return "gnome-screensaver-command"


def _sleep_cmd() -> str:
    return "systemctl"


def _linux_media_playback(command: str) -> dict:
    key_map = {
        "play_pause": "XF86AudioPlay",
        "next": "XF86AudioNext",
        "prev": "XF86AudioPrev",
    }
    key = key_map.get(command)

    if _check_tool("playerctl"):
        action = {"play_pause": "play-pause", "next": "next", "prev": "previous"}[command]
        subprocess.run(["playerctl", action], capture_output=True)
        return {"status": "ok", "command": command}

    if _check_tool("ydotool"):
        subprocess.run(["ydotool", "key", key], capture_output=True)
        return {"status": "ok", "command": command}

    if _check_tool("wtype"):
        subprocess.run(["wtype", "-k", key], capture_output=True)
        return {"status": "ok", "command": command}

    if _check_tool("xdotool"):
        subprocess.run(["xdotool", "key", key], capture_output=True)
        return {"status": "ok", "command": command}

    return {"status": "error", "message": "No media key tool found (install playerctl or wtype)"}


def _linux_brightness(command: str) -> dict:
    backlight_dirs = glob.glob("/sys/class/backlight/*")
    if not backlight_dirs:
        return {"status": "error", "message": "No backlight interface found"}
    backlight = backlight_dirs[0]
    try:
        with open(os.path.join(backlight, "max_brightness")) as f:
            max_val = int(f.read().strip())
        with open(os.path.join(backlight, "brightness")) as f:
            current = int(f.read().strip())
    except (IOError, ValueError):
        return {"status": "error", "message": "Cannot read backlight values"}

    step = max(1, max_val // 20)
    new_val = current + step if "up" in command else current - step
    new_val = max(0, min(max_val, new_val))

    # Try direct write first, fall back to pkexec
    try:
        with open(os.path.join(backlight, "brightness"), "w") as f:
            f.write(str(new_val))
        return {"status": "ok", "command": command}
    except IOError:
        pass

    try:
        subprocess.run(
            ["pkexec", "tee", os.path.join(backlight, "brightness")],
            input=f"{new_val}\n", capture_output=True, text=True, timeout=5
        )
        return {"status": "ok", "command": command}
    except Exception:
        return {"status": "error", "message": "Brightness needs root: add udev rule or use pkexec"}


def _linux_screenshot() -> dict:
    if _check_tool("grim"):
        path = os.path.expanduser("~/Pictures/Screenshots")
        os.makedirs(path, exist_ok=True)
        path = os.path.expanduser("~/Pictures/Screenshots")
        os.makedirs(path, exist_ok=True)
        filename = f"screenshot-{int(time.time())}.png"
        subprocess.Popen(["grim", os.path.join(path, filename)])
        return {"status": "ok"}

    if _check_tool("gnome-screenshot"):
        subprocess.Popen(["gnome-screenshot"])
        return {"status": "ok"}

    if _check_tool("import"):
        path = os.path.expanduser("~/Pictures/Screenshots")
        os.makedirs(path, exist_ok=True)
        filename = f"screenshot-{int(time.time())}.png"
        subprocess.Popen(["import", os.path.join(path, filename)])
        return {"status": "ok"}

    return {"status": "error", "message": "No screenshot tool (install grim or gnome-screenshot)"}


# ─── Windows ────────────────────────────────────────────────────────

def _windows_command(command: str) -> dict:
    app_map = {
        "code": "code",
        "terminal": "cmd",
        "browser": "start",
        "screenshot": "snippingtool",
        "lock": "rundll32.exe user32.dll,LockWorkStation",
    }

    if command in ("volume_up", "volume_down", "mute", "play_pause", "next", "prev"):
        try:
            import win32api, win32con
            vk = {"volume_up": 0xAF, "volume_down": 0xAE, "mute": 0xAD,
                  "play_pause": 0xB3, "next": 0xB0, "prev": 0xB1}[command]
            win32api.keybd_event(vk, 0, 0, 0)
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except ImportError:
            return {"status": "error", "message": "pip3 install pywin32 on Windows"}
        return {"status": "ok", "command": command}

    app = app_map.get(command, command)
    if command == "browser":
        subprocess.Popen(["start", ""], shell=True)
    else:
        subprocess.Popen(["start", app], shell=True)
    return {"status": "ok", "command": command}


# ─── WebSocket Server ──────────────────────────────────────────────

async def handler(websocket):
    addr = websocket.remote_address
    log.info(f"Client connected: {addr}")
    try:
        async for message in websocket:
            log.info(f"Received: {message}")
            try:
                payload = json.loads(message)
                command = payload.get("command", message)
            except (json.JSONDecodeError, TypeError):
                command = message.strip()
            result = execute_command(command)
            await websocket.send(json.dumps(result))
    except websockets.exceptions.ConnectionClosed:
        pass
    log.info(f"Client disconnected: {addr}")


async def main():
    # Check for updates in the background
    asyncio.create_task(asyncio.to_thread(updater.check_for_updates))

    host = "0.0.0.0"
    port = 9090

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    print("\033[36m")
    print("   ____  __                     ____            __  ")
    print("  / __ \\/ /_  ____  ____  ___  / __ \\___  _____/ /__")
    print(" / /_/ / __ \\/ __ \\/ __ \\/ _ \\/ / / / _ \\/ ___/ //_/")
    print("/ ____/ / / / /_/ / / / /  __/ /_/ /  __/ /__/ ,<   ")
    print("/_/   /_/ /_/\\____/_/ /_/\\___/_____/\\___/\\___/_/|_| \033[0m")
    print()
    print("  \033[1;35mBuilt with ❤️ by @iamhero337\033[0m")
    print("  ╔══════════════════════════════════════╗")
    print("  ║      \033[1;36mPhoneDeck Desktop Server\033[0m        ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  \033[33mConnect from PhoneDeck app to:\033[0m      ║")
    print(f"  ║  ws://{local_ip:<21}{port} ║")
    print("  ║                                      ║")
    print("  ║  \033[32mThe app will now auto-discover\033[0m      ║")
    print("  ║  \033[32mthis server using mDNS.\033[0m             ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    # Register mDNS service
    hostname = socket.gethostname()
    info = ServiceInfo(
        "_phonedeck._tcp.local.",
        f"PhoneDeck Desktop ({hostname})._phonedeck._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties={},
        server=f"{hostname}.local."
    )
    
    zc = Zeroconf()
    zc.register_service(info)

    try:
        async with websockets.serve(handler, host, port):
            log.info(f"Listening on {host}:{port}")
            await asyncio.Future()
    finally:
        zc.unregister_service(info)
        zc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")

