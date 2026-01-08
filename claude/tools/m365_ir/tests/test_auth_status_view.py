#!/usr/bin/env python3
"""
TDD Tests for Auth Success View (M365 IR Data Enhancements - Requirement 2)

Eliminates ambiguity in authentication status interpretation.
The field `conditional_access_status = 'notApplied'` does NOT mean
successful authentication - it means no CA policy evaluated the login.

Run: pytest claude/tools/m365_ir/tests/test_auth_status_view.py -v

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08 (PIR-FYNA-2025-12-08 lessons learned)
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import tempfile

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase


class TestAuthStatusView:
    """Tests for v_sign_in_auth_status view."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database with schema."""
        db = IRLogDatabase(case_id="TEST-AUTH-VIEW", base_path=str(tmp_path))
        db.create()
        return db

    def _insert_sign_in(
        self,
        db: IRLogDatabase,
        conditional_access_status: str = None,
        status_error_code: int = None,
        ip_address: str = "1.1.1.1",
        user: str = "test@example.com",
        browser: str = "Chrome",
        os: str = "Windows10"
    ) -> int:
        """Helper to insert a sign-in log record."""
        conn = db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                conditional_access_status, status_error_code,
                browser, os, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, user, ip_address, conditional_access_status, status_error_code, browser, os, now))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _query_auth_view(self, db: IRLogDatabase, row_id: int = None, ip: str = None) -> dict:
        """Query the auth status view."""
        conn = db.connect()
        cursor = conn.cursor()
        if row_id:
            cursor.execute("SELECT * FROM v_sign_in_auth_status WHERE id = ?", (row_id,))
        elif ip:
            cursor.execute("SELECT * FROM v_sign_in_auth_status WHERE ip_address = ?", (ip,))
        else:
            cursor.execute("SELECT * FROM v_sign_in_auth_status LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def test_view_exists_after_init(self, temp_db):
        """View should exist after database initialization."""
        conn = temp_db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name='v_sign_in_auth_status'
        """)
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "v_sign_in_auth_status view should exist"

    def test_confirmed_success_when_ca_success(self, temp_db):
        """CA status 'success' = CONFIRMED_SUCCESS."""
        row_id = self._insert_sign_in(temp_db, conditional_access_status='success')
        result = self._query_auth_view(temp_db, row_id=row_id)

        assert result['auth_determination'] == 'CONFIRMED_SUCCESS'
        assert result['auth_confidence_pct'] == 100

    def test_ca_blocked_when_ca_failure(self, temp_db):
        """CA status 'failure' = CA_BLOCKED."""
        row_id = self._insert_sign_in(temp_db, conditional_access_status='failure')
        result = self._query_auth_view(temp_db, row_id=row_id)

        assert result['auth_determination'] == 'CA_BLOCKED'
        assert result['auth_confidence_pct'] == 100

    def test_likely_success_when_notapplied_no_error(self, temp_db):
        """CA status 'notApplied' with no error = LIKELY_SUCCESS_NO_CA."""
        row_id = self._insert_sign_in(
            temp_db,
            conditional_access_status='notApplied',
            status_error_code=0
        )
        result = self._query_auth_view(temp_db, row_id=row_id)

        assert result['auth_determination'] == 'LIKELY_SUCCESS_NO_CA'
        assert result['auth_confidence_pct'] == 60  # Lower confidence

    def test_auth_failed_when_error_code_present(self, temp_db):
        """Non-zero error code = AUTH_FAILED."""
        row_id = self._insert_sign_in(temp_db, status_error_code=50126)  # Invalid credentials
        result = self._query_auth_view(temp_db, row_id=row_id)

        assert result['auth_determination'] == 'AUTH_FAILED'
        assert result['auth_confidence_pct'] == 90

    def test_indeterminate_when_no_data(self, temp_db):
        """Missing status fields = INDETERMINATE."""
        row_id = self._insert_sign_in(
            temp_db,
            conditional_access_status=None,
            status_error_code=None
        )
        result = self._query_auth_view(temp_db, row_id=row_id)

        assert result['auth_determination'] == 'INDETERMINATE'
        assert result['auth_confidence_pct'] == 0

    def test_attacker_ip_analysis_uses_view(self, temp_db):
        """Real-world test: AitM IPs should show correct status."""
        # Insert attacker login attempts (Safari on Windows - AitM signature)
        row_id = self._insert_sign_in(
            temp_db,
            ip_address='93.127.215.4',
            browser='Safari',
            os='Windows10',
            conditional_access_status='notApplied',
            status_error_code=0
        )
        result = self._query_auth_view(temp_db, ip='93.127.215.4')

        # Should NOT show as CONFIRMED_SUCCESS
        assert result['auth_determination'] != 'CONFIRMED_SUCCESS'
        assert result['auth_determination'] == 'LIKELY_SUCCESS_NO_CA'
        assert result['auth_confidence_pct'] < 100

    def test_view_preserves_all_original_columns(self, temp_db):
        """View should include all original sign_in_logs columns."""
        row_id = self._insert_sign_in(
            temp_db,
            ip_address='1.2.3.4',
            user='preserve@test.com',
            conditional_access_status='success'
        )
        result = self._query_auth_view(temp_db, row_id=row_id)

        # Original columns should be present
        assert result['ip_address'] == '1.2.3.4'
        assert result['user_principal_name'] == 'preserve@test.com'
        assert result['conditional_access_status'] == 'success'
        # New computed columns should also be present
        assert 'auth_determination' in result
        assert 'auth_confidence_pct' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
