#!/usr/bin/env python3
"""
Tests for P1: Context Injection - Auto-inject relevant prior sessions on init (TDD)

Phase 234: Context injection into session start flow.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestContextInjection:
    """Tests for context injection on session start."""

    def test_get_context_for_query_returns_relevant_sessions(self):
        """Test that get_context_for_query returns relevant prior sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Create some historical sessions
                memory.start_session("s1", "ctx1", "Fix authentication bug in OAuth")
                memory.end_session("s1", "Fixed token refresh logic",
                                   ["Used debugger"], {"bash": 5}, [], True, 0.9, {}, [])

                memory.start_session("s2", "ctx2", "Optimize database queries")
                memory.end_session("s2", "Added indexes", [], {"bash": 3}, [], True, 0.8, {}, [])

                # Query for authentication-related context
                context = memory.get_context_for_query("authentication")

                assert "Relevant Prior Sessions" in context
                assert "authentication" in context.lower() or "oauth" in context.lower()

    def test_get_context_for_query_returns_empty_when_no_matches(self):
        """Test that get_context_for_query returns empty string when no relevant sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.start_session("s1", "ctx1", "Fix CSS styling")
                memory.end_session("s1", "Updated colors", [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("kubernetes deployment helm")
                assert context == ""

    def test_get_context_respects_limit(self):
        """Test that get_context_for_query respects limit parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Create many sessions about "bug"
                for i in range(10):
                    memory.start_session(f"s{i}", "ctx", f"Fix bug {i}")
                    memory.end_session(f"s{i}", f"Fixed bug {i}", [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("bug", limit=2)

                # Should have limited results
                # Count occurrences of "###" which marks each session
                session_count = context.count("###")
                assert session_count <= 2


class TestContextInjectionIntegration:
    """Tests for context injection integration with session manager."""

    def test_session_manager_get_relevant_context(self):
        """Test SessionManager.get_relevant_context method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Create historical session via memory directly
                manager.memory.start_session("s1", "ctx1", "Deploy to production")
                manager.memory.end_session("s1", "Deployed app successfully",
                                           [], {"bash": 10}, [], True, 0.9, {}, [])

                # Get relevant context
                context = manager.get_relevant_context("deploy production")

                assert context != ""
                assert "deploy" in context.lower() or "production" in context.lower()

    def test_session_manager_get_relevant_context_empty(self):
        """Test SessionManager.get_relevant_context returns empty when no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singletons for clean test
                import claude.tools.learning.memory as memory_module
                import claude.tools.learning.session as session_module
                memory_module._memory = None
                session_module._manager = None

                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                context = manager.get_relevant_context("unrelated query xyz")
                assert context == ""


class TestContextInjectionHelper:
    """Tests for the context injection helper function."""

    def test_get_learning_context_returns_context(self):
        """Test get_learning_context helper function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                # Setup historical data
                memory = MaiaMemory()
                memory.start_session("s1", "ctx", "Fix memory leak")
                memory.end_session("s1", "Found and fixed cache issue", [], {}, [], True, 0.9, {}, [])

                # Import and test helper
                from claude.tools.learning.context_injection import get_learning_context

                context = get_learning_context("memory leak")

                assert "Relevant Prior Sessions" in context or context == ""

    def test_get_learning_context_graceful_degradation(self):
        """Test get_learning_context returns empty on errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            # Don't create the database - simulate error
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.context_injection import get_learning_context

                # Should not raise, just return empty
                context = get_learning_context("any query")
                assert isinstance(context, str)


class TestContextInjectionFormat:
    """Tests for context injection output format."""

    def test_context_format_includes_date(self):
        """Test that context includes session date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.start_session("s1", "ctx", "Test query")
                memory.end_session("s1", "Test summary", [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("test")

                # Should include date format YYYY-MM-DD
                import re
                assert re.search(r'\d{4}-\d{2}-\d{2}', context)

    def test_context_truncates_long_summaries(self):
        """Test that very long summaries are truncated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Create session with very long summary
                long_summary = "x" * 1000
                memory.start_session("s1", "ctx", "Long session")
                memory.end_session("s1", long_summary, [], {}, [], True, 0.9, {}, [])

                context = memory.get_context_for_query("long session")

                # Summary should be truncated to 500 chars
                assert len(context) < len(long_summary) + 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
