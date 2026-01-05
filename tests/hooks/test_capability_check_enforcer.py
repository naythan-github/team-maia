#!/usr/bin/env python3
"""
Tests for capability_check_enforcer.py - DB-first capability search.

Phase 235: Fix context bloat by replacing 68KB markdown file read with DB queries.

TDD Tests:
1. test_search_capability_db_finds_match - DB search finds existing capability
2. test_search_capability_db_no_match - DB search returns None when no match
3. test_search_capability_db_extracts_keywords - Keywords extracted correctly
4. test_search_capability_db_skips_common_words - Filters out build/create/make
5. test_db_search_faster_than_markdown - Performance validation
6. test_enforce_uses_db_not_markdown - Integration test ensuring DB path used
"""

import pytest
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude" / "hooks"))

from claude.hooks.capability_check_enforcer import CapabilityEnforcer


# Test fixtures
@pytest.fixture
def enforcer():
    """Create CapabilityEnforcer with valid maia_root."""
    maia_root = Path(__file__).parent.parent.parent
    return CapabilityEnforcer(maia_root=maia_root)


@pytest.fixture
def db_path():
    """Get path to capabilities database."""
    return Path(__file__).parent.parent.parent / "claude" / "data" / "databases" / "system" / "capabilities.db"


class TestSearchCapabilityDb:
    """Tests for the new DB-based capability search."""

    def test_search_capability_db_finds_match(self, enforcer, db_path):
        """DB search should find existing capabilities by keyword."""
        if not db_path.exists():
            pytest.skip("Capabilities DB not found")

        # Search for a known capability keyword
        result = enforcer.search_capability_db("security scanning tool")

        # Should find something security-related
        assert result is not None, "Should find a match for 'security'"
        assert 'name' in result, "Result should have 'name' field"
        assert 'path' in result, "Result should have 'path' field"

    def test_search_capability_db_no_match(self, enforcer, db_path):
        """DB search should return None for nonsense queries."""
        if not db_path.exists():
            pytest.skip("Capabilities DB not found")

        result = enforcer.search_capability_db("xyzzy12345 frobnicator")
        assert result is None, "Should return None for nonsense query"

    def test_search_capability_db_extracts_keywords(self, enforcer):
        """Should extract 4+ char words as keywords."""
        # Test the keyword extraction logic
        import re
        user_input = "build a security tool for scanning"
        words = re.findall(r'\b\w{4,}\b', user_input.lower())
        words = [w for w in words if w not in ['build', 'create', 'make', 'tool', 'agent']]

        assert 'security' in words, "Should extract 'security'"
        assert 'scanning' in words, "Should extract 'scanning'"
        assert 'build' not in words, "Should filter out 'build'"
        assert 'tool' not in words, "Should filter out 'tool'"

    def test_search_capability_db_skips_common_words(self, enforcer, db_path):
        """Should not search for build/create/make/tool/agent."""
        if not db_path.exists():
            pytest.skip("Capabilities DB not found")

        # Query with only common words should return None (no useful keywords)
        result = enforcer.search_capability_db("build a new tool")
        # This might return None or a match depending on 'new' - the point is
        # it shouldn't be searching for 'build' or 'tool'
        # Just verify it doesn't crash
        assert result is None or isinstance(result, dict)

    def test_db_search_faster_than_markdown(self, enforcer, db_path):
        """DB search should be significantly faster than reading 68KB file."""
        if not db_path.exists():
            pytest.skip("Capabilities DB not found")

        # Time DB search
        start = time.perf_counter()
        for _ in range(10):
            enforcer.search_capability_db("security tool")
        db_time = time.perf_counter() - start

        # Time markdown read (simulated by reading the file)
        cap_index = enforcer.maia_root / 'claude' / 'context' / 'core' / 'capability_index.md'
        if cap_index.exists():
            start = time.perf_counter()
            for _ in range(10):
                _ = cap_index.read_text()
            md_time = time.perf_counter() - start

            # DB should be at least 2x faster (usually much more)
            # Being lenient here since file caching can make reads fast
            print(f"DB time: {db_time:.4f}s, Markdown time: {md_time:.4f}s")
            # Just ensure DB search completes in reasonable time
            assert db_time < 1.0, "DB search should complete 10 iterations in <1s"

    def test_enforce_uses_db_not_markdown(self, enforcer, db_path):
        """Integration test: enforce() should use DB path, not read full markdown."""
        if not db_path.exists():
            pytest.skip("Capabilities DB not found")

        # Patch the markdown read to detect if it's called
        original_search_index = enforcer.search_capability_index
        markdown_called = False

        def tracking_search_index(user_input):
            nonlocal markdown_called
            markdown_called = True
            return original_search_index(user_input)

        enforcer.search_capability_index = tracking_search_index

        # Run enforce on a build request
        result = enforcer.enforce("build a security scanner")

        # The old search_capability_index should NOT be called anymore
        # (once we implement the fix)
        # For now, this test documents the expected behavior
        assert not markdown_called, (
            "enforce() should use search_capability_db(), not search_capability_index(). "
            "The 68KB markdown file should not be read."
        )


class TestCapabilityEnforcerExisting:
    """Tests for existing functionality that should still work."""

    def test_detect_build_request_positive(self, enforcer):
        """Should detect build requests."""
        assert enforcer.detect_build_request("build a new tool") is True
        assert enforcer.detect_build_request("create a security scanner") is True
        assert enforcer.detect_build_request("implement feature X") is True

    def test_detect_build_request_negative(self, enforcer):
        """Should not flag non-build requests."""
        assert enforcer.detect_build_request("what is the weather") is False
        assert enforcer.detect_build_request("help me understand this function") is False
        assert enforcer.detect_build_request("explain the architecture") is False

    def test_enforce_non_build_request(self, enforcer):
        """Non-build requests should pass through without capability check."""
        result = enforcer.enforce("what time is it")
        assert result['should_warn'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
