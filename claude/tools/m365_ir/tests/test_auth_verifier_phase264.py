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


class TestLatencyVerification:
    """Tests for Feature 3.1.3: Latency Performance Verification."""

    @pytest.fixture
    def db_with_latency_data(self, temp_dir):
        """Database with sign-in latency data."""
        db = IRLogDatabase(case_id="TEST-LATENCY-001", base_path=str(temp_dir))
        db.create()

        conn = db.connect()
        cursor = conn.cursor()

        # Fast sign-in (<100ms)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, latency_ms, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T10:00:00',
            'fast@example.com',
            '192.168.1.1',
            'Australia',
            'Office 365',
            0,
            50,  # 50ms - FAST
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Normal sign-in (100-500ms)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, latency_ms, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T11:00:00',
            'normal@example.com',
            '192.168.1.2',
            'Australia',
            'SharePoint',
            0,
            250,  # 250ms - NORMAL
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Slow sign-in (500-1000ms)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, latency_ms, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T12:00:00',
            'slow@example.com',
            '192.168.1.3',
            'Australia',
            'Teams',
            0,
            800,  # 800ms - SLOW
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Very slow sign-in (>5000ms)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, latency_ms, imported_at,
             schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T13:00:00',
            'veryslow@example.com',
            '192.168.1.4',
            'Australia',
            'Outlook',
            0,
            6000,  # 6000ms - VERY SLOW (>5000ms threshold)
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        conn.commit()
        conn.close()

        yield db

    def test_verify_signin_latency_patterns(self, db_with_latency_data):
        """Should detect slow sign-in patterns (potential attack)."""
        db_path = str(db_with_latency_data.db_path)
        result = verify_latency_patterns(db_path)

        # Should calculate latency metrics
        assert result.total_with_latency == 4
        assert result.avg_latency_ms > 0
        assert result.median_latency_ms > 0
        assert result.p95_latency_ms > 0

    def test_latency_categorization(self, db_with_latency_data):
        """Should categorize latencies correctly."""
        db_path = str(db_with_latency_data.db_path)
        result = verify_latency_patterns(db_path)

        # Should have breakdown by category
        assert hasattr(result, 'latency_categories')
        assert 'FAST' in result.latency_categories
        assert 'NORMAL' in result.latency_categories
        assert 'SLOW' in result.latency_categories
        assert 'VERY_SLOW' in result.latency_categories

        # Should match our test data
        assert result.latency_categories['FAST'] == 1
        assert result.latency_categories['NORMAL'] == 1
        assert result.latency_categories['SLOW'] == 1
        assert result.latency_categories['VERY_SLOW'] == 1

    def test_detect_slow_signin_count(self, db_with_latency_data):
        """Should count slow and very slow sign-ins."""
        db_path = str(db_with_latency_data.db_path)
        result = verify_latency_patterns(db_path)

        assert result.slow_signin_count == 1  # SLOW category
        assert result.very_slow_signin_count == 1  # VERY_SLOW category


class TestDeviceComplianceVerification:
    """Tests for Feature 3.1.4: Device Compliance Verification."""

    @pytest.fixture
    def db_with_device_data(self, temp_dir):
        """Database with device compliance data."""
        db = IRLogDatabase(case_id="TEST-DEVICE-001", base_path=str(temp_dir))
        db.create()

        conn = db.connect()
        cursor = conn.cursor()

        # Compliant + Managed device
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, device_compliant, device_managed,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T10:00:00',
            'compliant@example.com',
            '192.168.1.1',
            'Australia',
            'Office 365',
            0,
            1,  # Compliant
            1,  # Managed
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Non-compliant + Managed device
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, device_compliant, device_managed,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T11:00:00',
            'noncompliant@example.com',
            '192.168.1.2',
            'Australia',
            'SharePoint',
            0,
            0,  # Non-compliant
            1,  # Managed
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Non-compliant + Unmanaged device
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, device_compliant, device_managed,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T12:00:00',
            'unmanaged@example.com',
            '192.168.1.3',
            'Australia',
            'Teams',
            0,
            0,  # Non-compliant
            0,  # Unmanaged
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        conn.commit()
        conn.close()

        yield db

    def test_verify_device_compliance(self, db_with_device_data):
        """Should verify device compliance rates."""
        db_path = str(db_with_device_data.db_path)
        result = verify_device_compliance(db_path)

        # Should count devices correctly
        assert result.total_with_device_info == 3
        assert result.compliant_count == 1
        assert result.noncompliant_count == 2
        assert result.compliance_rate == pytest.approx(33.3, rel=0.1)

    def test_device_management_status(self, db_with_device_data):
        """Should track managed vs unmanaged devices."""
        db_path = str(db_with_device_data.db_path)
        result = verify_device_compliance(db_path)

        assert result.managed_count == 2  # 2 managed
        assert result.unmanaged_count == 1  # 1 unmanaged


class TestMFAVerification:
    """Tests for Feature 3.1.5: MFA Requirement Verification."""

    @pytest.fixture
    def db_with_mfa_data(self, temp_dir):
        """Database with MFA status data."""
        db = IRLogDatabase(case_id="TEST-MFA-001", base_path=str(temp_dir))
        db.create()

        conn = db.connect()
        cursor = conn.cursor()

        # MFA required and satisfied (real Graph API values)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, auth_requirement, mfa_result,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T10:00:00',
            'mfa_satisfied@example.com',
            '192.168.1.1',
            'Australia',
            'Office 365',
            0,
            'Multifactor authentication',  # Real Graph API value
            'MFA requirement satisfied by claim in the token',  # Real Graph API value
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # MFA required but NOT satisfied (security gap!)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, auth_requirement, mfa_result,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T11:00:00',
            'mfa_gap@example.com',
            '192.168.1.2',
            'Australia',
            'SharePoint',
            0,
            'Multifactor authentication',  # MFA required
            "The user didn't enter the right credentials",  # Real error message - GAP!
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        # Single factor auth (no MFA required)
        cursor.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_country,
             app_display_name, status_error_code, auth_requirement, mfa_result,
             imported_at, schema_variant, sign_in_type, is_service_principal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-01-01T12:00:00',
            'single_factor@example.com',
            '192.168.1.3',
            'Australia',
            'Teams',
            0,
            'Single-factor authentication',  # Real Graph API value
            None,  # No MFA result
            datetime.now().isoformat(),
            'graph_interactive',
            'interactive',
            0
        ))

        conn.commit()
        conn.close()

        yield db

    def test_verify_mfa_requirements(self, db_with_mfa_data):
        """Should verify MFA requirement vs actual MFA usage."""
        db_path = str(db_with_mfa_data.db_path)
        result = verify_mfa_status(db_path)

        # Should count MFA requirements
        assert result.total_signins == 3
        assert result.mfa_required_count == 2  # 2 required MFA
        assert result.mfa_satisfied_count == 1  # 1 satisfied
        assert result.mfa_gap_count == 1  # 1 gap (required but not satisfied)

    def test_detect_mfa_gaps(self, db_with_mfa_data):
        """Should detect MFA security gaps (required but not satisfied)."""
        db_path = str(db_with_mfa_data.db_path)
        result = verify_mfa_status(db_path)

        # Gap = required but not satisfied = security risk
        assert result.mfa_gap_count == 1
        assert len(result.warnings) > 0  # Should warn about gaps
