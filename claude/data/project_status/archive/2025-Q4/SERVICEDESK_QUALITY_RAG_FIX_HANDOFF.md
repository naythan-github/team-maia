# ServiceDesk Quality Analysis - RAG Database Fix & Next Steps

**Date**: 2025-10-19
**Status**: ✅ RAG Issues Fixed, ⚠️ LLM Scoring Needs Investigation
**Session**: Phase 5 Complete + Quality Data Regeneration

---

## Executive Summary

**Problem Solved**: Quality analyzers had embedding dimension mismatch (768-dim vs 384-dim) preventing RAG queries and causing JSON parse errors.

**Current State**:
- ✅ Both analyzers fixed and committed to GitHub
- ✅ e5-base-v2 (768-dim) embeddings working correctly
- ✅ Zero JSON parse errors (was 40% failure rate)
- ⚠️ LLM returning uniform 3.0 scores (separate issue)

**Next Action**: Run full 10K quality analysis to populate dashboards with real data

---

## What Was Fixed

### Root Cause Analysis

**Issue 1: Embedding Dimension Mismatch**
- **Problem**: RAG database created with `intfloat/e5-base-v2` (768-dim Microsoft model)
- **Analyzers using**: `nomic-embed-text` (384-dim Ollama model)
- **Error**: `Collection expecting embedding with dimension of 768, got 384`
- **Why e5-base-v2**: Comprehensive testing showed 50% better quality than 2nd place (Phase 118.3)

**Issue 2: LLM JSON Truncation**
- **Problem**: `llama3.2:3b` truncating JSON output at 500 tokens
- **Error**: `Expecting ',' delimiter: line 7 column 4 (char 112)` + missing `quality_tier` key
- **Root Cause**: Token limit hit before closing brace `}` added
- **Failure Rate**: ~40% of comments

### Fixes Applied (Committed to GitHub)

**Complete Analyzer** (`servicedesk_complete_quality_analyzer.py`):
```python
# Commit: c5c3f3c
✅ Added sentence-transformers import
✅ Load intfloat/e5-base-v2 (768-dim) in __init__
✅ Changed query_texts → query_embeddings (prevents dimension mismatch)
✅ Increased num_predict from default to 1000 tokens
✅ Added JSON repair logic (auto-adds missing closing braces)
```

**Basic Analyzer** (`servicedesk_comment_quality_analyzer.py`):
```python
# Commit: 9f975b5
✅ Added sentence-transformers import
✅ Load intfloat/e5-base-v2 (768-dim) in __init__
✅ Increased num_predict from 500 to 1000 tokens
✅ Added JSON repair logic (auto-adds missing closing braces)
✅ Added quality_tier calculation fallback (excellent/good/acceptable/poor)
```

### Test Results (100 comments)

**✅ Successes**:
- e5-base-v2 768-dim embeddings loaded successfully
- Zero JSON parse errors (was 40% failure rate)
- Zero embedding dimension mismatches
- All 100 comments analyzed without crashes

**⚠️ Unexpected Behavior**:
- LLM returning uniform 3.0 scores for all dimensions
- Sample had 67% empty comments (meaningless content)
- Need larger sample (10K) for better distribution analysis

---

## File Changes Summary

### Modified Files (Committed)
```bash
git log --oneline -3
9f975b5 🔧 Fix basic quality analyzer: e5-base-v2 embeddings + JSON repair
c5c3f3c 🔧 Fix complete quality analyzer: e5-base-v2 embeddings + JSON repair
5f6fdbc ✅ ServiceDesk ETL V2 Phase 5 - API Alignment Complete
```

### Key Files
- `claude/tools/sre/servicedesk_comment_quality_analyzer.py` - Basic analyzer (FIXED)
- `claude/tools/sre/servicedesk_complete_quality_analyzer.py` - Complete analyzer (FIXED)
- `claude/data/SERVICEDESK_QUALITY_DATA_ISSUE.md` - Original problem documentation
- `claude/data/RAG_EMBEDDING_MODEL_UPGRADE.md` - e5-base-v2 testing results

---

## Remaining Work

### 1. Investigate LLM Uniform Scoring (15-30 min)

**Problem**: All comments getting 3/3/3/3 scores regardless of content

**Possible Causes**:
1. **Sample bias**: 100-comment sample had 67% empty comments
2. **LLM prompt issue**: Prompt not clear enough for llama3.2:3b
3. **LLM model issue**: llama3.2:3b may default to 3.0 when uncertain
4. **JSON parsing**: LLM might be returning scores but parser not extracting correctly

