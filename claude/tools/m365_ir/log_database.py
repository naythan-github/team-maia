#!/usr/bin/env python3
"""
IRLogDatabase - Per-investigation SQLite storage for M365 IR logs.

Phase 226 - IR Log Database Implementation
Provides queryable persistence for parsed M365 security logs.

Usage:
    from log_database import IRLogDatabase

    db = IRLogDatabase(case_id="PIR-ACME-2025-001")
    db.create()

    conn = db.connect()
    # ... query data ...
    conn.close()

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-01-05
"""

import sqlite3
from pathlib import Path
from typing import Dict, Optional
import os


# Default base path for IR case databases
DEFAULT_BASE_PATH = os.path.expanduser("~/work_projects/ir_cases")

# Schema version for migrations
# v1: Initial schema (Phase 226)
# v2: Compression - raw_record and audit_data stored as BLOB (Phase 229)
# v3: Verification - verification_summary table (Phase 241)
# v4: Timeline persistence - timeline_events, timeline_annotations, timeline_phases, timeline_build_history (Phase 260)
# v5: Multi-schema ETL - schema_variant, sign_in_type, service_principal fields, Graph API fields (Phase 264)
SCHEMA_VERSION = 5


class IRLogDatabase:
    """
    Manages per-investigation SQLite database for M365 logs.

    Each investigation gets its own isolated database file containing
    all parsed log data. This maintains chain of custody and enables
    SQL queries for follow-up investigation questions.
    """

    def __init__(self, case_id: str, base_path: Optional[str] = None):
        """
        Initialize database for a specific investigation case.

        Args:
            case_id: Investigation identifier (e.g., PIR-ACME-2025-001)
            base_path: Base directory for case folders (default: ~/work_projects/ir_cases/)
        """
        self._case_id = case_id
        self._base_path = Path(base_path) if base_path else Path(DEFAULT_BASE_PATH)
        self._db_path: Optional[Path] = None

    @property
    def case_id(self) -> str:
        """Return the case identifier."""
        return self._case_id

    @property
    def db_path(self) -> Optional[Path]:
        """Return the database file path.

        Returns the expected path if database exists, None otherwise.
        Works even before connect() or create() is called.
        """
        if self._db_path is not None:
            return self._db_path
        # Compute expected path
        expected_path = self._base_path / self._case_id / f"{self._case_id}_logs.db"
        if expected_path.exists():
            return expected_path
        return None

    @property
    def exists(self) -> bool:
        """Check if the database file exists."""
        expected_path = self._base_path / self._case_id / f"{self._case_id}_logs.db"
        return expected_path.exists()

    def create(self) -> Path:
        """
        Create new database with full schema.

        Creates the case directory and database file with all tables
        and indexes. Safe to call multiple times (idempotent).

        Returns:
            Path to the created database file
        """
        # Create case directory
        case_dir = self._base_path / self._case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Create database file
        self._db_path = case_dir / f"{self._case_id}_logs.db"

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # Create all tables
        self._create_tables(cursor)

        # Create indexes
        self._create_indexes(cursor)

        conn.commit()
        conn.close()

        return self._db_path

    def connect(self) -> sqlite3.Connection:
        """
        Get connection to the database.

        Returns:
            sqlite3.Connection with Row factory enabled

        Raises:
            FileNotFoundError: If database doesn't exist (call create() first)
        """
        expected_path = self._base_path / self._case_id / f"{self._case_id}_logs.db"

        if not expected_path.exists():
            raise FileNotFoundError(
                f"Database not found: {expected_path}. Call create() first."
            )

        self._db_path = expected_path
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_stats(self) -> Dict[str, int]:
        """
        Get record counts for all tables.

        Returns:
            Dict mapping table name to record count
        """
        conn = self.connect()
        cursor = conn.cursor()

        tables = [
            'sign_in_logs',
            'unified_audit_log',
            'mailbox_audit_log',
            'oauth_consents',
            'inbox_rules',
            'legacy_auth_logs',
            'password_status',
            'entra_audit_log',
            'import_metadata',
            'mfa_changes',
            'risky_users',
            'verification_summary'
        ]

        stats = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[table] = 0

        conn.close()
        return stats

    def vacuum(self) -> None:
        """
        Optimize database after bulk operations.

        Runs SQLite VACUUM to reclaim space and optimize indexes.
        """
        conn = self.connect()
        conn.execute("VACUUM")
        conn.close()

    def _create_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create all database tables."""

        # Sign-in logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sign_in_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_principal_name TEXT NOT NULL,
                user_display_name TEXT,
                ip_address TEXT,
                location_city TEXT,
                location_country TEXT,
                location_coordinates TEXT,
                client_app TEXT,
                app_display_name TEXT,
                device_detail TEXT,
                browser TEXT,
                os TEXT,
                status_error_code INTEGER,
                status_failure_reason TEXT,
                conditional_access_status TEXT,
                mfa_detail TEXT,
                risk_level TEXT,
                risk_state TEXT,
                risk_detail TEXT,
                resource_display_name TEXT,
                correlation_id TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Unified Audit Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unified_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                operation TEXT NOT NULL,
                workload TEXT,
                record_type INTEGER,
                result_status TEXT,
                client_ip TEXT,
                user_agent TEXT,
                object_id TEXT,
                item_type TEXT,
                audit_data BLOB,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Mailbox Audit Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mailbox_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                operation TEXT NOT NULL,
                log_on_type TEXT,
                client_ip TEXT,
                client_info TEXT,
                item_id TEXT,
                folder_path TEXT,
                subject TEXT,
                result TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # OAuth Consents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_principal_name TEXT,
                app_id TEXT NOT NULL,
                app_display_name TEXT,
                permissions TEXT,
                consent_type TEXT,
                client_ip TEXT,
                risk_score REAL,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Inbox Rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inbox_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                operation TEXT,
                rule_name TEXT,
                rule_id TEXT,
                forward_to TEXT,
                forward_as_attachment_to TEXT,
                redirect_to TEXT,
                delete_message INTEGER,
                move_to_folder TEXT,
                conditions TEXT,
                client_ip TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Import Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                log_type TEXT NOT NULL,
                records_imported INTEGER NOT NULL,
                records_failed INTEGER DEFAULT 0,
                import_started TEXT NOT NULL,
                import_completed TEXT,
                parser_version TEXT NOT NULL
            )
        """)

        # NOTE: verification_summary table defined below in Phase 241 section
        # Removed duplicate Phase 1.1 definition that used incompatible column names

        # Quality Check Summary table (Phase 1.2 - Data Quality Checker)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_check_summary (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                overall_quality_score REAL NOT NULL,
                reliable_fields_count INTEGER NOT NULL,
                unreliable_fields_count INTEGER NOT NULL,
                check_passed INTEGER NOT NULL,
                warnings TEXT,
                recommendations TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Status Code Reference table (Phase 1.3 - Status Code Lookup Tables)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_code_reference (
                code_id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                field_name TEXT NOT NULL,
                code_value TEXT NOT NULL,
                meaning TEXT NOT NULL,
                severity TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_validated TEXT NOT NULL,
                deprecated INTEGER DEFAULT 0,
                UNIQUE(log_type, field_name, code_value)
            )
        """)

        # Schema Versions table (Phase 1.3 - Track Microsoft API changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                api_version TEXT NOT NULL,
                schema_hash TEXT NOT NULL,
                detected_date TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Legacy Auth Logs table (Phase 226.3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS legacy_auth_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_principal_name TEXT NOT NULL,
                user_display_name TEXT,
                client_app_used TEXT,
                app_display_name TEXT,
                ip_address TEXT,
                city TEXT,
                country TEXT,
                status TEXT,
                failure_reason TEXT,
                conditional_access_status TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Password Status table (Phase 226.3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_principal_name TEXT NOT NULL,
                display_name TEXT,
                last_password_change TEXT,
                days_since_change INTEGER,
                password_policies TEXT,
                account_enabled TEXT,
                created_datetime TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Entra ID Audit Log table (Phase 228)
        # Azure AD directory-level events: password changes, role assignments, etc.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entra_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                activity TEXT NOT NULL,
                initiated_by TEXT,
                target TEXT,
                result TEXT,
                result_reason TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # MFA Changes table (Phase 231)
        # MFA registration and modification events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                activity_display_name TEXT NOT NULL,
                user TEXT NOT NULL,
                result TEXT,
                imported_at TEXT NOT NULL
            )
        """)

        # Risky Users table (Phase 231)
        # Microsoft Identity Protection risky user detections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risky_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_principal_name TEXT NOT NULL,
                risk_level TEXT,
                risk_state TEXT,
                risk_detail TEXT,
                risk_last_updated TEXT,
                imported_at TEXT NOT NULL
            )
        """)

        # Verification Summary table (Phase 241)
        # Authentication status verification results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                total_events INTEGER NOT NULL,
                successful INTEGER NOT NULL,
                failed INTEGER NOT NULL,
                success_rate REAL NOT NULL,
                status_code_breakdown TEXT,
                verified_at TEXT NOT NULL,
                notes TEXT,
                UNIQUE(log_type, verified_at)
            )
        """)

        # ================================================================
        # New log type tables (Phase 249 - v2.1.0-Production export format)
        # ================================================================

        # Transport Rules table - CRITICAL for exfiltration detection
        # MITRE ATT&CK: T1114.003 (Email Collection: Email Forwarding Rule)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transport_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                state TEXT,
                priority INTEGER,
                mode TEXT,
                from_scope TEXT,
                sent_to_scope TEXT,
                blind_copy_to TEXT,
                copy_to TEXT,
                redirect_message_to TEXT,
                delete_message INTEGER,
                modify_subject TEXT,
                set_scl INTEGER,
                conditions TEXT,
                exceptions TEXT,
                when_changed TEXT,
                comments TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Evidence Manifest table - Chain of custody metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_manifest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT,
                investigation_id TEXT UNIQUE,
                collection_version TEXT,
                collected_at TEXT,
                collected_by TEXT,
                collected_on TEXT,
                date_range_start TEXT,
                date_range_end TEXT,
                days_back INTEGER,
                files_manifest TEXT,
                raw_json BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Mailbox Delegations table - Access permissions
        # MITRE ATT&CK: T1098.002 (Account Manipulation: Exchange Email Delegate)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mailbox_delegations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mailbox TEXT NOT NULL,
                permission_type TEXT NOT NULL,
                delegate TEXT NOT NULL,
                access_rights TEXT,
                is_inherited INTEGER,
                raw_record BLOB,
                imported_at TEXT NOT NULL,
                UNIQUE(mailbox, permission_type, delegate)
            )
        """)

        # Admin Role Assignments table - Privileged access
        # MITRE ATT&CK: T1078.004, T1098
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_role_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL,
                role_id TEXT NOT NULL,
                role_description TEXT,
                member_display_name TEXT,
                member_upn TEXT,
                member_id TEXT NOT NULL,
                member_type TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL,
                UNIQUE(role_id, member_id)
            )
        """)

        # Conditional Access Policies table
        # MITRE ATT&CK: T1562.001 (Impair Defenses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conditional_access_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                policy_id TEXT NOT NULL UNIQUE,
                state TEXT,
                created_datetime TEXT,
                modified_datetime TEXT,
                conditions TEXT,
                grant_controls TEXT,
                session_controls TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Named Locations table - Geographic/IP access control
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS named_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                location_id TEXT NOT NULL UNIQUE,
                created_datetime TEXT,
                modified_datetime TEXT,
                location_type TEXT,
                is_trusted INTEGER,
                ip_ranges TEXT,
                countries_and_regions TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Application Registrations table
        # MITRE ATT&CK: T1098.001 (Additional Cloud Credentials)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                app_id TEXT NOT NULL UNIQUE,
                object_id TEXT NOT NULL,
                created_datetime TEXT,
                sign_in_audience TEXT,
                publisher_domain TEXT,
                required_resource_access TEXT,
                password_credentials TEXT,
                key_credentials TEXT,
                web_redirect_uris TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # Service Principals table - Enterprise apps
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_principals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                app_id TEXT NOT NULL,
                object_id TEXT NOT NULL UNIQUE,
                service_principal_type TEXT,
                account_enabled INTEGER,
                created_datetime TEXT,
                app_owner_organization_id TEXT,
                reply_urls TEXT,
                tags TEXT,
                raw_record BLOB,
                imported_at TEXT NOT NULL
            )
        """)

        # ================================================================
        # Timeline Persistence Tables (Phase 260)
        # Persisted timeline for incremental builds, analyst annotations, and PIR integration
        # ================================================================

        # Timeline Events table - Core persisted timeline
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

        # Timeline Annotations table - Analyst notes and findings
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

        # Timeline Phases table - Attack phase boundaries
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

        # Timeline Build History table - Audit trail of timeline generation
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
        # Auth Status View (Phase 261 - PIR-SGS-4241809 risk level interpretation)
        # CRITICAL: HIGH risk + notApplied = LIKELY_SUCCESS_RISKY (NOT AUTH_FAILED)
        # ================================================================

        # Create backup of v4 view before changes
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_sign_in_auth_status_v4_backup AS
            SELECT
                *,
                CASE
                    -- CA policy explicitly passed = confirmed success
                    WHEN conditional_access_status = 'success' THEN 'CONFIRMED_SUCCESS'
                    WHEN conditional_access_status = 'failure' THEN 'CA_BLOCKED'
                    WHEN conditional_access_status = 'notApplied'
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 'LIKELY_SUCCESS_NO_CA'
                    WHEN status_error_code IS NOT NULL AND status_error_code != 0
                    THEN 'AUTH_FAILED'
                    ELSE 'INDETERMINATE'
                END as auth_determination,
                CASE
                    WHEN conditional_access_status = 'success' THEN 100
                    WHEN conditional_access_status = 'failure' THEN 100
                    WHEN conditional_access_status = 'notApplied'
                         AND (status_error_code IS NULL OR status_error_code = 0) THEN 60
                    WHEN status_error_code IS NOT NULL AND status_error_code != 0 THEN 90
                    ELSE 0
                END as auth_confidence_pct
            FROM sign_in_logs
        """)

        # Drop old view and create new one with risk level logic
        cursor.execute("DROP VIEW IF EXISTS v_sign_in_auth_status")

        cursor.execute("""
            CREATE VIEW v_sign_in_auth_status AS
            SELECT
                id,
                timestamp,
                user_principal_name,
                user_display_name,
                ip_address,
                location_city,
                location_country,
                location_coordinates,
                client_app,
                app_display_name,
                device_detail,
                browser,
                os,
                status_error_code,
                status_failure_reason,
                conditional_access_status,
                mfa_detail,
                risk_level,
                risk_state,
                risk_detail,
                resource_display_name,
                correlation_id,
                raw_record,
                imported_at,

                -- Enhanced authentication determination
                CASE
                    -- CONFIRMED SUCCESS: CA explicitly passed
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 'CONFIRMED_SUCCESS'

                    -- CA BLOCKED: CA explicitly failed
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('failure')
                    THEN 'CA_BLOCKED'

                    -- AUTH FAILED: Known Microsoft failure error codes
                    WHEN status_error_code IN (
                        50126,  -- Invalid username or password
                        50140,  -- Keep me signed in interrupt
                        50074,  -- Strong auth required
                        50076,  -- MFA required
                        50079,  -- User needs to register for MFA
                        50055,  -- Password expired
                        50057,  -- User disabled
                        50053,  -- Account locked
                        50034,  -- User not found
                        53003,  -- Blocked by CA
                        530032, -- Blocked by security defaults
                        7000218 -- Client app not allowed
                    )
                    THEN 'AUTH_FAILED'

                    -- NEW: LIKELY_SUCCESS_RISKY - High/medium risk but NOT blocked
                    -- This is the CRITICAL CORRECTION - these need investigation!
                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND (status_error_code IS NULL OR status_error_code IN (0, 1))
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 'LIKELY_SUCCESS_RISKY'

                    -- AUTH_INTERRUPTED: Error code 1 is PowerShell internal flag
                    -- Status object couldn't be serialized - may have failed, may have succeeded
                    WHEN status_error_code = 1
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                         AND LOWER(TRIM(COALESCE(risk_level, ''))) NOT IN ('high', 'medium')
                    THEN 'AUTH_INTERRUPTED'

                    -- LIKELY SUCCESS: No CA, no error, low/no risk
                    WHEN (status_error_code IS NULL OR status_error_code = 0)
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                         AND LOWER(TRIM(COALESCE(risk_level, ''))) IN ('none', 'low', 'hidden', 'unknown', '')
                    THEN 'LIKELY_SUCCESS_NO_CA'

                    -- Cannot determine
                    ELSE 'INDETERMINATE'
                END AS auth_determination,

                -- Confidence percentages with corrected values
                CASE
                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND (status_error_code IS NULL OR status_error_code = 0)
                    THEN 100

                    WHEN LOWER(TRIM(conditional_access_status)) IN ('failure')
                    THEN 100

                    WHEN status_error_code IN (50126, 50140, 50074, 50076, 50079, 50055, 50057, 50053, 50034, 53003, 530032, 7000218)
                    THEN 95

                    -- RISKY: 70% confidence - NEEDS INVESTIGATION
                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND (status_error_code IS NULL OR status_error_code IN (0, 1))
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 70

                    -- INTERRUPTED: 50% confidence - unknown outcome
                    WHEN status_error_code = 1
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 50

                    -- LIKELY SUCCESS: 60% confidence
                    WHEN (status_error_code IS NULL OR status_error_code = 0)
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 60

                    ELSE 0
                END AS auth_confidence_pct,

                -- NEW: Investigation priority based on classification
                CASE
                    WHEN LOWER(TRIM(COALESCE(risk_level, ''))) IN ('high', 'medium')
                         AND LOWER(TRIM(COALESCE(conditional_access_status, ''))) IN ('notapplied', 'not applied', 'not_applied', '')
                    THEN 'P1_IMMEDIATE'

                    WHEN LOWER(TRIM(conditional_access_status)) IN ('success')
                         AND location_country NOT IN ('AU', 'Australia')
                    THEN 'P2_REVIEW'

                    ELSE 'P4_NORMAL'
                END AS investigation_priority

            FROM sign_in_logs
        """)

        # ================================================================
        # Timeline View (Phase 260)
        # Unified timeline combining events with annotations
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

    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Create performance indexes on key columns."""

        # Sign-in logs indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signin_timestamp
            ON sign_in_logs(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signin_user
            ON sign_in_logs(user_principal_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signin_ip
            ON sign_in_logs(ip_address)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signin_country
            ON sign_in_logs(location_country)
        """)

        # UAL indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ual_timestamp
            ON unified_audit_log(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ual_user
            ON unified_audit_log(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ual_operation
            ON unified_audit_log(operation)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ual_ip
            ON unified_audit_log(client_ip)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ual_workload
            ON unified_audit_log(workload)
        """)

        # Mailbox audit indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mailbox_timestamp
            ON mailbox_audit_log(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mailbox_user
            ON mailbox_audit_log(user)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mailbox_operation
            ON mailbox_audit_log(operation)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mailbox_ip
            ON mailbox_audit_log(client_ip)
        """)

        # OAuth indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_timestamp
            ON oauth_consents(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_user
            ON oauth_consents(user_principal_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_app
            ON oauth_consents(app_id)
        """)

        # Inbox rules indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_timestamp
            ON inbox_rules(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_user
            ON inbox_rules(user)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_forward
            ON inbox_rules(forward_to)
        """)

        # ================================================================
        # UNIQUE indexes for record deduplication (Phase 226.2)
        # These prevent duplicate records when importing overlapping exports
        # ================================================================

        # Sign-in logs: unique on timestamp + user + ip + correlation_id
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_signin_unique
            ON sign_in_logs(timestamp, user_principal_name, ip_address, correlation_id)
        """)

        # UAL: unique on timestamp + user + operation + object_id
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ual_unique
            ON unified_audit_log(timestamp, user_id, operation, object_id)
        """)

        # Mailbox audit: unique on timestamp + user + operation + item_id
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_mailbox_unique
            ON mailbox_audit_log(timestamp, user, operation, item_id)
        """)

        # OAuth consents: unique on app_id + user (point-in-time snapshot)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_unique
            ON oauth_consents(app_id, user_principal_name, permissions)
        """)

        # Inbox rules: unique on user + rule_name (point-in-time snapshot)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_rules_unique
            ON inbox_rules(user, rule_name)
        """)

        # ================================================================
        # Legacy Auth Logs indexes (Phase 226.3)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_legacy_auth_timestamp
            ON legacy_auth_logs(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_legacy_auth_user
            ON legacy_auth_logs(user_principal_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_legacy_auth_ip
            ON legacy_auth_logs(ip_address)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_legacy_auth_client_app
            ON legacy_auth_logs(client_app_used)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_legacy_auth_country
            ON legacy_auth_logs(country)
        """)
        # Unique constraint for deduplication
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_legacy_auth_unique
            ON legacy_auth_logs(timestamp, user_principal_name, ip_address, client_app_used)
        """)

        # ================================================================
        # Password Status indexes (Phase 226.3)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_status_last_change
            ON password_status(last_password_change)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_status_days
            ON password_status(days_since_change)
        """)
        # Unique constraint - one record per user, REPLACE on reimport
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_password_status_unique
            ON password_status(user_principal_name)
        """)

        # ================================================================
        # Entra ID Audit Log indexes (Phase 228)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entra_audit_timestamp
            ON entra_audit_log(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entra_audit_activity
            ON entra_audit_log(activity)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entra_audit_target
            ON entra_audit_log(target)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entra_audit_initiated_by
            ON entra_audit_log(initiated_by)
        """)
        # Unique constraint for deduplication
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_entra_audit_unique
            ON entra_audit_log(timestamp, activity, target)
        """)

        # MFA Changes indexes (Phase 231)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mfa_timestamp
            ON mfa_changes(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mfa_user
            ON mfa_changes(user)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mfa_activity
            ON mfa_changes(activity_display_name)
        """)

        # Risky Users indexes (Phase 231)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risky_user
            ON risky_users(user_principal_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risky_level
            ON risky_users(risk_level)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risky_state
            ON risky_users(risk_state)
        """)

        # Verification Summary indexes (Phase 241)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_log_type
            ON verification_summary(log_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_verified_at
            ON verification_summary(verified_at)
        """)

        # Quality Check Summary indexes (Phase 1.2)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality_check_table_name
            ON quality_check_summary(table_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality_check_created_at
            ON quality_check_summary(created_at)
        """)

        # Status Code Reference indexes (Phase 1.3)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_code_log_type
            ON status_code_reference(log_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_code_field_name
            ON status_code_reference(field_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_code_lookup
            ON status_code_reference(log_type, field_name, code_value)
        """)

        # Schema Versions indexes (Phase 1.3)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_versions_log_type
            ON schema_versions(log_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_versions_detected_date
            ON schema_versions(detected_date)
        """)

        # ================================================================
        # Transport Rules indexes (Phase 249)
        # Critical for exfiltration detection queries
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_state
            ON transport_rules(state)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_redirect
            ON transport_rules(redirect_message_to)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_bcc
            ON transport_rules(blind_copy_to)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_cc
            ON transport_rules(copy_to)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_scl
            ON transport_rules(set_scl)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transport_rules_when_changed
            ON transport_rules(when_changed)
        """)

        # ================================================================
        # Conditional Access Policies indexes (Phase 249)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ca_policies_state
            ON conditional_access_policies(state)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ca_policies_modified
            ON conditional_access_policies(modified_datetime)
        """)

        # ================================================================
        # Application Registrations indexes (Phase 249)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_app_reg_app_id
            ON application_registrations(app_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_app_reg_publisher
            ON application_registrations(publisher_domain)
        """)

        # ================================================================
        # Service Principals indexes (Phase 249)
        # ================================================================
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_svc_principal_app_id
            ON service_principals(app_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_svc_principal_type
            ON service_principals(service_principal_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_svc_principal_enabled
            ON service_principals(account_enabled)
        """)

        # ================================================================
        # Timeline Persistence indexes (Phase 260)
        # ================================================================
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


if __name__ == "__main__":
    # Quick demo
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        db = IRLogDatabase(case_id="PIR-DEMO-2025-001", base_path=tmpdir)
        path = db.create()
        print(f"Created database: {path}")
        print(f"Stats: {db.get_stats()}")
        print(f"Exists: {db.exists}")
