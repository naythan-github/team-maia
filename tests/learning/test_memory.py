#!/usr/bin/env python3
"""
Tests for Phase 3: Maia Memory System (TDD)

Tests session history recording, summaries, and full-text search.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch


class TestMaiaMemoryInit:
    """Tests for MaiaMemory initialization."""

    def test_memory_creates_database_if_missing(self):
        """Test that MaiaMemory creates database if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                db_path = fake_home / ".maia" / "memory" / "memory.db"
                assert db_path.exists()

    def test_memory_creates_summaries_directory(self):
        """Test that MaiaMemory creates summaries directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                summaries_dir = fake_home / ".maia" / "memory" / "summaries"
                assert summaries_dir.exists()


class TestMemorySessionLifecycle:
    """Tests for session start and end."""

    def test_start_session_records_session(self):
        """Test that start_session creates a session record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                session_id = memory.start_session(
                    session_id="test_session_001",
                    context_id="ctx_12345",
                    initial_query="Fix the authentication bug",
                    agent_used="security_agent",
                    domain="security"
                )

                assert session_id == "test_session_001"

                # Verify in database
                recent = memory.get_recent(1)
                assert len(recent) == 1
                assert recent[0]['id'] == "test_session_001"
                assert recent[0]['initial_query'] == "Fix the authentication bug"
                assert recent[0]['status'] == "active"

    def test_end_session_updates_record(self):
        """Test that end_session updates session with summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Start session
                memory.start_session(
                    session_id="test_session",
                    context_id="ctx_1",
                    initial_query="Fix the bug",
                    agent_used="sre_agent",
                    domain="sre"
                )

                # End session
                memory.end_session(
                    session_id="test_session",
                    summary_text="Fixed the memory leak in auth module",
                    key_decisions=["Used profiler to find leak", "Applied fix to cache"],
                    tools_used={"bash": 5, "read": 10, "edit": 3},
                    files_touched=["auth.py", "cache.py"],
                    verify_success=True,
                    verify_confidence=0.85,
                    verify_metrics={"tool_success": 0.95},
                    learn_insights=[{"type": "workflow", "description": "Memory profiling"}],
                    status="completed"
                )

                # Verify
                recent = memory.get_recent(1)
                assert recent[0]['status'] == "completed"
                assert recent[0]['summary_text'] == "Fixed the memory leak in auth module"
                assert recent[0]['verify_success'] == 1  # SQLite boolean
                assert recent[0]['verify_confidence'] == 0.85

    def test_end_session_writes_summary_file(self):
        """Test that end_session creates markdown summary file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory
                from datetime import datetime

                memory = MaiaMemory()

                memory.start_session(
                    session_id="test_session",
                    context_id="ctx_1",
                    initial_query="Test query"
                )

                memory.end_session(
                    session_id="test_session",
                    summary_text="Test summary",
                    key_decisions=["Decision 1"],
                    tools_used={"bash": 1},
                    files_touched=[],
                    verify_success=True,
                    verify_confidence=0.8,
                    verify_metrics={},
                    learn_insights=[]
                )

                # Check summary file exists
                today = datetime.now().strftime("%Y-%m-%d")
                summary_file = fake_home / ".maia" / "memory" / "summaries" / today / "test_session.md"
                assert summary_file.exists()

                content = summary_file.read_text()
                assert "Test summary" in content
                assert "Decision 1" in content


