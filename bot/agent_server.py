"""
NetBot Agent Registration & Download Server
Handles agent self-registration and serves installer scripts
"""

import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path

from aiohttp import web

log = logging.getLogger("netbot.agentserver")

AGENTS_ROOT = Path(__file__).parent.parent / "agents"


def create_agent_server(agents: dict, snmp_devices: dict, config: dict) -> web.Application:
    """Create the aiohttp app for agent communication."""
    secret = config.get("server", {}).get("secret_key", "")

    app = web.Application()

    # ── Agent Registration ────────────────────────────────────────────────────

    async def register_agent(request: web.Request):
        try:
            data = await request.json()
        except Exception:
            raise web.HTTPBadRequest(text="Invalid JSON")

        hostname = data.get("hostname") or data.get("ip") or "unknown"
        agents[hostname] = {
            "hostname":  hostname,
            "ip":        data.get("ip"),
            "url":       data.get("url", f"http://{data.get('ip')}:7845"),
            "os":        data.get("os", "unknown"),
            "version":   data.get("version", "?"),
            "roles":     data.get("roles", []),
            "status":    "online",
            "last_seen": time.time(),
            "cpu":       data.get("cpu", 0),
            "memory":    data.get("memory", 0),
            "disk":      data.get("disk", 0),
            "uptime":    data.get("uptime", "?"),
        }
        log.info(f"Agent registered: {hostname} ({data.get('os')}) @ {data.get('ip')}")
        return web.json_response({"status": "registered", "hostname": hostname})

    # ── Agent Download ────────────────────────────────────────────────────────

    async def download_linux_agent(request: web.Request):
        agent_path = AGENTS_ROOT / "linux" / "agent.py"
        if agent_path.exists():
            return web.Response(text=agent_path.read_text(), content_type="text/plain")
        raise web.HTTPNotFound(text="Agent not found")

    async def download_windows_agent(request: web.Request):
        agent_path = AGENTS_ROOT / "windows" / "agent.ps1"
        if agent_path.exists():
            return web.Response(text=agent_path.read_text(), content_type="text/plain")
        raise web.HTTPNotFound(text="Agent not found")

    async def install_linux(request: web.Request):
        """Serve a one-liner install script with embedded server URL."""
        server_url = f"http://{request.host}"
        script = f"""#!/bin/bash
export NETBOT_SERVER="{server_url}"
curl -sSL {server_url}/agent/download/linux -o /tmp/netbot_agent.py
python3 /tmp/netbot_agent.py --install --server "$NETBOT_SERVER" --token "$NETBOT_TOKEN"
"""
        return web.Response(text=script, content_type="text/plain")

    async def install_windows(request: web.Request):
        server_url = f"http://{request.host}"
        script = f"""# NetBot Windows Agent Installer
$BotServer = "{server_url}"
$BotToken  = $env:NETBOT_TOKEN
Invoke-WebRequest -Uri "$BotServer/agent/download/windows" -OutFile C:\\NetBot\\agent.ps1
powershell -NonInteractive -File C:\\NetBot\\agent.ps1 -Install -BotServer $BotServer -Token $BotToken
"""
        return web.Response(text=script, content_type="text/plain")

    # ── Health ────────────────────────────────────────────────────────────────

    async def health(request: web.Request):
        return web.json_response({
            "status":  "ok",
            "agents":  len(agents),
            "snmp":    len(snmp_devices),
        })

    # ── Routes ────────────────────────────────────────────────────────────────

    app.router.add_post("/agent/register",           register_agent)
    app.router.add_get("/agent/download/linux",      download_linux_agent)
    app.router.add_get("/agent/download/windows",    download_windows_agent)
    app.router.add_get("/install/linux",             install_linux)
    app.router.add_get("/install/windows",           install_windows)
    app.router.add_get("/health",                    health)

    return app


async def start_agent_server(agents, snmp_devices, config):
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8080)
    app  = create_agent_server(agents, snmp_devices, config)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info(f"Agent server listening on {host}:{port}")
    return runner
