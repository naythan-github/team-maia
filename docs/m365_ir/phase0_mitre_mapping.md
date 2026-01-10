# M365 IR Phase 0 Auto-Checks - MITRE ATT&CK Mapping

## Coverage Overview

Phase 0 Auto-Checks provide detection coverage for **1 MITRE ATT&CK technique** with indirect indicators for several additional techniques.

### Direct Coverage

| Technique | Name | Detection Function | Sprint |
|-----------|------|-------------------|--------|
| T1562.008 | Impair Defenses: Disable Cloud Logs | `detect_logging_tampering()` | Sprint 3 (C1) |

### Indirect Indicators

| Technique | Name | Indicator Function | Sprint |
|-----------|------|-------------------|--------|
| T1078.004 | Valid Accounts: Cloud Accounts | `analyze_password_hygiene_with_context()` | Sprint 2 (B1) |
| T1110 | Brute Force | `detect_impossible_travel()` | Sprint 3 (C2) |
| T1556.006 | Modify Authentication Process: Multi-Factor Authentication | `detect_mfa_bypass()` | Sprint 3 (C3) |
| T1136.003 | Create Account: Cloud Account | `get_admin_accounts()` | Sprint 2 (B5) |
| T1098 | Account Manipulation | `detect_mfa_bypass()` | Sprint 3 (C3) |

---

## T1562.008 - Impair Defenses: Disable Cloud Logs

**MITRE Description**: Adversaries may disable cloud logging capabilities to thwart detection and evade defenses

### Detection Methodology

**Function**: `detect_logging_tampering(db_path)`

**Data Sources**:
1. **Entra ID Audit Log**:
   - Service principal modifications
   - Directory property changes
   - Policy modifications

2. **Unified Audit Log** (Exchange/M365):
   - `Set-AdminAuditLogConfig` operations
   - `Set-MailboxAuditBypassAssociation` operations

**Detection Logic**:
```python
# Entra ID audit log monitoring
SELECT timestamp, activity, initiated_by
FROM entra_audit_log
WHERE (activity LIKE '%service principal%'
   OR activity LIKE '%directory properties%'
   OR activity LIKE '%policy%')
  AND result = 'success'

# Unified audit log monitoring
SELECT timestamp, user_id, operation
FROM unified_audit_log
WHERE (operation LIKE '%AdminAuditLog%'
   OR operation LIKE '%MailboxAuditBypass%')
  AND result_status = 'Success'
```

**Risk Level**: CRITICAL (any logging change)

**False Positive Rate**: Low (legitimate logging changes are rare)

**Recommended Response**:
1. Investigate user who made changes
2. Review recent activities by that user
3. Check for other indicators of compromise
4. Restore logging configuration
5. Force password reset + MFA for involved accounts

---

## T1078.004 - Valid Accounts: Cloud Accounts (Indirect)

**MITRE Description**: Adversaries may obtain and abuse credentials of existing cloud accounts

### Detection Indicators

**Function**: `analyze_password_hygiene_with_context(db_path)`

**Indicators**:
- Weak password hygiene (70%+ passwords >1 year old)
- Low MFA enforcement (<50%)
- Context classification: PRIMARY_VULNERABILITY

**Rationale**: Weak passwords + low MFA = easy targets for credential compromise

**Risk Assessment**:
- PRIMARY_VULNERABILITY (MFA <50%): HIGH risk of T1078.004
- SECONDARY_VULNERABILITY (MFA ≥90%): LOW risk (MFA provides defense-in-depth)

**Recommended Response**:
1. Force password reset for old passwords
2. Enforce MFA tenant-wide
3. Implement Conditional Access policies
4. Monitor for anomalous sign-ins

---

## T1110 - Brute Force (Indirect)

**MITRE Description**: Adversaries may use brute force techniques to gain access to accounts

### Detection Indicators

**Function**: `detect_impossible_travel(db_path)`

**Indicators**:
- Geographically impossible travel patterns
- Multiple sign-ins from disparate locations in short timeframes
- Speed > 500 mph between consecutive logins

**Rationale**: Successful brute force often results in attacker sign-ins from different geographic locations (VPN, proxies) than legitimate user

**Detection Logic**:
```python
# Calculate travel speed
distance_km = haversine(lat1, lon1, lat2, lon2)
time_hours = (timestamp2 - timestamp1) / 3600
speed_mph = (distance_km * 0.621371) / time_hours

# Flag if impossible
if speed_mph > 500:  # Commercial flight speed threshold
    return 'CRITICAL'
```

**Risk Level**: CRITICAL (high confidence indicator of compromise)

**Recommended Response**:
1. Disable affected account immediately
2. Force sign-out all sessions
3. Reset password + enforce MFA
4. Review audit logs for unauthorized actions
5. Check for persistence mechanisms (app registrations, service principals)

---

## T1556.006 - Modify Authentication Process: MFA (Indirect)

**MITRE Description**: Adversaries may disable or modify MFA to maintain persistent access

### Detection Indicators

**Function**: `detect_mfa_bypass(db_path)`

**Indicators**:
- MFA enabled then disabled within 24 hours
- CRITICAL risk if <1 hour delta
- HIGH risk if 1-24 hour delta

**Rationale**: Legitimate MFA changes are infrequent; rapid enable→disable suggests attacker testing/bypassing controls

