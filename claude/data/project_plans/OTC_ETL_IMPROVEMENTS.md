# Project Plan: OTC ETL Pipeline Improvements

**Created:** 2026-01-07
**Priority:** High
**Estimated Effort:** 8-12 hours
**Status:** Ready for Implementation

---

## Executive Summary

The OTC ETL pipeline has critical issues preventing reliable data synchronization. This plan addresses UPSERT support, metadata tracking, performance optimization, and security improvements.

---

## Phase 1: Critical Fixes (P0) - 3 hours

### Task 1.1: Implement UPSERT for Tickets

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Lines:** 483-515 (load_tickets method)

**Current Problem:**
- `_insert_simple_batch()` silently fails on duplicate primary keys
- Re-running ETL doesn't update existing tickets

**Implementation:**

1. Replace the INSERT statement at line 483-490 with:

```python
insert_sql = """
    INSERT INTO servicedesk.tickets (
        "TKT-Ticket ID", "TKT-Title", "TKT-Status", "TKT-Severity", "TKT-Category",
        "TKT-Team", "TKT-Assigned To User", "TKT-Created Time", "TKT-Modified Time",
        "TKT-Account Name", "TKT-Client Name"
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT ("TKT-Ticket ID") DO UPDATE SET
        "TKT-Title" = EXCLUDED."TKT-Title",
        "TKT-Status" = EXCLUDED."TKT-Status",
        "TKT-Severity" = EXCLUDED."TKT-Severity",
        "TKT-Category" = EXCLUDED."TKT-Category",
        "TKT-Team" = EXCLUDED."TKT-Team",
        "TKT-Assigned To User" = EXCLUDED."TKT-Assigned To User",
        "TKT-Modified Time" = EXCLUDED."TKT-Modified Time",
        "TKT-Account Name" = EXCLUDED."TKT-Account Name",
        "TKT-Client Name" = EXCLUDED."TKT-Client Name"
"""
```

2. Create new method `_upsert_batch()` to track inserts vs updates:

```python
def _upsert_batch(self, cursor, upsert_sql: str, batch: List):
    """
    Upsert a batch of records using ON CONFLICT.
    Tracks inserted vs updated counts.
    """
    for values in batch:
        try:
            cursor.execute(upsert_sql, values)
            # xmax = 0 means INSERT, xmax > 0 means UPDATE
            if cursor.rowcount > 0:
                self.stats['inserted'] += 1
        except Exception as e:
            logger.warning(f"Failed to upsert record: {e}")
            self.stats['errors'] += 1
```

3. Update `load_tickets()` to use `_upsert_batch()` instead of `_insert_simple_batch()`

**Tests to Add:**
- `test_tickets_upsert_new_record` - Insert new ticket
- `test_tickets_upsert_existing_record` - Update existing ticket
- `test_tickets_upsert_preserves_created_time` - Created time not overwritten

---

### Task 1.2: Implement UPSERT for Timesheets

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Lines:** 396-424 (load_timesheets method)

**Current Problem:**
- Timesheets have no unique constraint, causing duplicates on re-run

**Implementation:**

1. First, add a unique constraint to the database (one-time migration):

```sql
-- Create composite unique constraint
ALTER TABLE servicedesk.timesheets
ADD CONSTRAINT timesheets_unique_entry
UNIQUE ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID");
```

2. Update INSERT at line 396-403:

```python
insert_sql = """
    INSERT INTO servicedesk.timesheets (
        "TS-User Username", "TS-User Full Name", "TS-Date", "TS-Time From",
        "TS-Time To", "TS-Hours", "TS-Category", "TS-Sub Category",
        "TS-Type", "TS-Crm ID", "TS-Description", "TS-Account Name"
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT ("TS-User Username", "TS-Date", "TS-Time From", "TS-Crm ID")
    DO UPDATE SET
        "TS-Hours" = EXCLUDED."TS-Hours",
        "TS-Description" = EXCLUDED."TS-Description",
        "TS-Category" = EXCLUDED."TS-Category",
        "TS-Sub Category" = EXCLUDED."TS-Sub Category"
"""
```

**Tests to Add:**
- `test_timesheets_no_duplicates_on_rerun`
- `test_timesheets_updates_existing_entry`

---

