#!/usr/bin/env python3
"""
Tests for Prompt Capture System (TDD)

Sprint: SPRINT-002-PROMPT-CAPTURE
Phase 1: Schema tests (session_prompts table, FTS5)
Phase 2: Memory API tests (capture, retrieval, search)
Phase 3: Hook tests (non-blocking, error handling)
Phase 4: Export tests (JSONL, Markdown, CSV)
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch


# =============================================================================
# Phase 1: Schema Tests
# =============================================================================

class TestPromptsSchema:
    """Tests for session_prompts table schema."""

    def test_prompts_table_created(self):
        """session_prompts table should be created when initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory._ensure_prompts_initialized()

                conn = memory._get_conn()
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='session_prompts'"
                )
                result = cursor.fetchone()
                conn.close()

                assert result is not None, "session_prompts table should exist"

    def test_prompts_fts_table_created(self):
        """FTS5 virtual table for prompts should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory._ensure_prompts_initialized()

                conn = memory._get_conn()
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='prompts_fts'"
                )
                result = cursor.fetchone()
                conn.close()

                assert result is not None, "prompts_fts FTS5 table should exist"

    def test_prompts_table_has_required_columns(self):
        """session_prompts should have all required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory._ensure_prompts_initialized()

                conn = memory._get_conn()
                cursor = conn.execute("PRAGMA table_info(session_prompts)")
                columns = {row[1] for row in cursor.fetchall()}
                conn.close()

                required = {
                    'prompt_id', 'session_id', 'context_id', 'prompt_index',
                    'prompt_text', 'timestamp', 'char_count', 'word_count',
                    'agent_active', 'prompt_hash'
                }
                assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_prompts_unique_constraint(self):
        """session_id + prompt_index should be unique."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory
                import sqlite3

                memory = MaiaMemory()
                memory._ensure_prompts_initialized()

                conn = memory._get_conn()
                # Insert first prompt
                conn.execute("""
                    INSERT INTO session_prompts
                    (session_id, context_id, prompt_index, prompt_text, timestamp, char_count, word_count)
                    VALUES ('s1', 'ctx1', 0, 'test', '2026-01-01', 4, 1)
                """)
                conn.commit()

                # Try duplicate - should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO session_prompts
                        (session_id, context_id, prompt_index, prompt_text, timestamp, char_count, word_count)
                        VALUES ('s1', 'ctx1', 0, 'duplicate', '2026-01-01', 9, 1)
                    """)
                conn.close()


# =============================================================================
# Phase 2: Memory API Tests
# =============================================================================

