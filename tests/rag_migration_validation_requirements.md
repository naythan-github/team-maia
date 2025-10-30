# RAG Migration Validation - Requirements Document

**Author**: SRE Principal Engineer Agent
**Created**: 2025-10-30
**Purpose**: Validate UFC compliance migration of RAG databases
**Status**: Requirements Complete

---

## Executive Summary

Validate that both RAG systems (Email RAG and Meeting Transcripts RAG) are fully operational after migration from `~/.maia/` to UFC-compliant `~/git/maia/claude/data/rag_databases/` location.

## Core Purpose

**What problem are we solving?**
Ensure zero data loss and full service functionality after migrating RAG databases to UFC-compliant file structure.

**Who will use this?**
SRE team validating infrastructure migrations, developers using RAG services.

**Success criteria?**
All RAG services operational with 100% data preservation and <2s query latency.

---

## Functional Requirements

### FR-1: Database Integrity Validation

**Requirement**: Verify ChromaDB databases exist at new UFC-compliant paths
**Acceptance Criteria**:
- Email RAG database exists at `~/git/maia/claude/data/rag_databases/email_rag_ollama/`
- Meeting transcripts RAG database exists at `~/git/maia/claude/data/rag_databases/meeting_transcripts_rag/`
- Both databases contain `chroma.sqlite3` file
- SQLite database files are not corrupted (can be opened)

**Test Scenario**:
```python
def test_database_paths_exist():
    email_rag_path = Path("~/git/maia/claude/data/rag_databases/email_rag_ollama").expanduser()
    meeting_rag_path = Path("~/git/maia/claude/data/rag_databases/meeting_transcripts_rag").expanduser()

    assert email_rag_path.exists()
    assert meeting_rag_path.exists()
    assert (email_rag_path / "chroma.sqlite3").exists()
    assert (meeting_rag_path / "chroma.sqlite3").exists()
```

---

### FR-2: Data Preservation Validation

**Requirement**: Confirm all data migrated without loss
**Acceptance Criteria**:
- Email RAG contains exactly 489 indexed emails (pre-migration count)
- Meeting transcripts RAG contains exactly 32 document chunks (pre-migration count)
- All embeddings are accessible and valid

**Test Scenario**:
```python
def test_email_rag_data_count():
    rag = EmailRAGOllama()
    collection = rag.collection
    count = collection.count()
    assert count == 489, f"Expected 489 emails, found {count}"

def test_meeting_rag_data_count():
    rag = MeetingTranscriptionRAG()
    collection = rag.collection
    count = collection.count()
    assert count == 32, f"Expected 32 chunks, found {count}"
```

---

### FR-3: Service Initialization Validation

**Requirement**: Both RAG services initialize without errors
**Acceptance Criteria**:
- EmailRAGOllama() initializes successfully
- MeetingTranscriptionRAG() initializes successfully
- Both services auto-discover UFC-compliant paths
- No exceptions during initialization

**Test Scenario**:
```python
def test_email_rag_initialization():
    try:
        rag = EmailRAGOllama()
        assert rag.db_path.endswith("claude/data/rag_databases/email_rag_ollama")
        assert rag.collection is not None
    except Exception as e:
        pytest.fail(f"Email RAG initialization failed: {e}")

def test_meeting_rag_initialization():
    try:
        rag = MeetingTranscriptionRAG()
        assert rag.db_path.endswith("claude/data/rag_databases/meeting_transcripts_rag")
        assert rag.collection is not None
    except Exception as e:
        pytest.fail(f"Meeting RAG initialization failed: {e}")
```

---

### FR-4: Query Functionality Validation

**Requirement**: Semantic search queries work correctly
**Acceptance Criteria**:
- Email RAG executes search queries successfully
- Meeting transcripts RAG executes search queries successfully
- Results contain valid data structure (documents, metadatas, distances)
- Results are semantically relevant to query

**Test Scenario**:
```python
def test_email_rag_search():
    rag = EmailRAGOllama()
    results = rag.search("test query", n_results=5)

    assert results is not None
    assert 'documents' in results
    assert 'metadatas' in results
    assert 'distances' in results
    assert len(results['documents'][0]) <= 5

def test_meeting_rag_search():
    rag = MeetingTranscriptionRAG()
    results = rag.search("test query", n_results=5)

    assert results is not None
    assert 'documents' in results
    assert 'metadatas' in results
    assert len(results['documents'][0]) <= 5
```

---

### FR-5: Dependency Health Validation

**Requirement**: All external dependencies are available
**Acceptance Criteria**:
- ChromaDB library importable and functional
- Sentence-transformers library available (meeting RAG)
- Ollama service running and accessible at localhost:11434 (email RAG)
- Embedding models available

**Test Scenario**:
```python
def test_chromadb_available():
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        assert client is not None
    except ImportError:
        pytest.fail("ChromaDB library not available")

def test_ollama_health():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        assert response.status_code == 200
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")

def test_sentence_transformers_available():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        assert model is not None
    except ImportError:
        pytest.fail("Sentence-transformers library not available")
```

---

## Non-Functional Requirements

### NFR-1: Performance (SLOs)

**Requirement**: Query performance within acceptable bounds
**Acceptance Criteria**:
- Database initialization: <5 seconds
- Search query latency: <2 seconds (P95)
- Memory usage: <500MB per RAG instance