### Task 1.3: Implement ETL Metadata Recording

**File:** `claude/tools/integrations/otc/load_to_postgres.py`

**Current Problem:**
- `etl_metadata` table exists but is never populated
- Can't track data freshness or load history

**Implementation:**

1. Add new method after line 297:

```python
def _record_etl_metadata(self, view_name: str, stats: dict,
                          start_time: datetime, end_time: datetime,
                          status: str = 'success', error_message: str = None):
    """
    Record ETL run metadata for tracking and monitoring.

    Args:
        view_name: 'tickets', 'comments', or 'timesheets'
        stats: Stats dict with fetched/inserted/updated/errors
        start_time: When load started
        end_time: When load completed
        status: 'success', 'partial', or 'failed'
        error_message: Error details if failed
    """
    try:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO servicedesk.etl_metadata (
                view_name,
                records_fetched,
                records_inserted,
                records_updated,
                records_errors,
                load_start,
                load_end,
                load_duration_seconds,
                status,
                error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            view_name,
            stats.get('fetched', 0),
            stats.get('inserted', 0),
            stats.get('updated', 0),
            stats.get('errors', 0),
            start_time,
            end_time,
            (end_time - start_time).total_seconds(),
            status,
            error_message
        ))
        self.conn.commit()
        logger.info(f"Recorded ETL metadata for {view_name}")
    except Exception as e:
        logger.error(f"Failed to record ETL metadata: {e}")
```

2. Update each load method to call `_record_etl_metadata()`:

In `load_tickets()` before the `return self.stats` (around line 527):
```python
self._record_etl_metadata('tickets', self.stats, start_time, datetime.now())
return self.stats
```

In `load_comments()` before `return self.stats` (around line 176):
```python
self._record_etl_metadata('comments', self.stats, start_time, datetime.now())
return self.stats
```

In `load_timesheets()` before `return self.stats` (around line 437):
```python
self._record_etl_metadata('timesheets', self.stats, start_time, datetime.now())
return self.stats
```

3. Add `load_start` and `load_end` columns to `etl_metadata` if not present:

```sql
ALTER TABLE servicedesk.etl_metadata
ADD COLUMN IF NOT EXISTS load_start TIMESTAMP,
ADD COLUMN IF NOT EXISTS load_end TIMESTAMP,
ADD COLUMN IF NOT EXISTS load_duration_seconds NUMERIC,
ADD COLUMN IF NOT EXISTS records_errors INTEGER DEFAULT 0;
```

**Tests to Add:**
- `test_etl_metadata_recorded_on_success`
- `test_etl_metadata_recorded_on_failure`
- `test_etl_metadata_duration_calculated`

---

## Phase 2: Performance Optimization (P1) - 3 hours

### Task 2.1: Use Batch Inserts with execute_batch

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Lines:** 535-550 (`_insert_simple_batch` method)

**Current Problem:**
- Row-by-row inserts cause N database round-trips
- `execute_batch` is imported but never used

**Implementation:**

1. Replace `_insert_simple_batch()` with:

```python
def _upsert_batch_fast(self, cursor, upsert_sql: str, batch: List):
    """
    Upsert a batch using execute_batch for better performance.

    Uses psycopg2.extras.execute_batch which batches statements
    for significantly better performance (10-50x faster).
    """
    try:
        execute_batch(cursor, upsert_sql, batch, page_size=100)
        self.stats['inserted'] += len(batch)
    except Exception as e:
        # Fall back to row-by-row for error isolation
        logger.warning(f"Batch upsert failed, falling back to row-by-row: {e}")
        for values in batch:
            try:
                cursor.execute(upsert_sql, values)
                self.stats['inserted'] += 1
            except Exception as row_error:
                logger.warning(f"Failed to upsert record: {row_error}")
                self.stats['errors'] += 1
```

2. Update all load methods to use `_upsert_batch_fast()`

**Expected Improvement:** 10-50x faster for large datasets

**Tests to Add:**
- `test_batch_insert_performance` - Verify batch faster than row-by-row
- `test_batch_insert_fallback_on_error` - Verify graceful degradation

---

### Task 2.2: Connection Reuse in load_all

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Lines:** 299-351 (`load_all` method)

**Current Problem:**
- Each view load opens/closes a new connection
- Unnecessary overhead for sequential operations

