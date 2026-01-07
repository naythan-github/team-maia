# M365 IR Status Code Reference - Maintenance Runbook

**Version**: 1.0
**Phase**: PHASE_1_FOUNDATION (Phase 1.3 - Status Code Lookup Tables)
**Created**: 2026-01-06
**Maintenance Schedule**: Quarterly (January, April, July, October)

---

## Purpose

This runbook guides SRE and IR teams through maintaining the `status_code_reference` table to ensure accurate status code lookups as Microsoft updates their APIs.

---

## Quarterly Maintenance Tasks

### Q1 - Validation (15 minutes)

1. **Check for Unknown Codes** (5 min)
   ```bash
   # Query unknown codes detected in last quarter
   sqlite3 /path/to/case.db "
   SELECT code_value, COUNT(*) as occurrences
   FROM (
       SELECT DISTINCT status_error_code as code_value
       FROM sign_in_logs
       WHERE imported_at >= date('now', '-3 months')
   )
   WHERE code_value NOT IN (
       SELECT code_value FROM status_code_reference
       WHERE log_type = 'sign_in_logs' AND field_name = 'status_error_code'
   )
   GROUP BY code_value
   ORDER BY occurrences DESC
   "
   ```

2. **Review Import Logs** (5 min)
   ```bash
   # Check for unknown code warnings
   grep "Unknown status code" /var/log/m365_ir/*.log | tail -20
   ```

3. **Update Last Validated Date** (5 min)
   ```python
   from claude.tools.m365_ir.status_code_manager import StatusCodeManager
   import sqlite3
   from datetime import datetime

   db_path = '/path/to/case.db'
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()

   # Update all codes
   cursor.execute("""
       UPDATE status_code_reference
       SET last_validated = ?
       WHERE last_validated < date('now', '-90 days')
   """, (datetime.now().isoformat(),))

   conn.commit()
   conn.close()

   print(f"✅ Updated {cursor.rowcount} status codes")
   ```

### Q2 - Research New Codes (30 minutes)

1. **Check Microsoft Documentation** (15 min)
   - Visit: https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes
   - Review changelog: https://learn.microsoft.com/en-us/entra/fundamentals/whats-new
   - Check for new AADSTS error codes announced in last 3 months

2. **Research Unknown Codes** (10 min)
   - For each unknown code found in Q1:
     - Search Microsoft Learn: `site:learn.microsoft.com AADSTS<code>`
     - Check Microsoft Q&A forums
     - Review Azure AD/Entra ID release notes

3. **Document Findings** (5 min)
   ```markdown
   ## Quarterly Review - 2026-Q1

   **Date**: 2026-01-06
   **Analyst**: John Doe

   **Unknown Codes Found**:
   - AADSTS99999: Found in 12 cases. Microsoft docs indicate...

   **New Codes to Add**:
   - AADSTS123456: "New error description" (CRITICAL)

   **Deprecated Codes**:
   - AADSTS50001: Now replaced by AADSTS50002
   ```

### Q3 - Update Reference Table (20 minutes)

1. **Add New Codes** (10 min)
   ```python
   from claude.tools.m365_ir.status_code_manager import StatusCodeManager

   manager = StatusCodeManager('/path/to/case.db')

   # Add newly discovered code
   manager.add_status_code(
       log_type='sign_in_logs',
       field_name='status_error_code',
       code_value='123456',
       meaning='[Description from Microsoft docs]',
       severity='CRITICAL'  # or WARNING, INFO
   )

   print("✅ New code added")
   ```

2. **Mark Deprecated Codes** (5 min)
   ```python
   # Mark code as deprecated
   manager.update_status_code(
       log_type='sign_in_logs',
       field_name='status_error_code',
       code_value='50001',
       deprecated=True,
       meaning='Legacy error (use AADSTS50002 instead)'
   )

   print("✅ Code marked as deprecated")
   ```

3. **Verify Updates** (5 min)
   ```bash
   # Count total codes
   sqlite3 /path/to/case.db "
   SELECT
       COUNT(*) as total_codes,
       SUM(CASE WHEN deprecated = 1 THEN 1 ELSE 0 END) as deprecated_codes,
       MAX(last_validated) as last_updated
   FROM status_code_reference
   WHERE log_type = 'sign_in_logs'
   "
   ```

### Q4 - Testing (15 minutes)

1. **Run Unit Tests** (5 min)
   ```bash
   python3 -m pytest tests/m365_ir/data_quality/test_status_code_manager.py -v
   ```

2. **Test Unknown Code Detection** (5 min)
   ```python
   from claude.tools.m365_ir.status_code_manager import StatusCodeManager

   manager = StatusCodeManager('/path/to/production.db')
   unknown = manager.scan_for_unknown_codes('sign_in_logs', 'status_error_code')

   print(f"Unknown codes: {len(unknown)}")
   for code in unknown[:5]:
       print(f"  - {code['code_value']}: {code['count']} occurrences")
   ```

3. **Verify Lookup Performance** (5 min)
   ```python
   import time

   manager = StatusCodeManager('/path/to/production.db')

   # Test lookup speed
   start = time.time()
   for i in range(100):
       result = manager.lookup_status_code('sign_in_logs', 'status_error_code', '50126')
   duration = time.time() - start

   avg_ms = (duration / 100) * 1000
   print(f"✅ Average lookup: {avg_ms:.2f}ms (target: <10ms)")
   assert avg_ms < 10, "Lookup performance degraded!"
   ```

