#!/bin/bash
# PhoneDeck systemd installation script
# Run: bash install_linux.sh

set -e

SERVER_DIR="$(cd "$(dirname "$0")" && pwd)/companion"
SERVER_SCRIPT="$SERVER_DIR/server.py"
TARGET_BIN="$HOME/.local/bin/phonedeck-server"

echo "========================================="
echo "  PhoneDeck Server Installation (Linux)"
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

# Create target bin directory
mkdir -p "$HOME/.local/bin"

# Check if PATH includes ~/.local/bin
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "NOTE: Add ~/.local/bin to your PATH by adding this to ~/.bashrc:"
    echo '  export PATH="$PATH:$HOME/.local/bin"'
fi

# Create launcher script (wraps python3 + server.py)
echo "[2/4] Creating launcher script..."
cat > "$TARGET_BIN" << LAUNCHER
#!/bin/bash
exec /usr/bin/env python3 "$SERVER_SCRIPT" "\$@"
LAUNCHER
chmod +x "$TARGET_BIN"

# Install systemd user service
echo "[3/4] Installing systemd user service..."
SERVICE_FILE="$HOME/.config/systemd/user/phonedeck.service"
mkdir -p "$HOME/.config/systemd/user"

cat > "$SERVICE_FILE" << SERVICE
[Unit]
Description=PhoneDeck Companion Server
After=network.target
Wants=network-online.target

[Service]
ExecStart=$TARGET_BIN
Restart=always
RestartSec=3
StartLimitBurst=5
StartLimitIntervalSec=30

[Install]
WantedBy=default.target
SERVICE

# Enable lingering for user services (needed for services to start at boot)
loginctl enable-linger "$(whoami)" 2>/dev/null || true

# Reload and start
echo "[4/4] Starting service..."
systemctl --user daemon-reload
systemctl --user enable --now phonedeck.service

echo ""
echo "========================================="
echo "  ✅ PhoneDeck Server installed!"
echo "========================================="
echo ""
echo "  Status:  systemctl --user status phonedeck.service"
echo "  Logs:    journalctl --user -u phonedeck.service -f"
echo "  Restart: systemctl --user restart phonedeck.service"
echo "  Stop:    systemctl --user stop phonedeck.service"
echo ""
echo "  Open the PhoneDeck app on your phone and it will"
echo "  auto-discover this server over WiFi."
echo ""
echo "  To check what IP to connect to:"
echo "    ip addr show | grep 'inet '"
echo ""
echo "========================================="
