# M365 Incident Response Playbook

## Overview

This playbook captures cumulative learnings from M365 incident response investigations. It serves as a reference for forensic analysis, PIR writing, and avoiding past mistakes.

**Last Updated**: 2026-01-07 (PIR-OCULUS-2025-12-19 - Added Section 0.5 Pre-Classification Checklist)

---

## 0. CRITICAL: Forensic Analysis Verification Protocol

### ⚠️ MANDATORY CHECKS Before Making Authentication Claims

**NEVER assume field names = success. ALWAYS verify with status codes.**

#### Step 1: Verify Success vs Failure
```sql
-- Check status field distribution
SELECT status, COUNT(*) as events,
       CASE
           WHEN status = '0' OR status = 'Success' THEN 'SUCCESS'
           ELSE 'FAILED'
       END as interpretation
FROM legacy_auth_logs  -- or sign_in_logs, unified_audit_log
GROUP BY status;
```

**Red Flags:**
- ❌ Field name "Authenticated SMTP" does NOT mean authentication succeeded
- ❌ Presence in `legacy_auth_logs` does NOT mean successful authentication
- ✅ ONLY `status` field determines success vs failure

**M365 Status Codes:**
| Code | Meaning | Interpretation |
|------|---------|----------------|
| 0 | Success | Authentication succeeded |
| 50126 | Invalid credentials | **FAILED** - Wrong password or account disabled |
| 50053 | Malicious IP / Account locked | **FAILED** - Blocked by security |
| 50055 | Expired password | **FAILED** |
| 50057 | Account disabled | **FAILED** |

#### Step 2: Baseline Queries (Run EVERY Time)
```sql
-- 1. Total events vs successful events
SELECT
    COUNT(*) as total_events,
    COUNT(CASE WHEN status = '0' THEN 1 END) as successful,
    COUNT(CASE WHEN status != '0' THEN 1 END) as failed,
    ROUND(100.0 * COUNT(CASE WHEN status = '0' THEN 1 END) / COUNT(*), 2) as success_rate_pct
FROM legacy_auth_logs;

-- 2. Success rate by account
SELECT
    user_principal_name,
    COUNT(*) as attempts,
    COUNT(CASE WHEN status = '0' THEN 1 END) as successes,
    COUNT(CASE WHEN status != '0' THEN 1 END) as failures
FROM legacy_auth_logs
GROUP BY user_principal_name
HAVING COUNT(*) > 0
ORDER BY successes DESC;

-- 3. Timeline analysis (pre vs post remediation)
SELECT
    DATE(timestamp) as date,
    COUNT(*) as attempts,
    COUNT(CASE WHEN status = '0' THEN 1 END) as successes
FROM legacy_auth_logs
WHERE user_principal_name = '[target_account]'
GROUP BY DATE(timestamp)
ORDER BY date;
```

#### Step 3: Check Schema First
```bash
# ALWAYS check available fields before querying
sqlite3 [database] "PRAGMA table_info(legacy_auth_logs)"

# Look for these fields:
# - status, result_status, error_code (indicates success/failure)
# - failure_reason, error_message (explains why it failed)
# - is_success, succeeded (boolean indicators)
```

#### Step 4: Challenge Your Interpretation
Before claiming "Account disable was bypassed":

**Ask:**
- Did I check the status field? (success vs failure)
- What is the success rate? (100% should be suspicious)
- Are there failure_reason fields explaining errors?
- Does timeline correlation support my theory?

**Verify:**
```sql
-- Check if account disable actually blocked authentication
SELECT
    timestamp,
    status,
    failure_reason,
    CASE
        WHEN status = '0' THEN '✅ SUCCESS'
        WHEN status = '50126' THEN '❌ FAILED (invalid creds)'
        WHEN status = '50053' THEN '❌ BLOCKED (security)'
        ELSE '❌ FAILED (other)'
    END as result
FROM legacy_auth_logs
WHERE user_principal_name = '[account]'
AND timestamp >= '[account_disable_time]'
ORDER BY timestamp;
```

### Case Study: PIR-OCULUS-2025-12-19 Error

