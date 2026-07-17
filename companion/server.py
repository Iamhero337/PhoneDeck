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
import signal
import socket
import subprocess
import shutil
import sys
import time
import uuid

import updater

try:
    import websockets
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "--break-system-packages"])
    import websockets

try:
    from zeroconf import ServiceInfo, Zeroconf
    from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "zeroconf"])
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "zeroconf", "--break-system-packages"])
    from zeroconf import ServiceInfo, Zeroconf
    from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

try:
    import ifaddr
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ifaddr"])
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ifaddr", "--break-system-packages"])
    import ifaddr

logging.basicConfig(level=logging.INFO, format="[PhoneDeck] %(message)s")
log = logging.getLogger("phonedeck")

SYSTEM = platform.system()
CONNECTED_CLIENTS = set()


def _check_tool(name: str) -> bool:
    return shutil.which(name) is not None


async def broadcast(message: str):
    if CONNECTED_CLIENTS:
        await asyncio.gather(
            *(client.send(message) for client in CONNECTED_CLIENTS.copy()),
            return_exceptions=True
        )


def execute_command(command: str) -> dict:
    log.info(f"Executing: {command}")

    if command.startswith("open_url:"):
        url = command.split("open_url:", 1)[1].strip()
        import webbrowser
        webbrowser.open(url)
        return {"status": "ok", "command": command}

    if command in ("restart", "reboot"):
        if SYSTEM == "Linux":
            subprocess.Popen(["systemctl", "reboot"])
        elif SYSTEM == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell app "System Events" to restart'])
        elif SYSTEM == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "0"])
        return {"status": "ok", "command": command}

    if command == "shutdown":
        if SYSTEM == "Linux":
            subprocess.Popen(["systemctl", "poweroff"])
        elif SYSTEM == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell app "System Events" to shut down'])
        elif SYSTEM == "Windows":
            subprocess.Popen(["shutdown", "/s", "/t", "0"])
        return {"status": "ok", "command": command}

    if command == "logout":
        if SYSTEM == "Linux":
            subprocess.Popen(["loginctl", "terminate-user", os.environ.get("USER", "")])
        elif SYSTEM == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell app "System Events" to log out'])
        elif SYSTEM == "Windows":
            subprocess.Popen(["shutdown", "/l"])
        return {"status": "ok", "command": command}

    if command == "hibernate":
        if SYSTEM == "Linux":
            subprocess.Popen(["systemctl", "hibernate"])
        elif SYSTEM == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell app "System Events" to sleep'])
        elif SYSTEM == "Windows":
            subprocess.Popen(["shutdown", "/h"])
        return {"status": "ok", "command": command}

    if command == "browser":
        import webbrowser
        webbrowser.open("https://google.com")
        return {"status": "ok", "command": command}

    if command == "spotify":
        if SYSTEM == "Darwin" and os.path.exists("/Applications/Spotify.app"):
            subprocess.run(["open", "-a", "Spotify"])
        elif SYSTEM == "Linux" and _check_tool("spotify"):
            subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif SYSTEM == "Windows" and _check_tool("spotify"):
            subprocess.Popen(["start", "spotify"], shell=True)
        else:
            import webbrowser
            webbrowser.open("https://open.spotify.com")
        return {"status": "ok", "command": command}

    if command == "get_system_info":
        info = {
            "hostname": socket.gethostname(),
            "platform": SYSTEM,
            "uptime": _get_uptime(),
        }
        return {"status": "ok", "command": command, "data": info}

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