class TestPromptCapture:
    """Tests for capture_prompt() API."""

    def test_capture_prompt_returns_id(self):
        """capture_prompt should return a prompt_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                prompt_id = memory.capture_prompt(
                    session_id="test_session",
                    context_id="ctx_123",
                    prompt_text="Help me debug this code"
                )

                assert prompt_id is not None
                assert isinstance(prompt_id, int)
                assert prompt_id > 0

    def test_capture_prompt_increments_index(self):
        """prompt_index should auto-increment per session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.capture_prompt("s1", "ctx", "First prompt")
                memory.capture_prompt("s1", "ctx", "Second prompt")
                memory.capture_prompt("s1", "ctx", "Third prompt")

                prompts = memory.get_prompts_for_session("s1")
                assert len(prompts) == 3
                assert prompts[0]['prompt_index'] == 0
                assert prompts[1]['prompt_index'] == 1
                assert prompts[2]['prompt_index'] == 2

    def test_capture_prompt_separate_sessions(self):
        """Different sessions should have independent prompt indices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                memory.capture_prompt("s1", "ctx", "Session 1 first")
                memory.capture_prompt("s2", "ctx", "Session 2 first")
                memory.capture_prompt("s1", "ctx", "Session 1 second")

                s1_prompts = memory.get_prompts_for_session("s1")
                s2_prompts = memory.get_prompts_for_session("s2")

                assert s1_prompts[0]['prompt_index'] == 0
                assert s1_prompts[1]['prompt_index'] == 1
                assert s2_prompts[0]['prompt_index'] == 0

    def test_capture_calculates_char_count(self):
        """Should calculate char_count correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                text = "Hello world test prompt"
                memory.capture_prompt("s1", "ctx", text)

                prompts = memory.get_prompts_for_session("s1")
                assert prompts[0]['char_count'] == len(text)

    def test_capture_calculates_word_count(self):
        """Should calculate word_count correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Hello world test prompt")

                prompts = memory.get_prompts_for_session("s1")
                assert prompts[0]['word_count'] == 4

    def test_capture_stores_agent_active(self):
        """Should store agent_active if provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Test", agent_active="sre_agent")

                prompts = memory.get_prompts_for_session("s1")
                assert prompts[0]['agent_active'] == "sre_agent"

    def test_capture_generates_hash(self):
        """Should generate prompt_hash for deduplication."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Test prompt")

                prompts = memory.get_prompts_for_session("s1")
                assert prompts[0]['prompt_hash'] is not None
                assert len(prompts[0]['prompt_hash']) == 64  # SHA256 hex


class TestPromptRetrieval:
    """Tests for get_prompts_for_session() API."""

    def test_get_prompts_returns_ordered(self):
        """Prompts should be returned in prompt_index order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "First")
                memory.capture_prompt("s1", "ctx", "Second")
                memory.capture_prompt("s1", "ctx", "Third")

                prompts = memory.get_prompts_for_session("s1")
                assert prompts[0]['prompt_text'] == "First"
                assert prompts[1]['prompt_text'] == "Second"
                assert prompts[2]['prompt_text'] == "Third"

    def test_get_prompts_empty_session(self):
        """Should return empty list for session with no prompts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                prompts = memory.get_prompts_for_session("nonexistent")
                assert prompts == []

    def test_get_prompts_returns_all_fields(self):
        """Returned prompts should include all expected fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Test prompt")

                prompts = memory.get_prompts_for_session("s1")
                prompt = prompts[0]

                assert 'prompt_id' in prompt
                assert 'session_id' in prompt
                assert 'context_id' in prompt
                assert 'prompt_index' in prompt
                assert 'prompt_text' in prompt
                assert 'timestamp' in prompt
                assert 'char_count' in prompt
                assert 'word_count' in prompt


class TestPromptSearch:
    """Tests for search_prompts() API."""

    def test_search_finds_matching_prompts(self):
        """FTS search should find matching prompts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Fix the authentication bug")
                memory.capture_prompt("s1", "ctx", "Optimize database queries")
                memory.capture_prompt("s2", "ctx", "Debug authentication flow")

                results = memory.search_prompts("authentication")
                assert len(results) == 2

    def test_search_respects_limit(self):
        """Search should respect limit parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                for i in range(10):
                    memory.capture_prompt("s1", "ctx", f"Bug fix number {i}")

                results = memory.search_prompts("bug", limit=3)
                assert len(results) == 3

    def test_search_returns_empty_for_no_match(self):
        """Search should return empty list when no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Fix authentication")

                results = memory.search_prompts("kubernetes")
                assert len(results) == 0

    def test_search_includes_relevance(self):
        """Search results should include relevance score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Fix the bug")

                results = memory.search_prompts("bug")
                assert len(results) > 0
                assert 'relevance' in results[0]


class TestPromptStats:
    """Tests for get_prompt_stats() API."""

    def test_stats_returns_counts(self):
        """Should return prompt count and character totals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Hello")  # 5 chars
                memory.capture_prompt("s1", "ctx", "World")  # 5 chars

                stats = memory.get_prompt_stats("s1")
                assert stats['prompt_count'] == 2
                assert stats['total_chars'] == 10

    def test_stats_global(self):
        """Should return global stats when no session specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Hello")
                memory.capture_prompt("s2", "ctx", "World")

                stats = memory.get_prompt_stats()
                assert stats['prompt_count'] == 2
                assert stats['unique_sessions'] == 2