class TestMemorySearch:
    """Tests for Maia Memory full-text search."""

    def test_search_finds_matching_sessions(self):
        """Test that search finds sessions by query text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Create sessions
                memory.start_session("s1", "ctx", "Fix authentication bug")
                memory.end_session("s1", "Fixed OAuth issue", [], {}, [], True, 0.9, {}, [])

                memory.start_session("s2", "ctx", "Optimize database queries")
                memory.end_session("s2", "Improved query performance", [], {}, [], True, 0.8, {}, [])

                memory.start_session("s3", "ctx", "Fix login authentication")
                memory.end_session("s3", "Fixed login flow", [], {}, [], True, 0.85, {}, [])

                # Search for authentication
                results = memory.search("authentication")

                assert len(results) >= 2
                session_ids = {r['id'] for r in results}
                assert "s1" in session_ids
                assert "s3" in session_ids

    def test_search_returns_empty_for_no_match(self):
        """Test that search returns empty list when no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.start_session("s1", "ctx", "Fix authentication bug")
                memory.end_session("s1", "Fixed OAuth", [], {}, [], True, 0.9, {}, [])

                results = memory.search("kubernetes deployment")
                assert len(results) == 0

    def test_search_respects_limit(self):
        """Test that search respects limit parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Create many sessions
                for i in range(10):
                    memory.start_session(f"s{i}", "ctx", f"Fix bug {i}")
                    memory.end_session(f"s{i}", f"Fixed bug {i}", [], {}, [], True, 0.9, {}, [])

                results = memory.search("bug", limit=3)
                assert len(results) == 3


class TestMemoryQueries:
    """Tests for Maia Memory query methods."""

    def test_get_recent_returns_latest_sessions(self):
        """Test that get_recent returns sessions in reverse chronological order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory
                import time

                memory = MaiaMemory()

                memory.start_session("s1", "ctx", "First session")
                time.sleep(0.01)
                memory.start_session("s2", "ctx", "Second session")
                time.sleep(0.01)
                memory.start_session("s3", "ctx", "Third session")

                recent = memory.get_recent(2)

                assert len(recent) == 2
                assert recent[0]['id'] == "s3"
                assert recent[1]['id'] == "s2"

    def test_get_by_domain_filters_correctly(self):
        """Test that get_by_domain returns only matching domain sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.start_session("s1", "ctx", "Security fix", domain="security")
                memory.start_session("s2", "ctx", "SRE task", domain="sre")
                memory.start_session("s3", "ctx", "Another security fix", domain="security")

                security_sessions = memory.get_by_domain("security")

                assert len(security_sessions) == 2
                assert all(s['domain'] == 'security' for s in security_sessions)

    def test_get_context_for_query(self):
        """Test that get_context_for_query returns relevant context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.start_session("s1", "ctx", "Fix memory leak in auth")
                memory.end_session("s1", "Found and fixed cache not being cleared", [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("memory leak")

                assert "Relevant Prior Sessions" in context
                assert "memory leak" in context.lower() or "cache" in context.lower()

    def test_get_context_returns_empty_for_no_match(self):
        """Test that get_context_for_query returns empty string when no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.start_session("s1", "ctx", "Fix authentication")
                memory.end_session("s1", "Fixed OAuth", [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("kubernetes deployment helm")
                assert context == ""


class TestMemorySingleton:
    """Tests for Maia Memory singleton pattern."""

    def test_get_memory_returns_singleton(self):
        """Test that get_memory returns same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                import claude.tools.learning.memory as memory_module
                memory_module._memory = None  # Reset singleton

                from claude.tools.learning.memory import get_memory

                memory1 = get_memory()
                memory2 = get_memory()

                assert memory1 is memory2


class TestMemoryDataIntegrity:
    """Tests for data integrity and JSON handling."""

    def test_key_decisions_stored_as_json(self):
        """Test that key_decisions are properly stored and retrieved as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                decisions = ["Used profiler", "Applied caching", "Added tests"]

                memory.start_session("s1", "ctx", "Task")
                memory.end_session("s1", "Done", decisions, {}, [], True, 0.9, {}, [])

                recent = memory.get_recent(1)
                stored_decisions = json.loads(recent[0]['key_decisions'])

                assert stored_decisions == decisions

    def test_tools_used_stored_as_json(self):
        """Test that tools_used are properly stored and retrieved as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                tools = {"bash": 10, "read": 5, "edit": 3}

                memory.start_session("s1", "ctx", "Task")
                memory.end_session("s1", "Done", [], tools, [], True, 0.9, {}, [])

                recent = memory.get_recent(1)
                stored_tools = json.loads(recent[0]['tools_used'])

                assert stored_tools == tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
