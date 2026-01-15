# RAG Embedding Quality A/B Testing Guide

**Created**: 2025-10-15
**Tool**: `claude/tools/sre/rag_embedding_quality_test.py`
**Purpose**: Compare Ollama vs GPU embedding quality for L3/L4 technical content

---

## Why Test Quality?

### The Question
**User**: "Given that there are updates from level 3 and 4, there may be more technical communication. For future reference would it be worth doing a side by side test?"

### The Answer
**YES** - Absolutely worth testing because:

1. **L3/L4 Technical Vocabulary**: Advanced troubleshooting uses specialized terms (VMware, Azure AD, SCOM, ESEUTIL, etc.) that may be better captured by higher-dimensional embeddings (768-dim vs 384-dim)

2. **Context Preservation**: Complex technical descriptions have more semantic nuance than basic "password reset" tickets

3. **Accuracy vs Speed Trade-off**: If 384-dim GPU embeddings lose 10%+ accuracy on technical queries, the 6.5x speedup may not be worth it

4. **Data-Driven Decision**: Rather than assumptions, test with real ServiceDesk queries

---

## Test Methodology

### Test Categories

**9 test queries across technical depth:**

| Category | Example Query | Level | Expected Complexity |
|----------|--------------|-------|-------------------|
| Infrastructure | "DNS resolution failure on domain controller" | L3 | High technical precision required |
| Security | "Azure AD conditional access policy blocking" | L4 | Advanced identity/access terms |
| Application | "Exchange mailbox database corruption" | L4 | Application-specific vocabulary |
| Performance | "SQL Server high CPU query timeouts" | L3/L4 | Performance analysis terms |
| Virtualization | "VMware vMotion failing network latency" | L4 | Platform-specific features |
| Storage | "RAID array degraded after disk failure" | L3 | Infrastructure hardware terms |
| Backup | "Veeam backup job stuck in starting state" | L3 | Backup/recovery vocabulary |
| Monitoring | "SCOM agent not reporting to server" | L3 | Monitoring tool specifics |
| Basic | "password reset for locked account" | L1 | Control test (should be equal) |

### Metrics

**1. Term Precision**
- Expected technical terms per query (e.g., "DNS", "domain controller", "resolution", "AD")
- Measure: What % of expected terms appear in top 5 search results?
- **Goal**: Both models should score >80% for L3/L4 queries

**2. Average Distance**
- ChromaDB distance score (lower = better match)
- Compare: Are GPU results significantly worse (higher distance)?
- **Threshold**: <10% difference acceptable

**3. Semantic Accuracy**
- Do top results actually answer the query?
- Manual review of top 3 results per query
- **Goal**: Both models return relevant technical content

---

## Running the Test

### Prerequisites

**Required**: Both Ollama and GPU collections must be fully indexed

```bash
# Check collection status
python3 -c "
import chromadb
from chromadb.config import Settings
client = chromadb.PersistentClient(
    path='/Users/YOUR_USERNAME/.maia/servicedesk_rag',
    settings=Settings(anonymized_telemetry=False)
)
for col in client.list_collections():
    print(f'{col.name}: {col.count():,} documents')
"
```

**Expected output:**
```
servicedesk_comments: 108,129 documents (Ollama 768-dim)
servicedesk_descriptions: 10,937 documents (GPU 384-dim)
servicedesk_solutions: 10,694 documents (GPU 384-dim)
servicedesk_titles: 10,939 documents (GPU 384-dim)
servicedesk_work_logs: 73,273 documents (GPU 384-dim)
```

### Run Quality Test

**Basic test (9 technical queries)**:
```bash
cd ~/git/maia
python3 claude/tools/sre/rag_embedding_quality_test.py --test relevance
```

**Full test (relevance + duplicates)**:
```bash
python3 claude/tools/sre/rag_embedding_quality_test.py --test all
```

**Output location**:
```
claude/data/rag_quality_test_results.json
```

---

## Interpreting Results

### Scenario 1: Equivalent Quality (Most Likely)

**Result**: GPU precision within 5% of Ollama

```
OVERALL RESULTS
Ollama (768-dim):  Average precision: 82.3%
GPU (384-dim):     Average precision: 80.1%
Difference: -2.2%

✅ VERDICT: Equivalent quality (< 5% difference)
   → GPU recommended (6.5x faster, 50% storage savings)
```

**Decision**: Use GPU for all collections
**Rationale**: 2% precision difference negligible vs 6.5x speed gain

---

### Scenario 2: GPU Superior (Possible)

**Result**: GPU precision >5% better than Ollama

