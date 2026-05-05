"""
NetBot Web Dashboard
Real-time view of all agents and SNMP devices
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "netbot-dashboard-secret")
socketio = SocketIO(app, cors_allowed_origins="*")

# Shared state injected from main bot
_agents       = {}
_snmp_devices = {}
_config       = {}


def init_dashboard(agents: dict, snmp_devices: dict, config: dict):
    global _agents, _snmp_devices, _config
    _agents       = agents
    _snmp_devices = snmp_devices
    _config       = config


@app.route("/")
def index():
    return render_template("index.html", title=_config.get("dashboard", {}).get("title", "NetBot"))


@app.route("/api/agents")
def api_agents():
    return jsonify(list(_agents.values()))


@app.route("/api/snmp")
def api_snmp():
    return jsonify(list(_snmp_devices.values()))


@app.route("/api/summary")
def api_summary():
    agents = list(_agents.values())
    return jsonify({
        "total_agents":   len(agents),
        "online_agents":  sum(1 for a in agents if a.get("status") == "online"),
        "windows_agents": sum(1 for a in agents if a.get("os") == "windows"),
        "linux_agents":   sum(1 for a in agents if a.get("os") == "linux"),
        "snmp_devices":   len(_snmp_devices),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
    })


@socketio.on("connect")
def handle_connect():
    emit("agents_update", {"agents": list(_agents.values())})
    emit("snmp_update",   {"devices": list(_snmp_devices.values())})


def push_updates():
    """Background thread pushing updates to WebSocket clients."""
    while True:
        time.sleep(10)
        socketio.emit("agents_update", {"agents": list(_agents.values())})
        socketio.emit("snmp_update",   {"devices": list(_snmp_devices.values())})


def start_dashboard(agents, snmp_devices, config):
    init_dashboard(agents, snmp_devices, config)
    import threading
    t = threading.Thread(target=push_updates, daemon=True)
    t.start()
    host = config.get("dashboard", {}).get("host", "0.0.0.0")
    port = config.get("dashboard", {}).get("port", 5000)
    socketio.run(app, host=host, port=port, use_reloader=False)


if __name__ == "__main__":
    # Standalone mode for testing
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
