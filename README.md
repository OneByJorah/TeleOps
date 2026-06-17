# 🛡️ J1-NOC-Nexus — Telegram Network Monitoring & Control Agent

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)](https://core.telegram.org/bots)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Maintained by OneByJorah](https://img.shields.io/badge/Maintained%20by-OneByJorah-1E90FF?logo=github)](https://github.com/OneByJorah)

---

## 📋 Overview

**J1-NOC-Nexus** is a powerful, multi-platform Telegram bot that auto-discovers servers and network devices, builds a live dashboard, and lets you control Windows (AD, DNS, DHCP) and Linux servers — all from Telegram. Designed for MSPs and network engineers who want full infrastructure control from their pocket.

> **Built with ❤️ by [OneByJorah](https://github.com/OneByJorah)**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Auto-Discovery** | Scans your network and discovers all agents automatically |
| 🖥️ **Windows Control** | Manage Active Directory, DNS, DHCP roles remotely |
| 👤 **User Management** | Create, reset, disable AD users from Telegram |
| 🐧 **Linux Control** | Full server stats, services, processes, firewall |
| 📡 **SNMP Polling** | Discovers and polls routers, switches, printers |
| 📊 **Live Dashboard** | Web dashboard auto-built from discovered agents |
| 🔔 **Alerts** | CPU, disk, memory, service-down alerts to Telegram |
| 🔐 **Secure** | Token-based auth, admin whitelist, encrypted comms |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  Telegram Bot                    │
│              (Central Controller)                │
└───────────────┬─────────────────┬───────────────┘
                │                 │
    ┌───────────▼──┐         ┌────▼──────────┐
    │  Windows     │         │  Linux        │
    │  Agent       │         │  Agent        │
    │  (agent.ps1) │         │  (agent.py)   │
    └───────────┬──┘         └────┬──────────┘
                │                 │
    ┌───────────▼─────────────────▼──────────┐
    │           SNMP Scanner                  │
    │      (routers, switches, APs)           │
    └─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
J1-NOC-Nexus/
├── bot/
│   ├── main.py              # Bot entry point
│   ├── handlers.py          # Telegram command handlers
│   ├── keyboards.py         # Inline keyboards/menus
│   └── scheduler.py         # Background polling scheduler
├── agents/
│   ├── windows/
│   │   ├── agent.ps1        # PowerShell agent for Windows Server
│   │   └── install.ps1      # Windows agent installer
│   └── linux/
│       ├── agent.py         # Python agent for Linux
│       └── install.sh       # Linux agent installer
├── discovery/
│   ├── network_scanner.py   # Auto-discovery via ping/ARP/mDNS
│   └── snmp_scanner.py      # SNMP device discovery
├── snmp_scanner.py          # SNMP polling engine
├── dashboard/
│   ├── app.py (index.html)  # Flask web dashboard
│   └── index.html           # Dashboard UI
├── config/                  # Configuration files
├── handlers.py              # Shared handlers
├── docker-compose.yml        # Full stack deployment
├── Dockerfile               # Bot container
├── requirements.txt         # Python dependencies
├── install.sh               # Linux installer
├── install.ps1              # Windows installer
├── ci.yml                   # CI pipeline
└── tests/                   # Test suite
```

---

## 📋 Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.11 or higher |
| **Redis** | For state management and task queue |
| **Windows Agents** | PowerShell 5.1+, RSAT tools |
| **Linux Agents** | Python 3.8+ |
| **SNMP** | Community strings configured on devices |
| **Telegram** | Bot token from [@BotFather](https://t.me/BotFather) |

---

## ⚡ Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/OneByJorah/J1-NOC-Nexus.git
cd J1-NOC-Nexus
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your bot token and admin IDs
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up -d
```

### 3. Run Locally

```bash
pip install -r requirements.txt
python bot/main.py
```

### 4. Deploy Agent on Windows Server

```powershell
# Run as Administrator
Invoke-WebRequest -Uri "http://YOUR_BOT_SERVER:8080/install/windows" -OutFile install.ps1
.\install.ps1 -BotToken "YOUR_TOKEN" -BotServer "http://YOUR_BOT_SERVER:8080"
```

### 5. Deploy Agent on Linux Server

```bash
curl -sSL http://YOUR_BOT_SERVER:8080/install/linux | \
  BOT_TOKEN=YOUR_TOKEN BOT_SERVER=http://YOUR_BOT_SERVER:8080 bash
```

---

## 💬 Bot Commands

### General

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/dashboard` | Get dashboard link |
| `/agents` | List all discovered agents |
| `/status` | Overall network health |

### Windows Commands

| Command | Description |
|---------|-------------|
| `/win <host> dns` | Show DNS zones and records |
| `/win <host> dhcp` | Show DHCP scopes and leases |
| `/win <host> ad users` | List AD users |
| `/win <host> ad create <user>` | Create AD user |
| `/win <host> ad reset <user>` | Reset AD user password |
| `/win <host> ad disable <user>` | Disable AD user |
| `/win <host> services` | List Windows services |
| `/win <host> eventlog` | Show recent critical events |

### Linux Commands

| Command | Description |
|---------|-------------|
| `/lx <host> stats` | CPU, RAM, disk usage |
| `/lx <host> services` | Systemd service status |
| `/lx <host> ps` | Top processes |
| `/lx <host> netstat` | Network connections |
| `/lx <host> firewall` | UFW/firewalld rules |
| `/lx <host> logs <service>` | Tail service logs |
| `/lx <host> cmd <command>` | Run shell command (admin only) |

### SNMP Commands

| Command | Description |
|---------|-------------|
| `/snmp scan` | Scan for SNMP devices |
| `/snmp <host>` | Poll device stats |
| `/snmp list` | List known SNMP devices |

---

## 🔐 Security

- Only whitelisted Telegram user IDs can control the bot
- Agent communication uses HMAC-signed requests
- Sensitive commands (`cmd`, `ad create`) require admin role
- All actions are logged and auditable
- No credentials stored in plain text

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Update to latest
docker compose pull && docker compose up -d
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot not responding | Verify token in config.yaml |
| Agents not discovered | Check network connectivity and firewall rules |
| Docker build fails | Ensure Dockerfile and .dockerignore are correct |
| SNMP timeout | Verify community strings and device accessibility |

---

## 🔄 Updates

```bash
cd /path/to/J1-NOC-Nexus
git pull origin main
docker compose up -d --build
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT — use freely, contribute back!

---

## 📞 Support

For issues or questions, please open an issue on GitHub:

https://github.com/OneByJorah/J1-NOC-Nexus/issues

---

**Made with ❤️ by [OneByJorah](https://github.com/OneByJorah)**
