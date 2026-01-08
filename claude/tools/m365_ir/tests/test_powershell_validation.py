#!/usr/bin/env python3
"""
TDD Tests for PowerShell Export Validation (M365 IR Data Enhancements - Requirement 3)

Detects corrupted exports where PowerShell failed to expand .NET objects,
resulting in type names like:
    Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus
instead of actual values.

This led to incorrect breach determination in PIR-FYNA-2025-12-08.

Run: pytest claude/tools/m365_ir/tests/test_powershell_validation.py -v

Author: Maia System (SRE Principal Engineer Agent)
Created: 2026-01-08 (PIR-FYNA-2025-12-08 lessons learned)
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase


class TestPowerShellValidation:
    """Tests for PowerShell .NET object detection."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database with schema."""
        db = IRLogDatabase(case_id="TEST-PS-VALID", base_path=str(tmp_path))
        db.create()
        return db

    def _insert_sign_in(
        self,
        db: IRLogDatabase,
        status_failure_reason: str = None,
        conditional_access_status: str = None,
        risk_detail: str = None,
    ) -> int:
        """Helper to insert a sign-in log record with specific field values."""
        conn = db.connect()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO sign_in_logs (
                timestamp, user_principal_name, ip_address,
                status_failure_reason, conditional_access_status,
                risk_detail, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now, "test@example.com", "1.1.1.1",
            status_failure_reason, conditional_access_status,
            risk_detail, now
        ))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _query_quality_summary(self, db: IRLogDatabase, table_name: str) -> dict:
        """Query quality check summary for a table."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM quality_check_summary
            WHERE table_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (table_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def test_detects_object_type_in_status(self, temp_db):
        """Should detect PowerShell object type in status field."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        self._insert_sign_in(
            temp_db,
            status_failure_reason='Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus'
        )

        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert result['corrupted'] is True
        assert 'status_failure_reason' in result['affected_fields']

    def test_detects_nested_graph_models(self, temp_db):
        """Should detect Microsoft.Graph.PowerShell.Models.* pattern."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        self._insert_sign_in(
            temp_db,
            risk_detail='Microsoft.Graph.PowerShell.Models.MicrosoftGraphRiskDetail'
        )

        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert result['corrupted'] is True
        assert 'risk_detail' in result['affected_fields']

    def test_no_false_positive_on_valid_data(self, temp_db):
        """Should not flag valid status values."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        self._insert_sign_in(
            temp_db,
            status_failure_reason='Invalid username or password',
            conditional_access_status='success'
        )

        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert result['corrupted'] is False
        assert result['affected_fields'] == []

    def test_updates_quality_check_summary(self, temp_db):
        """Should update quality_check_summary with detection results."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        self._insert_sign_in(
            temp_db,
            status_failure_reason='Microsoft.Graph.PowerShell.Models.Something'
        )

        check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        summary = self._query_quality_summary(temp_db, 'sign_in_logs')
        assert summary is not None
        # Check that powershell corruption was recorded in warnings
        assert 'PowerShell' in (summary.get('warnings') or '')

    def test_returns_sample_values_for_debugging(self, temp_db):
        """Should return sample corrupted values for analyst review."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        corrupted_value = 'Microsoft.Graph.PowerShell.Models.BadObject'
        self._insert_sign_in(temp_db, status_failure_reason=corrupted_value)

        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert corrupted_value in str(result['sample_values'])

    def test_handles_multiple_corrupted_fields(self, temp_db):
        """Should detect corruption in multiple fields."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        self._insert_sign_in(
            temp_db,
            status_failure_reason='Microsoft.Graph.PowerShell.Models.Status',
            risk_detail='Microsoft.Graph.PowerShell.Models.Risk'
        )

        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert result['corrupted'] is True
        assert len(result['affected_fields']) >= 2

    def test_handles_empty_table(self, temp_db):
        """Should handle empty tables gracefully."""
        from claude.tools.m365_ir.powershell_validation import check_powershell_object_corruption

        # Don't insert any records
        result = check_powershell_object_corruption(temp_db.db_path, 'sign_in_logs')

        assert result['corrupted'] is False
        assert result['affected_fields'] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