**Implementation:**

1. Add connection management methods:

```python
def __enter__(self):
    """Context manager entry - establish connection."""
    self.connect()
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit - close connection."""
    self.close()
    return False
```

2. Refactor load methods to accept optional cursor parameter:

```python
def load_tickets(self, batch_size: int = 500, cursor=None) -> Dict:
    """Load tickets. Uses provided cursor or creates new connection."""
    manage_connection = cursor is None
    if manage_connection:
        self.connect()
        cursor = self.conn.cursor()

    try:
        # ... existing logic using cursor ...
    finally:
        if manage_connection:
            cursor.close()
            self.close()
```

3. Update `load_all()` to reuse connection:

```python
def load_all(self, batch_size: int = 500) -> Dict:
    """Load all views using single connection."""
    all_stats = {}

    self.connect()
    cursor = self.conn.cursor()

    try:
        # Load all views with shared cursor
        all_stats['comments'] = self._load_comments_internal(cursor, batch_size)
        all_stats['timesheets'] = self._load_timesheets_internal(cursor, batch_size)
        all_stats['tickets'] = self._load_tickets_internal(cursor, batch_size)
        all_stats['user_lookup'] = self._update_user_lookup_internal(cursor)

        self.conn.commit()
    except Exception as e:
        self.conn.rollback()
        raise
    finally:
        cursor.close()
        self.close()

    return all_stats
```

**Tests to Add:**
- `test_load_all_single_connection` - Verify only one connection opened
- `test_load_all_rollback_on_failure` - Verify atomic behavior

---

### Task 2.3: Move Credentials to Environment Variables

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Lines:** 24-31

**Current Problem:**
- Password hardcoded in source code
- Security risk if code is shared/committed

**Implementation:**

1. Update `PG_CONFIG` to use environment variables:

```python
import os

def get_pg_config() -> Dict:
    """
    Get PostgreSQL configuration from environment variables.

    Environment variables:
        OTC_PG_HOST: Database host (default: localhost)
        OTC_PG_PORT: Database port (default: 5432)
        OTC_PG_DATABASE: Database name (default: servicedesk)
        OTC_PG_USER: Database user (default: servicedesk_user)
        OTC_PG_PASSWORD: Database password (required)
    """
    password = os.environ.get('OTC_PG_PASSWORD')
    if not password:
        # Try keychain as fallback
        try:
            from .auth import get_db_credentials
            _, password = get_db_credentials()
        except:
            raise ValueError(
                "Database password not found. Set OTC_PG_PASSWORD environment variable "
                "or store in keychain."
            )

    return {
        'host': os.environ.get('OTC_PG_HOST', 'localhost'),
        'port': int(os.environ.get('OTC_PG_PORT', 5432)),
        'database': os.environ.get('OTC_PG_DATABASE', 'servicedesk'),
        'user': os.environ.get('OTC_PG_USER', 'servicedesk_user'),
        'password': password
    }

# Replace hardcoded PG_CONFIG
PG_CONFIG = None  # Lazy loaded

class OTCPostgresLoader:
    def __init__(self, pg_config: Dict = None):
        global PG_CONFIG
        if pg_config is None:
            if PG_CONFIG is None:
                PG_CONFIG = get_pg_config()
            pg_config = PG_CONFIG
        self.pg_config = pg_config
        # ... rest of init
```

2. Update test file to use environment variable:

**File:** `tests/integrations/test_otc_schema_improvements.py`

```python
import os

@pytest.fixture
def db_connection():
    """PostgreSQL connection fixture using environment variables."""
    conn = psycopg2.connect(
        host=os.environ.get('OTC_PG_HOST', 'localhost'),
        port=int(os.environ.get('OTC_PG_PORT', 5432)),
        database=os.environ.get('OTC_PG_DATABASE', 'servicedesk'),
        user=os.environ.get('OTC_PG_USER', 'servicedesk_user'),
        password=os.environ.get('OTC_PG_PASSWORD', 'ServiceDesk2025!SecurePass')  # Fallback for local dev
    )
    yield conn
    conn.close()
```

3. Add to `.env.example`:

