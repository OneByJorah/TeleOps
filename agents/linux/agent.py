#!/usr/bin/env python3
"""
NetBot Linux Agent
Runs as a systemd service, reports metrics, accepts commands.
Install: sudo python3 agent.py --install --server http://BOTSERVER:8080 --token TOKEN
"""

import argparse
import asyncio
import hashlib
import hmac
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import urllib.request

AGENT_VERSION = "1.0.0"
AGENT_PORT    = 7845
CONFIG_PATH   = "/etc/netbot/agent.json"
LOG_PATH      = "/var/log/netbot-agent.log"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH) if os.path.exists("/var/log") else logging.StreamHandler(),
    ]
)
log = logging.getLogger("netbot.agent")

# ── System Detection ──────────────────────────────────────────────────────────

def detect_roles() -> list:
    roles = []
    checks = {
        "nginx":      ("nginx",   ["nginx", "-v"]),
        "apache":     ("apache2", ["apache2", "-v"]),
        "mysql":      ("mysql",   ["mysql", "--version"]),
        "postgresql": ("postgres",["pg_isready"]),
        "docker":     ("docker",  ["docker", "--version"]),
        "k8s":        ("kubectl", ["kubectl", "version", "--client"]),
        "bind9":      ("bind9",   ["named", "-v"]),
        "dhcpd":      ("dhcp",    ["dhcpd", "--version"]),
        "samba":      ("samba",   ["samba", "--version"]),
        "redis":      ("redis",   ["redis-cli", "--version"]),
    }
    for role, (name, cmd) in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=3)
            if result.returncode == 0 or result.returncode == 1:
                roles.append(name)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return roles


def get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# ── Metrics ───────────────────────────────────────────────────────────────────

def get_metrics() -> dict:
    import psutil

    cpu  = psutil.cpu_percent(interval=1)
    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "mount":    part.mountpoint,
                "total_gb": round(usage.total / 1e9, 1),
                "free_gb":  round(usage.free / 1e9, 1),
                "used_pct": usage.percent,
            })
        except PermissionError:
            pass

    uptime_secs = time.time() - psutil.boot_time()
    d, r = divmod(int(uptime_secs), 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)

    return {
        "cpu":       round(cpu, 1),
        "memory":    round(mem.percent, 1),
        "disk":      disk.percent,
        "disks":     disks,
        "uptime":    f"{d}d {h}h {m}m",
        "load_avg":  list(os.getloadavg()),
        "mem_total": round(mem.total / 1e9, 2),
        "mem_used":  round((mem.total - mem.available) / 1e9, 2),
    }


def get_agent_info() -> dict:
    try:
        m = get_metrics()
    except Exception:
        m = {"cpu": 0, "memory": 0, "disk": 0}
    return {
        "agent":    "netbot",
        "hostname": socket.gethostname(),
        "ip":       get_ip(),
        "os":       "linux",
        "distro":   " ".join(platform.linux_distribution()) if hasattr(platform, "linux_distribution") else platform.version(),
        "version":  AGENT_VERSION,
        "roles":    detect_roles(),
        "cpu":      m.get("cpu", 0),
        "memory":   m.get("memory", 0),
        "disk":     m.get("disk", 0),
        "uptime":   m.get("uptime", "?"),
    }


# ── Command Dispatch ──────────────────────────────────────────────────────────

