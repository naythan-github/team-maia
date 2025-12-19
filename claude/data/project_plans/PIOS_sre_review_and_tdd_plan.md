# PIOS Project - SRE Review & TDD Development Plan

## Document Information

**Project**: Personal Information Operating System (PIOS)
**Review Date**: 2025-12-17
**Updated**: 2025-12-19
**Reviewer**: SRE Principal Engineer Agent
**Status**: ✅ PHASE 0 COMPLETE - Ready for Phase 1
**Next Action**: Begin Phase 1 (Universal Document Intelligence)
**Related Document**: [PIOS_personal_information_operating_system.md](PIOS_personal_information_operating_system.md)

---

## 🎉 UPDATE: Knowledge Graph FIXED (2025-12-18)

The Knowledge Graph blocker has been resolved. The fix was simple:
- Removed dead import: `enhanced_context_manager` (was imported but never used)
- Removed unused assignment: `self.context_manager = get_context_manager()`

**Verification Results**:
- ✅ Import successful
- ✅ Node creation works
- ✅ Relationship creation works
- ✅ Semantic search works

**Phase 0.5 is no longer needed** - proceed directly to Phase 0.

---

## 🎉 UPDATE: Phase 0 COMPLETE (2025-12-19)

Downloads infrastructure has been fixed and is operational.

### Fixes Applied

| File | Issue | Fix |
|------|-------|-----|
| `com.maia.intelligent-downloads-router.plist` | `/git/maia/` paths | → `/maia/` |
| `com.maia.downloads-vtt-mover.plist` | `/git/maia/` paths + log paths | → `/maia/` + `~/.maia/logs/` |
| `com.maia.downloads-organizer-scheduler.plist` | `/git/maia/` paths, missing PYTHONPATH | → `/maia/` + added PYTHONPATH |
| `claude/commands/organize_downloads.py` | Hardcoded `git/maia` in sys.path | → `maia` |

### Status

| Agent | Status | Notes |
|-------|--------|-------|
| `intelligent-downloads-router` | ✅ Running | Real-time watcher (PID active) |
| `downloads-vtt-mover` | ✅ Running | Real-time watcher (PID active) |
| `downloads-organizer-scheduler` | ✅ Exit 0 | Runs every 60s |

### Known Issue
**Real-time watchers need Full Disk Access** for Python3 in macOS Security settings. Manual runs work (terminal has access). The scheduled organizer catches files the watchers can't move.

### Remaining (Optional)
- Consolidate redundant VTT watcher (`downloads-vtt-mover` duplicates `intelligent-downloads-router` functionality)

**Commit**: `321b301` - Phase 0: Fix Downloads Infrastructure Path Mismatch

---

## Quick Resume Context

When resuming this project, load the SRE Principal Engineer Agent and review:
1. This document (review findings and TDD plan)
2. The original project plan (PIOS_personal_information_operating_system.md)
3. Current state of Knowledge Graph (`claude/tools/personal_knowledge_graph.py`)

**Key Command to Resume**:
```
Load the SRE agent and continue PIOS development - start Phase 1
```

**Current Status** (2025-12-19):
- ✅ Knowledge Graph: Fixed and operational
- ✅ Phase 0: Downloads infrastructure complete
- 🔜 Phase 1: Universal Document Intelligence (next)

---

## Executive Summary

The PIOS project plan is **ambitious and well-structured**. The critical Knowledge Graph blocker has been **resolved** (2025-12-18). Remaining issues are architectural gaps that can be addressed during TDD development.

| Category | Assessment |
|----------|------------|
| **Architecture** | Good layered design, missing operational concerns |
| **Dependencies** | ✅ Knowledge Graph FIXED, Ollama model available |
| **Effort Estimates** | Revised: 26-36 days (was 17-25) |
| **Risk Mitigation** | Listed but not architected |
| **Testing Strategy** | TDD plan ready |
| **Operational Readiness** | To address in Phase 1.5 |

---

## Critical Issues (Must Fix Before Development)

### 1. ~~Knowledge Graph is BROKEN~~ ✅ RESOLVED (2025-12-18)

