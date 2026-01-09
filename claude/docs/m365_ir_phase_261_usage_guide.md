# Phase 261 M365 IR Usage Guide

**Version**: 1.0
**Date**: 2026-01-09
**Agent**: SRE Principal Engineer

---

## Overview

Phase 261 introduces critical fixes and enhancements to the M365 Incident Response tooling:

1. **Enhanced Auth Determination** - New `LIKELY_SUCCESS_RISKY` classification
2. **Post-Compromise Validation** - Automated 11-indicator analysis
3. **Risk Level Backfill** - Extract risk data from raw logs
4. **Duplicate Handling** - MERGE-based deduplication with audit trail

---

## Problem Solved

### The False Positive Issue

**Original Problem**: PIR-SGS-4241809 incorrectly classified high-risk sign-ins as blocked.

**Example**: edelaney@goodsams.org.au Turkey login (2025-11-25T04:55:50)
- **Old classification**: AUTH_FAILED (90% confidence) ❌ WRONG
- **New classification**: LIKELY_SUCCESS_RISKY (70% confidence, P1_IMMEDIATE) ✅ CORRECT

**Why this matters**:
- `RiskLevelDuringSignIn = "high"` is an ASSESSMENT by Identity Protection, NOT a BLOCK
- If `ConditionalAccessStatus = "notApplied"`, no CA policy evaluated the risk
- Result: The sign-in may have **SUCCEEDED** and requires investigation

---

## 1. Understanding LIKELY_SUCCESS_RISKY

### When This Classification Appears

A sign-in is classified as `LIKELY_SUCCESS_RISKY` when:
- Risk level is HIGH or MEDIUM (Identity Protection assessment)
- Conditional Access status is "notApplied" (no policy blocked it)
- Status error code is 0 or 1 (successful or interrupted)

### What It Means

