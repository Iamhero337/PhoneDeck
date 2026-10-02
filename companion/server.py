#!/usr/bin/env python3
"""
PhoneDeck Desktop Companion Server
Run this on your desktop to receive commands from the PhoneDeck Android app.
"""

import asyncio
import copy
import glob
import http.server
import json
import logging
import os
import platform
import signal
import socket
import subprocess
import shlex
import shutil
import sys
import threading
import time
import urllib.parse
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
    from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "zeroconf"])
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "zeroconf", "--break-system-packages"])
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

VERSION = "1.5.0"
PORT = 9090
CONFIG_PORT = 9091
CONFIG_DIR = os.path.expanduser("~/.phonedeck")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
# PyInstaller unpacks bundled data files to sys._MEIPASS; fall back to the source tree.
WEB_UI_DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "web-ui")
WEB_UI_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/script.js": ("script.js", "application/javascript; charset=utf-8"),
}
PROTECTED_PAGES = {"prod", "media", "system"}
MAX_LABEL_LEN = 64
MAX_COMMAND_LEN = 2048

DEFAULT_PAGES = [
    {"id": "prod", "name": "Prod", "tiles": [
        {"id": "dev1", "label": "VS Code", "icon": "code", "command": "code", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "dev2", "label": "Terminal", "icon": "terminal", "command": "terminal", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "dev3", "label": "Browser", "icon": "public", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "dev4", "label": "Spotify", "icon": "music_note", "command": "spotify", "color": 0xFF1E1E2E, "iconColor": 0xFF1DB954},
        {"id": "dev5", "label": "Slack", "icon": "chat", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFF4A154B},
        {"id": "dev6", "label": "Docker", "icon": "cloud", "command": "terminal", "color": 0xFF1E1E2E, "iconColor": 0xFF2496ED},
        {"id": "dev7", "label": "Postman", "icon": "api", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFFFF6C37},
        {"id": "dev8", "label": "Zoom", "icon": "videocam", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFF2D8CFF},
        {"id": "dev9", "label": "Notion", "icon": "article", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFF000000},
    ]},
    {"id": "media", "name": "Media", "tiles": [
        {"id": "md1", "label": "Volume Up", "icon": "volume_up", "command": "volume_up", "color": 0xFF1E1E2E, "iconColor": 0xFF4CAF50},
        {"id": "md2", "label": "Volume Down", "icon": "volume_down", "command": "volume_down", "color": 0xFF1E1E2E, "iconColor": 0xFF4CAF50},
        {"id": "md3", "label": "Mute", "icon": "volume_off", "command": "mute", "color": 0xFF1E1E2E, "iconColor": 0xFF4CAF50},
        {"id": "md4", "label": "Play/Pause", "icon": "play_pause", "command": "play_pause", "color": 0xFF1E1E2E, "iconColor": 0xFF1DB954},
        {"id": "md5", "label": "Next", "icon": "next", "command": "next", "color": 0xFF1E1E2E, "iconColor": 0xFF1DB954},
        {"id": "md6", "label": "Prev", "icon": "prev", "command": "prev", "color": 0xFF1E1E2E, "iconColor": 0xFF1DB954},
    ]},
    {"id": "system", "name": "System", "tiles": [
        {"id": "sys1", "label": "Screenshot", "icon": "screenshot", "command": "screenshot", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "sys2", "label": "Lock", "icon": "lock", "command": "lock", "color": 0xFF1E1E2E, "iconColor": 0xFFE53935},
        {"id": "sys3", "label": "Sleep", "icon": "bedtime", "command": "sleep", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "sys4", "label": "Browser", "icon": "public", "command": "browser", "color": 0xFF1E1E2E, "iconColor": 0xFF4A90D9},
        {"id": "sys5", "label": "Restart", "icon": "restart", "command": "restart", "color": 0xFF1E1E2E, "iconColor": 0xFFF57C00},
        {"id": "sys6", "label": "Shutdown", "icon": "shutdown", "command": "shutdown", "color": 0xFF1E1E2E, "iconColor": 0xFFF57C00},
        {"id": "sys7", "label": "Logout", "icon": "logout", "command": "logout", "color": 0xFF1E1E2E, "iconColor": 0xFFF57C00},
        {"id": "sys8", "label": "Hibernate", "icon": "hibernate", "command": "hibernate", "color": 0xFF1E1E2E, "iconColor": 0xFFF57C00},
        {"id": "sys9", "label": "Brightness +", "icon": "brightness_up", "command": "brightness_up", "color": 0xFF1E1E2E, "iconColor": 0xFFFFC107},
        {"id": "sys10", "label": "Brightness -", "icon": "brightness_down", "command": "brightness_down", "color": 0xFF1E1E2E, "iconColor": 0xFFFFC107},
    ]},
]

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


