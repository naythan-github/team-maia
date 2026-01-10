# M365 IR Phase 0 Auto-Checks - User Guide

## Overview

Phase 0 Auto-Checks are automated security checks that run immediately after M365 log import to identify critical security issues before detailed analysis begins.

**Purpose**: Rapid triage and prioritization of M365 incidents

**Runtime**: <5 seconds for typical tenants (1000 users)

---

## Quick Start

```bash
# Run Phase 0 checks (summary output)
python3 claude/tools/m365_ir/phase0_cli.py /path/to/investigation.db

# Detailed table output
python3 claude/tools/m365_ir/phase0_cli.py /path/to/investigation.db --format=table

# Machine-readable JSON output
python3 claude/tools/m365_ir/phase0_cli.py /path/to/investigation.db --format=json
```

**Exit Codes**:
- `0`: No critical/high issues
- `1`: High issues found
- `2`: Critical issues found
- `3`: Error during execution

---

## Checks Performed

### Sprint 1: Core Security Checks

#### Password Hygiene
**Detection**: Accounts with passwords older than 1, 2, or 3 years

**Risk Levels**:
- CRITICAL: ≥70% of accounts have passwords >1 year old
- HIGH: ≥50% of accounts
- MEDIUM: ≥30% of accounts
- OK: <30% of accounts

**Recommendation**: Force password reset for affected accounts, enforce regular rotation policy

#### Foreign Baseline
**Detection**: Sign-ins from countries outside the organization's baseline

**Risk Levels**:
- HIGH: Foreign sign-ins detected
- OK: All sign-ins from home country

**Recommendation**: Investigate foreign sign-ins, verify user travel, check for VPN usage

---

### Sprint 2: False Positive Prevention

#### MFA Context Check
**Detection**: Classifies password vulnerabilities based on MFA enforcement

**Context Levels**:
- PRIMARY_VULNERABILITY: <50% MFA enforcement (password is primary security control)
- MODERATE_RISK: 50-89% MFA enforcement
- SECONDARY_VULNERABILITY: ≥90% MFA enforcement (password less critical with strong MFA)

**Recommendation**: If PRIMARY, enforce MFA immediately. If SECONDARY, still rotate passwords but lower urgency.

#### Service Account Detection
**Detection**: Automatically excludes service accounts from dormant account alerts

**Patterns Detected**:
- `svc_*`, `service.*`, `app-*`, `noreply@`, `api.*`

**Recommendation**: Review service accounts separately with app owners

#### Dormant Accounts
**Detection**: Accounts with no sign-in activity in 60 days (configurable)

**Exclusions**:
- Service accounts (automatic)
- Break-glass accounts (whitelist)

**Recommendation**: Disable dormant accounts, review with account owners

#### Break-Glass Whitelist
**Configuration**: `~/.maia/config/breakglass_accounts.json`

```json
{
  "accounts": [
    "breakglass.admin@contoso.com",
    "emergency.admin@contoso.com"
  ]
}
```

**Recommendation**: Whitelist emergency admin accounts that are intentionally dormant

#### FIDO2/Passwordless Detection
**Detection**: Excludes passwordless accounts from password hygiene checks

**Methods Detected**:
- FIDO2
- CertificateBasedAuthentication
- WindowsHello

**Recommendation**: No action needed for passwordless accounts

#### Role-Based Admin Detection
**Detection**: Identifies admin accounts by Entra ID role assignments (not naming conventions)

**Fallback**: If no role data, uses naming patterns (`admin`, `sysadmin`, etc.)

**Recommendation**: Cross-reference with dormant/compromised accounts for priority review

---

### Sprint 3: False Negative Prevention

#### T1562.008: Logging Tampering Detection
**Detection**: Changes to audit logging configuration

**MITRE ATT&CK**: T1562.008 - Impair Defenses: Disable Cloud Logs

**Sources Monitored**:
- Entra ID audit log (service principal, directory properties, policy changes)
- Exchange/M365 unified audit log (audit disable commands)

**Risk Level**: CRITICAL for any logging changes

**Recommendation**: Investigate immediately. Logging changes often indicate attacker presence.

#### Impossible Travel Detection
**Detection**: Sign-ins from geographically impossible locations within short timeframes

**Method**: Haversine formula for distance calculation

**Threshold**: 500 mph (commercial flight speed)

**Example**: NYC → Beijing in 1.5 hours = 4,551 mph (IMPOSSIBLE)