**Detection Logic**:
```python
# Track MFA state transitions per user
for user in users:
    if user.mfa_enabled_timestamp and user.mfa_disabled_timestamp:
        time_delta = disabled_timestamp - enabled_timestamp
        if time_delta <= threshold_hours:
            flag_as_bypass_attempt()
```

**Risk Level**:
- CRITICAL (<1 hour): Active attack likely
- HIGH (1-24 hours): Suspicious behavior

**Recommended Response**:
1. Investigate user account for compromise
2. Review recent activity by this account
3. Re-enable MFA and enforce policy
4. Check for other modified security controls
5. Alert security team for deeper investigation

---

## T1136.003 - Create Account: Cloud Account (Indirect)

**MITRE Description**: Adversaries may create cloud accounts to maintain access to environments

### Detection Indicators

**Function**: `get_admin_accounts(db_path)`

**Indicators**:
- Admin accounts detected by role assignment (not naming convention)
- Cross-reference with dormant account checks
- New admin accounts without corresponding IT change tickets

**Rationale**: Attackers often create rogue admin accounts for persistence; role-based detection is more reliable than naming conventions

**Detection Logic**:
```python
# Query role assignments from audit log
SELECT DISTINCT target_user
FROM entra_audit_log
WHERE activity LIKE '%role%'
  AND activity LIKE '%add%'
  AND result = 'success'
```

**Risk Assessment**: Medium (requires correlation with other indicators)

**Recommended Response**:
1. Verify all admin accounts against authorized list
2. Investigate unknown admin accounts
3. Review when account was created and by whom
4. Check recent activities by suspicious admin accounts
5. Remove unauthorized admin accounts

---

## T1098 - Account Manipulation (Indirect)

**MITRE Description**: Adversaries may manipulate accounts to maintain access

### Detection Indicators

**Functions**:
- `detect_mfa_bypass(db_path)` - MFA manipulation
- `get_admin_accounts(db_path)` - Privilege escalation

**Indicators**:
- MFA disabled on high-value accounts
- Unexpected role assignments
- Service principal modifications

**Rationale**: Account manipulation includes MFA changes, role modifications, and authentication method changes

**Risk Level**: HIGH (especially if targeting admin accounts)

**Recommended Response**:
1. Investigate all account modifications
2. Verify with account owners
3. Review audit trail for unauthorized changes
4. Restore original account configuration
5. Force password reset + MFA for manipulated accounts

---

## Detection Coverage Matrix

| MITRE Tactic | Techniques Covered | Detection Capability |
|--------------|-------------------|---------------------|
| Defense Evasion | T1562.008 (Direct) | HIGH |
| Persistence | T1136.003, T1098 (Indirect) | MEDIUM |
| Credential Access | T1078.004, T1110 (Indirect) | MEDIUM |

**Overall Coverage**: 6 techniques (1 direct, 5 indirect)

---

## Limitations & Gaps

### What Phase 0 Does NOT Detect

1. **T1566 - Phishing**: No email analysis capability
2. **T1059 - Command and Scripting Interpreter**: No PowerShell/CLI log analysis
3. **T1114 - Email Collection**: No mailbox access analysis
4. **T1003 - OS Credential Dumping**: Cloud-focused, no endpoint coverage
5. **T1071 - Application Layer Protocol**: No C2 communication detection

### Recommended Complementary Tools

- **Endpoint Detection**: Microsoft Defender for Endpoint
- **Email Security**: Microsoft Defender for Office 365
- **Network Analysis**: Azure Network Watcher, NSG Flow Logs
- **Behavioral Analytics**: Microsoft Sentinel (UEBA)
- **Threat Intelligence**: Azure Sentinel Threat Intelligence connectors

---

## Integration with SIEM/SOAR

### Tagging for ATT&CK Navigator

```json
{
  "name": "M365 IR Phase 0 Auto-Checks",
  "versions": {
    "attack": "14",
    "navigator": "4.9.4",
    "layer": "4.5"
  },
  "domain": "enterprise-attack",
  "techniques": [
    {
      "techniqueID": "T1562.008",
      "tactic": "defense-evasion",
      "color": "#ff0000",
      "comment": "Direct detection via detect_logging_tampering()",
      "enabled": true,
      "metadata": [
        {
          "name": "detection_function",
          "value": "detect_logging_tampering()"
        }
      ],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1078.004",
      "tactic": "persistence",
      "color": "#ffaa00",
      "comment": "Indirect indicator via password hygiene + MFA context",
      "enabled": true,
      "metadata": [
        {
          "name": "detection_function",
          "value": "analyze_password_hygiene_with_context()"
        }
      ],
      "showSubtechniques": false
    }
  ]
}
```

---

## Future Enhancements

### Planned Coverage Expansions

1. **T1071 - Application Layer Protocol**:
   - Detect C2 communication via anomalous OAuth app activity
   - Estimated: Sprint 5-6

2. **T1059 - PowerShell/CLI Usage**:
   - Analyze Azure Activity Log for suspicious automation
   - Estimated: Sprint 5-6

3. **T1114 - Email Collection**:
   - Detect mailbox export operations
   - Estimated: Sprint 6-7

---

**Version**: 1.0.0 (Sprint 4)
**Last Updated**: 2026-01-10
**MITRE ATT&CK Version**: 14.1
