# M365 IR Data Enhancements - Requirements Specification

**Document Version**: 1.0
**Created**: 2026-01-08
**Author**: Data Analyst Agent (handoff from M365 IR Agent)
**For**: SRE Principal Engineer Agent
**Case Reference**: PIR-FYNA-2025-12-08

---

## Executive Summary

During PIR-FYNA-2025-12-08 investigation, four lessons were identified that require data/tooling enhancements to prevent future IR analysis errors. This document provides TDD-ready specifications for implementation.

---

## Background Context

### Source Case: PIR-FYNA-2025-12-08 (Fyna Foods AitM Attack)

**What happened**:
- AitM (Adversary-in-the-Middle) attack detected via Safari-on-Windows forensic signature
- 81 login attempts from attacker IPs (93.127.215.4, 45.129.35.103, etc.)
- Original PIR incorrectly stated "BREACH CONFIRMED" due to data interpretation errors

**Root causes of analysis errors**:
1. PowerShell export contained `.NET object type names` instead of actual status values
2. `conditional_access_status = 'notApplied'` was misinterpreted as "successful login"
3. UAL/mailbox logs had shorter retention than sign-in logs, creating undetected forensic gap
4. File naming pattern changes between export versions caused import failures

---

## Requirement 1: Log Coverage Summary Table

### Purpose
Provide instant visibility into forensic coverage gaps during IR triage. Prevents analysts from missing that different log types have different retention windows.

### Database Location
`{case_dir}/{case_id}_logs.db`

### Schema Specification

```sql
CREATE TABLE IF NOT EXISTS log_coverage_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT NOT NULL UNIQUE,
    earliest_timestamp TEXT NOT NULL,
    latest_timestamp TEXT NOT NULL,
    total_records INTEGER NOT NULL,
    coverage_days INTEGER NOT NULL,
    expected_days INTEGER DEFAULT 90,
    gap_detected BOOLEAN DEFAULT FALSE,
    gap_description TEXT,
    last_updated TEXT NOT NULL
);

CREATE INDEX idx_coverage_log_type ON log_coverage_summary(log_type);
CREATE INDEX idx_coverage_gap ON log_coverage_summary(gap_detected);
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `log_type` | TEXT | One of: sign_in, unified_audit_log, mailbox_audit, entra_audit, inbox_rules, oauth, legacy_auth, password_status, risky_users |
| `earliest_timestamp` | TEXT | ISO8601 timestamp of oldest record |
| `latest_timestamp` | TEXT | ISO8601 timestamp of newest record |
| `total_records` | INTEGER | Count of records for this log type |
| `coverage_days` | INTEGER | Calculated: `(latest - earliest).days` |
| `expected_days` | INTEGER | Expected retention (default 90, configurable) |
| `gap_detected` | BOOLEAN | TRUE if `coverage_days < expected_days * 0.8` (80% threshold) |
| `gap_description` | TEXT | Human-readable gap explanation |
| `last_updated` | TEXT | ISO8601 timestamp of last refresh |

### Population Logic

Function: `update_log_coverage_summary(db_path: str) -> dict`

```python
def update_log_coverage_summary(db_path: str) -> dict:
    """
    Scan all log tables and populate/update log_coverage_summary.

    Returns:
        dict with keys: 'tables_scanned', 'gaps_detected', 'coverage_report'
    """
    LOG_TABLES = {
        'sign_in_logs': ('timestamp', 'sign_in'),
        'unified_audit_log': ('timestamp', 'unified_audit_log'),
        'mailbox_audit_log': ('timestamp', 'mailbox_audit'),
        'entra_audit_log': ('timestamp', 'entra_audit'),
        'inbox_rules': ('created_date', 'inbox_rules'),
        'oauth_consents': ('consent_timestamp', 'oauth'),
        'legacy_auth_logs': ('timestamp', 'legacy_auth'),
        'password_status': ('last_password_change', 'password_status'),
        'risky_users': ('risk_last_updated', 'risky_users'),
    }

    # For each table:
    # 1. Query MIN(timestamp), MAX(timestamp), COUNT(*)
    # 2. Calculate coverage_days
    # 3. Compare to expected_days
    # 4. Set gap_detected and gap_description
    # 5. UPSERT into log_coverage_summary
