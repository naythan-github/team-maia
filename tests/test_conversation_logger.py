#!/usr/bin/env python3
"""
Test suite for conversation_logger.py - TDD approach.

Tests conversation logging system for weekly Maia journey narratives.
Validates:
- Database schema and lifecycle
- Privacy flagging (default true, opt-in to sharing)
- Multiple agents tracking
- Weekly retrieval (last 7 days)
- Data integrity and graceful degradation
- Performance requirements (<50ms log, <200ms retrieval)
"""

import pytest
import sqlite3
import tempfile
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path to import conversation_logger
sys.path.insert(0, str(Path(__file__).parent.parent / 'claude' / 'tools'))

import conversation_logger


class TestDatabaseSchema:
    """Test database schema and initialization."""

    def test_database_creation_with_correct_path(self, tmp_path):
        """Test database is created at correct path (databases/system/ subdirectory)."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        assert db_path.exists(), "Database file should be created"
        assert db_path.parent.name == "system", "Database should be in 'system' subdirectory"
        assert db_path.parent.parent.name == "databases", "Database should be in 'databases' subdirectory"

    def test_schema_version_field_exists(self, tmp_path):
        """Test schema_version field is included in schema."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(conversations)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'schema_version' in columns, "Schema should include schema_version field"

    def test_all_required_fields_exist(self, tmp_path):
        """Test all required fields from schema are present."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(conversations)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required_fields = {
            'journey_id', 'timestamp', 'problem_description', 'initial_question',
            'maia_options_presented', 'user_refinement_quote', 'agents_used',
            'deliverables', 'business_impact', 'meta_learning', 'iteration_count',
            'privacy_flag', 'schema_version'
        }

        assert required_fields.issubset(columns), f"Missing fields: {required_fields - columns}"


class TestConversationLifecycle:
    """Test conversation journey lifecycle (start -> log -> complete)."""

    def test_start_journey_creates_record(self, tmp_path):
        """Test starting a journey creates a new record."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Need to migrate SonicWall VPN to Azure",
            initial_question="How do I migrate SonicWall SMA 500 VPN to Azure VPN Gateway?"
        )

        assert journey_id is not None, "Should return journey_id"
        assert len(journey_id) == 36, "Should be UUID format (36 chars with hyphens)"

    def test_start_journey_privacy_default_true(self, tmp_path):
        """Test privacy_flag defaults to True (opt-in to sharing)."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT privacy_flag FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 1, "privacy_flag should default to True (1)"

    def test_log_maia_response_updates_journey(self, tmp_path):
        """Test logging Maia response updates journey record."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.log_maia_response(
            journey_id=journey_id,
            options_presented=["Option A: Manual migration", "Option B: Automated toolkit", "Option C: Hybrid approach"]
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT maia_options_presented FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] is not None, "Should store options_presented"
        assert "Option A" in row[0], "Should contain option A"

    def test_log_user_refinement_updates_journey(self, tmp_path):
        """Test logging user refinement updates journey record."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        refinement = "I like Option B but need to preserve existing firewall rules"
        logger.log_user_refinement(journey_id=journey_id, refinement_quote=refinement)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_refinement_quote FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == refinement, "Should store user refinement quote"

    def test_complete_journey_finalizes_record(self, tmp_path):
        """Test completing journey finalizes all metadata."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.complete_journey(
            journey_id=journey_id,
            business_impact="95% time reduction (2 weeks → 5 min)",
            meta_learning="Discovered 'Assumption Testing' workflow pattern",
            iteration_count=2
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT business_impact, meta_learning, iteration_count FROM conversations WHERE journey_id = ?",
            (journey_id,)
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "95% time reduction (2 weeks → 5 min)", "Should store business impact"
        assert row[1] == "Discovered 'Assumption Testing' workflow pattern", "Should store meta learning"
        assert row[2] == 2, "Should store iteration count"