This login is **risky but possibly successful**. It requires:
- **Priority**: P1_IMMEDIATE investigation
- **Confidence**: 70% (not 100% - absence of CA block doesn't guarantee success)
- **Action**: Immediate post-compromise validation

### Investigation Workflow

```sql
-- Query all LIKELY_SUCCESS_RISKY sign-ins
SELECT
    timestamp,
    user_principal_name,
    location_country,
    ip_address,
    risk_level,
    auth_determination,
    investigation_priority
FROM v_sign_in_auth_status
WHERE auth_determination = 'LIKELY_SUCCESS_RISKY'
  AND location_country NOT IN ('AU', 'US')  -- Filter by expected countries
ORDER BY timestamp DESC;
```

For each result:
1. Run post-compromise validation (see below)
2. Check for follow-on activity
3. Determine if account was compromised

---

## 2. Post-Compromise Validation

### Command Usage

```bash
python3 m365_ir_cli.py validate-compromise <CASE_ID> \
    --user <USER_EMAIL> \
    --timestamp <SIGNIN_TIME> \
    --ip <IP_ADDRESS>
```

### Example

```bash
python3 m365_ir_cli.py validate-compromise PIR-SGS-4241809 \
    --user edelaney@goodsams.org.au \
    --timestamp "2025-11-25T04:55:50" \
    --ip 46.252.102.34
```

### Output Interpretation

```
VERDICT: LIKELY_COMPROMISE
Confidence: 70%

Indicators Found (1/11):
  ✓ Follow On Signins
    Confidence: 70%
    Count: 2
```

**Verdicts**:
- `NO_COMPROMISE`: 0-1 indicators, ≤80% confidence
- `LIKELY_COMPROMISE`: 2-3 indicators, 70-90% confidence
- `CONFIRMED_COMPROMISE`: 4+ indicators, ≥95% confidence

### 11 Indicators Checked

| Indicator | Confidence | What It Detects |
|-----------|------------|-----------------|
| mailbox_access_from_ip | 80% | Mailbox access from sign-in IP |
| ual_operations_from_ip | 75% | UAL operations from sign-in IP |
| inbox_rules_created | 90% (forwarding), 70% (other) | Inbox rules created after sign-in |
| password_changed | 85% | Password changes after sign-in |
| follow_on_signins | 70% | Additional sign-ins from same IP |
| persistence_mechanisms | 85% | OAuth apps, delegate access |
| data_exfiltration | 80% | Large file downloads/shares |
| oauth_app_consents | 85% | OAuth app permissions granted |
| mfa_modifications | 90% | MFA settings changed |
| delegate_access_changes | 85% | Mailbox delegate permissions |
| orphan_ual_activity | 95% | UAL activity without sign-in (token theft) |

### Analysis Window

- **Immediate**: 60 minutes after sign-in
- **Extended**: 72 hours after sign-in (captures delayed attacker activity)

---

## 3. Duplicate Handling

### Identifying Duplicates

```bash
python3 m365_ir_cli.py identify-duplicates PIR-SGS-4241809
```

**Output**:
```
Duplicate groups: 4,222
Duplicate records: 5,621

Duplicate Groups:
1. zrayos@goodsams.org.au @ 2025-11-05T04:54:29
   IP: 60.242.11.126
   Record IDs: [18982, 18983, ...]
   Count: 13 duplicates
```

### Merging Duplicates

```bash
# Interactive (confirms before merging)
python3 m365_ir_cli.py merge-duplicates PIR-SGS-4241809

# Automatic (no confirmation)
python3 m365_ir_cli.py merge-duplicates PIR-SGS-4241809 --auto-apply

# Dry run (preview only)
python3 m365_ir_cli.py merge-duplicates PIR-SGS-4241809 --dry-run
```

### How MERGE Works

**Data preservation approach** (not DELETE):
1. Primary record (lowest ID) marked with `merge_status='primary'`
2. Secondary records marked with `merge_status='merged'` and `merged_into=primary_id`
3. Timestamp recorded in `merged_at`
4. ALL records preserved in database

**Query active records**:
```sql
SELECT * FROM v_sign_in_logs_active;  -- Excludes merged records
```

**Recovery**:
```python
from claude.tools.m365_ir.duplicate_handler import unmerge_group
unmerge_group(db_path, primary_id=18982)  # Restore all records in group
```

---

## 4. Risk Level Backfill

### When to Use

If older sign-in records have `risk_level = NULL` or `risk_level = 'unknown'`, run backfill to extract risk data from raw JSON.

### Command Usage

```bash
python3 m365_ir_cli.py backfill-risk-levels PIR-SGS-4241809
```

### What It Does

1. Finds records with `risk_level IS NULL OR risk_level = 'unknown'`
2. Decompresses `raw_record` BLOB
3. Parses JSON for `RiskLevelDuringSignIn` field
4. Updates `risk_level` column (case-insensitive, lowercase)
5. Idempotent (safe to re-run)

---

## 5. Migrating Existing Cases

### Migration Steps

For any case database created before Phase 261:

```bash
cd ~/work_projects/ir_cases/<CASE_ID>

# Step 1: Backup (recommended)
cp <CASE_ID>_logs.db <CASE_ID>_logs_backup.db

# Step 2: Apply Phase 261.1 - Update auth determination view
python3 ~/maia/claude/tools/m365_ir/migrations/migrate_phase_261.py <CASE_ID>_logs.db

# Step 3: Apply Phase 261.2 - Backfill risk levels (if needed)
PYTHONPATH=~/maia python3 ~/maia/claude/tools/m365_ir/migrations/backfill_risk_levels.py <CASE_ID>_logs.db

# Step 4: Apply Phase 261.4 - Add merge columns and active view
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/naythandawe/maia')
from claude.tools.m365_ir.duplicate_handler import add_merge_columns, create_active_view

db_path = '<CASE_ID>_logs.db'
add_merge_columns(db_path)
create_active_view(db_path)
EOF
```

**Or use CLI commands**:
```bash
# After migration, use CLI for backfill and duplicate handling
python3 ~/maia/claude/tools/m365_ir/m365_ir_cli.py backfill-risk-levels <CASE_ID>
python3 ~/maia/claude/tools/m365_ir/m365_ir_cli.py identify-duplicates <CASE_ID>
```

### Verify Migration

```sql
-- Check view exists
SELECT name FROM sqlite_master WHERE name = 'v_sign_in_auth_status';

-- Check for LIKELY_SUCCESS_RISKY classifications
SELECT COUNT(*)
FROM v_sign_in_auth_status
WHERE auth_determination = 'LIKELY_SUCCESS_RISKY';

-- Check merge columns exist
PRAGMA table_info(sign_in_logs);
-- Should see: merged_into, merge_status, merged_at

-- Check active view exists
SELECT name FROM sqlite_master WHERE name = 'v_sign_in_logs_active';
```

---

## 6. Updated Classification Logic

### All Auth Determinations

| Classification | Criteria | Confidence | Priority |
|----------------|----------|------------|----------|
| **CONFIRMED_SUCCESS** | CA status = "success", error_code = 0 | 100% | P4_NORMAL |
| **LIKELY_SUCCESS_RISKY** | HIGH/MEDIUM risk + notApplied + error_code ≤ 1 | 70% | **P1_IMMEDIATE** |
| **AUTH_INTERRUPTED** | error_code = 50058, 50074 | 50% | P4_NORMAL |
| **CA_BLOCKED** | CA status = "failure" | 100% | P4_NORMAL |
| **AUTH_FAILED** | error_code = 50126, 50053, etc. | 90% | P4_NORMAL |
| **LIKELY_BLOCKED** | CA status = "notApplied" + error_code > 1 | 80% | P4_NORMAL |
| **INDETERMINATE** | Unclear status | 30% | P3_REVIEW |

### Key Changes from Phase 258

**OLD** (Phase 258):
```
HIGH risk + notApplied = AUTH_FAILED (90%)
```

**NEW** (Phase 261):
```
HIGH risk + notApplied = LIKELY_SUCCESS_RISKY (70%, P1_IMMEDIATE)
```

---

## 7. Example Investigation Workflow

### Scenario: Suspicious Turkey Login

```sql
-- 1. Find high-risk foreign logins
SELECT
    timestamp,
    user_principal_name,
    location_country,
    ip_address,
    risk_level,
    auth_determination,
    investigation_priority
FROM v_sign_in_auth_status
WHERE location_country NOT IN ('AU', 'US')
  AND risk_level IN ('high', 'medium')
ORDER BY timestamp DESC
LIMIT 20;
```

**Result**: edelaney@goodsams.org.au from Turkey (TR) with LIKELY_SUCCESS_RISKY

```bash
# 2. Run post-compromise validation
python3 m365_ir_cli.py validate-compromise PIR-SGS-4241809 \
    --user edelaney@goodsams.org.au \
    --timestamp "2025-11-25T04:55:50" \
    --ip 46.252.102.34
```

**Result**: LIKELY_COMPROMISE (1 indicator: follow-on signins)

```sql
-- 3. Check follow-on activity details
SELECT
    timestamp,
    ip_address,
    location_country,
    location_city,
    client_app,
    auth_determination
FROM v_sign_in_auth_status
WHERE user_principal_name = 'edelaney@goodsams.org.au'
  AND timestamp >= '2025-11-25T04:55:50'
  AND timestamp <= '2025-11-28T04:55:50'  -- 72 hour window
ORDER BY timestamp;
```

```sql
-- 4. Check UAL activity
SELECT
    timestamp,
    operation,
    workload,
    client_ip,
    object_id
FROM unified_audit_log
WHERE user_id = 'edelaney@goodsams.org.au'
  AND timestamp >= '2025-11-25T04:55:50'
  AND timestamp <= '2025-11-28T04:55:50'
ORDER BY timestamp;
```

### Decision Tree

```
LIKELY_SUCCESS_RISKY detected
    │
    ├─→ Run post-compromise validation
    │   │
    │   ├─→ NO_COMPROMISE (0-1 indicators)
    │   │   └─→ Monitor user for 7 days
    │   │
    │   ├─→ LIKELY_COMPROMISE (2-3 indicators)
    │   │   └─→ Manual review + containment decision
    │   │
    │   └─→ CONFIRMED_COMPROMISE (4+ indicators)
    │       └─→ Immediate containment (disable account, reset password, revoke sessions)
```

---

## 8. Common Pitfalls

### ❌ WRONG: Trusting risk_level alone

```sql
-- This MISSES compromises where risk level is not set
SELECT * FROM sign_in_logs WHERE risk_level = 'high';
```

### ✅ CORRECT: Use auth_determination view

```sql
-- This captures all risky classifications
SELECT * FROM v_sign_in_auth_status
WHERE auth_determination = 'LIKELY_SUCCESS_RISKY';
```

---

### ❌ WRONG: Assuming no CA block = success

```
if conditional_access_status == 'notApplied':
    verdict = 'AUTH_FAILED'  # WRONG!
```

### ✅ CORRECT: Check error code and risk level

```
if risk_level in ['high', 'medium'] and ca_status == 'notApplied' and error_code <= 1:
    verdict = 'LIKELY_SUCCESS_RISKY'  # Requires investigation
```

---

### ❌ WRONG: 100% confidence in NO_COMPROMISE

```
if no indicators detected:
    confidence = 1.0  # WRONG - absence of evidence ≠ evidence of absence
```

### ✅ CORRECT: Cap NO_COMPROMISE at 80%

```
if no indicators detected:
    confidence = 0.80  # Attacker may have acted outside log retention
```

---

### ❌ WRONG: Partial UPN matching

```sql
WHERE user_principal_name LIKE '%edelaney%'  -- Matches bedelaney, edelaney.smith
```

### ✅ CORRECT: Exact UPN matching

```sql
WHERE user_principal_name = 'edelaney@goodsams.org.au'
```

---

### ❌ WRONG: DELETE duplicates

```sql
DELETE FROM sign_in_logs WHERE id IN (secondary_ids);  -- Data loss!
```

### ✅ CORRECT: MERGE duplicates

```sql
UPDATE sign_in_logs
SET merge_status = 'merged', merged_into = primary_id
WHERE id IN (secondary_ids);  -- Preserves data
```

---

## 9. Phase 261 Corrections (Swarm Review)

The following corrections were made based on comprehensive 4-agent review:

1. **HIGH risk ≠ blocked** - Risk level is assessment, not action
2. **Use existing risk_level column** - Don't add new columns
3. **Exact UPN matching** - Prevent false matches
4. **MERGE not DELETE** - Data preservation with audit trail
5. **72-hour window** - Capture delayed attacker activity
6. **Cap NO_COMPROMISE at 80%** - Acknowledge detection limitations

---

## 10. References

### Files Modified

- `claude/tools/m365_ir/log_database.py` - Updated `v_sign_in_auth_status` view
- `claude/tools/m365_ir/m365_ir_cli.py` - Added 4 new CLI commands

### Files Created

- `claude/tools/m365_ir/compromise_validator.py` - 11-indicator post-compromise validation
- `claude/tools/m365_ir/duplicate_handler.py` - MERGE-based duplicate handling
- `claude/tools/m365_ir/migrations/migrate_phase_261.py` - View migration script
- `claude/tools/m365_ir/migrations/backfill_risk_levels.py` - Risk level extraction

### Tests

- `tests/m365_ir/test_phase_261_auth_determination.py` (21 tests)
- `tests/m365_ir/test_phase_261_backfill_risk_levels.py` (9 tests)
- `tests/m365_ir/test_phase_261_compromise_validator.py` (21 tests)
- `tests/m365_ir/test_phase_261_duplicate_handler.py` (17 tests)

**Total**: 68 tests passing

### Documentation

- PHASE_261_REQUIREMENTS_v2.md - Full requirements (after Swarm review)
- /tmp/CHECKPOINT_PHASE_261.md - Implementation checkpoint

---

## Support

For questions or issues with Phase 261 features:
1. Check test cases for expected behavior
2. Review `/tmp/CHECKPOINT_PHASE_261.md` for implementation details
3. Consult PHASE_261_REQUIREMENTS_v2.md for requirements rationale

---

*End of Phase 261 Usage Guide*
