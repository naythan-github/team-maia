# SGS Legacy Authentication Breach - Incident Response Report

**Client**: Sisters of the Good Samaritan (goodsams.org.au)
**Report Date**: 2025-12-05 (Updated)
**Initial Report**: 2025-12-04
**Status**: 🟡 REMEDIATED (Credentials Reset, Attackers Blocked)
**Confluence**: https://vivoemc.atlassian.net/wiki/spaces/SECADV/pages/3180494849

---

## Executive Summary

A coordinated credential stuffing attack compromised one user account (rbrady@goodsams.org.au) via legacy authentication protocols that bypass MFA. **The initial breach on Nov 13 went undetected for 20 days** until Orro security monitoring identified a second successful login from Saudi Arabia on Dec 3. The compromised credentials were never reset after the initial breach, allowing the attacker (or credential buyer) to regain access.

**Key Findings**:
- **Initial compromise**: Nov 13, 2025 22:15 UTC via ROPC flow from US datacenter
- **Detection gap**: 20 days - password NOT reset between Nov 13 and Dec 3
- **Secondary breach**: Dec 3, 2025 12:20 UTC via legacy auth from Saudi Arabia
- **Detected by**: Orro security monitoring (not customer)
- 8 accounts targeted, 1 confirmed compromised
- No FileMaker or other legitimate legacy auth usage detected
- Safe to block legacy authentication tenant-wide

---

## Attack Timeline

### Phase 1: Credential Testing & Initial Breach (Nov 9-26, 2025)

| Date | Account | IP Location | Result | Notes |
|------|---------|-------------|--------|-------|
| Nov 9-10 | vgriffith | Cheyenne, WY | ❌ FAILED | Credential testing |
| Nov 10-11 | kduckworth | Cheyenne, WY | ❌ FAILED | Credential testing |
| **Nov 13 22:15** | **rbrady** | **Cheyenne, WY** | **✅ SUCCESS (ROPC)** | **INITIAL BREACH - UNDETECTED** |
| Nov 14 | rbrady | Cheyenne, WY | ❌ FAILED | Likely rate limit/lockout |
| Nov 14-16 | tibouri | Cheyenne, WY | ❌ FAILED | Credential testing |
| Nov 15-16 | thegoodoil | Cheyenne, WY | ❌ FAILED + LOCKED | Account lockout |
| Nov 16 | emurray | Cheyenne, WY | ❌ FAILED | Credential testing |
| Nov 16-17 | jfarrell | Cheyenne, WY | ❌ FAILED | Credential testing |
| Nov 22-26 | msmith | Cheyenne, WY | ❌ FAILED | Credential testing |

### Detection Gap: 20 Days (Nov 14 - Dec 2, 2025)

| Finding | Evidence |
|---------|----------|
| Password reset for rbrady | ❌ **NOT PERFORMED** |
| Security alerts triggered | ❌ None |
| Customer awareness | ❌ None |
| Credential status | 🔴 **REMAINED COMPROMISED** |

*Password audit log (AuditLogs_2025-12-05) confirms NO SSPR or admin-initiated password reset for rbrady during this period.*

### Phase 2: Credential Monetization & Detection (Dec 3-4, 2025)

| Time (UTC) | Account | IP Location | Result | Notes |
|------------|---------|-------------|--------|-------|
| **Dec 3 12:20** | **rbrady** | **Ar Riyad, Saudi Arabia** | **✅ SUCCESS** | **DETECTED BY ORRO** |
| Dec 3 ~15:00 | rbrady | - | 🔒 PASSWORD RESET | Remediation by Orro |
| Dec 3 15:29 | rbrady | Itabuna, Brazil | ❌ FAILED | Post-remediation |
| Dec 3 15:53 | mrobinson | Santo Amaro, Brazil | ❌ FAILED | Credential testing |
| Dec 3 17:59 | mrobinson | Buenos Aires, Argentina | ❌ FAILED | Credential testing |
| Dec 4 01:41 - 07:45 | rbrady/mrobinson | Brazil/Argentina/Chile | ❌ ALL FAILED | Post-remediation |

### Breach Duration Summary

| Metric | Value |
|--------|-------|
| Initial breach | Nov 13, 2025 22:15 UTC |
| Detection | Dec 3, 2025 (by Orro) |
| Remediation | Dec 3, 2025 ~15:00 UTC |
| **Total undetected period** | **20 days** |
| Time from detection to remediation | ~3 hours |