```

### Integration Point
Call `update_log_coverage_summary()` at end of `import_logs()` in:
- File: `claude/tools/m365_ir/m365_log_parser.py`
- Function: `import_logs()` (after all log types imported)

### TDD Test Cases

```python
# File: tests/m365_ir/test_log_coverage_summary.py

class TestLogCoverageSummary:

    def test_creates_table_if_not_exists(self, temp_db):
        """Table should be created on first run."""
        update_log_coverage_summary(temp_db)
        tables = get_tables(temp_db)
        assert 'log_coverage_summary' in tables

    def test_calculates_coverage_days_correctly(self, temp_db):
        """Coverage days = latest - earliest timestamps."""
        # Insert sign_in_logs with known date range
        insert_sign_in_logs(temp_db, [
            {'timestamp': '2025-11-10T00:00:00', ...},
            {'timestamp': '2026-01-08T00:00:00', ...},
        ])
        update_log_coverage_summary(temp_db)

        result = query_coverage(temp_db, 'sign_in')
        assert result['coverage_days'] == 59  # Nov 10 to Jan 8

    def test_detects_gap_when_below_threshold(self, temp_db):
        """Gap detected when coverage < 80% of expected."""
        # Insert UAL with only 32 days coverage
        insert_ual_logs(temp_db, start='2025-12-07', end='2026-01-08')
        update_log_coverage_summary(temp_db)

        result = query_coverage(temp_db, 'unified_audit_log')
        assert result['gap_detected'] == True
        assert result['coverage_days'] == 32
        assert '32 days' in result['gap_description']

    def test_no_gap_when_coverage_sufficient(self, temp_db):
        """No gap when coverage >= 80% of expected."""
        insert_sign_in_logs(temp_db, start='2025-10-10', end='2026-01-08')
        update_log_coverage_summary(temp_db)

        result = query_coverage(temp_db, 'sign_in')
        assert result['gap_detected'] == False

    def test_handles_empty_table(self, temp_db):
        """Empty tables should show 0 records, no crash."""
        # Create empty risky_users table
        create_empty_table(temp_db, 'risky_users')
        update_log_coverage_summary(temp_db)

        result = query_coverage(temp_db, 'risky_users')
        assert result['total_records'] == 0
        assert result['earliest_timestamp'] is None

    def test_upserts_on_reimport(self, temp_db):
        """Re-running should update, not duplicate."""
        insert_sign_in_logs(temp_db, count=100)
        update_log_coverage_summary(temp_db)

        insert_sign_in_logs(temp_db, count=50)  # Add more
        update_log_coverage_summary(temp_db)

        count = count_coverage_rows(temp_db, 'sign_in')
        assert count == 1  # Only one row
```

---

## Requirement 2: Auth Success Indicator View

### Purpose
Eliminate ambiguity in authentication status interpretation. The field `conditional_access_status = 'notApplied'` does NOT mean successful authentication - it means no CA policy evaluated the login.

### Current Problem

| conditional_access_status | Misinterpretation | Correct Interpretation |
|---------------------------|-------------------|------------------------|
| `success` | Login succeeded | CA policy passed, auth confirmed |
| `failure` | Login failed | CA policy blocked |
| `notApplied` | **Login succeeded** (WRONG) | No CA policy evaluated - auth status UNKNOWN |

### Schema Specification

```sql
CREATE VIEW IF NOT EXISTS v_sign_in_auth_status AS
SELECT
    *,
    CASE
        -- CA policy explicitly passed = confirmed success
        WHEN conditional_access_status = 'success' THEN 'CONFIRMED_SUCCESS'

        -- CA policy blocked = confirmed failure
        WHEN conditional_access_status = 'failure' THEN 'CA_BLOCKED'

        -- No CA policy but no error code = likely success (legacy/excluded apps)
        WHEN conditional_access_status = 'notApplied'
             AND (status_error_code IS NULL OR status_error_code = 0)
        THEN 'LIKELY_SUCCESS_NO_CA'

        -- Error code present = failed auth
        WHEN status_error_code IS NOT NULL AND status_error_code != 0
        THEN 'AUTH_FAILED'

        -- Cannot determine
        ELSE 'INDETERMINATE'
    END as auth_determination,

    CASE
        WHEN conditional_access_status = 'success' THEN 100
        WHEN conditional_access_status = 'failure' THEN 100
        WHEN conditional_access_status = 'notApplied' AND status_error_code = 0 THEN 60
        WHEN status_error_code != 0 THEN 90
        ELSE 0
    END as auth_confidence_pct

