# M365 IR Phase 261 Protocol

**Version**: 1.0
**Date**: 2026-01-09
**Purpose**: Agent guidance for Phase 261 enhanced M365 IR capabilities

---

## Overview

Phase 261 introduces critical enhancements to M365 Incident Response tooling, specifically addressing false positive classifications where high-risk sign-ins were incorrectly dismissed as blocked.

**Key Principle**: `RiskLevelDuringSignIn = "high"` is an ASSESSMENT by Identity Protection, NOT a BLOCK. These require investigation, not dismissal.

---

## When to Use Phase 261 Tools

### 1. Investigating Suspicious Sign-Ins

**Use**: `validate-compromise` CLI command

**Trigger conditions**:
- Sign-in classified as `LIKELY_SUCCESS_RISKY` in database
- High/medium risk + CA status "notApplied"
- Foreign country access with suspicious patterns
- User requests post-compromise analysis

**Example**:
```bash
python3 m365_ir_cli.py validate-compromise PIR-CUSTOMER-TICKET \
    --user victim@company.com \
    --timestamp "2025-11-25T04:55:50" \
    --ip 46.252.102.34
```

**Output interpretation**:
- `NO_COMPROMISE` (≤80%): Monitor for 7 days, low priority
- `LIKELY_COMPROMISE` (70-90%): Manual review required
- `CONFIRMED_COMPROMISE` (≥95%): Immediate containment

### 2. Database Cleanup

**Use**: `identify-duplicates` and `merge-duplicates`

**Trigger conditions**:
- Multiple exports imported from different sources
- Database queries showing duplicate sign-in events
- Before generating PIR reports (cleaner data)

**Workflow**:
```bash
# 1. Identify duplicates
python3 m365_ir_cli.py identify-duplicates PIR-CUSTOMER-TICKET

# 2. Review results, then merge
python3 m365_ir_cli.py merge-duplicates PIR-CUSTOMER-TICKET --auto-apply
```

**Safety**: MERGE approach preserves all data with audit trail

### 3. Risk Data Extraction

**Use**: `backfill-risk-levels`

**Trigger conditions**:
- Database imported before Phase 261
- `risk_level` column shows NULL or 'unknown' values
- Need complete risk assessment data

**Command**:
```bash
python3 m365_ir_cli.py backfill-risk-levels PIR-CUSTOMER-TICKET
```

---

## Classification Logic Changes

### OLD (Pre-Phase 261)
```
HIGH risk + notApplied → AUTH_FAILED (90% confidence)
Analyst action: Dismiss as blocked ❌
```

### NEW (Phase 261)
```
HIGH risk + notApplied → LIKELY_SUCCESS_RISKY (70%, P1_IMMEDIATE)
Analyst action: Investigate immediately ✅
```

**Why this matters**: Prevents false negatives where actual compromises were missed because they were incorrectly classified as blocked.

---

## Database Queries

### Find LIKELY_SUCCESS_RISKY Sign-Ins
```sql
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
  AND location_country NOT IN ('AU', 'US')
ORDER BY timestamp DESC;
```

### Check Duplicate Status
```sql
-- Active records only (excludes merged)
SELECT COUNT(*) FROM v_sign_in_logs_active;

-- All records including merged
SELECT COUNT(*) FROM sign_in_logs;

-- Merge statistics
SELECT
    merge_status,
    COUNT(*) as count
FROM sign_in_logs
GROUP BY merge_status;
```

---

## Agent Handoff Scenarios

### To Security Specialist
**When**: CONFIRMED_COMPROMISE verdict from validation
**Context to provide**:
- User principal name
- Compromise timestamp
- IP address
- Indicators detected (e.g., inbox rules, password changes)
- Verdict and confidence level

**Example handoff**:
```
HANDOFF DECLARATION:
To: security_specialist
Reason: Confirmed compromise requires containment
Context: User edelaney@goodsams.org.au compromised 2025-11-25T04:55:50 from Turkey
Key data: {
    "verdict": "CONFIRMED_COMPROMISE",
    "confidence": 95,
    "indicators": ["inbox_rules_created", "follow_on_signins", "mfa_modifications"],
    "user": "edelaney@goodsams.org.au",
    "ip": "46.252.102.34"
}
```

