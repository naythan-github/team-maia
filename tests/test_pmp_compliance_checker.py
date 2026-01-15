#!/usr/bin/env python3
"""
Tests for PMP Compliance Checker - Essential Eight compliance evaluation

Tests compliance checking for:
- Essential Eight Patch Applications maturity levels (1-3)
- Critical patch SLA (48 hours)
- High patch SLA (2 weeks)

Author: SRE Principal Engineer Agent
Date: 2026-01-15
Sprint: SPRINT-PMP-UNIFIED-001
Phase: P5 - Compliance Checks
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil


class TestComplianceCheckerImport:
    """Test that ComplianceChecker can be imported"""

    def test_import_checker(self):
        """ComplianceChecker importable."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker
        assert PMPComplianceChecker is not None


class TestEssentialEightChecks:
    """Test Essential Eight compliance checks"""

    @pytest.fixture
    def test_db(self):
        """Create temporary test database with schema"""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "test_pmp_intelligence.db"

        # Read schema
        schema_file = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        schema_sql = schema_file.read_text()

        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        shutil.rmtree(tmp_dir)

    @pytest.fixture
    def snapshot_with_patches(self, test_db):
        """Create snapshot with various patch states"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Create snapshot
        cursor.execute("INSERT INTO snapshots (status) VALUES ('success')")
        snapshot_id = cursor.lastrowid

        # Current time in milliseconds
        now_ms = int(datetime.now().timestamp() * 1000)

        # Critical patches
        # - 2 critical patches applied within 48 hours (compliant)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'CRIT-001', 'Critical Patch 1', 4, 'Critical',
            now_ms - int(timedelta(hours=24).total_seconds() * 1000), 1
        ))

        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'CRIT-002', 'Critical Patch 2', 4, 'Critical',
            now_ms - int(timedelta(hours=36).total_seconds() * 1000), 1
        ))

        # - 1 critical patch not yet applied, released 72 hours ago (non-compliant)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'CRIT-003', 'Critical Patch 3', 4, 'Critical',
            now_ms - int(timedelta(hours=72).total_seconds() * 1000), 0
        ))

        # High severity patches
        # - 3 high patches applied within 2 weeks (compliant)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'HIGH-001', 'High Patch 1', 3, 'Important',
            now_ms - int(timedelta(days=7).total_seconds() * 1000), 1
        ))

        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'HIGH-002', 'High Patch 2', 3, 'Important',
            now_ms - int(timedelta(days=10).total_seconds() * 1000), 1
        ))

        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'HIGH-003', 'High Patch 3', 3, 'Important',
            now_ms - int(timedelta(days=5).total_seconds() * 1000), 1
        ))

        # - 1 high patch not applied, released 20 days ago (non-compliant)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'HIGH-004', 'High Patch 4', 3, 'Important',
            now_ms - int(timedelta(days=20).total_seconds() * 1000), 0
        ))

        conn.commit()
        conn.close()

        return snapshot_id, test_db

    def test_patch_applications_maturity(self, snapshot_with_patches):
        """Calculates E8 Patch Applications maturity level."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = snapshot_with_patches

        checker = PMPComplianceChecker(db_path=db_path)
        result = checker.check_compliance(snapshot_id)

        assert result['success'] is True
        assert 'maturity_level' in result
        assert result['maturity_level'] in [1, 2, 3]

    def test_critical_patch_sla(self, snapshot_with_patches):
        """Checks critical patches applied within 48 hours."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = snapshot_with_patches

        checker = PMPComplianceChecker(db_path=db_path)
        result = checker.check_compliance(snapshot_id)

        assert result['success'] is True
        assert 'critical_sla' in result
        assert 'critical_sla_percentage' in result['critical_sla']

        # We have 3 critical patches: 2 applied within 48h, 1 not applied (released 72h ago)
        # Expected: 66.67% compliance (2/3)
        assert result['critical_sla']['critical_sla_percentage'] < 100

    def test_high_patch_sla(self, snapshot_with_patches):
        """Checks high patches applied within 2 weeks."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = snapshot_with_patches

        checker = PMPComplianceChecker(db_path=db_path)
        result = checker.check_compliance(snapshot_id)

        assert result['success'] is True
        assert 'high_sla' in result
        assert 'high_sla_percentage' in result['high_sla']

        # We have 4 high patches: 3 applied within 2 weeks, 1 not applied (released 20 days ago)
        # Expected: 75% compliance (3/4)
        assert result['high_sla']['high_sla_percentage'] < 100


