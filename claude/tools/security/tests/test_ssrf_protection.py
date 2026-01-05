#!/usr/bin/env python3
"""
TDD Tests for SSRF Protection Module
Tests written BEFORE implementation (RED phase).

SSRF (Server-Side Request Forgery) protection prevents WebFetch from
accessing internal resources like localhost, private networks, and
cloud metadata endpoints.
"""

import pytest
import sys
from pathlib import Path

# Add security module to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSSRFProtection:
    """Test suite for SSRFProtection class"""

    def test_import(self):
        """Tool should be importable"""
        from ssrf_protection import SSRFProtection
        assert SSRFProtection is not None

    def test_instantiation(self):
        """Should create instance without errors"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        assert ssrf is not None

    def test_get_stats(self):
        """Should return statistics dict"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        stats = ssrf.get_stats()
        assert 'total_checked' in stats
        assert 'blocked' in stats
        assert 'allowed' in stats

    def test_check_url_returns_dict(self):
        """check_url should return properly structured dict"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("https://example.com")
        assert isinstance(result, dict)
        assert 'is_safe' in result
        assert 'reason' in result
        assert isinstance(result['is_safe'], bool)


class TestSSRFBlockingRules:
    """Test SSRF blocking rules for various internal addresses"""

    def test_block_localhost_127(self):
        """Should block 127.0.0.1"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://127.0.0.1/admin")
        assert not result['is_safe']
        assert result['threat_type'] == 'localhost'

    def test_block_localhost_127_any(self):
        """Should block any 127.x.x.x address"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://127.0.0.2:8080/api")
        assert not result['is_safe']

    def test_block_localhost_name(self):
        """Should block localhost hostname"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://localhost/admin")
        assert not result['is_safe']
        assert result['threat_type'] == 'localhost'

    def test_block_localhost_with_port(self):
        """Should block localhost with any port"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://localhost:8080/api")
        assert not result['is_safe']

    def test_block_private_10_network(self):
        """Should block 10.0.0.0/8 private network"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        private_ips = [
            "http://10.0.0.1/internal",
            "http://10.255.255.255/api",
            "http://10.100.50.25:3000/data",
        ]
        for url in private_ips:
            result = ssrf.check_url(url)
            assert not result['is_safe'], f"Should block: {url}"
            assert result['is_private']

    def test_block_private_172_network(self):
        """Should block 172.16.0.0/12 private network"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        private_ips = [
            "http://172.16.0.1/internal",
            "http://172.31.255.255/api",
            "http://172.20.10.5:8080/data",
        ]
        for url in private_ips:
            result = ssrf.check_url(url)
            assert not result['is_safe'], f"Should block: {url}"

    def test_block_private_192_network(self):
        """Should block 192.168.0.0/16 private network"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        private_ips = [
            "http://192.168.1.1/router",
            "http://192.168.0.1/admin",
            "http://192.168.255.255:443/api",
        ]
        for url in private_ips:
            result = ssrf.check_url(url)
            assert not result['is_safe'], f"Should block: {url}"

    def test_block_cloud_metadata_aws(self):
        """Should block AWS metadata endpoint 169.254.169.254"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://169.254.169.254/latest/meta-data/")
        assert not result['is_safe']

    def test_block_cloud_metadata_gcp(self):
        """Should block GCP metadata endpoint"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://metadata.google.internal/computeMetadata/v1/")
        assert not result['is_safe']

    def test_block_link_local(self):
        """Should block link-local addresses 169.254.x.x"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://169.254.1.1/api")
        assert not result['is_safe']

    def test_block_ipv6_localhost(self):
        """Should block IPv6 localhost [::1]"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://[::1]/admin")
        assert not result['is_safe']

    def test_block_ipv6_loopback(self):
        """Should block IPv6 loopback variations"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://[0:0:0:0:0:0:0:1]/admin")
        assert not result['is_safe']


class TestSSRFAllowRules:
    """Test that legitimate public URLs are allowed"""

    def test_allow_public_https(self):
        """Should allow legitimate public HTTPS URLs"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        public_urls = [
            "https://example.com",
            "https://github.com/user/repo",
            "https://api.openai.com/v1/chat",
            "https://www.google.com/search?q=test",
        ]
        for url in public_urls:
            result = ssrf.check_url(url, resolve_dns=False)
            assert result['is_safe'], f"Should allow: {url}"

    def test_allow_public_http(self):
        """Should allow public HTTP URLs (even if less secure)"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://example.com/page", resolve_dns=False)
        assert result['is_safe']

    def test_allow_public_ip(self):
        """Should allow legitimate public IP addresses"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        # 8.8.8.8 is Google's public DNS
        result = ssrf.check_url("https://8.8.8.8/dns-query")
        assert result['is_safe']


