#!/usr/bin/env python3
"""
TDD Tests for IR Knowledge Base (ir_knowledge.py)

Tests written BEFORE implementation per TDD methodology.
Phase 224 - IR Automation Tools

Run: python3 -m pytest test_ir_knowledge.py -v
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime

# Import will fail until implementation exists - this is expected in TDD
try:
    from ir_knowledge import IRKnowledgeBase
except ImportError:
    IRKnowledgeBase = None


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
    """Create a knowledge base instance with temp database."""
    if IRKnowledgeBase is None:
        pytest.skip("IRKnowledgeBase not yet implemented")
    return IRKnowledgeBase(temp_db)


class TestInvestigations:
    """Test investigation management (KB-001, KB-010)."""

    def test_kb_001_create_investigation(self, kb):
        """KB-001: Create new investigation record."""
        inv_id = kb.create_investigation(
            investigation_id="PIR-FYNA-2025-001",
            customer="Fyna Foods",
            tenant="fynafoods.onmicrosoft.com",
            status="OPEN"
        )

        assert inv_id is not None
        assert inv_id == "PIR-FYNA-2025-001"

    def test_kb_001_investigation_has_required_fields(self, kb):
        """KB-001: Investigation record has all required fields."""
        kb.create_investigation(
            investigation_id="PIR-TEST-001",
            customer="Test Customer",
            tenant="test.onmicrosoft.com"
        )

        inv = kb.get_investigation("PIR-TEST-001")

        assert inv is not None
        assert inv['investigation_id'] == "PIR-TEST-001"
        assert inv['customer'] == "Test Customer"
        assert inv['tenant'] == "test.onmicrosoft.com"
        assert 'created_date' in inv
        assert 'status' in inv

    def test_kb_010_get_investigation_summary(self, kb):
        """KB-010: Get investigation summary with counts."""
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")
        kb.add_ioc("PIR-TEST-001", "ip", "1.2.3.4", "Test IP")
        kb.add_ioc("PIR-TEST-001", "ip", "5.6.7.8", "Another IP")
        kb.add_pattern("PIR-TEST-001", "impossible_ua", "Safari.*Windows", 1.0)

        summary = kb.get_investigation_summary("PIR-TEST-001")

        assert summary['ioc_count'] == 2
        assert summary['pattern_count'] == 1


class TestIOCs:
    """Test IOC management (KB-002, KB-003)."""

    def test_kb_002_add_ioc_to_investigation(self, kb):
        """KB-002: Add IOC linked to investigation."""
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")

        ioc_id = kb.add_ioc(
            investigation_id="PIR-TEST-001",
            ioc_type="ip",
            value="97.93.69.128",
            context="Malicious - blocked attack",
            status="BLOCKED"
        )

        assert ioc_id is not None

    def test_kb_003_query_ioc_by_ip(self, kb):
        """KB-003: Query IOC by IP address returns all investigations."""
        # Create two investigations with same IP
        kb.create_investigation("PIR-TEST-001", "Customer A", "a.onmicrosoft.com")
        kb.create_investigation("PIR-TEST-002", "Customer B", "b.onmicrosoft.com")

        kb.add_ioc("PIR-TEST-001", "ip", "93.127.215.4", "Foreign access")
        kb.add_ioc("PIR-TEST-002", "ip", "93.127.215.4", "Suspicious IP")

        results = kb.query_ioc("ip", "93.127.215.4")

        assert len(results) == 2
        assert any(r['investigation_id'] == "PIR-TEST-001" for r in results)
        assert any(r['investigation_id'] == "PIR-TEST-002" for r in results)

    def test_kb_003_query_unknown_ip(self, kb):
        """KB-003: Query unknown IP returns empty list."""
        results = kb.query_ioc("ip", "1.1.1.1")

        assert results == []


class TestPatterns:
    """Test pattern management (KB-004, KB-005)."""

    def test_kb_004_add_suspicious_pattern(self, kb):
        """KB-004: Add suspicious pattern with confidence score."""
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")

        pattern_id = kb.add_pattern(
            investigation_id="PIR-TEST-001",
            pattern_type="impossible_ua",
            signature="Safari.*Windows",
            confidence=1.0,
            description="Safari on Windows is impossible"
        )

        assert pattern_id is not None

    def test_kb_005_query_patterns_by_type(self, kb):
        """KB-005: Query patterns by type returns all instances."""
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")
        kb.add_pattern("PIR-TEST-001", "impossible_ua", "Safari.*Windows", 1.0)
        kb.add_pattern("PIR-TEST-001", "off_hours", "consent.*0[0-5]:", 0.8)

        results = kb.query_patterns("impossible_ua")

        assert len(results) == 1
        assert results[0]['signature'] == "Safari.*Windows"
        assert results[0]['confidence'] == 1.0


class TestVerifiedApps:
    """Test verified app management (KB-006, KB-007)."""

    def test_kb_006_add_verified_app(self, kb):
        """KB-006: Add verified OAuth app."""
        app_id = kb.add_verified_app(
            app_id="00000003-0000-0000-c000-000000000000",
            name="Microsoft Graph",
            owner="Microsoft",
            permissions=["User.Read", "Mail.Read"],
            verification_date=datetime.now().isoformat()
        )

        assert app_id is not None

    def test_kb_007_check_app_verified_true(self, kb):
        """KB-007: Check verified app returns True with details."""
        kb.add_verified_app(
            app_id="test-app-id",
            name="Test App",
            owner="Orro",
            permissions=["User.Read"]
        )

        result = kb.is_app_verified("test-app-id")

        assert result['verified'] is True
        assert result['name'] == "Test App"
        assert result['owner'] == "Orro"

    def test_kb_007_check_app_verified_false(self, kb):
        """KB-007: Check unknown app returns False."""
        result = kb.is_app_verified("unknown-app-id")

        assert result['verified'] is False


class TestCustomerServices:
    """Test customer service mapping (KB-008, KB-009)."""

    def test_kb_008_add_customer_service(self, kb):
        """KB-008: Add customer service with expected IPs."""
        service_id = kb.add_customer_service(
            customer="Fyna Foods",
            service_name="Usemotion",
            expected_ips=["93.127.215.4"],
            verified=False,
            notes="zacd claims to use this service"
        )

        assert service_id is not None

    def test_kb_009_check_ip_matches_service(self, kb):
        """KB-009: Check if IP matches known service."""
        kb.add_customer_service(
            customer="Test Customer",
            service_name="Known Service",
            expected_ips=["10.0.0.1", "10.0.0.2"],
            verified=True
        )

        result = kb.check_ip_service("Test Customer", "10.0.0.1")

        assert result is not None
        assert result['service_name'] == "Known Service"
        assert result['verified'] is True

    def test_kb_009_check_ip_no_match(self, kb):
        """KB-009: Check unknown IP returns None."""
        result = kb.check_ip_service("Test Customer", "99.99.99.99")

        assert result is None


class TestDatabaseIntegrity:
    """Test database operations and integrity."""

    def test_database_created_on_init(self, temp_db):
        """Database file is created when IRKnowledgeBase is initialized."""
        if IRKnowledgeBase is None:
            pytest.skip("IRKnowledgeBase not yet implemented")

        kb = IRKnowledgeBase(temp_db)

        assert os.path.exists(temp_db)

    def test_schema_has_all_tables(self, kb):
        """Database schema has all required tables."""
        tables = kb.get_tables()

        required_tables = [
            'investigations',
            'iocs',
            'patterns',
            'verified_apps',
            'customer_services'
        ]

        for table in required_tables:
            assert table in tables, f"Missing table: {table}"

    def test_duplicate_investigation_raises_error(self, kb):
        """Creating duplicate investigation raises error."""
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")

        with pytest.raises(Exception):  # Could be ValueError or sqlite3.IntegrityError
            kb.create_investigation("PIR-TEST-001", "Test2", "test2.onmicrosoft.com")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