FROM sign_in_logs;
```

### Field Definitions

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `auth_determination` | TEXT | CONFIRMED_SUCCESS, CA_BLOCKED, LIKELY_SUCCESS_NO_CA, AUTH_FAILED, INDETERMINATE | Clear auth status |
| `auth_confidence_pct` | INTEGER | 0-100 | Confidence in the determination |

### Integration Point
Create view during database initialization in:
- File: `claude/tools/m365_ir/m365_log_parser.py`
- Function: `initialize_database()` or `create_schema()`

### TDD Test Cases

```python
# File: tests/m365_ir/test_auth_status_view.py

class TestAuthStatusView:

    def test_view_exists_after_init(self, temp_db):
        """View should exist after database initialization."""
        initialize_database(temp_db)
        views = get_views(temp_db)
        assert 'v_sign_in_auth_status' in views

    def test_confirmed_success_when_ca_success(self, temp_db):
        """CA status 'success' = CONFIRMED_SUCCESS."""
        insert_sign_in(temp_db, conditional_access_status='success')
        result = query_auth_view(temp_db)

        assert result['auth_determination'] == 'CONFIRMED_SUCCESS'
        assert result['auth_confidence_pct'] == 100

    def test_ca_blocked_when_ca_failure(self, temp_db):
        """CA status 'failure' = CA_BLOCKED."""
        insert_sign_in(temp_db, conditional_access_status='failure')
        result = query_auth_view(temp_db)

        assert result['auth_determination'] == 'CA_BLOCKED'
        assert result['auth_confidence_pct'] == 100

    def test_likely_success_when_notapplied_no_error(self, temp_db):
        """CA status 'notApplied' with no error = LIKELY_SUCCESS_NO_CA."""
        insert_sign_in(temp_db,
                      conditional_access_status='notApplied',
                      status_error_code=0)
        result = query_auth_view(temp_db)

        assert result['auth_determination'] == 'LIKELY_SUCCESS_NO_CA'
        assert result['auth_confidence_pct'] == 60  # Lower confidence

    def test_auth_failed_when_error_code_present(self, temp_db):
        """Non-zero error code = AUTH_FAILED."""
        insert_sign_in(temp_db, status_error_code=50126)  # Invalid credentials
        result = query_auth_view(temp_db)

        assert result['auth_determination'] == 'AUTH_FAILED'
        assert result['auth_confidence_pct'] == 90

    def test_indeterminate_when_no_data(self, temp_db):
        """Missing status fields = INDETERMINATE."""
        insert_sign_in(temp_db,
                      conditional_access_status=None,
                      status_error_code=None)
        result = query_auth_view(temp_db)

        assert result['auth_determination'] == 'INDETERMINATE'
        assert result['auth_confidence_pct'] == 0

    def test_attacker_ip_analysis_uses_view(self, temp_db):
        """Real-world test: AitM IPs should show correct status."""
        # Insert attacker login attempts (Safari on Windows)
        insert_sign_in(temp_db,
                      ip_address='93.127.215.4',
                      browser='Safari',
                      os='Windows10',
                      conditional_access_status='notApplied',
                      status_error_code=0)

        result = query_auth_view(temp_db, ip='93.127.215.4')

        # Should NOT show as CONFIRMED_SUCCESS
        assert result['auth_determination'] != 'CONFIRMED_SUCCESS'
        assert result['auth_determination'] == 'LIKELY_SUCCESS_NO_CA'
        assert result['auth_confidence_pct'] < 100