**What Was Claimed:**
> "ben@oculus.info had 37 SMTP authentication events while disabled, proving legacy SMTP bypasses account disable status"

**What Was Actually True:**
- 37 SMTP authentication **ATTEMPTS** (not successes)
- ALL 37 had status code 50126 (authentication **FAILED**)
- Account disable **DID work** - 100% rejection rate post-disable
- Field name "Authenticated SMTP" meant "SMTP auth was attempted", not "succeeded"

**Root Cause of Error:**
1. Assumed "Authenticated SMTP" = successful authentication
2. Never checked the `status` field to verify success vs failure
3. Built narrative ("legacy auth bypasses disable") before verifying data
4. Confirmation bias - looked for evidence supporting theory instead of testing it

**Impact:**
- Incorrect PIR report delivered to customer
- False claim of M365 security control failure
- Recommended unnecessary remediation actions

**Lesson:**
> **PRIMARY EVIDENCE (status codes) > FIELD NAMES > DOCUMENTATION > ASSUMPTIONS**

### Automated Verification (Phase 241)

**RECOMMENDED**: Use automated tooling to prevent forensic errors.

#### Auto-Verification During Import

When importing logs, verification runs automatically:

```bash
python3 m365_ir_cli.py import /path/to/exports.zip --case-id PIR-ACME-2025-001
```

**Automatic Output:**
```
Imported 354 records from legacy_auth.csv

✅ Auto-verification completed:
   Total: 354 events
   Successful: 0 (0.0%)
   Failed: 354 (100.0%)
   ✅ 0% success rate - all authentication attempts FAILED (attack was blocked)
```

#### Manual Verification Command

Verify authentication status codes at any time:

```bash
# Verify all log types
python3 m365_ir_cli.py verify-status PIR-ACME-2025-001

# Verify specific log type
python3 m365_ir_cli.py verify-status PIR-ACME-2025-001 --log-type legacy_auth

# Show detailed status code breakdown
python3 m365_ir_cli.py verify-status PIR-ACME-2025-001 --verbose
```

**Example Output:**
```
============================================================
Authentication Status Verification
Case: PIR-OCULUS-2025-12-19
============================================================

Legacy Auth Events:
  Total: 354
  Successful: 0 (0.0%)
  Failed: 354 (100.0%)

  Status Code Breakdown:
    50126 (Invalid credentials (FAILED)): 232 events
    50053 (Malicious IP / Account locked (FAILED)): 122 events

  Warnings:
    ✅ 0% success rate - all authentication attempts FAILED (attack was blocked)
```

#### Programmatic Verification

For custom analysis scripts:

```python
from claude.tools.m365_ir.auth_verifier import verify_auth_status
from claude.tools.m365_ir.log_database import IRLogDatabase

db = IRLogDatabase(case_id='PIR-ACME-2025-001')
conn = db.connect()

result = verify_auth_status(conn, log_type='legacy_auth')

print(f"Success rate: {result.success_rate:.1f}%")
if result.success_rate == 0.0:
    print("✅ All authentication attempts failed (attack was blocked)")
elif result.success_rate == 100.0:
    print("⚠️  All authentication attempts succeeded (verify expected)")

conn.close()
```

**Key Benefits:**
- **Prevents PIR-OCULUS-2025-12-19 errors**: Automatic detection of 0% success rate
- **Audit trail**: Verification results stored in database for PIR evidence
- **Warnings**: Alerts for suspicious patterns (100% success, unknown status codes)
- **Fast**: <2 seconds for 10K+ events

---

## 0.5 MANDATORY: Pre-Classification Checklist (PIR-OCULUS Lessons)

**⚠️ COMPLETE ALL ITEMS BEFORE classifying foreign logins as "attacker" or declaring a breach.**

**Added**: 2026-01-07 (PIR-OCULUS-2025-12-19 - False positive prevention)

### Checklist

