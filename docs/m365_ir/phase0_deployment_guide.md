# M365 IR Phase 0 Auto-Checks - Deployment Guide

## System Requirements

### Python Requirements
- **Python Version**: 3.9+ (tested on 3.9, 3.10, 3.11)
- **Dependencies**: sqlite3 (built-in), typing (built-in for 3.9+)

### Hardware Requirements
| Tenant Size | CPU | RAM | Disk |
|-------------|-----|-----|------|
| Small (<1K users) | 1 core | 512 MB | 100 MB |
| Medium (1-10K users) | 2 cores | 1 GB | 500 MB |
| Large (10-100K users) | 4 cores | 2 GB | 2 GB |

### Operating System
- Linux (Ubuntu 20.04+, RHEL 8+)
- macOS 11+
- Windows 10+ (with WSL2 recommended)

---

## Installation

### Option 1: Clone Repository
```bash
git clone https://github.com/naythan-orro/maia.git
cd maia

# Verify installation
python3 -m pytest tests/test_phase0_auto_checks.py -v
```

### Option 2: Direct File Deployment
```bash
# Copy core files
cp claude/tools/m365_ir/phase0_auto_checks.py /opt/m365-ir/
cp claude/tools/m365_ir/phase0_cli.py /opt/m365-ir/

# Make CLI executable
chmod +x /opt/m365-ir/phase0_cli.py
```

---

## Configuration

### 1. Break-Glass Whitelist (Optional)

Create `~/.maia/config/breakglass_accounts.json`:

```bash
mkdir -p ~/.maia/config
cat > ~/.maia/config/breakglass_accounts.json <<EOF
{
  "accounts": [
    "breakglass.admin@contoso.com",
    "emergency.admin@contoso.com"
  ]
}
EOF
```

**Security**: Set restrictive permissions
```bash
chmod 600 ~/.maia/config/breakglass_accounts.json
```

### 2. Service Account Patterns (Optional)

If your organization uses custom service account naming, update `SERVICE_ACCOUNT_PATTERNS` in `phase0_auto_checks.py`:

```python
SERVICE_ACCOUNT_PATTERNS = [
    r'^svc[_\-\.]',       # svc_backup, svc-api
    r'^service[_\-\.]',   # service_account
    r'^app[_\-\.]',       # app-integration
    r'^noreply@',         # noreply@
    r'^api[_\-\.]',       # api.connector
    r'^your_custom_pattern',  # Add custom patterns
]
```

---

## Database Setup

### Schema Validation

Verify your M365 IR database has required tables:

```bash
sqlite3 /path/to/investigation.db ".schema" | grep -E "password_status|sign_in_logs"
```

**Required Tables**:
1. `password_status` (user_principal_name, last_password_change, mfa_status, auth_method)
2. `sign_in_logs` (user_principal_name, timestamp, location_country, latitude, longitude, auth_method)

**Optional Tables** (features degrade gracefully):
3. `entra_audit_log` (timestamp, activity, initiated_by, target_user, result)
4. `unified_audit_log` (timestamp, user_id, operation, result_status)
5. `mfa_changes` (user, timestamp, activity_display_name, result)

### Performance Optimization

Create indexes for large databases:

```sql
-- Password status
CREATE INDEX idx_password_status_upn ON password_status(user_principal_name);
CREATE INDEX idx_password_status_mfa ON password_status(mfa_status);

-- Sign-in logs
CREATE INDEX idx_signin_upn_timestamp ON sign_in_logs(user_principal_name, timestamp);
CREATE INDEX idx_signin_country ON sign_in_logs(location_country);
CREATE INDEX idx_signin_coords ON sign_in_logs(latitude, longitude);

-- Audit logs
CREATE INDEX idx_entra_audit_timestamp ON entra_audit_log(timestamp);
CREATE INDEX idx_unified_audit_timestamp ON unified_audit_log(timestamp);
CREATE INDEX idx_mfa_changes_user_timestamp ON mfa_changes(user, timestamp);
```

**Impact**: 50-80% runtime reduction for large datasets

---

## Deployment Patterns

### Pattern 1: Standalone CLI Tool

**Use Case**: Manual incident response

```bash
# Add to PATH
ln -s /opt/m365-ir/phase0_cli.py /usr/local/bin/m365-phase0

# Run checks
m365-phase0 /path/to/investigation.db --format=table
```

### Pattern 2: SOAR Integration

**Use Case**: Automated incident triage

```python
# playbook.py
from claude.tools.m365_ir.phase0_cli import run_phase0_checks

def m365_incident_triage(case_id, db_path):
    results = run_phase0_checks(db_path, output_format='json')

    # Auto-escalate critical issues
    if results['summary']['critical'] > 0:
        escalate_to_tier2(case_id, results)

    # Auto-remediate
    for event in results['checks']['impossible_travel']['impossible_travel_events']:
        disable_user(event['upn'])
        send_notification(event['upn'])

    return results
```

### Pattern 3: Scheduled Baseline Monitoring

**Use Case**: Continuous monitoring

```bash
# cron: Daily at 2 AM
0 2 * * * /usr/local/bin/m365-phase0 /data/tenant.db --format=json > /var/log/phase0/$(date +\%Y\%m\%d).json
```

### Pattern 4: API Endpoint

**Use Case**: Web dashboard integration

```python
# Flask example
from flask import Flask, jsonify
from claude.tools.m365_ir.phase0_cli import run_phase0_checks

app = Flask(__name__)

@app.route('/api/phase0/<tenant_id>')
def phase0_check(tenant_id):
    db_path = f"/data/{tenant_id}.db"
    results = run_phase0_checks(db_path, output_format='json')
    return jsonify(results)
```