# =============================================================================
# Phase 3: Hook Tests (placeholder - will extend)
# =============================================================================

class TestPromptHook:
    """Tests for prompt_capture.py hook."""

    def test_hook_module_exists(self):
        """prompt_capture hook module should be importable."""
        try:
            from claude.hooks import prompt_capture
            assert hasattr(prompt_capture, 'capture_prompt')
        except ImportError:
            pytest.skip("Hook not implemented yet")

    def test_hook_handles_missing_session(self):
        """Hook should handle missing session gracefully."""
        try:
            from claude.hooks.prompt_capture import capture_prompt

            result = capture_prompt({
                'prompt_text': 'Test prompt',
                'context_id': 'nonexistent_ctx',
            })

            assert result['captured'] is False
            assert 'no_session' in result.get('reason', '')
        except ImportError:
            pytest.skip("Hook not implemented yet")

    def test_hook_handles_empty_prompt(self):
        """Hook should handle empty prompts gracefully."""
        try:
            from claude.hooks.prompt_capture import capture_prompt

            result = capture_prompt({
                'prompt_text': '',
                'context_id': 'ctx',
            })

            assert result['captured'] is False
        except ImportError:
            pytest.skip("Hook not implemented yet")


# =============================================================================
# Phase 4: Export Tests (placeholder - will extend)
# =============================================================================

class TestPromptExport:
    """Tests for prompt_export.py functionality."""

    def test_export_jsonl(self):
        """Should export prompts as valid JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singleton to use patched home
                import claude.tools.learning.memory as memory_module
                memory_module._memory = None

                from claude.tools.learning.memory import MaiaMemory
                from claude.tools.learning.prompt_export import export_session_prompts

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "First prompt")
                memory.capture_prompt("s1", "ctx", "Second prompt")

                output = export_session_prompts("s1", format='jsonl')
                lines = output.strip().split('\n')

                assert len(lines) == 2
                for line in lines:
                    data = json.loads(line)
                    assert 'prompt_text' in data

    def test_export_markdown(self):
        """Should export prompts as readable Markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singleton to use patched home
                import claude.tools.learning.memory as memory_module
                memory_module._memory = None

                from claude.tools.learning.memory import MaiaMemory
                from claude.tools.learning.prompt_export import export_session_prompts

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Test prompt")

                output = export_session_prompts("s1", format='markdown')

                assert "# Session Prompts" in output
                assert "Test prompt" in output

    def test_export_csv(self):
        """Should export prompts as CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                # Reset singleton to use patched home
                import claude.tools.learning.memory as memory_module
                memory_module._memory = None

                from claude.tools.learning.memory import MaiaMemory
                from claude.tools.learning.prompt_export import export_session_prompts

                memory = MaiaMemory()
                memory.capture_prompt("s1", "ctx", "Test prompt")

                output = export_session_prompts("s1", format='csv')

                assert 'prompt_text' in output
                assert 'Test prompt' in output


# =============================================================================
# Backward Compatibility Tests
# =============================================================================

class TestBackwardCompatibility:
    """Tests for backward compatibility with existing sessions."""

    def test_existing_sessions_work_without_prompts(self):
        """Sessions without prompts should work normally."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Start session without capturing prompts
                memory.start_session(
                    session_id="old_session",
                    context_id="ctx",
                    initial_query="Old style session"
                )

                # Should not error when getting prompts
                prompts = memory.get_prompts_for_session("old_session")
                assert prompts == []

    def test_prompts_table_created_on_demand(self):
        """Prompts table should be created when first accessed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.memory import MaiaMemory

                memory = MaiaMemory()

                # Don't call _ensure_prompts_initialized explicitly
                # Just try to get prompts - should work
                prompts = memory.get_prompts_for_session("any_session")
                assert prompts == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