```

---

## Requirement 3: PowerShell Export Validation

### Purpose
Detect corrupted exports where PowerShell failed to expand .NET objects, resulting in type names like `Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus` instead of actual values.

### Current Problem
Original PIR-FYNA export had Status field containing:
```
Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus
```
Instead of actual status values. This led to incorrect breach determination.

### Detection Pattern
```python
POWERSHELL_OBJECT_PATTERN = r'^Microsoft\.(Graph\.)?PowerShell\.Models\.'
```

### Schema Addition to quality_check_summary

Add column to existing table:
```sql
ALTER TABLE quality_check_summary ADD COLUMN powershell_object_detected BOOLEAN DEFAULT FALSE;
ALTER TABLE quality_check_summary ADD COLUMN powershell_object_fields TEXT;  -- JSON array
```

### Validation Logic

Function: `check_powershell_object_corruption(db_path: str, table: str) -> dict`

```python
def check_powershell_object_corruption(db_path: str, table: str) -> dict:
    """
    Scan text columns for PowerShell object type patterns.

    Returns:
        {
            'corrupted': bool,
            'affected_fields': ['status', 'risk_detail', ...],
            'sample_values': {'status': 'Microsoft.Graph.PowerShell...'}
        }
    """
    PATTERN = r'^Microsoft\.(Graph\.)?PowerShell\.Models\.'

    # Get all TEXT columns from table schema
    # For each column, check if any value matches PATTERN
    # Return affected columns and sample corrupted values
```

### Integration Points
1. Call during import in `claude/tools/m365_ir/m365_log_parser.py`
2. Add warning to import summary if detected
3. Update `quality_check_summary` table

### TDD Test Cases

```python
# File: tests/m365_ir/test_powershell_validation.py

class TestPowerShellValidation:

    def test_detects_object_type_in_status(self, temp_db):
        """Should detect PowerShell object type in status field."""
        insert_sign_in(temp_db,
            status_failure_reason='Microsoft.Graph.PowerShell.Models.MicrosoftGraphSignInStatus')

        result = check_powershell_object_corruption(temp_db, 'sign_in_logs')

        assert result['corrupted'] == True
        assert 'status_failure_reason' in result['affected_fields']

    def test_detects_nested_graph_models(self, temp_db):
        """Should detect Microsoft.Graph.PowerShell.Models.* pattern."""
        insert_sign_in(temp_db,
            risk_detail='Microsoft.Graph.PowerShell.Models.MicrosoftGraphRiskDetail')

        result = check_powershell_object_corruption(temp_db, 'sign_in_logs')

        assert result['corrupted'] == True
        assert 'risk_detail' in result['affected_fields']

    def test_no_false_positive_on_valid_data(self, temp_db):
        """Should not flag valid status values."""
        insert_sign_in(temp_db,
            status_failure_reason='Invalid username or password',
            conditional_access_status='success')

        result = check_powershell_object_corruption(temp_db, 'sign_in_logs')

        assert result['corrupted'] == False
        assert result['affected_fields'] == []

    def test_updates_quality_check_summary(self, temp_db):
        """Should update quality_check_summary with detection results."""
        insert_sign_in(temp_db,
            status_failure_reason='Microsoft.Graph.PowerShell.Models.Something')

        check_powershell_object_corruption(temp_db, 'sign_in_logs')

        summary = query_quality_summary(temp_db, 'sign_in_logs')
        assert summary['powershell_object_detected'] == True
        assert 'status_failure_reason' in summary['powershell_object_fields']

    def test_returns_sample_values_for_debugging(self, temp_db):
        """Should return sample corrupted values for analyst review."""
        corrupted_value = 'Microsoft.Graph.PowerShell.Models.BadObject'
        insert_sign_in(temp_db, status_failure_reason=corrupted_value)

        result = check_powershell_object_corruption(temp_db, 'sign_in_logs')

        assert corrupted_value in str(result['sample_values'])