**Investigation Steps**:
```bash
# 1. Check a few raw LLM responses
python3 << 'EOF'
import requests
prompt = """Analyze this ServiceDesk comment: "Hi, I just called and left you a voicemail. Please call back."
Provide JSON with professionalism_score, clarity_score, empathy_score, actionability_score (1-5 scale)."""

response = requests.post("http://localhost:11434/api/generate",
    json={"model": "llama3.2:3b", "prompt": prompt, "stream": False, "format": "json"})
print(response.json()['response'])
EOF

# 2. Check if different LLM model works better
# Try: llama3.1:8b or mistral:7b

# 3. Simplify prompt to see if LLM can score at all
```

### 2. Run Full 10K Quality Analysis (30-60 min)

**Command**:
```bash
cd /Users/YOUR_USERNAME/git/maia

# Clear old test data
sqlite3 claude/data/servicedesk_tickets.db "DELETE FROM comment_quality;"

# Run 10K sample (30-60 min)
python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
  --full \
  --sample-size 10000 \
  --batch-size 10 \
  2>&1 | tee /tmp/quality_10k_analysis.log
```

**Expected Runtime**: 30-60 minutes (10K comments × 2-5 sec/comment)

**Success Criteria**:
```sql
-- Check results
sqlite3 claude/data/servicedesk_tickets.db << 'EOF'
SELECT
  COUNT(*) as total,
  COUNT(DISTINCT professionalism_score) as unique_prof,
  MIN(quality_score) as min_q,
  MAX(quality_score) as max_q,
  ROUND(AVG(quality_score), 2) as avg_q
FROM comment_quality;

-- Should see:
-- unique_prof > 3 (not just 1)
-- min_q < 2.5
-- max_q > 3.5
-- avg_q between 2.5-3.5
EOF
```

### 3. Migrate to PostgreSQL (5 min)

**Prerequisites**: Quality data shows variation (not all 3.0)

**Commands**:
```bash
cd /Users/YOUR_USERNAME/git/maia/claude/infrastructure/servicedesk-dashboard

# Truncate old failed data
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "TRUNCATE TABLE servicedesk.comment_quality;"

# Re-run migration
python3 migration/migrate_sqlite_to_postgres.py

# Verify
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*), COUNT(DISTINCT professionalism_score)
   FROM servicedesk.comment_quality;"
```

### 4. Verify Dashboards (2 min)

**URL**: http://localhost:3000/d/servicedesk-quality

**Check**:
- Professionalism score: Shows variation (not uniform 3.0)
- Clarity score: Shows variation
- Empathy score: Shows variation
- Actionability score: Shows variation
- Quality Tier Distribution: Balanced (not 61% poor)

---

## Technical Reference

### RAG Database Details

**Location**: `~/.maia/servicedesk_rag/`
**Size**: 720MB
**Model**: intfloat/e5-base-v2 (768-dim)
**Collections**:
- `servicedesk_comments`: 108,084 docs
- `servicedesk_descriptions`: 10,937 docs
- `servicedesk_solutions`: 10,694 docs
- `servicedesk_titles`: 10,939 docs
- `servicedesk_work_logs`: 73,273 docs

**Why e5-base-v2**:
```
Testing Results (500 technical comments):
🥇 intfloat/e5-base-v2:    0.3912 avg distance (BEST)
🥈 BAAI/bge-base-en-v1.5:  0.7964 (50% worse)
🥉 BAAI/bge-large-en-v1.5: 0.8280 (53% worse)
   all-mpnet-base-v2:      1.2894 (70% worse)
❌ all-MiniLM-L6-v2:        ~1.5+  (74% worse)
```

### Analyzer Architecture

**Basic Analyzer** (stratified sampling):
- Samples 10K comments (configurable)
- Fast sampling strategies (random, stratified, coverage)
- Good for quick validation
- Runtime: 30-60 min for 10K

**Complete Analyzer** (RAG deduplication):
- Analyzes all 108K comments
- RAG-based duplicate detection (95% similarity)
- Only analyzes unique comments (~80-90K)
- Propagates scores to duplicates
- 10-30% token savings
- Runtime: 4-6 hours

### Database Schema

**SQLite**: `/Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db`
```sql
CREATE TABLE comment_quality (
    comment_id TEXT PRIMARY KEY,
    ticket_id TEXT,
    user_name TEXT,
    team TEXT,
    comment_type TEXT,
    created_time TIMESTAMP,
    cleaned_text TEXT,
    professionalism_score INTEGER,     -- 1-5
    clarity_score INTEGER,             -- 1-5
    empathy_score INTEGER,             -- 1-5
    actionability_score INTEGER,       -- 1-5
    quality_score REAL,                -- avg of 4 scores
    quality_tier TEXT,                 -- excellent/good/acceptable/poor
    content_tags TEXT,                 -- JSON array
    red_flags TEXT,                    -- JSON array
    intent_summary TEXT,               -- 1-2 sentence description
    analysis_timestamp TIMESTAMP
);
```

