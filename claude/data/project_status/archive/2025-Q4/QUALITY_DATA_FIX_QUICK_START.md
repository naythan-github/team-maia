# Quality Data Fix - Quick Start Guide

**Status**: ⏸️ Run AFTER pipeline update completes

---

## TL;DR

Quality Dashboard shows uniform 3.0 scores because 96.5% of the October 14 analysis failed. Need to re-run quality analyzer to get real data.

---

## One-Command Fix (Recommended)

```bash
cd /Users/YOUR_USERNAME/git/maia

# Run complete quality analyzer (4-6 hours, can run overnight)
python3 claude/tools/sre/servicedesk_complete_quality_analyzer.py \
  --full \
  --similarity 0.95 \
  --batch-size 10
```

**Then migrate to PostgreSQL:**

```bash
cd claude/infrastructure/servicedesk-dashboard

# Clear old data
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "TRUNCATE TABLE servicedesk.comment_quality;"

# Migrate new data
python3 migration/migrate_sqlite_to_postgres.py
```

**Then verify:**
- Open http://localhost:3000/d/servicedesk-quality
- Check if scores vary (not all 3.0)
- Quality tier should show balanced distribution (not 61% poor)

---

## What Happened?

**October 14, 2025**: Quality analysis run on 517 comments
- **Failed**: 499 comments (96.5%) → defaulted to 3.0 scores
- **Succeeded**: 18 comments (3.5%)
- **Result**: Uniform 3.0 across all dimensions = useless data

**Why**: LLM couldn't analyze most comments (empty/meaningless content or analysis errors)

---

## Quick Validation

**Check current state:**
```bash
sqlite3 /Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db \
  "SELECT COUNT(DISTINCT professionalism_score) FROM comment_quality;"
# Should return: 1 (BAD - means all same value)
```

**After re-analysis:**
```bash
sqlite3 /Users/YOUR_USERNAME/git/maia/claude/data/servicedesk_tickets.db \
  "SELECT COUNT(DISTINCT professionalism_score) FROM comment_quality;"
# Should return: >5 (GOOD - means real variation)
```

---

## Alternative: Quick Test (30-60 min)

If you want to test first before full run:

```bash
python3 claude/tools/sre/servicedesk_comment_quality_analyzer.py \
  --full \
  --sample-size 10000 \
  --batch-size 10
```

Trade-off: Only 10K comments analyzed vs 100K, but faster validation.

---

## Full Details

See: `/Users/YOUR_USERNAME/git/maia/claude/data/SERVICEDESK_QUALITY_DATA_ISSUE.md`

---

**Created**: 2025-10-19
**Status**: Ready to run after pipeline update
