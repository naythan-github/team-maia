# ServiceDesk ETL Pipeline - Complete Usage Guide

> ⚠️ **ARCHIVED**: This guide documents the SQLite-based ETL pipeline from Phase 127.
> **Current Pipeline**: PostgreSQL-based import via `xlsx_to_postgres.py`
> **See**: `claude/context/knowledge/servicedesk/otc_database_reference.md` for current instructions.
>
> **Key Changes (Jan 2026)**:
> - Database: SQLite → PostgreSQL (Docker)
> - Comments columns: `CT-*` → `TKTCT-*` format
> - Import tool: `xlsx_to_postgres.py` (upsert with conflict handling)

**Created**: 2025-10-17 (Phase 127)
**Status**: ⚠️ ARCHIVED (Superseded by PostgreSQL pipeline)
**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

---

## 📋 Quick Start - Process Fresh ServiceDesk Data

**Single Command** (recommended - includes validation):
```bash
cd ~/git/maia
python3 claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

This will automatically:
1. ✅ Validate data quality (score ≥60 required to proceed)
2. ✅ Clean data (dates, types, text, missing values)
3. ✅ Score final quality (5-dimension assessment)
4. ✅ Import to database (Cloud-touched logic preserved)
5. ✅ Record import metadata

---

## 🛠️ Pipeline Components

### 1. **Validator** - Pre-Import Quality Check
**File**: `claude/tools/sre/servicedesk_etl_validator.py` (792 lines)
**Purpose**: Validate XLSX data quality before import
**Rules**: 40 validation rules across 6 categories

**Usage**:
```bash
python3 claude/tools/sre/servicedesk_etl_validator.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

**Output**:
```
Composite Score: 94.21/100 (🟢 EXCELLENT)
Decision: ✅ PROCEED

Category Scores:
  Schema Validation: 10/10 (100.0%) ✅
  Completeness: 32/40 (80.0%) ✅
  Data Types: 8/8 (100.0%) ✅
  Business Rules: 7/8 (87.5%) ✅
  Referential Integrity: 4/4 (100.0%) ✅
  Text Integrity: 2/2 (100.0%) ✅
```

**Key Rules**:
- Schema: Required columns present, no unexpected columns
- Completeness: Critical fields populated (CT-COMMENT-ID 94%, TKT-Ticket ID 100%)
- Data Types: Numeric IDs, parseable dates, valid booleans
- Business Rules: Date ranges valid, text lengths reasonable
- Referential Integrity: Foreign keys valid (comments→tickets, timesheets→tickets)
- Text Integrity: No NULL bytes, reasonable newlines

---

### 2. **Cleaner** - Data Standardization
**File**: `claude/tools/sre/servicedesk_etl_cleaner.py` (612 lines)
**Purpose**: Clean and standardize data for import
**Operations**: 5 types (dates, types, text, missing values, defaults)

**Usage**:
```bash
python3 claude/tools/sre/servicedesk_etl_cleaner.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

**Output**:
```
✅ Cleaning complete: 22 transformations applied

Total Transformations: 22
Total Records Affected: 4,571,716

Transformations by Operation:
  date_standardization: 3
  type_normalization_int: 5
  type_normalization_float: 1
  type_normalization_bool: 1
  text_cleaning: 5
  missing_value_imputation: 2
  missing_value_check: 5
```

**Cleaning Operations**:
1. **Date Standardization**: DD/MM/YYYY → ISO 8601 (dayfirst=True parsing)
2. **Type Normalization**: String IDs → Int64, hours → float, booleans → bool
3. **Text Cleaning**: Whitespace trim, newline normalization, null byte removal
4. **Missing Value Imputation**: Business rules (CT-VISIBLE-CUSTOMER NULL → FALSE)
5. **Business Defaults**: Conservative values for missing critical fields

**Complete Audit Trail**: All transformations logged with before/after samples

---

### 3. **Scorer** - Quality Assessment
**File**: `claude/tools/sre/servicedesk_quality_scorer.py` (705 lines)
**Purpose**: Calculate post-cleaning quality score
**Dimensions**: 5 (Completeness, Validity, Consistency, Uniqueness, Integrity)

**Usage**:
```bash
python3 claude/tools/sre/servicedesk_quality_scorer.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

**Output**:
```
Composite Score: 90.85/100
Quality Grade: 🟢 EXCELLENT
Recommendation: Production ready

Dimension Breakdown:
  COMPLETENESS: 38.23/40.0 (95.6%)
  VALIDITY: 29.99/30.0 (100.0%)
  CONSISTENCY: 16.39/20.0 (82.0%)
  UNIQUENESS: 3.27/5.0 (65.4%)
  INTEGRITY: 2.96/5.0 (59.2%)
```

