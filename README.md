<!-- j1-brand:v2 -->
<div align="center">

# J1-NOC-Nexus

A powerful, multi-platform Telegram bot that auto-discovers servers and network devices, builds a live dashboard, and lets you control Windows (AD, DNS, DHCP) and Linux servers — all from Telegram.

[![GitHub](https://img.shields.io/badge/github-OneByJorah%2FJ1--NOC--Nexus-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah/J1-NOC-Nexus)
[![License](https://img.shields.io/badge/license-MIT-FFB300?style=for-the-badge&labelColor=0d0d0c)](LICENSE)
[![Language](https://img.shields.io/badge/Python-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://python.org)
[![Built by](https://img.shields.io/badge/built%20by-JorahOne%20LLC-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah)

</div>

---

## Why This Exists

NOC dashboards are great for a big screen in the office, but when you're away from your desk you need the same visibility in your pocket. J1-NOC-Nexus bridges both worlds: a Telegram bot for on-the-go commands and alerts, plus a Flask dashboard for the full view — with SNMP auto-discovery so you don't have to punch in every device by hand.

## Key Features

| Feature | Why It Matters |
|---|---|
| Telegram bot control | Run commands, check status, get alerts — all from your phone |
| SNMP auto-discovery | Finds devices on your network without manual entry |
| Flask dashboard | Real-time web UI for the full NOC picture |
| Cross-platform agents | Bootstrap scripts for both Linux and Windows targets |
| AD, DNS, DHCP management | Windows domain operations from the same interface |
| FastAPI backend | Async API layer for integrations and extensibility |

## Quick Start

```bash
git clone https://github.com/OneByJorah/J1-NOC-Nexus.git
cd J1-NOC-Nexus

# Native
pip install -r requirements.txt
cp .env.example .env   # configure Telegram bot token, etc.
python3 handlers.py

# Docker
docker compose up -d
```

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Telegram     │◀───▶│  Bot Engine   │────▶│  FastAPI      │
│  (user)       │     │  handlers.py  │     │  API Layer    │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │  SNMP     │  │  Flask   │  │  Agents  │
       │  Scanner  │  │Dashboard │  │  Win/Lin  │
       └──────────┘  └──────────┘  └──────────┘
```

## Documentation

| Doc | Description |
|---|---|
| [Bot Commands](docs/bot.md) | Full Telegram command reference |
| [Agent Setup](docs/agents.md) | Installing the Windows and Linux agents |
| [Dashboard Guide](docs/dashboard.md) | Using the Flask web dashboard |

---

## License

MIT © JorahOne, LLC — see [LICENSE](LICENSE)

<sub>Part of the JorahOne infrastructure ecosystem.</sub>
