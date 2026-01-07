"""
Populate Status Code Reference Table - Phase 1.3

This script populates the status_code_reference table with Microsoft Entra ID
(formerly Azure AD) status codes from official Microsoft documentation.

Usage:
    python3 claude/tools/m365_ir/populate_status_codes.py <db_path>

Source: https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes
Date: 2026-01-06
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path


# Microsoft Entra ID Status Codes (AADSTS)
# Source: https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes
STATUS_CODES = [
    # Critical Authentication Failures
    ('sign_in_logs', 'status_error_code', '50126', 'InvalidUserNameOrPassword - Invalid username or password', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50053', 'IdsLocked - Account locked due to repeated failed sign-ins', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50055', 'InvalidPasswordExpiredPassword - Password expired', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50057', 'UserDisabled - User account disabled', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50058', 'UserInformationNotProvided - Session info insufficient for SSO', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50034', 'UserAccountNotFound - Account not found in directory', 'CRITICAL'),

    # Conditional Access & MFA
    ('sign_in_logs', 'status_error_code', '50076', 'UserStrongAuthClientAuthNRequired - MFA required', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '50079', 'UserStrongAuthEnrollmentRequired - MFA enrollment required', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '50074', 'UserStrongAuthClientAuthNRequiredInterrupt - MFA challenge failed', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '53003', 'BlockedByConditionalAccess - Blocked by Conditional Access', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '530035', 'BlockedBySecurityDefaults - Blocked by security defaults', 'WARNING'),

    # Application & Resource Errors
    ('sign_in_logs', 'status_error_code', '700016', 'UnauthorizedClient_DoesNotMatchRequest - App not found', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50001', 'InvalidResource - Resource disabled or missing', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '500011', 'InvalidResourceServicePrincipalNotFound - Resource principal not found', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '500014', 'InvalidResourceServicePrincipalDisabled - Service principal disabled', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '70001', 'UnauthorizedClient - Application disabled', 'CRITICAL'),

    # Token & Grant Errors
    ('sign_in_logs', 'status_error_code', '50173', 'GrantExpiredRevoked - Grant expired or revoked', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '70008', 'ExpiredOrRevokedGrant - Refresh token expired due to inactivity', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '700082', 'ExpiredOrRevokedGrantInactiveToken - Token inactive', 'INFO'),
    ('sign_in_logs', 'status_error_code', '70043', 'BadTokenDueToSignInFrequency - Token expired per CA policy', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '70011', 'InvalidScope - Invalid scope requested', 'WARNING'),

    # Consent & Authorization
    ('sign_in_logs', 'status_error_code', '65001', 'DelegationDoesNotExist - User/admin consent missing', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '65004', 'UserDeclinedConsent - User declined consent', 'INFO'),
    ('sign_in_logs', 'status_error_code', '90094', 'AdminConsentRequired - Admin consent required', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50105', 'EntitlementGrantsNotFound - User not assigned to app role', 'CRITICAL'),

    # Configuration & Protocol
    ('sign_in_logs', 'status_error_code', '50011', 'InvalidReplyTo - Reply address misconfigured', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '50012', 'AuthenticationFailed - Cert/auth failed', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '75005', 'Saml2MessageInvalid - Invalid SAML request', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '750054', 'SAMLRequestNotPresent - Missing SAML request/response', 'CRITICAL'),

    # User Account Errors
    ('sign_in_logs', 'status_error_code', '50020', 'UserUnauthorized - User unauthorized from IDP', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '50014', 'GuestUserInPendingState - Guest account pending', 'WARNING'),
    ('sign_in_logs', 'status_error_code', '16000', 'InteractionRequired - External user interaction required', 'INFO'),
    ('sign_in_logs', 'status_error_code', '50500208', 'InvalidLoginDomain - Invalid login domain', 'WARNING'),

    # Tenant & Policy
    ('sign_in_logs', 'status_error_code', '500021', 'TenantRestrictionDenied - Tenant not in allowed list', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '500212', 'NotAllowedByOutboundPolicyTenant - Outbound policy blocks access', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '500213', 'NotAllowedByInboundPolicyTenant - Inbound policy blocks access', 'CRITICAL'),

    # Server & Transient
    ('sign_in_logs', 'status_error_code', '50000', 'TokenIssuanceError - Service error', 'CRITICAL'),
    ('sign_in_logs', 'status_error_code', '50033', 'RetryableError - Transient error', 'INFO'),
    ('sign_in_logs', 'status_error_code', '90033', 'MsodsServiceUnavailable - Service unavailable', 'INFO'),
    ('sign_in_logs', 'status_error_code', '90055', 'TenantThrottlingError - Too many requests', 'INFO'),

    # Success code
    ('sign_in_logs', 'status_error_code', '0', 'Success - Authentication successful', 'INFO'),

    # Synthetic error codes (generated by log_importer.py when actual AADSTS code missing)
    ('sign_in_logs', 'status_error_code', '1', 'Non-success status (synthetic code - actual error code not provided in source data)', 'WARNING'),

    # Conditional Access Status Codes
    ('sign_in_logs', 'conditional_access_status', 'success', 'Conditional Access policy satisfied', 'INFO'),
    ('sign_in_logs', 'conditional_access_status', 'failure', 'Conditional Access policy blocked sign-in', 'CRITICAL'),
    ('sign_in_logs', 'conditional_access_status', 'notApplied', 'No Conditional Access policy applied', 'INFO'),

    # Sign-in Status Codes (high-level)
    ('sign_in_logs', 'status', 'Success', 'Sign-in successful', 'INFO'),
    ('sign_in_logs', 'status', 'Failure', 'Sign-in failed', 'WARNING'),
    ('sign_in_logs', 'status', 'Interrupted', 'Sign-in interrupted (MFA/CA)', 'WARNING'),

    # Unified Audit Log - Common Operations
    ('unified_audit_log', 'Operation', 'MailItemsAccessed', 'Mail items accessed (potential exfiltration)', 'WARNING'),
    ('unified_audit_log', 'Operation', 'FileSyncDownloadedFull', 'Full file sync downloaded (potential exfiltration)', 'WARNING'),
    ('unified_audit_log', 'Operation', 'FileAccessed', 'File accessed', 'INFO'),
    ('unified_audit_log', 'Operation', 'FileDownloaded', 'File downloaded', 'WARNING'),
    ('unified_audit_log', 'Operation', 'UserLoggedIn', 'User logged in', 'INFO'),
    ('unified_audit_log', 'Operation', 'Add user', 'User added to directory', 'WARNING'),
    ('unified_audit_log', 'Operation', 'Update user', 'User updated in directory', 'INFO'),
    ('unified_audit_log', 'Operation', 'Delete user', 'User deleted from directory', 'CRITICAL'),
    ('unified_audit_log', 'Operation', 'Add member to role', 'Member added to admin role', 'CRITICAL'),
    ('unified_audit_log', 'Operation', 'Remove member from role', 'Member removed from admin role', 'WARNING'),
]


def populate_status_codes(db_path: str, replace_existing: bool = False) -> None:
    """
    Populate status_code_reference table with Microsoft Entra ID codes.

    Args:
        db_path: Path to SQLite database
        replace_existing: If True, delete existing codes before populating
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verify table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='status_code_reference'
        """)
        if not cursor.fetchone():
            raise ValueError("status_code_reference table does not exist")

        if replace_existing:
            print("Clearing existing status codes...")
            cursor.execute("DELETE FROM status_code_reference")
            conn.commit()

        # Insert status codes
        now = datetime.now().isoformat()
        inserted = 0
        skipped = 0

        for log_type, field_name, code_value, meaning, severity in STATUS_CODES:
            try:
                cursor.execute("""
                    INSERT INTO status_code_reference
                    (log_type, field_name, code_value, meaning, severity,
                     first_seen, last_validated, deprecated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_type,
                    field_name,
                    code_value,
                    meaning,
                    severity,
                    now,
                    now,
                    0
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                # Code already exists (UNIQUE constraint)
                skipped += 1

        conn.commit()

        print(f"\n✅ Status code population complete!")
        print(f"   Inserted: {inserted} codes")
        print(f"   Skipped: {skipped} codes (already exist)")
        print(f"   Total: {inserted + skipped} codes processed")
        print(f"\n📊 Breakdown:")
        print(f"   Sign-in error codes: {sum(1 for _, f, _, _, _ in STATUS_CODES if f == 'status_error_code')}")
        print(f"   Conditional Access codes: {sum(1 for _, f, _, _, _ in STATUS_CODES if f == 'conditional_access_status')}")
        print(f"   Status codes: {sum(1 for _, f, _, _, _ in STATUS_CODES if f == 'status')}")
        print(f"   Audit log operations: {sum(1 for lt, _, _, _, _ in STATUS_CODES if lt == 'unified_audit_log')}")

    finally:
        conn.close()


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 populate_status_codes.py <db_path> [--replace]")
        print("\nExample:")
        print("  python3 claude/tools/m365_ir/populate_status_codes.py /path/to/case.db")
        sys.exit(1)

    db_path = sys.argv[1]
    replace_existing = '--replace' in sys.argv

    try:
        populate_status_codes(db_path, replace_existing=replace_existing)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
