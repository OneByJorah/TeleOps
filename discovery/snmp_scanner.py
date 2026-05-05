"""
NetBot SNMP Discovery and Polling Engine
Supports SNMP v1/v2c/v3
"""

import asyncio
import logging
import time
from typing import Optional

log = logging.getLogger("netbot.snmp")

# Core OIDs
OID_SYSNAME    = "1.3.6.1.2.1.1.5.0"
OID_SYSDESCR   = "1.3.6.1.2.1.1.1.0"
OID_SYSUPTIME  = "1.3.6.1.2.1.1.3.0"
OID_IF_IN      = "1.3.6.1.2.1.2.2.1.10"   # ifInOctets
OID_IF_OUT     = "1.3.6.1.2.1.2.2.1.16"   # ifOutOctets
OID_CPU_LOAD   = "1.3.6.1.4.1.2021.10.1.3.1"  # UCD-SNMP 1-min load
OID_MEM_TOTAL  = "1.3.6.1.4.1.2021.4.5.0"
OID_MEM_FREE   = "1.3.6.1.4.1.2021.4.11.0"
OID_HR_PROC    = "1.3.6.1.2.1.25.3.3.1.2"     # HOST-MIB CPU


def _format_uptime(ticks: int) -> str:
    """Convert SNMP TimeTicks (1/100 sec) to human readable."""
    seconds = ticks // 100
    d, rem  = divmod(seconds, 86400)
    h, rem  = divmod(rem, 3600)
    m, s    = divmod(rem, 60)
    return f"{d}d {h}h {m}m {s}s"


def _bytes_to_human(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


class SNMPScanner:
    def __init__(self, config: dict):
        self.cfg         = config
        self.snmp_cfg    = config.get("snmp", {})
        self.communities = self.snmp_cfg.get("communities", ["public"])
        self.port        = self.snmp_cfg.get("port", 161)
        self.timeout     = self.snmp_cfg.get("timeout", 5)
        self.retries     = self.snmp_cfg.get("retries", 2)
        self.poll_interval = self.snmp_cfg.get("poll_interval", 60)
        self.networks    = config.get("discovery", {}).get("networks", [])
        self._devices: dict = {}  # ip -> device data

    def set_device_store(self, devices: dict):
        self._devices = devices

    async def start_background_poll(self):
        log.info(f"SNMP background polling every {self.poll_interval}s")
        scan_count = 0
        while True:
            try:
                # Full scan every 10 polls, otherwise just poll known devices
                if scan_count % 10 == 0:
                    await self.scan_now()
                else:
                    await self.poll_all()
                scan_count += 1
            except Exception as e:
                log.error(f"SNMP poll error: {e}")
            await asyncio.sleep(self.poll_interval)

    async def scan_now(self) -> int:
        """Discover SNMP devices across all configured networks."""
        import ipaddress

        all_ips = []
        for net in self.networks:
            try:
                network = ipaddress.ip_network(net, strict=False)
                all_ips.extend([str(ip) for ip in network.hosts()])
            except ValueError:
                pass

        sem   = asyncio.Semaphore(30)
        tasks = [self._try_snmp_host(ip, sem) for ip in all_ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        found = sum(1 for r in results if r and not isinstance(r, Exception))
        log.info(f"SNMP scan complete: {found} responding devices")
        return found

    async def _try_snmp_host(self, ip: str, sem: asyncio.Semaphore):
        async with sem:
            for community in self.communities:
                data = await self._snmp_get_basic(ip, community)
                if data:
                    data["community"] = community
                    data["ip"]        = ip
                    data["last_seen"] = time.time()
                    self._devices[ip] = data
                    return data
        return None

    async def poll_all(self):
        """Poll all known SNMP devices."""
        if not self._devices:
            return
        sem   = asyncio.Semaphore(20)
        tasks = [self._poll_known(ip, info, sem) for ip, info in self._devices.items()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _poll_known(self, ip: str, info: dict, sem: asyncio.Semaphore):
        async with sem:
            community = info.get("community", "public")
            data = await self._snmp_get_basic(ip, community)
            if data:
                info.update(data)
                info["last_seen"] = time.time()
                info["status"]    = "online"
            else:
                info["status"] = "offline"

    async def poll_device(self, ip: str) -> Optional[dict]:
        """Poll a specific device, trying all communities."""
        for community in self.communities:
            data = await self._snmp_get_basic(ip, community)
            if data:
                data["community"] = community
                data["ip"]        = ip
                self._devices[ip] = data
                return data
        return None

    async def _snmp_get_basic(self, ip: str, community: str) -> Optional[dict]:
        """
        Perform basic SNMP GETs using pysnmp.
        Returns a dict of device info, or None if unreachable.
        """
        try:
            from pysnmp.hlapi.asyncio import (
                getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
                ContextData, ObjectType, ObjectIdentity
            )

            engine = SnmpEngine()

            async def get_oid(oid_str):
                iterator = getCmd(
                    engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid_str))
                )
                error_indication, error_status, _, var_binds = await iterator
                if error_indication or error_status:
                    return None
                for _, val in var_binds:
                    return str(val)
                return None

            # Fetch core OIDs concurrently
            name, description, uptime_raw = await asyncio.gather(
                get_oid(OID_SYSNAME),
                get_oid(OID_SYSDESCR),
                get_oid(OID_SYSUPTIME),
                return_exceptions=True
            )

            if not description:
                return None  # Didn't respond

            uptime_str = "?"
            if uptime_raw and not isinstance(uptime_raw, Exception):
                try:
                    uptime_str = _format_uptime(int(uptime_raw))
                except (ValueError, TypeError):
                    uptime_str = str(uptime_raw)

            # Optionally fetch interface counters
            if_in = await get_oid(f"{OID_IF_IN}.1")
            if_out = await get_oid(f"{OID_IF_OUT}.1")

            if_in_str  = _bytes_to_human(int(if_in))  if if_in  else "N/A"
            if_out_str = _bytes_to_human(int(if_out)) if if_out else "N/A"

            # CPU load (UCD-SNMP or HOST-MIB)
            cpu_load = await get_oid(OID_CPU_LOAD)
            if not cpu_load:
                cpu_load = await get_oid(f"{OID_HR_PROC}.1")

            # Memory
            mem_total = await get_oid(OID_MEM_TOTAL)
            mem_free  = await get_oid(OID_MEM_FREE)
            mem_str   = "N/A"
            if mem_total and mem_free:
                try:
                    total = int(mem_total) * 1024
                    free  = int(mem_free)  * 1024
                    used_pct = (1 - free / total) * 100 if total else 0
                    mem_str  = f"{used_pct:.1f}% ({_bytes_to_human(total - free)} / {_bytes_to_human(total)})"
                except Exception:
                    pass

            return {
                "name":        str(name)        if name        else ip,
                "description": str(description) if description else "Unknown",
                "uptime":      uptime_str,
                "if_in":       if_in_str,
                "if_out":      if_out_str,
                "cpu_load":    f"{cpu_load}%" if cpu_load else "N/A",
                "memory":      mem_str,
                "status":      "online",
            }

        except ImportError:
            log.error("pysnmp not installed. Run: pip install pysnmp")
            return None
        except Exception as e:
            log.debug(f"SNMP error {ip}: {e}")
            return None