| # | Check | Query/Action | Why It Matters |
|---|-------|--------------|----------------|
| ☐ | **Customer Context** | Ask: "Do you have employees outside AU?" | 179 "suspicious" US logins were legitimate employees |
| ☐ | **Log Coverage Gap** | Compare incident report date vs earliest log timestamp | Breach may have occurred BEFORE your logs start |
| ☐ | **Ticket History** | Review ticketing system notes | Customer may have already remediated |
| ☐ | **Legacy Auth Separate** | Query `legacy_auth_logs` independently | Not blocked by geo-CA policies |
| ☐ | **Baseline Location** | Run baseline query below | 100% foreign logins = user based there |
| ☐ | **Shared IP Analysis** | Check device fingerprints on shared IPs | Same IP + different devices = office network |

### Required Queries

**1. Log Coverage Check:**
```sql
SELECT
    MIN(timestamp) as earliest_log,
    MAX(timestamp) as latest_log,
    julianday(MAX(timestamp)) - julianday(MIN(timestamp)) as days_coverage
FROM sign_in_logs;
-- Compare earliest_log to incident report date
```

**2. Baseline Location Analysis:**
```sql
SELECT user_principal_name, location_country, COUNT(*) as logins,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY user_principal_name), 1) as pct
FROM sign_in_logs
WHERE conditional_access_status = 'success'
GROUP BY user_principal_name, location_country
HAVING pct > 80  -- 80%+ from same country = likely home location
ORDER BY user_principal_name, logins DESC;
```

**3. Legacy Auth Status (Separate from CA):**
```sql
SELECT status_error_code, COUNT(*) as attempts,
       CASE WHEN status_error_code = 0 THEN 'SUCCESS' ELSE 'FAILED' END as result
FROM legacy_auth_logs
GROUP BY status_error_code
ORDER BY attempts DESC;
```

**4. Shared IP Device Analysis:**
```sql
SELECT ip_address, COUNT(DISTINCT user_principal_name) as users,
       COUNT(DISTINCT browser || os) as device_fingerprints,
       GROUP_CONCAT(DISTINCT user_principal_name) as accounts
FROM sign_in_logs
WHERE conditional_access_status = 'success'
GROUP BY ip_address
HAVING users > 1
ORDER BY users DESC;
-- Different users + different fingerprints = office network, not attacker
```

### Customer Context Questions (MANDATORY)

Before classifying ANY foreign login as "attacker":

| Question | Why |
|----------|-----|
| Which employees are based outside Australia? | Their "foreign" logins are NORMAL |
| Is IT support/MSP offshore? | Admin logins from PH/IN may be legitimate |
| Any current employee travel? | Short foreign login bursts may be travel |
| Any remote workers or contractors? | Consistent foreign logins may be authorized |

### Evidence Indicators

**Legitimate Foreign Logins:**
- ✅ 100% of user's logins from that country
- ✅ Same IP accessed by multiple employees
- ✅ Consistent device fingerprint over time
- ✅ Customer confirms employee location

**Suspicious Foreign Logins:**
- ⚠️ User has AU baseline, then sudden foreign logins
- ⚠️ Same IP accesses accounts with DIFFERENT home countries
- ⚠️ Device fingerprint changes dramatically
- ⚠️ Impossible travel patterns
- ⚠️ Foreign login immediately followed by malicious actions

### Future Enhancements (Planned)

| Option | Description | Status |
|--------|-------------|--------|
| **B: Tooling Enforcement** | `pre_classification_checks.py` - Auto-runs all queries, blocks classification until complete | Planned |
| **C: Database Workflow** | `ir_workflow_checklist` table tracks step completion, required for PIR generation | Planned |

---

## 1. Attack Signatures

### Session Token Theft Indicators

| Signature | Attack Type | Confidence | Notes |
|-----------|-------------|------------|-------|
| **Safari on Windows** | AitM (Evilginx) | HIGH | Apple discontinued Safari for Windows in 2012. Any Safari on Windows10 UA in 2025 is technically impossible = synthetic toolkit |
| Safari on macOS from Windows IP | AitM | HIGH | UA/IP mismatch indicates proxy |
| Multiple geolocations < 1 hour | Token replay or VPN | MEDIUM | Check if customer uses VPN before concluding |
| Same token, different IPs | Token theft | HIGH | Session tokens bound to single device don't hop IPs |

