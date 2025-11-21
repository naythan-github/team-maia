# Additional RAG Indexing Candidates Analysis

**Created**: 2025-10-15
**Context**: Post-GPU RAG implementation - identifying high-value fields for semantic search

---

## Executive Summary

**Question**: "Are there any other fields worth RAGing now we have the GPU ragging process?"

**Answer**: **YES - 1 high-value collection identified**

**Recommendation**: Add `sla_breach_explanations` collection (347 documents, avg 54 chars, highly valuable context)

---

## Currently Indexed Collections

✅ **Already RAG-indexed** (5 collections, 214K documents):

| Collection | Documents | Avg Length | Model | Status |
|------------|-----------|------------|-------|--------|
| comments | 108,129 | 609 chars | Ollama 768-dim | ✅ Complete |
| descriptions | 10,937 | 1,266 chars | GPU 384-dim | ✅ Complete |
| solutions | 10,694 | 51 chars | GPU 384-dim | ✅ Complete |
| titles | 10,939 | 59 chars | GPU 384-dim | ✅ Complete |
| work_logs | 73,273 | 138 chars | GPU 384-dim | ⏳ Completing |

---

## Additional Candidates Analyzed

### 1. ✅ **SLA Breach Comments** - HIGH VALUE

**Field**: `TKT-SLA Breach Comment`
**Count**: 347 documents (0.3% of tickets)
**Unique**: 298 unique (85.9%)
**Avg Length**: 54 characters (~8 words)
**Max Length**: 731 characters (~110 words)

**Why Valuable:**
- **Escalation context**: Explains WHY SLAs were breached
- **Process improvement**: Identifies systemic issues
- **L3/L4 insights**: Complex problems that took longer than expected
- **Customer impact**: Severity of delays documented

**Sample content:**
```
"KB5056579 is a cumulative update for the .NET Framework 3.5 and 4.8.1,
specifically targeting Windows 11 version 24H2. Released on April 25, 2025,
this update focuses on quality and reliability fixes..."

"Whitelisting was completed in Airlock, but did not work as expected.
It needs to be done via the File path. Liaised with Security Team and
actioned, worked on Test device..."
```

**Use Cases:**
- Find similar SLA breach scenarios
- Identify patterns in escalations
- Training material for handling complex tickets
- Post-incident analysis

**Recommendation**: ✅ **Index as `sla_breach_explanations` collection**

---

### 2. ⚠️ **Root Cause Categories** - LOW VALUE (Skip)

**Field**: `TKT-Root Cause Category`
**Count**: 10,914 documents
**Unique**: 22 unique (0.2%)
**Avg Length**: 10 characters

**Why Skip:**
- **Too categorical**: Only 22 unique values (e.g., "User Error", "Configuration", "Hardware")
- **No semantic richness**: Short labels, not descriptive text
- **Better as metadata**: Filter field, not search target
- **Already captured**: Root causes explained in descriptions/solutions

**Example values:**
- "User Error"
- "Configuration Issue"
- "Hardware Failure"
- "Software Bug"

**Recommendation**: ❌ **Skip - Use as metadata filter instead**

---

### 3. ⚠️ **SLA Breach Reasons** - LOW VALUE (Skip)

**Field**: `TKT-SLA Breach Reason`
**Count**: 5,562 documents
**Unique**: 8 unique (0.1%)
**Avg Length**: 10 characters

**Why Skip:**
- **Extremely categorical**: Only 8 unique values
- **Predefined list**: "Awaiting Customer", "Awaiting Vendor", "High Volume", etc.
- **No semantic content**: Labels, not explanatory text
- **Better as filter**: Classification field

**Recommendation**: ❌ **Skip - Use as metadata filter**

---

### 4. ❌ **Related CI** - NEGLIGIBLE (Skip)

**Field**: `TKT-Related CI`
**Count**: 1 document
**Unique**: 1 unique
**Avg Length**: 37 characters

**Why Skip:**
- **Nearly empty**: Only 1 entry in entire database
- **Not populated**: Field exists but unused

**Recommendation**: ❌ **Skip - Insufficient data**

---

## Additional Analysis: Comment Types

### Can You Tell Customer vs Internal Communication?

**YES!** ✅ **`comment_type` field tracks visibility**

Already indexed in `comments` collection with metadata:

| Type | Count | % | Avg Length | Purpose |
|------|-------|---|------------|---------|
| **`comments`** | 16,620 | 15.4% | 2,028 chars | Customer-facing updates |
| **`worknotes`** | 10,413 | 9.6% | 980 chars | Internal L3/L4 technical notes |
| **`system`** | 81,071 | 75.0% | 271 chars | Auto-generated events |

**Key Insight**: Customer comments are 2x longer than internal notes (polished vs technical)

**Usage**:
```python
# Query customer-facing communications only
results = collection.query(
    query_texts=["how to explain outage to customer"],
    where={"comment_type": "comments"}
)

# Query internal technical troubleshooting
results = collection.query(
    query_texts=["DNS resolution troubleshooting"],
    where={"comment_type": "worknotes"}
)
```

---

## Recommendation: Add ONE Collection

### **Proposed Addition**: `sla_breach_explanations`

