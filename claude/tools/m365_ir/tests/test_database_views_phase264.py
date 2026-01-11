#!/usr/bin/env python3
"""
Tests for Phase 264 Database Views
Tests multi-schema ETL database views for Graph API data.

Views tested:
- v_graph_interactive_signins: Interactive/NonInteractive Graph API sign-ins
- v_service_principal_signins: Service principal authentication
- v_signin_performance: Latency analysis

Created: 2026-01-11
Phase: 264 Sprint 2.3
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from claude.tools.m365_ir.log_database import IRLogDatabase


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def db(temp_dir):
    """Create test database with Phase 264 schema."""
    db = IRLogDatabase(case_id="TEST-VIEWS-001", base_path=str(temp_dir))
    db.create()

    # Insert test data covering all schema variants
    conn = db.connect()
    cursor = conn.cursor()

    # Legacy Portal sign-in
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, ip_address,
         location_city, location_country, app_display_name, browser, os,
         status_error_code, conditional_access_status, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T10:00:00',
        'user1@example.com',
        'User One',
        '192.168.1.1',
        'Sydney',
        'Australia',
        'Office 365',
        'Chrome',
        'Windows',
        0,
        'success',
        datetime.now().isoformat(),
        'legacy_portal',
        'interactive',
        0
    ))

    # Graph Interactive sign-in with full Phase 264 fields
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, user_id, ip_address,
         location_city, location_country, client_app, app_display_name,
         browser, os, device_compliant, device_managed, status_error_code,
         conditional_access_status, auth_requirement, mfa_result, latency_ms,
         request_id, correlation_id, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T11:00:00',
        'user2@example.com',
        'User Two',
        'user-id-123',
        '10.0.0.1',
        'Melbourne',
        'Australia',
        'Browser',
        'SharePoint',
        'Edge',
        'Windows',
        1,
        1,
        0,
        'success',
        'singleFactorAuthentication',
        'satisfied',
        150,
        'req-123',
        'corr-123',
        datetime.now().isoformat(),
        'graph_interactive',
        'interactive',
        0
    ))

    # Graph NonInteractive sign-in
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, user_display_name, user_id, ip_address,
         location_city, location_country, app_display_name, latency_ms,
         request_id, status_error_code, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T12:00:00',
        'user3@example.com',
        'User Three',
        'user-id-456',
        '10.0.0.2',
        'Brisbane',
        'Australia',
        'Azure AD',
        50,
        'req-456',
        0,
        datetime.now().isoformat(),
        'graph_noninteractive',
        'noninteractive',
        0
    ))

    # Graph Application (Service Principal) sign-in
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country,
         app_display_name, service_principal_id, service_principal_name,
         credential_key_id, latency_ms, request_id, status_error_code,
         imported_at, schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T13:00:00',
        '',  # Service principals have no user
        '40.88.0.1',
        'United States',
        'Azure DevOps',
        'sp-id-789',
        'DevOps Agent',
        'key-abc123',
        200,
        'req-789',
        0,
        datetime.now().isoformat(),
        'graph_application',
        'service_principal',
        1
    ))

    # Graph Application (Service Principal) - slow sign-in
    cursor.execute("""
        INSERT INTO sign_in_logs
        (timestamp, user_principal_name, ip_address, location_country,
         app_display_name, service_principal_id, service_principal_name,
         latency_ms, request_id, status_error_code, imported_at,
         schema_variant, sign_in_type, is_service_principal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '2025-01-01T14:00:00',
        '',
        '40.88.0.2',
        'United States',
        'PowerShell',
        'sp-id-999',
        'Automation Account',
        1500,  # Very slow
        'req-999',
        0,
        datetime.now().isoformat(),
        'graph_application',
        'service_principal',
        1
    ))

    conn.commit()
    conn.close()

    yield db