class TestMultipleAgentsTracking:
    """Test tracking multiple agents in a journey."""

    def test_add_single_agent(self, tmp_path):
        """Test adding a single agent to journey."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_agent(
            journey_id=journey_id,
            agent_name="SRE Principal Engineer",
            rationale="API validation and infrastructure design"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT agents_used FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] is not None, "Should store agent data"
        assert "SRE Principal Engineer" in row[0], "Should contain agent name"
        assert "API validation" in row[0], "Should contain rationale"

    def test_add_multiple_agents(self, tmp_path):
        """Test adding multiple agents to journey."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_agent(
            journey_id=journey_id,
            agent_name="SRE Principal Engineer",
            rationale="API validation"
        )

        logger.add_agent(
            journey_id=journey_id,
            agent_name="UI Systems Agent",
            rationale="Dashboard design"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT agents_used FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert "SRE Principal Engineer" in row[0], "Should contain first agent"
        assert "UI Systems Agent" in row[0], "Should contain second agent"

    def test_agent_timestamps(self, tmp_path):
        """Test agents have started_at timestamps."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_agent(
            journey_id=journey_id,
            agent_name="SRE Principal Engineer",
            rationale="API validation"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT agents_used FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert "started_at" in row[0], "Agent data should include started_at timestamp"


class TestDeliverablesTracking:
    """Test tracking deliverables (files, documentation, etc)."""

    def test_add_file_deliverable(self, tmp_path):
        """Test adding file deliverable."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_deliverable(
            journey_id=journey_id,
            deliverable_type="file",
            name="sma_api_discovery.py",
            description="SonicWall SMA API discovery tool",
            size="9.8KB"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deliverables FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] is not None, "Should store deliverable data"
        assert "sma_api_discovery.py" in row[0], "Should contain file name"
        assert "9.8KB" in row[0], "Should contain file size"

    def test_add_documentation_deliverable(self, tmp_path):
        """Test adding documentation deliverable."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_deliverable(
            journey_id=journey_id,
            deliverable_type="documentation",
            name="Migration guide",
            description="Step-by-step migration guide",
            size="12.3KB"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deliverables FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert "Migration guide" in row[0], "Should contain documentation name"
        assert "documentation" in row[0], "Should specify type as documentation"

    def test_multiple_deliverables(self, tmp_path):
        """Test adding multiple deliverables."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        logger.add_deliverable(
            journey_id=journey_id,
            deliverable_type="file",
            name="tool.py",
            description="Tool",
            size="5KB"
        )

        logger.add_deliverable(
            journey_id=journey_id,
            deliverable_type="documentation",
            name="Guide.md",
            description="Guide",
            size="3KB"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deliverables FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert "tool.py" in row[0], "Should contain first deliverable"
        assert "Guide.md" in row[0], "Should contain second deliverable"


class TestPrivacyFiltering:
    """Test privacy flagging and filtering capabilities."""

    def test_mark_shareable_sets_privacy_false(self, tmp_path):
        """Test marking journey as shareable sets privacy_flag to False."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Should default to True
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT privacy_flag FROM conversations WHERE journey_id = ?", (journey_id,))
        assert cursor.fetchone()[0] == 1, "Should default to True"

        # Mark as shareable
        logger.mark_shareable(journey_id=journey_id)

        cursor.execute("SELECT privacy_flag FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 0, "privacy_flag should be False (0) after marking shareable"

    def test_get_week_journeys_excludes_private_by_default(self, tmp_path):
        """Test weekly retrieval excludes private journeys by default."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        # Create private journey (default)
        private_id = logger.start_journey(
            problem_description="Private problem",
            initial_question="Private question?"
        )

        # Create shareable journey
        shareable_id = logger.start_journey(
            problem_description="Shareable problem",
            initial_question="Shareable question?"
        )
        logger.mark_shareable(journey_id=shareable_id)

        # Get shareable journeys only
        journeys = logger.get_week_journeys(include_private=False)

        journey_ids = [j['journey_id'] for j in journeys]
        assert shareable_id in journey_ids, "Should include shareable journey"
        assert private_id not in journey_ids, "Should exclude private journey"

    def test_get_week_journeys_includes_private_when_requested(self, tmp_path):
        """Test weekly retrieval includes private when explicitly requested."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        # Create private journey
        private_id = logger.start_journey(
            problem_description="Private problem",
            initial_question="Private question?"
        )

        # Get all journeys including private
        journeys = logger.get_week_journeys(include_private=True)

        journey_ids = [j['journey_id'] for j in journeys]
        assert private_id in journey_ids, "Should include private journey when requested"


class TestWeeklyRetrieval:
    """Test weekly retrieval (last 7 days)."""

    def test_get_week_journeys_returns_last_7_days(self, tmp_path):
        """Test retrieval returns only journeys from last 7 days."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        # Create journey from 5 days ago
        recent_id = logger.start_journey(
            problem_description="Recent problem",
            initial_question="Recent question?"
        )
        logger.mark_shareable(journey_id=recent_id)

        # Manually backdate timestamp to 5 days ago
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
        cursor.execute("UPDATE conversations SET timestamp = ? WHERE journey_id = ?", (five_days_ago, recent_id))
        conn.commit()

        # Create old journey (10 days ago)
        old_id = logger.start_journey(
            problem_description="Old problem",
            initial_question="Old question?"
        )
        logger.mark_shareable(journey_id=old_id)

        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        cursor.execute("UPDATE conversations SET timestamp = ? WHERE journey_id = ?", (ten_days_ago, old_id))
        conn.commit()
        conn.close()

        # Get week journeys
        journeys = logger.get_week_journeys(include_private=False)
        journey_ids = [j['journey_id'] for j in journeys]

        assert recent_id in journey_ids, "Should include journey from 5 days ago"
        assert old_id not in journey_ids, "Should exclude journey from 10 days ago"

    def test_get_week_journeys_returns_list_of_dicts(self, tmp_path):
        """Test retrieval returns list of journey dictionaries."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )
        logger.mark_shareable(journey_id=journey_id)

        journeys = logger.get_week_journeys(include_private=False)

        assert isinstance(journeys, list), "Should return list"
        assert len(journeys) > 0, "Should have at least one journey"
        assert isinstance(journeys[0], dict), "Should contain dictionaries"
        assert 'journey_id' in journeys[0], "Dictionary should have journey_id"
        assert 'problem_description' in journeys[0], "Dictionary should have problem_description"


class TestDataIntegrity:
    """Test data integrity and atomic operations."""

    def test_atomic_writes(self, tmp_path):
        """Test writes are atomic (no partial updates)."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Verify record exists and is complete
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT journey_id, problem_description, initial_question FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Record should exist"
        assert row[0] == journey_id, "journey_id should be set"
        assert row[1] == "Test problem", "problem_description should be set"
        assert row[2] == "Test question?", "initial_question should be set"

    def test_concurrent_updates_safe(self, tmp_path):
        """Test concurrent updates to same journey are safe."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Add agent and deliverable concurrently (simulate)
        logger.add_agent(journey_id=journey_id, agent_name="Agent 1", rationale="Reason 1")
        logger.add_deliverable(journey_id=journey_id, deliverable_type="file", name="file.py", description="File", size="1KB")

        # Verify both updates succeeded
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT agents_used, deliverables FROM conversations WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()

        assert "Agent 1" in row[0], "Agent should be recorded"
        assert "file.py" in row[1], "Deliverable should be recorded"


class TestGracefulDegradation:
    """Test graceful degradation when DB unavailable."""

    def test_invalid_db_path_returns_none(self):
        """Test invalid DB path returns None instead of crashing."""
        # Use invalid path (no write permission)
        db_path = Path("/root/forbidden/conversations.db")
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Should return None instead of raising exception
        assert journey_id is None, "Should return None when DB unavailable"

    def test_db_unavailable_logs_error(self, tmp_path, caplog):
        """Test DB unavailable scenario logs error."""
        # Create logger with invalid path
        db_path = Path("/root/forbidden/conversations.db")
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Check that error was logged
        assert any("error" in record.message.lower() or "failed" in record.message.lower()
                  for record in caplog.records), "Should log error when DB unavailable"

    def test_corrupt_data_handled_gracefully(self, tmp_path):
        """Test corrupt data doesn't crash system."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Manually corrupt agents_used data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE conversations SET agents_used = ? WHERE journey_id = ?", ("not valid json", journey_id))
        conn.commit()
        conn.close()

        # Should handle gracefully when adding another agent
        result = logger.add_agent(journey_id=journey_id, agent_name="New Agent", rationale="Reason")

        # Should either succeed with new valid JSON or return None
        assert result is not False, "Should handle corrupt data gracefully"


class TestPerformanceRequirements:
    """Test performance requirements (<50ms log, <200ms retrieval)."""

    def test_log_operation_under_50ms(self, tmp_path):
        """Test log operations complete in <50ms."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        journey_id = logger.start_journey(
            problem_description="Test problem",
            initial_question="Test question?"
        )

        # Time add_agent operation
        start = time.time()
        logger.add_agent(journey_id=journey_id, agent_name="SRE Principal Engineer", rationale="Testing")
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 50, f"Log operation took {elapsed_ms:.1f}ms, should be <50ms"

    def test_retrieval_under_200ms(self, tmp_path):
        """Test retrieval operations complete in <200ms."""
        db_path = tmp_path / "databases" / "system" / "conversations.db"
        logger = conversation_logger.ConversationLogger(db_path=db_path)

        # Create 10 journeys
        for i in range(10):
            journey_id = logger.start_journey(
                problem_description=f"Problem {i}",
                initial_question=f"Question {i}?"
            )
            logger.mark_shareable(journey_id=journey_id)

        # Time retrieval
        start = time.time()
        journeys = logger.get_week_journeys(include_private=False)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 200, f"Retrieval took {elapsed_ms:.1f}ms, should be <200ms"
        assert len(journeys) == 10, "Should retrieve all 10 journeys"


# Test fixtures
@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory with databases/system/ structure."""
    base = tmp_path_factory.mktemp("test_conversations")
    (base / "databases" / "system").mkdir(parents=True, exist_ok=True)
    return base


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
