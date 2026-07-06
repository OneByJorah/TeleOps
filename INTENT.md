# INTENT.md — J1-NOC-Nexus (ORACLE Phase)

> **Phase**: -1 (ORACLE) — Read-only intent reconstruction  
> **Date**: 2026-07-05  
> **Analyst**: J1-PIPELINE  
> **Status**: Complete

---

## What This System Does

**J1-NOC-Nexus** (codename "NetBot") is a **unified Network Operations Center (NOC) platform** that combines a Telegram bot, cross-platform infrastructure agents, SNMP discovery, and a live web dashboard into a single deployable system. It is the operational nerve center for the JorahOne infrastructure estate.

### Technical Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Telegram Bot                         │
│              (Central Controller)                     │
│  python-telegram-bot · FastAPI · aiohttp              │
└───────────────┬──────────────────┬──────────────────┐
                │                  │                  │
    ┌───────────▼──┐    ┌─────────▼──────┐   ┌───────▼──────┐
    │  Windows     │    │  Linux         │   │  SNMP        │
    │  Agent       │    │  Agent         │   │  Scanner     │
    │  (agent.ps1) │    │  (agent.py)    │   │  (pysnmp)    │
    │  PS 5.1+     │    │  Python 3.8+   │   │  v1/v2c/v3   │
    └───────┬──────┘    └───────┬────────┘   └───────┬──────┘
            │                   │                    │
            └───────────────────┴────────────────────┘
                         │
                    ┌────▼────┐
                    │  Redis  │  ← State / Job Queue
                    └─────────┘
                         │
                    ┌────▼──────────┐
                    │  Flask + WS   │  ← Live Dashboard
                    │  Dashboard    │     (SocketIO)
                    └───────────────┘