---

## Ad-Hoc Maintenance

### New Unknown Code Detected

**Trigger**: Import logs show: `⚠️  Unknown status codes detected`

**Response** (5 minutes):
1. Review the unknown code in import output
2. Quick search Microsoft docs: `site:learn.microsoft.com AADSTS<code>`
3. If found in docs → add to reference table
4. If not found → escalate to SRE team for investigation

**Example**:
```python
# Quick add unknown code
from claude.tools.m365_ir.status_code_manager import StatusCodeManager

manager = StatusCodeManager('/path/to/case.db')
manager.add_status_code(
    log_type='sign_in_logs',
    field_name='status_error_code',
    code_value='99999',
    meaning='[PENDING RESEARCH] - Unknown code',
    severity='WARNING'
)
```

### Microsoft API Schema Change

**Trigger**: Microsoft announces Entra ID API update

**Response** (30 minutes):
1. Review Microsoft changelog/release notes
2. Check for new fields or renamed fields
3. Update `schema_versions` table:
   ```python
   import sqlite3
   from datetime import datetime
   import hashlib

   conn = sqlite3.connect('/path/to/case.db')
   cursor = conn.cursor()

   # Get current schema
   cursor.execute("PRAGMA table_info(sign_in_logs)")
   fields = [row[1] for row in cursor.fetchall()]
   schema_hash = hashlib.sha256(','.join(sorted(fields)).encode()).hexdigest()

   # Record schema version
   cursor.execute("""
       INSERT INTO schema_versions
       (log_type, api_version, schema_hash, detected_date, notes)
       VALUES (?, ?, ?, ?, ?)
   """, (
       'sign_in_logs',
       'v1.0',
       schema_hash,
       datetime.now().isoformat(),
       'Updated after Microsoft Entra ID API v2.0 release'
   ))

   conn.commit()
   conn.close()
   ```

---

## Monitoring & Alerting

### Metrics to Track

1. **Unknown Code Rate** (target: <5% of imports)
   ```sql
   SELECT
       COUNT(DISTINCT status_error_code) as total_codes,
       COUNT(DISTINCT CASE
           WHEN status_error_code NOT IN (
               SELECT code_value FROM status_code_reference
               WHERE log_type = 'sign_in_logs' AND field_name = 'status_error_code'
           ) THEN status_error_code
       END) as unknown_codes
   FROM sign_in_logs
   WHERE imported_at >= date('now', '-30 days')
   ```

2. **Last Validation Age** (alert if >120 days)
   ```sql
   SELECT
       MIN(last_validated) as oldest_validation,
       julianday('now') - julianday(MIN(last_validated)) as days_since_validation
   FROM status_code_reference
   ```

3. **Deprecated Code Usage** (alert if detected)
   ```sql
   SELECT
       scr.code_value,
       scr.meaning,
       COUNT(*) as usage_count
   FROM sign_in_logs sl
   JOIN status_code_reference scr
       ON sl.status_error_code = scr.code_value
       AND scr.log_type = 'sign_in_logs'
       AND scr.field_name = 'status_error_code'
   WHERE scr.deprecated = 1
     AND sl.imported_at >= date('now', '-30 days')
   GROUP BY scr.code_value
   ORDER BY usage_count DESC
   ```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Unknown code rate | >5% | >15% |
| Last validation age | >90 days | >120 days |
| Deprecated code usage | >0 | >100 occurrences |

---

## Troubleshooting

### Issue: High Unknown Code Rate (>15%)

**Causes**:
1. Microsoft released new API version
2. Reference table outdated
3. Data quality issue (invalid codes in CSV)

**Resolution**:
1. Check Microsoft Entra ID changelog
2. Run quarterly maintenance ahead of schedule
3. Verify CSV data source is from official M365 export

### Issue: Lookup Performance Degraded (>10ms)

**Causes**:
1. Database not indexed
2. Table grown too large
3. Disk I/O bottleneck

**Resolution**:
```sql
-- Rebuild indexes
REINDEX idx_status_code_log_type;
REINDEX idx_status_code_field_name;
REINDEX idx_status_code_lookup;

-- Vacuum database
VACUUM;

-- Check index usage
EXPLAIN QUERY PLAN
SELECT meaning FROM status_code_reference
WHERE log_type = 'sign_in_logs'
  AND field_name = 'status_error_code'
  AND code_value = '50126';
```

### Issue: Duplicate Code Errors

**Cause**: Attempting to add code that already exists

**Resolution**:
```python
# Use update instead of add
manager.update_status_code(
    log_type='sign_in_logs',
    field_name='status_error_code',
    code_value='50126',
    meaning='Updated description',
    severity='WARNING'
)
```

---

## Reference Links

- **Microsoft Entra Error Codes**: https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes
- **Sign-in Troubleshooting**: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/howto-troubleshoot-sign-in-errors
- **Entra ID What's New**: https://learn.microsoft.com/en-us/entra/fundamentals/whats-new
- **Error Code Lookup Tool**: https://login.microsoftonline.com/error

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial runbook for Phase 1.3 |

---

**Maintenance Owner**: SRE Team
**Escalation Contact**: Principal IR Analyst

**End of Runbook**
