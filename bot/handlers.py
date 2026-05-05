"""
NetBot Telegram Command Handlers
"""

import logging
import json
from datetime import datetime, timezone
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.keyboards import (
    main_menu_keyboard, agent_list_keyboard, windows_menu_keyboard,
    linux_menu_keyboard, ad_menu_keyboard
)

log = logging.getLogger("netbot.handlers")

# ── Auth Decorator ────────────────────────────────────────────────────────────

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = update.effective_user.id
        admins = ctx.bot_data.get("config", {}).get("bot", {}).get("admin_ids", [])
        if uid not in admins:
            await update.message.reply_text("⛔ Access denied. Your ID is not authorized.")
            log.warning(f"Unauthorized access attempt by user {uid}")
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper


def get_agents(ctx) -> dict:
    return ctx.bot_data.get("agents", {})


# ── /start ────────────────────────────────────────────────────────────────────

@admin_only
async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    agents = get_agents(ctx)
    online = sum(1 for a in agents.values() if a.get("status") == "online")
    text = (
        f"🛡️ *NetBot — Network Control Center*\n\n"
        f"👤 Welcome, `{update.effective_user.first_name}`\n"
        f"🖥️ Agents online: *{online}/{len(agents)}*\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"Use the menu below or type `/help` for all commands."
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )


# ── /status ───────────────────────────────────────────────────────────────────