def _get_uptime() -> str:
    try:
        if SYSTEM == "Linux":
            with open("/proc/uptime") as f:
                uptime_sec = float(f.read().split()[0])
            hours = int(uptime_sec // 3600)
            minutes = int((uptime_sec % 3600) // 60)
            return f"{hours}h {minutes}m"
    except Exception:
        pass
    return ""


def _macos_command(command: str) -> dict:
    try:
        import applescript
        cmds = {
            "code": 'tell application "Visual Studio Code" to activate',
            "terminal": 'tell application "Terminal" to activate',
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


def _linux_command(command: str) -> dict:
    app_map = {
        "code": "code",
        "terminal": _find_terminal(),
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

    if command == "volume_up":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])
        return {"status": "ok", "command": command}
    if command == "volume_down":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])
        return {"status": "ok", "command": command}
    if command == "mute":
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        return {"status": "ok", "command": command}

    if command in ("play_pause", "next", "prev"):
        return _linux_media_playback(command)

    if command in ("brightness_up", "brightness_down"):
        return _linux_brightness(command)

    if command == "screenshot":
        return _linux_screenshot()

    if command == "lock":
        subprocess.run(["loginctl", "lock-session"])
        return {"status": "ok", "command": command}
    if command == "sleep":
        subprocess.run(["systemctl", "suspend"])
        return {"status": "ok", "command": command}

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
    if _check_tool("brightnessctl"):
        arg = "5%+" if "up" in command else "5%-"
        subprocess.run(["brightnessctl", "s", arg])
        return {"status": "ok", "command": command}

    if _check_tool("xbacklight"):
        arg = "+5" if "up" in command else "-5"
        subprocess.run(["xbacklight", arg])
        return {"status": "ok", "command": command}

    backlight_dirs = glob.glob("/sys/class/backlight/*")
    if not backlight_dirs:
        return {"status": "error", "message": "No backlight interface found. Install brightnessctl."}
    backlight = backlight_dirs[0]
    try:
        with open(os.path.join(backlight, "max_brightness")) as f:
            max_val = int(f.read().strip())
        with open(os.path.join(backlight, "brightness")) as f:
            current = int(f.read().strip())
        step = max(1, max_val // 20)
        new_val = current + step if "up" in command else current - step
        new_val = max(0, min(max_val, new_val))
        with open(os.path.join(backlight, "brightness"), "w") as f:
            f.write(str(new_val))
        return {"status": "ok", "command": command}
    except Exception:
        return {"status": "error", "message": "Brightness needs root: add udev rule or install brightnessctl"}


def _linux_screenshot() -> dict:
    path = os.path.expanduser("~/Pictures/Screenshots")
    os.makedirs(path, exist_ok=True)
    filename = os.path.join(path, f"screenshot-{int(time.time())}.png")

    if _check_tool("spectacle"):
        subprocess.Popen(["spectacle", "-b", "-n", "-o", filename])
        return {"status": "ok"}
    if _check_tool("gnome-screenshot"):
        subprocess.Popen(["gnome-screenshot", "-f", filename])
        return {"status": "ok"}
    if _check_tool("grim"):
        subprocess.Popen(["grim", filename])
        return {"status": "ok"}
    if _check_tool("scrot"):
        subprocess.Popen(["scrot", filename])
        return {"status": "ok"}
    if _check_tool("import"):
        subprocess.Popen(["import", "-window", "root", filename])
        return {"status": "ok"}

    return {"status": "error", "message": "No screenshot tool (install spectacle, grim, scrot, or gnome-screenshot)"}


def _windows_command(command: str) -> dict:
    app_map = {
        "code": "code",
        "terminal": "cmd",
        "screenshot": "snippingtool",
        "lock": "rundll32.exe user32.dll,LockWorkStation",
    }

    if command in ("volume_up", "volume_down", "mute", "play_pause", "next", "prev"):
        try:
            import win32api
            import win32con
            vk = {"volume_up": 0xAF, "volume_down": 0xAE, "mute": 0xAD,
                  "play_pause": 0xB3, "next": 0xB0, "prev": 0xB1}[command]
            win32api.keybd_event(vk, 0, 0, 0)
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except ImportError:
            return {"status": "error", "message": "pip3 install pywin32 on Windows"}
        return {"status": "ok", "command": command}

    if command == "lock":
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return {"status": "ok", "command": command}

    app = app_map.get(command, command)
    subprocess.Popen(["start", app], shell=True)
    return {"status": "ok", "command": command}


async def handler(websocket):
    addr = websocket.remote_address
    log.info(f"Client connected: {addr}")
    CONNECTED_CLIENTS.add(websocket)
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
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        log.info(f"Client disconnected: {addr}")


def get_best_local_ip():
    try:
        best_ip = None
        for adapter in ifaddr.get_adapters():
            name = adapter.name.lower()
            if name == 'lo' or name.startswith('docker') or name.startswith('br-') or name.startswith('veth') or 'warp' in name or name.startswith('tun') or name.startswith('wg'):
                continue
            for ip in adapter.ips:
                if isinstance(ip.ip, str) and not ip.ip.startswith("127.") and not ip.ip.startswith("169.254."):
                    return ip.ip
    except ImportError:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


async def heartbeat():
    while True:
        await asyncio.sleep(30)
        if CONNECTED_CLIENTS:
            dead = set()
            for ws in CONNECTED_CLIENTS:
                try:
                    pong = await asyncio.wait_for(ws.ping(), timeout=5)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                CONNECTED_CLIENTS.discard(ws)


async def main():
    if SYSTEM == "Linux":
        asyncio.create_task(asyncio.to_thread(updater.check_for_updates))

    host = "0.0.0.0"
    port = 9090

    local_ip = get_best_local_ip()

    print("\033[36m")
    print("   ____  __                     ____            __  ")
    print("  / __ \\/ /_  ____  ____  ___  / __ \\___  _____/ /__")
    print(" / /_/ / __ \\/ __ \\/ __ \\/ _ \\/ / / / _ \\/ ___/ //_/")
    print("/ ____/ / / / /_/ / / / /  __/ /_/ /  __/ /__/ ,<   ")
    print("/_/   /_/ /_/\\____/_/ /_/\\___/_____/\\___/\\___/_/|_| \033[0m")
    print()
    print("  \033[1;35mBuilt with \u2764 by @iamhero337\033[0m")
    print("  \033[1;33mVersion: \033[0m\033[1;97m{}\033[0m".format(updater.CURRENT_VERSION))
    print("  \033[1;33mOS: \033[0m\033[1;97m{}\033[0m".format(SYSTEM))
    print("  \033[1;33mHostname: \033[0m\033[1;97m{}\033[0m".format(socket.gethostname()))
    print("  \033[1;33mAuto-connect IP: \033[0m\033[1;97m{}\033[0m".format(local_ip))
    print("  ╔══════════════════════════════════════╗")
    print("  ║      \033[1;36mPhoneDeck Desktop Server\033[0m        ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  \033[33mConnect from PhoneDeck app to:\033[0m      ║")
    print(f"  ║  ws://{local_ip}:{port:<26} ║")
    print("  ║                                      ║")
    print("  ║  \033[32mThe app will now auto-discover\033[0m      ║")
    print("  ║  \033[32mthis server using mDNS.\033[0m             ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    hostname = socket.gethostname()
    unique_id = uuid.uuid4().hex[:6]
    info = AsyncServiceInfo(
        "_phonedeck._tcp.local.",
        f"PhoneDeck Desktop ({hostname}-{unique_id})._phonedeck._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties={},
        server=f"{hostname}.local."
    )

    zc = AsyncZeroconf()
    await zc.async_register_service(info)

    asyncio.create_task(heartbeat())

    stop = asyncio.Future()

    def shutdown_handler(sig, frame):
        if not stop.done():
            stop.set_result(None)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        async with websockets.serve(handler, host, port):
            log.info(f"Listening on {host}:{port}")
            await stop
    finally:
        await zc.async_unregister_service(info)
        await zc.async_close()
        log.info("Server stopped")


def auto_install_linux_service():
    if SYSTEM != "Linux":
        return

    current_exe = os.path.abspath(sys.argv[0])

    target_bin = os.path.expanduser("~/.local/bin/phonedeck-server")

    if current_exe == target_bin:
        return

    if not getattr(sys, 'frozen', False):
        return

    print("╔══════════════════════════════════════╗")
    print("║   PhoneDeck Auto-Install (Linux)     ║")
    print("╚══════════════════════════════════════╝")
    if not os.path.exists(target_bin):
        print("Installing background service...")

    os.makedirs(os.path.dirname(target_bin), exist_ok=True)
    try:
        shutil.copyfile(current_exe, target_bin)
        os.chmod(target_bin, 0o755)
    except OSError as e:
        import errno
        if e.errno == errno.ETXTBSY:
            print("\n✅ Background service is already installed and running perfectly!")
            print("You can just open your PhoneDeck Android app and connect.\n")
            return
        raise

    service_content = f"""[Unit]
Description=PhoneDeck Companion Server
After=network.target
Wants=network-online.target

[Service]
ExecStart={target_bin}
Restart=always
RestartSec=3
StartLimitBurst=5
StartLimitIntervalSec=30

[Install]
WantedBy=default.target
"""
    systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_dir, exist_ok=True)

    service_path = os.path.join(systemd_dir, "phonedeck.service")
    with open(service_path, "w") as f:
        f.write(service_content)

    try:
        subprocess.run(["loginctl", "enable-linger", os.environ.get("USER", "")],
                       capture_output=True)
        subprocess.check_call(["systemctl", "--user", "daemon-reload"])
        subprocess.check_call(["systemctl", "--user", "enable", "--now", "phonedeck.service"])
        print("\n✅ Successfully installed and started in the background!")
        print("✅ Auto-start on login enabled.")
        print("You can safely close this terminal. It will always start automatically.")
        print("Just open your PhoneDeck Android app and enjoy.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start systemd service: {e}")


if __name__ == "__main__":
    if "--install" in sys.argv:
        auto_install_linux_service()
        sys.exit(0)

    auto_install_linux_service()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except OSError as e:
        import errno
        if e.errno in (errno.EADDRINUSE, 10048):
            print("\n✅ PhoneDeck Server is already actively running in the background on port 9090!")
            print("Open the PhoneDeck app on your phone, and it will connect automatically.\n")
        else:
            raise