```
ORIGINAL ERROR: ModuleNotFoundError: No module named 'claude.tools.enhanced_context_manager'

FIX APPLIED: Removed dead code (import was never used)
STATUS: Knowledge Graph now fully functional
```

**Resolution**:
- The `enhanced_context_manager` was imported but NEVER USED anywhere in the 922-line file
- The `ml_pattern_recognition` dependency was already handled gracefully (try/except)
- Fix: Removed 2 lines of dead code
- Result: Full KG functionality restored

**Verified Working**:
- `get_knowledge_graph()` instantiates correctly
- `add_node()` creates nodes with all attributes
- `add_relationship()` links nodes with strength/attributes
- `semantic_search()` returns relevant results
- `get_knowledge_summary()` returns stats

---

### 2. Missing Queue/Processing Architecture

The plan mentions "queue system with background processing" in risk mitigation but provides **no actual queue design**.

**Questions unanswered**:
- What happens when 50 files are dropped simultaneously?
- How are retries handled for failed processing?
- Where is the dead letter queue for permanent failures?
- How does the watcher hand off to the processor?

**Impact**: System will fail under load or lose documents.

**Recommended Architecture**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  File Watcher   │────▶│  SQLite Queue   │────▶│   Processor     │
│  (watchdog)     │     │  (FIFO + DLQ)   │     │   (worker)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  Dead Letter    │
                        │  Queue (DLQ)    │
                        └─────────────────┘
```

**Queue Schema** (to add to Phase 1):
```sql
CREATE TABLE processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    worker_id TEXT
);

CREATE INDEX idx_queue_status ON processing_queue(status, priority, created_at);
```

---

### 3. Ollama Model Mismatch

**Plan specifies**: `llama3.2`
**Available on system**:
- `llama3.2:3b` (2.0 GB) - Too small for reliable entity extraction
- `llama3.1:8b` (4.9 GB) - Better choice
- `qwen2.5:7b-instruct` (4.7 GB) - Good alternative
- `gemma2:9b` (5.4 GB) - Also viable

**Recommendation**: Use `llama3.1:8b` or `qwen2.5:7b-instruct` for entity extraction.

**Validation Required**: Before committing, test entity extraction quality with sample documents.

---

### 4. No Concurrency/Locking Strategy

Multiple components access shared resources:
- Knowledge Graph (SQLite)
- ChromaDB collections
- Document Lifecycle DB
- File system (moving files)

**Recommended Strategy**:
1. **Single processor worker** (simplest, start here)
2. SQLite in WAL mode for concurrent reads
3. File-level locking during move operations
4. Transaction boundaries at document level

---

## Major Issues (Should Fix Before Development)

### 5. Phase 0 Effort Underestimated

**Original**: 1 day | **Revised**: 2-3 days

**Additional scope**:
- Verify ALL Python scripts for hardcoded paths
- Integration testing after fixes
- Consolidate redundant watchers
- Handle existing `downloads_processed.json`

**Files requiring path audit**:
```
claude/tools/intelligent_downloads_router.py
claude/tools/downloads_vtt_mover.py
claude/commands/organize_downloads.py
/Users/naythandawe/Library/LaunchAgents/com.maia.intelligent-downloads-router.plist
/Users/naythandawe/Library/LaunchAgents/com.maia.downloads-vtt-mover.plist
/Users/naythandawe/Library/LaunchAgents/com.maia.downloads-organizer-scheduler.plist
```

---

### 6. Missing Error Recovery Workflow

**Add to Phase 3 spec**:
```python
class ErrorRecoveryWorkflow:
    def list_failed_documents(self) -> List[FailedDocument]:
        """List all documents in FAILED state"""

    def retry_document(self, document_id: str) -> ProcessingResult:
        """Retry processing a failed document"""

    def move_to_manual_review(self, document_id: str, reason: str):
        """Move to manual review queue"""

    def get_failure_summary(self) -> FailureSummary:
        """Aggregate failure stats for alerting"""