```

---

## Requirement 4: File Pattern Handling (Already Implemented)

### Status: COMPLETE

File patterns in `m365_log_parser.py` already updated to handle both:
- Zero-padded: `01_SignInLogs.csv`
- Non-padded: `1_SignInLogs.csv`

### Current Implementation
```python
LOG_FILE_PATTERNS = {
    LogType.SIGNIN: r"0?1_.*SignInLogs\.csv$",
    LogType.ENTRA_AUDIT: r"0?2_.*(?:Directory)?AuditLogs\.csv$",
    # ... etc
}
```

### Verification Test (Add if missing)
```python
def test_accepts_zero_padded_filenames():
    assert matches_pattern('01_SignInLogs.csv', LogType.SIGNIN)
    assert matches_pattern('1_SignInLogs.csv', LogType.SIGNIN)
    assert matches_pattern('01_AllUsers_SignInLogs.csv', LogType.SIGNIN)
```

---

## Implementation Priority

| Requirement | Priority | Effort | Impact | Status |
|-------------|----------|--------|--------|--------|
| Auth Success View | HIGH | Low (SQL view) | Prevents breach misclassification | ✅ DONE |
| Log Coverage Summary | HIGH | Medium | Prevents forensic gap blindness | ✅ DONE |
| PowerShell Validation | MEDIUM | Medium | Prevents corrupt data analysis | ✅ DONE |
| File Patterns | DONE | - | Already implemented | ✅ DONE |

---

## Acceptance Criteria

### Overall
- [x] All tests pass (`pytest tests/m365_ir/ -v`) - **144 tests passing**
- [x] No regressions in existing import functionality
- [ ] Documentation updated in agent markdown

### Per Requirement
1. **Log Coverage Summary** ✅
   - [x] Table created on first import
   - [x] All log types scanned and summarized
   - [x] Gaps detected when coverage < 80%
   - [x] Human-readable gap descriptions

2. **Auth Success View** ✅
   - [x] View created during DB init
   - [x] 5 auth_determination values correctly assigned
   - [x] Confidence percentages accurate
   - [x] Query performance acceptable (<100ms for 50K rows)

3. **PowerShell Validation** ✅
   - [x] Pattern detection works for all known .NET types
   - [x] No false positives on valid data
   - [x] Results stored in quality_check_summary
   - [x] Warning displayed during import if detected

---

## File Locations

| Component | Path |
|-----------|------|
| Log Parser | `claude/tools/m365_ir/m365_log_parser.py` |
| Log Database | `claude/tools/m365_ir/log_database.py` |
| Log Coverage | `claude/tools/m365_ir/log_coverage.py` (NEW) |
| PS Validation | `claude/tools/m365_ir/powershell_validation.py` (NEW) |
| Tests | `claude/tools/m365_ir/tests/test_*.py` |
| Agent Docs | `claude/agents/m365_incident_response_agent.md` |
| This Spec | `claude/data/project_status/active/M365_IR_DATA_ENHANCEMENTS.md` |

---

## Implementation Summary (Phase 258)

**Completed**: 2026-01-08 by SRE Principal Engineer Agent

### New Files Created:
- `claude/tools/m365_ir/log_coverage.py` - Log coverage gap detection
- `claude/tools/m365_ir/powershell_validation.py` - PowerShell .NET object detection
- `claude/tools/m365_ir/tests/test_auth_status_view.py` - 8 tests
- `claude/tools/m365_ir/tests/test_log_coverage_summary.py` - 8 tests
- `claude/tools/m365_ir/tests/test_powershell_validation.py` - 7 tests

### Modified Files:
- `claude/tools/m365_ir/log_database.py` - Added v_sign_in_auth_status view
- `claude/tools/m365_ir/tests/test_m365_log_parser.py` - Fixed deprecated LogType.AUDIT test

### Test Results:
- **144 tests passing**
- **0 failures**
- **0.93s runtime**

---

**Document Complete - Implementation Finished**
