#!/bin/bash
# install-clip-png-daemon.sh
# Installs and enables the Windows -> WSL X11 clipboard image bridge

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/clip-png-daemon.service"
DAEMON_FILE="$SCRIPT_DIR/clip-png-daemon.py"

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing clip-png-daemon ==="

# Check files
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

if [ ! -f "$DAEMON_FILE" ]; then
    echo "Error: Daemon script not found at $DAEMON_FILE"
    exit 1
fi

# Make daemon executable
chmod +x "$DAEMON_FILE"

# Create systemd dir if needed
mkdir -p "$SYSTEMD_USER_DIR"

# Copy or symlink service file
ln -sf "$SERVICE_FILE" "$SYSTEMD_USER_DIR/clip-png-daemon.service"
echo "Symlinked service file to $SYSTEMD_USER_DIR/clip-png-daemon.service"

# Reload and enable
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

echo "Enabling and starting service..."
systemctl --user enable --now clip-png-daemon

echo ""
echo "=== Installation complete ==="
echo "Status:"
systemctl --user status clip-png-daemon | head -10
