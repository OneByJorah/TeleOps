"""
NetBot Background Scheduler
Runs heartbeat checks, alert polling, metric collection
"""

import logging
import time
from datetime import datetime, timezone, timedelta

from telegram.ext import Application
from telegram.constants import ParseMode

log = logging.getLogger("netbot.scheduler")

# Track last alert time per host+metric to avoid spam
_alert_cooldowns: dict = {}


def setup_scheduler(app: Application):
    """Register all scheduled jobs with the APScheduler via PTB's job queue."""
    jq = app.job_queue

    cfg = app.bot_data.get("config", {})
    heartbeat_interval = cfg.get("agents", {}).get("heartbeat_interval", 30)
    poll_interval      = cfg.get("agents", {}).get("collect_interval", 60)
    snmp_interval      = cfg.get("snmp", {}).get("poll_interval", 60)

    # Check agent heartbeats
    jq.run_repeating(check_agent_heartbeats, interval=heartbeat_interval, first=15)

    # Collect metrics from all online agents
    jq.run_repeating(collect_agent_metrics, interval=poll_interval, first=20)

    # SNMP polling
    jq.run_repeating(poll_snmp_devices, interval=snmp_interval, first=25)

    log.info(f"Scheduler running: heartbeat={heartbeat_interval}s, metrics={poll_interval}s, snmp={snmp_interval}s")


async def check_agent_heartbeats(context):
    """Mark agents as offline if they haven't checked in."""
    cfg     = context.bot_data.get("config", {})
    agents  = context.bot_data.get("agents", {})
    admins  = cfg.get("bot", {}).get("admin_ids", [])
    threshold = cfg.get("agents", {}).get("offline_threshold", 90)
    now     = time.time()

    for hostname, agent in list(agents.items()):
        last_seen  = agent.get("last_seen", 0)
        was_online = agent.get("status") == "online"
        is_online  = (now - last_seen) < threshold

        if was_online and not is_online:
            agent["status"] = "offline"
            log.warning(f"Agent {hostname} went OFFLINE")
            await _send_alert(context, admins, f"🔴 *Agent Offline*\n`{hostname}` has not checked in for >{threshold}s")

        elif not was_online and is_online:
            agent["status"] = "online"
            log.info(f"Agent {hostname} came back ONLINE")
            await _send_alert(context, admins, f"🟢 *Agent Online*\n`{hostname}` is back online")


async def collect_agent_metrics(context):
    """Pull latest metrics from all online agents and check thresholds."""
    import aiohttp, asyncio, json, hmac, hashlib

    cfg     = context.bot_data.get("config", {})
    agents  = context.bot_data.get("agents", {})
    admins  = cfg.get("bot", {}).get("admin_ids", [])
    secret  = cfg.get("server", {}).get("secret_key", "")
    thresholds = cfg.get("alerts", {}).get("thresholds", {})

    tasks = []
    for hostname, agent in list(agents.items()):
        if agent.get("status") == "online":
            tasks.append(_fetch_metrics(agent, secret))

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for hostname, result in zip(
        [h for h, a in agents.items() if a.get("status") == "online"],
        results
    ):
        if isinstance(result, Exception):
            log.debug(f"Metrics fetch failed for {hostname}: {result}")
            continue
        if not result:
            continue

        agent = agents[hostname]
        agent.update(result)
        agent["last_metrics"] = time.time()

        # Check alert thresholds
        await _check_thresholds(context, admins, hostname, result, thresholds)


async def _fetch_metrics(agent: dict, secret: str) -> dict | None:
    import aiohttp, json, hmac, hashlib, time as t

    url     = agent.get("url", "")
    payload = {"action": "metrics"}
    ts      = str(int(t.time()))
    sig     = hmac.new(secret.encode(), f"{ts}:{json.dumps(payload)}".encode(), hashlib.sha256).hexdigest()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/command",
                json=payload,
                headers={"X-Timestamp": ts, "X-Signature": sig},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get("metrics", {})
    except Exception:
        return None


async def _check_thresholds(context, admins, hostname, metrics, thresholds):
    """Send alert if any metric exceeds threshold (with cooldown)."""
    checks = [
        ("cpu",    metrics.get("cpu"),    thresholds.get("cpu_percent", 90),    "🔥 CPU"),
        ("memory", metrics.get("memory"), thresholds.get("memory_percent", 85), "💾 Memory"),
        ("disk",   metrics.get("disk"),   thresholds.get("disk_percent", 90),   "💿 Disk"),
    ]
    cooldown = context.bot_data.get("config", {}).get("alerts", {}).get("cooldown", 300)

    for key, value, threshold, label in checks:
        if value is None:
            continue
        try:
            val = float(value)
        except (TypeError, ValueError):
            continue

        if val >= threshold:
            alert_key = f"{hostname}:{key}"
            last_alert = _alert_cooldowns.get(alert_key, 0)
            if time.time() - last_alert > cooldown:
                _alert_cooldowns[alert_key] = time.time()
                msg = f"⚠️ *Alert: {label} High*\nHost: `{hostname}`\nValue: *{val:.1f}%* (threshold: {threshold}%)"
                await _send_alert(context, admins, msg)


async def poll_snmp_devices(context):
    """Refresh SNMP device data in background."""
    snmp = context.bot_data.get("snmp")
    if snmp:
        await snmp.poll_all()


async def _send_alert(context, admin_ids: list, message: str):
    """Send alert message to all admins."""
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            log.error(f"Failed to send alert to {admin_id}: {e}")