### AitM-Specific Patterns

```
Attack Flow (confirmed via Fyna investigation):
1. Victim receives phishing email with link to fake Microsoft login
2. Victim clicks link → AitM proxy (looks identical to Microsoft)
3. Victim enters password → Proxy forwards to REAL Microsoft
4. Microsoft prompts for MFA → Victim approves on phone
5. Microsoft issues authenticated session token
6. AitM proxy CAPTURES the valid token ← MFA already satisfied
7. Attacker replays token from foreign IP → Full access granted
```

**Key insight**: MFA doesn't prevent AitM because token theft happens AFTER MFA completion.

### Legitimate vs Malicious Applications

| Application | Likely Legitimate | Likely Malicious |
|-------------|-------------------|------------------|
| Microsoft Office | Yes | - |
| Outlook Web | Depends on context | If from foreign IP with no travel |
| Azure CLI | Admin activity | Unusual for regular users |
| AAD PowerShell | Admin activity | Unusual for regular users |
| Python Requests | Never legitimate for M365 | Always suspicious |
| Custom OAuth apps | Depends | Check consent grants |

---

## 2. Forensic Confidence Levels

### Definitions

| Level | Definition | PIR Wording |
|-------|------------|-------------|
| **CONFIRMED** | Direct log evidence proves the finding | "confirmed", "verified", "evidence shows" |
| **HIGH** | Strong forensic pattern match, no reasonable alternative | "assessed with high confidence", "forensic indicators suggest" |
| **MEDIUM** | Evidence exists but activity details unknown | "access confirmed, activity unknown" |
| **LOW** | Cannot confirm due to log gaps or insufficient evidence | "cannot confirm", "insufficient evidence" |

### Evidence vs Inference

**Always distinguish in PIRs:**

| Type | Example | How to Document |
|------|---------|-----------------|
| **Direct Evidence** | 81 logins from foreign IPs | "Sign-in logs confirm..." |
| **Inference** | Attack method was AitM | "Based on forensic indicators (Safari on Windows), this is assessed with high confidence as..." |

### Forensic Confidence Table Template

```markdown
| Finding | Confidence | Evidence | Inference |
|---------|------------|----------|-----------|
| Account compromised | **CONFIRMED** | [direct evidence] | Direct evidence |
| Attack method | **HIGH** | [forensic pattern] | Inference based on forensic pattern |
| Data accessed | **MEDIUM** | [what we know] | Activity unknown |
| Data exfiltrated | **LOW** | [log gaps] | Cannot confirm |
```

---

## 3. Known Data Quality Issues

### PowerShell Export Bugs

| Field | Issue | Impact | Workaround |
|-------|-------|--------|------------|
| **Status** | Serializes as object type string (e.g., `@{ErrorCode=0}`) | Can't trust status field | Use `is_failure` flag based on pattern matching, treat unknown as failure |
| **DeviceDetail** | Nested JSON sometimes malformed | Parsing failures | Use try/catch, fallback to raw |

### Log Retention Limits

| Log Type | Default Retention | Impact |
|----------|-------------------|--------|
| Sign-in Logs | 30 days | Usually available for recent incidents |
| UAL (Unified Audit Log) | 90 days | May not cover attack window |
| Mailbox Audit | 90 days | May not cover attack window |
| Entra ID Audit | 30 days | Admin actions may be missing |

**Best Practice**: Always check log availability EARLY in investigation. Document gaps prominently in PIR.

### Import Tool Pitfalls

| Issue | Root Cause | Prevention |
|-------|-----------|------------|
| Manual extraction workflow | Manually unzipped files, created exports/ folder, left zips in Downloads | **CRITICAL**: Use CLI `import` command with zip path. Never manually extract. Breaks audit trail and prevents re-import |
| Missing data from subdirectories | Importer didn't recurse | Fixed in Phase 229 - now uses `rglob('*.csv')` |
| Duplicate records | Multiple imports | UNIQUE constraints handle deduplication |
| Wrong file type detected | Ambiguous filename | Check LOG_FILE_PATTERNS matching |

