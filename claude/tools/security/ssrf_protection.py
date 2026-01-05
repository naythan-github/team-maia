#!/usr/bin/env python3
"""
SSRF Protection Module
Prevents Server-Side Request Forgery attacks in WebFetch/WebSearch.

Features:
- Block localhost (127.0.0.0/8, ::1)
- Block private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Block link-local (169.254.0.0/16)
- Block cloud metadata endpoints (169.254.169.254)
- Custom domain blocklist support
- Various encoding bypass detection (decimal, hex, octal)
"""

import ipaddress
import socket
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SSRFCheckResult:
    """Result of SSRF check"""
    is_safe: bool
    reason: str
    resolved_ip: Optional[str] = None
    is_private: bool = False
    threat_type: Optional[str] = None


class SSRFProtection:
    """
    Detects and blocks SSRF attempts.

    Blocks:
    - localhost (127.0.0.0/8, ::1)
    - Private IPs (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Link-local (169.254.0.0/16, fe80::/10)
    - Cloud metadata endpoints (169.254.169.254)
    - Zero address (0.0.0.0)

    Usage:
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://192.168.1.1/admin")
        if not result['is_safe']:
            block_request()
    """

    # Private network ranges
    PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),  # Link-local
        ipaddress.ip_network('0.0.0.0/8'),  # Zero network
    ]

    # IPv6 private/local ranges
    PRIVATE_NETWORKS_V6 = [
        ipaddress.ip_network('::1/128'),  # Loopback
        ipaddress.ip_network('fe80::/10'),  # Link-local
        ipaddress.ip_network('fc00::/7'),  # Unique local
    ]

    # Cloud metadata endpoints
    METADATA_HOSTS = [
        '169.254.169.254',  # AWS, GCP, Azure
        'metadata.google.internal',
        'metadata.gcp.internal',
    ]

    def __init__(self, custom_blocklist: List[str] = None):
        """
        Initialize SSRF protection.

        Args:
            custom_blocklist: Additional domains to block
        """
        self.custom_blocklist = custom_blocklist or []
        self.stats = {
            'total_checked': 0,
            'blocked': 0,
            'allowed': 0,
            'by_threat_type': {},
            'start_time': datetime.now().isoformat()
        }

    def check_url(self, url: str, resolve_dns: bool = True) -> Dict[str, Any]:
        """
        Check URL for SSRF vulnerabilities.

        Args:
            url: URL to check
            resolve_dns: Whether to resolve hostname to IP (default True)

        Returns:
            {
                'is_safe': bool,
                'reason': str,
                'resolved_ip': Optional[str],
                'is_private': bool,
                'threat_type': Optional[str]
            }
        """
        self.stats['total_checked'] += 1

        # Handle None/empty
        if not url:
            return self._blocked_result("Empty or None URL", "invalid")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return self._blocked_result(f"Invalid URL: {e}", "invalid")

        # Must have a host
        hostname = parsed.hostname
        if not hostname:
            return self._blocked_result("No hostname in URL", "invalid")

        # Check for localhost hostnames
        if self.is_localhost(hostname):
            return self._blocked_result(
                f"Blocked localhost: {hostname}",
                "localhost",
                is_private=True
            )

        # Check for cloud metadata hosts
        if hostname.lower() in [h.lower() for h in self.METADATA_HOSTS]:
            return self._blocked_result(
                f"Blocked cloud metadata endpoint: {hostname}",
                "metadata",
                is_private=True
            )

        # Check custom blocklist
        blocklist_match = self._check_blocklist(hostname)
        if blocklist_match:
            return self._blocked_result(
                f"Blocked domain (blocklist): {blocklist_match}",
                "blocked_domain"
            )

        # Try to parse as IP address directly
        ip_result = self._check_ip_address(hostname)
        if ip_result:
            return ip_result

        # If resolve_dns is enabled, resolve hostname and check
        if resolve_dns:
            dns_result = self._check_dns_resolution(hostname)
            if dns_result:
                return dns_result

        # All checks passed
        self.stats['allowed'] += 1
        return {
            'is_safe': True,
            'reason': 'URL passed all SSRF checks',
            'resolved_ip': None,
            'is_private': False,
            'threat_type': None
        }

    def _check_ip_address(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Check if hostname is an IP address and if it's private."""
        # Handle various IP encodings
        ip_str = self._normalize_ip(hostname)
        if not ip_str:
            return None

        try:
            ip = ipaddress.ip_address(ip_str)

            # Check if private
            if self.is_private_ip(str(ip)):
                return self._blocked_result(
                    f"Blocked private IP: {ip}",
                    "private_ip" if str(ip) != "127.0.0.1" else "localhost",
                    resolved_ip=str(ip),
                    is_private=True
                )
        except ValueError:
            pass

        return None

    def _normalize_ip(self, hostname: str) -> Optional[str]:
        """
        Normalize various IP encodings to standard format.
        Handles decimal, hex, octal representations.
        """
        # Remove brackets for IPv6
        if hostname.startswith('[') and hostname.endswith(']'):
            return hostname[1:-1]

        # Try standard IP parse first
        try:
            ip = ipaddress.ip_address(hostname)
            return str(ip)
        except ValueError:
            pass

        # Try decimal encoding (e.g., 2130706433 = 127.0.0.1)
        try:
            if hostname.isdigit():
                decimal = int(hostname)
                if 0 <= decimal <= 0xFFFFFFFF:
                    ip = ipaddress.ip_address(decimal)
                    return str(ip)
        except (ValueError, OverflowError):
            pass

        # Try hex encoding (e.g., 0x7f000001 = 127.0.0.1)
        if hostname.lower().startswith('0x'):
            try:
                decimal = int(hostname, 16)
                if 0 <= decimal <= 0xFFFFFFFF:
                    ip = ipaddress.ip_address(decimal)
                    return str(ip)
            except (ValueError, OverflowError):
                pass

        # Try octal encoding (e.g., 0177.0.0.1 = 127.0.0.1)
        if '.' in hostname:
            parts = hostname.split('.')
            if any(p.startswith('0') and len(p) > 1 and p.isdigit() for p in parts):
                try:
                    # Convert each octal part
                    decimal_parts = []
                    for p in parts:
                        if p.startswith('0') and len(p) > 1:
                            decimal_parts.append(str(int(p, 8)))
                        else:
                            decimal_parts.append(p)
                    normalized = '.'.join(decimal_parts)
                    ip = ipaddress.ip_address(normalized)
                    return str(ip)
                except (ValueError, OverflowError):
                    pass

        return None

    def _check_dns_resolution(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Resolve hostname and check if it points to private IP."""
        try:
            # Get all IP addresses for hostname
            infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            for info in infos:
                ip_str = info[4][0]
                if self.is_private_ip(ip_str):
                    return self._blocked_result(
                        f"Hostname {hostname} resolves to private IP: {ip_str}",
                        "dns_rebinding",
                        resolved_ip=ip_str,
                        is_private=True
                    )
        except socket.gaierror:
            # DNS resolution failed - might be invalid hostname
            pass
        except Exception:
            pass

        return None

    def _check_blocklist(self, hostname: str) -> Optional[str]:
        """Check hostname against custom blocklist."""
        hostname_lower = hostname.lower()
        for blocked in self.custom_blocklist:
            blocked_lower = blocked.lower()
            # Exact match or subdomain match
            if hostname_lower == blocked_lower or hostname_lower.endswith('.' + blocked_lower):
                return blocked
        return None

    def _blocked_result(
        self,
        reason: str,
        threat_type: str,
        resolved_ip: str = None,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """Create a blocked result and update stats."""
        self.stats['blocked'] += 1
        self.stats['by_threat_type'][threat_type] = \
            self.stats['by_threat_type'].get(threat_type, 0) + 1

        return {
            'is_safe': False,
            'reason': reason,
            'resolved_ip': resolved_ip,
            'is_private': is_private,
            'threat_type': threat_type
        }

    def is_private_ip(self, ip: str) -> bool:
        """
        Check if IP address is private/internal.

        Args:
            ip: IP address string

        Returns:
            True if private/internal, False otherwise
        """
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check IPv4 private ranges
            if isinstance(ip_obj, ipaddress.IPv4Address):
                for network in self.PRIVATE_NETWORKS:
                    if ip_obj in network:
                        return True

            # Check IPv6 private ranges
            elif isinstance(ip_obj, ipaddress.IPv6Address):
                for network in self.PRIVATE_NETWORKS_V6:
                    if ip_obj in network:
                        return True

            return False
        except ValueError:
            return False

    def is_localhost(self, hostname: str) -> bool:
        """
        Check if hostname is localhost or loopback.

        Args:
            hostname: Hostname to check

        Returns:
            True if localhost, False otherwise
        """
        hostname_lower = hostname.lower()

        # Common localhost names
        if hostname_lower in ['localhost', 'localhost.localdomain']:
            return True

        # Check if it's a loopback IP
        normalized = self._normalize_ip(hostname)
        if normalized:
            try:
                ip = ipaddress.ip_address(normalized)
                # IPv4 loopback (127.0.0.0/8)
                if isinstance(ip, ipaddress.IPv4Address):
                    return ip in ipaddress.ip_network('127.0.0.0/8')
                # IPv6 loopback (::1)
                elif isinstance(ip, ipaddress.IPv6Address):
                    return ip == ipaddress.ip_address('::1')
            except ValueError:
                pass

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get SSRF protection statistics."""
        return {
            'total_checked': self.stats['total_checked'],
            'blocked': self.stats['blocked'],
            'allowed': self.stats['allowed'],
            'by_threat_type': self.stats['by_threat_type'],
            'start_time': self.stats['start_time']
        }


def main():
    """CLI interface for SSRF protection testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 ssrf_protection.py <url>")
        print("Example: python3 ssrf_protection.py http://127.0.0.1/admin")
        sys.exit(1)

    url = sys.argv[1]
    ssrf = SSRFProtection()
    result = ssrf.check_url(url)

    print(f"URL: {url}")
    print(f"Safe: {result['is_safe']}")
    print(f"Reason: {result['reason']}")
    if result['threat_type']:
        print(f"Threat Type: {result['threat_type']}")
    if result['resolved_ip']:
        print(f"Resolved IP: {result['resolved_ip']}")

    sys.exit(0 if result['is_safe'] else 1)


if __name__ == '__main__':
    main()
