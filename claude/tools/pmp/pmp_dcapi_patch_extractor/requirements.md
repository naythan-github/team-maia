# PMP DCAPI Patch Extractor - Requirements Specification

**Project**: PMP Resilient Patch-System Mapping Extractor with Checkpoint/Resume
**Version**: 1.0
**Date**: 2025-11-26
**Author**: SRE Principal Engineer Agent + Patch Manager Plus API Specialist Agent
**Status**: Requirements Complete - Ready for Test Design

---

## Executive Summary

Build production-grade PMP patch-system mapping extractor achieving 95%+ coverage (3,150+ of 3,317 systems) through resilient extraction with checkpoint/resume capability, eliminating token expiry failures and handling transient API errors gracefully. Uses newly discovered DCAPI `/threats/systemreport/patches` endpoint for complete patch inventory per system.

---

## Problem Statement

### Current State
- **0 patch records** in `patches` table (empty)
- **0 patch-system mappings** in `patch_system_mapping` table (empty)
- Cannot answer compliance questions:
  - "Which systems have patch X installed?"
  - "What patches is system Y missing?"
  - "What is our patching coverage for CVE-YYYY-NNNNN?"
- Wrong endpoint attempted (`/api/1.4/patch/allpatches`) resulted in JSON parse errors
- 364K supported patches endpoint would take 8+ hours (mostly irrelevant Linux patches)

### Desired State
- 95%+ system coverage (3,150+ of 3,317 systems)
- Complete patch inventory per system (installed + missing patches)
- Resilient to token expiry (fresh tokens per batch)
- Graceful handling of transient API failures
- Resume capability (continue from last successful page)
- Complete observability (know what failed and why)
- Automated convergence (runs until target met)

### Discovery: DCAPI Endpoint
- **Endpoint**: `/dcapi/threats/systemreport/patches`
- **Data**: System-patch mappings with installation status per system
- **Pagination**: 111 pages (30 systems/page)
- **Extraction time**: ~5 minutes per 50-page batch (~13 batches total)
- **Advantage**: Single endpoint vs 5,383 separate API calls (99.98% efficiency gain)

---

## Functional Requirements

### FR-1: Checkpoint-Based Extraction

**Description**: Extract patch-system mappings in batches with persistent checkpoint tracking

**Acceptance Criteria**:
- ✅ Extract in 50-page batches (250 systems per batch)
- ✅ Track last successful page in database checkpoint table
- ✅ Resume from `last_page + 1` on subsequent runs
- ✅ Auto-detect completion (≥95% coverage) and exit
- ✅ Page-level progress tracking with batch-level commits (every 10 pages)

**Example Usage**:
```bash
# Run 1: Extracts pages 1-50 (250 systems), saves checkpoint at page 50
python3 pmp_dcapi_patch_extractor.py

# Run 2: Resumes from page 51, extracts 51-100 (500 systems total), saves checkpoint at page 100
python3 pmp_dcapi_patch_extractor.py

# Run 13: Resumes from page 651, extracts 651-664 (3,317 systems total), detects 95%+ coverage, exits
python3 pmp_dcapi_patch_extractor.py
```

**Edge Cases**:
- First run (no checkpoint): Start from page 1
- Checkpoint corruption: Detect and reset to safe state
- Mid-batch interruption: Resume from last commit (max 10 pages lost = 50 systems)

---

### FR-2: Token Management

**Description**: Eliminate token expiry failures through proactive token refresh

**Acceptance Criteria**:
- ✅ Fresh OAuth token at start of each batch run
- ✅ Check token age before EACH page request
- ✅ Proactive refresh if token age > 80% of TTL
- ✅ Immediate refresh + retry on 401 (Unauthorized) response
- ✅ Token age logging for TTL calibration

**Token Lifecycle**:
```python
# Batch start (every 50 pages)
1. Get fresh OAuth token from PMPOAuthManager
2. Record token_created_at timestamp

# Before each page request (664 times total, 50 per batch)
3. Check: (current_time - token_created_at) > (TTL * 0.8)?
4. If YES: Refresh token proactively
5. If NO: Proceed with request

# On 401 error
6. Refresh token immediately
7. Retry same page with new token
```