### Supported Log Types (Phase 238)

All M365 export file types are now fully supported. The importer auto-detects and processes:

| File Pattern | LogType | Database Table | Status |
|--------------|---------|----------------|--------|
| `1_*SignInLogs.csv` | SIGNIN | sign_in_logs | Full support |
| `2_*AuditLogs.csv` | ENTRA_AUDIT | entra_audit_log | Full support |
| `3_*InboxRules.csv` | INBOX_RULES | inbox_rules | Full support |
| `4_*MailboxAudit.csv` | MAILBOX_AUDIT | mailbox_audit_log | Full support |
| `5_*OAuthConsents.csv` | OAUTH_CONSENTS | oauth_consents | Full support |
| `6_*MFAChanges.csv` | MFA_CHANGES | mfa_changes | Added Phase 238 |
| `7_*FullAuditLog.csv` | FULL_AUDIT | unified_audit_log | Full support |
| `8_*RiskyUsers.csv` | RISKY_USERS | risky_users | Added Phase 238 |
| `9_*PasswordLastChanged.csv` | PASSWORD_CHANGED | password_status | Full support |
| `10_*LegacyAuth*.csv` | LEGACY_AUTH | legacy_auth_logs | Full support |

**Warning System**: Files matching patterns without handlers now generate warnings (prevents silent data loss).

**Test Coverage**: `test_all_patterns_have_handlers()` ensures all patterns have import methods (prevents future regressions).

---

## 4. PIR Writing Standards

### Qualifying Claims

**DO:**
- "Session token theft, assessed with high confidence as AitM based on forensic indicators"
- "Safari on Windows user agent indicates AitM toolkit (Evilginx or similar)"
- "Attack method cannot be confirmed without original phishing email"

**DON'T:**
- "The attacker used Evilginx" (unless you have infrastructure evidence)
- "MFA was bypassed" (technically incorrect - MFA completed, token was stolen)
- "All attacks were blocked" (unless you can verify status field)

### Explaining Technical Concepts

**Why MFA didn't prevent the attack** (use this template):
```
Standard MFA (push notifications, OTP codes) protects against password theft
but NOT session token theft. The attacker never needed to bypass MFA - they
let the victim complete MFA, then stole the resulting session token.
```

**Why Safari on Windows is malicious**:
```
Apple discontinued Safari for Windows in 2012. Any "Safari on Windows10"
user agent in 2025 is technically impossible and indicates an AitM attack
toolkit (Evilginx, Modlishka, or similar).
```

### Document Control

Always version PIRs when facts change:
- v1.0: Initial release
- v2.0: Major revision (e.g., "blocked" → "confirmed breach")
- v2.1: Minor revision (e.g., added confidence qualifiers)

---

## 5. Customer Q&A Patterns

### Common Clarifications Needed

| Question | Why It Matters |
|----------|----------------|
| "Does [user] use a VPN?" | Foreign IPs may be legitimate VPN traffic |
| "Does [user] travel internationally?" | Explains foreign login locations |
| "What MFA method is enforced?" | Push/OTP vulnerable to AitM, FIDO2 is not |
| "When were CA policies added?" | Determines if attacks were blocked or successful |
| "Does anyone use [unusual app]?" | Distinguishes legitimate tools from attack tools |

### Red Flags in Customer Responses

| Response | Follow-up |
|----------|-----------|
| "We have MFA so we're secure" | Explain AitM token theft |
| "That user doesn't use Safari" | Good - confirms malicious activity |
| "We added CA policies after the breach" | Attacks before CA were likely successful |
| "I don't know what [app] is" | Likely malicious if unexpected |

---

## 6. MITRE ATT&CK Mappings

### Common M365 Attack Techniques

| Technique | ID | Indicators |
|-----------|-----|------------|
| Phishing: Spearphishing Link | T1566.002 | User clicked AitM phishing link |
| Steal Web Session Cookie | T1539 | Safari on Windows, token replay |
| Valid Accounts: Cloud | T1078.004 | Sustained access over days/weeks |
| Email Collection | T1114.002 | Mailbox access during compromise |
| Account Manipulation | T1098 | Inbox rules, OAuth consents |

