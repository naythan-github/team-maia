#!/usr/bin/env python3
"""
TDD Tests for IR Knowledge Query Tool (ir_knowledge_query.py)

Tests written BEFORE implementation per TDD methodology.
Phase 224 - IR Automation Tools

Run: python3 -m pytest test_ir_knowledge_query.py -v
"""

import pytest
import tempfile
import os
import subprocess
import sys

try:
    from ir_knowledge import IRKnowledgeBase
except ImportError:
    IRKnowledgeBase = None

try:
    from ir_knowledge_query import query_ip, query_app, query_pattern, query_service, get_stats
except ImportError:
    query_ip = None
    query_app = None
    query_pattern = None
    query_service = None
    get_stats = None


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def kb(temp_db):
    """Create a knowledge base instance with test data."""
    if IRKnowledgeBase is None:
        pytest.skip("IRKnowledgeBase not yet implemented")

    kb = IRKnowledgeBase(temp_db)

    # Add test investigation
    kb.create_investigation("PIR-FYNA-2025-001", "Fyna Foods", "fynafoods.onmicrosoft.com")

    # Add test IOCs
    kb.add_ioc("PIR-FYNA-2025-001", "ip", "97.93.69.128", "Malicious - rodneyt attack", "BLOCKED")
    kb.add_ioc("PIR-FYNA-2025-001", "ip", "93.127.215.4", "zacd foreign access - Hostinger US", "MONITOR")

    # Add test patterns
    kb.add_pattern("PIR-FYNA-2025-001", "impossible_ua", "Safari.*Windows", 1.0, "Safari on Windows is impossible")
    kb.add_pattern("PIR-FYNA-2025-001", "off_hours_consent", "consent.*0[0-5]:", 0.8, "Off-hours consent")

    # Add verified app
    kb.add_verified_app(
        app_id="00000003-0000-0000-c000-000000000000",
        name="Microsoft Graph",
        owner="Microsoft",
        permissions=["User.Read", "Mail.Read"]
    )

    # Add customer service
    kb.add_customer_service(
        customer="Fyna Foods",
        service_name="Usemotion",
        expected_ips=["93.127.215.4"],
        verified=False,
        notes="zacd claims to use this service"
    )

    return kb


class TestIPQuery:
    """Test IP query functionality (KQ-001, KQ-002)."""

    def test_kq_001_query_known_malicious_ip(self, kb, temp_db):
        """KQ-001: Query known malicious IP returns MALICIOUS with context."""
        if query_ip is None:
            pytest.skip("query_ip not yet implemented")

        result = query_ip("97.93.69.128", temp_db)

        assert "MALICIOUS" in result or "BLOCKED" in result
        assert "rodneyt" in result.lower() or "PIR-FYNA" in result

    def test_kq_002_query_unknown_ip(self, kb, temp_db):
        """KQ-002: Query unknown IP returns UNKNOWN."""
        if query_ip is None:
            pytest.skip("query_ip not yet implemented")

        result = query_ip("1.1.1.1", temp_db)

        assert "UNKNOWN" in result or "not found" in result.lower()

    def test_query_monitored_ip(self, kb, temp_db):
        """Query monitored IP returns MONITOR status with details."""
        if query_ip is None:
            pytest.skip("query_ip not yet implemented")

        result = query_ip("93.127.215.4", temp_db)

        assert "MONITOR" in result or "Hostinger" in result
        assert "PIR-FYNA" in result or "Fyna" in result


class TestAppQuery:
    """Test app query functionality (KQ-003, KQ-004)."""

    def test_kq_003_query_verified_app(self, kb, temp_db):
        """KQ-003: Query verified app returns VERIFIED with permissions."""
        if query_app is None:
            pytest.skip("query_app not yet implemented")

        result = query_app("00000003-0000-0000-c000-000000000000", temp_db)

        assert "VERIFIED" in result
        assert "Microsoft Graph" in result or "Microsoft" in result

    def test_kq_004_query_unverified_app(self, kb, temp_db):
        """KQ-004: Query unverified/unknown app returns appropriate status."""
        if query_app is None:
            pytest.skip("query_app not yet implemented")

        result = query_app("683b8f3c-cc24-4eda-9fd3-bf7f29551704", temp_db)

        assert "UNKNOWN" in result or "UNVERIFIED" in result or "not found" in result.lower()


