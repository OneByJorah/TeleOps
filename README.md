<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Flask-000?style=for-the-badge&logo=flask&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white">
</div>

<br>

<div align="center">
  <h1>📡 J1 NOC Nexus</h1>
  <p><strong>Unified Network Operations Center Platform</strong></p>
  <p>Telegram bot, SNMP discovery, live dashboard, and cross-platform agents for infrastructure management</p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-components">Components</a>
  </p>
</div>

---

## 📸 Screenshot

This is a CLI/backend-only tool. No screenshots available.

## ✨ Features

- **Telegram Bot** — Command execution, notifications, scheduling via Telegram
- **Flask Dashboard** — Real-time observability dashboard
- **SNMP Discovery** — Automated network scanning and discovery
- **Cross-Platform Agents** — Linux and Windows bootstrap scripts
- **FastAPI Backend** — Modern async API layer
- **Unified Monitoring** — Centralized view of infrastructure events

## 🚀 Quick Start

```bash
git clone https://github.com/OneByJorah/J1-NOC-Nexus.git
cd J1-NOC-Nexus
pip install -r requirements.txt
# Configure your .env file with Telegram bot token
python3 handlers.py
```

Or with Docker:
```bash
docker-compose up -d
```

## 🏗️ Architecture

```
J1-NOC-Nexus/
├── agents/                    # Platform-specific agents
│   ├── agent.ps1              # Windows agent
│   └── install.sh             # Linux agent bootstrap
├── bot/                       # Telegram bot logic
├── config/                    # Configuration files
├── dashboard/                 # Flask dashboard
├── discovery/                 # SNMP & network discovery
├── tests/                     # Test suite
├── docs/                      # Documentation
├── handlers.py                # Bot command handlers
├── snmp_scanner.py            # SNMP scanning module
├── index.html                 # Dashboard frontend
├── docker-compose.yml         # Docker deployment
└── requirements.txt
```

## 🔧 Components

| Component | Technology | Description |
|-----------|------------|-------------|
| Dashboard | Flask/HTML5 | Real-time monitoring UI |
| Bot | python-telegram-bot | Telegram command interface |
| Backend | FastAPI | Async API layer |
| Discovery | Python/SNMP | Network scanning |
| Agents | PowerShell/Bash | Cross-platform deployment |

## 📄 License

MIT © Jhonattan L. Jimenez

---

<div align="center">
  <p>🌐 Your NOC, unified</p>
  <p><a href="https://github.com/OneByJorah">@OneByJorah</a></p>
</div>
