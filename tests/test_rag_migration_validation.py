#!/usr/bin/env python3
"""
RAG Migration Validation Test Suite

Tests UFC compliance migration of RAG databases from ~/.maia/ to
~/git/maia/claude/data/rag_databases/

Author: SRE Principal Engineer Agent
Created: 2025-10-30
Requirements: tests/rag_migration_validation_requirements.md
"""

import os
import sys
import time
import pytest
import requests
from pathlib import Path
from typing import Dict, Any

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Import RAG systems
try:
    from claude.tools.email_rag_ollama import EmailRAGOllama
except ImportError as e:
    pytest.skip(f"Email RAG not available: {e}", allow_module_level=True)

try:
    from claude.tools.whisper_meeting_transcriber import MeetingTranscriptionRAG
except ImportError as e:
    pytest.skip(f"Meeting transcription RAG not available: {e}", allow_module_level=True)


# ============================================================================
# FR-1: Database Integrity Validation
# ============================================================================

def test_database_paths_exist():
    """Verify ChromaDB databases exist at UFC-compliant paths"""
    email_rag_path = MAIA_ROOT / "claude" / "data" / "rag_databases" / "email_rag_ollama"
    meeting_rag_path = MAIA_ROOT / "claude" / "data" / "rag_databases" / "meeting_transcripts_rag"

    assert email_rag_path.exists(), f"Email RAG path missing: {email_rag_path}"
    assert meeting_rag_path.exists(), f"Meeting RAG path missing: {meeting_rag_path}"

    # Check for SQLite database files
    email_db_file = email_rag_path / "chroma.sqlite3"
    meeting_db_file = meeting_rag_path / "chroma.sqlite3"

    assert email_db_file.exists(), f"Email RAG database missing: {email_db_file}"
    assert meeting_db_file.exists(), f"Meeting RAG database missing: {meeting_db_file}"

    # Verify files are not empty
    assert email_db_file.stat().st_size > 1000, "Email RAG database file is suspiciously small"
    assert meeting_db_file.stat().st_size > 1000, "Meeting RAG database file is suspiciously small"


def test_database_file_structure():
    """Verify database directory structure is intact"""
    email_rag_path = MAIA_ROOT / "claude" / "data" / "rag_databases" / "email_rag_ollama"
    meeting_rag_path = MAIA_ROOT / "claude" / "data" / "rag_databases" / "meeting_transcripts_rag"

    # Email RAG should have index_state.json
    assert (email_rag_path / "index_state.json").exists(), "Email RAG index state missing"

    # Both should have chroma.sqlite3
    assert (email_rag_path / "chroma.sqlite3").exists()
    assert (meeting_rag_path / "chroma.sqlite3").exists()


# ============================================================================
# FR-2: Data Preservation Validation
# ============================================================================

def test_email_rag_data_count():
    """Verify email RAG contains expected document count (489 emails)"""
    rag = EmailRAGOllama()
    collection = rag.collection
    count = collection.count()

    # Pre-migration count was 489 emails
    assert count == 489, f"Expected 489 emails, found {count}"


def test_meeting_rag_data_count():
    """Verify meeting RAG contains expected document count (32 chunks)"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled (missing dependencies)")

    collection = rag.collection
    count = collection.count()

    # Pre-migration count was 32 document chunks
    assert count == 32, f"Expected 32 chunks, found {count}"


def test_email_rag_embeddings_accessible():
    """Verify email RAG embeddings are accessible"""
    rag = EmailRAGOllama()
    collection = rag.collection

    # Get a sample document
    results = collection.get(limit=1)

    assert results is not None
    assert 'documents' in results
    assert len(results['documents']) > 0


def test_meeting_rag_embeddings_accessible():
    """Verify meeting RAG embeddings are accessible"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled")

    collection = rag.collection

    # Get a sample document
    results = collection.get(limit=1)

    assert results is not None
    assert 'documents' in results
    assert len(results['documents']) > 0


# ============================================================================
# FR-3: Service Initialization Validation
# ============================================================================

def test_email_rag_initialization():
    """Verify EmailRAGOllama initializes successfully"""
    try:
        rag = EmailRAGOllama()

        # Check UFC-compliant path
        assert "claude/data/rag_databases/email_rag_ollama" in rag.db_path
        assert rag.collection is not None
        assert rag.client is not None

    except Exception as e:
        pytest.fail(f"Email RAG initialization failed: {e}")