class TestPatternQuery:
    """Test pattern query functionality (KQ-005)."""

    def test_kq_005_query_known_pattern(self, kb, temp_db):
        """KQ-005: Query known pattern returns pattern details."""
        if query_pattern is None:
            pytest.skip("query_pattern not yet implemented")

        result = query_pattern("Safari.*Windows", temp_db)

        assert "impossible" in result.lower() or "100%" in result or "1.0" in result

    def test_query_unknown_pattern(self, kb, temp_db):
        """Query unknown pattern returns not found."""
        if query_pattern is None:
            pytest.skip("query_pattern not yet implemented")

        result = query_pattern("unknown_pattern_xyz", temp_db)

        assert "not found" in result.lower() or "UNKNOWN" in result


class TestServiceQuery:
    """Test customer service query functionality (KQ-006)."""

    def test_kq_006_query_customer_service(self, kb, temp_db):
        """KQ-006: Query customer service returns verification status."""
        if query_service is None:
            pytest.skip("query_service not yet implemented")

        result = query_service("Fyna Foods", "Usemotion", temp_db)

        assert "UNVERIFIED" in result or "NOT VERIFIED" in result.lower()
        assert "zacd" in result.lower() or "claims" in result.lower()

    def test_query_verified_service(self, kb, temp_db):
        """Query verified service returns VERIFIED."""
        if query_service is None:
            pytest.skip("query_service not yet implemented")

        # Add a verified service
        kb.add_customer_service(
            customer="Test Corp",
            service_name="Verified Service",
            expected_ips=["10.0.0.1"],
            verified=True,
            notes="Confirmed by IT"
        )

        result = query_service("Test Corp", "Verified Service", temp_db)

        assert "VERIFIED" in result

    def test_query_unknown_service(self, kb, temp_db):
        """Query unknown service returns not found."""
        if query_service is None:
            pytest.skip("query_service not yet implemented")

        result = query_service("Unknown Customer", "Unknown Service", temp_db)

        assert "not found" in result.lower() or "UNKNOWN" in result


class TestStats:
    """Test statistics functionality (KQ-007)."""

    def test_kq_007_get_statistics(self, kb, temp_db):
        """KQ-007: Get statistics returns counts for all tables."""
        if get_stats is None:
            pytest.skip("get_stats not yet implemented")

        result = get_stats(temp_db)

        # Should have counts for each entity type
        assert "Investigation" in result or "investigation" in result
        assert "IOC" in result or "ioc" in result
        assert "Pattern" in result or "pattern" in result
        assert "App" in result or "app" in result

        # Should show actual counts
        assert "1" in result  # 1 investigation
        assert "2" in result  # 2 IOCs


class TestCLI:
    """Test CLI interface (KQ-008)."""

    def test_kq_008_invalid_command(self, temp_db):
        """KQ-008: Invalid command returns usage help."""
        script_path = os.path.join(os.path.dirname(__file__), 'ir_knowledge_query.py')

        if not os.path.exists(script_path):
            pytest.skip("ir_knowledge_query.py not yet implemented")

        result = subprocess.run(
            [sys.executable, script_path, 'invalid_command'],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "help" in output.lower() or "invalid" in output.lower()

    def test_cli_no_args(self, temp_db):
        """CLI with no args shows usage."""
        script_path = os.path.join(os.path.dirname(__file__), 'ir_knowledge_query.py')

        if not os.path.exists(script_path):
            pytest.skip("ir_knowledge_query.py not yet implemented")

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "help" in output.lower()

    def test_cli_ip_command(self, kb, temp_db):
        """CLI ip command works correctly."""
        script_path = os.path.join(os.path.dirname(__file__), 'ir_knowledge_query.py')

        if not os.path.exists(script_path):
            pytest.skip("ir_knowledge_query.py not yet implemented")

        # Note: --db must come BEFORE the subcommand
        result = subprocess.run(
            [sys.executable, script_path, '--db', temp_db, 'ip', '97.93.69.128'],
            capture_output=True,
            text=True
        )

        output = result.stdout
        assert "MALICIOUS" in output or "BLOCKED" in output or "PIR-FYNA" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