**Justification:**
1. ✅ **High value, low volume**: 347 documents = ~4 seconds GPU indexing
2. ✅ **Unique content**: 298 unique explanations (85.9%)
3. ✅ **Semantic richness**: Average 54 chars, max 731 chars
4. ✅ **Critical context**: Explains complex escalations
5. ✅ **L3/L4 knowledge**: Advanced troubleshooting scenarios

**Implementation:**

```python
# Add to servicedesk_gpu_rag_indexer.py collections
self.collections = {
    # ... existing 5 collections ...
    "sla_breach_explanations": {
        "description": "SLA breach context and escalation explanations (347 entries)",
        "table": "tickets",
        "id_field": "[TKT-Ticket ID]",
        "text_field": "[TKT-SLA Breach Comment]",
        "metadata_fields": [
            "[TKT-Title]",
            "[TKT-Severity]",
            "[TKT-Category]",
            "[TKT-SLA Breach Reason]",  # Categorical reason
            "[TKT-Team]",
            "[TKT-Created Time]"
        ]
    }
}
```

**Indexing Time**: ~4 seconds on GPU (347 docs @ 97 docs/sec)

**Use Cases:**
- "Find similar SLA breaches involving .NET updates"
- "What caused previous Airlock whitelisting delays?"
- "Show me escalations related to vendor dependencies"
- "Analyze patterns in L3/L4 SLA misses"

---

## Fields NOT Worth Indexing

### Metadata/Categorical Fields (Use as Filters)

Better used as `where` clauses in queries, not search targets:

- ❌ `TKT-Root Cause Category` (22 categories)
- ❌ `TKT-SLA Breach Reason` (8 reasons)
- ❌ `TKT-Severity` (3-4 levels)
- ❌ `TKT-Status` (10-15 statuses)
- ❌ `TKT-Category` (50-100 categories)
- ❌ `TKT-Team` (team names)
- ❌ `TKT-Platform` (platform names)

**Why Skip**: Short labels with no semantic content - better as metadata filters

### Empty/Sparse Fields

- ❌ `TKT-Related CI` (1 entry)
- ❌ `visible_to_customer` (NULL for all)

**Why Skip**: Insufficient data

---

## Performance Impact

### Current System
- **5 collections**: 214K documents
- **Indexing time**: ~12 minutes (hybrid Ollama/GPU)
- **Storage**: ~400MB embeddings

### With SLA Breach Addition
- **6 collections**: 214,347 documents (+0.16%)
- **Additional indexing time**: +4 seconds
- **Additional storage**: +0.5MB

**Impact**: Negligible (~0.2% increase)

---

## Alternative: Enhance Existing Collections

Instead of new collections, could add metadata to existing ones:

### Option A: Add to Descriptions Collection
- Already has ticket-level data
- SLA breach comments relate to specific tickets
- Could filter: `where={"has_sla_breach": True}`

### Option B: Dedicated Collection (Recommended)
- **Cleaner separation**: Breach explanations are distinct use case
- **Targeted queries**: "Show me all SLA breach scenarios"
- **Performance**: No need to filter 10K+ descriptions

**Recommendation**: Option B (dedicated collection) for query efficiency

---

## Implementation Steps

### 1. Update GPU Indexer

```bash
# Edit collection definitions
nano ~/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py

# Add sla_breach_explanations to collections dict
```

### 2. Run GPU Indexer

```bash
cd ~/git/maia

# Index just the new collection
python3 claude/tools/sre/servicedesk_gpu_rag_indexer.py \
    --index sla_breach_explanations \
    --batch-size 256

# ETA: ~4 seconds
```

### 3. Verify

```python
import chromadb
client = chromadb.PersistentClient(path='~/.maia/servicedesk_rag')
collection = client.get_collection('servicedesk_sla_breach_explanations')
print(f"Indexed: {collection.count()} documents")  # Expect: 347
```

### 4. Test Query

```python
# Find similar breach scenarios
results = collection.query(
    query_texts=["update caused compatibility issues"],
    n_results=5
)
```

---

## Summary

### ✅ Recommended Addition
**1 collection**: `sla_breach_explanations` (347 documents)
- **Value**: HIGH (L3/L4 escalation context)
- **Cost**: NEGLIGIBLE (4 seconds, 0.5MB)
- **Use case**: Pattern analysis, similar incident search

### ❌ Not Recommended
- Root Cause Categories (too categorical)
- SLA Breach Reasons (too categorical)
- Related CI (insufficient data)

### 💡 Existing Feature
- Customer vs Internal already tracked via `comment_type` metadata in comments collection

### 🎯 Total RAG System (After Addition)
- **6 collections**
- **214,347 documents**
- **~400MB storage**
- **~12 minutes indexing** (one-time)
- **97 docs/sec query speed** (GPU)

---

## Next Action

**If you want to proceed:**

```bash
# Quick command to add the collection
cd ~/git/maia && python3 claude/tools/sre/servicedesk_gpu_rag_indexer.py \
    --index sla_breach_explanations --batch-size 256
```

**If you want to analyze first:**
- Review sample SLA breach comments
- Validate query use cases
- Consider integration with ServiceDesk Manager Agent

**If you want to skip:**
- Current 5 collections cover 99.8% of text content
- SLA breach explanations nice-to-have, not critical