def _to_color_int(value, default):
    """Accept a '#rrggbb' string or an ARGB int (signed or unsigned) and return an unsigned ARGB int."""
    if isinstance(value, str):
        try:
            return hex_to_color_int(value)
        except (ValueError, IndexError):
            return default
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return value & 0xFFFFFFFF


def _clean_tile(data, existing=None):
    """Validate and normalise tile fields coming from the web UI or an import."""
    tile = dict(existing or {})
    if "label" in data or existing is None:
        tile["label"] = str(data.get("label", "")).strip()[:MAX_LABEL_LEN]
    if "command" in data or existing is None:
        tile["command"] = str(data.get("command", "")).strip()[:MAX_COMMAND_LEN]
    if "icon" in data or existing is None:
        tile["icon"] = str(data.get("icon", "") or "apps").strip()[:64] or "apps"
    if "color" in data or existing is None:
        tile["color"] = _to_color_int(data.get("color"), 0xFF1E1E2E)
    if "iconColor" in data or existing is None:
        tile["iconColor"] = _to_color_int(data.get("iconColor"), 0xFF4A90D9)
    return tile


class ConfigManager:
    """Thread-safe store for pages/tiles, persisted to ~/.phonedeck/config.json.

    `revision` increments on every change; `synced_revision` records the revision
    last pushed to phones, so the web UI can show unsynced edits and phone
    config_init messages don't clobber them.
    """

    def __init__(self):
        self.pages = []
        self.revision = 0
        self.synced_revision = 0
        self._lock = threading.RLock()
        self.load()

    @property
    def dirty(self):
        return self.revision != self.synced_revision

    def load(self):
        with self._lock:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE) as f:
                        data = json.load(f)
                        self.pages = data.get("pages", [])
                        if data.get("pendingSync"):
                            self.synced_revision = -1
                except Exception:
                    log.warning("Config file is unreadable, falling back to defaults")
                    self.pages = []
            if not self.pages:
                self.pages = copy.deepcopy(DEFAULT_PAGES)
                self.save(synced=True)

    def save(self, synced=False):
        with self._lock:
            self.revision += 1
            if synced:
                self.synced_revision = self.revision
            self._write()

    def _write(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        # Write to a temp file and rename so a crash never leaves a truncated config.
        # pendingSync survives restarts so a reconnecting phone can't overwrite unsynced edits.
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"version": "1", "pendingSync": self.dirty, "pages": self.pages}, f, indent=2)
        os.replace(tmp, CONFIG_FILE)

    def mark_synced(self):
        with self._lock:
            if self.dirty:
                self.synced_revision = self.revision
                self._write()

    def snapshot(self):
        with self._lock:
            return copy.deepcopy(self.pages), self.revision

    def reset_to_defaults(self):
        with self._lock:
            self.pages = copy.deepcopy(DEFAULT_PAGES)
            self.save()

    def get_pages(self):
        with self._lock:
            return copy.deepcopy(self.pages)

    def set_pages(self, pages, from_phone=False):
        with self._lock:
            self.pages = pages
            # When the config came from the phone, the phone already has it: nothing is pending.
            self.save(synced=from_phone)

    def import_pages(self, pages):
        """Replace all pages with validated imported data. Returns the page count or None if invalid."""
        if not isinstance(pages, list):
            return None
        cleaned = []
        for p in pages:
            if not isinstance(p, dict) or not str(p.get("name", "")).strip():
                return None
            tiles = []
            for t in p.get("tiles", []) or []:
                if not isinstance(t, dict):
                    return None
                tile = _clean_tile(t)
                tile["id"] = str(t.get("id") or uuid.uuid4())
                tiles.append(tile)
            cleaned.append({
                "id": str(p.get("id") or uuid.uuid4()),
                "name": str(p["name"]).strip()[:MAX_LABEL_LEN],
                "tiles": tiles,
            })
        with self._lock:
            self.pages = cleaned
            self.save()
        return len(cleaned)

    def _find_page(self, page_id):
        return next((p for p in self.pages if p["id"] == page_id), None)

    def add_page(self, name):
        with self._lock:
            page = {"id": str(uuid.uuid4()), "name": name[:MAX_LABEL_LEN], "tiles": []}
            self.pages.append(page)
            self.save()
            return copy.deepcopy(page)

    def update_page(self, page_id, name):
        with self._lock:
            page = self._find_page(page_id)
            if not page:
                return None
            page["name"] = name[:MAX_LABEL_LEN]
            self.save()
            return copy.deepcopy(page)

    def delete_page(self, page_id):
        with self._lock:
            if page_id in PROTECTED_PAGES:
                return False
            self.pages = [p for p in self.pages if p["id"] != page_id]
            self.save()
            return True

    def reorder_pages(self, order):
        """Reorder pages to match a list of ids. Unknown ids are ignored, missing pages keep their relative order at the end."""
        with self._lock:
            by_id = {p["id"]: p for p in self.pages}
            ordered = [by_id.pop(pid) for pid in order if pid in by_id]
            self.pages = ordered + [p for p in self.pages if p["id"] in by_id]
            self.save()

    def add_tile(self, page_id, tile_data):
        with self._lock:
            page = self._find_page(page_id)
            if not page:
                return None
            tile = {"id": str(uuid.uuid4())}
            tile.update(_clean_tile(tile_data))
            page.setdefault("tiles", []).append(tile)
            self.save()
            return copy.deepcopy(tile)

    def update_tile(self, tile_id, tile_data):
        with self._lock:
            for page in self.pages:
                for i, tile in enumerate(page.get("tiles", [])):
                    if tile["id"] == tile_id:
                        page["tiles"][i] = _clean_tile(tile_data, existing=tile)
                        self.save()
                        return copy.deepcopy(page["tiles"][i])
            return None

    def duplicate_tile(self, tile_id):
        with self._lock:
            for page in self.pages:
                tiles = page.get("tiles", [])
                for i, tile in enumerate(tiles):
                    if tile["id"] == tile_id:
                        clone = copy.deepcopy(tile)
                        clone["id"] = str(uuid.uuid4())
                        clone["label"] = (tile.get("label", "") + " copy")[:MAX_LABEL_LEN]
                        tiles.insert(i + 1, clone)
                        self.save()
                        return copy.deepcopy(clone)
            return None

    def move_tile(self, tile_id, target_page_id, index=None):
        """Move a tile to another page (or position). Returns the tile or None."""
        with self._lock:
            target = self._find_page(target_page_id)
            if not target:
                return None
            for page in self.pages:
                tiles = page.get("tiles", [])
                for i, tile in enumerate(tiles):
                    if tile["id"] == tile_id:
                        tiles.pop(i)
                        dest = target.setdefault("tiles", [])
                        if index is None or not isinstance(index, int) or index > len(dest):
                            index = len(dest)
                        dest.insert(max(0, index), tile)
                        self.save()
                        return copy.deepcopy(tile)
            return None

    def reorder_tiles(self, page_id, order):
        with self._lock:
            page = self._find_page(page_id)
            if not page:
                return False
            by_id = {t["id"]: t for t in page.get("tiles", [])}
            ordered = [by_id.pop(tid) for tid in order if tid in by_id]
            page["tiles"] = ordered + [t for t in page.get("tiles", []) if t["id"] in by_id]
            self.save()
            return True

    def delete_tile(self, page_id, tile_id):
        with self._lock:
            page = self._find_page(page_id)
            if not page:
                return False
            before = len(page.get("tiles", []))
            page["tiles"] = [t for t in page.get("tiles", []) if t["id"] != tile_id]
            if len(page["tiles"]) == before:
                return False
            self.save()
            return True