def run_cmd(cmd: list, timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"Command not found: {cmd[0]}"
    except Exception as e:
        return f"Error: {e}"


def dispatch_command(action: str, args: list) -> dict:
    result = _dispatch(action, args)
    return {"result": result}


def _dispatch(action: str, args: list) -> str:
    if action == "metrics":
        return json.dumps(get_metrics())

    if action == "stats":
        m = get_metrics()
        out  = f"=== {socket.gethostname()} System Stats ===\n"
        out += f"CPU:     {m['cpu']}%\n"
        out += f"Memory:  {m['memory']}% ({m.get('mem_used',0)}/{m.get('mem_total',0)} GB)\n"
        out += f"Uptime:  {m['uptime']}\n"
        out += f"Load:    {' '.join(str(l) for l in m.get('load_avg',[]))}\n\nDisks:\n"
        for d in m.get("disks", []):
            out += f"  {d['mount']}  {d['used_pct']}% used ({d['free_gb']} GB free)\n"
        return out

    if action == "services":
        return run_cmd(["systemctl", "list-units", "--type=service", "--no-pager", "--no-legend",
                        "--state=running,failed,dead"])

    if action in ("restart_service", "stop_service", "start_service"):
        if not args:
            return "Provide service name"
        op  = action.split("_")[0]
        svc = args[0]
        return run_cmd(["systemctl", op, svc])

    if action == "ps":
        return run_cmd(["ps", "aux", "--sort=-%cpu"])

    if action == "netstat":
        if shutil.which("ss"):
            return run_cmd(["ss", "-tulnp"])
        return run_cmd(["netstat", "-tulnp"])

    if action == "disk":
        return run_cmd(["df", "-h"])

    if action == "syslog":
        lines = args[0] if args else "30"
        return run_cmd(["journalctl", "-n", str(lines), "--no-pager"])

    if action == "logs":
        svc   = args[0] if args else "syslog"
        lines = args[1] if len(args) > 1 else "30"
        return run_cmd(["journalctl", "-u", svc, "-n", str(lines), "--no-pager"])

    if action == "firewall":
        if shutil.which("ufw"):
            return run_cmd(["ufw", "status", "verbose"])
        if shutil.which("firewall-cmd"):
            return run_cmd(["firewall-cmd", "--list-all"])
        return run_cmd(["iptables", "-L", "-n", "--line-numbers"])

    if action == "ssh_keys":
        keys = []
        for f in Path("/root/.ssh").glob("authorized_keys"):
            keys.append(f.read_text())
        for home in Path("/home").iterdir():
            ak = home / ".ssh" / "authorized_keys"
            if ak.exists():
                keys.append(f"=== {home.name} ===\n{ak.read_text()}")
        return "\n".join(keys) or "No authorized_keys found"

    if action == "users":
        return run_cmd(["who"])

    if action == "last_logins":
        return run_cmd(["last", "-n", "20"])

    if action == "top_cpu":
        return run_cmd(["ps", "aux", "--sort=-%cpu", "--no-headers"])

    if action == "uptime":
        return run_cmd(["uptime"])

    if action == "cmd":
        # Admin-only arbitrary command
        if not args:
            return "Provide command"
        shell_cmd = " ".join(args)
        log.warning(f"Executing shell command: {shell_cmd}")
        try:
            r = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True, timeout=30)
            return (r.stdout + r.stderr).strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {e}"

    if action == "docker_ps":
        return run_cmd(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"])

    if action == "docker_stats":
        return run_cmd(["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"])

    return f"Unknown action: {action}"


# ── HMAC Verification ─────────────────────────────────────────────────────────

def verify_signature(token: str, timestamp: str, signature: str, body: str) -> bool:
    try:
        data = f"{timestamp}:{body}".encode()
        expected = hmac.new(token.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


# ── HTTP Server ───────────────────────────────────────────────────────────────

class AgentHandler(BaseHTTPRequestHandler):
    token: str = ""

    def log_message(self, format, *args):
        pass  # suppress default logging

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/info":
            self.send_json(get_agent_info())
        elif self.path == "/health":
            self.send_json({"status": "ok"})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/command":
            self.send_json({"error": "not found"}, 404)
            return

        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length).decode()
        ts      = self.headers.get("X-Timestamp", "")
        sig     = self.headers.get("X-Signature", "")

        if not verify_signature(self.token, ts, sig, body):
            log.warning("Rejected command: invalid signature")
            self.send_json({"error": "unauthorized"}, 401)
            return

        try:
            cmd    = json.loads(body)
            action = cmd.get("action", "")
            args   = cmd.get("args", [])
            log.info(f"Command: {action} {args}")

            if action == "metrics":
                m = get_metrics()
                self.send_json({"metrics": m})
            else:
                result = dispatch_command(action, args)
                self.send_json(result)
        except Exception as e:
            log.error(f"Command error: {e}")
            self.send_json({"error": str(e)}, 500)


def register_with_server(bot_server: str):
    """Register this agent with the central bot server."""
    info = get_agent_info()
    info["url"] = f"http://{get_ip()}:{AGENT_PORT}"
    try:
        data = json.dumps(info).encode()
        req  = urllib.request.Request(
            f"{bot_server}/agent/register",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        log.info(f"Registered with bot server: {bot_server}")
    except Exception as e:
        log.warning(f"Could not register with bot server: {e}")


def heartbeat_loop(bot_server: str, interval: int = 25):
    while True:
        time.sleep(interval)
        register_with_server(bot_server)


# ── Install ───────────────────────────────────────────────────────────────────

SYSTEMD_UNIT = """[Unit]
Description=NetBot Linux Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {script_path} --server {server} --token {token}
Restart=always
RestartSec=10
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

def install(server: str, token: str):
    script_path = os.path.abspath(__file__)
    os.makedirs("/etc/netbot", exist_ok=True)

    cfg = {"server": server, "token": token}
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f)
    os.chmod(CONFIG_PATH, 0o600)

    unit = SYSTEMD_UNIT.format(script_path=script_path, server=server, token=token)
    with open("/etc/systemd/system/netbot-agent.service", "w") as f:
        f.write(unit)

    os.system("pip3 install psutil --quiet")
    os.system("systemctl daemon-reload")
    os.system("systemctl enable netbot-agent")
    os.system("systemctl start netbot-agent")
    print(f"✅ NetBot Linux Agent installed and started.")
    print(f"   Server: {server}")
    print(f"   Status: systemctl status netbot-agent")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server",  default=os.environ.get("NETBOT_SERVER", ""))
    parser.add_argument("--token",   default=os.environ.get("NETBOT_TOKEN", ""))
    parser.add_argument("--port",    type=int, default=AGENT_PORT)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()

    if args.install:
        if not args.server or not args.token:
            print("Error: --server and --token required for install")
            sys.exit(1)
        install(args.server, args.token)
        return

    # Load from config if args not provided
    server = args.server
    token  = args.token
    if not server and Path(CONFIG_PATH).exists():
        with open(CONFIG_PATH) as f:
            cfg    = json.load(f)
            server = cfg.get("server", "")
            token  = cfg.get("token", "")

    if not token:
        print("Error: No token configured. Run with --install or set NETBOT_TOKEN env var.")
        sys.exit(1)

    log.info(f"NetBot Linux Agent v{AGENT_VERSION} starting on port {args.port}")
    log.info(f"Hostname: {socket.gethostname()} | IP: {get_ip()}")
    log.info(f"Roles: {', '.join(detect_roles()) or 'none detected'}")

    # Register with bot server
    if server:
        register_with_server(server)
        # Start heartbeat thread
        hb = Thread(target=heartbeat_loop, args=(server,), daemon=True)
        hb.start()

    # Start HTTP server
    AgentHandler.token = token
    httpd = HTTPServer(("0.0.0.0", args.port), AgentHandler)
    log.info(f"Listening on 0.0.0.0:{args.port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
