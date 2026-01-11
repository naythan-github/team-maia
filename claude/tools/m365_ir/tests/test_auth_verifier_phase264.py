#!/usr/bin/env python3
"""
Tests for Phase 264 Auth Verifier Enhancements
Tests multi-schema authentication verification (Graph API status codes, service principals).

Created: 2026-01-11
Phase: 264 Sprint 3.1
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.auth_verifier import (
    verify_sign_in_status,
    verify_service_principal_status,
    verify_latency_patterns,
    verify_device_compliance,
    verify_mfa_status
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def db_with_graph_data(temp_dir):
    """Create test database with Graph API sign-in data."""
    db = IRLogDatabase(case_id="TEST-GRAPH-001", base_path=str(temp_dir))
    db.create()

    conn = db.connect()
    cursor = conn.cursor()

    # Graph Interactive sign-in - SUCCESS (status_error_code = 0)
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, ip_address,
         location_city, location_country, app_display_name,
         status_error_code, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T10:00:00',
        'user1@example.com',
        'User One',
        '192.168.1.1',
        'Sydney',
        'Australia',
        'Office 365',
        0,  # Graph API: 0 = success
        datetime.now().isoformat(),
        'graph_interactive',
        'interactive',
        0
    ))

    # Graph Interactive sign-in - FAILED (status_error_code = 50126)
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, ip_address,
         location_city, location_country, app_display_name,
         status_error_code, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T11:00:00',
        'user2@example.com',
        'User Two',
        '10.0.0.1',
        'Melbourne',
        'Australia',
        'SharePoint',
        50126,  # Graph API: 50126 = invalid credentials (FAILED)
        datetime.now().isoformat(),
        'graph_interactive',
        'interactive',
        0
    ))

    # Graph Interactive sign-in - SUCCESS
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, ip_address,
         location_city, location_country, app_display_name,
         status_error_code, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T12:00:00',
        'user3@example.com',
        'User Three',
        '10.0.0.2',
        'Brisbane',
        'Australia',
        'Azure AD',
        0,  # SUCCESS
        datetime.now().isoformat(),
        'graph_interactive',
        'interactive',
        0
    ))

    conn.commit()
    conn.close()

    yield db


class TestGraphAPIStatusCodeSupport:
    """Tests for Feature 3.1.1: Graph API Status Code Support."""

    def test_verify_graph_api_integer_status_codes(self, db_with_graph_data):
        """Should handle Graph API integer status codes (0 vs '0')."""
        db_path = str(db_with_graph_data.db_path)
        result = verify_sign_in_status(db_path)

        # Should use status_error_code field for Graph API data
        assert result.status_field_used == 'status_error_code'

        # Should correctly count successes and failures
        assert result.total_records == 3
        assert result.success_count == 2  # 2 with status_error_code = 0
        assert result.failure_count == 1  # 1 with status_error_code = 50126
        assert result.success_rate == pytest.approx(66.7, rel=0.1)

    def test_detect_graph_api_schema_variant(self, db_with_graph_data):
        """Should detect when data is Graph API vs Legacy Portal."""
        db_path = str(db_with_graph_data.db_path)
        result = verify_sign_in_status(db_path)

        # Should detect Graph API schema
        assert 'graph' in result.status_field_used or 'error_code' in result.status_field_used

    def test_handle_mixed_schema_data(self, temp_dir):
        """Should handle database with both Graph API and Legacy Portal data."""
        db = IRLogDatabase(case_id="TEST-MIXED-001", base_path=str(temp_dir))
        db.create()

        conn = db.connect()
        cursor = conn.cursor()

        # Legacy Portal sign-in (stored as status_error_code = 0 after import)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T10:00:00',
            'legacy@example.com',
            '192.168.1.1',
            'Australia',
            'Office 365',
            0,  # Legacy Portal: normalized to 0
            datetime.now().isoformat(),
            'legacy_portal',
            'interactive',
            0
        ))

        # Graph API sign-in (status_error_code = 0 integer)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T11:00:00',
            'graph@example.com',
            '10.0.0.1',
            'Australia',
            'SharePoint',
            0,  # Graph API: integer 0
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        conn.commit()
        conn.close()

        # Should auto-select most reliable field
        result = verify_sign_in_status(str(db.db_path))
        assert result.total_records == 2
        assert result.success_count == 2  # Both successful


class TestServicePrincipalVerification:
    """Tests for Feature 3.1.2: Service Principal Verification."""

    @pytest.fixture
    def db_with_sp_data(self, temp_dir):
        """Database with service principal sign-ins."""
        db = IRLogDatabase(case_id="TEST-SP-001", base_path=str(temp_dir))
        db.create()

        conn = db.connect()
        cursor = conn.cursor()

        # User sign-in (interactive)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T10:00:00',
            'user@example.com',
            '192.168.1.1',
            'Australia',
            'Office 365',
            0,
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0  # Not a service principal
        ))

        # Service principal sign-in (successful)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country, app_display_name,
             service_principal_id, service_principal_name, status_error_code,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T11:00:00',
            '',  # Service principals have no user_principal_name
            '40.88.0.1',
            'United States',
            'Azure DevOps',
            'sp-id-123',
            'DevOps Agent',
            0,  # SUCCESS
            datetime.now().isoformat(),
            'graph_application',
            'service_principal',
            1  # IS a service principal
        ))

        # Service principal sign-in (failed)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country, app_display_name,
             service_principal_id, service_principal_name, status_error_code,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T12:00:00',
            '',  # Service principals have no user_principal_name
            '40.88.0.2',
            'United States',
            'PowerShell',
            'sp-id-456',
            'Automation Account',
            70021,  # Certificate credentials have expired
            datetime.now().isoformat(),
            'graph_application',
            'service_principal',
            1
        ))

        conn.commit()
        conn.close()

        yield db

    def test_verify_service_principal_sign_ins(self, db_with_sp_data):
        """Should verify service principal authentications separately from users."""
        db_path = str(db_with_sp_data.db_path)
        result = verify_service_principal_status(db_path)

        # Should separate user vs SP auth
        assert result.total_sp_signins == 2
        assert result.total_user_signins == 1

        # Should calculate separate success rates
        assert result.sp_success_count == 1
        assert result.sp_failure_count == 1
        assert result.sp_success_rate == pytest.approx(50.0, rel=0.1)

    def test_count_unique_service_principals(self, db_with_sp_data):
        """Should count unique service principals."""
        db_path = str(db_with_sp_data.db_path)
        result = verify_service_principal_status(db_path)

        assert result.unique_service_principals == 2  # sp-id-123, sp-id-456

    def test_service_principal_by_application(self, db_with_sp_data):
        """Should break down SP auth by application."""
        db_path = str(db_with_sp_data.db_path)
        result = verify_service_principal_status(db_path)

        assert hasattr(result, 'by_application')
        assert 'Azure DevOps' in result.by_application
        assert 'PowerShell' in result.by_application


# Placeholder for Features 3.1.3, 3.1.4, 3.1.5
# Will implement after Feature 3.1.1 and 3.1.2 pass

class TestLatencyVerification:
    """Tests for Feature 3.1.3: Latency Performance Verification."""

    def test_verify_signin_latency_patterns(self):
        """TODO: Should detect slow sign-in patterns (potential attack)."""
        pytest.skip("Feature 3.1.3 not yet implemented")


class TestDeviceComplianceVerification:
    """Tests for Feature 3.1.4: Device Compliance Verification."""

    def test_verify_device_compliance(self):
        """TODO: Should verify device compliance rates."""
        pytest.skip("Feature 3.1.4 not yet implemented")


class TestMFAVerification:
    """Tests for Feature 3.1.5: MFA Requirement Verification."""

    def test_verify_mfa_requirements(self):
        """TODO: Should verify MFA requirement vs actual MFA usage."""
        pytest.skip("Feature 3.1.5 not yet implemented")