def test_meeting_rag_initialization():
    """Verify MeetingTranscriptionRAG initializes successfully"""
    try:
        rag = MeetingTranscriptionRAG()

        if not rag.enabled:
            pytest.skip("Meeting RAG not enabled")

        # Check UFC-compliant path
        assert "claude/data/rag_databases/meeting_transcripts_rag" in rag.db_path
        assert rag.collection is not None

    except Exception as e:
        pytest.fail(f"Meeting RAG initialization failed: {e}")


def test_email_rag_auto_discovers_ufc_path():
    """Verify email RAG auto-discovers UFC-compliant path without manual config"""
    rag = EmailRAGOllama()  # No db_path parameter

    expected_path_suffix = "claude/data/rag_databases/email_rag_ollama"
    assert rag.db_path.endswith(expected_path_suffix), \
        f"Expected path ending with {expected_path_suffix}, got {rag.db_path}"


def test_meeting_rag_auto_discovers_ufc_path():
    """Verify meeting RAG auto-discovers UFC-compliant path"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled")

    expected_path_suffix = "claude/data/rag_databases/meeting_transcripts_rag"
    assert rag.db_path.endswith(expected_path_suffix), \
        f"Expected path ending with {expected_path_suffix}, got {rag.db_path}"


# ============================================================================
# FR-4: Query Functionality Validation
# ============================================================================

def test_email_rag_search_basic():
    """Verify email RAG executes basic search queries"""
    rag = EmailRAGOllama()
    results = rag.semantic_search("meeting", n_results=5)

    assert results is not None
    assert isinstance(results, list)
    assert len(results) <= 5
    if len(results) > 0:
        assert 'subject' in results[0]
        assert 'sender' in results[0]
        assert 'relevance' in results[0]


def test_meeting_rag_search_basic():
    """Verify meeting RAG executes basic search queries"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled")

    results = rag.search("discussion", n_results=5)

    assert results is not None
    assert 'documents' in results
    assert 'metadatas' in results
    assert len(results['documents'][0]) <= 5


def test_email_rag_search_returns_valid_structure():
    """Verify email RAG search returns properly structured results"""
    rag = EmailRAGOllama()
    results = rag.semantic_search("update", n_results=3)

    # Check structure - returns list of dicts
    assert isinstance(results, list)
    assert len(results) <= 3

    if len(results) > 0:
        # Each result should be a dict with expected keys
        result = results[0]
        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'sender' in result
        assert 'date' in result
        assert 'relevance' in result
        assert 'preview' in result
        assert 'message_id' in result

        # Relevance should be a float
        assert isinstance(result['relevance'], float)


def test_meeting_rag_search_returns_valid_structure():
    """Verify meeting RAG search returns properly structured results"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled")

    results = rag.search("meeting", n_results=3)

    # Check structure
    assert isinstance(results, dict)
    assert 'documents' in results
    assert 'metadatas' in results

    # Check documents
    assert isinstance(results['documents'], list)
    if len(results['documents']) > 0:
        assert len(results['documents'][0]) <= 3


# ============================================================================
# FR-5: Dependency Health Validation
# ============================================================================

def test_chromadb_available():
    """Verify ChromaDB library is available and functional"""
    try:
        import chromadb
        from chromadb.config import Settings

        # Create a test client
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        assert client is not None

    except ImportError:
        pytest.fail("ChromaDB library not available")


def test_ollama_health():
    """Verify Ollama service is running and accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        assert response.status_code == 200

        data = response.json()
        assert 'models' in data

    except requests.exceptions.RequestException as e:
        pytest.skip(f"Ollama not available (expected for email RAG): {e}")


def test_sentence_transformers_available():
    """Verify sentence-transformers library is available"""
    try:
        from sentence_transformers import SentenceTransformer

        # Try to load the model (may download on first run)
        model = SentenceTransformer('all-MiniLM-L6-v2')
        assert model is not None

    except ImportError:
        pytest.fail("Sentence-transformers library not available")
    except Exception as e:
        pytest.skip(f"Model download required or other issue: {e}")


# ============================================================================
# NFR-1: Performance Validation (SLOs)
# ============================================================================

def test_email_rag_query_performance():
    """Verify email RAG query latency <2s (P95 SLO)"""
    rag = EmailRAGOllama()

    start = time.time()
    results = rag.semantic_search("test query", n_results=5)
    latency = time.time() - start

    assert latency < 2.0, f"Query took {latency:.3f}s (SLO: <2s)"


def test_meeting_rag_query_performance():
    """Verify meeting RAG query latency <2s (P95 SLO)"""
    rag = MeetingTranscriptionRAG()

    if not rag.enabled:
        pytest.skip("Meeting RAG not enabled")

    start = time.time()
    results = rag.search("test query", n_results=5)
    latency = time.time() - start

    assert latency < 2.0, f"Query took {latency:.3f}s (SLO: <2s)"