```

---

### 7. Missing Data Migration/Bootstrap Strategy

**Add Phase 0.5: Data Migration Planning**

**Scope**:
1. Inventory existing documents in ~/Documents/
2. Design backfill process (batch, not real-time)
3. Historical email import strategy
4. Knowledge graph seeding from existing CVs

**Estimated Effort**: 1-2 days planning, 2-3 days implementation

---

### 8. Email Integration Decision Required

**Option A: EML Files Only**
- Simpler implementation
- Misses sent emails (unless explicitly saved)
- No real-time processing
- Effort: 3-4 days

**Option B: M365 API Integration**
- Full email access (sent + received)
- Requires OAuth setup, app registration
- Real-time via webhooks or polling
- Effort: 5-7 days

**Recommendation**: Start with EML files (Option A), add M365 later as enhancement.

---

### 9. Missing Health Monitoring/Observability

**Add to Phase 1.5 or cross-cutting**:

```python
class PIOSHealthMonitor:
    """Health monitoring for PIOS system"""

    def check_launchagent_status(self) -> Dict[str, str]:
        """Check all LaunchAgents are running"""

    def get_queue_depth(self) -> int:
        """Current items in processing queue"""

    def get_processing_rate(self, hours: int = 24) -> float:
        """Documents processed per hour"""

    def get_error_rate(self, hours: int = 24) -> float:
        """Error rate as percentage"""

    def check_disk_space(self) -> Dict[str, int]:
        """Available space for RAG databases"""

    def get_ollama_status(self) -> bool:
        """Check Ollama is responding"""
```

---

### 10. Incomplete Deduplication Strategy

**Current**: Content hash for exact duplicates

**Enhanced Strategy**:
```python
class DeduplicationStrategy:
    # Level 1: Exact duplicate (content hash match)
    # Level 2: Near duplicate (>95% text similarity)
    # Level 3: Semantic duplicate (same entity, different format)

    def check_duplicate(self, file_path: Path) -> DuplicateResult:
        # 1. Content hash check
        content_hash = self.compute_hash(file_path)
        if existing := self.find_by_hash(content_hash):
            return DuplicateResult(level=1, existing=existing)

        # 2. Text similarity check (for text documents)
        text = self.extract_text(file_path)
        if similar := self.find_similar_text(text, threshold=0.95):
            return DuplicateResult(level=2, existing=similar)

        # 3. Entity-based check (same person's CV)
        entities = self.extract_entities(text)
        if semantic := self.find_semantic_duplicate(entities):
            return DuplicateResult(level=3, existing=semantic)

        return DuplicateResult(level=0, existing=None)
```

---

## Revised Effort Estimates

| Phase | Original | Revised | Delta | Reason |
|-------|----------|---------|-------|--------|
| 0 | 1 day | 2-3 days | +1-2 | Integration testing, consolidation |
| 0.5 | - | 1-2 days | NEW | Fix Knowledge Graph |
| 1 | 3-5 days | 5-7 days | +2 | Queue architecture, circuit breaker |
| 1.5 | - | 1-2 days | NEW | Observability |
| 2 | 2-3 days | 3-4 days | +1 | KG integration complexity |
| 3 | 2-3 days | 3-4 days | +1 | Error recovery workflow |
| 3.5 | - | 2-3 days | NEW | Data migration |
| 4 | 3-4 days | 4-5 days | +1 | EML-only decision |
| 5 | 2-3 days | 3-4 days | +1 | Throttling architecture |
| 6 | 2-3 days | 3-4 days | +1 | Multi-source complexity |
| 7 | 2-3 days | 2-3 days | 0 | Reasonable |
| **Total** | **17-25 days** | **30-41 days** | **+60%** | |

---

## Revised Build Sequence

```
Phase 0:   Fix Downloads Infrastructure (2-3 days) ✅ COMPLETE (2025-12-19)
           └── Path fixes, LaunchAgents operational, integration tested

Phase 0.5: Fix Knowledge Graph (1-2 days) ✅ COMPLETE (2025-12-18)
           └── Removed dead code, KG fully functional