```bash
# OTC Database Configuration
OTC_PG_HOST=localhost
OTC_PG_PORT=5432
OTC_PG_DATABASE=servicedesk
OTC_PG_USER=servicedesk_user
OTC_PG_PASSWORD=your_password_here
```

**Tests to Add:**
- `test_config_from_environment_variables`
- `test_config_missing_password_raises`

---

## Phase 3: Reliability Improvements (P2) - 2 hours

### Task 3.1: Transaction Control with Rollback

**File:** `claude/tools/integrations/otc/load_to_postgres.py`
**Line:** 58

**Current Problem:**
- `autocommit=True` means partial loads can't be rolled back
- Failed ETL leaves orphaned data

**Implementation:**

1. Change connection to use transactions:

```python
def connect(self):
    """Establish PostgreSQL connection with transaction support."""
    if not self.conn:
        self.conn = psycopg2.connect(**self.pg_config)
        self.conn.autocommit = False  # Changed from True
        logger.info("Connected to PostgreSQL (transaction mode)")
```

2. Add commit/rollback handling to each load method:

```python
def load_tickets(self, batch_size: int = 500) -> Dict:
    # ... existing setup ...

    try:
        # ... loading logic ...

        self.conn.commit()  # Commit on success
        logger.info("Transaction committed successfully")

    except Exception as e:
        self.conn.rollback()  # Rollback on failure
        logger.error(f"Transaction rolled back due to: {e}")
        raise
    finally:
        self.close()
```

3. Add savepoint support for large batches:

```python
def _upsert_batch_with_savepoint(self, cursor, upsert_sql: str, batch: List, batch_num: int):
    """
    Upsert batch with savepoint for partial recovery.
    """
    savepoint_name = f"batch_{batch_num}"
    cursor.execute(f"SAVEPOINT {savepoint_name}")

    try:
        execute_batch(cursor, upsert_sql, batch, page_size=100)
        self.stats['inserted'] += len(batch)
        cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
    except Exception as e:
        cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        logger.warning(f"Batch {batch_num} failed, rolled back to savepoint: {e}")
        # Process row by row to find problem records
        for values in batch:
            try:
                cursor.execute(upsert_sql, values)
                self.stats['inserted'] += 1
            except Exception as row_error:
                logger.warning(f"Row failed: {row_error}")
                self.stats['errors'] += 1
```

**Tests to Add:**
- `test_rollback_on_failure`
- `test_partial_batch_recovery_with_savepoint`
- `test_commit_on_success`

---

### Task 3.2: Consistent Stats Reset

**File:** `claude/tools/integrations/otc/load_to_postgres.py`

**Current Problem:**
- `load_comments()` doesn't reset stats
- `load_timesheets()` and `load_tickets()` do reset
- Inconsistent behavior when calling methods individually

**Implementation:**

Add stats reset to `load_comments()` at line 82:

```python
def load_comments(self, batch_size: int = 500) -> Dict:
    logger.info("=" * 60)
    logger.info("LOADING OTC COMMENTS TO POSTGRESQL")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Reset stats (ADD THIS)
    self.stats = {
        'fetched': 0,
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }

    self.connect()
    # ... rest of method
```

**Tests to Add:**
- `test_stats_reset_between_loads`

---

## Phase 4: Code Quality (P3) - 2 hours

### Task 4.1: Extract Shared Datetime Parser

**File:** `claude/tools/integrations/otc/models.py`

**Current Problem:**
- `parse_datetime` validator duplicated 3 times (lines 54-79, 158-184, 284-310)

**Implementation:**

1. Add shared utility at top of file (after imports):

```python
from datetime import datetime
from typing import Any, Optional

DATETIME_FORMATS = [
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%d/%m/%Y',
]

def parse_datetime_value(v: Any) -> Optional[datetime]:
    """
    Parse datetime from various formats.

    Handles:
    - ISO 8601 format (with Z suffix)
    - Common date/time formats
    - Already parsed datetime objects
    - None/empty values

    Args:
        v: Value to parse (str, datetime, or None)

    Returns:
        Parsed datetime or None
    """
    if v is None or v == '':
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            pass
        # Try common formats
        for fmt in DATETIME_FORMATS:
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
    return None
```

2. Update all models to use shared function:

