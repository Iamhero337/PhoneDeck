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
import webbrowser

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

VERSION = "1.3.1"
PORT = 9090

COMMAND_MAP = {
    "code": "Visual Studio Code",
    "terminal": "Terminal",
    "browser": "Web Browser",
    "spotify": "Spotify",
    "figma": "Figma",
    "photoshop": "Photoshop",
    "illustrator": "Illustrator",
    "preview": "Preview",
    "screenshot": "Screenshot",
    "lock": "Lock Screen",
    "sleep": "Sleep",
    "restart": "Restart",
    "shutdown": "Shutdown",
    "logout": "Logout",
    "hibernate": "Hibernate",
    "volume_up": "Volume Up",
    "volume_down": "Volume Down",
    "mute": "Toggle Mute",
    "play_pause": "Play/Pause",
    "next": "Next Track",
    "prev": "Previous Track",
    "brightness_up": "Brightness Up",
    "brightness_down": "Brightness Down",
}


def _check_tool(name: str) -> bool:
    return shutil.which(name) is not None


async def broadcast(message: str):
    if CONNECTED_CLIENTS:
        await asyncio.gather(
            *(client.send(message) for client in CONNECTED_CLIENTS.copy()),
            return_exceptions=True
        )


def _run_async(cmd: list, shell: bool = False) -> dict:
    try:
        subprocess.Popen(cmd, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _run_sync(cmd: list, shell: bool = False) -> dict:
    try:
        subprocess.run(cmd, shell=shell, capture_output=True, check=True)
        return {"status": "ok"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr.decode().strip() if e.stderr else str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_command(command: str) -> dict:
    log.info(f"Executing: {command}")

    if command.startswith("open_url:"):
        url = command.split("open_url:", 1)[1].strip()
        webbrowser.open(url)
        return {"status": "ok", "command": command}

    if command in ("restart", "reboot"):
        return _handle_power("restart")

    if command == "shutdown":
        return _handle_power("shutdown")

    if command == "logout":
        return _handle_power("logout")

    if command == "hibernate":
        return _handle_power("hibernate")

    if command == "browser":
        webbrowser.open("https://google.com")
        return {"status": "ok", "command": command}

    if command == "spotify":
        return _launch_spotify()

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
        log.error(f"Command execution error: {e}")
        return {"status": "error", "message": str(e)}


def _handle_power(action: str) -> dict:
    if SYSTEM == "Linux":
        cmds = {
            "restart": ["systemctl", "reboot"],
            "shutdown": ["systemctl", "poweroff"],
            "logout": ["loginctl", "terminate-user", os.environ.get("USER", "")],
            "hibernate": ["systemctl", "hibernate"],
        }
        return _run_async(cmds.get(action, []))
    elif SYSTEM == "Darwin":
        scripts = {
            "restart": 'tell app "System Events" to restart',
            "shutdown": 'tell app "System Events" to shut down',
            "logout": 'tell app "System Events" to log out',
            "hibernate": 'tell app "System Events" to sleep',
        }
        return _run_async(["osascript", "-e", scripts.get(action, "")])
    elif SYSTEM == "Windows":
        cmds = {
            "restart": ["shutdown", "/r", "/t", "0"],
            "shutdown": ["shutdown", "/s", "/t", "0"],
            "logout": ["shutdown", "/l"],
            "hibernate": ["shutdown", "/h"],
        }
        return _run_async(cmds.get(action, []))
    return {"status": "error", "message": f"Power action not supported on {SYSTEM}"}


def _launch_spotify() -> dict:
    if SYSTEM == "Darwin" and os.path.exists("/Applications/Spotify.app"):
        return _run_async(["open", "-a", "Spotify"])
    elif SYSTEM == "Linux" and _check_tool("spotify"):
        return _run_async(["spotify"])
    elif SYSTEM == "Windows" and _check_tool("spotify"):
        return _run_async(["start", "spotify"], shell=True)
    webbrowser.open("https://open.spotify.com")
    return {"status": "ok", "command": "spotify"}


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
            "brightness_up": 'tell application "System Events" to key code 144',
            "brightness_down": 'tell application "System Events" to key code 145',
        }
        script = cmds.get(command)
        if script:
            applescript.AppleScript(script).run()
            return {"status": "ok", "command": command}
        return _run_async(["open", "-a", command])
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
    }

    if command in ("volume_up", "volume_down", "mute"):
        return _linux_volume(command)

    if command in ("play_pause", "next", "prev"):
        return _linux_media(command)

    if command in ("brightness_up", "brightness_down"):
        return _linux_brightness(command)

    if command == "screenshot":
        return _linux_screenshot()

    if command == "lock":
        return _run_sync(["loginctl", "lock-session"])

    if command == "sleep":
        return _run_async(["systemctl", "suspend"])

    app = app_map.get(command, command)
    if app is None:
        return {"status": "error", "message": f"No mapping for: {command}"}
    return _run_async([app])


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


