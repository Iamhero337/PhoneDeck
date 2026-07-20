#!/bin/bash
# PhoneDeck macOS Installation Script
# Creates a launchd user agent for auto-start on login

set -e

SERVER_DIR="$(cd "$(dirname "$0")" && pwd)/companion"
SERVER_SCRIPT="$SERVER_DIR/server.py"
PLIST_NAME="com.phonedeck.server"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/$PLIST_NAME.plist"

echo "========================================="
echo "  PhoneDeck Server Installation (macOS)"
echo "========================================="
echo ""

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3 first."
    exit 1
fi

# Install Python dependencies
echo "[1/4] Installing Python dependencies..."
pip3 install websockets zeroconf ifaddr --break-system-packages 2>/dev/null || \
pip3 install websockets zeroconf ifaddr --user 2>/dev/null || \
pip3 install websockets zeroconf ifaddr

# Create LaunchAgents directory
mkdir -p "$PLIST_DIR"

# Create plist file
echo "[2/4] Creating launchd agent..."
cat > "$PLIST_FILE" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>python3</string>
        <string>$SERVER_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/phonedeck-server.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/phonedeck-server-error.log</string>
    <key>WorkingDirectory</key>
    <string>$SERVER_DIR</string>
</dict>
</plist>
PLIST

# Load the agent
echo "[3/4] Loading launchd agent..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

# Start the service
echo "[4/4] Starting service..."
launchctl start "$PLIST_NAME"

echo ""
echo "========================================="
echo "  ✅ PhoneDeck Server installed!"
echo "========================================="
echo ""
echo "  Status:  launchctl list | grep phonedeck"
echo "  Logs:    tail -f /tmp/phonedeck-server.log"
echo "  Restart: launchctl kickstart -k gui/\$(id -u)/$PLIST_NAME"
echo "  Stop:    launchctl unload $PLIST_FILE"
echo ""
echo "  Open the PhoneDeck app on your phone and it will"
echo "  auto-discover this server over WiFi."
echo ""
echo "  Config UI: http://localhost:9091"
echo "    (Open this in your browser to customize apps & shortcuts)"
echo ""
echo "========================================="