```python
class OTCComment(BaseModel):
    # ...

    @field_validator('created_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        return parse_datetime_value(v)


class OTCTicket(BaseModel):
    # ...

    @field_validator('created_time', 'modified_time', 'resolved_time',
                     'closed_time', 'due_date', 'response_date', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        return parse_datetime_value(v)


class OTCTimesheet(BaseModel):
    # ...

    @field_validator('date', 'modified_time', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        return parse_datetime_value(v)
```

**Tests to Add:**
- `test_parse_datetime_iso_format`
- `test_parse_datetime_common_formats`
- `test_parse_datetime_none_handling`

---

## Test Plan

### New Test File: `tests/integrations/test_otc_etl_improvements.py`

```python
"""
Tests for OTC ETL pipeline improvements.

Covers:
- UPSERT functionality
- ETL metadata recording
- Batch performance
- Transaction control
"""

import pytest
import psycopg2
from datetime import datetime
from claude.tools.integrations.otc.load_to_postgres import OTCPostgresLoader


class TestUpsertFunctionality:
    """Test UPSERT (INSERT ... ON CONFLICT) behavior."""

    def test_tickets_insert_new(self, db_connection, sample_ticket):
        """New tickets should be inserted."""
        pass

    def test_tickets_update_existing(self, db_connection, existing_ticket):
        """Existing tickets should be updated."""
        pass

    def test_tickets_preserves_created_time(self, db_connection):
        """UPSERT should not overwrite TKT-Created Time."""
        pass


class TestETLMetadata:
    """Test ETL metadata recording."""

    def test_metadata_recorded_on_success(self, db_connection):
        """Successful loads should record metadata."""
        pass

    def test_metadata_includes_duration(self, db_connection):
        """Metadata should include load duration."""
        pass

    def test_metadata_queryable_via_v_data_freshness(self, db_connection):
        """v_data_freshness view should use etl_metadata."""
        pass


class TestBatchPerformance:
    """Test batch insert performance."""

    def test_batch_faster_than_row_by_row(self, db_connection):
        """execute_batch should be faster than row-by-row."""
        pass


class TestTransactionControl:
    """Test transaction behavior."""

    def test_rollback_on_failure(self, db_connection):
        """Failed load should rollback all changes."""
        pass

    def test_commit_on_success(self, db_connection):
        """Successful load should commit changes."""
        pass
```

---

## Acceptance Criteria

### Phase 1 Complete When:
- [ ] Running ETL twice produces same ticket count (no duplicates, updates work)
- [ ] `SELECT * FROM servicedesk.etl_metadata` shows recent load records
- [ ] All 22 existing tests still pass
- [ ] 6 new tests for UPSERT/metadata pass

### Phase 2 Complete When:
- [ ] Large dataset load (10K+ records) completes in <30 seconds
- [ ] `load_all()` creates only 1 database connection
- [ ] Credentials not visible in source code (use env vars)

### Phase 3 Complete When:
- [ ] Intentionally failing ETL mid-run leaves no orphaned data
- [ ] Stats are consistent whether calling methods individually or via `load_all()`

### Phase 4 Complete When:
- [ ] Only one `parse_datetime` implementation in models.py
- [ ] All datetime parsing tests pass

---

## Rollback Plan

If issues are discovered:

1. **Database changes** (unique constraint on timesheets):
   ```sql
   ALTER TABLE servicedesk.timesheets
   DROP CONSTRAINT IF EXISTS timesheets_unique_entry;
   ```

2. **Code changes**: Revert to previous commit
   ```bash
   git revert HEAD
   ```

3. **Environment variables**: Fall back to hardcoded config temporarily

---

## Dependencies

- PostgreSQL 14+ (for ON CONFLICT support)
- psycopg2 2.9+ (for execute_batch)
- Python 3.11+

---

## Notes for Implementer

1. **Run existing tests first** to establish baseline:
   ```bash
   pytest tests/integrations/test_otc_schema_improvements.py -v
   ```

2. **Apply database migrations before code changes**:
   - Timesheets unique constraint
   - etl_metadata column additions

3. **Test each phase independently** before moving to next

4. **Commit after each phase** with descriptive message

5. **Update documentation** after all phases:
   - `claude/context/knowledge/servicedesk/otc_database_reference.md`
   - `claude/agents/data_analyst_agent.md` (if relevant)

---

**Ready for Implementation** ✅