---

## 7. Remediation Checklists

### Confirmed Compromise

- [ ] Reset password for compromised account
- [ ] Revoke all active sessions (`Revoke-AzureADUserAllRefreshToken`)
- [ ] Review sent items during compromise window
- [ ] Check for BEC activity (invoices, wire transfers)
- [ ] Review inbox rules for persistence
- [ ] Check OAuth consent grants
- [ ] Enable geofencing CA policy
- [ ] Consider phishing-resistant MFA (FIDO2)

### Suspected Compromise (Unverified)

- [ ] Reset password (precautionary)
- [ ] Review recent sign-in activity
- [ ] Check inbox rules
- [ ] Monitor for suspicious activity

---

## 8. Tool Reference

### PIR Document Generation

```bash
# ALWAYS use this for markdown → docx (not raw pandoc)
python3 claude/tools/document_conversion/convert_md_to_docx.py report.md --output report.docx
```

### Log Import

```bash
# ⭐ RECOMMENDED: Import from zip files (CLI handles case creation + file management)
python3 claude/tools/m365_ir/m365_ir_cli.py import ~/Downloads/Export.zip --customer "Customer Name"
# Automatically: creates case, moves zip to source-files/, imports logs

# Multiple zips for same incident
python3 claude/tools/m365_ir/m365_ir_cli.py import ~/Downloads/Export-1.zip --customer "Customer"
python3 claude/tools/m365_ir/m365_ir_cli.py import ~/Downloads/Export-2.zip --case-id PIR-CUSTOMER-2025-XX-XX
python3 claude/tools/m365_ir/m365_ir_cli.py import ~/Downloads/Export-3.zip --case-id PIR-CUSTOMER-2025-XX-XX

# Legacy: Programmatic import (if you need custom logic)
python3 -c "
from claude.tools.m365_ir.log_database import IRLogDatabase
from claude.tools.m365_ir.log_importer import LogImporter
db = IRLogDatabase(case_id='PIR-XXX-YYYY-MM-DD', base_path='/path/to/case')
db.create()
importer = LogImporter(db)
results = importer.import_all('/path/to/exports')
"
```

**⚠️ CRITICAL**: Never manually extract zips to case folders. Use CLI import - it maintains audit trail and enables re-import.

### IR Knowledge Base Query

```bash
# Check if IP seen in previous investigations
python3 claude/tools/ir/ir_knowledge_query.py ip 93.127.215.4
```

---

## 9. Lessons Learned Log

### 2026-01-05: PIR-FYNA-2025-12-08

**Issue**: Initially assessed "all attacks blocked" but CA was added post-breach
**Root Cause**: Didn't verify CA timeline with customer
**Fix**: Always ask when CA policies were implemented relative to attack window

**Issue**: Missing 9,626 sign-in records from Fyna/ subdirectory
**Root Cause**: Log importer didn't recurse into subdirectories
**Fix**: Changed `iterdir()` to `rglob('*.csv')` in `log_importer.py`

**Issue**: Stated "AitM attack" without confidence qualifier
**Root Cause**: Conflated direct evidence with forensic inference
**Fix**: Always distinguish CONFIRMED (direct evidence) from HIGH (inference)

**Issue**: Forgot to use Orro docx converter
**Root Cause**: Tool not documented in IR agent
**Fix**: Added PIR Document Generation section to `m365_incident_response_agent.md`

---

## 10. References

- [Evilginx Documentation](https://github.com/kgretzky/evilginx2) - AitM toolkit
- [MITRE ATT&CK Cloud Matrix](https://attack.mitre.org/matrices/enterprise/cloud/)
- [Microsoft Sign-in Logs Schema](https://learn.microsoft.com/en-us/azure/active-directory/reports-monitoring/reference-azure-monitor-sign-ins-log-schema)
- [Safari for Windows EOL](https://en.wikipedia.org/wiki/Safari_(web_browser)#Windows) - Discontinued 2012

---

*This playbook is maintained as part of the MAIA M365 IR tooling. Add learnings after each investigation.*
