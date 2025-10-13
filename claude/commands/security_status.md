# Security Status - Quick Security Check

**Command**: `/security-status`
**Purpose**: Quick security health check without loading full Security Specialist Agent
**Response Time**: <5 seconds
**Output**: Security status summary with actionable insights

---

## Command Behavior

When user types `/security-status`, Maia will:

1. Query security orchestration service database
2. Analyze recent scan results and alerts
3. Present concise security status summary
4. Provide actionable recommendations if issues found

---

## Output Format

```
🛡️ **Security Status: [HEALTHY|WARNING|CRITICAL|DEGRADED]**

**Last Scan**: [timestamp]
**Active Alerts**: [count by severity]
**Recent Findings**: [summary]

### Dependency Health
- [Status] - Last scan: [time ago]
- [Vulnerability count if any]

### Code Security
- [Status] - Last scan: [time ago]
- [Issue count if any]

### Compliance
- SOC2: [✅|❌]
- ISO27001: [✅|❌]
- UFC: [✅|❌]

### Next Actions
[If issues found, list 1-3 specific actions]
[If clean, confirmation message]

---
**Dashboard**: http://127.0.0.1:8063
**Full Report**: Use Security Specialist Agent for detailed analysis
```

---

## Implementation Logic

### Data Source
Query `claude/data/security_metrics.db`:
- `scan_history` table - Last 24 hours of scans
- `security_alerts` table - Active alerts (status='new')
- `security_metrics` table - Recent metrics

### Status Determination
- **HEALTHY**: No alerts, recent scans clean
- **WARNING**: Medium/Low alerts OR scan errors
- **CRITICAL**: Critical/High alerts present
- **DEGRADED**: No recent scans (>24h gap) OR database errors

### Response Time Optimization
- Direct SQLite query (no subprocess calls)
- Read-only database access
- Cached results for 60 seconds
- Single query with JOINs where possible

---

## Examples

### Example 1: Clean System
```
🛡️ **Security Status: HEALTHY** ✅

**Last Scan**: 2 hours ago
**Active Alerts**: None

### Dependency Health
✅ Clean - Last scan: 2 hours ago
No known vulnerabilities in dependencies

### Code Security
✅ Clean - Last scan: 18 hours ago
Code quality: A+ (9.2/10 Bandit score)

### Compliance
- SOC2: ✅
- ISO27001: ✅
- UFC: ✅

### Next Actions
✅ System secure. Next scheduled scan in 4 hours.

---
**Dashboard**: http://127.0.0.1:8063
```

### Example 2: Critical Issues
```
🛡️ **Security Status: CRITICAL** 🚨

**Last Scan**: 15 minutes ago
**Active Alerts**: 2 critical, 3 high

### Dependency Health
⚠️ 2 critical vulnerabilities detected
- numpy 1.24.3 (CVE-2024-XXXXX) - Upgrade to 1.26.0
- requests 2.28.0 (CVE-2024-YYYYY) - Upgrade to 2.31.0

### Code Security
⚠️ 3 high-severity issues
- Hardcoded credentials in config.py:42
- SQL injection risk in database.py:156
- Insecure deserialization in api.py:89

### Compliance
- SOC2: ❌ (credential issues)
- ISO27001: ⚠️ (pending resolution)
- UFC: ✅

### Next Actions
1. **URGENT**: Remove hardcoded credentials from config.py
2. **URGENT**: Upgrade numpy and requests packages
3. Review and fix code security issues (use Security Specialist Agent)

---
**Dashboard**: http://127.0.0.1:8063
**Full Report**: Run `python3 claude/tools/security/local_security_scanner.py`
```

### Example 3: Degraded System
```
🛡️ **Security Status: DEGRADED** ⚠️

**Last Scan**: 36 hours ago (overdue)
**Active Alerts**: None

### Dependency Health
⚠️ No recent scan (>24h)
Last scan status: Clean (36 hours ago)

### Code Security
⚠️ No recent scan (>24h)
Last scan status: Clean (36 hours ago)

### Compliance
- SOC2: ⚠️ (scan overdue)
- ISO27001: ⚠️ (scan overdue)
- UFC: ✅

### Next Actions
1. Check if security orchestration service is running
2. Run manual scan: `python3 claude/extensions/experimental/security_orchestration_service.py --scan-now all`
3. Verify LaunchAgent status: `launchctl list | grep security`

---
**Dashboard**: http://127.0.0.1:8063
```

---

## Usage Scenarios

### Quick Check Before Commit
User: `/security-status`
→ Quick 5-second check before git commit
→ Identifies any blocking security issues

### Morning Routine
User: `/security-status`
→ Part of daily startup routine
→ Confirms overnight scans completed

### Pre-Deployment Check
User: `/security-status`
→ Validate security before production deployment
→ Ensure no critical vulnerabilities

### Troubleshooting
User: `/security-status`
→ Diagnose why security alerts triggered
→ Quick assessment before deeper investigation

---

## Integration with Other Commands

### Escalation Path
1. `/security-status` - Quick check (5s)
2. Load Security Specialist Agent - Detailed analysis (30s)
3. Run full security tools - Deep scan (5+ minutes)

### Complementary Commands
- `/save-state` - Includes security preflight (Phase 4)
- Security Specialist Agent commands - Full suite of security operations
- Manual tools - `local_security_scanner.py`, `security_hardening_manager.py`

---

## Technical Implementation

### Database Queries
```sql
-- Recent scans (last 24h)
SELECT * FROM scan_history
WHERE timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;

-- Active alerts
SELECT severity, COUNT(*) FROM security_alerts
WHERE status = 'new'
GROUP BY severity;

-- Latest metrics
SELECT metric_name, metric_value FROM security_metrics
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;
```

### Response Caching
Cache results for 60 seconds to avoid excessive DB queries during rapid repeated calls.

### Error Handling
- Database not found → Suggest running orchestrator first
- Database locked → Wait and retry (max 3 attempts)
- Query errors → Fallback to "UNKNOWN" status with error message

---

## Performance Requirements

- **Response Time**: <5 seconds (target: 2-3 seconds)
- **Database Queries**: 3 queries max
- **Memory Usage**: <50MB
- **CPU Usage**: Minimal (read-only queries)

---

## Security Considerations

- Read-only database access
- No credential exposure in output
- Sanitized file paths (relative only)
- No execution of arbitrary commands
- Safe error messages (no stack traces to user)

---

**Version**: 1.0
**Created**: 2025-10-13 (Phase 113 - Security Automation Project)
**Last Updated**: 2025-10-13
