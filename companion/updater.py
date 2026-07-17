import json
import os
import platform
import re
import subprocess
import sys
import urllib.request

CURRENT_VERSION = "v1.2.0"
REPO = "Iamhero337/PhoneDeck"


def _parse_version(version_str: str) -> tuple:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        return tuple(int(x) for x in match.groups())
    return (0, 0, 0)


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'PhoneDeck-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']

            if _is_newer(latest_version, CURRENT_VERSION):
                print(f"New version {latest_version} found! Updating from {CURRENT_VERSION}...")
                do_update(data)
    except Exception as e:
        print("[Updater] Check failed:", e)


def do_update(release_data):
    sys_plat = platform.system()

    if sys_plat == "Windows":
        _update_windows(release_data)
    elif sys_plat == "Linux":
        _update_linux()
    elif sys_plat == "Darwin":
        _update_macos()


def _update_linux():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, ".git")):
        try:
            subprocess.run(["git", "pull", "origin", "master"], cwd=script_dir, check=True)
            subprocess.run(["systemctl", "--user", "restart", "phonedeck.service"])
            print("Updated and restarted.")
        except Exception as e:
            print("[Updater] Linux git update failed:", e)
    else:
        print("[Updater] Not a git repo. Download the latest release from:")
        print(f"  https://github.com/{REPO}/releases/latest")


def _update_macos():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, ".git")):
        try:
            subprocess.run(["git", "pull", "origin", "master"], cwd=script_dir, check=True)
            print("Updated. Please restart the script manually.")
        except Exception as e:
            print("[Updater] macOS update failed:", e)
    else:
        print(f"[Updater] Download the latest release from: https://github.com/{REPO}/releases/latest")


def _update_windows(release_data):
    try:
        exe_url = None
        for asset in release_data['assets']:
            if asset['name'].endswith('.exe'):
                exe_url = asset['browser_download_url']
                break

        if not exe_url:
            print("[Updater] No .exe asset found in release")
            return

        current_exe = sys.executable
        new_exe = current_exe + ".new"

        print("Downloading new version...")
        req = urllib.request.Request(exe_url, headers={'User-Agent': 'PhoneDeck-Updater/1.0'})
        with urllib.request.urlopen(req) as response, open(new_exe, 'wb') as out_file:
            out_file.write(response.read())

        bat_script = f"""@echo off
timeout /t 2 /nobreak > NUL
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        bat_path = os.path.join(os.path.dirname(current_exe), "update_phonedeck.bat")
        with open(bat_path, "w") as f:
            f.write(bat_script)

        subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    except Exception as e:
        print("[Updater] Windows update failed:", e)


if __name__ == "__main__":
    check_for_updates()
