#!/usr/bin/env python3
"""
Migration Script: v3 → v4 (Phase 260 - IR Timeline Persistence)

Adds timeline persistence tables to existing v3 databases:
- timeline_events
- timeline_annotations
- timeline_phases
- timeline_build_history
- v_timeline view

Idempotent: Safe to run multiple times (uses IF NOT EXISTS).

Usage:
    from claude.tools.m365_ir.migrations.migrate_v4 import migrate_to_v4
    from claude.tools.m365_ir.log_database import IRLogDatabase

    db = IRLogDatabase(case_id="PIR-EXISTING-CASE")
    migrate_to_v4(db)

Author: SRE Principal Engineer Agent
Created: 2026-01-09
Phase: 260
"""

from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


def migrate_to_v4(db) -> None:
    """
    Migrate existing v3 database to v4 (add timeline tables).

    Args:
        db: IRLogDatabase instance

    Raises:
        Exception if database doesn't exist
    """
    if not db.exists:
        raise ValueError(f"Database does not exist: {db.db_path}")

    conn = db.connect()
    cursor = conn.cursor()

    print(f"Migrating {db.case_id} to schema v4...")

    # ================================================================
    # Timeline Events table
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Event identification
            event_hash TEXT NOT NULL UNIQUE,

            -- Core event data
            timestamp TEXT NOT NULL,
            user_principal_name TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,

            -- Source traceability (FK to raw log tables)
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,

            -- Classification
            phase TEXT,
            severity TEXT DEFAULT 'INFO',
            mitre_technique TEXT,

            -- Evidence (denormalized for query performance)
            ip_address TEXT,
            location_country TEXT,
            client_app TEXT,

            -- Metadata
            created_at TEXT NOT NULL,
            created_by TEXT DEFAULT 'system',

            -- Soft delete for timeline curation
            excluded INTEGER DEFAULT 0,
            exclusion_reason TEXT
        )
    """)

    # ================================================================
    # Timeline Annotations table
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Link to timeline event
            timeline_event_id INTEGER NOT NULL,

            -- Annotation content
            annotation_type TEXT NOT NULL,
            content TEXT NOT NULL,

            -- PIR integration
            pir_section TEXT,
            include_in_pir INTEGER DEFAULT 1,

            -- Metadata
            created_at TEXT NOT NULL,
            created_by TEXT DEFAULT 'analyst',
            updated_at TEXT,

            FOREIGN KEY (timeline_event_id) REFERENCES timeline_events(id)
        )
    """)

    # ================================================================
    # Timeline Phases table
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Phase definition
            phase TEXT NOT NULL,
            phase_start TEXT NOT NULL,
            phase_end TEXT,

            -- Trigger event
            trigger_event_id INTEGER,

            -- Classification
            confidence TEXT DEFAULT 'MEDIUM',
            description TEXT NOT NULL,

            -- Evidence count (denormalized)
            event_count INTEGER DEFAULT 0,

            -- Metadata
            created_at TEXT NOT NULL,
            updated_at TEXT,

            FOREIGN KEY (trigger_event_id) REFERENCES timeline_events(id)
        )
    """)

    # ================================================================
    # Timeline Build History table
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_build_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Build metadata
            build_timestamp TEXT NOT NULL,
            build_type TEXT NOT NULL,

            -- Statistics
            events_added INTEGER DEFAULT 0,
            events_updated INTEGER DEFAULT 0,
            phases_detected INTEGER DEFAULT 0,

            -- Source data summary
            source_tables TEXT,
            date_range_start TEXT,
            date_range_end TEXT,

            -- Parameters used
            home_country TEXT DEFAULT 'AU',
            parameters TEXT,

            -- Status
            status TEXT DEFAULT 'completed',
            error_message TEXT
        )
    """)

    # ================================================================
    # Timeline View
    # ================================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_timeline AS
        SELECT
            te.id,
            te.timestamp,
            te.user_principal_name,
            te.action,
            te.details,
            te.source_type,
            te.source_id,
            te.phase,
            te.severity,
            te.mitre_technique,
            te.ip_address,
            te.location_country,
            te.client_app,
            te.excluded,
            te.exclusion_reason,
            te.created_at,
            te.created_by,

            -- Aggregated annotations
            (SELECT COUNT(*) FROM timeline_annotations ta WHERE ta.timeline_event_id = te.id) as annotation_count,
            (SELECT GROUP_CONCAT(ta.annotation_type, ', ') FROM timeline_annotations ta WHERE ta.timeline_event_id = te.id) as annotation_types,

            -- Phase context
            tp.phase as phase_name,
            tp.confidence as phase_confidence

        FROM timeline_events te
        LEFT JOIN timeline_phases tp ON te.phase = tp.phase
        WHERE te.excluded = 0
        ORDER BY te.timestamp
    """)

    # ================================================================
    # Indexes
    # ================================================================
    # Timeline events indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_timestamp
        ON timeline_events(timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_user
        ON timeline_events(user_principal_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_phase
        ON timeline_events(phase)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_severity
        ON timeline_events(severity)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_source
        ON timeline_events(source_type, source_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeline_mitre
        ON timeline_events(mitre_technique)
    """)

    # Timeline annotations indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_annotation_event
        ON timeline_annotations(timeline_event_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_annotation_type
        ON timeline_annotations(annotation_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_annotation_pir
        ON timeline_annotations(pir_section)
    """)

    # Timeline phases indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phase_name
        ON timeline_phases(phase)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phase_start
        ON timeline_phases(phase_start)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phase_confidence
        ON timeline_phases(confidence)
    """)

    # Timeline build history indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_build_timestamp
        ON timeline_build_history(build_timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_build_status
        ON timeline_build_history(status)
    """)

    conn.commit()
    conn.close()

    print(f"✅ Migration complete: {db.case_id} now on schema v4")
    print("   Added: timeline_events, timeline_annotations, timeline_phases, timeline_build_history, v_timeline")


if __name__ == "__main__":
    """Migrate all existing v3 databases in ~/work_projects/ir_cases/"""
    from claude.tools.m365_ir.log_database import IRLogDatabase
    import os

    base_path = os.path.expanduser("~/work_projects/ir_cases")

    if not os.path.exists(base_path):
        print(f"No IR cases directory found: {base_path}")
        sys.exit(1)

    # Find all case directories with databases
    migrated = 0
    for case_id in os.listdir(base_path):
        case_dir = os.path.join(base_path, case_id)
        if os.path.isdir(case_dir):
            db_path = os.path.join(case_dir, f"{case_id}_logs.db")
            if os.path.exists(db_path):
                print(f"\nMigrating {case_id}...")
                try:
                    db = IRLogDatabase(case_id=case_id, base_path=base_path)
                    migrate_to_v4(db)
                    migrated += 1
                except Exception as e:
                    print(f"❌ Error migrating {case_id}: {e}")

    print(f"\n{'='*60}")
    print(f"Migration complete: {migrated} cases upgraded to v4")
