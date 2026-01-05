#!/usr/bin/env python3
"""
AccountValidator - Enforces systematic validation of M365 compromised accounts

Phase 230: Account Validator Implementation
Requirements: PYTHON_VALIDATOR_REQUIREMENTS.md (FR-1 through FR-5)

PURPOSE: Prevent assumption-based analytical errors by enforcing hard validation
checks at the code level. Cannot skip validation steps - raises exceptions.

CRITICAL: This tool prevents the ben@oculus.info error from PIR-OCULUS-2025-01
where IR agent assumed account was disabled long ago without checking actual
disable timestamp in entra_audit_log.

ENFORCEMENT MECHANISMS:
1. Cannot skip validation steps (raises ValidationError if data missing)
2. Cannot assume timestamps (requires actual query results)
3. Cannot ignore logic errors (automatic sanity checks)
4. Cannot generate report without passing validation
5. All findings must cite sources
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from claude.tools.m365_ir.assumption_logger import AssumptionLog
from claude.tools.m365_ir.validation_checks import validate_timeline_logic


class ValidationError(Exception):
    """
    Raised when validation fails or required data is missing.

    This exception prevents the validator from proceeding when:
    - Critical timestamps are missing
    - Timeline logic errors are detected
    - Disproven assumptions exist
    - Required data sources are unavailable
    """
    pass


class AccountValidator:
    """
    Main validator class - enforces all requirements (FR-1 through FR-5).

    CANNOT skip validation steps. Raises exceptions if data missing.
    """

    def __init__(self, db_path: str, account_email: str):
        """
        Initialize validator for a specific account.

        Args:
            db_path: Path to IR investigation database
            account_email: User principal name to validate

        Raises:
            ValidationError: If database doesn't exist or account not found
        """
        self.db_path = db_path
        self.account = account_email
        self.validated = False
        self.validation_results: Dict[str, Any] = {}
        self.assumption_log = AssumptionLog()

        # Verify database exists
        if not Path(db_path).exists():
            raise ValidationError(f"Database not found: {db_path}")

    def _connect(self) -> sqlite3.Connection:
        """Create database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _validate_lifecycle(self) -> Dict[str, Any]:
        """
        FR-1: Account Lifecycle Validation

        MUST verify:
        - Creation date (cannot assume)
        - Password history (calculate age, don't infer)
        - Status changes (CRITICAL - check entra_audit_log for disable events)

        Returns:
            Dict with lifecycle data and sources

        Raises:
            ValidationError: If currently disabled but no disable event found
        """
        conn = self._connect()
        cursor = conn.cursor()

        # FR-1.1: Query current account status
        cursor.execute("""
            SELECT created_datetime, last_password_change, account_enabled, days_since_change
            FROM password_status
            WHERE user_principal_name = ?
        """, (self.account,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValidationError(
                f"Account {self.account} not found in password_status table. "
                "Cannot validate account that doesn't exist in database."
            )

        created_datetime = row['created_datetime']
        last_password_change = row['last_password_change']
        account_enabled = bool(row['account_enabled'])
        password_age_days = row['days_since_change']

        # FR-1.3: Account Status Changes (CRITICAL - this is where failure occurred)
        cursor.execute("""
            SELECT timestamp, activity, initiated_by
            FROM entra_audit_log
            WHERE target = ? AND activity IN ('Disable account', 'Enable account')
            ORDER BY timestamp
        """, (self.account,))

        status_changes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # CRITICAL CHECK: If currently disabled, MUST have disable timestamp
        if not account_enabled:
            disable_events = [e for e in status_changes if e['activity'] == 'Disable account']

            if not disable_events:
                raise ValidationError(
                    f"Account {self.account} is currently DISABLED but no disable event found in entra_audit_log.\n\n"
                    "Cannot determine when account was disabled.\n\n"
                    "Possible causes:\n"
                    "1. Disable event predates log retention period\n"
                    "2. Manual AD change not captured in audit logs\n"
                    "3. Database query error\n\n"
                    "Action required:\n"
                    "- If predates logs: Document as 'disable date unknown (predates retention)'\n"
                    "- If manual change: Check AD directly for disable date\n"
                    "- If query error: Verify entra_audit_log contains data for incident period"
                )

            # Get most recent disable event
            latest_disable = max(disable_events, key=lambda x: x['timestamp'])
            disable_timestamp = latest_disable['timestamp']
            disabled_by = latest_disable['initiated_by']
        else:
            disable_timestamp = None
            disabled_by = None

        # Check for re-enable events
        enable_events = [e for e in status_changes if e['activity'] == 'Enable account']
        if enable_events and not account_enabled:
            # Account was re-enabled at some point but is now disabled again
            latest_enable = max(enable_events, key=lambda x: x['timestamp'])
            re_enabled = True
            re_enabled_date = latest_enable['timestamp']
        elif enable_events and account_enabled:
            # Account is currently enabled, was disabled and re-enabled
            latest_enable = max(enable_events, key=lambda x: x['timestamp'])
            re_enabled = True
            re_enabled_date = latest_enable['timestamp']
        else:
            re_enabled = False
            re_enabled_date = None

        return {
            'created_date': created_datetime,
            'password_last_change': last_password_change,
            'password_age_days': password_age_days,
            'current_status': 'Enabled' if account_enabled else 'Disabled',
            'disabled_date': disable_timestamp,
            'disabled_by': disabled_by,
            're_enabled': re_enabled,
            're_enabled_date': re_enabled_date,
            'status_change_count': len(status_changes),
            'source': 'password_status, entra_audit_log'
        }

    def _validate_compromise(self) -> Dict[str, Any]:
        """
        FR-2: Compromise Evidence Collection

        MUST query:
        - Foreign login timeline (first/last timestamps)
        - SMTP abuse events
        All from actual database queries, no assumptions

        Returns:
            Dict with compromise evidence and sources
        """
        conn = self._connect()
        cursor = conn.cursor()

        # FR-2.1: Foreign Login Timeline
        cursor.execute("""
            SELECT timestamp, ip_address, location_country
            FROM sign_in_logs
            WHERE user_principal_name = ?
              AND location_country NOT IN ('AU', 'Australia')
            ORDER BY timestamp
        """, (self.account,))

        foreign_logins = [dict(row) for row in cursor.fetchall()]

        if foreign_logins:
            first_foreign = min(foreign_logins, key=lambda x: x['timestamp'])
            last_foreign = max(foreign_logins, key=lambda x: x['timestamp'])

            foreign_data = {
                'first_foreign_login': first_foreign['timestamp'],
                'last_foreign_login': last_foreign['timestamp'],
                'total_foreign_logins': len(foreign_logins),
                'countries': list(set(f['location_country'] for f in foreign_logins)),
                'source': 'sign_in_logs'
            }
        else:
            foreign_data = {
                'first_foreign_login': None,
                'last_foreign_login': None,
                'total_foreign_logins': 0,
                'countries': [],
                'source': 'sign_in_logs'
            }

        # FR-2.2: SMTP Abuse Detection
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM legacy_auth_logs
            WHERE user_principal_name = ?
              AND client_app_used LIKE '%SMTP%'
        """, (self.account,))

        smtp_count = cursor.fetchone()['count']
        conn.close()

        return {
            'foreign_logins': foreign_data,
            'smtp_abuse_count': smtp_count,
            'source': 'sign_in_logs, legacy_auth_logs'
        }

    def validate(self) -> Dict[str, Any]:
        """
        Run full validation - CANNOT skip steps.

        Executes:
        1. FR-1: Account lifecycle validation
        2. FR-2: Compromise evidence collection
        3. FR-3: Timeline sanity checks (automatic)
        4. FR-4: Check for disproven assumptions

        Returns:
            Dict with complete validation results

        Raises:
            ValidationError: If validation fails or data missing
        """
        # FR-1: Account lifecycle
        self.validation_results['lifecycle'] = self._validate_lifecycle()

        # FR-2: Compromise evidence
        self.validation_results['compromise'] = self._validate_compromise()

        # FR-3: Timeline sanity checks
        sanity_check = validate_timeline_logic(
            lifecycle=self.validation_results['lifecycle'],
            compromise=self.validation_results['compromise']
        )

        # If critical errors found, raise ValidationError
        if not sanity_check['timeline_valid']:
            # Build error message
            error_messages = [e['message'] for e in sanity_check['errors']]
            raise ValidationError(
                f"Timeline logic errors detected for {self.account}:\n\n" +
                "\n".join(f"- {msg}" for msg in error_messages)
            )

        self.validation_results['sanity_check'] = sanity_check

        # Determine root cause category
        lifecycle = self.validation_results['lifecycle']
        compromise = self.validation_results['compromise']

        # Check if password policy failure
        if lifecycle['password_age_days'] > 365 and compromise['foreign_logins']['total_foreign_logins'] > 0:
            root_cause = 'PASSWORD_POLICY_FAILURE'
        elif lifecycle['current_status'] == 'Disabled' and lifecycle.get('disabled_during_attack'):
            root_cause = 'REMEDIATION'
        else:
            root_cause = 'UNKNOWN'

        self.validation_results['root_cause_category'] = root_cause

        # FR-4: Check for disproven assumptions
        if self.assumption_log.has_disproven_assumptions():
            disproven = self.assumption_log.get_disproven_assumptions()
            raise ValidationError(
                f"Cannot proceed with disproven assumptions:\n" +
                "\n".join(f"- {a['assumption']}: {a['result']}" for a in disproven)
            )

        self.validated = True
        return self.validation_results

    def generate_report(self) -> Dict[str, Any]:
        """
        FR-5: Report generation - Only callable after successful validation.

        Returns:
            Dict with validated account report

        Raises:
            ValidationError: If validation not completed
        """
        if not self.validated:
            raise ValidationError(
                "Cannot generate report without completing validation. "
                "Call validate() first."
            )

        return {
            'account': self.account,
            'validated': True,
            'validation_timestamp': datetime.now().isoformat(),
            **self.validation_results,
            'assumptions_made': self.assumption_log.assumptions,
            'sources_queried': self._get_sources_used()
        }

    def _get_sources_used(self) -> List[str]:
        """Get list of all database tables queried during validation."""
        sources = set()

        if 'lifecycle' in self.validation_results:
            sources.add('password_status')
            sources.add('entra_audit_log')

        if 'compromise' in self.validation_results:
            sources.add('sign_in_logs')
            sources.add('legacy_auth_logs')

        return sorted(list(sources))