**Edge Cases**:
- Token refresh fails: Retry 3 times, then abort batch (log error, exit gracefully)
- Token TTL unknown: Default to 45-second threshold (conservative estimate)
- Multiple 401s: After 3 consecutive 401s, abort (auth configuration issue)

---

### FR-3: Intelligent Error Handling

**Description**: Classify errors and apply appropriate retry/skip logic

**Acceptance Criteria**:
- ✅ **401 (Unauthorized)**: Refresh token → retry immediately (no backoff)
- ✅ **429 (Rate Limited)**: Honor Retry-After header → exponential backoff → retry (max 3 attempts)
- ✅ **5xx (Server Error)**: Exponential backoff (1s, 2s, 4s) → retry (max 3 attempts)
- ✅ **Network timeout**: Exponential backoff (1s, 2s, 4s) → retry (max 3 attempts)
- ✅ **JSON parse error**: Log raw response → skip page immediately (data corruption, no retry)
- ✅ **After 3 failed attempts**: Skip page, log error details, continue extraction
- ✅ **No abort threshold**: Continue extraction even with multiple page failures

**Error Classification Logic**:
```python
def handle_error(error, page_num, attempt):
    if error.type == "401_unauthorized":
        refresh_token()
        return RETRY_IMMEDIATELY

    elif error.type == "429_rate_limit":
        wait_time = response.headers.get("Retry-After", 2 ** attempt)
        time.sleep(wait_time)
        return RETRY if attempt < 3 else SKIP

    elif error.type in ["500_server_error", "503_unavailable", "network_timeout"]:
        time.sleep(2 ** attempt)  # 1s, 2s, 4s
        return RETRY if attempt < 3 else SKIP

    elif error.type == "json_parse_error":
        log_raw_response(response.text)
        return SKIP  # Data corruption, no retry

    else:  # Unknown error
        return SKIP  # Fail gracefully
```

**Edge Cases**:
- Mixed errors on same page: Each attempt classified independently
- Cascading 5xx errors: No abort - skip failed pages, continue
- Empty response (0 bytes): Treat as JSON parse error → skip

---

### FR-4: Coverage Target & Convergence

**Description**: Extract until 95% coverage achieved, then auto-stop

**Acceptance Criteria**:
- ✅ Target: ≥3,150 unique systems (95% of 3,317)
- ✅ Pre-run check: Query current coverage from database
- ✅ If coverage ≥95%: Log completion, exit with status 0
- ✅ If coverage <95%: Extract next 50 pages, save checkpoint, exit with status 0
- ✅ Gap analysis: Track which pages failed (for manual investigation)

**Coverage Calculation**:
```sql
SELECT COUNT(DISTINCT resource_id) FROM patch_system_mapping;
-- If result >= 3150: Target met
-- If result < 3150: Continue extraction
```

**Convergence Timeline** (with 6-hour cron):
- Run 1 (T+0h): Pages 1-50 → 7.5% coverage (250/3,317 systems)
- Run 2 (T+6h): Pages 51-100 → 15.1% coverage (500/3,317 systems)
- Run 7 (T+36h): Pages 301-350 → 52.6% coverage (1,750/3,317 systems)
- Run 13 (T+72h): Pages 651-664 → 100% coverage (3,317/3,317 systems) → AUTO-STOP ✅

**Edge Cases**:
- Coverage decreases between runs: Log warning, continue (possible data deletion in PMP)
- Coverage stuck at 94%: Continue extraction, generate gap report after page 664

---

### FR-5: Data Model - Patch-System Mappings

**Description**: Store complete patch inventory per system in `patch_system_mapping` table

**Acceptance Criteria**:
- ✅ **Unique constraint**: (resource_id, patch_id) to prevent duplicates
- ✅ **Idempotent inserts**: INSERT OR REPLACE for re-runs
- ✅ **Complete fields**: patch_id, patchname, severity, patch_status, bulletinid, vendor_name, installed_time, resource_id
- ✅ **Batch commits**: Commit every 10 pages (50 systems) to minimize I/O
- ✅ **Transaction safety**: Rollback on error during batch commit

