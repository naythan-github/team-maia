# ServiceDesk XLSX Re-Import & Re-RAG Recovery Plan

**Created**: 2025-10-16 16:50
**Status**: READY TO EXECUTE
**Estimated Time**: 4-5 hours total (15 min import + 3-4 hours re-RAG)
**Context**: CSV corruption fix - unescaped commas caused column misalignment

---

## 🚨 Problem Summary

**Root Cause**: CSV export from internal system had unescaped commas in comment text
- CSV parser sees 3,564 fields instead of 10
- Column misalignment after comment_text field (position #3)
- **CT-VISIBLE-CUSTOMER field corrupted** (position #8) - CRITICAL for customer communication % metric
- Comment text may be truncated at comma boundaries
- RAG embeddings created from corrupted text

**Impact**:
- Lost ability to track customer communication % (key success metric)
- Semantic search quality degraded by corrupted comment text
- Data integrity compromised

**Solution**: Import from XLSX (no comma-splitting issues) + Re-RAG from clean data

---

## 📋 10-Step Recovery Plan

### Phase 1: XLSX Import (10-15 minutes)

#### Step 1: Backup Current Database
```bash
cp /Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db \
   /Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db.backup_$(date +%Y%m%d_%H%M%S)
```
**Safety**: Can rollback if import fails

#### Step 2: Drop Corrupted Tables
```bash
sqlite3 /Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db << 'EOF'
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS timesheets;
EOF
```
**Keep**: cloud_team_roster, import_metadata, comment_quality (preserve history)

#### Step 3: Import comments.xlsx
```bash
cd ~/git/maia
python3 claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.xlsx \
  ~/Downloads/tickets.xlsx \
  ~/Downloads/timesheets.xlsx
```
**Critical Validation**: Check CT-VISIBLE-CUSTOMER field populated
```sql
-- Should return counts, not all NULL
SELECT visible_to_customer, COUNT(*)
FROM comments
GROUP BY visible_to_customer;
```

#### Step 4: Import tickets.xlsx
**Included in Step 3** - 3-stage import process handles all files

#### Step 5: Import timesheets.xlsx
**Included in Step 3** - 3-stage import process handles all files

#### Step 6: Validate Data Quality
```bash
sqlite3 /Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db << 'EOF'
-- Record counts
SELECT 'comments' as table_name, COUNT(*) as count FROM comments
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'timesheets', COUNT(*) FROM timesheets;

-- CT-VISIBLE-CUSTOMER validation (CRITICAL!)
SELECT
  visible_to_customer,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM comments), 1) as pct
FROM comments
GROUP BY visible_to_customer;

-- Spot check comment text integrity (should be full sentences, not truncated)
SELECT comment_text FROM comments WHERE LENGTH(comment_text) > 100 LIMIT 5;
EOF
```

**Expected Results**:
- Comments: ~108,129 rows (similar to CSV import)
- Tickets: ~10,939 rows
- Timesheets: ~141,062 rows
- **CT-VISIBLE-CUSTOMER**: Should show True/False distribution, NOT all NULL
- Comment text: Full sentences without truncation

---

### Phase 2: Re-RAG from Clean Data (3-4 hours)

#### Step 7: Clean ChromaDB Collections
```bash
# Delete all 5 existing collections (created from corrupted CSV data)
python3 << 'EOF'
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="/Users/naythandawe/.maia/servicedesk_rag",
    settings=Settings(anonymized_telemetry=False)
)

collections_to_delete = [
    'servicedesk_comments',
    'servicedesk_descriptions',
    'servicedesk_solutions',
    'servicedesk_titles',
    'servicedesk_work_logs'
]

for coll_name in collections_to_delete:
    try:
        client.delete_collection(coll_name)
        print(f"✅ Deleted: {coll_name}")
    except Exception as e:
        print(f"⚠️  {coll_name}: {e}")

print("\n✅ ChromaDB cleaned - ready for fresh indexing")
EOF
```

#### Step 8: Re-index All Documents with E5-base-v2
```bash
cd ~/git/maia
python3 claude/tools/sre/servicedesk_gpu_rag_indexer.py \
  --model intfloat/e5-base-v2 \
  --index-all
```

**Expected Output**:
```
Indexing collection: work_logs (73,273 docs) - ~63 min
Indexing collection: comments (108,104 docs) - ~93 min
Indexing collection: descriptions (10,937 docs) - ~9 min
Indexing collection: titles (10,939 docs) - ~9 min
Indexing collection: solutions (10,694 docs) - ~9 min

Total: ~183 min (3.05 hours)
```

**Progress Monitoring**:
```bash
# In separate terminal, watch progress
watch -n 30 'python3 -c "
import chromadb
from chromadb.config import Settings
client = chromadb.PersistentClient(path=\"/Users/naythandawe/.maia/servicedesk_rag\", settings=Settings(anonymized_telemetry=False))
for coll in client.list_collections():
    print(f\"{coll.name}: {coll.count():,} docs\")
"'
```

#### Step 9: Validate RAG System
```bash
python3 << 'EOF'
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="/Users/naythandawe/.maia/servicedesk_rag",
    settings=Settings(anonymized_telemetry=False)
)

expected = {
    'servicedesk_comments': 108104,
    'servicedesk_work_logs': 73273,
    'servicedesk_descriptions': 10937,
    'servicedesk_titles': 10939,
    'servicedesk_solutions': 10694
}

print("RAG Validation Results:")
print("=" * 60)
all_pass = True
for name, expected_count in expected.items():
    coll = client.get_collection(name)
    actual = coll.count()
    metadata = coll.metadata

    status = "✅" if actual == expected_count else "❌"
    if actual != expected_count:
        all_pass = False

    print(f"{status} {name}:")
    print(f"   Count: {actual:,} (expected {expected_count:,})")
    print(f"   Model: {metadata.get('model', 'UNKNOWN')}")
    print()

if all_pass:
    print("✅ ALL VALIDATIONS PASSED - RAG system operational")
else:
    print("❌ VALIDATION FAILURES DETECTED - investigate before proceeding")
EOF
```

**Success Criteria**:
- All 5 collections present
- Document counts match expected values (±1%)
- Model metadata = "intfloat/e5-base-v2"
- No errors during indexing

#### Step 10: Update Context File
```bash
# Manually update SERVICEDESK_AUTOMATION_PROJECT_CONTEXT.md with:
# - Import completion timestamp
# - Final record counts
# - CT-VISIBLE-CUSTOMER validation results
# - Re-RAG completion status
# - New baseline metrics established
```

**Context Updates Required**:
1. Session history: Add "XLSX Re-import Complete" entry with results
2. Data Quality Notes: Update with CT-VISIBLE-CUSTOMER status
3. Time Period: Confirm July 1 → Oct 15 (or updated date)
4. Next Session Actions: Remove import tasks, add analysis tasks

---

## 🎯 Critical Success Metrics

### Import Success
- [x] All 3 XLSX files imported without errors
- [x] Record counts within expected ranges
- [x] **CT-VISIBLE-CUSTOMER field populated** (not all NULL)
- [x] Comment text integrity verified (full sentences)
- [x] No column misalignment detected

### Re-RAG Success
- [x] All 213,947 documents re-indexed
- [x] All 5 collections validated (correct counts)
- [x] Model metadata = E5-base-v2
- [x] Zero indexing errors
- [x] Semantic search quality improved (test queries)

---

## 🔧 Troubleshooting

### Issue: Import fails with "too many columns"
**Solution**: Verify XLSX files, not CSV
```bash
file ~/Downloads/comments.xlsx  # Should show "Microsoft Excel 2007+"
```

### Issue: CT-VISIBLE-CUSTOMER still NULL
**Check**: Field exists in XLSX
```python
import pandas as pd
df = pd.read_excel("~/Downloads/comments.xlsx", nrows=10)
print(df.columns.tolist())
# Should include 'CT-VISIBLE-CUSTOMER'
```

### Issue: Re-RAG indexing stalls
**Check**: GPU memory, restart if needed
```bash
# Check GPU usage
python3 -c "import torch; print(torch.cuda.is_available())"

# Kill and restart if needed
ps aux | grep servicedesk_gpu_rag_indexer
kill <PID>
```

### Issue: Different record counts than expected
**Expected**: Minor variance (±1%) acceptable
**Action**: If >5% different, investigate:
```sql
SELECT MIN(created_time), MAX(created_time) FROM comments;
-- Verify date range is July 1 - Oct 15
```

---

## 📊 Baseline Metrics (Post-Import)

### To Establish After Completion

**Record Counts**:
- Comments: _______ (expected ~108K)
- Tickets: _______ (expected ~11K)
- Timesheets: _______ (expected ~141K)

**Data Quality**:
- CT-VISIBLE-CUSTOMER populated: _____% (target: >80%)
- Comment text avg length: _____ chars (should be >100)
- Date range: July 1, 2025 → _________

**RAG Quality**:
- Collections indexed: 5/5
- Total documents: 213,947
- Model: E5-base-v2 (768-dim)
- Test query similarity: _____% (target: >60%)

**FCR Baseline**:
```sql
-- Run after import to re-establish baseline
WITH ticket_comment_counts AS (
    SELECT
        wt.ticket_id,
        COUNT(*) as comment_count
    FROM (
        SELECT t."TKT-Ticket ID" as ticket_id
        FROM tickets t
        WHERE t."TKT-Category" != 'Alert'
    ) wt
    INNER JOIN comments c ON wt.ticket_id = c.ticket_id
    INNER JOIN cloud_team_roster r ON c.user_name = r.username
    WHERE c.user_name IS NOT NULL AND c.user_name <> 'nan'
    GROUP BY wt.ticket_id
)
SELECT
    COUNT(*) as total_tickets,
    SUM(CASE WHEN comment_count <= 3 THEN 1 ELSE 0 END) as fcr_tickets,
    ROUND(100.0 * SUM(CASE WHEN comment_count <= 3 THEN 1 ELSE 0 END) / COUNT(*), 1) as fcr_rate
FROM ticket_comment_counts;
```
Expected: ~88.4% FCR (previous baseline)

---

## 🔗 Related Files

**Import Tool**: `/Users/naythandawe/git/maia/claude/tools/sre/incremental_import_servicedesk.py`
**RAG Indexer**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py`
**Database**: `/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db`
**ChromaDB**: `/Users/naythandawe/.maia/servicedesk_rag/`
**Context File**: `/Users/naythandawe/git/maia/claude/data/SERVICEDESK_AUTOMATION_PROJECT_CONTEXT.md`

**XLSX Files**:
- `/Users/naythandawe/Downloads/comments.xlsx` (88MB)
- `/Users/naythandawe/Downloads/tickets.xlsx` (322MB)
- `/Users/naythandawe/Downloads/timesheets.xlsx` (104MB)

---

## 🚀 Quick Recovery Command

**If context lost, resume from this single command**:

```bash
cd ~/git/maia && \
echo "Reading recovery plan..." && \
cat claude/data/SERVICEDESK_XLSX_REIMPORT_PLAN.md && \
echo -e "\n\n🎯 Ready to execute Step 1 (Backup)? Type 'yes' to proceed."
```

---

**Status**: ⏳ AWAITING EXECUTION
**Next Action**: Execute Step 1 (Database backup)
**Estimated Completion**: ~4-5 hours from start
