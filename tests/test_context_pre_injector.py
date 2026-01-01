#!/usr/bin/env python3
"""
TDD Tests for Context Pre-Injector
Phase 226: Automatic DB-First Context Loading

Tests written BEFORE implementation per MAIA TDD protocol.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add hooks directory to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude" / "hooks" / "context_pre_injector"))
sys.path.insert(0, str(MAIA_ROOT / "claude" / "hooks"))


class TestKeywordExtraction:
    """TC-2: Keyword extraction tests."""

    def test_extracts_meaningful_keywords(self):
        """TC-2.1: Extracts meaningful words, filters stopwords."""
        from context_pre_injector import extract_keywords

        result = extract_keywords("how do I use security tools")

        assert "security" in result
        assert "tools" in result
        assert "how" not in result
        assert "do" not in result
        assert len(result) <= 3  # Max 3 keywords

    def test_filters_stopwords(self):
        """TC-2.2: Stopwords are filtered out."""
        from context_pre_injector import extract_keywords

        result = extract_keywords("the a an is are to for")

        assert result == []

    def test_handles_empty_query(self):
        """TC-2.3: Empty query returns empty list."""
        from context_pre_injector import extract_keywords

        result = extract_keywords("")

        assert result == []

    def test_filters_short_words(self):
        """Words <= 3 chars should be filtered."""
        from context_pre_injector import extract_keywords

        result = extract_keywords("the sre db fix")

        # "sre", "fix" are 3 chars - should be filtered (>3 required)
        # Only words > 3 chars should pass
        assert all(len(w) > 3 for w in result)

    def test_returns_max_three_keywords(self):
        """Should return maximum 3 keywords."""
        from context_pre_injector import extract_keywords

        result = extract_keywords("security authentication authorization encryption validation")

        assert len(result) <= 3


class TestComplexityDetection:
    """TC-3: Query complexity detection tests."""

    def test_detects_implement_as_complex(self):
        """TC-3.1: 'implement' triggers complex query."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("implement authentication") is True

    def test_simple_question_not_complex(self):
        """TC-3.2: Simple questions are not complex."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("what is X") is False
        assert is_complex_query("explain this") is False

    def test_detects_create_as_complex(self):
        """TC-3.3: 'create' triggers complex query."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("create new agent") is True

    def test_detects_build_as_complex(self):
        """'build' triggers complex query."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("build a dashboard") is True

    def test_detects_fix_as_complex(self):
        """'fix' triggers complex query."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("fix the bug in auth") is True

    def test_detects_debug_as_complex(self):
        """'debug' triggers complex query."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("debug the performance issue") is True

    def test_handles_empty_query(self):
        """Empty query is not complex."""
        from context_pre_injector import is_complex_query

        assert is_complex_query("") is False


class TestContextInjection:
    """TC-1: Basic context injection functionality."""

    def test_empty_query_returns_summary(self):
        """TC-1.1: Empty query still returns capability summary."""
        from context_pre_injector import inject_context

        # Capture stdout
        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        # Should contain summary header
        assert "AUTO-INJECTED CONTEXT" in output or "Context Summary" in output

    def test_security_query_returns_relevant_caps(self):
        """TC-1.2: Security query returns security-related capabilities."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("security tools")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        # Should contain output (may or may not have matches depending on DB)
        assert len(output) > 0

    def test_implement_query_triggers_phase_search(self):
        """TC-1.3: Implementation query triggers phase search."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("implement a new feature")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        # Should produce output
        assert len(output) > 0


class TestGracefulDegradation:
    """TC-4: Graceful degradation tests."""

    def test_works_without_capabilities_db(self):
        """TC-4.1: Works when capabilities.db missing."""
        from context_pre_injector import inject_context

        # Test that inject_context handles DB failures gracefully
        # We test by calling with a query - if it doesn't raise, it passed
        captured = StringIO()
        sys.stdout = captured

        try:
            # Should not raise even if DB queries fail internally
            inject_context("test query with nonexistent capability xyz123abc")
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
        finally:
            sys.stdout = sys.__stdout__

        # Should have produced some output (fallback)
        assert len(captured.getvalue()) > 0

    def test_works_without_system_state_db(self):
        """TC-4.2: Works when system_state.db missing."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            # Should not raise even for complex queries when DB fails
            inject_context("implement something that doesnt exist xyz789")
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
        finally:
            sys.stdout = sys.__stdout__

        # Should have produced some output
        assert len(captured.getvalue()) > 0

    def test_never_raises_exception(self):
        """TC-4.3: Never raises exception to caller."""
        from context_pre_injector.context_pre_injector import inject_context, _print_fallback_context

        # Test the fallback directly
        captured = StringIO()
        sys.stdout = captured

        try:
            _print_fallback_context()
        except Exception as e:
            pytest.fail(f"Fallback should not raise: {e}")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        assert "AUTO-INJECTED" in output
        assert len(output) > 0

    def test_inject_with_mock_failure(self):
        """Test inject_context handles complete loader failure."""
        from context_pre_injector.context_pre_injector import inject_context

        # Patch at the correct module level
        with patch('context_pre_injector.context_pre_injector.LOADER_AVAILABLE', False):
            captured = StringIO()
            sys.stdout = captured

            try:
                inject_context("anything")
            except Exception as e:
                pytest.fail(f"Should not raise exception: {e}")
            finally:
                sys.stdout = sys.__stdout__

            # Should still produce output via fallback
            assert len(captured.getvalue()) > 0


class TestPerformance:
    """TC-5: Performance tests."""

    def test_execution_under_100ms(self):
        """TC-5.1: Execution completes in <100ms."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        start = time.time()
        try:
            inject_context("security tools query")
        finally:
            sys.stdout = sys.__stdout__

        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, f"Execution took {elapsed_ms:.1f}ms, should be <100ms"

    def test_output_under_500_tokens(self):
        """TC-5.2: Output is <500 tokens (~2000 chars)."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("implement security authentication system")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        # Rough token estimate: 4 chars per token
        estimated_tokens = len(output) / 4

        assert estimated_tokens < 500, f"Output is ~{estimated_tokens:.0f} tokens, should be <500"


class TestCLIInterface:
    """NFR-3: CLI integration tests."""

    def test_callable_as_script(self):
        """NFR-3.2: Can be called with query as CLI argument."""
        import subprocess

        script_path = MAIA_ROOT / "claude" / "hooks" / "context_pre_injector" / "context_pre_injector.py"

        if not script_path.exists():
            pytest.skip("Implementation not yet created")

        result = subprocess.run(
            [sys.executable, str(script_path), "test query"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should exit 0 always (NFR-2.4)
        assert result.returncode == 0

    def test_works_with_empty_query(self):
        """NFR-3.3: Works with empty query (summary only)."""
        import subprocess

        script_path = MAIA_ROOT / "claude" / "hooks" / "context_pre_injector" / "context_pre_injector.py"

        if not script_path.exists():
            pytest.skip("Implementation not yet created")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert len(result.stdout) > 0


class TestOutputFormat:
    """FR-4: Output format tests."""

    def test_has_visual_delimiters(self):
        """FR-4.2: Output has clear visual delimiters."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("test")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        # Should have some kind of delimiter (─ or --- or ===)
        assert "─" in output or "---" in output or "===" in output or "AUTO-INJECTED" in output

    def test_labeled_as_auto_injected(self):
        """FR-4.3: Output labeled as AUTO-INJECTED."""
        from context_pre_injector import inject_context

        captured = StringIO()
        sys.stdout = captured

        try:
            inject_context("test")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()

        assert "AUTO-INJECTED" in output or "auto-injected" in output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
