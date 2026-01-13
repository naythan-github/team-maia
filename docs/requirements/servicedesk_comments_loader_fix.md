# ServiceDesk Comments Loader Fix - Requirements

**Created:** 2026-01-12
**Agent:** Data Analyst
**Assignee:** SRE Principal Engineer (TDD)
**Priority:** High
**Issue:** Comments API import failing due to transaction mode conflict

---

## Problem Statement

The comments loader at `claude/tools/integrations/otc/load_to_postgres.py:95-230` fails to load new comments due to improper transaction handling.

### Current Behavior (Broken)

```python
# Uses manual INSERT + catch IntegrityError + UPDATE pattern
insert_sql = "INSERT INTO servicedesk.comments (...) VALUES (...)"
update_sql = "UPDATE servicedesk.comments SET ... WHERE comment_id = ?"

for values in batch:
    try:
        cursor.execute(insert_sql, values)
        self.stats['inserted'] += 1
    except psycopg2.IntegrityError:
        cursor.execute(update_sql, ...)  # FAILS: transaction aborted
        self.stats['updated'] += 1
```

**Failure mode:**
- Connection uses `autocommit = False` (transaction mode)
- First INSERT hits duplicate key → transaction aborted
- All subsequent operations fail with "current transaction is aborted"
- Result: 0 of 7,649 comments loaded

### Expected Behavior (Fixed)

Use ON CONFLICT DO UPDATE (upsert) like tickets and timesheets loaders:

```python
upsert_sql = """
    INSERT INTO servicedesk.comments (
        comment_id, ticket_id, comment_text, user_id, user_name,
        owner_type, created_time, visible_to_customer, comment_type, team
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (comment_id) DO UPDATE SET
        comment_text = EXCLUDED.comment_text,
        visible_to_customer = EXCLUDED.visible_to_customer,
        comment_type = EXCLUDED.comment_type,
        team = EXCLUDED.team
"""
```

---

## Requirements

### Functional Requirements

1. **Upsert Logic**: Replace manual INSERT/UPDATE with ON CONFLICT DO UPDATE
2. **Batch Processing**: Use `execute_batch()` for performance (like timesheets/tickets)
3. **Stats Tracking**: Track inserted count (new records added)
4. **Error Handling**: Individual record errors should not abort entire batch
5. **API Compatibility**: Continue using OTCClient.fetch_comments() (no changes)

### Non-Functional Requirements

1. **Performance**: Match or exceed current tickets/timesheets loader speed
2. **Idempotency**: Re-running import should not create duplicates
3. **Backward Compatibility**: Same CLI interface and return structure

### Data Requirements

- **Primary Key**: `comment_id` (existing constraint)
- **Updatable Fields**: `comment_text`, `visible_to_customer`, `comment_type`, `team`
- **Immutable Fields**: `comment_id`, `ticket_id`, `user_id`, `user_name`, `owner_type`, `created_time`

---

## Acceptance Criteria

### 1. Unit Tests (TDD)

```python
# tests/test_otc_comments_loader.py

def test_comments_upsert_new_records():
    """Insert new comments successfully"""
    # Given: Empty comments table
    # When: Load 100 new comments
    # Then: 100 inserted, 0 updated, 0 errors

def test_comments_upsert_duplicate_records():
    """Update existing comments without error"""
    # Given: 100 comments already in DB
    # When: Load same 100 comments with updated text
    # Then: 0 inserted, 100 updated, 0 errors

def test_comments_upsert_mixed_batch():
    """Handle mix of new and existing comments"""
    # Given: 50 comments in DB
    # When: Load 100 comments (50 duplicates, 50 new)
    # Then: 50 inserted, 50 updated, 0 errors

def test_comments_upsert_invalid_record():
    """Skip invalid records without aborting batch"""
    # Given: Batch with 1 invalid record
    # When: Load batch with malformed data
    # Then: Valid records processed, errors tracked

def test_comments_batch_performance():
    """Process large batches efficiently"""
    # Given: 10,000 comments
    # When: Load with batch_size=500
    # Then: Complete in <30s, use execute_batch
```

### 2. Integration Tests

```python
def test_comments_api_to_postgres_full_flow():
    """End-to-end API fetch and load"""
    # Given: OTC API credentials configured
    # When: Run load_comments()
    # Then: API data in PostgreSQL, stats accurate

def test_comments_idempotency():
    """Re-running import doesn't create duplicates"""
    # Given: Import run once
    # When: Run same import again
    # Then: Same record count, no duplicates
```

### 3. Production Validation

After deployment:
```bash
# Run import
python3 -m claude.tools.integrations.otc.load_to_postgres comments

# Verify results
psql -h localhost -U servicedesk_user -d servicedesk \
  -c "SELECT COUNT(*) FROM servicedesk.comments WHERE created_time >= NOW() - INTERVAL '10 days'"

# Expected: ~7,649 comments (last 10 days from API)
# Current DB has 6,321 from Jan 2-8
# Missing 1,328 from Jan 9-12 should now be loaded
```

---

## Implementation Reference

### Working Example: Timesheets Loader

See `load_to_postgres.py:490-503` for upsert pattern:

```python
upsert_sql = """
    INSERT INTO servicedesk.timesheets (...)
    VALUES (%s, %s, ...)
    ON CONFLICT ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID")
    DO UPDATE SET
        "TS-Hours" = EXCLUDED."TS-Hours",
        ...
"""

execute_batch(cursor, upsert_sql, batch, page_size=100)
```

### Helper Method: `_upsert_batch_fast()`

See `load_to_postgres.py:701-729` - already exists, reuse for comments.

---

## Database Schema

```sql
-- Primary key constraint (already exists)
ALTER TABLE servicedesk.comments
ADD CONSTRAINT comments_pkey PRIMARY KEY (comment_id);

-- No schema changes required
```

---

## Current Impact

- **Missing Data**: 1,328 new comments from Jan 9-12, 2026
- **API Fetches**: 7,649 comments (last 10 days)
- **DB Current**: 317,601 comments (through Jan 8)
- **Expected After Fix**: 318,929 comments (317,601 + 1,328)

---

## TDD Workflow

1. **Write failing tests** - All 5 unit tests should fail
2. **Implement fix** - Replace INSERT/UPDATE with upsert in `load_comments()`
3. **Tests pass** - All unit tests green
4. **Integration test** - Full API-to-PostgreSQL flow
5. **Manual validation** - Run production import, verify counts
6. **Documentation** - Update otc_database_reference.md if needed

---

## Files to Modify

- **Main**: `claude/tools/integrations/otc/load_to_postgres.py` (lines 95-230)
- **Tests**: `tests/test_otc_comments_loader.py` (new file)

---

## Questions for SRE

1. Should we use the existing `_upsert_batch_fast()` helper or create comments-specific logic?
2. Do we need to add ETL metadata recording for comments (like tickets/timesheets)?
3. Should we add a `--force` flag to reload all 10 days even if duplicates exist?

---

## Success Metrics

- ✅ All unit tests pass
- ✅ Integration test passes
- ✅ Production import loads 1,328 missing comments
- ✅ No transaction abort errors in logs
- ✅ Performance: <10s for 7,649 comments

---

**Ready for TDD implementation by SRE Principal Engineer**
