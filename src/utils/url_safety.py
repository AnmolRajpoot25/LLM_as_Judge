"""Network destination validation for user-controlled service URLs."""

import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_ollama_url(url_str: str) -> bool:
    """Allow loopback for local Ollama, but reject private or special destinations."""
    try:
        parsed = urlparse(url_str.strip())
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        hostname = parsed.hostname.rstrip(".").lower()
        if parsed.username or parsed.password:
            return False
        if hostname in ("localhost", "localhost.localdomain"):
            return True
        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(hostname, parsed.port or 80, type=socket.SOCK_STREAM)
            ]
        return bool(addresses) and all(
            address.is_global or address.is_loopback for address in addresses
        )
    except (ValueError, OSError):
        return False
