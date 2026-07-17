#!/bin/bash
# PhoneDeck one-time systemd installation script

set -e

echo "Installing PhoneDeck Server as a systemd service..."

# Ensure we have the required dependencies
if ! command -v python3 &> /dev/null; then
    echo "python3 could not be found. Please install it first."
    exit 1
fi

pip3 install websockets zeroconf --break-system-packages || pip3 install websockets zeroconf

# Define service file path
SERVICE_FILE="$HOME/.config/systemd/user/phonedeck.service"
mkdir -p "$HOME/.config/systemd/user"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=PhoneDeck Companion Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/env python3 $(pwd)/companion/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now phonedeck.service

echo "========================================="
echo "PhoneDeck Server has been installed and started as a background service!"
echo "It will automatically start on login."
echo "You can check the status with: systemctl --user status phonedeck.service"
echo "========================================="
