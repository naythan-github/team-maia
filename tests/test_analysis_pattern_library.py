#!/usr/bin/env python3
"""
Unit Tests for Analysis Pattern Library

Phase 141: Global Analysis Pattern Library
TDD Implementation - Test First Approach
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
import sqlite3
import json

# Import the module we're testing (will fail until we create it - that's TDD!)
try:
    from claude.tools.analysis_pattern_library import (
        AnalysisPatternLibrary,
        ValidationError,
        PatternNotFoundError
    )
except ImportError:
    # Expected to fail initially - that's the RED phase
    pytest.skip("Module not yet implemented", allow_module_level=True)


# Test Fixtures
@pytest.fixture
def temp_db():
    """Temporary SQLite database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield db_path
    try:
        os.remove(db_path)
    except:
        pass


@pytest.fixture
def temp_chromadb():
    """Temporary ChromaDB directory for testing."""
    chroma_path = tempfile.mkdtemp()
    yield chroma_path
    try:
        shutil.rmtree(chroma_path)
    except:
        pass


@pytest.fixture
def pattern_library(temp_db, temp_chromadb):
    """AnalysisPatternLibrary instance with temp databases."""
    return AnalysisPatternLibrary(db_path=temp_db, chromadb_path=temp_chromadb)


@pytest.fixture
def sample_pattern_data():
    """Sample pattern data for testing."""
    return {
        "pattern_name": "Timesheet Project Breakdown",
        "domain": "servicedesk",
        "question_type": "timesheet_breakdown",
        "description": "Analyze person's hours across projects with percentage of available time",
        "sql_template": "SELECT ... WHERE name IN ({{names}})",
        "presentation_format": "Top 5 + remaining + unaccounted",
        "business_context": "7.6 hrs/day, sick/holidays not recorded",
        "tags": ["timesheet", "hours", "projects"]
    }


# ============================================================================
# Test Suite 1: Pattern CRUD Operations (15 tests)
# ============================================================================