def _linux_volume(command: str) -> dict:
    actions = {
        "volume_up": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
        "volume_down": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
        "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
    }
    return _run_sync(actions[command])


def _linux_media(command: str) -> dict:
    key_map = {"play_pause": "XF86AudioPlay", "next": "XF86AudioNext", "prev": "XF86AudioPrev"}
    action_map = {"play_pause": "play-pause", "next": "next", "prev": "previous"}
    key = key_map.get(command)
    action = action_map.get(command)

    if _check_tool("playerctl"):
        return _run_sync(["playerctl", action])
    if _check_tool("ydotool"):
        return _run_sync(["ydotool", "key", key])
    if _check_tool("wtype"):
        return _run_sync(["wtype", "-k", key])
    if _check_tool("xdotool"):
        return _run_sync(["xdotool", "key", key])
    return {"status": "error", "message": "No media key tool found (install playerctl or wtype)"}


def _linux_brightness(command: str) -> dict:
    if _check_tool("brightnessctl"):
        arg = "5%+" if "up" in command else "5%-"
        return _run_sync(["brightnessctl", "s", arg])
    if _check_tool("xbacklight"):
        arg = "+5" if "up" in command else "-5"
        return _run_sync(["xbacklight", arg])

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

    tools = [
        (["spectacle", "-b", "-n", "-o", filename], "spectacle"),
        (["gnome-screenshot", "-f", filename], "gnome-screenshot"),
        (["grim", filename], "grim"),
        (["scrot", filename], "scrot"),
        (["import", "-window", "root", filename], "import"),
    ]

    for cmd, tool in tools:
        if _check_tool(tool):
            subprocess.Popen(cmd)
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
        return _windows_media(command)

    if command == "lock":
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return {"status": "ok", "command": command}

    if command == "sleep":
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return {"status": "ok", "command": command}

    if command in ("brightness_up", "brightness_down"):
        return _windows_brightness(command)

    app = app_map.get(command, command)
    subprocess.Popen(["start", app], shell=True)
    return {"status": "ok", "command": command}


def _windows_media(command: str) -> dict:
    try:
        import win32api
        import win32con
        vk_map = {
            "volume_up": 0xAF, "volume_down": 0xAE, "mute": 0xAD,
            "play_pause": 0xB3, "next": 0xB0, "prev": 0xB1,
        }
        vk = vk_map[command]
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        return {"status": "ok", "command": command}
    except ImportError:
        return {"status": "error", "message": "pip3 install pywin32 on Windows"}


def _windows_brightness(command: str) -> dict:
    try:
        import wmi
        w = wmi.WMI(namespace='wmi')
        for monitor in w.WmiMonitorBrightnessMethods():
            current = monitor.WmiMonitorBrightness()[0].CurrentBrightness
            step = 10
            new_val = current + step if "up" in command else current - step
            new_val = max(0, min(100, new_val))
            monitor.WmiSetBrightness(new_val, 0)
            return {"status": "ok", "command": command}
    except ImportError:
        return {"status": "error", "message": "pip3 install wmi on Windows"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
            result["command"] = command
            await websocket.send(json.dumps(result))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        log.info(f"Client disconnected: {addr}")


def get_best_local_ip() -> str:
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
                    await asyncio.wait_for(ws.ping(), timeout=5)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                CONNECTED_CLIENTS.discard(ws)


async def main():
    if SYSTEM == "Linux":
        asyncio.create_task(asyncio.to_thread(updater.check_for_updates))

    host = "0.0.0.0"
    port = PORT
    local_ip = get_best_local_ip()

    print("\033[36m")
    print("   ____  __                     ____            __  ")
    print("  / __ \\/ /_  ____  ____  ___  / __ \\___  _____/ /__")
    print(" / /_/ / __ \\/ __ \\/ __ \\/ _ \\/ / / / _ \\/ ___/ //_/")
    print("/ ____/ / / / /_/ / / / /  __/ /_/ /  __/ /__/ ,<   ")
    print("/_/   /_/ /_/\\____/_/ /_/\\___/_____/\\___/\\___/_/|_| \033[0m")
    print()
    print("  \033[1;35mBuilt with \u2764 by @iamhero337\033[0m")
    print("  \033[1;33mVersion: \033[0m\033[1;97m{}\033[0m".format(VERSION))
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
        properties={"version": VERSION.encode()},
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
        subprocess.run(["loginctl", "enable-linger", os.environ.get("USER", "")], capture_output=True)
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

    if "--version" in sys.argv:
        print(VERSION)
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