---

## Attack Infrastructure

### Phase 1: US Datacenter (Credential Testing)

| Attribute | Value |
|-----------|-------|
| IPv6 Range | 2605:6400:8045::/48 |
| ASN | AS20473 - Vultr Holdings LLC |
| Type | VPS/Cloud Datacenter |
| Location | Cheyenne, Wyoming, USA |
| Tool | Microsoft Azure CLI |
| Auth Method | ROPC (Resource Owner Password Credential) |

### Phase 2: Residential Proxies (Exploitation)

| Country | Sample IPs | Purpose |
|---------|------------|---------|
| Saudi Arabia | 142.154.122.154 | Initial exploitation |
| Brazil | 177.10.74.9, 186.216.6.124, 189.113.193.123 | Continued attempts |
| Argentina | 181.117.72.132, 131.108.80.123 | Continued attempts |
| Chile | 179.60.67.144 | Continued attempts |
| Vietnam | 14.163.238.117 | Continued attempts |

---

## Initial Compromise Event Details

| Field | Value |
|-------|-------|
| Timestamp | 2025-11-13T22:15:17Z |
| User | rbrady@goodsams.org.au |
| IP | 2605:6400:8045:e656:66a5:62fa:4a7f:c313 |
| Location | Cheyenne, Wyoming, US |
| Auth Method | ROPC (Resource Owner Password Credential) |
| Application | Microsoft Azure CLI |
| Resource | Azure Resource Manager |
| MFA | Single-factor (BYPASSED) |
| Auth Detail | Password Hash Sync - Correct password |

---

## MITRE ATT&CK Mapping

| Technique ID | Name | Phase | Evidence |
|--------------|------|-------|----------|
| T1110.001 | Brute Force: Password Guessing | Initial Access | 8 accounts tested from Vultr VPS |
| T1078.004 | Valid Accounts: Cloud Accounts | Initial Access | rbrady credentials compromised |
| T1550.001 | Use Alternate Auth Material | Defense Evasion | ROPC flow bypassed MFA |
| T1114 | Email Collection | Collection | Potential (requires UAL review) |
| T1078 | Valid Accounts | Persistence | Same credentials reused 20 days later |

---

## Detection Gap Analysis

### Why Nov 13 Breach Went Undetected

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| No alerting on ROPC authentication | Initial compromise invisible | Alert on ALL legacy auth successes |
| No alerting on datacenter IP logins | Vultr VPS access not flagged | Alert on cloud provider IP ranges |
| No alerting on non-AU geolocation | US-based attack not flagged | Alert on logins outside AU/expected countries |
| No legacy auth blocking policy | Attack vector remained open | Implement CA policy to block legacy auth |
| No risky sign-in detection | Azure AD Identity Protection not enabled | Enable and configure Identity Protection |

### Detection Capability Gaps

| Capability | Status | Risk |
|------------|--------|------|
| Legacy auth success alerting | ❌ Not configured | HIGH - Attackers bypass MFA undetected |
| Impossible travel detection | ❌ Not configured | MEDIUM - Geographic anomalies missed |
| Datacenter IP detection | ❌ Not configured | HIGH - Automated attacks undetected |
| Failed auth threshold alerts | ⚠️ Partial (lockout only) | MEDIUM - Low-and-slow attacks missed |
| UAL monitoring | ❌ Not configured | HIGH - Post-compromise activity invisible |

### Credential Exposure Timeline

```
Nov 13 22:15 ─────────────────────────────────────────── Dec 3 12:20
     │                                                        │
  BREACH                    20 DAYS EXPOSED                DETECTED
  (ROPC)                   (No password reset)            (by Orro)
     │                                                        │
     └── Password remained valid ────────────────────────────►│
         Attacker retained access capability                  │
         Credentials likely sold/shared                       │
                                                             ▼
                                                    Dec 3 ~15:00
                                                    PASSWORD RESET
```

---

## Legacy Authentication Analysis

### Legitimate Usage Assessment

| Category | Finding |
|----------|---------|
| FileMaker/Claris | ❌ Not detected |
| Printer/Scanner SMTP | ❌ Not detected |
| IMAP/POP3 clients | ❌ Not detected |
| ActiveSync (legacy) | ❌ Not detected |
| Interactive "Other clients" | Only attacker activity |
| Non-Interactive "Other clients" | All modern auth (MS apps with MFA) |

