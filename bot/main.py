#!/usr/bin/env python3
"""
NetBot - Telegram Network Monitoring & Control Agent
Main entry point
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

import yaml
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.handlers import (
    start_handler, status_handler, agents_handler,
    windows_handler, linux_handler, snmp_handler,
    dashboard_handler, alert_handler, callback_handler
)
from bot.scheduler import setup_scheduler
from discovery.network_scanner import NetworkScanner
from discovery.snmp_scanner import SNMPScanner

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/netbot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("netbot.main")

# ── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        log.error("config/config.yaml not found. Copy config.yaml.example and fill in values.")
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)

# ── Main ─────────────────────────────────────────────────────────────────────

async def post_init(application):
    """Called after bot starts — boot background tasks."""
    cfg = application.bot_data["config"]
    log.info("🚀 NetBot starting up...")

    # Start network scanner
    scanner = NetworkScanner(cfg)
    application.bot_data["scanner"] = scanner
    asyncio.create_task(scanner.start_background_scan())

    # Start SNMP scanner
    snmp = SNMPScanner(cfg)
    application.bot_data["snmp"] = snmp
    asyncio.create_task(snmp.start_background_poll())

    log.info("✅ NetBot ready. All systems go.")


def main():
    os.makedirs("logs", exist_ok=True)
    cfg = load_config()

    token = cfg["bot"]["token"]
    if token == "YOUR_TELEGRAM_BOT_TOKEN":
        log.error("Please set your bot token in config/config.yaml")
        sys.exit(1)

    # Build application
    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )
    app.bot_data["config"] = cfg
    app.bot_data["agents"] = {}      # hostname -> agent info
    app.bot_data["snmp_devices"] = {}  # ip -> device info

    # ── Command Handlers ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",     start_handler))
    app.add_handler(CommandHandler("status",    status_handler))
    app.add_handler(CommandHandler("agents",    agents_handler))
    app.add_handler(CommandHandler("dashboard", dashboard_handler))
    app.add_handler(CommandHandler("win",       windows_handler))
    app.add_handler(CommandHandler("lx",        linux_handler))
    app.add_handler(CommandHandler("snmp",      snmp_handler))
    app.add_handler(CommandHandler("alert",     alert_handler))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Setup scheduled jobs (heartbeat checks, alerts)
    setup_scheduler(app)

    log.info(f"Bot polling started. Admins: {cfg['bot']['admin_ids']}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