def hex_to_color_int(hex_str):
    hex_str = hex_str.lstrip("#")
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return (0xFF << 24) | (r << 16) | (g << 8) | b


config_manager = ConfigManager()


def scan_installed_apps():
    try:
        if SYSTEM == "Linux":
            return _scan_linux_apps()
        elif SYSTEM == "Darwin":
            return _scan_macos_apps()
        elif SYSTEM == "Windows":
            return _scan_windows_apps()
    except Exception as e:
        log.warning(f"App scan failed: {e}")
    return []


def _parse_desktop_entry(content):
    """Return the key/values of the [Desktop Entry] group only (later groups are Desktop Actions)."""
    entry = {}
    in_entry = False
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
            continue
        if in_entry and "=" in line:
            key, value = line.split("=", 1)
            entry.setdefault(key.strip(), value.strip())
    return entry


def _desktop_exec_to_command(exec_line):
    """Turn a desktop Exec= line into a command PhoneDeck can launch (field codes like %U removed)."""
    try:
        parts = shlex.split(exec_line)
    except ValueError:
        return None
    # Drop field codes (%U, %f…) and Flatpak's file-forwarding markers, which only matter when opening files.
    parts = [p for p in parts
             if not (len(p) == 2 and p.startswith("%")) and p not in ("@@", "@@u", "--file-forwarding")]
    if not parts:
        return None
    # Prefer the bare program name when the absolute path is what PATH resolves to anyway.
    base = os.path.basename(parts[0])
    if parts[0].startswith("/") and shutil.which(base) == parts[0]:
        parts[0] = base
    return shlex.join(parts)