**Scoring Algorithm**:
- **Completeness (40 pts)**: Comments 16pts, Tickets 14pts, Timesheets 10pts
- **Validity (30 pts)**: Dates parseable, no invalid ranges, text integrity
- **Consistency (20 pts)**: Temporal logic, type consistency
- **Uniqueness (5 pts)**: Primary keys unique
- **Integrity (5 pts)**: Foreign keys valid, orphan rate acceptable

---

### 4. **Column Mappings** - XLSX→Database
**File**: `claude/tools/sre/servicedesk_column_mappings.py` (139 lines)
**Purpose**: Map XLSX column names to database fields
**Usage**: Imported by other tools automatically

**Example Mappings**:
```python
COMMENTS_COLUMNS = {
    'CT-COMMENT-ID': 'comment_id',
    'CT-TKT-ID': 'ticket_id',
    'CT-DATEAMDTIME': 'created_time',
    'CT-COMMENT': 'comment_text',
    # ... etc
}
```

---

### 5. **Integrated ETL** - Production Import
**File**: `claude/tools/sre/incremental_import_servicedesk.py` (354 lines, +112 from original)
**Purpose**: Complete end-to-end import with quality validation
**Integration**: Calls validator → cleaner → scorer → import

**Usage**:
```bash
# Standard import (with validation)
python3 claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx

# Emergency import (skip validation)
python3 claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx \
  --skip-validation

# View import history
python3 claude/tools/sre/incremental_import_servicedesk.py history
```

**Workflow**:
```
STEP 0: Pre-import quality validation
├── 0.1 Validator: Baseline quality (94.21/100)
├── 0.2 Cleaner: Data standardization (22 transformations)
├── 0.3 Scorer: Post-cleaning verification (90.85/100)
└── Decision Gate: PROCEED (≥60) or HALT (<60)

STEP 1: Import comments (Cloud-touched logic)
STEP 2: Import tickets (Cloud-touched filter)
STEP 3: Import timesheets (Cloud-touched filter)
```

**Quality Gate**: Automatic halt if score <60

---

## 📊 Complete Workflow Example

### Scenario: Process Fresh October Data Export

```bash
# 1. Download XLSX files to ~/Downloads/
# 2. Run integrated import (includes validation)
cd ~/git/maia
python3 claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

**Expected Output**:
```
================================================================================
SERVICEDESK DATA IMPORT - Enhanced with Quality Validation (Phase 127)
================================================================================

================================================================================
🔍 PRE-IMPORT QUALITY VALIDATION (Phase 127)
================================================================================

📋 STEP 0.1: Validating source data quality...
   ✅ Validation score: 94.21/100
   ✅ Validation passed: 94.21/100 >= 60 (threshold)

🧹 STEP 0.2: Cleaning data (date standardization, type normalization)...
   ✅ Applied 22 data cleaning transformations

📊 STEP 0.3: Scoring cleaned data quality...
   ✅ Final quality score: 90.85/100

================================================================================
✅ PRE-IMPORT VALIDATION COMPLETE
================================================================================
   Quality Score: 90.85/100
   Decision: PROCEED WITH IMPORT
================================================================================

💬 STEP 1: Importing comments from: /Users/naythandawe/Downloads/comments.xlsx
   Loaded 204,625 rows
   ✅ Filtered to 176,637 rows (July 1+ only)
   📋 Cloud roster: 48 members
   🎯 Identified 10,939 Cloud-touched tickets
   ✅ Keeping ALL comments for Cloud-touched tickets: 108,129 rows
   ✅ Imported as import_id=14
   📅 Date range: 2025-07-03 to 2025-10-14

📋 STEP 2: Importing tickets from: /Users/naythandawe/Downloads/tickets.xlsx
   Loaded 652,681 rows
   🎯 Cloud-touched tickets: 10,939 rows
   ✅ Imported as import_id=15
   📅 Date range: 2025-07-03 to 2025-10-13

⏱️  STEP 3: Importing timesheets from: /Users/naythandawe/Downloads/timesheets.xlsx
   Loaded 732,959 rows
   ✅ Filtered to 141,062 rows (July 1+ only)
   ⚠️  Found 128,007 orphaned timesheet entries (90.7%)
   ✅ Imported as import_id=16
   📅 Date range: 2025-07-01 to 2026-07-01

================================================================================
✅ IMPORT COMPLETE
================================================================================
   Comments import_id: 14
   Tickets import_id: 15
   Timesheets import_id: 16
   Cloud-touched tickets: 10,939
   Pre-import quality score: 90.85/100
```

---

## 🔄 Re-Index RAG Database (After Import)

After importing fresh data, rebuild the RAG index:

```bash
# Delete old index
rm -rf ~/.maia/servicedesk_rag

# Re-index with fresh data (using local GPU)
python3 ~/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py --index-all
```

**Expected Output**:
```
✅ GPU RAG Indexer initialized
   Model: intfloat/e5-base-v2
   Device: mps (Apple Silicon)
   Batch size: 64