Phase 1:   Universal Document Intelligence (5-7 days) 🔜 NEXT
           └── + Queue architecture
           └── + Circuit breaker for Ollama
           └── + Fallback classification

Phase 1.5: Observability Foundation (1-2 days)
           └── Logging, metrics, health checks

Phase 2:   Knowledge Graph Connector (3-4 days)
           └── Entity mapping, dedup, RAG indexing

Phase 3:   Document Lifecycle Manager (3-4 days)
           └── + Error recovery workflow
           └── + Manual review interface

Phase 3.5: Data Migration (2-3 days)
           └── Bootstrap existing documents
           └── Historical backfill

Phase 4:   Email Integration (4-5 days)
           └── EML files only (M365 later)

Phase 5:   Proactive Insights (3-4 days)
           └── + Throttling, digest mode

Phase 6:   Unified Query Interface (3-4 days)
           └── Multi-source queries

Phase 7:   Dashboard/Notifications (2-3 days)
           └── CLI, macOS notifications, web dashboard
```

---

## TDD Development Plan

### Pre-Development Checklist

Before writing any code:

- [ ] **Decision**: Knowledge Graph - fix existing or replace?
- [ ] **Decision**: Email integration - EML only or M365?
- [ ] **Decision**: Ollama model - validate `llama3.1:8b` quality
- [ ] **Decision**: Queue technology - SQLite queue recommended
- [ ] **Create**: Test data set (sample CVs, JDs, invoices, emails)
- [ ] **Verify**: All Python dependencies installed

### Phase 0 TDD Specification

**Test File**: `claude/tools/pios/tests/test_phase0_infrastructure.py`

```python
# Test 1: LaunchAgent paths are correct
def test_launchagent_paths_point_to_maia():
    """All LaunchAgents should reference ~/maia/ not ~/git/maia/"""
    plist_files = [
        "com.maia.intelligent-downloads-router.plist",
        "com.maia.downloads-vtt-mover.plist",
        "com.maia.downloads-organizer-scheduler.plist",
    ]
    for plist in plist_files:
        content = read_plist(f"~/Library/LaunchAgents/{plist}")
        assert "/git/maia/" not in content
        assert "/maia/" in content

# Test 2: Python scripts have correct paths
def test_python_scripts_paths():
    """Internal paths in Python scripts should be correct"""
    scripts = [
        "claude/tools/intelligent_downloads_router.py",
        "claude/tools/downloads_vtt_mover.py",
        "claude/commands/organize_downloads.py",
    ]
    for script in scripts:
        content = read_file(script)
        assert "/git/maia/" not in content

# Test 3: LaunchAgents can be loaded
def test_launchagents_load_successfully():
    """LaunchAgents should load without error"""
    result = subprocess.run(["launchctl", "list"], capture_output=True)
    # After reload, should not show exit code 2

# Test 4: Downloads watcher responds to new files
def test_downloads_watcher_detects_new_file():
    """Watcher should detect new file in Downloads"""
    test_file = create_temp_file("~/Downloads/test_pios.txt")
    time.sleep(2)
    assert file_was_detected(test_file)
    cleanup(test_file)

# Test 5: Redundant watchers consolidated
def test_single_vtt_handler():
    """VTT handling should only be in intelligent_downloads_router"""
    # downloads_vtt_mover should be disabled or removed
```

### Phase 0.5 TDD Specification (Knowledge Graph Fix)

**Test File**: `claude/tools/pios/tests/test_phase05_knowledge_graph.py`

```python
# Test 1: Knowledge Graph imports successfully
def test_knowledge_graph_imports():
    """KG module should import without errors"""
    from claude.tools.personal_knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    assert kg is not None

# Test 2: Can add nodes
def test_add_node():
    """Should be able to add a node to the graph"""
    kg = get_knowledge_graph()
    node_id = kg.add_node(
        node_type=NodeType.PERSON,
        name="Test Person",
        description="Test description",
        attributes={"role": "candidate"},
        source_agent="test"
    )
    assert node_id is not None
    assert kg.get_node_by_name("Test Person") is not None