class TestComplianceStorage:
    """Test compliance results storage"""

    @pytest.fixture
    def test_db(self):
        """Create temporary test database with schema"""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "test_pmp_intelligence.db"

        # Read schema
        schema_file = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        schema_sql = schema_file.read_text()

        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()

        # Create snapshot
        cursor.execute("INSERT INTO snapshots (status) VALUES ('success')")
        snapshot_id = cursor.lastrowid

        # Add minimal patch data
        now_ms = int(datetime.now().timestamp() * 1000)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'PATCH-001', 'Test Patch', 4, 'Critical',
            now_ms - int(timedelta(hours=24).total_seconds() * 1000), 1
        ))

        conn.commit()
        conn.close()

        yield snapshot_id, db_path

        # Cleanup
        shutil.rmtree(tmp_dir)

    def test_stores_compliance_results(self, test_db):
        """Writes to compliance_checks table."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = test_db

        checker = PMPComplianceChecker(db_path=db_path)
        result = checker.check_compliance(snapshot_id)

        assert result['success'] is True

        # Verify data written to compliance_checks table
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM compliance_checks WHERE snapshot_id = ?
        """, (snapshot_id,))

        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0, "No compliance checks stored in database"

    def test_compliance_linked_to_snapshot(self, test_db):
        """Results have snapshot_id."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = test_db

        checker = PMPComplianceChecker(db_path=db_path)
        checker.check_compliance(snapshot_id)

        # Verify snapshot_id linkage
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT snapshot_id FROM compliance_checks WHERE snapshot_id = ?
        """, (snapshot_id,))

        rows = cursor.fetchall()
        conn.close()

        assert len(rows) > 0
        assert all(row[0] == snapshot_id for row in rows)

    def test_compliance_history_queryable(self, test_db):
        """Can query compliance trend over time."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = test_db

        # Run compliance check
        checker = PMPComplianceChecker(db_path=db_path)
        checker.check_compliance(snapshot_id)

        # Query compliance history
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT check_name, passed, timestamp
            FROM compliance_checks
            WHERE snapshot_id = ?
            ORDER BY timestamp DESC
        """, (snapshot_id,))

        rows = cursor.fetchall()
        conn.close()

        assert len(rows) > 0
        # Verify each row has check_name, passed status, and timestamp
        for row in rows:
            assert row[0] is not None  # check_name
            assert row[1] in (0, 1)    # passed (boolean)
            assert row[2] is not None  # timestamp


class TestComplianceReporting:
    """Test compliance report generation"""

    @pytest.fixture
    def test_db_with_compliance(self):
        """Create test database with compliance data"""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "test_pmp_intelligence.db"

        # Read schema
        schema_file = Path(__file__).parent.parent / "claude/tools/pmp/pmp_unified_schema.sql"
        schema_sql = schema_file.read_text()

        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()

        # Create snapshot
        cursor.execute("INSERT INTO snapshots (status) VALUES ('success')")
        snapshot_id = cursor.lastrowid

        # Add patch data
        now_ms = int(datetime.now().timestamp() * 1000)
        cursor.execute("""
            INSERT INTO patches (
                snapshot_id, pmp_patch_id, patch_name, severity, severity_label,
                patch_released_time, installed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 'PATCH-001', 'Test Patch', 4, 'Critical',
            now_ms - int(timedelta(hours=24).total_seconds() * 1000), 1
        ))

        conn.commit()
        conn.close()

        yield snapshot_id, db_path

        # Cleanup
        shutil.rmtree(tmp_dir)

    def test_generate_compliance_report(self, test_db_with_compliance):
        """Generates human-readable compliance report."""
        from claude.tools.pmp.pmp_compliance_checker import PMPComplianceChecker

        snapshot_id, db_path = test_db_with_compliance

        checker = PMPComplianceChecker(db_path=db_path)
        checker.check_compliance(snapshot_id)

        # Generate report
        report = checker.generate_report(snapshot_id)

        assert report is not None
        assert isinstance(report, str)
        assert len(report) > 0

        # Report should contain key information
        assert 'Essential Eight' in report or 'E8' in report
        assert 'Maturity' in report or 'Level' in report