======================================================================
GPU INDEXING ALL COLLECTIONS
======================================================================

Processing collections:
  ✅ comments (108,084 docs) - 10 min
  ✅ descriptions (10,939 docs) - 1 min
  ✅ solutions (10,694 docs) - 30 sec
  ✅ titles (10,939 docs) - 25 sec
  ✅ work_logs (73,273 docs) - 5 min

Total: 213,929 documents indexed in ~15-20 minutes
```

---

## 🧪 Testing the Pipeline

### Test 1: Validate Only (No Changes)
```bash
python3 claude/tools/sre/servicedesk_etl_validator.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

### Test 2: Clean Only (No Import)
```bash
python3 claude/tools/sre/servicedesk_etl_cleaner.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

### Test 3: Score Only (After Cleaning)
```bash
python3 claude/tools/sre/servicedesk_quality_scorer.py \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```

### Test 4: Full Pipeline with Dry Run
```bash
# No dry-run mode yet - use --skip-validation and check database before committing
sqlite3 ~/git/maia/claude/data/servicedesk_tickets.db "SELECT COUNT(*) FROM comments"
```

---

## 📈 Quality Metrics

### Baseline Results (October 2025 Data):
- **Validator Score**: 94.21/100 (EXCELLENT)
- **Post-Cleaning Score**: 90.85/100 (EXCELLENT)
- **Transformations Applied**: 22
- **Records Affected**: 4,571,716
- **Import Volume**: 260,125 rows (comments, tickets, timesheets)
- **RAG Documents**: 213,929 indexed

### Quality Thresholds:
- **90-100**: EXCELLENT - Production ready
- **80-89**: GOOD - Minor issues acceptable
- **70-79**: ACCEPTABLE - Review warnings
- **60-69**: POOR - Address issues before import
- **<60**: FAILED - DO NOT IMPORT (automatic halt)

---

## ⚠️ Known Issues & Limitations

### 1. In-Place Cleaning
**Issue**: Cleaner modifies source XLSX files in-place
**Workaround**: Backup XLSX files before running
**Future**: Create temporary cleaned files, preserve originals
**Priority**: LOW (acceptable for development)

### 2. ChromaDB Settings Conflicts
**Issue**: Re-indexing may fail with "different settings" error
**Workaround**: Delete `~/.maia/servicedesk_rag/` before re-indexing
**Status**: Resolved by deleting old index first

### 3. Timesheet Entry ID Column
**Issue**: TS-Title is NOT the timesheet entry ID column (0.04% numeric)
**Impact**: Cannot validate timesheet uniqueness correctly
**TODO**: Find correct column in XLSX, update column mappings
**Priority**: LOW (orphaned timesheets expected behavior)

---

## 🔧 Troubleshooting

### Issue: Validation Fails with Score <60
**Solution**: Review validation report, fix source data issues before import

### Issue: Cleaner Type Conversion Error
**Solution**: Bug fixed in Phase 127 - ensure using latest version (check git commit)

### Issue: RAG Indexing "Different Settings" Error
**Solution**:
```bash
rm -rf ~/.maia/servicedesk_rag
python3 ~/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py --index-all
```

### Issue: Import Fails on Tickets/Timesheets (UnicodeDecodeError)
**Solution**: Bug fixed in Phase 127 - ensure XLSX format support in `incremental_import_servicedesk.py`

---

## 📚 Related Documentation

**Phase 127 Documentation**:
- `PHASE_127_DAY_4-5_INTEGRATION_COMPLETE.md` - Complete implementation summary
- `PHASE_127_RECOVERY_STATE.md` - Resume instructions
- `SERVICEDESK_PATTERN_ANALYSIS_OCT_2025.md` - Pattern analysis example

**Project Plan**:
- `SERVICEDESK_ETL_QUALITY_ENHANCEMENT_PROJECT.md` - Full 7-day project plan
- `ROOT_CAUSE_ANALYSIS_ServiceDesk_ETL_Quality.md` - Day 1-2 findings

**Database**:
- Location: `~/git/maia/claude/data/servicedesk_tickets.db` (1.24GB)
- RAG Index: `~/.maia/servicedesk_rag/` (753MB)

---

## 🎯 Success Criteria

After processing fresh data, verify:

✅ **Data Quality**: Score ≥90/100 (EXCELLENT)
✅ **Import Volume**: Expected row counts (comments ~108K, tickets ~11K, timesheets ~141K)
✅ **RAG Index**: 213K+ documents successfully indexed
✅ **Search Quality**: Test queries return relevant results (0.09-1.03 distance)
✅ **No Errors**: Zero Python exceptions during pipeline execution
✅ **Audit Trail**: All transformations logged with before/after samples

---

**Pipeline Status**: ✅ PRODUCTION READY
**Last Tested**: 2025-10-17 (Phase 127)
**Maintained By**: Maia System / ServiceDesk Manager Agent