**Verdict**: ✅ **SAFE TO BLOCK** - No legitimate legacy auth usage detected

---

## Remediation Status

### Completed Actions

| Action | Status | Date |
|--------|--------|------|
| Password reset for rbrady | ✅ Complete | Dec 3, 2025 |
| Attacker access blocked | ✅ Complete | Dec 3, 2025 |
| Credential stuffing continues but fails | ✅ Monitored | Ongoing |
| Incident report published to Confluence | ✅ Complete | Dec 5, 2025 |

### Required Actions - Prevention

| Priority | Action | Status |
|----------|--------|--------|
| **CRITICAL** | Block legacy authentication via Conditional Access | ⏳ Pending |
| **CRITICAL** | Block ROPC flow via CA policy | ⏳ Pending |
| **HIGH** | Block Azure CLI for non-admin users | ⏳ Pending |
| **MEDIUM** | Block Vultr IP ranges (2605:6400::/32) | ⏳ Pending |

### Required Actions - Detection (NEW)

| Priority | Action | Status |
|----------|--------|--------|
| **HIGH** | Enable Azure AD Identity Protection | ⏳ Pending |
| **HIGH** | Configure alerts for legacy auth successes | ⏳ Pending |
| **HIGH** | Configure alerts for non-AU logins | ⏳ Pending |
| **MEDIUM** | Configure alerts for datacenter IP logins | ⏳ Pending |
| **MEDIUM** | Enable UAL monitoring for sensitive operations | ⏳ Pending |

### Required Actions - Investigation

| Priority | Action | Status |
|----------|--------|--------|
| **HIGH** | Export UAL for Nov 13-Dec 3 (rbrady) | ⏳ Pending |
| **MEDIUM** | Review all 8 targeted accounts for IOCs | ⏳ Pending |
| **MEDIUM** | Check for inbox rules/forwarding (rbrady) | ⏳ Pending |

---

## Recommended Conditional Access Policies

### Policy 1: Block Legacy Authentication

```
Name: Block Legacy Authentication
State: On
Users: All users
Cloud apps: All cloud apps
Conditions:
  - Client apps: Exchange ActiveSync clients, Other clients
Grant: Block access
```

### Policy 2: Block ROPC Flow

```
Name: Block ROPC Authentication
State: On
Users: All users (exclude break-glass)
Cloud apps: All cloud apps
Conditions:
  - Client apps: Mobile apps and desktop clients
  - Authentication flows: Resource owner password credentials (ROPC)
Grant: Block access
```

---

## IOC Summary

### IP Addresses to Block

**Vultr VPS Range (Credential Testing)**:
- 2605:6400::/32 (IPv6)
- 45.32.0.0/16, 149.28.0.0/16 (IPv4)

**South American Residential Proxies**:
- 177.10.74.9, 186.216.6.124, 189.113.193.123
- 181.117.72.132, 131.108.80.123
- 45.190.135.83, 179.218.17.143

**Other**:
- 142.154.122.154 (Saudi Arabia)
- 14.163.238.117 (Vietnam)

### User Agent (Attack Signature)

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

---

## Log Sources Analyzed

| Export | Period | Contents |
|--------|--------|----------|
| `SGS_2025-11-28_2025-12-05/` | 7 days | InteractiveSignIns, NonInteractiveSignIns, AuditLogs |
| `Sisters_of_the_Good_Samaritan_2025-11-04_2025-12-04_extracted/` | 30 days | InteractiveSignIns, NonInteractiveSignIns, AuditLogs, ApplicationSignIns |
| `Sisters_of_the_Good_Samaritan_AuditLogs_2025-12-05 (Password).csv` | Point-in-time | Password audit events (SSPR, resets) |

### Logs NOT Available (Required for Full Investigation)

| Log Type | Purpose | Status |
|----------|---------|--------|
| **Unified Audit Log (UAL)** | What was accessed during breach | ❌ NOT EXPORTED |
| Mailbox Audit Log | Email access patterns | ❌ NOT EXPORTED |

*UAL export required to determine what data rbrady accessed during the 20-day breach window.*

---

*Report generated by M365 Incident Response Agent (Maia)*
*Last updated: 2025-12-05 (v3 - Detection Gap Analysis)*
