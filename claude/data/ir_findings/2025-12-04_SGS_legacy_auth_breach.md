# SGS Legacy Authentication Breach - Incident Response Report

**Client**: Sisters of the Good Samaritan (goodsams.org.au)
**Report Date**: 2025-12-05 (Updated)
**Initial Report**: 2025-12-04
**Status**: 🟡 REMEDIATED (Credentials Reset, Attackers Blocked)
**Confluence**: https://vivoemc.atlassian.net/wiki/spaces/SECADV/pages/3180494849

---

## Executive Summary

A coordinated credential stuffing attack compromised one user account (rbrady@goodsams.org.au) via legacy authentication protocols that bypass MFA. The breach was active for approximately 3 hours before passwords were reset. Attackers continue to attempt access but all current attempts are blocked.

**Key Findings**:
- Initial compromise: Nov 13, 2025 via ROPC flow from US datacenter
- Secondary breach: Dec 3, 2025 via legacy auth from Saudi Arabia
- 8 accounts targeted, 1 confirmed compromised
- No FileMaker or other legitimate legacy auth usage detected
- Safe to block legacy authentication tenant-wide

---

## Attack Timeline

### Phase 1: Credential Testing (Nov 9-26, 2025)

| Date | Account | IP Location | Result |
|------|---------|-------------|--------|
| Nov 9-10 | vgriffith | Cheyenne, WY | ❌ FAILED |
| Nov 10-11 | kduckworth | Cheyenne, WY | ❌ FAILED |
| **Nov 13 22:15** | **rbrady** | **Cheyenne, WY** | **✅ SUCCESS (ROPC)** |
| Nov 14 | rbrady | Cheyenne, WY | ❌ FAILED (pwd changed) |
| Nov 14-16 | tibouri | Cheyenne, WY | ❌ FAILED |
| Nov 15-16 | thegoodoil | Cheyenne, WY | ❌ FAILED + LOCKED |
| Nov 16 | emurray | Cheyenne, WY | ❌ FAILED |
| Nov 16-17 | jfarrell | Cheyenne, WY | ❌ FAILED |
| Nov 22-26 | msmith | Cheyenne, WY | ❌ FAILED |

### Phase 2: Credential Monetization (Dec 3-4, 2025)

| Time (UTC) | Account | IP Location | Result |
|------------|---------|-------------|--------|
| Dec 3 12:20 | rbrady | Ar Riyad, Saudi Arabia | ✅ SUCCESS |
| Dec 3 15:29 | rbrady | Itabuna, Brazil | ❌ FAILED |
| Dec 3 15:53 | mrobinson | Santo Amaro, Brazil | ❌ FAILED |
| Dec 3 17:59 | mrobinson | Buenos Aires, Argentina | ❌ FAILED |
| Dec 4 01:41 - 07:45 | rbrady/mrobinson | Brazil/Argentina/Chile | ❌ ALL FAILED |

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

### Required Actions

| Priority | Action | Status |
|----------|--------|--------|
| **HIGH** | Block legacy authentication via Conditional Access | ⏳ Pending |
| **HIGH** | Block ROPC flow via CA policy | ⏳ Pending |
| **MEDIUM** | Block Azure CLI for non-admin users | ⏳ Pending |
| **MEDIUM** | Block Vultr IP ranges (2605:6400::/32) | ⏳ Pending |
| **LOW** | Review all 8 targeted accounts for IOCs | ⏳ Pending |

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

- `SGS_2025-11-28_2025-12-05/` (latest export)
- `Sisters_of_the_Good_Samaritan_2025-11-04_2025-12-04_extracted/` (30-day history)
- InteractiveSignIns, NonInteractiveSignIns, AuditLogs

---

*Report generated by M365 Incident Response Agent (Maia)*
*Last updated: 2025-12-05*
