# M365 IR Data Quality Failure Runbook

**Version**: 2.1
**Phase**: PHASE_2_SMART_ANALYSIS (Phase 2.1 - Intelligent Field Selection)
**Created**: 2026-01-06
**Updated**: 2026-01-07 (Phase 2.1 operational guidance added)

---

## ✅ Phase 2.1 Update (2026-01-07)

**NEW**: This runbook now includes operational guidance for Phase 2.1 intelligent field selection system.

### What Changed
- Added "Phase 2.1 Field Selection" section (see below)
- Added confidence score interpretation guide
- Added historical learning troubleshooting
- Original Phase 1 content remains unchanged

### Quick Links
- [Phase 2.1 Field Selection Guide](#phase-21-intelligent-field-selection-guide) ← **NEW**
- [Understanding Confidence Scores](#understanding-confidence-scores) ← **NEW**
- [Historical Learning Troubleshooting](#historical-learning-troubleshooting) ← **NEW**
- [Original Phase 1 Runbook](#purpose) (starts below)

---

## Purpose

This runbook guides forensic analysts through troubleshooting and resolving data quality failures during M365 IR log imports.

---

## When Does This Runbook Apply?

Use this runbook when you encounter a `DataQualityError` during import:

```
DataQualityError: Data quality check FAILED: Quality score 0.33 is below threshold (0.5). Import aborted.

Unreliable fields (12): user_display_name, location_city, location_country, ...

Recommendations:
  - Use 'conditional_access_status' for status analysis (reliable field with 2 distinct values)
```

---

## Understanding the Error

### Quality Score Calculation

**Quality Score** = (Reliable Fields / Populated Fields)

- **Reliable Field**: Field with >0.5% variation (not 100% uniform)
- **Populated Field**: Field with >5% non-NULL values
- **Threshold**: 0.5 (50% of populated fields must be reliable)

### Common Scenarios

| Scenario | Quality Score | Cause |
|----------|---------------|-------|
| Partial CSV export | 0.20-0.40 | Only essential fields populated |
| Test/synthetic data | 0.00-0.30 | Uniform test values |
| Legacy auth logs | 0.40-0.60 | Missing modern fields |
| Complete export | 0.70-1.00 | All fields populated with real data |

---

## Troubleshooting Steps

### Step 1: Review Quality Report

The error message contains key information:

```
Quality score 0.33 is below threshold (0.5)
Unreliable fields (12): user_display_name, location_city, ...
Recommendations:
  - Use 'conditional_access_status' for status analysis
```

**Questions to ask**:
1. How many fields are unreliable?
2. Are critical fields (user_id, timestamp, location) reliable?
3. What recommendations are provided?

---

### Step 2: Identify Root Cause

#### Cause A: Partial CSV Export

**Symptoms**:
- Many fields 100% NULL (unpopulated)
- Quality score 0.20-0.40
- CSV has <10 columns

**Solution**: Export complete log data from M365
```powershell
# Export sign-in logs with ALL fields
Connect-AzureAD
Get-AzureADAuditSignInLogs -All:$true | Export-Csv sign_in_logs_full.csv -NoTypeInformation
```

**Quick Fix**: Lower quality threshold for this specific import
```python
# Add to import command
importer.import_sign_in_logs(csv_file, quality_threshold=0.3)
```

---

#### Cause B: Uniform Test Data

**Symptoms**:
- All users have same location (e.g., 100% "AU")
- All IPs from same subnet
- Quality score 0.00-0.30

**Solution**: Use REAL data, not synthetic test data

**Quick Fix**: Skip quality check for test environments
```python
# WARNING: Only use in non-production environments
importer.import_sign_in_logs(csv_file, skip_quality_check=True)
```

---

#### Cause C: Legacy Auth Logs (Missing Modern Fields)

**Symptoms**:
- Fields like `conditional_access_status`, `risk_level` are NULL
- Quality score 0.40-0.60
- Logs from pre-2020 timeframe

**Solution**: This is expected for legacy logs
```python
# Accept lower quality for legacy logs
importer.import_sign_in_logs(csv_file, quality_threshold=0.4)
```

---

#### Cause D: Field Mapping Issues

**Symptoms**:
- CSV has data but fields show as 100% NULL
- Column names don't match expected format

**Solution**: Verify CSV column names match M365 export format
```csv
# Expected columns:
CreatedDateTime, UserPrincipalName, IPAddress, Country, ConditionalAccessStatus, ...
```

**Fix**: Rename CSV columns to match expected names

---

### Step 3: Determine Action

| Quality Score | Action | Justification |
|---------------|--------|---------------|
| 0.00-0.20 | **REJECT** | Too unreliable for analysis |
| 0.20-0.40 | **REVIEW** | Partial data - verify completeness |
| 0.40-0.60 | **ACCEPT** (legacy) | Acceptable for historical logs |
| 0.60-1.00 | **ACCEPT** | Good quality data |

---

### Step 4: Override Quality Check (If Necessary)

#### Option 1: Lower Threshold (Recommended)

```python
from claude.tools.m365_ir.log_importer import LogImporter

importer = LogImporter(db)
result = importer.import_sign_in_logs(
    'sign_in_logs.csv',
    quality_threshold=0.3  # Lower threshold for partial data
)
```

#### Option 2: Skip Quality Check (Use with Caution)

```python
result = importer.import_sign_in_logs(
    'sign_in_logs.csv',
    skip_quality_check=True  # WARNING: No validation
)
```

**⚠️ Warning**: Skipping quality checks increases risk of forensic errors!

---

### Step 5: Document Override Decision

If you override quality checks, document your decision:

```markdown
## Quality Check Override - PIR-ACME-2025-001

**Date**: 2026-01-06
**Analyst**: John Doe
**Quality Score**: 0.35
**Threshold Used**: 0.3 (lowered from 0.5)

**Justification**:
Legacy auth logs from 2019 missing modern fields (conditional_access_status, risk_level).
Only basic fields (user_id, timestamp, ip, location) populated. These fields passed reliability checks.

**Mitigation**:
- Verified critical fields (user_id, timestamp, location) are reliable
- Manual review of status field selection (using 'Status' not 'StatusErrorCode')
- Cross-referenced with Azure AD sign-in reports

**Risk Assessment**: LOW - Core fields reliable, only modern features missing
```

---

## Prevention

### Best Practices for Data Exports

1. **Use Complete Exports**: Always export ALL fields from M365
   ```powershell
   Get-AzureADAuditSignInLogs -All:$true | Select-Object *
   ```

2. **Verify Before Import**: Check CSV has >10 columns with varied data

3. **Test on Sample**: Import 100 records first to validate quality

4. **Use Official Tools**: Prefer M365 Compliance Center exports over custom scripts

---

## Quality Check Parameters (Reference)

### Reliability Criteria

A field is **UNRELIABLE** if:
- >99.5% of values are identical (uniform)
- OR only 1 distinct value exists

### Population Criteria

A field is **POPULATED** if:
- >5% of records have non-NULL values

### Quality Thresholds

| Threshold | Use Case |
|-----------|----------|
| 0.7 | Production imports (strict) |
| 0.5 | Standard imports (default) |
| 0.3 | Legacy/partial data |
| 0.0 (skip) | Test/development only |

---

## Escalation

If you cannot resolve the quality issue:

1. **Check Data Source**: Verify M365 export completed successfully
2. **Consult SRE**: Quality check logic may need tuning
3. **Manual Review**: Expert analyst can approve override

**Contact**: SRE Team or Principal IR Analyst

---

## Appendix A: Common Field Issues

### Sign-In Logs

| Field | Common Issue | Fix |
|-------|--------------|-----|
| `status_error_code` | 100% uniform (all `1`) | Use `conditional_access_status` instead |
| `location_country` | 100% same value | Geographic restriction or VPN |
| `client_app` | 100% NULL | Legacy logs pre-modern auth |

### Unified Audit Logs

| Field | Common Issue | Fix |
|-------|--------------|-----|
| `operation` | Too many distinct values | Expected (hundreds of ops) |
| `result_status` | 100% Success | Filtered export (only successful ops) |

---

## Appendix B: Example Quality Reports

### Good Quality (0.85)
```
Quality score: 0.85
Reliable fields (17/20):
  - timestamp, user_principal_name, ip_address, location_country,
    conditional_access_status, risk_level, client_app, ...
Unreliable fields (3/20):
  - status_error_code (100% uniform)
  - user_display_name (95% NULL)
  - correlation_id (100% unique - not useful for grouping)
```

### Poor Quality (0.25)
```
Quality score: 0.25
Reliable fields (5/20):
  - timestamp, user_principal_name, ip_address, user_id, raw_record
Unreliable fields (15/20):
  - location_country (100% NULL)
  - conditional_access_status (100% NULL)
  - risk_level (100% NULL)
  - status_error_code (100% uniform - all 1)
  ...
```

---

## Phase 2.1 Intelligent Field Selection Guide

**NEW**: Phase 2.1 adds intelligent, multi-factor field selection with confidence scoring and historical learning.

### How It Works

When you import sign-in logs, Phase 2.1 automatically:
1. **Discovers** all candidate status fields in your dataset
2. **Scores** each field across 5 dimensions (uniformity, discriminatory power, population, historical success, domain knowledge)
3. **Ranks** fields by overall reliability score (0-1)
4. **Selects** the best field with confidence level (HIGH/MEDIUM/LOW)
5. **Learns** from the outcome for future cases

### What You'll See

```
Phase 2.1 selected 'conditional_access_status' (confidence: HIGH, score: 0.72)

Selected 'conditional_access_status' (rank #1 of 3). Overall score: 0.72.
Uniformity: 0.89. Discriminatory power: 0.00. Population: 100.0%.
Historical success: 100%. Preferred field (domain knowledge).
```

---

## Understanding Confidence Scores

### Confidence Levels

| Level | Score Range | Meaning | Action |
|-------|-------------|---------|--------|
| **HIGH** | 0.70-1.00 | Excellent reliability | ✅ Trust the selection |
| **MEDIUM** | 0.50-0.69 | Acceptable reliability | ⚠️ Review reasoning |
| **LOW** | 0.00-0.49 | Poor reliability | 🚨 Manual review required |

### What Each Dimension Measures

1. **Uniformity Score (0-1)**:
   - How varied the field values are
   - 0.00 = 100% same value (bad)
   - 1.00 = Perfect distribution (good)
   - **Target**: >0.50

2. **Discriminatory Power (0-1)**:
   - How well the field separates success from failure
   - 0.00 = No separation (expected for status fields)
   - 1.00 = Perfect separation
   - **Note**: Status fields typically have ~0.00 (this is normal)

3. **Population Coverage (0-100%)**:
   - Percentage of records with non-NULL values
   - **Target**: >95%

4. **Historical Success Rate (0-100%)**:
   - How often this field led to correct verification in past cases
   - **Target**: >80%

5. **Domain Knowledge Bonus**:
   - Preferred fields (like `conditional_access_status`) get +0.05 bonus
   - Based on forensic best practices

---

## Interpreting Phase 2.1 Outputs

### Example 1: High Confidence (Good)

```
Field: conditional_access_status
Confidence: HIGH
Score: 0.72
Reasoning: Selected 'conditional_access_status' (rank #1 of 3).
  Uniformity: 0.89 ✅ (good variety)
  Discriminatory power: 0.00 (expected)
  Population: 100.0% ✅ (fully populated)
  Historical success: 100% ✅ (always works)
  Preferred field ✅ (domain knowledge)
```

**Interpretation**: Excellent choice. Trust this field selection.

---

### Example 2: Medium Confidence (Review)

```
Field: status_error_code
Confidence: MEDIUM
Score: 0.58
Reasoning: Selected 'status_error_code' (rank #1 of 2).
  Uniformity: 0.65 ⚠️ (some variation but not ideal)
  Discriminatory power: 0.00 (expected)
  Population: 100.0% ✅
  Historical success: 75% ⚠️ (worked 3/4 times)
  Not preferred field (missing domain knowledge bonus)
```

**Interpretation**: Acceptable but not ideal. Review the verification results carefully.

**Action**: Check if `conditional_access_status` exists but wasn't populated.

---

### Example 3: Low Confidence (Manual Review Required)

```
Field: result_status
Confidence: LOW
Score: 0.42
Reasoning: Selected 'result_status' (rank #1 of 1).
  Uniformity: 0.35 🚨 (mostly uniform)
  Discriminatory power: 0.00 (expected)
  Population: 98.0% ✅
  Historical success: 50% 🚨 (only worked 1/2 times)
  Not preferred field
```

**Interpretation**: Poor quality field selected because no better alternatives exist.

**Action**:
1. Review the verification summary warnings
2. Check if data export was incomplete
3. Consider manual analysis instead of auto-verification

---

## Historical Learning Troubleshooting

### How Historical Learning Works

Phase 2.1 stores field selection outcomes in:
`claude/data/databases/system/m365_ir_field_reliability_history.db`

Each case adds:
- Which field was used
- Whether verification succeeded
- Whether breach was detected
- Reliability score at time of use

Future cases benefit from this learning via the "Historical Success Rate" dimension.

---

### Checking Historical Data

```bash
# View historical learning records
sqlite3 claude/data/databases/system/m365_ir_field_reliability_history.db \
  "SELECT case_id, field_name, verification_successful, breach_detected, reliability_score
   FROM field_reliability_history
   ORDER BY created_at DESC
   LIMIT 10"
```

---

### Common Issues

#### Issue: Historical success rate always 100%

**Symptom**:
```
Historical success: 100%
```

**Cause**: All previous cases using this field succeeded

**Action**: No action needed - this is good! Field is proven reliable.

---

#### Issue: Historical success rate <50%

**Symptom**:
```
Historical success: 40% 🚨
```

**Cause**: This field failed verification in 60% of past cases

**Action**:
1. Check why other cases failed (query historical DB)
2. Consider if this case has similar characteristics
3. May need manual verification instead of auto-verification

---

#### Issue: No historical data available

**Symptom**:
```
Historical success: N/A (no historical data)
```

**Cause**: First time using this field, or historical DB doesn't exist

**Action**: Normal for first case. Future cases will benefit from this case's outcome.

---

## Feature Flags

### Disabling Phase 2.1 (Rollback to Phase 1)

If Phase 2.1 causes issues, you can instantly rollback:

**File**: `claude/tools/m365_ir/auth_verifier.py`

```python
# Near top of file (line ~35)
USE_PHASE_2_1_SCORING = False  # Change to False to disable Phase 2.1
```

**Effect**:
- Disables intelligent field selection
- Falls back to Phase 1 hard-coded logic
- No breaking changes to APIs
- Historical learning disabled but not deleted

**When to Rollback**:
- Phase 2.1 consistently selects wrong fields
- Performance issues (though overhead is only 4ms)
- Debugging requires simpler logic path

---

## Performance Characteristics

### Expected Performance

| Dataset Size | Import Time | Verification Time | Phase 2.1 Overhead |
|--------------|-------------|-------------------|-------------------|
| 5K records | ~0.2s | ~7ms | ~4ms |
| 10K records | ~0.4s | ~10ms | ~5ms |
| 50K records | ~2s | ~15ms | ~7ms |
| 100K records | ~4s | ~20ms | ~10ms |

**Phase 2.1 Overhead**: The additional 4-10ms for intelligent field selection vs Phase 1 hard-coded selection.

---

## Escalation Path

### When to Escalate to SRE

1. **Confidence consistently LOW (<0.5)** across multiple cases
2. **Historical success rate dropping** over time for a field
3. **Wrong field selected** despite HIGH confidence
4. **Performance degradation** beyond expected targets
5. **Historical DB corruption** or access errors

**Contact**: SRE Principal Engineer

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial runbook for Phase 1.2 |
| 2.1 | 2026-01-07 | Added Phase 2.1 intelligent field selection guidance |

---

**End of Runbook**
