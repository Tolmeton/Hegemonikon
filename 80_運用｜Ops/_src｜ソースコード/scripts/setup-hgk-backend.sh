#!/bin/bash
# =============================================================================
# HGK Backend Setup Script
# Run this on hgk-backend (e2-small) via GCP Console SSH
# =============================================================================
set -euo pipefail

echo "=== HGK Backend Setup Starting ==="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Memory: $(free -m | awk '/Mem:/{print $2}') MB total"

# 1. System packages
echo ""
echo ">>> [1/5] System packages..."
sudo apt-get update -y
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  git curl nginx \
  docker.io docker-compose-plugin

# 2. Docker setup
echo ""
echo ">>> [2/5] Docker..."
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

# 3. Tailscale
echo ""
echo ">>> [3/5] Tailscale..."
if ! command -v tailscale &>/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sudo sh
fi
echo "⚠️  Run: sudo tailscale up"
echo "   After authenticating, run: tailscale ip -4"

# 4. Clone repo + venv
echo ""
echo ">>> [4/5] Repository + Python venv..."
mkdir -p ~/oikos
if [ ! -d ~/oikos/01_ヘゲモニコン｜Hegemonikon ]; then
  echo "⚠️  Need to clone hegemonikon repo."
  echo "   Run: cd ~/oikos && git clone <REPO_URL> hegemonikon"
else
  echo "hegemonikon already exists"
fi

# Note: venv will be set up after repo is cloned
# cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && python3 -m venv .venv
# source .venv/bin/activate && pip install -r requirements.txt

# 5. Systemd services (placeholder)
echo ""
echo ">>> [5/5] Systemd placeholder..."
cat <<'EOF'
Next steps after Tailscale auth + repo clone:
  1. cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && python3 -m venv .venv
  2. source .venv/bin/activate && pip install -r requirements.txt
  3. sudo cp mekhane/mcp/hgk-gateway.service /etc/systemd/system/
  4. sudo systemctl daemon-reload && sudo systemctl enable hgk-gateway
  5. Copy docker-compose.yml and start containers
  6. Configure Tailscale Funnel: tailscale funnel 8765
EOF

echo ""
echo "=== Setup Phase 1 Complete ==="
echo "Date: $(date)"
