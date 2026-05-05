# 🛡️ NetBot — Telegram Network Monitoring & Control Agent

A powerful, multi-platform Telegram bot that auto-discovers servers and network devices, builds a live dashboard, and lets you control Windows (AD, DNS, DHCP) and Linux servers — all from Telegram.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔍 Auto-Discovery | Scans your network and discovers all agents automatically |
| 🖥️ Windows Control | Manage Active Directory, DNS, DHCP roles remotely |
| 👤 User Management | Create, reset, disable AD users from Telegram |
| 🐧 Linux Control | Full server stats, services, processes, firewall |
| 📡 SNMP Polling | Discovers and polls routers, switches, printers |
| 📊 Live Dashboard | Web dashboard auto-built from discovered agents |
| 🔔 Alerts | CPU, disk, memory, service-down alerts to Telegram |
| 🔐 Secure | Token-based auth, admin whitelist, encrypted comms |

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

## 📦 Project Structure

```
netbot/
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
├── snmp/
│   ├── poller.py            # SNMP polling engine
│   └── mibs/                # Common MIB definitions
├── dashboard/
│   ├── app.py               # Flask web dashboard
│   ├── templates/
│   │   └── index.html       # Dashboard UI
│   └── static/              # CSS/JS assets
├── config/
│   ├── config.yaml          # Main configuration
│   └── snmp_community.yaml  # SNMP community strings
├── docker-compose.yml        # Full stack deployment
├── Dockerfile               # Bot container
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/netbot.git
cd netbot
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your bot token and admin IDs
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up -d
```

### 3. Deploy Agent on Windows Server

```powershell
# Run as Administrator
Invoke-WebRequest -Uri "http://YOUR_BOT_SERVER:8080/install/windows" -OutFile install.ps1
.\install.ps1 -BotToken "YOUR_TOKEN" -BotServer "http://YOUR_BOT_SERVER:8080"
```

### 4. Deploy Agent on Linux Server

```bash
curl -sSL http://YOUR_BOT_SERVER:8080/install/linux | \
  BOT_TOKEN=YOUR_TOKEN BOT_SERVER=http://YOUR_BOT_SERVER:8080 bash
```

---

## 💬 Bot Commands

### General
| Command | Description |
|---|---|
| `/start` | Show main menu |
| `/dashboard` | Get dashboard link |
| `/agents` | List all discovered agents |
| `/status` | Overall network health |

### Windows Commands
| Command | Description |
|---|---|
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
|---|---|
| `/lx <host> stats` | CPU, RAM, disk usage |
| `/lx <host> services` | Systemd service status |
| `/lx <host> ps` | Top processes |
| `/lx <host> netstat` | Network connections |
| `/lx <host> firewall` | UFW/firewalld rules |
| `/lx <host> logs <service>` | Tail service logs |
| `/lx <host> cmd <command>` | Run shell command (admin only) |

### SNMP Commands
| Command | Description |
|---|---|
| `/snmp scan` | Scan for SNMP devices |
| `/snmp <host>` | Poll device stats |
| `/snmp list` | List known SNMP devices |

---

## 🔐 Security Notes

- Only whitelisted Telegram user IDs can control the bot
- Agent communication uses HMAC-signed requests
- Sensitive commands (cmd, ad create) require admin role
- All actions are logged

---

## 📋 Requirements

- Python 3.11+
- Redis (for state/queue)
- Windows agents: PowerShell 5.1+, RSAT tools
- Linux agents: Python 3.8+
- SNMP: community strings configured on devices

---

## 📄 License

MIT — use freely, contribute back!