```
OVERALL RESULTS
Ollama (768-dim):  Average precision: 78.5%
GPU (384-dim):     Average precision: 85.2%
Difference: +6.7%

✅ VERDICT: GPU superior (+6.7% better precision)
   → GPU strongly recommended
```

**Decision**: Use GPU for all collections
**Rationale**: GPU faster AND more accurate (distillation win)

---

### Scenario 3: Ollama Superior (Unlikely but Possible)

**Result**: Ollama precision >5% better than GPU

```
OVERALL RESULTS
Ollama (768-dim):  Average precision: 88.4%
GPU (384-dim):     Average precision: 76.1%
Difference: -12.3%

⚠️  VERDICT: Ollama superior (12.3% better precision)
   → Consider Ollama for L3/L4 technical content
```

**Decision**: Mixed strategy
- **Comments**: Ollama (highest technical depth)
- **Descriptions**: Ollama (problem descriptions critical)
- **Titles/Solutions/Work logs**: GPU (less critical, speed prioritized)

**Trade-off**:
- 12% better accuracy on technical queries
- 6.5x slower indexing
- 2x more storage

---

## Current Status (2025-10-15)

### Decision Made
**Selected**: GPU (all-MiniLM-L6-v2, 384-dim) for 4 collections based on:
- ✅ Proven at Google/Microsoft scale for semantic search
- ✅ Optimized for similarity tasks (your use case)
- ✅ 6.5x faster indexing (97 vs 15 docs/sec)
- ✅ 50% storage savings
- ✅ Research shows equivalent quality for general technical content

### Hybrid Approach In Use
- **Comments** (108K): Ollama 768-dim (already indexed, serial)
- **Descriptions** (11K): GPU 384-dim (L3/L4 problem descriptions)
- **Solutions** (11K): GPU 384-dim (resolution text)
- **Titles** (11K): GPU 384-dim (short summaries)
- **Work logs** (73K): GPU 384-dim (timesheet descriptions)

### Testing Recommendation
**When to run A/B test**:
1. ✅ **All indexing complete** (serial + GPU processes finished)
2. ✅ **Before committing to GPU for future re-indexing**
3. ✅ **If L3/L4 users report poor search results**
4. ✅ **Before scaling to other ServiceDesk instances**

**Current ETA**: ~10 minutes (work_logs collection completing)

---

## Next Steps

### 1. Wait for Indexing Completion
```bash
# Monitor progress
tail -f ~/servicedesk_rag_indexing_full.log
```

### 2. Run Quality Test
```bash
python3 claude/tools/sre/rag_embedding_quality_test.py --test relevance
```

### 3. Review Results
```bash
# View detailed results
cat claude/data/rag_quality_test_results.json | python3 -m json.tool
```

### 4. Decide Strategy
Based on test results:
- **<5% diff**: Continue GPU for all ✅
- **5-10% diff**: Re-test with larger sample
- **>10% diff**: Consider hybrid (Ollama for comments/descriptions, GPU for rest)

### 5. Document Decision
Update this file with:
- Test date
- Results summary
- Final embedding strategy
- Lessons learned

---

## Advanced Testing (Future)

### Production Quality Monitoring

**Track over time:**
- User search success rate (clicks on top 3 results)
- Support ticket deflection (RAG finds solution without ticket)
- L3/L4 engineer feedback on semantic search quality

**Metrics to instrument:**
```python
# In ServiceDesk Manager Agent
def track_search_quality(query, results, user_action):
    """Log: query → top results → user clicked position"""
    # Identifies when search quality degrades
```

### Domain-Specific Fine-Tuning (Advanced)

If standard models insufficient:
- Fine-tune sentence-transformers on 108K ServiceDesk comments
- Train on (ticket description, solution) pairs
- Specialized for your technical vocabulary
- **Cost**: ~$50-100 GPU time, 2-3 hours training

---

## Reference Implementation

**Test Tool**: `claude/tools/sre/rag_embedding_quality_test.py`
- 9 technical query categories
- Automated precision calculation
- JSON output for tracking over time
- Extensible for custom test queries

**Add your own queries:**
```python
# Edit get_technical_test_queries() method
{
    "category": "YourCategory",
    "query": "Your technical query here",
    "expected_terms": ["term1", "term2", "term3"],
    "description": "L3/L4 specific issue"
}
```

---

## Conclusion

**Yes, side-by-side testing is worth it** for L3/L4 technical content because:

1. ✅ **Risk mitigation**: Validates 384-dim maintains quality
2. ✅ **Data-driven**: Removes guesswork about technical vocabulary
3. ✅ **Optimization opportunity**: May discover GPU actually better for your domain
4. ✅ **Documentation**: Creates baseline for future quality monitoring

**Recommended**: Run test after current indexing completes (~10 min) to validate GPU choice for future re-indexing decisions.