**Test Scenario**:
```python
def test_email_rag_query_performance():
    rag = EmailRAGOllama()
    start = time.time()
    results = rag.search("test query", n_results=5)
    latency = time.time() - start

    assert latency < 2.0, f"Query took {latency}s (SLO: <2s)"

def test_meeting_rag_initialization_performance():
    start = time.time()
    rag = MeetingTranscriptionRAG()
    latency = time.time() - start

    assert latency < 5.0, f"Initialization took {latency}s (SLO: <5s)"
```

---

### NFR-2: Observability

**Requirement**: Clear logging and status reporting
**Acceptance Criteria**:
- RAG services log initialization status
- Database paths logged on startup
- Collection counts logged on startup
- Query operations logged with timing

**Test Scenario**:
```python
def test_logging_initialization(caplog):
    rag = EmailRAGOllama()

    # Verify logs contain essential info
    assert any("Email RAG initialized" in record.message for record in caplog.records)
```

---

### NFR-3: Reliability

**Requirement**: Zero data loss, graceful error handling
**Acceptance Criteria**:
- 100% data preservation (489 emails, 32 meeting chunks)
- Graceful handling of missing dependencies
- Clear error messages for configuration issues
- Idempotent test execution (can run multiple times)

**Test Scenario**:
```python
def test_data_integrity_hash():
    """Verify data integrity through collection count consistency"""
    rag1 = EmailRAGOllama()
    count1 = rag1.collection.count()

    # Re-initialize and check again
    rag2 = EmailRAGOllama()
    count2 = rag2.collection.count()

    assert count1 == count2, "Inconsistent data counts between initializations"
```

---

## Edge Cases

### EC-1: Missing Database Path
**Scenario**: Database directory doesn't exist
**Expected**: Service initialization fails with clear error message
**Test**: Create RAG instance with non-existent path, verify error

### EC-2: Corrupted Database
**Scenario**: SQLite database file corrupted
**Expected**: ChromaDB detects corruption and reports error
**Test**: (Manual test - not automated due to risk)

### EC-3: Ollama Service Down
**Scenario**: Ollama not running (email RAG dependency)
**Expected**: Email RAG initialization succeeds but queries may fail
**Test**: Mock Ollama unavailable, verify graceful degradation

### EC-4: Missing Embedding Model
**Scenario**: Sentence-transformers model not downloaded
**Expected**: Service downloads model or fails with clear error
**Test**: (Skip - first run will download model)

---

## Success Criteria Summary

✅ **Database Integrity**: All databases exist at UFC-compliant paths
✅ **Data Preservation**: 489 emails + 32 meeting chunks preserved
✅ **Service Initialization**: Both RAG services initialize successfully
✅ **Query Functionality**: Semantic search returns valid results
✅ **Dependency Health**: All dependencies available and functional
✅ **Performance**: Query latency <2s, initialization <5s
✅ **Reliability**: Zero data loss, graceful error handling
✅ **Observability**: Clear logging and status reporting

---

## Integration Points

| Component | Type | Endpoint/Path | Purpose |
|-----------|------|---------------|---------|
| ChromaDB | Library | N/A | Vector database persistence |
| Ollama | HTTP API | http://localhost:11434 | Email RAG embeddings |
| Sentence-transformers | Library | N/A | Meeting RAG embeddings |
| Email RAG Database | File System | ~/git/maia/claude/data/rag_databases/email_rag_ollama/ | Email vector storage |
| Meeting RAG Database | File System | ~/git/maia/claude/data/rag_databases/meeting_transcripts_rag/ | Meeting transcript storage |

---

## Test Coverage Matrix

| Requirement | Test Type | Priority | Automated? |
|-------------|-----------|----------|------------|
| FR-1: Database Integrity | Integration | High | ✅ Yes |
| FR-2: Data Preservation | Integration | Critical | ✅ Yes |
| FR-3: Service Initialization | Unit | High | ✅ Yes |
| FR-4: Query Functionality | Integration | High | ✅ Yes |
| FR-5: Dependency Health | Integration | Medium | ✅ Yes |
| NFR-1: Performance | Performance | High | ✅ Yes |
| NFR-2: Observability | Integration | Medium | ✅ Yes |
| NFR-3: Reliability | Integration | Critical | ✅ Yes |
| EC-1: Missing Database | Negative | Medium | ✅ Yes |
| EC-3: Ollama Down | Negative | Medium | ⚠️ Conditional |

---

## Assumptions

1. Email RAG had 489 emails pre-migration (verified earlier)
2. Meeting RAG had 32 chunks pre-migration (verified earlier)
3. ChromaDB and sentence-transformers libraries already installed
4. Ollama running for email RAG operations (graceful skip if not)
5. Tests run from Maia repository root

---

## Out of Scope

- Data migration automation (already completed manually)
- Backup/restore functionality
- Multi-user concurrent access testing
- Database optimization/tuning
- Security/access control testing

---

## Dependencies

- Python 3.9+
- ChromaDB library
- Sentence-transformers library
- Ollama (optional, for email RAG)
- pytest framework
- Existing RAG service implementations

---

**REQUIREMENTS STATUS**: ✅ COMPLETE - Ready for Phase 3 (Test Design)