### To SRE Principal Engineer
**When**: Migration needed for existing cases
**Context to provide**:
- Case ID
- Database path
- Migration type needed (view update, backfill, duplicate handling)

---

## Migration Protocol

For any case database created before Phase 261:

```bash
cd ~/work_projects/ir_cases/<CASE_ID>

# Backup first (recommended)
cp <CASE_ID>_logs.db <CASE_ID>_logs_backup.db

# Apply Phase 261.1 - View update
python3 ~/maia/claude/tools/m365_ir/migrations/migrate_phase_261.py <CASE_ID>_logs.db

# Apply Phase 261.2 - Risk backfill (if needed)
python3 ~/maia/claude/tools/m365_ir/m365_ir_cli.py backfill-risk-levels <CASE_ID>

# Apply Phase 261.4 - Duplicate handling
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/naythandawe/maia')
from claude.tools.m365_ir.duplicate_handler import add_merge_columns, create_active_view

add_merge_columns('<CASE_ID>_logs.db')
create_active_view('<CASE_ID>_logs.db')
EOF
```

---

## Common Pitfalls

### ❌ WRONG: Trusting risk_level alone
```sql
SELECT * FROM sign_in_logs WHERE risk_level = 'high';
```
**Why wrong**: Misses compromises with NULL/unknown risk levels

### ✅ CORRECT: Use auth_determination view
```sql
SELECT * FROM v_sign_in_auth_status
WHERE auth_determination = 'LIKELY_SUCCESS_RISKY';
```

---

### ❌ WRONG: Partial UPN matching
```sql
WHERE user_principal_name LIKE '%username%'
```
**Why wrong**: Matches wrong users (e.g., 'edelaney' matches 'bedelaney')

### ✅ CORRECT: Exact UPN matching
```sql
WHERE user_principal_name = 'user@domain.com'
```

---

### ❌ WRONG: DELETE duplicates
```sql
DELETE FROM sign_in_logs WHERE id IN (duplicate_ids);
```
**Why wrong**: Data loss, no audit trail, no recovery

### ✅ CORRECT: MERGE duplicates
```bash
python3 m365_ir_cli.py merge-duplicates <CASE_ID> --auto-apply
```
**Why right**: Preserves data, full audit trail, reversible

---

## Documentation References

- **Full usage guide**: `claude/docs/m365_ir_phase_261_usage_guide.md`
- **SYSTEM_STATE entry**: Search for "Phase 261" in SYSTEM_STATE.md
- **Requirements**: PIR-SGS-4241809 reports directory
- **Code**: `claude/tools/m365_ir/` (compromise_validator.py, duplicate_handler.py)

---

## Quick Reference Card

| Task | Command | Output |
|------|---------|--------|
| Validate compromise | `m365_ir_cli.py validate-compromise` | Verdict + indicators |
| Find duplicates | `m365_ir_cli.py identify-duplicates` | Group count + IDs |
| Merge duplicates | `m365_ir_cli.py merge-duplicates --auto-apply` | Merge statistics |
| Extract risk data | `m365_ir_cli.py backfill-risk-levels` | Records updated |
| Query risky logins | `SELECT * FROM v_sign_in_auth_status WHERE auth_determination = 'LIKELY_SUCCESS_RISKY'` | Sign-in records |
| Active records only | `SELECT * FROM v_sign_in_logs_active` | Excludes merged |

---

## Success Criteria

When using Phase 261 tools, verify:
- ✅ LIKELY_SUCCESS_RISKY events are investigated (not dismissed)
- ✅ Post-compromise validation completes in <30 seconds
- ✅ Duplicate merges preserve all data (check merge_status column)
- ✅ Risk levels populated from raw_record where possible
- ✅ No false negatives (real compromises not missed)

---

*End of Phase 261 Protocol*