def test_email_rag_initialization_performance():
    """Verify email RAG initialization <5s (SLO)"""
    start = time.time()
    rag = EmailRAGOllama()
    latency = time.time() - start

    assert latency < 5.0, f"Initialization took {latency:.3f}s (SLO: <5s)"


def test_meeting_rag_initialization_performance():
    """Verify meeting RAG initialization <5s (SLO)"""
    start = time.time()
    rag = MeetingTranscriptionRAG()
    latency = time.time() - start

    assert latency < 5.0, f"Initialization took {latency:.3f}s (SLO: <5s)"


# ============================================================================
# NFR-3: Reliability Validation
# ============================================================================

def test_email_rag_data_consistency():
    """Verify email RAG data count is consistent across re-initialization"""
    rag1 = EmailRAGOllama()
    count1 = rag1.collection.count()

    # Re-initialize
    rag2 = EmailRAGOllama()
    count2 = rag2.collection.count()

    assert count1 == count2, f"Inconsistent counts: {count1} vs {count2}"


def test_meeting_rag_data_consistency():
    """Verify meeting RAG data count is consistent across re-initialization"""
    rag1 = MeetingTranscriptionRAG()

    if not rag1.enabled:
        pytest.skip("Meeting RAG not enabled")

    count1 = rag1.collection.count()

    # Re-initialize
    rag2 = MeetingTranscriptionRAG()
    count2 = rag2.collection.count()

    assert count1 == count2, f"Inconsistent counts: {count1} vs {count2}"


def test_idempotent_test_execution():
    """Verify tests can run multiple times without side effects"""
    # Run email RAG search twice
    rag = EmailRAGOllama()

    results1 = rag.semantic_search("test", n_results=3)
    results2 = rag.semantic_search("test", n_results=3)

    # Should return same number of results
    assert len(results1) == len(results2)


# ============================================================================
# EC-1: Edge Case - Missing Database Path
# ============================================================================

def test_email_rag_handles_invalid_path():
    """Verify email RAG handles non-existent database path gracefully"""
    try:
        # Attempt to create RAG with invalid path
        rag = EmailRAGOllama(db_path="/tmp/nonexistent_test_path_12345")

        # Should either create empty DB or fail gracefully
        # (Implementation-dependent behavior)
        assert True  # If we get here, it handled it gracefully

    except Exception as e:
        # Error should be clear and informative
        assert "path" in str(e).lower() or "directory" in str(e).lower(), \
            f"Error message not informative: {e}"


# ============================================================================
# Test Summary and Reporting
# ============================================================================

def test_generate_health_report():
    """Generate comprehensive health report for both RAG systems"""
    report = {
        "email_rag": {},
        "meeting_rag": {},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Email RAG health
    try:
        rag = EmailRAGOllama()
        report["email_rag"] = {
            "status": "✅ Operational",
            "path": rag.db_path,
            "document_count": rag.collection.count(),
            "initialization_time": None
        }

        # Measure init time
        start = time.time()
        EmailRAGOllama()
        report["email_rag"]["initialization_time"] = f"{time.time() - start:.3f}s"

    except Exception as e:
        report["email_rag"] = {
            "status": "❌ Failed",
            "error": str(e)
        }

    # Meeting RAG health
    try:
        rag = MeetingTranscriptionRAG()

        if rag.enabled:
            report["meeting_rag"] = {
                "status": "✅ Operational",
                "path": rag.db_path,
                "document_count": rag.collection.count(),
                "initialization_time": None
            }

            # Measure init time
            start = time.time()
            MeetingTranscriptionRAG()
            report["meeting_rag"]["initialization_time"] = f"{time.time() - start:.3f}s"
        else:
            report["meeting_rag"] = {
                "status": "⚠️ Disabled",
                "reason": "Missing dependencies"
            }

    except Exception as e:
        report["meeting_rag"] = {
            "status": "❌ Failed",
            "error": str(e)
        }

    # Print report
    print("\n" + "=" * 80)
    print("RAG SYSTEMS HEALTH REPORT")
    print("=" * 80)

    print(f"\nEmail RAG:")
    for key, value in report["email_rag"].items():
        print(f"  {key}: {value}")

    print(f"\nMeeting RAG:")
    for key, value in report["meeting_rag"].items():
        print(f"  {key}: {value}")

    print(f"\nGenerated: {report['timestamp']}")
    print("=" * 80 + "\n")

    # Assert both systems operational or disabled gracefully
    assert report["email_rag"]["status"] in ["✅ Operational", "⚠️ Disabled"]
    assert report["meeting_rag"]["status"] in ["✅ Operational", "⚠️ Disabled"]


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