**DCAPI Response Structure**:
```json
{
  "systemreport": [
    {
      "resource_id": "10001",
      "resource_name": "SERVER01",
      "patches": [
        {
          "patch_id": "10044",
          "patchname": "vcredist_KB2538242_x86.exe",
          "severity": "Important",
          "patch_status": "Installed",
          "bulletinid": "MS11-025",
          "vendor_name": "Microsoft",
          "installed_time": "1634567890000"
        },
        {
          "patch_id": "10045",
          "patchname": "Windows10.0-KB5005565-x64.msu",
          "severity": "Critical",
          "patch_status": "Missing",
          "bulletinid": "MS21-008",
          "vendor_name": "Microsoft",
          "installed_time": null
        }
      ]
    }
  ]
}
```

**Database Insert Logic**:
```python
def insert_patch_mappings(system_data):
    """
    Insert all patch-system mappings for a single system

    Args:
        system_data: Dict with resource_id and patches list
    """
    resource_id = system_data['resource_id']
    patches = system_data.get('patches', [])

    for patch in patches:
        cursor.execute("""
            INSERT OR REPLACE INTO patch_system_mapping (
                resource_id, patch_id, patchname, severity,
                patch_status, bulletinid, vendor_name, installed_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resource_id,
            patch['patch_id'],
            patch.get('patchname'),
            patch.get('severity'),
            patch.get('patch_status'),
            patch.get('bulletinid'),
            patch.get('vendor_name'),
            patch.get('installed_time')
        ))
```

**Edge Cases**:
- System with 0 patches: Log warning, skip (unusual but valid)
- System with >500 patches: Normal for servers, no special handling
- Duplicate patches in response: INSERT OR REPLACE handles this
- NULL fields: Allow NULL for optional fields (installed_time, bulletinid)

---

### FR-6: Observability & Logging

**Description**: Comprehensive structured logging for debugging and monitoring

**Acceptance Criteria**:
- ✅ **JSON structured logs** (machine-readable)
- ✅ **Progress events**: Every page (page num, systems count, patches count, % complete, ETA)
- ✅ **Error events**: Every failure (HTTP status, error message, page num, attempt count, raw response sample)
- ✅ **Token events**: Every refresh (timestamp, reason, success/failure)
- ✅ **Checkpoint events**: Every commit (last_page, systems_extracted, patches_extracted, coverage_pct)
- ✅ **Summary events**: Batch start, batch complete, target met

**Log Schema** (JSON format):
```json
{
  "timestamp": "2025-11-26T17:30:00.123Z",
  "level": "INFO",
  "event_type": "extraction_progress",
  "snapshot_id": 1,
  "page": 50,
  "systems_extracted": 250,
  "patches_extracted": 12500,
  "total_systems": 3317,
  "progress_pct": 7.5,
  "errors_total": 2,
  "eta_minutes": 5
}

{
  "timestamp": "2025-11-26T17:30:15.456Z",
  "level": "ERROR",
  "event_type": "page_extraction_failed",
  "snapshot_id": 1,
  "page": 51,
  "attempt": 3,
  "http_status": 503,
  "error_message": "Service Unavailable",
  "response_sample": "<html><body>503 Service Temporarily Unavailable</body></html>",
  "action": "skip_page"
}
```

**Log Levels**:
- **DEBUG**: Token checks, retry logic decisions
- **INFO**: Progress, checkpoints, batch completion
- **WARNING**: Skip decisions, approaching coverage target
- **ERROR**: Failed pages after retries, token refresh failures
- **CRITICAL**: Abort conditions (e.g., 3 consecutive 401s)

**Edge Cases**:
- Response too large (>10KB): Truncate to first 1KB for logging
- PII in responses: Sanitize before logging (redact email, IP addresses)

---

### FR-7: Optional Slack Notifications

