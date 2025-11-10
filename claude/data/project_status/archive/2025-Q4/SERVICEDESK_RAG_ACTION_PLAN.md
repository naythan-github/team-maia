# ServiceDesk RAG Optimization - Action Plan

**Created**: 2025-10-15
**Status**: IN PROGRESS
**Goal**: Complete RAG indexing + intelligent LLM analysis with minimum token usage

---

## 🎯 Optimal Sequence for Best Outcome + Minimum Tokens

### Phase 1: Complete RAG Indexing (ZERO tokens)
**Status**: 🔄 IN PROGRESS
**Time**: ~10-15 minutes
**Token Cost**: $0 (embedding model only, no LLM)

**Tasks**:
1. ✅ Fix indexer field name bug (metadata access)
2. ⏳ Index all 5 collections:
   - `descriptions` - Ticket problem descriptions (10,937 entries, avg 1,266 chars)
   - `solutions` - Ticket resolutions (10,694 entries, avg 51 chars)
   - `titles` - Ticket titles (10,939 entries, 65.7% unique)
   - `work_logs` - Timesheet descriptions (73,273 entries, avg 138 chars)
   - `comments` - Complete comments (108,129 total, currently 6,486)
3. ⏳ Verify with `--stats`

**Command**:
```bash
cd ~/git/maia
python3 claude/tools/sre/servicedesk_multi_rag_indexer.py --index-all --batch-size 100
```

**Output**: Complete searchable vector database across all ServiceDesk text fields

---

### Phase 2: RAG-Optimized LLM Analysis (95% token reduction)
**Status**: ⏳ PENDING
**Time**: ~30-60 minutes
**Token Cost**: ~$0.75-$1.50 (vs $15-20 naive approach)

**Strategy**: Use RAG to cluster similar comments, sample intelligently

**Tasks**:
1. ⏳ Cluster comments using ChromaDB similarity search
2. ⏳ Sample 1 representative comment per cluster
3. ⏳ LLM quality analysis on samples only (5-10K instead of 108K)
4. ⏳ Extrapolate quality scores to cluster members
5. ⏳ Validate with spot checks

**Why This Works**:
- Comments cluster by patterns (alert notifications, handoffs, resolutions)
- Analyzing 1 "Azure portal issue" comment = understand all similar ones
- 95% token savings while maintaining 95% effective coverage

**Implementation**:
```python
# Pseudo-code
clusters = chromadb.cluster_comments(min_similarity=0.85)
samples = [cluster.get_representative() for cluster in clusters]
for sample in samples:
    quality = llm.analyze(sample.text)
    cluster.propagate_quality(quality)
```

---

### Phase 3: Service Desk Manager Analysis (Targeted queries)
**Status**: ⏳ PENDING
**Time**: On-demand
**Token Cost**: Minimal (targeted queries only)

**Capabilities Enabled**:
- "Find all tickets similar to this complaint" → RAG retrieves relevant context
- "Show me escalation patterns for Azure issues" → RAG filters by similarity
- "What are common handoff problems?" → RAG clusters patterns
- Service Desk Manager analyzes only what's relevant (not all 108K)

**Use Cases**:
1. Customer complaint investigation
2. Pattern detection for automation
3. Agent coaching with specific examples
4. Root cause analysis with similar incidents

---

## 📊 Token Usage Comparison

| Approach | Comments Analyzed | Token Cost | Coverage | Outcome |
|----------|------------------|------------|----------|---------|
| **Naive** (all 108K) | 108,000 | ~$15-20 | 100% | Expensive, slow |
| **RAG-optimized** (cluster sampling) | 5,000-10,000 | ~$0.75-$1.50 | 95% effective | ✅ OPTIMAL |
| **Current** (random 517) | 517 | $0 | 0.5% | Incomplete, skewed by "brian" |

---

## 🔧 Current Issues to Fix

### Issue 1: Indexer Field Access Bug
**Location**: `servicedesk_multi_rag_indexer.py:209`
**Error**: `IndexError: No item with that key`
**Cause**: Metadata fields with brackets `[TKT-Title]` not accessible via `row[field]`
**Fix**: Access using row index or clean field names in SELECT

### Issue 2: Incomplete Comments Collection
**Current**: 6,486 of 108,129 comments indexed (6%)
**Reason**: Previous run stopped at 38.6% progress
**Fix**: Resume indexing with deduplication check

### Issue 3: LLM Quality Analyzer JSON Errors
**Location**: `servicedesk_comment_quality_analyzer.py`
**Error**: `KeyError: 'quality_tier'` at 84% progress
**Status**: Deferred until Phase 2 (after RAG complete)

---

## 📁 File Locations

**New Files**:
- Indexer: `~/git/maia/claude/tools/sre/servicedesk_multi_rag_indexer.py`
- Action Plan: `~/git/maia/claude/data/SERVICEDESK_RAG_ACTION_PLAN.md` (this file)

**ChromaDB Collections**:
- Path: `~/.maia/servicedesk_rag/`
- Collections:
  - `servicedesk_comments` (6,486 → target 108,129)
  - `servicedesk_descriptions` (target 10,937)
  - `servicedesk_solutions` (target 10,694)
  - `servicedesk_titles` (target 10,939)
  - `servicedesk_work_logs` (target 73,273)

**Existing Assets**:
- Database: `~/git/maia/claude/data/servicedesk_tickets.db`
- Quality Analyzer: `~/git/maia/claude/tools/sre/servicedesk_comment_quality_analyzer.py`
- Service Desk Manager Agent: `~/git/maia/claude/agents/service_desk_manager_agent.md`

---

## 🎯 Success Metrics

**Phase 1 Complete When**:
- ✅ All 5 collections indexed
- ✅ Total documents: ~214K (108K comments + 11K descriptions + 11K solutions + 11K titles + 73K work_logs)
- ✅ ChromaDB stats show expected counts
- ✅ Sample searches return relevant results

**Phase 2 Complete When**:
- ✅ Quality scores for 5-10K representative comments
- ✅ Cluster coverage validated (95%+ of comments mapped to clusters)
- ✅ Agent performance metrics calculated (excluding "brian" system account)
- ✅ Identified problem agents with specific examples

**Phase 3 Complete When**:
- ✅ Service Desk Manager can query across all collections
- ✅ Multi-collection search working (title + description + solution)
- ✅ Complaint analysis workflow validated end-to-end

---

## 🔄 Recovery Instructions

**If context is lost, resume from**:
1. Read this file: `~/git/maia/claude/data/SERVICEDESK_RAG_ACTION_PLAN.md`
2. Check progress: `python3 claude/tools/sre/servicedesk_multi_rag_indexer.py --stats`
3. Continue: Find next pending task in action plan above
4. Context files:
   - `~/git/maia/claude/data/SERVICEDESK_ETL_PROJECT.md` (Phase 118 - data infrastructure)
   - `~/git/maia/claude/agents/service_desk_manager_agent.md` (agent capabilities)

---

**Next Immediate Action**: Fix indexer bug and run `--index-all`
