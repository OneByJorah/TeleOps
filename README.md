<div align="center">

![TeleOps banner](docs/assets/banner.svg)

# TeleOps

**Unified NOC platform for Telegram — monitor agents, discover SNMP devices, run a live dashboard, and manage Linux and Windows hosts from chat commands**

[![GitHub release](https://img.shields.io/github/v/release/OneByJorah/TeleOps?color=3776AB&label=release&logo=github)](https://github.com/OneByJorah/TeleOps/releases)
[![PyPI version](https://img.shields.io/pypi/v/teleops?color=3776AB&label=pip&logo=pypi)](https://pypi.org/project/teleops/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Flask-SocketIO](https://img.shields.io/badge/Flask-SocketIO-000000?style=flat-square&logo=flask&logoColor=white)](https://flask-socketio.readthedocs.io/)
[![Telegram](https://img.shields.io/badge/Telegram-0088CC?style=flat-square&logo=telegram&logoColor=white)](https://telegram.org/)
[![SNMP](https://img.shields.io/badge/SNMP-v1/v2c/v3-000000?style=flat-square&logo=netflix&logoColor=white)](https://en.wikipedia.org/wiki/Simple_Network_Management_Protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?color=FFB300&logo=open-source-initiative&logoColor=FFB300)](https://opensource.org/licenses/MIT)

</div>

![TeleOps dashboard](docs/assets/screenshot.png)

## What This Is

TeleOps turns Telegram into a network operations console. A bot fronts a set of cross-platform agents, an SNMP discovery engine, and a live web dashboard, so you can check host health, run signed commands, and get threshold alerts without opening a terminal or a monitoring portal.

Built for small NOC and homelab operators who want lightweight, self-hosted infrastructure monitoring that reaches them where they already are — chat.

## Quick Start

### pip

```bash
pip install teleops
```

### Docker (recommended)

```bash
git clone https://github.com/OneByJorah/TeleOps.git
cd TeleOps
cp .env.example .env        # set TELEGRAM_BOT_TOKEN and ADMIN_CHAT_IDS
docker compose up -d
```

Open **http://localhost:5000** for the dashboard. The agent server listens on **http://localhost:8080**.

### From Source

```bash
git clone https://github.com/OneByJorah/TeleOps.git
cd TeleOps
pip install -r requirements.txt
cp .env.example .env
python3 bot.py
```

## Install

### pip

```bash
pip install teleops
```

### Docker

```bash
git clone https://github.com/OneByJorah/TeleOps.git
cd TeleOps
cp .env.example .env
docker compose up -d
```

### From Source

```bash
git clone https://github.com/OneByJorah/TeleOps.git
cd TeleOps
pip install -r requirements.txt
cp .env.example .env
python3 bot.py
```

## Features

- **Telegram control plane** — admin-gated commands for status, agents, SNMP, and per-host actions
- **Cross-platform agents** — stdlib Linux agent and PowerShell 5.1 Windows agent with HMAC-SHA256 signed command dispatch
- **SNMP discovery** — automated device discovery and polling over SNMP v1/v2c/v3
- **Live dashboard** — Flask + SocketIO API with REST polling fallback
- **Alert management** — CPU/memory/disk thresholds, configurable alert routing
- **Self-hosted** — no external dependencies, no cloud required
- **Docker support** — run with `docker compose up -d`

## Tech Stack

- **Backend** — Python 3.10+, Flask, Flask-SocketIO, Eventlet
- **Telegram** — python-telegram-bot 20+
- **SNMP** — pysnmp 4.4+
- **Agents** — stdlib (Linux), PowerShell 5.1 (Windows), HMAC-SHA256 signed commands
- **Deployment** — Docker Compose, pip install
- **Config** — YAML (`config/config.yaml`), environment variables (`.env`)

## Package Badges

[![GitHub release](https://img.shields.io/github/v/release/OneByJorah/TeleOps?color=3776AB&label=release&logo=github)](https://github.com/OneByJorah/TeleOps/releases)
[![PyPI version](https://img.shields.io/pypi/v/teleops?color=3776AB&label=pip&logo=pypi)](https://pypi.org/project/teleops/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?color=FFB300&logo=open-source-initiative&logoColor=FFB300)](https://opensource.org/licenses/MIT)

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (required) |
| `ADMIN_CHAT_IDS` | Comma-separated admin chat IDs (required) |
| `FLASK_PORT` | Dashboard port (default: 5000) |
| `AGENT_PORT` | Agent server port (default: 8080) |

The `bot` service seeds `config/config.yaml` from `.env` on first run.

## Architecture

```
Telegram Bot ──▶ Bot Service (bot.py)
                       │
                       ├──▶ Agent Server (agents/server.py) ──▶ Linux/Windows Agents
                       │
                       ├──▶ SNMP Discovery (snmp/discover.py)
                       │
                       └──▶ Dashboard (dashboard/app.py) ──▶ Flask + SocketIO
```

## Contributing

Contributions are welcome. [Open an issue](https://github.com/OneByJorah/TeleOps/issues) to report a bug or request a feature.

## License

MIT — see [LICENSE](LICENSE).
