"""
NetBot Network Auto-Discovery
Scans subnets for agent endpoints, builds the agent registry
"""

import asyncio
import ipaddress
import logging
import time
from typing import Optional

import aiohttp

log = logging.getLogger("netbot.discovery")

AGENT_PORT = 7845  # Default port agents listen on


class NetworkScanner:
    def __init__(self, config: dict):
        self.cfg       = config
        self.networks  = config.get("discovery", {}).get("networks", [])
        self.interval  = config.get("discovery", {}).get("scan_interval", 300)
        self.timeout   = config.get("discovery", {}).get("ping_timeout", 1)
        self.workers   = config.get("discovery", {}).get("ping_workers", 50)
        self.secret    = config.get("server", {}).get("secret_key", "")
        self._agents: dict = {}  # shared reference updated in place

    def set_agent_store(self, agents: dict):
        self._agents = agents

    async def start_background_scan(self):
        log.info(f"Network discovery scanning: {self.networks} every {self.interval}s")
        while True:
            try:
                await self.scan_all_networks()
            except Exception as e:
                log.error(f"Discovery scan error: {e}")
            await asyncio.sleep(self.interval)

    async def scan_all_networks(self):
        """Ping-scan all configured networks and probe for agents."""
        all_ips = []
        for net in self.networks:
            try:
                network = ipaddress.ip_network(net, strict=False)
                all_ips.extend([str(ip) for ip in network.hosts()])
            except ValueError as e:
                log.error(f"Invalid network {net}: {e}")

        if not all_ips:
            return

        log.info(f"Scanning {len(all_ips)} hosts across {len(self.networks)} networks")

        # Probe for agents in batches
        semaphore = asyncio.Semaphore(self.workers)
        tasks = [self._probe_host(ip, semaphore) for ip in all_ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        found = sum(1 for r in results if r and not isinstance(r, Exception))
        log.info(f"Discovery scan complete. Found/updated {found} agents.")

    async def _probe_host(self, ip: str, sem: asyncio.Semaphore) -> Optional[dict]:
        """Try to reach the NetBot agent on a host."""
        async with sem:
            url = f"http://{ip}:{AGENT_PORT}/info"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as resp:
                        if resp.status != 200:
                            return None
                        data = await resp.json()

                # Validate it's actually a NetBot agent
                if data.get("agent") != "netbot":
                    return None

                hostname = data.get("hostname", ip)
                info = {
                    "hostname": hostname,
                    "ip":       ip,
                    "url":      f"http://{ip}:{AGENT_PORT}",
                    "os":       data.get("os", "unknown"),
                    "version":  data.get("version", "?"),
                    "roles":    data.get("roles", []),
                    "status":   "online",
                    "last_seen": time.time(),
                    "cpu":      data.get("cpu", 0),
                    "memory":   data.get("memory", 0),
                    "disk":     data.get("disk", 0),
                }
                self._agents[hostname] = info
                log.debug(f"Agent found: {hostname} @ {ip} ({info['os']})")
                return info

            except (aiohttp.ClientError, asyncio.TimeoutError):
                return None
            except Exception as e:
                log.debug(f"Probe error {ip}: {e}")
                return None

    async def register_agent(self, data: dict) -> dict:
        """Handle agent self-registration (called from HTTP endpoint)."""
        hostname = data.get("hostname", data.get("ip", "unknown"))
        self._agents[hostname] = {
            "hostname":  hostname,
            "ip":        data.get("ip"),
            "url":       data.get("url", f"http://{data.get('ip')}:{AGENT_PORT}"),
            "os":        data.get("os", "unknown"),
            "version":   data.get("version", "?"),
            "roles":     data.get("roles", []),
            "status":    "online",
            "last_seen": time.time(),
            "cpu":       data.get("cpu", 0),
            "memory":    data.get("memory", 0),
            "disk":      data.get("disk", 0),
        }
        log.info(f"Agent registered: {hostname} ({data.get('os')})")
        return {"status": "registered", "hostname": hostname}