@admin_only
async def status_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    agents = get_agents(ctx)
    snmp_devices = ctx.bot_data.get("snmp_devices", {})

    if not agents and not snmp_devices:
        await update.message.reply_text(
            "📡 *Network Status*\n\nNo agents or SNMP devices discovered yet.\n"
            "Make sure you have deployed agents on your servers.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    lines = ["📊 *Network Status Overview*\n"]

    # Agents summary
    windows_agents = [a for a in agents.values() if a.get("os") == "windows"]
    linux_agents   = [a for a in agents.values() if a.get("os") == "linux"]

    lines.append(f"🖥️ *Windows Servers:* {len(windows_agents)}")
    for a in windows_agents:
        icon = "🟢" if a.get("status") == "online" else "🔴"
        host = a.get("hostname", "unknown")
        cpu  = a.get("cpu", "?")
        mem  = a.get("memory", "?")
        lines.append(f"  {icon} `{host}` — CPU:{cpu}% MEM:{mem}%")

    lines.append(f"\n🐧 *Linux Servers:* {len(linux_agents)}")
    for a in linux_agents:
        icon = "🟢" if a.get("status") == "online" else "🔴"
        host = a.get("hostname", "unknown")
        cpu  = a.get("cpu", "?")
        mem  = a.get("memory", "?")
        lines.append(f"  {icon} `{host}` — CPU:{cpu}% MEM:{mem}%")

    if snmp_devices:
        lines.append(f"\n📡 *SNMP Devices:* {len(snmp_devices)}")
        for ip, d in list(snmp_devices.items())[:10]:
            lines.append(f"  📶 `{ip}` — {d.get('description', 'Unknown device')[:40]}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )


# ── /agents ───────────────────────────────────────────────────────────────────

@admin_only
async def agents_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    agents = get_agents(ctx)
    if not agents:
        await update.message.reply_text("No agents registered yet.")
        return
    await update.message.reply_text(
        "🖥️ *Registered Agents* — select one:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=agent_list_keyboard(agents)
    )


# ── /dashboard ────────────────────────────────────────────────────────────────

@admin_only
async def dashboard_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cfg = ctx.bot_data.get("config", {})
    host = cfg.get("server", {}).get("host", "localhost")
    port = cfg.get("dashboard", {}).get("port", 5000)
    url  = f"http://{host}:{port}"
    await update.message.reply_text(
        f"📊 *NetBot Dashboard*\n\n🔗 [Open Dashboard]({url})\n\n"
        f"The dashboard shows live metrics from all discovered agents and SNMP devices.",
        parse_mode=ParseMode.MARKDOWN
    )


# ── /win <host> <action> ──────────────────────────────────────────────────────

@admin_only
async def windows_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    agents = get_agents(ctx)

    if not args:
        # Show all Windows agents
        win_agents = {k: v for k, v in agents.items() if v.get("os") == "windows"}
        if not win_agents:
            await update.message.reply_text("No Windows agents online.")
            return
        await update.message.reply_text(
            "🖥️ *Windows Agents* — select a server:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=agent_list_keyboard(win_agents, prefix="win")
        )
        return

    host   = args[0]
    action = args[1] if len(args) > 1 else "menu"

    agent = agents.get(host)
    if not agent:
        await update.message.reply_text(f"❌ Agent `{host}` not found or offline.", parse_mode=ParseMode.MARKDOWN)
        return

    await _dispatch_windows_command(update, ctx, agent, action, args[2:])


async def _dispatch_windows_command(update, ctx, agent, action, extra_args):
    host = agent["hostname"]
    url  = agent["url"]

    if action == "menu":
        await update.message.reply_text(
            f"🖥️ *{host}* — Windows Menu",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=windows_menu_keyboard(host)
        )
        return

    msg = await update.message.reply_text(f"⏳ Querying `{host}`...", parse_mode=ParseMode.MARKDOWN)

    try:
        import aiohttp, asyncio
        cfg = ctx.bot_data["config"]
        secret = cfg["server"]["secret_key"]

        payload = {"action": action, "args": extra_args}
        import hmac, hashlib, time
        ts = str(int(time.time()))
        sig = hmac.new(secret.encode(), f"{ts}:{json.dumps(payload)}".encode(), hashlib.sha256).hexdigest()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/command",
                json=payload,
                headers={"X-Timestamp": ts, "X-Signature": sig},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    await msg.edit_text(f"❌ Agent returned HTTP {resp.status}")
                    return
                data = await resp.json()

        result = data.get("result", "No output")
        text = f"🖥️ *{host}* — `{action}`\n\n```\n{result[:3500]}\n```"
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await msg.edit_text(f"❌ Error communicating with agent: `{e}`", parse_mode=ParseMode.MARKDOWN)


# ── /lx <host> <action> ───────────────────────────────────────────────────────

@admin_only
async def linux_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    agents = get_agents(ctx)

    if not args:
        lx_agents = {k: v for k, v in agents.items() if v.get("os") == "linux"}
        if not lx_agents:
            await update.message.reply_text("No Linux agents online.")
            return
        await update.message.reply_text(
            "🐧 *Linux Agents* — select a server:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=agent_list_keyboard(lx_agents, prefix="lx")
        )
        return

    host   = args[0]
    action = args[1] if len(args) > 1 else "menu"
    agent  = agents.get(host)

    if not agent:
        await update.message.reply_text(f"❌ Agent `{host}` not found.", parse_mode=ParseMode.MARKDOWN)
        return

    await _dispatch_linux_command(update, ctx, agent, action, args[2:])


async def _dispatch_linux_command(update, ctx, agent, action, extra_args):
    host = agent["hostname"]
    msg  = await update.message.reply_text(f"⏳ Querying `{host}`...", parse_mode=ParseMode.MARKDOWN)

    try:
        import aiohttp, time, hmac, hashlib
        cfg    = ctx.bot_data["config"]
        secret = cfg["server"]["secret_key"]
        url    = agent["url"]

        payload = {"action": action, "args": extra_args}
        ts  = str(int(time.time()))
        sig = hmac.new(secret.encode(), f"{ts}:{json.dumps(payload)}".encode(), hashlib.sha256).hexdigest()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/command",
                json=payload,
                headers={"X-Timestamp": ts, "X-Signature": sig},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()

        result = data.get("result", "No output")
        text   = f"🐧 *{host}* — `{action}`\n\n```\n{result[:3500]}\n```"
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await msg.edit_text(f"❌ Error: `{e}`", parse_mode=ParseMode.MARKDOWN)


# ── /snmp ─────────────────────────────────────────────────────────────────────

@admin_only
async def snmp_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    snmp_devices = ctx.bot_data.get("snmp_devices", {})

    if not args or args[0] == "list":
        if not snmp_devices:
            await update.message.reply_text("📡 No SNMP devices discovered yet. Try `/snmp scan`.")
            return
        lines = ["📡 *SNMP Devices*\n"]
        for ip, d in snmp_devices.items():
            lines.append(f"• `{ip}` — {d.get('description','?')[:50]}")
            lines.append(f"  Uptime: {d.get('uptime','?')} | In: {d.get('if_in','?')} | Out: {d.get('if_out','?')}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        return

    if args[0] == "scan":
        msg = await update.message.reply_text("📡 Starting SNMP discovery scan...")
        scanner = ctx.bot_data.get("snmp")
        if scanner:
            count = await scanner.scan_now()
            await msg.edit_text(f"✅ SNMP scan complete. Found *{count}* devices.", parse_mode=ParseMode.MARKDOWN)
        else:
            await msg.edit_text("❌ SNMP scanner not initialized.")
        return

    # /snmp <ip> — poll specific device
    ip = args[0]
    scanner = ctx.bot_data.get("snmp")
    if not scanner:
        await update.message.reply_text("❌ SNMP scanner not available.")
        return

    msg = await update.message.reply_text(f"📡 Polling `{ip}`...", parse_mode=ParseMode.MARKDOWN)
    data = await scanner.poll_device(ip)
    if not data:
        await msg.edit_text(f"❌ Could not poll `{ip}`. Check SNMP community string.", parse_mode=ParseMode.MARKDOWN)
        return

    text = (
        f"📡 *SNMP Report — {ip}*\n\n"
        f"📛 *Name:* {data.get('name','?')}\n"
        f"📝 *Desc:* {data.get('description','?')[:80]}\n"
        f"⏱️ *Uptime:* {data.get('uptime','?')}\n"
        f"📥 *IF In:* {data.get('if_in','?')}\n"
        f"📤 *IF Out:* {data.get('if_out','?')}\n"
        f"🌡️ *CPU Load:* {data.get('cpu_load','N/A')}\n"
        f"💾 *Memory:* {data.get('memory','N/A')}\n"
    )
    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)


# ── Alert handler ─────────────────────────────────────────────────────────────

async def alert_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 *Alert Configuration*\n\n"
        "Alerts are sent automatically when:\n"
        "• CPU > threshold\n• Memory > threshold\n• Disk > threshold\n• Service goes down\n\n"
        "Edit thresholds in `config/config.yaml`",
        parse_mode=ParseMode.MARKDOWN
    )


# ── Inline Callback Handler ───────────────────────────────────────────────────

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Route callbacks by prefix
    if data.startswith("win:"):
        _, host, action = data.split(":", 2)
        agents = get_agents(ctx)
        agent  = agents.get(host)
        if agent:
            # Fake update to reuse handler
            ctx.args = [host, action]
            await _dispatch_windows_command(
                type('obj', (object,), {'message': query.message, 'effective_user': query.from_user})(),
                ctx, agent, action, []
            )

    elif data.startswith("lx:"):
        _, host, action = data.split(":", 2)
        agents = get_agents(ctx)
        agent  = agents.get(host)
        if agent:
            ctx.args = [host, action]
            await _dispatch_linux_command(
                type('obj', (object,), {'message': query.message, 'effective_user': query.from_user})(),
                ctx, agent, action, []
            )

    elif data == "status":
        await status_handler(
            type('obj', (object,), {'message': query.message, 'effective_user': query.from_user})(),
            ctx
        )