class TestSSRFEdgeCases:
    """Test SSRF edge cases and bypass attempts"""

    def test_block_decimal_ip(self):
        """Should block decimal IP encoding (2130706433 = 127.0.0.1)"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        # 2130706433 = 127.0.0.1 in decimal
        result = ssrf.check_url("http://2130706433/admin")
        assert not result['is_safe']

    def test_block_octal_ip(self):
        """Should block octal IP encoding (0177.0.0.1 = 127.0.0.1)"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://0177.0.0.1/admin")
        assert not result['is_safe']

    def test_block_hex_ip(self):
        """Should block hex IP encoding (0x7f000001 = 127.0.0.1)"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://0x7f000001/admin")
        assert not result['is_safe']

    def test_block_url_with_credentials(self):
        """Should handle URLs with embedded credentials"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://user:pass@127.0.0.1/admin")
        assert not result['is_safe']

    def test_block_zero_ip(self):
        """Should block 0.0.0.0"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("http://0.0.0.0/admin")
        assert not result['is_safe']

    def test_handle_invalid_url(self):
        """Should handle invalid URLs gracefully"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("not-a-valid-url")
        assert not result['is_safe']
        # Accept various error indicators
        reason_lower = result['reason'].lower()
        assert any(x in reason_lower for x in ['invalid', 'error', 'hostname', 'no'])

    def test_handle_empty_url(self):
        """Should handle empty URL"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url("")
        assert not result['is_safe']

    def test_handle_none_url(self):
        """Should handle None URL"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()
        result = ssrf.check_url(None)
        assert not result['is_safe']


class TestSSRFCustomBlocklist:
    """Test custom domain blocklist functionality"""

    def test_custom_blocklist_blocks_domain(self):
        """Should respect custom domain blocklist"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection(custom_blocklist=["evil.com", "malware.net"])
        result = ssrf.check_url("https://evil.com/payload")
        assert not result['is_safe']
        assert result['threat_type'] == 'blocked_domain'

    def test_custom_blocklist_blocks_subdomain(self):
        """Should block subdomains of blocklisted domains"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection(custom_blocklist=["evil.com"])
        result = ssrf.check_url("https://api.evil.com/data")
        assert not result['is_safe']

    def test_custom_blocklist_allows_unlisted(self):
        """Should allow domains not on blocklist"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection(custom_blocklist=["evil.com"])
        result = ssrf.check_url("https://good.com/api", resolve_dns=False)
        assert result['is_safe']


class TestSSRFHelperMethods:
    """Test helper methods"""

    def test_is_private_ip_true(self):
        """is_private_ip should return True for private IPs"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        private_ips = ["10.0.0.1", "172.16.0.1", "192.168.1.1", "127.0.0.1"]
        for ip in private_ips:
            assert ssrf.is_private_ip(ip), f"Should be private: {ip}"

    def test_is_private_ip_false(self):
        """is_private_ip should return False for public IPs"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        public_ips = ["8.8.8.8", "1.1.1.1", "93.184.216.34"]
        for ip in public_ips:
            assert not ssrf.is_private_ip(ip), f"Should be public: {ip}"

    def test_is_localhost_true(self):
        """is_localhost should identify localhost variations"""
        from ssrf_protection import SSRFProtection
        ssrf = SSRFProtection()

        localhost_names = ["localhost", "127.0.0.1", "::1"]
        for name in localhost_names:
            assert ssrf.is_localhost(name), f"Should be localhost: {name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
