# Quality Analysis 10K - In Progress

**Date**: 2025-10-19
**Status**: 🔄 RUNNING IN BACKGROUND
**PID**: 20386
**Log**: `/tmp/quality_10k_final.log`

---

## Current Status

✅ **Analyzer Started**: PID 20386 running with FIXED code
✅ **Model Loaded**: e5-base-v2 (768-dim) loaded successfully
✅ **Quality Data Cleared**: Starting fresh (0 rows)
🔄 **In Progress**: Analyzing 10,000 comments with batch size 10

**Expected Runtime**: 30-60 minutes (10K comments × 2-5 sec/comment)

---

## Monitor Progress

```bash
# Check if still running
ps aux | grep "20386" | grep -v grep

# Monitor log output
tail -f /tmp/quality_10k_final.log

# Check database progress
sqlite3 /Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db \
  "SELECT COUNT(*) as analyzed FROM comment_quality;"

# Monitor with watch (updates every 5 seconds)
watch -n 5 'sqlite3 /Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db \
  "SELECT COUNT(*) as analyzed FROM comment_quality;"'
```

---

## When Complete

### Step 1: Validate Results

```bash
sqlite3 /Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db << 'EOF'
SELECT
  COUNT(*) as total,
  COUNT(DISTINCT professionalism_score) as unique_prof,
  COUNT(DISTINCT clarity_score) as unique_clarity,
  MIN(quality_score) as min_q,
  MAX(quality_score) as max_q,
  ROUND(AVG(quality_score), 2) as avg_q,
  SUM(CASE WHEN intent_summary LIKE '%failed%' THEN 1 ELSE 0 END) as failures
FROM comment_quality;

-- Check quality tier distribution
SELECT quality_tier, COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM comment_quality), 1) as pct
FROM comment_quality
GROUP BY quality_tier
ORDER BY CASE quality_tier
  WHEN 'excellent' THEN 1
  WHEN 'good' THEN 2
  WHEN 'acceptable' THEN 3
  WHEN 'poor' THEN 4
END;
EOF
```

**Success Criteria**:
- ✅ Total ≥ 9,000 (90%+ completion)
- ✅ unique_prof > 3 (showing variation, not all 3.0)
- ✅ min_q < 2.5
- ✅ max_q > 3.5
- ✅ avg_q between 2.5-3.5
- ✅ Failures < 20%

### Step 2: Migrate to PostgreSQL

**If results show variation** (not all uniform 3.0 scores):

```bash
cd /Users/YOUR_USERNAME/git/maia/claude/infrastructure/servicedesk-dashboard

# Clear old failed data
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "TRUNCATE TABLE servicedesk.comment_quality;"

# Migrate
python3 migration/migrate_sqlite_to_postgres.py

# Verify
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*), COUNT(DISTINCT professionalism_score)
   FROM servicedesk.comment_quality;"
```

### Step 3: Verify Dashboards

Visit: http://localhost:3000/d/servicedesk-quality

**Check**:
- Professionalism score shows variation (not flat 3.0)
- Clarity score shows variation
- Empathy score shows variation
- Actionability score shows variation
- Quality Tier Distribution is balanced (not 61% poor)

---

## If Uniform Scores Persist

**If validation shows all 3.0 scores still**:

### Investigate LLM Behavior

```bash
# Test LLM directly
python3 << 'EOF'
import requests
import json

comment = "Hi, I called and left a voicemail. Please call back when you can. Thanks!"

prompt = f"""Analyze this ServiceDesk comment and score 1-5:
Comment: "{comment}"

Provide JSON with professionalism_score, clarity_score, empathy_score, actionability_score."""

response = requests.post("http://localhost:11434/api/generate",
    json={
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_predict": 1000}
    })

print(response.json()['response'])
EOF
```

**Expected**: JSON with varied scores (not all 3)

**If LLM returns all 3s**:
1. Try larger model: `ollama pull llama3.1:8b`
2. Update analyzer to use llama3.1:8b
3. Or switch to external API (Anthropic/OpenAI)

---

## Background Process Management

### Check Process Status
```bash
# Is it running?
ps aux | grep "20386" | grep -v grep

# CPU and memory usage
ps aux | grep "20386" | grep -v grep | awk '{print "CPU:", $3"%", "MEM:", $4"%"}'

# Running time
ps -p 20386 -o etime=
```

### Kill If Needed
```bash
# Graceful
kill 20386

# Force (if graceful fails)
kill -9 20386
```

---

## Analyzer Configuration

**Using FIXED Code** (committed to GitHub):
- ✅ sentence-transformers with e5-base-v2 (768-dim)
- ✅ num_predict: 1000 tokens (prevents JSON truncation)
- ✅ JSON repair logic (auto-adds missing braces)
- ✅ quality_tier calculation fallback

**Command Used**:
```bash
python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
  --full \
  --sample-size 10000 \
  --batch-size 10 \
  > /tmp/quality_10k_final.log 2>&1 &
```

---

## Troubleshooting

### Process Appears Stuck

**Symptoms**: Log file not growing, CPU near 0%

**Check**:
```bash
# Python output is buffered - force flush
python3 -u claude/tools/sre/servicedesk_comment_quality_analyzer.py \
  --full --sample-size 10000 --batch-size 10
```

### ChromaDB Issues

**Symptoms**: Hangs during initialization

**Solution**:
```bash
# Check ChromaDB
ls -lh ~/.maia/servicedesk_rag/
# Should see chroma.sqlite3 (~720MB)

# If corrupted, may need to rebuild (4-6 hours)
# Use GPU indexer:
python3 claude/tools/sre/servicedesk_gpu_rag_indexer.py --all
```

---

## Files Reference

**Analyzer**: `claude/tools/sre/servicedesk_comment_quality_analyzer.py` (FIXED)
**Database**: `/Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db`
**Log**: `/tmp/quality_10k_final.log`
**Process**: PID 20386

**Documentation**:
- `SERVICEDESK_QUALITY_RAG_FIX_HANDOFF.md` - Complete technical handoff
- `SESSION_SUMMARY_2025-10-19.md` - Session summary

---

**Status**: 🔄 Analysis running in background, check periodically
**Next Check**: 15-20 minutes (should have 2K-4K comments analyzed)