def _scan_linux_apps():
    seen = set()
    apps = []
    data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    dirs = [os.path.expanduser("~/.local/share/applications")]
    dirs += [os.path.join(d, "applications") for d in data_dirs if d]
    dirs += [
        "/var/lib/snapd/desktop/applications",
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    ]
    for d in dict.fromkeys(dirs):
        if not os.path.isdir(d):
            continue
        try:
            files = sorted(os.listdir(d))
        except OSError:
            continue
        for f in files:
            if not f.endswith(".desktop"):
                continue
            try:
                with open(os.path.join(d, f), "r", errors="ignore") as fh:
                    entry = _parse_desktop_entry(fh.read())
            except OSError:
                continue
            name = entry.get("Name")
            if not name or name in seen:
                continue
            if entry.get("Type", "Application") != "Application":
                continue
            if entry.get("NoDisplay") == "true" or entry.get("Hidden") == "true":
                continue
            cmd = _desktop_exec_to_command(entry.get("Exec", ""))
            if not cmd:
                continue
            seen.add(name)
            apps.append({"name": name, "command": cmd})
    return sorted(apps, key=lambda x: x["name"].lower())


def _scan_macos_apps():
    apps = []
    seen = set()
    dirs = [
        "/Applications",
        "/Applications/Utilities",
        os.path.expanduser("~/Applications"),
        "/System/Applications",
        "/System/Applications/Utilities",
    ]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        try:
            for f in sorted(os.listdir(d)):
                if not f.endswith(".app"):
                    continue
                name = f[:-len(".app")]
                if name in seen:
                    continue
                seen.add(name)
                # _macos_command runs `open -a <command>`, so the command is just the app name.
                apps.append({"name": name, "command": name})
        except OSError:
            continue
    return sorted(apps, key=lambda x: x["name"].lower())


def _scan_windows_apps():
    apps = []
    dirs = [
        os.path.expandvars("%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"),
    ]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        try:
            for root, _dirs, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = os.path.splitext(f)[0]
                        if "uninstall" in name.lower():
                            continue
                        # _windows_command opens existing paths with os.startfile.
                        apps.append({"name": name, "command": os.path.join(root, f)})
        except OSError:
            continue
    seen = set()
    unique = []
    for a in apps:
        if a["name"] not in seen:
            seen.add(a["name"])
            unique.append(a)
    return sorted(unique, key=lambda x: x["name"].lower())


_apps_cache = {"time": 0.0, "apps": []}
_apps_lock = threading.Lock()


