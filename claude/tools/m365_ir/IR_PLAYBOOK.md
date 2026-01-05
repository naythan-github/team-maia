# M365 Incident Response Playbook

## Overview

This playbook captures cumulative learnings from M365 incident response investigations. It serves as a reference for forensic analysis, PIR writing, and avoiding past mistakes.

**Last Updated**: 2026-01-06 (PIR-OCULUS-2025-01 - Phase 230 zip workflow lessons)

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