---

## Production Checklist

### Pre-Deployment

- [ ] Python 3.9+ installed
- [ ] All dependencies available
- [ ] Test suite passes (29/29 tests)
- [ ] Database schema validated
- [ ] Indexes created (large tenants)
- [ ] Break-glass whitelist configured
- [ ] Service account patterns validated

### Security

- [ ] Database access restricted (filesystem permissions)
- [ ] Break-glass config has 600 permissions
- [ ] Logging configured (audit trail)
- [ ] PII redaction policy defined
- [ ] Data retention policy applied

### Performance

- [ ] Baseline runtime measured (<5s for 1000 users)
- [ ] Memory usage profiled (<200MB for typical tenant)
- [ ] Concurrent execution tested (if applicable)

### Monitoring

- [ ] Error logging configured
- [ ] Performance metrics tracked
- [ ] Alert thresholds defined
- [ ] Dashboard created (optional)

---

## Scaling Considerations

### Horizontal Scaling

For very large deployments (100K+ users):

```python
# Process tenants in parallel
from multiprocessing import Pool

def process_tenant(tenant_db):
    return run_phase0_checks(tenant_db)

with Pool(processes=4) as pool:
    results = pool.map(process_tenant, tenant_dbs)
```

### Database Optimization

For slow queries:

1. **Use indexes** (see Performance Optimization section)
2. **Partition large tables** by date
3. **Archive old data** (>180 days)
4. **Use connection pooling** for high-frequency checks

---

## Troubleshooting

### Issue: "Database locked" error

**Cause**: Concurrent access or incomplete transaction

**Fix**:
```bash
# Check for locks
lsof /path/to/investigation.db

# If stuck, clear journal
rm /path/to/investigation.db-journal
```

### Issue: Slow performance

**Cause**: Missing indexes or large dataset

**Fix**:
1. Create indexes (see Performance Optimization)
2. Vacuum database: `sqlite3 db.db "VACUUM;"`
3. Analyze query plans: `EXPLAIN QUERY PLAN SELECT...`

### Issue: "No module named 'claude'"

**Cause**: Incorrect Python path

**Fix**:
```bash
export PYTHONPATH=/path/to/maia:$PYTHONPATH
# OR
python3 -m pip install -e /path/to/maia
```

### Issue: Incorrect results

**Cause**: Data quality or schema mismatch

**Fix**:
1. Validate schema: `.schema tablename`
2. Check for NULLs: `SELECT COUNT(*) FROM password_status WHERE last_password_change IS NULL;`
3. Verify data types: `.schema` should match requirements

---

## Rollback Procedure

If issues occur in production:

1. **Stop execution**:
   ```bash
   pkill -f phase0_cli.py
   ```

2. **Restore previous version**:
   ```bash
   git checkout <previous-commit>
   ```

3. **Verify tests**:
   ```bash
   python3 -m pytest tests/test_phase0_auto_checks.py -v
   ```

4. **Document incident** and report to development team

---

## Upgrade Procedure

### Minor Updates (Bug fixes, optimizations)

```bash
cd /path/to/maia
git pull origin main

# Run tests
python3 -m pytest tests/test_phase0_auto_checks.py -v

# If tests pass, deploy
cp claude/tools/m365_ir/phase0_*.py /opt/m365-ir/
```

### Major Updates (Breaking changes)

1. **Review changelog** and migration guide
2. **Test in staging environment**
3. **Backup existing configuration**
4. **Apply schema migrations** (if any)
5. **Deploy to production**
6. **Monitor for 24 hours**

---

## Monitoring & Alerting

### Key Metrics to Track

| Metric | Threshold | Action |
|--------|-----------|--------|
| Runtime | >10s for 1000 users | Investigate performance |
| Memory | >500MB | Check for memory leaks |
| Critical issues | >0 | Alert security team |
| Error rate | >5% | Check database schema |

### Sample Monitoring Script

```bash
#!/bin/bash
# monitor_phase0.sh

DB_PATH="/data/production.db"
LOG_FILE="/var/log/phase0/runtime.log"

START=$(date +%s)
python3 /opt/m365-ir/phase0_cli.py "$DB_PATH" --format=json > /tmp/phase0_result.json
EXIT_CODE=$?
END=$(date +%s)
RUNTIME=$((END - START))

echo "$(date +%Y-%m-%d\ %H:%M:%S) - Runtime: ${RUNTIME}s, Exit code: $EXIT_CODE" >> "$LOG_FILE"

# Alert if runtime exceeds threshold
if [ $RUNTIME -gt 10 ]; then
    echo "ALERT: Phase 0 runtime exceeded 10s (${RUNTIME}s)" | mail -s "Phase 0 Performance Alert" ops@contoso.com
fi

# Alert if critical issues found
if [ $EXIT_CODE -eq 2 ]; then
    CRITICAL_COUNT=$(jq '.summary.critical' /tmp/phase0_result.json)
    echo "ALERT: ${CRITICAL_COUNT} critical issues detected" | mail -s "Phase 0 Critical Issues" security@contoso.com
fi
```

---

## Support & Maintenance

### Regular Maintenance

- **Weekly**: Review performance metrics
- **Monthly**: Update break-glass whitelist
- **Quarterly**: Review and update service account patterns
- **Annually**: Full security audit and penetration testing

### Getting Help

- **Documentation**: `/Users/YOUR_USERNAME/maia/docs/m365_ir/`
- **GitHub Issues**: https://github.com/naythan-orro/maia/issues
- **Test Suite**: Run `pytest -v` to verify functionality

---

**Version**: 1.0.0 (Sprint 4)
**Last Updated**: 2026-01-10