def cached_installed_apps(max_age=60):
    with _apps_lock:
        if time.time() - _apps_cache["time"] > max_age or not _apps_cache["apps"]:
            _apps_cache["apps"] = scan_installed_apps()
            _apps_cache["time"] = time.time()
        return _apps_cache["apps"]


def _is_local_host_name(host):
    """True if `host` (from a Host/Origin header, no port) names this machine rather than an arbitrary domain.

    Rejecting other names blocks DNS-rebinding attacks from websites against the config API.
    """
    host = host.strip("[]").lower()
    if host in ("localhost", "") or host.endswith(".localhost"):
        return True
    try:
        socket.inet_pton(socket.AF_INET6 if ":" in host else socket.AF_INET, host)
        return True
    except OSError:
        pass
    hostname = socket.gethostname().lower()
    return host in (hostname, hostname + ".local", hostname.split(".")[0] + ".local")


class ConfigHTTPHandler(http.server.BaseHTTPRequestHandler):
    config_manager = None
    main_loop = None
    server_version = "PhoneDeck/" + VERSION

    CSP = ("default-src 'self'; script-src 'self'; "
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
           "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

    def log_message(self, format, *args):
        log.debug(f"[HTTP] {format % args}")

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, name, mime):
        try:
            with open(os.path.join(WEB_UI_DIR, name), "rb") as f:
                content = f.read()
        except OSError:
            self._send_json({"error": f"Web UI file missing: {name}"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", self.CSP)
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _host_ok(self):
        host = self.headers.get("Host", "")
        return _is_local_host_name(urllib.parse.urlsplit("//" + host).hostname or "")

    def _write_allowed(self):
        """Block cross-site requests: any Origin must match our Host, and bodies must be JSON
        (which forces a CORS preflight that this server never approves)."""
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get("Host", ""):
            return False
        if self.command in ("POST", "PUT"):
            ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if ctype != "application/json":
                return False
        return True

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > 2 * 1024 * 1024:
            raise ValueError("Request body too large")
        body = self.rfile.read(length).decode() if length else "{}"
        data = json.loads(body or "{}")
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def _dispatch(self, method):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if not self._host_ok():
            self._send_json({"error": "Forbidden host"}, 403)
            return
        if method != "GET" and not self._write_allowed():
            self._send_json({"error": "Cross-origin request blocked"}, 403)
            return
        data = {}
        if method in ("POST", "PUT"):
            try:
                data = self._read_json()
            except (ValueError, json.JSONDecodeError) as e:
                self._send_json({"error": f"Invalid JSON: {e}"}, 400)
                return
        parts = [p for p in path.split("/") if p]
        try:
            getattr(self, f"_handle_{method.lower()}")(path, parts, data)
        except Exception as e:
            log.exception("HTTP handler error")
            self._send_json({"error": str(e)}, 500)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _status(self):
        cm = self.config_manager
        return {
            "connected": len(CONNECTED_CLIENTS),
            "version": VERSION,
            "revision": cm.revision,
            "dirty": cm.dirty,
        }

    def _handle_get(self, path, parts, data):
        cm = self.config_manager
        if path in WEB_UI_FILES:
            self._send_file(*WEB_UI_FILES[path])
        elif path == "/api/pages":
            pages, revision = cm.snapshot()
            self._send_json({"pages": pages, "revision": revision})
        elif path == "/api/apps":
            self._send_json({"apps": cached_installed_apps()})
        elif path == "/api/status":
            self._send_json(self._status())
        elif path == "/api/meta":
            self._send_json({
                "version": VERSION,
                "platform": SYSTEM,
                "hostname": socket.gethostname(),
                "protectedPages": sorted(PROTECTED_PAGES),
                "commands": [{"command": k, "label": v} for k, v in COMMAND_MAP.items()],
            })
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_post(self, path, parts, data):
        cm = self.config_manager
        if path == "/api/pages":
            name = str(data.get("name", "")).strip()
            if not name:
                return self._send_json({"error": "Name is required"}, 400)
            self._send_json({"page": cm.add_page(name)}, 201)

        elif path == "/api/pages/reorder":
            order = data.get("order")
            if not isinstance(order, list):
                return self._send_json({"error": "order must be a list of page ids"}, 400)
            cm.reorder_pages([str(x) for x in order])
            self._send_json({"status": "ok"})

        elif path == "/api/tiles":
            page_id = data.get("pageId", "")
            if not page_id:
                return self._send_json({"error": "pageId is required"}, 400)
            if not str(data.get("label", "")).strip():
                return self._send_json({"error": "Label is required"}, 400)
            tile = cm.add_tile(page_id, data)
            if tile:
                self._send_json({"tile": tile}, 201)
            else:
                self._send_json({"error": "Page not found"}, 404)

        elif path == "/api/tiles/reorder":
            order = data.get("order")
            if not isinstance(order, list):
                return self._send_json({"error": "order must be a list of tile ids"}, 400)
            if cm.reorder_tiles(data.get("pageId", ""), [str(x) for x in order]):
                self._send_json({"status": "ok"})
            else:
                self._send_json({"error": "Page not found"}, 404)

        elif len(parts) == 4 and parts[:2] == ["api", "tiles"] and parts[3] == "duplicate":
            tile = cm.duplicate_tile(parts[2])
            if tile:
                self._send_json({"tile": tile}, 201)
            else:
                self._send_json({"error": "Tile not found"}, 404)

        elif len(parts) == 4 and parts[:2] == ["api", "tiles"] and parts[3] == "move":
            tile = cm.move_tile(parts[2], data.get("pageId", ""), data.get("index"))
            if tile:
                self._send_json({"tile": tile})
            else:
                self._send_json({"error": "Tile or page not found"}, 404)

        elif path == "/api/test":
            command = str(data.get("command", "")).strip()
            if not command:
                return self._send_json({"error": "Command is required"}, 400)
            result = execute_command(command)
            self._send_json(result, 200 if result.get("status") == "ok" else 400)

        elif path == "/api/import":
            count = cm.import_pages(data.get("pages"))
            if count is None:
                return self._send_json({"error": "Invalid config: expected {\"pages\": [{\"name\", \"tiles\"}]}"}, 400)
            self._send_json({"status": "ok", "pages": count})

        elif path == "/api/reset":
            cm.reset_to_defaults()
            self._send_json({"status": "ok"})

        elif path == "/api/sync":
            connected = self._send_config_sync_to_phones()
            self._send_json({"connected": connected, "status": "ok", **self._status()})

        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_put(self, path, parts, data):
        cm = self.config_manager
        if len(parts) == 3 and parts[:2] == ["api", "pages"]:
            name = str(data.get("name", "")).strip()
            if not name:
                return self._send_json({"error": "Name is required"}, 400)
            page = cm.update_page(parts[2], name)
            if page:
                self._send_json({"page": page})
            else:
                self._send_json({"error": "Page not found"}, 404)

        elif len(parts) == 3 and parts[:2] == ["api", "tiles"]:
            if "label" in data and not str(data["label"]).strip():
                return self._send_json({"error": "Label is required"}, 400)
            fields = {k: data[k] for k in ("label", "command", "icon", "color", "iconColor") if k in data}
            tile = cm.update_tile(parts[2], fields)
            if tile:
                self._send_json({"tile": tile})
            else:
                self._send_json({"error": "Tile not found"}, 404)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_delete(self, path, parts, data):
        cm = self.config_manager
        if len(parts) == 3 and parts[:2] == ["api", "pages"]:
            if cm.delete_page(parts[2]):
                self._send_json({"status": "deleted"})
            else:
                self._send_json({"error": "Built-in pages can't be deleted"}, 400)

        elif len(parts) == 4 and parts[:2] == ["api", "tiles"]:
            if cm.delete_tile(parts[2], parts[3]):
                self._send_json({"status": "deleted"})
            else:
                self._send_json({"error": "Tile not found"}, 404)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _send_config_sync_to_phones(self):
        connected = len(CONNECTED_CLIENTS)
        if connected and self.main_loop:
            asyncio.run_coroutine_threadsafe(push_config_to_phones(), self.main_loop)
        return connected


async def push_config_to_phones(clients=None):
    """Send the current config to phones and mark it as synced."""
    pages, revision = config_manager.snapshot()
    message = json.dumps({"type": "config_sync", "pages": pages})
    targets = clients if clients is not None else CONNECTED_CLIENTS.copy()
    if not targets:
        return
    await asyncio.gather(*(c.send(message) for c in targets), return_exceptions=True)
    with config_manager._lock:
        if config_manager.revision == revision:
            config_manager.mark_synced()


def start_http_server(cm, main_loop):
    ConfigHTTPHandler.config_manager = cm
    ConfigHTTPHandler.main_loop = main_loop
    try:
        server = http.server.ThreadingHTTPServer(("0.0.0.0", CONFIG_PORT), ConfigHTTPHandler)
    except OSError as e:
        log.error(f"Config web UI could not start on port {CONFIG_PORT}: {e}")
        return
    server.daemon_threads = True
    log.info(f"Config web UI started at http://localhost:{CONFIG_PORT}")
    try:
        server.serve_forever()
    except Exception:
        log.exception("Config web UI stopped")


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
    # Commands may carry arguments (e.g. "flatpak run org.app.Name"); split without a shell.
    try:
        argv = shlex.split(app)
    except ValueError as e:
        return {"status": "error", "message": f"Invalid command: {e}"}
    if not argv:
        return {"status": "error", "message": "Empty command"}
    if not shutil.which(argv[0]):
        return {"status": "error", "message": f"Program not found: {argv[0]}"}
    return _run_async(argv)


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
            try:
                subprocess.Popen(["notify-send", "PhoneDeck", f"Screenshot saved: {filename}"])
            except Exception:
                pass
            return {"status": "ok", "message": f"Screenshot saved to {filename}"}

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

    if os.path.exists(command):
        os.startfile(command)
        return {"status": "ok", "command": command}

    app = app_map.get(command, command)
    # `start "" <app>` resolves App Paths entries; quote via list2cmdline to avoid shell injection.
    subprocess.Popen("start \"\" " + subprocess.list2cmdline([app]), shell=True)
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
            log.info(f"Received: {message[:300]}")
            command = ""
            try:
                payload = json.loads(message)
                msg_type = payload.get("type", "")
                if msg_type == "config_init":
                    pages = payload.get("pages", [])
                    if config_manager.dirty:
                        # Edits made in the web UI haven't reached the phone yet; push them
                        # instead of overwriting them with the phone's older copy.
                        log.info("Phone connected with stale config, sending desktop edits")
                        await websocket.send(json.dumps({"type": "config_init_ack", "status": "ok"}))
                        await push_config_to_phones({websocket})
                        continue
                    if pages:
                        config_manager.set_pages(pages, from_phone=True)
                        log.info(f"Config received from phone ({len(pages)} pages)")
                    await websocket.send(json.dumps({"type": "config_init_ack", "status": "ok"}))
                    continue
                elif msg_type == "command":
                    command = payload.get("command", "")
                else:
                    command = payload.get("command", message)
            except (json.JSONDecodeError, TypeError):
                command = message.strip()

            if command:
                result = execute_command(command)
                result["command"] = command
                try:
                    await websocket.send(json.dumps(result))
                except Exception:
                    pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        log.info(f"Client disconnected: {addr}")


def get_best_local_ip() -> str:
    try:
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
    print("  ║  \033[33mConnect from PhoneDeck app to:\033[0m      ║")
    print(f"  ║  ws://{local_ip}:{port:<26} ║")
    print("  ║                                      ║")
    print("  ║  \033[32mThe app will now auto-discover\033[0m      ║")
    print("  ║  \033[32mthis server using mDNS.\033[0m             ║")
    print("  ║                                      ║")
    print(f"  ║  \033[36mConfig UI: http://{local_ip}:{CONFIG_PORT}\033[0m ║")
    print(f"  ║  \033[36m          http://localhost:{CONFIG_PORT}\033[0m  ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    main_loop = asyncio.get_running_loop()
    http_thread = threading.Thread(target=start_http_server, args=(config_manager, main_loop), daemon=True)
    http_thread.start()

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
        if os.path.exists(target_bin):
            os.remove(target_bin)
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
        subprocess.check_call(["systemctl", "--user", "enable", "phonedeck.service"])
        subprocess.check_call(["systemctl", "--user", "restart", "phonedeck.service"])
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