# PMP TDD Checklist - Comprehensive Testing Protocol

**Purpose**: Mandatory testing checklist for ALL Patch Manager Plus development work
**Created**: 2025-12-01
**Case Study**: PRIMARY KEY bug (99.98% data loss) - missed due to no TDD
**Reference**: General TDD protocol at `claude/context/core/tdd_development_protocol.md`

---

## 🚨 CRITICAL LEARNING: PRIMARY KEY BUG (2025-12-01)

**What Happened**:
- Extracted 58,600 supported patches over 10.6 hours
- Only 9 records saved to database (99.98% data loss)
- Root cause: Used non-unique `update_id` (0-9 sequential) as PRIMARY KEY instead of unique `patch_id`
- `INSERT OR REPLACE` overwrote records repeatedly

**What Would Have Caught It**:
- ✅ **Test 1**: Record preservation test (verify count matches fetched count)
- ✅ **Test 2**: Primary key uniqueness test (verify schema uses unique field)
- ✅ **Test 3**: Duplicate handling test (verify duplicate update_ids don't overwrite)

**Cost of No TDD**:
- 35 hours lost (10.6h extraction + 24h rate limit wait + re-run time)
- Cost of TDD: 30 minutes investment
- **ROI: 69x return on investment**

**Lesson**: TDD is NOT optional - it's cheaper and faster than production failures

---

## Mandatory Test Categories

### 1. Schema Validation Tests ⭐ CRITICAL

**Purpose**: Verify database schema matches API reality

#### 1.1 Primary Key Tests
```python
def test_primary_key_uses_unique_identifier():
    """Verify PRIMARY KEY uses globally unique field from API"""
    # For supported_patches: patch_id (NOT update_id)
    # For systems: resource_id (NOT display sequence)
    # For policies: policy_id (NOT policy_name)
    schema = get_table_schema("supported_patches")
    assert schema['primary_key'] == 'patch_id', "PRIMARY KEY must be unique identifier"
    assert schema['primary_key'] != 'update_id', "update_id is NOT unique (0-9 sequential)"
```

#### 1.2 Foreign Key Tests
```python
def test_foreign_keys_valid():
    """Verify all foreign key references exist"""
    # extraction_id must exist in api_extraction_runs
    # system_id must exist in systems table
    # etc.
```

#### 1.3 Field Type Tests
```python
def test_field_types_match_api():
    """Verify column types match API response types"""
    # Timestamps should be INTEGER (Unix epoch) not TEXT
    # Booleans should be INTEGER (0/1) not TEXT
    # IDs should match API type (usually INTEGER)
```

---

### 2. API Integration Tests ⭐ CRITICAL

**Purpose**: Verify API interactions work as expected

#### 2.1 OAuth Tests
```python
def test_oauth_uses_correct_scopes():
    """Verify OAuth scopes match working implementation"""
    oauth_manager = PmpOAuthManager()
    assert "PatchManagerPlusCloud.Common.READ" in oauth_manager.SCOPES
    assert "PatchManagerPlusCloud.PatchMgmt.READ" in oauth_manager.SCOPES
    # Bug #1 from bug_fixes_summary.md - wrong scopes

def test_authorization_header_format():
    """Verify Zoho-specific auth header (not standard Bearer)"""
    headers = oauth_manager.get_auth_headers()
    assert headers['Authorization'].startswith('Zoho-oauthtoken ')
    assert not headers['Authorization'].startswith('Bearer ')
    # Bug #2 from bug_fixes_summary.md - wrong format
```

#### 2.2 Response Parsing Tests
```python
def test_multi_field_response_checking():
    """Verify code checks multiple possible field names"""
    # Different endpoints return data in different fields:
    # /api/1.4/patch/allpatches → 'allpatches'
    # /api/1.4/patch/allsystems → 'allsystems' OR 'computers'
    # /api/1.4/som/computers → 'computers'
    mock_response = {'computers': [...]}
    records = extract_records(mock_response, expected_key='allsystems')
    assert len(records) > 0, "Should find data in alternative field names"
    # Bug #3 from bug_fixes_summary.md - single field checking

def test_throttling_detection():
    """Verify HTML throttling pages detected"""
    html_response = "<!DOCTYPE html><html>...</html>"
    with pytest.raises(ThrottlingDetectedException):
        parse_api_response(html_response)
    # Bug #4 from bug_fixes_summary.md - no HTML detection
```

#### 2.3 Pagination Tests
```python
def test_pagination_page_size():
    """Verify pagination uses correct page size"""
    assert extractor.PAGE_SIZE == 25
    # PMP API returns EXACTLY 25 records per page (fixed, not configurable)

def test_pagination_calculates_total_correctly():
    """Verify total record calculation from pagination"""
    # If API returns total_count=58,600 and page_size=25
    # Expected pages = 2,344
    total_pages = extractor.calculate_total_pages(58600)
    assert total_pages == 2344
```

---

### 3. Data Integrity Tests ⭐ CRITICAL

**Purpose**: Verify all fetched data is saved correctly

#### 3.1 Record Preservation Tests
```python
def test_extract_supported_patches_preserves_all_records():
    """PRIMARY KEY BUG TEST - verify all fetched records saved"""
    # Mock API response with 1000 records
    mock_patches = [{'patch_id': i, 'update_id': i % 10, ...} for i in range(1000)]

    # Extract to database
    count = extractor.extract_supported_patches(mock_patches, 'supported_patches')

    # Verify ALL records saved (not just 10 due to update_id conflict)
    db_count = get_record_count('supported_patches')
    assert db_count == 1000, f"Expected 1000 records, got {db_count}"
    # This test would have caught the PRIMARY KEY bug immediately
```

#### 3.2 Duplicate Handling Tests
```python
def test_handles_duplicate_update_ids():
    """Verify duplicate update_ids don't overwrite records"""
    # update_id is 0-9 sequential, NOT unique
    patches = [
        {'patch_id': 1, 'update_id': 0, 'bulletin_id': 'KB001'},
        {'patch_id': 2, 'update_id': 0, 'bulletin_id': 'KB002'},  # Same update_id
    ]
    extractor.extract_supported_patches(patches, 'supported_patches')

    # Both records should exist
    assert get_record_count('supported_patches') == 2
    assert record_exists('supported_patches', patch_id=1)
    assert record_exists('supported_patches', patch_id=2)
```

#### 3.3 Field Completeness Tests
```python
def test_all_api_fields_extracted():
    """Verify no data loss - all API fields captured"""
    mock_patch = {
        'patch_id': 123,
        'bulletin_id': 'KB123456',
        'patch_lang': 'en',
        'severity': 'Critical',
        'vendor_name': 'Microsoft',
        # ... all fields from API
    }
    extractor.extract_supported_patches([mock_patch], 'supported_patches')

    record = get_record('supported_patches', patch_id=123)
    for field in mock_patch.keys():
        assert field in record.keys(), f"Field '{field}' not extracted"
```

---

### 4. Resume Capability Tests ⭐ HIGH PRIORITY

**Purpose**: Verify extraction can resume after interruptions

#### 4.1 Resume Point Calculation
```python
def test_calculate_resume_point_from_beginning():
    """Verify resume starts at page 1 when no existing records"""
    start_page, existing_count = extractor.calculate_resume_point('supported_patches', 'endpoint')
    assert start_page == 1
    assert existing_count == 0

def test_calculate_resume_point_midway():
    """Verify resume calculation from existing records"""
    # Simulate 1,250 existing records (50 pages × 25 records/page)
    insert_mock_records('supported_patches', count=1250)

    start_page, existing_count = extractor.calculate_resume_point('supported_patches', 'endpoint')
    assert start_page == 51  # Resume from page 51
    assert existing_count == 1250
```

#### 4.2 Duplicate Prevention
```python
def test_resume_prevents_duplicates():
    """Verify resumed extraction doesn't create duplicates"""
    # First run: extract 500 records
    extractor.extract_endpoint('supported_patches', start_page=1)
    count_first = get_record_count('supported_patches')

    # Resume from midpoint
    extractor.extract_endpoint('supported_patches', start_page=calculate_resume_point())
    count_after = get_record_count('supported_patches')

    # Should have more records, but no duplicates
    assert count_after > count_first
    assert no_duplicates('supported_patches', key='patch_id')
```

#### 4.3 Checkpoint Tracking
```python
def test_checkpoint_saves_progress():
    """Verify checkpoint state persisted correctly"""
    # Extract 10 pages
    extractor.extract_with_checkpoints(pages=10)

    # Verify checkpoint state
    checkpoint = load_checkpoint()
    assert checkpoint['last_page'] == 10
    assert checkpoint['records_extracted'] == 250  # 10 pages × 25 records
    assert checkpoint['endpoint'] == 'supported_patches'
```

---

### 5. Error Handling Tests ⭐ HIGH PRIORITY

**Purpose**: Verify graceful handling of API errors

#### 5.1 Rate Limit Tests
```python
def test_handles_rate_limit_429():
    """Verify 429 Too Many Requests handled gracefully"""
    with patch('requests.get', return_value=Mock(status_code=429)):
        with pytest.raises(RateLimitException):
            extractor.fetch_page(endpoint='supported_patches', page=1)

def test_handles_daily_quota_exceeded():
    """Verify daily quota detection and graceful exit"""
    # After 10.6 hours of extraction, remaining endpoints failed
    # Should detect quota exceeded and exit cleanly (not crash)
```

#### 5.2 Network Error Tests
```python
def test_retries_on_network_error():
    """Verify network errors trigger retry logic"""
    # First 2 calls fail, 3rd succeeds
    with patch('requests.get', side_effect=[
        requests.exceptions.ConnectionError(),
        requests.exceptions.ConnectionError(),
        Mock(status_code=200, json=lambda: {'data': [...]})
    ]):
        result = extractor.fetch_with_retry(endpoint='supported_patches', page=1)
        assert result is not None

def test_max_retries_exceeded():
    """Verify graceful failure after max retries"""
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError()):
        with pytest.raises(MaxRetriesExceeded):
            extractor.fetch_with_retry(endpoint='supported_patches', page=1, max_retries=3)
```

#### 5.3 JSON Parse Error Tests
```python
def test_handles_malformed_json():
    """Verify malformed JSON responses handled"""
    # Bug #4: API sometimes returns HTML when throttled
    with patch('requests.get', return_value=Mock(
        status_code=200,
        text='<!DOCTYPE html>...'
    )):
        with pytest.raises(JSONDecodeError):
            extractor.fetch_page(endpoint='supported_patches', page=1)
```

---

### 6. Performance Tests ⭐ MEDIUM PRIORITY

**Purpose**: Verify extraction performance and resource usage

#### 6.1 Rate Limiting Tests
```python
def test_respects_rate_limits():
    """Verify delays between API calls"""
    start_time = time.time()
    extractor.fetch_page(endpoint='supported_patches', page=1)
    extractor.fetch_page(endpoint='supported_patches', page=2)
    elapsed = time.time() - start_time

    # Should have 250ms delay between pages
    assert elapsed >= 0.25, "Rate limit delay not respected"

def test_rate_limit_configurable():
    """Verify rate limit delays can be adjusted"""
    extractor = PmpExtractor(page_delay_ms=100)
    assert extractor.page_delay == 0.1
```

#### 6.2 Batch Processing Tests
```python
def test_batch_size_optimization():
    """Verify batch processing for database inserts"""
    # Should insert in batches (e.g., 1000 records) not one-by-one
    mock_patches = [{'patch_id': i, ...} for i in range(5000)]

    with patch('sqlite3.Connection.execute') as mock_execute:
        extractor.extract_supported_patches(mock_patches, 'supported_patches')
        # Should batch into 5 calls (5000 records / 1000 batch size)
        assert mock_execute.call_count <= 10  # Allow some overhead
```

---

### 7. WAL Mode & Concurrency Tests ⭐ MEDIUM PRIORITY

**Purpose**: Verify database can be queried during extraction

#### 7.1 WAL Mode Tests
```python
def test_wal_mode_enabled():
    """Verify WAL mode enabled for concurrent access"""
    conn = sqlite3.connect(extractor.db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    assert mode == 'wal', "WAL mode must be enabled"
    conn.close()

def test_concurrent_read_during_write():
    """Verify database readable during extraction"""
    # Start extraction in thread
    extraction_thread = Thread(target=extractor.extract_endpoint, args=('supported_patches',))
    extraction_thread.start()

    # Query database while extraction running
    time.sleep(1)  # Let extraction start
    count = query_database("SELECT COUNT(*) FROM supported_patches")
    assert count >= 0  # Should not block or error

    extraction_thread.join()
```

---

### 8. Integration Tests ⭐ HIGH PRIORITY

**Purpose**: End-to-end extraction validation

#### 8.1 Full Extraction Test (Mock)
```python
def test_full_extraction_mock():
    """End-to-end extraction with mocked API"""
    # Mock API with realistic pagination
    with patch_api_responses(total_records=1000, page_size=25):
        extractor.run_full_extraction()

    # Verify all endpoints extracted
    assert get_record_count('supported_patches') == 1000
    assert get_record_count('all_patches') > 0
    assert get_record_count('systems') > 0

    # Verify extraction metadata
    run = get_extraction_run()
    assert run['status'] == 'completed'
    assert run['endpoints_extracted'] == 13  # All working endpoints

def test_extraction_with_resume():
    """End-to-end extraction with simulated interruption"""
    # Extract first 500 records
    with patch_api_responses(total_records=1000, page_size=25):
        extractor.run_extraction(max_pages=20)
    count_first = get_record_count('supported_patches')

    # Simulate interruption, then resume
    extractor = PmpExtractor()  # New instance
    with patch_api_responses(total_records=1000, page_size=25):
        extractor.run_extraction()  # Should resume automatically
    count_final = get_record_count('supported_patches')

    assert count_final == 1000
    assert count_final > count_first
```

---

## Test Organization

### Directory Structure
```
claude/tools/pmp/tests/
├── __init__.py
├── conftest.py                      # Pytest fixtures
├── test_schema_validation.py       # Category 1
├── test_api_integration.py          # Category 2
├── test_data_integrity.py           # Category 3 ⭐ CRITICAL
├── test_resume_capability.py        # Category 4
├── test_error_handling.py           # Category 5
├── test_performance.py              # Category 6
├── test_wal_concurrency.py          # Category 7
├── test_integration.py              # Category 8
└── fixtures/
    ├── mock_api_responses.json
    └── sample_data.json
```

### Pytest Fixtures (conftest.py)
```python
import pytest
import sqlite3
import tempfile

@pytest.fixture
def temp_db():
    """Temporary database for testing"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    # Initialize schema
    conn = sqlite3.connect(db_path)
    # Create tables...
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)

@pytest.fixture
def extractor(temp_db):
    """Configured extractor instance"""
    return PmpExtractor(db_path=temp_db)

@pytest.fixture
def mock_api_response():
    """Sample API response"""
    with open('fixtures/mock_api_responses.json') as f:
        return json.load(f)
```

---

## TDD Workflow Integration

### Step 1: Requirements → Tests (BEFORE coding)
```bash
# 1. Create test file first
touch claude/tools/pmp/tests/test_new_feature.py

# 2. Write failing tests
pytest claude/tools/pmp/tests/test_new_feature.py
# All tests should FAIL (red)
```

### Step 2: Implementation
```bash
# 3. Implement feature
vim claude/tools/pmp/pmp_new_feature.py

# 4. Run tests until green
pytest claude/tools/pmp/tests/test_new_feature.py
# Tests should PASS (green)
```

### Step 3: Validation
```bash
# 5. Run full test suite
pytest claude/tools/pmp/tests/
# All tests must pass before production

# 6. Coverage report
pytest --cov=claude/tools/pmp --cov-report=html
# Aim for >80% coverage on critical paths
```

---

## Pre-Commit Checklist

**Before ANY PMP code commit:**
- [ ] All tests passing (`pytest claude/tools/pmp/tests/`)
- [ ] Coverage >80% on modified code
- [ ] Schema validation tests updated (if schema changed)
- [ ] Data integrity tests pass (record preservation)
- [ ] Integration test passes (end-to-end)
- [ ] Manual smoke test on small dataset
- [ ] Documentation updated

**If ANY test fails:**
- ❌ DO NOT commit
- ❌ DO NOT merge
- ❌ DO NOT deploy to production

---

## Coverage Targets

### Critical Paths (100% coverage required)
- Database schema creation
- Primary key definitions
- Data extraction and insertion
- Resume point calculation
- OAuth token management

### High Priority (>90% coverage)
- API pagination logic
- Error handling
- Retry mechanisms
- Checkpoint tracking

### Medium Priority (>70% coverage)
- Performance optimization
- Logging
- Progress reporting

---

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: PMP Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest claude/tools/pmp/tests/ --cov=claude/tools/pmp --cov-fail-under=80
```

---

## Success Metrics

### Before TDD (Historical)
- ❌ PRIMARY KEY bug: 99.98% data loss
- ❌ 35 hours wasted on failed extraction
- ❌ No automated validation
- ❌ Production failures discovery

### After TDD (Target)
- ✅ Bugs caught in <5 minutes (test execution)
- ✅ Zero production data loss incidents
- ✅ 30 minutes investment saves 35+ hours
- ✅ Confidence in deployments

---

## References

- **General TDD Protocol**: `claude/context/core/tdd_development_protocol.md`
- **Bug Fixes Summary**: `~/work_projects/pmp_reports/pmp_api_bug_fixes_summary.md`
- **Primary KEY Bug**: SYSTEM_STATE.md (Phase TBD - 2025-12-01)
- **SRE Agent TDD**: `claude/agents/sre_principal_engineer_agent.md`

---

**Last Updated**: 2025-12-01
**Status**: ✅ PRODUCTION READY
**Enforcement**: MANDATORY for ALL PMP development

**Remember**: 30 minutes of TDD prevents 35 hours of production pain. ROI = 69x.