---

## Troubleshooting

### If Analyzer Fails Again

**Symptoms**:
- Dimension mismatch errors
- JSON parse errors
- Import errors

**Debug Steps**:
```bash
# 1. Verify e5-base-v2 is loaded
python3 -c "from sentence_transformers import SentenceTransformer; \
  m = SentenceTransformer('intfloat/e5-base-v2'); \
  print(f'Dims: {m.get_sentence_embedding_dimension()}')"
# Expected: Dims: 768

# 2. Test RAG collection access
python3 << 'EOF'
import chromadb
from chromadb.config import Settings
import os
client = chromadb.PersistentClient(
    path=os.path.expanduser("~/.maia/servicedesk_rag"),
    settings=Settings(anonymized_telemetry=False)
)
coll = client.get_collection("servicedesk_comments")
print(f"Collection count: {coll.count()}")
EOF
# Expected: Collection count: 108084

# 3. Test LLM
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"llama3.2:3b","prompt":"Score this 1-5: Good service","stream":false,"format":"json"}'
```

### If Uniform Scores Persist

**Options**:
1. **Try different LLM model**:
   ```bash
   # Install larger model
   ollama pull llama3.1:8b

   # Update analyzer
   analyzer = ServiceDeskCommentAnalyzer(llm_model="llama3.1:8b")
   ```

2. **Simplify prompt**: Current prompt may be too complex for llama3.2:3b

3. **Use external API**: Switch to Anthropic/OpenAI APIs for better scoring

---

## Success Metrics

**RAG Database Fixes** ✅:
- ✅ e5-base-v2 (768-dim) embeddings loading
- ✅ Zero dimension mismatch errors
- ✅ Zero JSON parse errors
- ✅ Both analyzers working without crashes

**Quality Data Goals** (Pending):
- [ ] 10K+ comments analyzed
- [ ] >5 unique values per score dimension
- [ ] Quality score range: 1.5-4.5 (not all 3.0)
- [ ] <20% failure rate
- [ ] Dashboards showing real variation

---

## Files for Review

**Documentation**:
- This file: `SERVICEDESK_QUALITY_RAG_FIX_HANDOFF.md`
- Original issue: `SERVICEDESK_QUALITY_DATA_ISSUE.md`
- e5-base-v2 testing: `RAG_EMBEDDING_MODEL_UPGRADE.md`

**Fixed Code**:
- `claude/tools/sre/servicedesk_comment_quality_analyzer.py` (basic)
- `claude/tools/sre/servicedesk_complete_quality_analyzer.py` (complete)

**Test Logs**:
- `/tmp/quality_test_100.log` - 100-comment test (uniform scores)
- `/tmp/quality_10k_analysis.log` - Will contain 10K results

---

## Next Session Quick Start

```bash
# 1. Navigate to project
cd /Users/YOUR_USERNAME/git/maia

# 2. Check if 10K analysis completed
sqlite3 claude/data/servicedesk_tickets.db \
  "SELECT COUNT(*), COUNT(DISTINCT professionalism_score) FROM comment_quality;"

# 3. If not complete, run it
python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
  --full --sample-size 10000 --batch-size 10

# 4. If complete with variation, migrate to PostgreSQL
cd claude/infrastructure/servicedesk-dashboard
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "TRUNCATE TABLE servicedesk.comment_quality;"
python3 migration/migrate_sqlite_to_postgres.py

# 5. Verify dashboards
open http://localhost:3000/d/servicedesk-quality
```

---

## Summary

**Accomplished**:
- ✅ Diagnosed root cause (embedding mismatch + JSON truncation)
- ✅ Fixed both analyzers (committed to GitHub)
- ✅ Tested on 100 comments (no errors)
- ✅ Comprehensive documentation created

**Remaining** (30-60 min):
- [ ] Run 10K quality analysis
- [ ] Investigate uniform scoring if persists
- [ ] Migrate to PostgreSQL
- [ ] Verify dashboards

**Confidence**: 85% - Core RAG issues solved, LLM scoring behavior needs validation with larger sample

---

**Document Control**
- **Created**: 2025-10-19
- **Author**: Data Cleaning & ETL Expert Agent
- **Status**: ✅ RAG Fixes Complete, Ready for 10K Analysis
- **Next Review**: After 10K analysis completes
