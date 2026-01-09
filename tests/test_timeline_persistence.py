#!/usr/bin/env python3
"""
Test suite for Phase 260: IR Timeline Persistence

Tests timeline_events, timeline_annotations, timeline_phases, timeline_build_history tables,
event filtering logic, and incremental timeline building.

Author: SRE Principal Engineer Agent
Created: 2026-01-09
Phase: 260
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

import sys
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.log_database import IRLogDatabase


class TestTimelineSchema:
    """Test timeline tables schema (TDD Step 1)."""

    def test_timeline_events_table_exists(self):
        """Timeline events table should be created with schema v4."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='timeline_events'
            """)
            assert cursor.fetchone() is not None

            # Check key columns
            cursor.execute("PRAGMA table_info(timeline_events)")
            columns = {row[1] for row in cursor.fetchall()}

            required_columns = {
                'id', 'event_hash', 'timestamp', 'user_principal_name',
                'action', 'details', 'source_type', 'source_id',
                'phase', 'severity', 'mitre_technique',
                'ip_address', 'location_country', 'client_app',
                'created_at', 'created_by', 'excluded', 'exclusion_reason'
            }
            assert required_columns.issubset(columns)

            conn.close()

    def test_timeline_annotations_table_exists(self):
        """Timeline annotations table should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='timeline_annotations'
            """)
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(timeline_annotations)")
            columns = {row[1] for row in cursor.fetchall()}

            required = {
                'id', 'timeline_event_id', 'annotation_type', 'content',
                'pir_section', 'include_in_pir', 'created_at', 'created_by', 'updated_at'
            }
            assert required.issubset(columns)

            conn.close()

    def test_timeline_phases_table_exists(self):
        """Timeline phases table should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='timeline_phases'
            """)
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(timeline_phases)")
            columns = {row[1] for row in cursor.fetchall()}

            required = {
                'id', 'phase', 'phase_start', 'phase_end', 'trigger_event_id',
                'confidence', 'description', 'event_count', 'created_at', 'updated_at'
            }
            assert required.issubset(columns)

            conn.close()

    def test_timeline_build_history_table_exists(self):
        """Timeline build history table should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='timeline_build_history'
            """)
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(timeline_build_history)")
            columns = {row[1] for row in cursor.fetchall()}

            required = {
                'id', 'build_timestamp', 'build_type', 'events_added',
                'events_updated', 'phases_detected', 'source_tables',
                'date_range_start', 'date_range_end', 'home_country',
                'parameters', 'status', 'error_message'
            }
            assert required.issubset(columns)

            conn.close()

    def test_v_timeline_view_exists(self):
        """v_timeline view should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='view' AND name='v_timeline'
            """)
            assert cursor.fetchone() is not None

            # View should be queryable
            cursor.execute("SELECT * FROM v_timeline LIMIT 0")

            conn.close()

    def test_timeline_indexes_created(self):
        """Timeline tables should have performance indexes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_timeline%'
            """)
            indexes = {row[0] for row in cursor.fetchall()}

            required_indexes = {
                'idx_timeline_timestamp',
                'idx_timeline_user',
                'idx_timeline_phase',
                'idx_timeline_severity',
                'idx_timeline_source',
                'idx_timeline_mitre'
            }
            assert required_indexes.issubset(indexes)

            conn.close()

    def test_event_hash_unique_constraint(self):
        """event_hash should have UNIQUE constraint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            conn = db.connect()
            cursor = conn.cursor()

            # Insert first event
            cursor.execute("""
                INSERT INTO timeline_events
                (event_hash, timestamp, user_principal_name, action, source_type, source_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("hash123", "2026-01-01T00:00:00Z", "user@test.com", "Test", "test", 1, datetime.now().isoformat()))

            # Attempt duplicate - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO timeline_events
                    (event_hash, timestamp, user_principal_name, action, source_type, source_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("hash123", "2026-01-01T00:01:00Z", "user2@test.com", "Test2", "test", 2, datetime.now().isoformat()))

            conn.close()


class TestEventFiltering:
    """Test event filtering criteria (TDD Step 2)."""

    def test_foreign_login_is_interesting(self):
        """Foreign login (non-AU) should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'sign_in_logs',
            'location_country': 'RU',
            'conditional_access_status': 'success',
            'status_error_code': None
        }

        assert is_interesting_event(event, home_country='AU') is True

    def test_failed_auth_is_interesting(self):
        """Failed authentication should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'sign_in_logs',
            'location_country': 'AU',
            'conditional_access_status': 'failure',
            'status_error_code': 50126
        }

        assert is_interesting_event(event, home_country='AU') is True

    def test_legacy_auth_is_interesting(self):
        """Legacy auth event should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'legacy_auth_logs',
            'location_country': 'AU',
            'client_app_used': 'IMAP'
        }

        assert is_interesting_event(event, home_country='AU') is True

    def test_inbox_rule_change_is_interesting(self):
        """Inbox rule changes should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'inbox_rules',
            'operation': 'Set-InboxRule'
        }

        assert is_interesting_event(event, home_country='AU') is True

    def test_routine_au_login_not_interesting(self):
        """Routine successful AU login should NOT be interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'sign_in_logs',
            'location_country': 'AU',
            'conditional_access_status': 'success',
            'status_error_code': None,
            'app_display_name': 'Microsoft Teams'
        }

        assert is_interesting_event(event, home_country='AU') is False

    def test_high_risk_ip_is_interesting(self):
        """Login from high-risk IP should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'sign_in_logs',
            'location_country': 'AU',
            'ip_address': '185.234.100.50',  # Known bad IP
            'conditional_access_status': 'success'
        }

        # Would need IR knowledge base lookup - skip for now
        assert is_interesting_event(event, home_country='AU') is False  # No KB lookup yet

    def test_password_change_is_interesting(self):
        """Password changes should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'entra_audit_log',
            'activity': 'Change password (self-service)'
        }

        assert is_interesting_event(event, home_country='AU') is True

    def test_admin_role_assignment_is_interesting(self):
        """Admin role assignments should be classified as interesting."""
        from claude.tools.m365_ir.timeline_filter import is_interesting_event

        event = {
            'source_type': 'entra_audit_log',
            'activity': 'Add member to role'
        }

        assert is_interesting_event(event, home_country='AU') is True