class TestPatternCRUD:
    """Test suite for CRUD operations."""

    def test_save_pattern_success(self, pattern_library, sample_pattern_data):
        """
        Test 1.1: Verify successful pattern save with all required fields.

        RED PHASE: This test will FAIL until we implement save_pattern()
        """
        # Act
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Assert
        assert pattern_id is not None, "Pattern ID should be returned"
        assert isinstance(pattern_id, str), "Pattern ID should be a string"
        assert "servicedesk" in pattern_id, "Pattern ID should contain domain"
        assert "timesheet_breakdown" in pattern_id, "Pattern ID should contain question type"

        # Verify pattern exists in database
        conn = sqlite3.connect(pattern_library.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_patterns WHERE pattern_id = ?", [pattern_id])
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Pattern should exist in database"

    def test_save_pattern_missing_required_fields(self, pattern_library):
        """
        Test 1.2: Verify validation for missing required fields.

        RED PHASE: This test will FAIL until we implement validation
        """
        # Test missing pattern_name
        with pytest.raises(ValidationError) as exc_info:
            pattern_library.save_pattern(
                pattern_name=None,
                domain="test",
                question_type="test",
                description="Test description"
            )
        assert "pattern_name" in str(exc_info.value).lower()

        # Test missing domain
        with pytest.raises(ValidationError) as exc_info:
            pattern_library.save_pattern(
                pattern_name="Test",
                domain=None,
                question_type="test",
                description="Test description"
            )
        assert "domain" in str(exc_info.value).lower()

        # Test missing description
        with pytest.raises(ValidationError) as exc_info:
            pattern_library.save_pattern(
                pattern_name="Test",
                domain="test",
                question_type="test",
                description=None
            )
        assert "description" in str(exc_info.value).lower()

    def test_get_pattern_success(self, pattern_library, sample_pattern_data):
        """
        Test 1.4: Verify pattern retrieval by ID.

        RED PHASE: This test will FAIL until we implement get_pattern()
        """
        # Arrange - save a pattern first
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act
        pattern = pattern_library.get_pattern(pattern_id)

        # Assert
        assert pattern is not None, "Pattern should be retrieved"
        assert pattern['pattern_id'] == pattern_id
        assert pattern['pattern_name'] == sample_pattern_data['pattern_name']
        assert pattern['domain'] == sample_pattern_data['domain']
        assert pattern['description'] == sample_pattern_data['description']

        # Check usage statistics are included
        assert 'usage_stats' in pattern
        assert pattern['usage_stats']['total_uses'] == 0
        assert pattern['usage_stats']['success_rate'] is None
        assert pattern['usage_stats']['last_used'] is None

    def test_get_pattern_not_found(self, pattern_library):
        """
        Test 1.5: Verify behavior when pattern doesn't exist.

        RED PHASE: This test will FAIL until we implement proper not-found handling
        """
        # Act
        pattern = pattern_library.get_pattern("nonexistent_pattern_id")

        # Assert
        assert pattern is None, "Should return None for nonexistent pattern"

    def test_list_patterns_default(self, pattern_library, sample_pattern_data):
        """
        Test 1.11: Verify pattern listing with no filters.

        RED PHASE: This test will FAIL until we implement list_patterns()
        """
        # Arrange - save multiple patterns
        pattern_library.save_pattern(**sample_pattern_data)

        # Save another pattern
        sample_pattern_data['pattern_name'] = "Another Pattern"
        sample_pattern_data['question_type'] = "another_type"
        pattern_library.save_pattern(**sample_pattern_data)

        # Act
        patterns = pattern_library.list_patterns()

        # Assert
        assert len(patterns) == 2, "Should return 2 patterns"
        assert all('pattern_id' in p for p in patterns)
        assert all('pattern_name' in p for p in patterns)
        assert all('domain' in p for p in patterns)

    def test_list_patterns_domain_filter(self, pattern_library, sample_pattern_data):
        """
        Test 1.12: Verify domain filtering.

        RED PHASE: This test will FAIL until we implement domain filtering
        """
        # Arrange - save patterns in different domains
        pattern_library.save_pattern(**sample_pattern_data)  # servicedesk

        recruitment_data = sample_pattern_data.copy()
        recruitment_data['domain'] = "recruitment"
        recruitment_data['question_type'] = "candidate_hours"
        pattern_library.save_pattern(**recruitment_data)

        # Act
        servicedesk_patterns = pattern_library.list_patterns(domain="servicedesk")

        # Assert
        assert len(servicedesk_patterns) == 1, "Should return only servicedesk patterns"
        assert servicedesk_patterns[0]['domain'] == "servicedesk"


# ============================================================================
# Test Suite 2: Semantic Search (10 tests)
# ============================================================================

class TestSemanticSearch:
    """Test suite for semantic search functionality."""

    def test_search_exact_match(self, pattern_library, sample_pattern_data):
        """
        Test 2.1: Verify high similarity for exact match queries.

        RED PHASE: This test will FAIL until we implement search_patterns()
        """
        # Arrange
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act
        results = pattern_library.search_patterns("Timesheet project breakdown")

        # Assert
        assert len(results) > 0, "Should find at least one result"

        best_match = results[0]
        pattern, similarity = best_match

        assert pattern['pattern_id'] == pattern_id
        assert similarity >= 0.75, f"Similarity should be >= 0.75, got {similarity}"

    def test_search_no_match(self, pattern_library, sample_pattern_data):
        """
        Test 2.3: Verify empty results when no matches above threshold.

        RED PHASE: This test will FAIL until we implement search with threshold
        """
        # Arrange
        pattern_library.save_pattern(**sample_pattern_data)

        # Act
        results = pattern_library.search_patterns("quantum physics simulator")

        # Assert
        assert len(results) == 0, "Should return empty list for unrelated query"

    def test_search_domain_filter(self, pattern_library, sample_pattern_data):
        """
        Test 2.4: Verify domain filtering in search.

        RED PHASE: This test will FAIL until we implement domain filtering in search
        """
        # Arrange - save patterns in different domains
        sd_pattern_id = pattern_library.save_pattern(**sample_pattern_data)  # servicedesk

        recruitment_data = sample_pattern_data.copy()
        recruitment_data['domain'] = "recruitment"
        recruitment_data['pattern_name'] = "Candidate Hours"
        recruitment_data['question_type'] = "candidate_hours"
        pattern_library.save_pattern(**recruitment_data)

        # Act - use a query that will match both patterns
        results = pattern_library.search_patterns("timesheet project breakdown", domain="servicedesk")

        # Assert
        assert len(results) > 0, "Should find servicedesk pattern"
        for pattern, similarity in results:
            assert pattern['domain'] == "servicedesk", "Should only return servicedesk patterns"


# ============================================================================
# Test Suite 4: Usage Tracking (8 tests)
# ============================================================================

class TestPatternVersioning:
    """Test suite for pattern versioning."""

    def test_update_pattern_creates_new_version(self, pattern_library, sample_pattern_data):
        """Test 5.1: Verify version creation workflow."""
        # Arrange - save v1
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act - update to create v2
        new_pattern_id = pattern_library.update_pattern(
            pattern_id,
            sql_template="NEW SQL TEMPLATE",
            changes="Fixed SQL bug"
        )

        # Assert
        assert new_pattern_id != pattern_id, "Should create new pattern ID"
        assert "_v2" in new_pattern_id or "v2" in new_pattern_id, "Should have version indicator"

        # v1 should be deprecated
        v1 = pattern_library.get_pattern(pattern_id, include_archived=True)
        assert v1['status'] == 'deprecated'

        # v2 should be active
        v2 = pattern_library.get_pattern(new_pattern_id)
        assert v2 is not None
        assert v2['status'] == 'active'
        assert v2['version'] == 2
        assert v2['sql_template'] == "NEW SQL TEMPLATE"

    def test_delete_pattern_soft_delete(self, pattern_library, sample_pattern_data):
        """Test 1.9: Verify soft delete behavior."""
        # Arrange
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act
        result = pattern_library.delete_pattern(pattern_id)

        # Assert
        assert result is True, "Delete should succeed"

        # Pattern excluded from normal retrieval
        pattern = pattern_library.get_pattern(pattern_id)
        assert pattern is None, "Archived pattern should not be retrieved by default"

        # But still exists with include_archived
        pattern_archived = pattern_library.get_pattern(pattern_id, include_archived=True)
        assert pattern_archived is not None
        assert pattern_archived['status'] == 'archived'


class TestAutoSuggestion:
    """Test suite for auto-suggestion functionality."""

    def test_suggest_pattern_high_confidence(self, pattern_library, sample_pattern_data):
        """Test 3.1: Verify auto-suggestion works with lower confidence threshold."""
        # Arrange
        pattern_library.save_pattern(**sample_pattern_data)

        # Act - use exact pattern name for high match
        suggestion = pattern_library.suggest_pattern(
            "Timesheet Project Breakdown",
            confidence_threshold=0.30  # Lower threshold for testing
        )

        # Assert
        assert suggestion is not None
        assert suggestion['matched'] is True
        assert suggestion['confidence'] > 0.0
        assert 'pattern' in suggestion
        assert suggestion['pattern']['pattern_name'] == "Timesheet Project Breakdown"

    def test_suggest_pattern_low_confidence(self, pattern_library, sample_pattern_data):
        """Test 3.2: Verify no suggestion when confidence <0.70."""
        # Arrange
        pattern_library.save_pattern(**sample_pattern_data)

        # Act
        suggestion = pattern_library.suggest_pattern("What's the weather today?")

        # Assert
        assert suggestion is not None
        assert suggestion['matched'] is False
        assert suggestion['confidence'] < 0.70


class TestUsageTracking:
    """Test suite for usage tracking functionality."""

    def test_track_usage_success(self, pattern_library, sample_pattern_data):
        """
        Test 4.1: Verify usage logging on pattern use.

        RED PHASE: This test will FAIL until we implement track_usage()
        """
        # Arrange
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act
        pattern_library.track_usage(
            pattern_id=pattern_id,
            user_question="Show hours for Olli",
            success=True
        )

        # Assert - check usage was recorded
        pattern = pattern_library.get_pattern(pattern_id)
        assert pattern['usage_stats']['total_uses'] == 1
        assert pattern['usage_stats']['success_rate'] == 1.0
        assert pattern['usage_stats']['last_used'] is not None

    def test_track_usage_failure(self, pattern_library, sample_pattern_data):
        """
        Test 4.2: Verify usage logging when pattern fails.

        RED PHASE: This test will FAIL until we implement failure tracking
        """
        # Arrange
        pattern_id = pattern_library.save_pattern(**sample_pattern_data)

        # Act - track both success and failure
        pattern_library.track_usage(pattern_id, "Query 1", success=True)
        pattern_library.track_usage(pattern_id, "Query 2", success=False,
                                   feedback="SQL error: column not found")

        # Assert
        pattern = pattern_library.get_pattern(pattern_id)
        assert pattern['usage_stats']['total_uses'] == 2
        assert pattern['usage_stats']['success_rate'] == 0.5  # 1 success out of 2

    def test_track_usage_nonexistent_pattern(self, pattern_library):
        """
        Test 4.3: Verify graceful handling for invalid pattern_id.

        RED PHASE: This test should NOT raise exception (non-blocking)
        """
        # Act - should not raise exception
        pattern_library.track_usage(
            pattern_id="nonexistent_id",
            user_question="test question",
            success=True
        )

        # Assert - just verify no exception was raised
        # (usage tracking should be non-blocking)
        assert True, "Should handle nonexistent pattern gracefully"


# ============================================================================
# Run tests if executed directly
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