**Risk Level**: CRITICAL for any impossible travel

**Recommendation**: Investigate account compromise, review recent activity, force password reset + MFA

#### MFA Bypass Detection
**Detection**: MFA enabled then disabled within 24 hours (configurable)

**Risk Levels**:
- CRITICAL: MFA disabled <1 hour after enabling
- HIGH: MFA disabled 1-24 hours after enabling

**Recommendation**: Investigate attacker attempting to bypass security controls

---

## Interpreting Results

### Summary Output (Default)

```
M365 IR Phase 0 Auto-Checks - Summary
==================================================

⚠️  CRITICAL: 2 issue(s) require immediate attention
  • Password Hygiene
  • Impossible Travel

⚠️  HIGH: 1 issue(s) need review
  • Mfa Bypass

Total checks run: 7

Run with --format=table for detailed results
```

**Action**: Start with CRITICAL issues, then HIGH, then MEDIUM

### Table Output (Detailed)

Shows full details for each check including:
- Risk levels
- Account counts
- Specific findings
- Recommendations

**Use Case**: Detailed analysis and documentation

### JSON Output (Programmatic)

Machine-readable format for:
- Integration with other tools
- Automated reporting
- Log aggregation systems

**Use Case**: SIEM integration, automated workflows

---

## Common Scenarios

### Scenario 1: Clean Tenant
```
✅ All checks passed - no critical issues detected

Total checks run: 7
```

**Action**: Document baseline, proceed with detailed analysis if incident reported

### Scenario 2: Compromised Account
```
⚠️  CRITICAL: 2 issue(s) require immediate attention
  • Impossible Travel
  • Mfa Bypass
```

**Actions**:
1. Disable compromised account immediately
2. Force sign-out all sessions
3. Reset password + enforce MFA
4. Review audit logs for unauthorized actions
5. Check for persistence mechanisms (app registrations, service principals)

### Scenario 3: Weak Security Posture
```
⚠️  CRITICAL: 1 issue(s) require immediate attention
  • Password Hygiene (80% passwords >1 year, 25% MFA)
```

**Actions**:
1. Enforce MFA tenant-wide
2. Implement password expiration policy
3. Force password reset for accounts >1 year
4. Enable Conditional Access policies

---

## Best Practices

1. **Run Immediately**: Execute Phase 0 checks as soon as logs are imported
2. **Document Baseline**: Run on known-clean tenants to establish baseline metrics
3. **Whitelist Correctly**: Only whitelist genuine break-glass accounts (verify with security team)
4. **Monitor Trends**: Track metrics over time (password age, MFA adoption, dormant accounts)
5. **Automate**: Integrate into incident response playbooks and SOAR platforms

---

## Troubleshooting

### "No data available" errors
**Cause**: Missing tables or empty database

**Fix**: Verify log collection completed successfully, check database schema

### Service accounts flagged as dormant
**Cause**: Service account naming doesn't match patterns

**Fix**: Update `SERVICE_ACCOUNT_PATTERNS` in `phase0_auto_checks.py` or add to break-glass whitelist

### False positive foreign baseline
**Cause**: VPN usage or legitimate travel

**Fix**: Update `override_home_country` parameter if org uses VPN exit nodes

### Passwordless accounts flagged
**Cause**: Auth method not recognized

**Fix**: Update `get_passwordless_accounts()` with additional auth methods

---

## Performance Guidelines

| Tenant Size | Expected Runtime | Memory Usage |
|-------------|------------------|--------------|
| Small (100 users, 30 days) | <1 second | <50 MB |
| Medium (1,000 users, 90 days) | <5 seconds | <200 MB |
| Large (10,000 users, 180 days) | <30 seconds | <1 GB |

**Optimization**: If runtime exceeds guidelines, check for N+1 query patterns or database indexing issues

---

## Security Considerations

1. **Sanitize Output**: Redact UPNs/PII before sharing reports externally
2. **Access Control**: Restrict database access to authorized incident responders
3. **Audit Trail**: Log all Phase 0 check executions
4. **Data Retention**: Follow organization's data retention policy for investigation databases

---

## Support

For issues or questions:
- GitHub: https://github.com/naythan-orro/maia/issues
- Documentation: `/Users/naythandawe/maia/docs/m365_ir/`

---

**Version**: 1.0.0 (Sprint 4)
**Last Updated**: 2026-01-10