class TestGraphInteractiveSigninsView:
    """Tests for v_graph_interactive_signins view."""

    def test_view_exists(self, db):
        """Should create v_graph_interactive_signins view."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_graph_interactive_signins'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'v_graph_interactive_signins'

    def test_view_filters_graph_only(self, db):
        """Should only show Graph API Interactive/NonInteractive sign-ins."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM v_graph_interactive_signins")
        count = cursor.fetchone()[0]
        conn.close()

        # Should return 2 records (graph_interactive + graph_noninteractive)
        # NOT the legacy_portal or graph_application records
        assert count == 2

    def test_view_includes_phase_264_fields(self, db):
        """Should include Phase 264 fields (user_id, latency_ms, etc)."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, latency_ms, device_compliant, auth_requirement, mfa_result
            FROM v_graph_interactive_signins
            WHERE schema_variant = 'graph_interactive'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['user_id'] == 'user-id-123'
        assert row['latency_ms'] == 150
        assert row['device_compliant'] == 1
        assert row['auth_requirement'] == 'singleFactorAuthentication'
        assert row['mfa_result'] == 'satisfied'

    def test_view_ordered_by_timestamp_desc(self, db):
        """Should order results by timestamp descending."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM v_graph_interactive_signins
            LIMIT 2
        """)
        rows = cursor.fetchall()
        conn.close()

        # First row should be newer than second
        assert rows[0]['timestamp'] > rows[1]['timestamp']


class TestServicePrincipalSigninsView:
    """Tests for v_service_principal_signins view."""

    def test_view_exists(self, db):
        """Should create v_service_principal_signins view."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_service_principal_signins'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_view_filters_service_principals_only(self, db):
        """Should only show service principal sign-ins."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM v_service_principal_signins")
        count = cursor.fetchone()[0]
        conn.close()

        # Should return 2 service principal records only
        assert count == 2

    def test_view_includes_sp_specific_fields(self, db):
        """Should include service_principal_id, service_principal_name, credential_key_id."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT service_principal_id, service_principal_name, credential_key_id
            FROM v_service_principal_signins
            WHERE service_principal_id = 'sp-id-789'
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['service_principal_id'] == 'sp-id-789'
        assert row['service_principal_name'] == 'DevOps Agent'
        assert row['credential_key_id'] == 'key-abc123'

    def test_view_excludes_user_sign_ins(self, db):
        """Should not include user sign-ins (interactive/noninteractive)."""
        conn = db.connect()
        cursor = conn.cursor()

        # Check that all records are service principals (should have sp_id)
        cursor.execute("""
            SELECT COUNT(*) FROM v_service_principal_signins
            WHERE service_principal_id IS NOT NULL
        """)
        sp_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM v_service_principal_signins")
        total_count = cursor.fetchone()[0]
        conn.close()

        # All records should have service_principal_id
        assert sp_count == total_count
        assert total_count == 2  # Both test SPs


class TestSigninPerformanceView:
    """Tests for v_signin_performance view."""

    def test_view_exists(self, db):
        """Should create v_signin_performance view."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_signin_performance'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_view_categorizes_latency(self, db):
        """Should categorize latency into FAST/NORMAL/SLOW/VERY_SLOW."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT latency_ms, latency_category
            FROM v_signin_performance
            ORDER BY latency_ms
        """)
        rows = cursor.fetchall()
        conn.close()

        # Verify categorization logic
        categories = {row['latency_ms']: row['latency_category'] for row in rows}

        assert categories[50] == 'FAST'        # < 100ms
        assert categories[150] == 'NORMAL'     # 100-500ms
        assert categories[200] == 'NORMAL'     # 100-500ms
        assert categories[1500] == 'VERY_SLOW' # >= 1000ms

    def test_view_calculates_success_flag(self, db):
        """Should calculate is_success flag (1 if error_code = 0/NULL)."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status_error_code, is_success
            FROM v_signin_performance
            WHERE latency_ms = 150
        """)
        row = cursor.fetchone()
        conn.close()

        assert row['status_error_code'] == 0
        assert row['is_success'] == 1

    def test_view_ordered_by_latency_desc(self, db):
        """Should order by latency descending (slowest first)."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT latency_ms FROM v_signin_performance
            LIMIT 2
        """)
        rows = cursor.fetchall()
        conn.close()

        # First row should have higher latency
        assert rows[0]['latency_ms'] >= rows[1]['latency_ms']

    def test_view_filters_null_latency(self, db):
        """Should only include records with non-null latency."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM v_signin_performance
            WHERE latency_ms IS NULL
        """)
        count = cursor.fetchone()[0]
        conn.close()

        # No NULL latency records should appear
        assert count == 0


class TestViewIntegration:
    """Integration tests for Phase 264 views."""

    def test_all_views_created(self, db):
        """Should create all 3 Phase 264 views."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view'
            AND name IN (
                'v_graph_interactive_signins',
                'v_service_principal_signins',
                'v_signin_performance'
            )
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert len(views) == 3
        assert 'v_graph_interactive_signins' in views
        assert 'v_service_principal_signins' in views
        assert 'v_signin_performance' in views

    def test_views_no_data_overlap(self, db):
        """Graph Interactive and Service Principal views should have no overlap."""
        conn = db.connect()
        cursor = conn.cursor()

        # Count records in each view
        cursor.execute("SELECT COUNT(*) FROM v_graph_interactive_signins")
        graph_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM v_service_principal_signins")
        sp_count = cursor.fetchone()[0]

        conn.close()

        # Should be different counts (no overlap)
        assert graph_count == 2
        assert sp_count == 2
        assert graph_count + sp_count <= 5  # Total test records
