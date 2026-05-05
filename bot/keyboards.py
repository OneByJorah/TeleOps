"""
Inline keyboard builder for NetBot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status",      callback_data="status"),
            InlineKeyboardButton("🖥️ Agents",      callback_data="agents"),
        ],
        [
            InlineKeyboardButton("🪟 Windows",     callback_data="win_list"),
            InlineKeyboardButton("🐧 Linux",       callback_data="lx_list"),
        ],
        [
            InlineKeyboardButton("📡 SNMP",        callback_data="snmp_list"),
            InlineKeyboardButton("📊 Dashboard",   callback_data="dashboard"),
        ],
    ])


def agent_list_keyboard(agents: dict, prefix: str = "agent") -> InlineKeyboardMarkup:
    buttons = []
    for hostname, info in list(agents.items())[:20]:  # Telegram has button limits
        icon   = "🟢" if info.get("status") == "online" else "🔴"
        os_icon = "🪟" if info.get("os") == "windows" else "🐧"
        label  = f"{icon}{os_icon} {hostname}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"{prefix}:{hostname}:menu")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def windows_menu_keyboard(host: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 System Stats",   callback_data=f"win:{host}:stats"),
            InlineKeyboardButton("⚙️ Services",       callback_data=f"win:{host}:services"),
        ],
        [
            InlineKeyboardButton("👤 AD Users",       callback_data=f"win:{host}:ad_users"),
            InlineKeyboardButton("🌐 DNS Zones",      callback_data=f"win:{host}:dns"),
        ],
        [
            InlineKeyboardButton("🔌 DHCP Scopes",    callback_data=f"win:{host}:dhcp"),
            InlineKeyboardButton("📋 Event Log",      callback_data=f"win:{host}:eventlog"),
        ],
        [
            InlineKeyboardButton("👥 AD Groups",      callback_data=f"win:{host}:ad_groups"),
            InlineKeyboardButton("🖥️ Processes",     callback_data=f"win:{host}:processes"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="win_list")],
    ])


def linux_menu_keyboard(host: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats",          callback_data=f"lx:{host}:stats"),
            InlineKeyboardButton("⚙️ Services",       callback_data=f"lx:{host}:services"),
        ],
        [
            InlineKeyboardButton("🔄 Processes",      callback_data=f"lx:{host}:ps"),
            InlineKeyboardButton("🌐 Netstat",        callback_data=f"lx:{host}:netstat"),
        ],
        [
            InlineKeyboardButton("🛡️ Firewall",      callback_data=f"lx:{host}:firewall"),
            InlineKeyboardButton("💾 Disk",           callback_data=f"lx:{host}:disk"),
        ],
        [
            InlineKeyboardButton("📝 Syslog",         callback_data=f"lx:{host}:syslog"),
            InlineKeyboardButton("🔑 SSH Keys",       callback_data=f"lx:{host}:ssh_keys"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="lx_list")],
    ])


def ad_menu_keyboard(host: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 List Users",         callback_data=f"win:{host}:ad_users")],
        [InlineKeyboardButton("➕ Create User",        callback_data=f"win:{host}:ad_create_prompt")],
        [InlineKeyboardButton("🔑 Reset Password",     callback_data=f"win:{host}:ad_reset_prompt")],
        [InlineKeyboardButton("🚫 Disable User",       callback_data=f"win:{host}:ad_disable_prompt")],
        [InlineKeyboardButton("✅ Enable User",        callback_data=f"win:{host}:ad_enable_prompt")],
        [InlineKeyboardButton("🔍 Search User",        callback_data=f"win:{host}:ad_search_prompt")],
        [InlineKeyboardButton("⬅️ Back",               callback_data=f"win:{host}:menu")],
    ])