# Test 3: Can add relationships
def test_add_relationship():
    """Should be able to add relationships between nodes"""
    kg = get_knowledge_graph()
    person_id = kg.add_node(NodeType.PERSON, "Alice", "", {})
    skill_id = kg.add_node(NodeType.SKILL, "Python", "", {})
    rel_id = kg.add_relationship(
        person_id, skill_id,
        RelationshipType.HAS_SKILL,
        strength=0.9
    )
    assert rel_id is not None

# Test 4: Semantic search works
def test_semantic_search():
    """Semantic search should return relevant results"""
    kg = get_knowledge_graph()
    # Add test data
    kg.add_node(NodeType.SKILL, "Azure AZ-305", "Cloud certification", {})

    results = kg.semantic_search(SemanticQuery(
        query_text="cloud certification",
        max_results=5
    ))
    assert len(results) > 0

# Test 5: Knowledge summary works
def test_knowledge_summary():
    """Should return valid summary statistics"""
    kg = get_knowledge_graph()
    summary = kg.get_knowledge_summary()
    assert "total_nodes" in summary
    assert "total_relationships" in summary
```

### Phase 1 TDD Specification

**Test File**: `claude/tools/pios/tests/test_phase1_document_intelligence.py`

```python
# Test 1: PDF text extraction
def test_pdf_extraction():
    """Should extract text from PDF files"""
    extractor = PDFExtractor()
    text = extractor.extract("test_data/sample_cv.pdf")
    assert len(text) > 100
    assert "experience" in text.lower() or "skills" in text.lower()

# Test 2: DOCX text extraction
def test_docx_extraction():
    """Should extract text from DOCX files"""
    extractor = DOCXExtractor()
    text = extractor.extract("test_data/sample_jd.docx")
    assert len(text) > 100

# Test 3: CV classification
def test_cv_classification():
    """Should correctly classify CV documents"""
    intel = UniversalDocumentIntelligence()
    result = intel.classify_document(Path("test_data/sample_cv.pdf"))
    assert result.document_type == "CV"
    assert result.confidence > 0.8

# Test 4: JD classification
def test_jd_classification():
    """Should correctly classify Job Description documents"""
    intel = UniversalDocumentIntelligence()
    result = intel.classify_document(Path("test_data/sample_jd.docx"))
    assert result.document_type == "JD"
    assert result.confidence > 0.8

# Test 5: Entity extraction from CV
def test_cv_entity_extraction():
    """Should extract entities from CV"""
    intel = UniversalDocumentIntelligence()
    result = intel.process(Path("test_data/sample_cv.pdf"))

    # Should find person
    persons = [e for e in result.entities if e.type == "PERSON"]
    assert len(persons) >= 1

    # Should find skills
    skills = [e for e in result.entities if e.type == "SKILL"]
    assert len(skills) >= 3

# Test 6: Relationship inference
def test_relationship_inference():
    """Should infer relationships between entities"""
    intel = UniversalDocumentIntelligence()
    result = intel.process(Path("test_data/sample_cv.pdf"))

    # Should have HAS_SKILL relationships
    has_skill = [r for r in result.relationships if r.type == "HAS_SKILL"]
    assert len(has_skill) >= 1

# Test 7: Queue integration
def test_queue_add_and_process():
    """Should add files to queue and process them"""
    queue = ProcessingQueue()
    queue.add("test_data/sample_cv.pdf")

    item = queue.get_next()
    assert item is not None
    assert item.status == "PROCESSING"

# Test 8: Circuit breaker for Ollama
def test_ollama_circuit_breaker():
    """Should handle Ollama failures gracefully"""
    intel = UniversalDocumentIntelligence()
    # Simulate Ollama being down
    with mock_ollama_failure():
        result = intel.classify_document(Path("test_data/sample_cv.pdf"))
        # Should fall back to pattern matching
        assert result.document_type in ["CV", "UNKNOWN"]

# Test 9: Large file handling
def test_large_file_handling():
    """Should handle large files without memory issues"""
    intel = UniversalDocumentIntelligence()
    # File > 10MB
    result = intel.process(Path("test_data/large_document.pdf"))
    assert result is not None

