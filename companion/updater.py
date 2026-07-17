import urllib.request
import json
import os
import sys
import subprocess
import platform
import time

CURRENT_VERSION = "v1.1.2"
REPO = "Iamhero337/PhoneDeck"

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            if latest_version != CURRENT_VERSION:
                print(f"New version {latest_version} found! Updating...")
                do_update(data)
    except Exception as e:
        print("Update check failed:", e)

def do_update(release_data):
    sys_plat = platform.system()
    
    if sys_plat == "Windows":
        # Find the .exe asset
        exe_url = None
        for asset in release_data['assets']:
            if asset['name'].endswith('.exe'):
                exe_url = asset['browser_download_url']
                break
        
        if exe_url:
            update_windows(exe_url)
    elif sys_plat == "Linux":
        # Just pull the latest from git and restart service
        try:
            print("Pulling latest code via git...")
            subprocess.run(["git", "pull", "origin", "master"], cwd=os.path.dirname(os.path.abspath(__file__)))
            print("Restarting service...")
            subprocess.run(["systemctl", "--user", "restart", "phonedeck.service"])
        except Exception as e:
            print("Failed to auto-update on Linux:", e)
    elif sys_plat == "Darwin":
        try:
            subprocess.run(["git", "pull", "origin", "master"], cwd=os.path.dirname(os.path.abspath(__file__)))
            print("Updated. Please restart the script manually.")
        except Exception as e:
            pass

def update_windows(url):
    try:
        current_exe = sys.executable
        new_exe = current_exe + ".new"
        
        print("Downloading new version...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(new_exe, 'wb') as out_file:
            out_file.write(response.read())
            
        # Create a batch script to replace the exe and restart
        bat_script = f"""@echo off
timeout /t 2 /nobreak > NUL
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        bat_path = os.path.join(os.path.dirname(current_exe), "update_phonedeck.bat")
        with open(bat_path, "w") as f:
            f.write(bat_script)
            
        # Launch batch and exit
        subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    except Exception as e:
        print("Windows update failed:", e)

if __name__ == "__main__":
    check_for_updates()
