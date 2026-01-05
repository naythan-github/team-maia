#!/usr/bin/env python3
"""
TDD Tests for WebFetch Security Gate (PreToolUse Hook)
Tests written BEFORE implementation (RED phase).

This hook validates WebFetch/WebSearch URLs BEFORE the fetch occurs,
blocking SSRF attacks, dangerous schemes, and blocklisted domains.
"""

import pytest
import json
import sys
from pathlib import Path

# Add security module to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWebFetchSecurityGate:
    """Test suite for WebFetchSecurityGate class"""

    def test_import(self):
        """Tool should be importable"""
        from webfetch_security_gate import WebFetchSecurityGate
        assert WebFetchSecurityGate is not None

    def test_instantiation(self):
        """Should create instance without errors"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()
        assert gate is not None

    def test_get_stats(self):
        """Should return statistics dict"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()
        stats = gate.get_stats()
        assert 'total_requests' in stats
        assert 'blocked_requests' in stats
        assert 'allowed_requests' in stats


class TestPreToolUseValidation:
    """Test PreToolUse validation logic"""

    def test_allow_valid_https_webfetch(self):
        """Should allow valid HTTPS WebFetch requests"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'https://example.com/article',
            'prompt': 'Summarize this article'
        })
        assert result['decision'] == 'allow'

    def test_allow_valid_http_webfetch(self):
        """Should allow valid HTTP WebFetch requests"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'http://example.com/page',
            'prompt': 'Read this page'
        })
        assert result['decision'] == 'allow'

    def test_block_javascript_scheme(self):
        """Should block javascript: URLs"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'javascript:alert(1)',
            'prompt': 'Execute this'
        })
        assert result['decision'] == 'block'
        assert 'scheme' in result['reason'].lower()

    def test_block_file_scheme(self):
        """Should block file: URLs"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'file:///etc/passwd',
            'prompt': 'Read this file'
        })
        assert result['decision'] == 'block'

    def test_block_data_scheme(self):
        """Should block data: URLs"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'data:text/html,<script>alert(1)</script>',
            'prompt': 'Process this'
        })
        assert result['decision'] == 'block'

    def test_block_ftp_scheme(self):
        """Should block ftp: URLs"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'ftp://ftp.example.com/file.txt',
            'prompt': 'Download this'
        })
        assert result['decision'] == 'block'


class TestSSRFBlocking:
    """Test SSRF blocking in PreToolUse hook"""

    def test_block_ssrf_localhost(self):
        """Should block SSRF to localhost"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'http://localhost:8080/admin',
            'prompt': 'Get admin page'
        })
        assert result['decision'] == 'block'
        assert result['threat_type'] == 'ssrf'

    def test_block_ssrf_127(self):
        """Should block SSRF to 127.0.0.1"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'http://127.0.0.1/api/internal',
            'prompt': 'Get internal API'
        })
        assert result['decision'] == 'block'
        assert result['threat_type'] == 'ssrf'

    def test_block_ssrf_private_ip(self):
        """Should block SSRF to private IPs"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        private_urls = [
            'http://192.168.1.1/config',
            'http://10.0.0.1/internal',
            'http://172.16.0.1/admin',
        ]
        for url in private_urls:
            result = gate.validate_request({
                'url': url,
                'prompt': 'Get internal resource'
            })
            assert result['decision'] == 'block', f"Should block: {url}"
            assert result['threat_type'] == 'ssrf'

    def test_block_ssrf_metadata(self):
        """Should block SSRF to cloud metadata"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'http://169.254.169.254/latest/meta-data/',
            'prompt': 'Get AWS credentials'
        })
        assert result['decision'] == 'block'


class TestHookInputOutput:
    """Test hook input/output format"""

    def test_process_pretool_input_format(self):
        """Should process PreToolUse hook input format"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebFetch',
            'tool_input': {
                'url': 'https://example.com',
                'prompt': 'Summarize'
            },
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        assert 'decision' in result
        assert result['decision'] in ['allow', 'block']

    def test_returns_reason_on_block(self):
        """Should return reason when blocking"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebFetch',
            'tool_input': {
                'url': 'http://127.0.0.1/admin',
                'prompt': 'Get admin'
            },
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        assert result['decision'] == 'block'
        assert 'reason' in result
        assert len(result['reason']) > 0

    def test_returns_checks_performed(self):
        """Should list checks performed"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebFetch',
            'tool_input': {
                'url': 'https://example.com',
                'prompt': 'Read'
            },
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        assert 'checks_performed' in result
        assert isinstance(result['checks_performed'], list)

    def test_handles_missing_url(self):
        """Should handle missing URL gracefully"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebFetch',
            'tool_input': {
                'prompt': 'Summarize'
                # Missing 'url'
            },
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        assert result['decision'] == 'block'
        assert 'url' in result['reason'].lower() or 'missing' in result['reason'].lower()

    def test_handles_empty_tool_input(self):
        """Should handle empty tool_input"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebFetch',
            'tool_input': {},
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        assert result['decision'] == 'block'


class TestWebSearchValidation:
    """Test WebSearch-specific validation"""

    def test_allow_valid_websearch(self):
        """Should allow valid WebSearch queries"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        # WebSearch has different input format - query instead of url
        result = gate.validate_request({
            'query': 'Python documentation 2024',
            'allowed_domains': ['python.org']
        })
        assert result['decision'] == 'allow'

    def test_websearch_no_url_validation_needed(self):
        """WebSearch with query only should pass (no URL to validate)"""
        from webfetch_security_gate import process_pretool_input

        hook_input = {
            'tool_name': 'WebSearch',
            'tool_input': {
                'query': 'best python frameworks 2024'
            },
            'session_id': 'test-123'
        }

        result = process_pretool_input(hook_input)
        # WebSearch doesn't have a URL to validate, should allow
        assert result['decision'] == 'allow'


class TestSchemeValidation:
    """Test URL scheme validation"""

    def test_check_scheme_https(self):
        """Should allow https scheme"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.check_scheme('https://example.com')
        assert result['is_safe']

    def test_check_scheme_http(self):
        """Should allow http scheme"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.check_scheme('http://example.com')
        assert result['is_safe']

    def test_check_scheme_javascript(self):
        """Should block javascript scheme"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.check_scheme('javascript:alert(1)')
        assert not result['is_safe']

    def test_check_scheme_data(self):
        """Should block data scheme"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.check_scheme('data:text/html,<h1>test</h1>')
        assert not result['is_safe']


class TestConfidenceScoring:
    """Test confidence scoring"""

    def test_high_confidence_on_ssrf(self):
        """Should return high confidence for SSRF attempts"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'http://127.0.0.1/admin',
            'prompt': 'Get admin'
        })
        assert result['decision'] == 'block'
        assert result['confidence'] >= 0.9

    def test_high_confidence_on_scheme_violation(self):
        """Should return high confidence for scheme violations"""
        from webfetch_security_gate import WebFetchSecurityGate
        gate = WebFetchSecurityGate()

        result = gate.validate_request({
            'url': 'javascript:evil()',
            'prompt': 'Execute'
        })
        assert result['decision'] == 'block'
        assert result['confidence'] >= 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