# Test 10: Empty/corrupted file handling
def test_corrupted_file_handling():
    """Should handle corrupted files gracefully"""
    intel = UniversalDocumentIntelligence()
    result = intel.process(Path("test_data/corrupted.pdf"))
    assert result.document_type.document_type == "UNKNOWN"
```

### Phase 2 TDD Specification

**Test File**: `claude/tools/pios/tests/test_phase2_kg_connector.py`

```python
# Test 1: Entity deduplication
def test_entity_deduplication():
    """Same person from multiple documents should be single node"""
    connector = KnowledgeGraphConnector()

    # Process two CVs for same person
    connector.process_document(Path("test_data/john_doe_cv_v1.pdf"))
    connector.process_document(Path("test_data/john_doe_cv_v2.pdf"))

    kg = connector.kg
    johns = [n for n in kg.nodes.values() if "John Doe" in n.name]
    assert len(johns) == 1  # Should be deduplicated

# Test 2: Relationship accumulation
def test_relationship_strength_accumulation():
    """Multiple evidence should strengthen relationships"""
    connector = KnowledgeGraphConnector()

    # Process multiple documents mentioning same skill
    connector.process_document(Path("test_data/cv_with_python.pdf"))
    connector.process_document(Path("test_data/interview_mentions_python.vtt"))

    # Python skill relationship should be stronger
    # (implementation depends on KG design)

# Test 3: RAG indexing by document type
def test_rag_routing():
    """Documents should be indexed to correct RAG collection"""
    connector = KnowledgeGraphConnector()

    connector.process_document(Path("test_data/sample_cv.pdf"))
    assert document_in_collection("sample_cv.pdf", "cv_rag")

    connector.process_document(Path("test_data/sample_invoice.pdf"))
    assert document_in_collection("sample_invoice.pdf", "document_rag")

# Test 4: Rollback on failure
def test_rollback_on_failure():
    """Failed processing should not leave partial state"""
    connector = KnowledgeGraphConnector()
    initial_node_count = len(connector.kg.nodes)

    with mock_rag_failure():
        try:
            connector.process_document(Path("test_data/sample_cv.pdf"))
        except:
            pass

    # Should rollback to initial state
    assert len(connector.kg.nodes) == initial_node_count
```

### Phase 3 TDD Specification

**Test File**: `claude/tools/pios/tests/test_phase3_lifecycle.py`

```python
# Test 1: State transitions
def test_state_transitions():
    """Document should progress through states correctly"""
    manager = DocumentLifecycleManager()
    doc_id = manager.register_document(Path("~/Downloads/test.pdf"))

    assert manager.get_state(doc_id) == "ARRIVED"

    manager.start_processing(doc_id)
    assert manager.get_state(doc_id) == "PROCESSING"

    manager.mark_indexed(doc_id)
    assert manager.get_state(doc_id) == "INDEXED"

# Test 2: Duplicate detection
def test_duplicate_detection():
    """Should detect duplicate documents"""
    manager = DocumentLifecycleManager()

    doc1 = manager.register_document(Path("test_data/sample.pdf"))
    doc2 = manager.register_document(Path("test_data/sample_copy.pdf"))  # Same content

    assert manager.get_state(doc2) == "DUPLICATE"

# Test 3: Correct routing
def test_cv_routing():
    """CV should be routed to Recruitment/CVs folder"""
    manager = DocumentLifecycleManager()
    manager.process_and_route(Path("test_data/sample_cv.pdf"), doc_type="CV")

    # Should be in ~/Documents/Recruitment/CVs/YYYY-MM/
    assert Path("~/Documents/Recruitment/CVs").expanduser().exists()

# Test 4: History tracking
def test_history_tracking():
    """All state changes should be recorded"""
    manager = DocumentLifecycleManager()
    doc_id = manager.register_document(Path("test_data/sample.pdf"))
    manager.start_processing(doc_id)
    manager.mark_indexed(doc_id)

    history = manager.get_history(doc_id)
    assert len(history) >= 3  # ARRIVED, PROCESSING, INDEXED