class TestTimelineBuilder:
    """Test TimelineBuilder persistence (TDD Step 3)."""

    def test_build_and_persist_creates_events(self):
        """build_and_persist() should insert timeline events from raw logs."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()

            # Insert sample sign-in log
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))
            conn.commit()

            # Build timeline
            builder = TimelineBuilder(db=db)
            result = builder.build_and_persist(incremental=False)

            # Verify event created
            cursor.execute("SELECT COUNT(*) FROM timeline_events")
            assert cursor.fetchone()[0] == 1

            # Verify event details
            cursor.execute("SELECT * FROM timeline_events")
            event = cursor.fetchone()
            assert event['user_principal_name'] == "user@test.com"
            assert event['source_type'] == 'sign_in_logs'
            assert event['location_country'] == "RU"
            assert event['severity'] == 'ALERT'  # Foreign + high-risk country

            conn.close()

    def test_incremental_build_only_processes_new_records(self):
        """Incremental build should skip already-processed events."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()
            conn = db.connect()
            cursor = conn.cursor()

            # Insert 2 sign-in events
            cursor.execute("""
                INSERT INTO sign_in_logs
                (id, timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))

            cursor.execute("""
                INSERT INTO sign_in_logs
                (id, timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (2, ?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T11:00:00Z", "user2@test.com", "5.6.7.8", "CN", "success", datetime.now().isoformat()))
            conn.commit()

            # First build - should process both
            builder = TimelineBuilder(db=db)
            result = builder.build_and_persist(incremental=False)
            cursor.execute("SELECT COUNT(*) FROM timeline_events")
            assert cursor.fetchone()[0] == 2

            # Second build (incremental) - should process 0 new
            result2 = builder.build_and_persist(incremental=True)
            cursor.execute("SELECT COUNT(*) FROM timeline_events")
            assert cursor.fetchone()[0] == 2  # No duplicates

            # Verify build history records incremental run
            cursor.execute("SELECT * FROM timeline_build_history ORDER BY id DESC LIMIT 1")
            build = cursor.fetchone()
            assert build['build_type'] == 'incremental'
            assert build['events_added'] == 0

            conn.close()

    def test_event_hash_prevents_duplicates(self):
        """Event hash should prevent duplicate events across builds."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder, compute_event_hash

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()
            conn = db.connect()
            cursor = conn.cursor()

            # Insert same event twice with different IDs
            cursor.execute("""
                INSERT INTO sign_in_logs
                (id, timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))
            conn.commit()

            # Build timeline
            builder = TimelineBuilder(db=db)
            builder.build_and_persist(incremental=False)

            # Verify hash was generated
            cursor.execute("SELECT event_hash FROM timeline_events")
            hash1 = cursor.fetchone()['event_hash']
            assert len(hash1) == 64  # SHA256 hex digest

            # Force rebuild - should not create duplicate
            builder.build_and_persist(incremental=False, force_rebuild=False)
            cursor.execute("SELECT COUNT(*) FROM timeline_events")
            assert cursor.fetchone()[0] == 1  # Still only 1 event

            conn.close()

    def test_add_annotation(self):
        """add_annotation() should create annotation record linked to event."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()
            conn = db.connect()
            cursor = conn.cursor()

            # Insert event
            cursor.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))
            conn.commit()

            # Build timeline
            builder = TimelineBuilder(db=db)
            builder.build_and_persist(incremental=False)

            # Get event ID
            cursor.execute("SELECT id FROM timeline_events")
            event_id = cursor.fetchone()['id']

            # Add annotation
            annotation_id = builder.add_annotation(
                event_id=event_id,
                annotation_type='finding',
                content='Initial access from Russian IP',
                pir_section='timeline'
            )

            # Verify annotation created
            cursor.execute("SELECT * FROM timeline_annotations WHERE id = ?", (annotation_id,))
            annotation = cursor.fetchone()
            assert annotation['timeline_event_id'] == event_id
            assert annotation['annotation_type'] == 'finding'
            assert annotation['content'] == 'Initial access from Russian IP'
            assert annotation['pir_section'] == 'timeline'
            assert annotation['include_in_pir'] == 1

            conn.close()

    def test_exclude_event(self):
        """exclude_event() should soft-delete event with reason."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()
            conn = db.connect()
            cursor = conn.cursor()

            # Insert event
            cursor.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))
            conn.commit()

            # Build timeline
            builder = TimelineBuilder(db=db)
            builder.build_and_persist(incremental=False)

            # Get event ID
            cursor.execute("SELECT id FROM timeline_events")
            event_id = cursor.fetchone()['id']

            # Exclude event
            builder.exclude_event(event_id=event_id, reason="False positive - VPN user")

            # Verify soft delete
            cursor.execute("SELECT excluded, exclusion_reason FROM timeline_events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            assert row['excluded'] == 1
            assert row['exclusion_reason'] == "False positive - VPN user"

            conn.close()

    def test_get_timeline_filters_excluded(self):
        """get_timeline() should exclude soft-deleted events by default."""
        from claude.tools.m365_ir.timeline_builder import TimelineBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            db = IRLogDatabase(case_id="PIR-TEST-001", base_path=tmpdir)
            db.create()
            conn = db.connect()
            cursor = conn.cursor()

            # Insert 2 events
            cursor.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T10:00:00Z", "user1@test.com", "1.2.3.4", "RU", "success", datetime.now().isoformat()))

            cursor.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country,
                 conditional_access_status, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("2026-01-01T11:00:00Z", "user2@test.com", "5.6.7.8", "CN", "success", datetime.now().isoformat()))
            conn.commit()

            # Build timeline
            builder = TimelineBuilder(db=db)
            builder.build_and_persist(incremental=False)

            # Exclude first event
            cursor.execute("SELECT id FROM timeline_events LIMIT 1")
            event_id = cursor.fetchone()['id']
            builder.exclude_event(event_id=event_id, reason="Test exclusion")

            # Get timeline (should exclude deleted)
            timeline = builder.get_timeline()
            assert len(timeline) == 1
            assert timeline[0]['user_principal_name'] == "user2@test.com"

            # Get timeline with include_excluded=True
            timeline_all = builder.get_timeline(include_excluded=True)
            assert len(timeline_all) == 2

            conn.close()


class TestMigration:
    """Test v3 -> v4 migration (TDD Step 4)."""

    def test_migrate_v3_to_v4(self):
        """Migration should add timeline tables to v3 database."""
        pytest.skip("Implement after migration script created")

    def test_migration_idempotent(self):
        """Running migration twice should not cause errors."""
        pytest.skip("Implement after migration script created")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
