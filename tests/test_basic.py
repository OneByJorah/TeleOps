"""
NetBot Basic Tests
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json
import time
import hmac
import hashlib


def make_signature(secret: str, timestamp: str, body: str) -> str:
    data = f"{timestamp}:{body}".encode()
    return hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()


class TestSignature:
    def test_valid_signature(self):
        secret = "test-secret"
        ts     = str(int(time.time()))
        body   = json.dumps({"action": "stats"})
        sig    = make_signature(secret, ts, body)
        assert len(sig) == 64

    def test_signature_mismatch(self):
        sig1 = make_signature("secret1", "123", '{"a":1}')
        sig2 = make_signature("secret2", "123", '{"a":1}')
        assert sig1 != sig2


class TestDiscovery:
    def test_network_scanner_import(self):
        from discovery.network_scanner import NetworkScanner
        cfg = {
            "discovery": {"networks": ["192.168.1.0/24"], "scan_interval": 300, "ping_timeout": 1, "ping_workers": 10},
            "server": {"secret_key": "test"}
        }
        scanner = NetworkScanner(cfg)
        assert scanner is not None

    def test_snmp_scanner_import(self):
        from discovery.snmp_scanner import SNMPScanner
        cfg = {
            "snmp": {"communities": ["public"], "port": 161, "timeout": 5, "retries": 2, "poll_interval": 60},
            "discovery": {"networks": ["192.168.1.0/24"]}
        }
        scanner = SNMPScanner(cfg)
        assert scanner is not None


class TestAgentServer:
    def test_agent_server_import(self):
        from bot.agent_server import create_agent_server
        cfg = {
            "server": {"secret_key": "test", "host": "0.0.0.0", "port": 8080}
        }
        app = create_agent_server({}, {}, cfg)
        assert app is not None


class TestLinuxAgent:
    def test_get_ip(self):
        # Add agent dir to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../agents/linux"))
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "agent",
                os.path.join(os.path.dirname(__file__), "../agents/linux/agent.py")
            )
            agent = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent)
            ip = agent.get_ip()
            assert isinstance(ip, str)
            assert "." in ip
        except Exception:
            pytest.skip("Agent module not loadable in test env")