# Test 5: Error recovery
def test_error_recovery():
    """Failed documents should be recoverable"""
    manager = DocumentLifecycleManager()
    doc_id = manager.register_document(Path("test_data/sample.pdf"))
    manager.mark_failed(doc_id, "Test failure")

    assert manager.get_state(doc_id) == "FAILED"

    # Should be able to retry
    manager.retry(doc_id)
    assert manager.get_state(doc_id) == "PROCESSING"
```

---

## Test Data Requirements

### Sample Documents Needed

Create `claude/tools/pios/test_data/` with:

| File | Purpose | Source |
|------|---------|--------|
| `sample_cv.pdf` | CV classification & entity extraction | Anonymized real CV |
| `sample_cv.docx` | DOCX CV extraction | Anonymized real CV |
| `sample_jd.docx` | JD classification & requirements | Real JD (sanitized) |
| `sample_invoice.pdf` | Invoice classification & data extraction | Fake invoice |
| `sample_policy.pdf` | Policy classification | Orro policy (sanitized) |
| `sample_email.eml` | Email parsing | Exported email |
| `sample_vtt.vtt` | Meeting transcript | Real VTT (sanitized) |
| `large_document.pdf` | Large file handling | >10MB PDF |
| `corrupted.pdf` | Error handling | Intentionally broken |
| `john_doe_cv_v1.pdf` | Deduplication testing | Synthetic |
| `john_doe_cv_v2.pdf` | Deduplication testing | Synthetic |

---

## Questions Requiring User Decision

Before proceeding with development, these decisions are needed:

### Architecture Decisions

1. **Knowledge Graph Strategy**
   - [ ] Option A: Fix existing `personal_knowledge_graph.py`
   - [ ] Option B: Create new simplified PIOS-specific graph
   - [ ] Option C: Use existing KG but stub the missing dependency

2. **Email Integration Scope**
   - [ ] Option A: EML files only (simpler, start here)
   - [ ] Option B: M365 API (full access, more complex)

3. **Ollama Model**
   - [ ] `llama3.1:8b` (recommended)
   - [ ] `qwen2.5:7b-instruct` (alternative)
   - [ ] Other: ____________

4. **Queue Technology**
   - [ ] SQLite-based queue (recommended, simple)
   - [ ] Redis (if already in use)
   - [ ] Python multiprocessing.Queue (in-memory only)

### Operational Decisions

5. **Failure Alerting**
   - [ ] macOS notifications only
   - [ ] Log file + monitoring
   - [ ] Dashboard indicator

6. **Archival Timeline**
   - [ ] After ____ days in ACTIVE state
   - [ ] Manual only
   - [ ] Based on last access date

7. **Privacy/Exclusions**
   - [ ] Exclude files containing: ____________
   - [ ] Exclude folders: ____________
   - [ ] No exclusions

---

## Next Steps

When resuming this project:

1. **Review this document** for context
2. **Make decisions** on questions above
3. **Create test data** in `claude/tools/pios/test_data/`
4. **Start Phase 0** with TDD approach:
   - Write tests first
   - Fix LaunchAgent paths
   - Run tests to verify
   - Commit when green

5. **Proceed to Phase 0.5** (Knowledge Graph fix)
6. **Continue sequentially** through phases

---

## File Locations Reference

| Purpose | Location |
|---------|----------|
| Project Plan | `claude/data/project_plans/PIOS_personal_information_operating_system.md` |
| This Review | `claude/data/project_plans/PIOS_sre_review_and_tdd_plan.md` |
| PIOS Code | `claude/tools/pios/` (to be created) |
| Tests | `claude/tools/pios/tests/` (to be created) |
| Test Data | `claude/tools/pios/test_data/` (to be created) |
| Knowledge Graph | `claude/tools/personal_knowledge_graph.py` |
| Downloads Router | `claude/tools/intelligent_downloads_router.py` |
| LaunchAgents | `~/Library/LaunchAgents/com.maia.*.plist` |

---

*Document saved: 2025-12-17*
*Ready for resumption when user returns*