```

### Core Components

| Component | Technology | Role |
|-----------|-----------|------|
| **Telegram Bot** | `python-telegram-bot` 20.7 | Command interface, alert delivery, inline menus |
| **Agent Server** | `aiohttp` (FastAPI-style) | Agent registration, script download, HMAC auth |
| **Windows Agent** | PowerShell 5.1+ | AD/DNS/DHCP management, metrics, command execution |
| **Linux Agent** | Python 3.8+ (psutil) | System stats, services, firewall, logs, arbitrary commands |
| **Network Scanner** | Python (aiohttp) | Auto-discovers agents on port 7845 across subnets |
| **SNMP Scanner** | Python (pysnmp) | Discovers/polls routers, switches, printers via SNMP |
| **Web Dashboard** | Flask + SocketIO | Real-time agent/SNMP metrics via WebSocket push |
| **State Layer** | Redis 7 (alpine) | Job queue, agent state, SNMP device cache |

### Operational Capabilities

- **Zero-config agent discovery**: Scans configured subnets for agents listening on port 7845; agents self-register via HTTP POST
- **Windows Server management**: Active Directory user CRUD, DNS zone/record management, DHCP scope/lease inspection, service control, event log tailing
- **Linux management**: CPU/RAM/disk stats, systemd service control, process listing, netstat, firewall rules, journalctl logs, SSH key inspection, arbitrary shell commands
- **SNMP device polling**: v1/v2c/v3 support, sysName/sysDescr/uptime, interface counters, CPU load, memory utilization
- **Threshold-based alerting**: CPU >90%, memory >85%, disk >90%, service-down detection with configurable cooldown
- **Live dashboard**: Real-time WebSocket-pushed agent cards with CPU/MEM/DISK gauges, SNMP device list, summary stats
- **Cross-platform deployment**: One-liner install scripts for both Windows (PowerShell) and Linux (bash/systemd)
- **HMAC-secured agent communication**: All agent commands signed with SHA-256 HMAC using shared secret

---

## Why This Was Built

### The Real Problem

JorahOne LLC operates a heterogeneous infrastructure estate spanning Windows Server (Active Directory, DNS, DHCP) and Linux servers, alongside traditional SNMP-managed network gear (routers, switches, firewalls). The operational reality before NetBot was fragmented:

1. **Windows AD/DNS/DHCP management** required RDP or dedicated RSAT workstations — no mobile access, no unified interface
2. **Linux server monitoring** used separate SSH sessions, Nagios/Icinga checks, or ad-hoc scripts
3. **SNMP device polling** required a separate NMS tool (PRTG, SolarWinds, Cacti)
4. **Alerting** was split across multiple channels (email, Slack, SMS) with no single source of truth
5. **Agent deployment** was manual — no auto-discovery, no self-registration

Existing tools were insufficient because:
- **Enterprise NMS platforms** (SolarWinds, PRTG, Nagios XI) are expensive, complex to configure, and require dedicated monitoring infrastructure
- **Cloud monitoring** (Datadog, New Relic) doesn't cover on-prem network gear via SNMP or Windows AD management
- **Individual point tools** (RSAT for AD, SSH for Linux, SNMP walkers) create operational silos and require context switching
- **No existing tool** combined Telegram-based mobile control with cross-platform agent deployment and SNMP in a single open-source package

### What Triggered Development

The JorahOne NOC team needed a **single pane of glass** that could be operated from a mobile device (Telegram) without VPN, without a dedicated monitoring workstation, and without licensing costs. The trigger was the operational overhead of managing a growing hybrid infrastructure with separate tools for Windows, Linux, and network gear — particularly the inability to respond to AD lockouts, DNS issues, or server alerts from outside the office.

### How It Fits the JorahOne Ecosystem

J1-NOC-Nexus is the **observability and operations layer** of the JorahOne stack. It complements:

- **J1-DevOps** (CI/CD pipeline tooling) by providing the runtime monitoring for deployed infrastructure
- **J1-Security** (security tooling) by providing alerting and audit trail for infrastructure events
- **J1-Infra** (infrastructure provisioning) by providing the operational management layer for provisioned servers
- **J1-Automation** (automation framework) by providing the agent-based remote execution substrate

It is designed as a **self-hosted, zero-license-cost** alternative to commercial NMS platforms, optimized for the specific Windows+Linux+SNMP hybrid that characterizes SMB and mid-market IT environments.

---

## Operational Classification

| Dimension | Classification |
|-----------|---------------|
| **Type** | **Production** — designed for 24/7 infrastructure monitoring and management |
| **Domain** | **Observability** + **Automation** — real-time metrics, alerting, and remote control |
| **Maturity** | v1.0.0 — initial release, functional but early-stage |
| **Deployment** | Docker Compose (bot + Redis) + per-server agent install |
| **Security Posture** | Admin whitelist, HMAC-signed agent communication, configurable thresholds |
| **License** | MIT — open source, permissive |

---

## Key Design Decisions

1. **Telegram as primary interface** — Chosen over Slack/Discord/Web UI because Telegram bots require no infrastructure (no webhook setup), work on mobile without VPN, and support rich inline keyboards
2. **Agent self-registration** — Agents register themselves via HTTP POST rather than requiring a central inventory, enabling zero-config auto-discovery
3. **HMAC over TLS** — Agent commands are HMAC-signed rather than requiring mutual TLS, simplifying deployment on networks without PKI
4. **Redis for state** — Chosen over SQLite/Postgres for the job queue pattern; agents are ephemeral state that doesn't need ACID guarantees
5. **Dual dashboard** — Both Telegram (mobile) and Web (desktop) dashboards, with the web dashboard using SocketIO for real-time push rather than polling
6. **psutil-based Linux agent** — Single-file Python agent with no framework dependencies, deployable via curl pipe to bash

---

## Repository Structure

```
J1-NOC-Nexus/
├── bot/                    # Telegram bot + agent server
│   ├── main.py             # Bot entry point, command registration
│   ├── handlers.py         # All Telegram command handlers
│   ├── keyboards.py        # Inline keyboard builders
│   ├── agent_server.py     # Agent registration + download HTTP server
│   └── scheduler.py        # Background heartbeat/alert/metrics jobs
├── agents/                 # Cross-platform agent code
│   ├── linux/
│   │   ├── agent.py        # Linux agent (Python, systemd service)
│   │   └── install.sh      # Linux one-liner installer
│   └── windows/
│       ├── agent.ps1       # Windows agent (PowerShell, scheduled task)
│       └── install.ps1     # Windows installer script
├── discovery/              # Network discovery engines
│   ├── network_scanner.py # Agent auto-discovery via HTTP probe
│   └── snmp_scanner.py    # SNMP device discovery + polling
├── dashboard/              # Web dashboard
│   ├── app.py             # Flask + SocketIO server
│   └── templates/
│       └── index.html     # Dark-theme real-time dashboard UI
├── config/
│   └── config.yaml.example # Full configuration template
├── tests/
│   └── test_basic.py      # HMAC signature + import tests
├── .github/                # CI/CD
│   ├── workflows/codeql.yml
│   ├── dependabot.yml
│   └── ISSUE_TEMPLATE/
├── docker-compose.yml      # Bot + Redis stack
├── Dockerfile              # Bot container (python:3.11-slim + nmap/snmp)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── SECURITY.md             # Security policy
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Code of conduct
├── ROADMAP.md              # Development roadmap
├── CHANGELOG.md            # Release history
└── LICENSE                 # MIT license
```
