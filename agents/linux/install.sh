#!/bin/bash
# NetBot Linux Agent Installer
# Usage: curl -sSL http://BOTSERVER:8080/install/linux | BOT_TOKEN=xxx BOT_SERVER=http://xxx bash

set -e

NETBOT_SERVER="${BOT_SERVER:-$NETBOT_SERVER}"
NETBOT_TOKEN="${BOT_TOKEN:-$NETBOT_TOKEN}"
AGENT_URL="${NETBOT_SERVER}/agent/download/linux"
INSTALL_DIR="/opt/netbot"
AGENT_PY="$INSTALL_DIR/agent.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     NetBot Linux Agent Installer     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Root check
[ "$(id -u)" -eq 0 ] || error "Run as root (sudo bash install.sh)"

[ -n "$NETBOT_SERVER" ] || error "BOT_SERVER not set"
[ -n "$NETBOT_TOKEN"  ] || error "BOT_TOKEN not set"

# Install Python + psutil
info "Installing dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq && apt-get install -y -qq python3 python3-pip
    pip3 install psutil --quiet
elif command -v yum &>/dev/null; then
    yum install -y -q python3 python3-pip
    pip3 install psutil --quiet
elif command -v dnf &>/dev/null; then
    dnf install -y -q python3 python3-pip
    pip3 install psutil --quiet
else
    warn "Package manager not recognized. Make sure python3 and psutil are installed."
fi

# Create install dir
mkdir -p "$INSTALL_DIR"

# Download agent
info "Downloading agent..."
if command -v curl &>/dev/null; then
    curl -sSL "$AGENT_URL" -o "$AGENT_PY" || {
        warn "Could not download from server. Using bundled agent."
        # Agent will be embedded here in production, fallback to local copy
    }
else
    wget -q "$AGENT_URL" -O "$AGENT_PY" || warn "wget failed"
fi

# If still no agent.py, copy the one next to this script
if [ ! -f "$AGENT_PY" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cp "$SCRIPT_DIR/agent.py" "$AGENT_PY"
fi

chmod +x "$AGENT_PY"

# Create config
info "Writing config..."
mkdir -p /etc/netbot
cat > /etc/netbot/agent.json << EOF
{
  "server": "$NETBOT_SERVER",
  "token":  "$NETBOT_TOKEN"
}
EOF
chmod 600 /etc/netbot/agent.json

# Create systemd service
info "Creating systemd service..."
cat > /etc/systemd/system/netbot-agent.service << EOF
[Unit]
Description=NetBot Linux Agent
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/usr/bin/python3 $AGENT_PY
Restart=always
RestartSec=10
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable netbot-agent
systemctl restart netbot-agent

sleep 2
if systemctl is-active --quiet netbot-agent; then
    info "✅ NetBot Agent is running!"
    echo ""
    echo "  Hostname: $(hostname)"
    echo "  Server:   $NETBOT_SERVER"
    echo "  Logs:     journalctl -u netbot-agent -f"
    echo ""
else
    error "Agent failed to start. Check: journalctl -u netbot-agent -n 20"
fi