**Description**: Configurable Slack webhook notifications for stakeholder visibility

**Acceptance Criteria**:
- ✅ **Disabled by default** (no env var = no Slack calls)
- ✅ **Enable via env var**: `SLACK_WEBHOOK_URL=https://hooks.slack.com/...`
- ✅ **Batch start**: "🔄 PMP DCAPI extraction started (target: 3,317 systems)"
- ✅ **Progress milestones**: 25%, 50%, 75% (not every page)
- ✅ **Batch complete**: "✅ Batch complete: 250 systems extracted (7.5% total coverage, 12,500 patches)"
- ✅ **Target met**: "🎉 Extraction complete: 3,150/3,317 systems (95.0%)"
- ✅ **Errors**: "⚠️ Page 51 failed after 3 attempts (503 Server Error)"

**Slack Message Format** (Markdown):
```markdown
**PMP DCAPI Extraction Progress**
- Page: 50/664
- Systems: 250/3,317 (7.5%)
- Patches: 12,500
- Errors: 2 (pages 15, 23)
- ETA: 5 minutes
```

**Error Handling**:
- Slack webhook fails: Log warning, continue extraction (don't block on notifications)
- Rate limiting on Slack: Batch notifications (max 1 per minute)

**Edge Cases**:
- Invalid webhook URL: Validate at startup, disable notifications if invalid
- Webhook returns 404: Disable notifications for this run, log warning

---

## Non-Functional Requirements

### NFR-1: Performance

**Acceptance Criteria**:
- ✅ Batch extraction time: <15 minutes per 50-page batch
- ✅ Throughput: ≥10 systems/second (API rate limit compliant)
- ✅ Rate limiting: 0.25s delay between pages (4 pages/sec)
- ✅ Memory usage: <100 MB during extraction (streaming, not buffering)
- ✅ Database writes: Batch commits (every 10 pages) to minimize I/O

**Performance Targets**:
- 50 pages × 30 systems/page × 0.25s delay = 12.5 seconds minimum + API latency (~2-5 minutes total per batch)
- 13 batches × 5 minutes = ~65 minutes total extraction time (all batches)

---

### NFR-2: Reliability

**Acceptance Criteria**:
- ✅ **Target coverage**: 95% success rate (≥3,150/3,317 systems)
- ✅ **Token expiry**: 0% failure rate due to token expiry
- ✅ **Transient errors**: 70% recovery rate via retry logic
- ✅ **Checkpoint recovery**: 100% success rate resuming from checkpoint
- ✅ **Data integrity**: 100% idempotent (safe to re-run, no duplicates)

**Reliability Patterns**:
- Exponential backoff for transient failures
- Circuit breaker for permanent failures (skip after 3 attempts)
- Graceful degradation (skip vs abort)
- Idempotent operations (INSERT OR REPLACE)

---

### NFR-3: Security

**Acceptance Criteria**:
- ✅ OAuth tokens via PMPOAuthManager (secure storage in macOS Keychain)
- ✅ No tokens in logs (only "token refreshed" events)
- ✅ Database file permissions: 600 (owner read/write only)
- ✅ Sanitize PII from error logs (emails, IPs)

---

### NFR-4: Maintainability

**Acceptance Criteria**:
- ✅ Single responsibility: Extractor does extraction only (no post-processing)
- ✅ Modular design: Token mgmt, error handling, checkpoint logic separated
- ✅ Type hints: All functions typed (Python 3.9+ typing)
- ✅ Docstrings: All public methods documented
- ✅ Test coverage: ≥80% code coverage (unit + integration tests)

---

### NFR-5: Operability

**Acceptance Criteria**:
- ✅ **CLI interface**: Simple invocation (`python3 pmp_dcapi_patch_extractor.py`)
- ✅ **Exit codes**: 0=success, 1=fatal error, 2=partial completion (gap analysis needed)
- ✅ **Cron-friendly**: Runs unattended, logs to file, auto-stops on completion
- ✅ **Health check**: `--status` flag shows current coverage without extracting
- ✅ **Reset option**: `--reset` flag clears checkpoint (start from page 1)

**CLI Usage**:
```bash
# Standard extraction (resume from checkpoint)
python3 pmp_dcapi_patch_extractor.py

# Check current coverage (no extraction)
python3 pmp_dcapi_patch_extractor.py --status

# Reset checkpoint and start from page 1
python3 pmp_dcapi_patch_extractor.py --reset

# Enable Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/... python3 pmp_dcapi_patch_extractor.py
```

---

## Integration Points

### Upstream Dependencies
- **PMPOAuthManager** (claude/tools/pmp/pmp_oauth_manager.py): OAuth token management
- **PMP DCAPI** (https://patch.manageengine.com.au/dcapi/threats/systemreport/patches): Patch-system mapping endpoint
- **SQLite Database** (~/.maia/databases/intelligence/pmp_config.db): Data storage
- **Existing Database Schema**: `patch_system_mapping` table (already exists from Phase 188)

### Downstream Consumers
- **Patch Compliance Queries**: Query patch_system_mapping for installed/missing patches per system
- **CVE Coverage Analysis**: Query by bulletinid to find affected systems
- **Patch Dashboard**: Query by severity to prioritize critical/high patches
- **MSP Intelligence**: Per-organization patch coverage analysis

### Optional Integrations (via hooks)
- Post-extraction analysis scripts (triggered by `POST_EXTRACTION_HOOK` env var)
- Grafana dashboards (future enhancement)
- ServiceNow integration (future enhancement)

---

## Operational Requirements

### Deployment
- **Location**: claude/tools/pmp/pmp_dcapi_patch_extractor.py
- **Cron Schedule**: Every 6 hours until 95% coverage achieved
- **Log Location**: /tmp/pmp_dcapi_extraction.log (rotated daily)
- **Database**: ~/.maia/databases/intelligence/pmp_config.db

**Cron Configuration**:
```cron
# PMP DCAPI Resilient Extraction (every 6 hours)
0 */6 * * * cd /Users/YOUR_USERNAME/git/maia && python3 claude/tools/pmp/pmp_dcapi_patch_extractor.py >> /tmp/pmp_dcapi_extraction.log 2>&1
```

### Monitoring
- **Logs**: Tail /tmp/pmp_dcapi_extraction.log for real-time progress
- **Database queries**: Check coverage via SQL
- **Slack notifications**: Real-time progress updates (if configured)

### Alerting
- **Coverage stuck**: If <95% after 72 hours, manual investigation needed
- **Multiple 401s**: Auth configuration issue, check PMP OAuth credentials
- **High error rate**: If >20% page failures, check PMP API health

---

## Database Schema

### Checkpoint Table (reuse from Phase 192)

```sql
CREATE TABLE IF NOT EXISTS dcapi_extraction_checkpoints (
    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    last_page INTEGER NOT NULL,
    systems_extracted INTEGER NOT NULL,
    patches_extracted INTEGER NOT NULL,
    coverage_pct REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(snapshot_id)
);

CREATE TABLE IF NOT EXISTS dcapi_extraction_gaps (
    gap_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    page_num INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    response_sample TEXT,
    attempts INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(snapshot_id, page_num)
);

CREATE INDEX IF NOT EXISTS idx_dcapi_checkpoints_snapshot ON dcapi_extraction_checkpoints(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_dcapi_gaps_snapshot ON dcapi_extraction_gaps(snapshot_id);
```

### Data Table (existing from Phase 188)

```sql
-- Already exists from Phase 188, no changes needed
CREATE TABLE IF NOT EXISTS patch_system_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id TEXT NOT NULL,
    patch_id TEXT NOT NULL,
    patchname TEXT,
    severity TEXT,
    patch_status TEXT,
    bulletinid TEXT,
    vendor_name TEXT,
    installed_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource_id, patch_id)
);

CREATE INDEX IF NOT EXISTS idx_psm_resource ON patch_system_mapping(resource_id);
CREATE INDEX IF NOT EXISTS idx_psm_patch ON patch_system_mapping(patch_id);
CREATE INDEX IF NOT EXISTS idx_psm_status ON patch_system_mapping(patch_status);
CREATE INDEX IF NOT EXISTS idx_psm_severity ON patch_system_mapping(severity);
```

---

## Success Metrics

### Coverage Metrics
- **Target**: ≥3,150 unique systems (95% of 3,317)
- **Stretch goal**: ≥3,250 unique systems (98%)
- **Timeline**: Achieve target within 72 hours of initial run

### Reliability Metrics
- **Token expiry failures**: 0 per extraction (leverage Phase 192 success)
- **Transient error recovery**: ≥70% success rate via retry logic
- **Checkpoint recovery**: 100% success rate resuming after interruption

### Operational Metrics
- **Manual intervention**: 0 required (fully automated convergence)
- **Data quality**: 100% idempotent (no duplicate mappings)
- **Observability**: 100% error attribution (know why every page failed)

### Data Quality Metrics
- **Patch count per system**: 10-500 patches (typical range)
- **Patch status distribution**: ~80% Installed, ~20% Missing (typical)
- **Severity distribution**: ~30% Critical, ~40% Important, ~30% Moderate/Low

---

## Example Scenarios

### Scenario 1: Successful Multi-Run Extraction

**Timeline**:
1. **T+0h (Run 1)**:
   - Start: No checkpoint, begin at page 1
   - Extract: Pages 1-50 (250 systems, ~12,500 patches)
   - Errors: Pages 15, 23 (network timeout, recovered via retry)
   - Checkpoint: Save last_page=50, coverage=7.5%
   - Exit: Status 0 (success)

2. **T+6h (Run 2)**:
   - Start: Load checkpoint (last_page=50)
   - Resume: Page 51
   - Extract: Pages 51-100 (500 systems total, ~25,000 patches)
   - Errors: Page 78 (503 error, skipped after 3 retries)
   - Checkpoint: Save last_page=100, coverage=15.1%
   - Exit: Status 0 (success)

3. **T+72h (Run 13)**:
   - Start: Load checkpoint (last_page=650)
   - Resume: Page 651
   - Extract: Pages 651-664 (3,317 systems total, ~165,850 patches)
   - Errors: Pages 655, 660 (JSON parse errors, skipped)
   - Coverage check: 3,250/3,317 = 98.0% ✅ TARGET MET
   - Gap report: Pages 15 (recovered), 23 (recovered), 78 (skipped), 655 (skipped), 660 (skipped)
   - Exit: Status 0 (success, auto-stop)

**Result**: 98.0% coverage achieved in 72 hours, 3 gaps identified (78, 655, 660)

---

### Scenario 2: Token Expiry Prevention

**Situation**: Batch run taking longer than expected due to slow API responses

**Extractor behavior**:
1. Page 1: Fresh token obtained (token_age=0s)
2. Pages 2-10: Token age increasing (5s, 10s, 15s...)
3. Page 25 (token_age=45s, 80% of estimated 60s TTL):
   - **Proactive refresh triggered**
   - New token obtained
   - Reset token_age=0s
4. Pages 26-50: Continue with fresh token
5. Batch completes without 401 errors

**Result**: Token expiry prevented through proactive refresh

---

### Scenario 3: Transient API Failure Recovery

**Situation**: PMP DCAPI experiencing intermittent 503 errors

**Page 65 extraction attempts**:
1. **Attempt 1**: 503 Server Error → Wait 1s → Retry
2. **Attempt 2**: 503 Server Error → Wait 2s → Retry
3. **Attempt 3**: 200 OK → Success (5 systems, ~250 patches extracted)

**Result**: Transient error recovered via exponential backoff, no data loss

---

### Scenario 4: Permanent API Failure Graceful Degradation

**Situation**: Page 78 has corrupted data, API returns HTML error page

**Page 78 extraction attempts**:
1. **Attempt 1**: JSON parse error (HTML response) → Wait 1s → Retry
2. **Attempt 2**: JSON parse error → Wait 2s → Retry
3. **Attempt 3**: JSON parse error → Log raw response → Skip page
4. Continue to page 79 (no abort)

**Gap report entry**:
```json
{
  "page": 78,
  "error_type": "json_parse_error",
  "attempts": 3,
  "response_sample": "<html><body>Internal Server Error</body></html>"
}
```

**Result**: Permanent failure handled gracefully, 5 systems lost on page 78, remaining 3,312 systems still extracted (99.8% of recoverable data)

---

## Out of Scope

### Explicitly NOT Included (v1.0)
- ❌ Grafana dashboard integration (future enhancement)
- ❌ Email notifications (use Slack or logs)
- ❌ Per-system patch analysis (use separate analysis tools)
- ❌ Automatic gap remediation (requires manual API investigation)
- ❌ Parallel extraction (multiple batches concurrently)
- ❌ Real-time progress API endpoint (logs only)
- ❌ Patch installation automation (read-only extraction)

### Deferred to Future Versions
- v1.1: Grafana dashboard integration
- v1.2: Intelligent gap remediation (query specific systems via on-demand API)
- v1.3: Delta extraction (query only changed systems since last run)
- v2.0: Patch analysis and risk scoring (CVE correlation, CVSS scoring)

---

## Acceptance Criteria Summary

**Minimum Viable Product (v1.0)**:
- [ ] Achieves ≥95% coverage (3,150+ systems) within 72 hours
- [ ] Zero token expiry failures
- [ ] Checkpoint/resume works correctly (tested with manual interruption)
- [ ] Retry logic recovers ≥70% of transient failures
- [ ] Gap report accurately identifies failed pages
- [ ] Structured JSON logs for all events
- [ ] Cron-compatible (runs unattended, auto-stops on target)
- [ ] All test cases pass (unit + integration)

**Production Ready Checklist**:
- [ ] Test suite: ≥80% code coverage
- [ ] Documentation: README with usage examples
- [ ] Security: No credentials in logs
- [ ] Observability: All failure modes logged
- [ ] Operability: CLI interface tested
- [ ] Integration: Works with existing PMP OAuth manager
- [ ] Validation: Manually verified with production DCAPI

---

## Comparison with Phase 192 (System Inventory Extractor)

| Metric | Phase 192 (System Inventory) | This Project (DCAPI Patches) |
|--------|------------------------------|------------------------------|
| **Endpoint** | `/api/1.4/patch/scandetails` | `/dcapi/threats/systemreport/patches` |
| **Total Systems** | 3,362 | 3,317 |
| **Total Pages** | 135 | 664 |
| **Systems/Page** | 25 | 5 |
| **Batch Size** | 50 pages | 50 pages |
| **Batches to Complete** | 3 | 13 |
| **Data Model** | `systems` table | `patch_system_mapping` table |
| **Data Volume** | ~1 row per system | ~50 rows per system (avg) |
| **Expected Total Rows** | 3,362 | ~165,000 |
| **Convergence Time** | 12 hours | 72 hours |

**Key Learnings from Phase 192**:
- ✅ Checkpoint/resume architecture proven (99.1% coverage achieved)
- ✅ Token management strategy validated (0% token expiry failures)
- ✅ Error handling patterns successful (70%+ transient recovery)
- ✅ Observability approach effective (JSON logs + Slack)

**Adaptations for DCAPI**:
- ✅ Longer convergence timeline (13 batches vs 3)
- ✅ Lower systems/page (5 vs 25) but same batch size (50 pages)
- ✅ Higher data volume per system (~50 patch records vs 1 system record)
- ✅ Separate checkpoint tables to avoid conflicts

---

## Review & Approval

**Requirements Discovery Date**: 2025-11-26
**Reviewed By**: User (approved recommendations)
**Next Phase**: Test Design (Phase 3)

**Sign-off**:
- ✅ SRE Principal Engineer Agent: Requirements complete, ready for test design
- ✅ User: Approved "proceed with your recommendations"

---

**Status**: ✅ REQUIREMENTS COMPLETE - READY FOR PHASE 3 (TEST DESIGN)
