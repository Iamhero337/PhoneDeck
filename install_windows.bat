@echo off
REM PhoneDeck Windows Installation Script
REM Installs dependencies and creates startup entry

set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%companion\server.py" (
    set SERVER_DIR=%SCRIPT_DIR%companion
) else if exist "%SCRIPT_DIR%..\desktop\server.py" (
    set SERVER_DIR=%SCRIPT_DIR%..\desktop
) else (
    echo ERROR: Cannot find server.py. Run this script from the PhoneDeck release folder.
    pause
    exit /b 1
)
set SERVER_EXE=%SERVER_DIR%\phonedeck-server-windows.exe
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=PhoneDeck Server.lnk

echo =========================================
echo   PhoneDeck Server Installation (Windows)
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
pip install websockets zeroconf ifaddr pywin32 wmi --quiet
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may have failed to install.
)

REM Check if pre-built exe exists
if exist "%SERVER_EXE%" (
    echo [2/4] Found pre-built executable.
) else (
    echo [2/4] Building executable with PyInstaller...
    cd /d "%SERVER_DIR%"
    pyinstaller --clean --noconfirm phonedeck-server-windows.spec
    if not exist "%SERVER_EXE%" (
        echo ERROR: Failed to build executable.
        pause
        exit /b 1
    )
)

echo [3/4] Creating startup shortcut...
powershell -Command ^
    "$WshShell = New-Object -comObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%'); ^
    $Shortcut.TargetPath = '%SERVER_EXE%'; ^
    $Shortcut.WorkingDirectory = '%SERVER_DIR%'; ^
    $Shortcut.WindowStyle = 7; ^
    $Shortcut.Save()"

echo [4/4] Starting server...
cd /d "%SERVER_DIR%"
start "" "%SERVER_EXE%"

echo.
echo =========================================
echo   ✅ PhoneDeck Server installed!
echo =========================================
echo.
echo   The server is now running and will start automatically on login.
echo   Open the PhoneDeck app on your phone and it will auto-discover this server.
echo.
echo   Config UI: http://localhost:9091
echo   (Open in browser to customize apps & shortcuts)
echo.
echo   To stop: Close the console window or use Task Manager.
echo   To uninstall: Delete "%STARTUP_DIR%\%SHORTCUT_NAME%"
echo.
echo =========================================
pause