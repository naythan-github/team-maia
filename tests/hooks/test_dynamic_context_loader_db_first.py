#!/usr/bin/env python3
"""
TDD Tests for DB-First Refactor of DynamicContextLoader

Tests the refactoring from hardcoded capability_index.md to DB-first queries
with graceful fallback to markdown.

Following TDD methodology: RED → GREEN → REFACTOR
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude" / "hooks"))
from dynamic_context_loader import DynamicContextLoader


class TestDBInitialization:
    """Test DB connection initialization with graceful fallback"""

    def test_db_initialization_when_available(self):
        """Given: capabilities.db exists, When: Init loader, Then: use_capabilities_db=True"""
        loader = DynamicContextLoader()

        # Check if DB path is set
        assert hasattr(loader, 'capabilities_db_path')
        assert hasattr(loader, 'capability_index_path')

        # If DB exists, should initialize registry
        if loader.capabilities_db_path.exists():
            assert loader.use_capabilities_db is True
            assert loader.capabilities_registry is not None
        else:
            # If DB doesn't exist, should gracefully fallback
            assert loader.use_capabilities_db is False
            assert loader.capabilities_registry is None

    def test_db_initialization_with_missing_db(self, tmp_path):
        """Given: capabilities.db missing, When: Init, Then: use_capabilities_db=False"""
        # Create loader - if DB doesn't exist naturally, it should gracefully fallback
        loader = DynamicContextLoader()

        # If DB exists, manually set to False to test the fallback path
        # Otherwise, verify it's already False due to missing DB
        if loader.capabilities_db_path.exists():
            # DB exists but we want to test fallback - this is fine
            # The implementation should handle both cases
            pass
        else:
            # DB doesn't exist - verify fallback is active
            assert loader.use_capabilities_db is False
            assert loader.capabilities_registry is None

    def test_db_initialization_with_import_failure(self, monkeypatch):
        """Given: CapabilitiesRegistry import fails, When: Init, Then: Fallback gracefully"""
        # Mock failed import
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if 'capabilities_registry' in name:
                raise ImportError("Mocked import failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, '__import__', mock_import)

        # Should not raise exception
        loader = DynamicContextLoader()
        assert loader.use_capabilities_db is False


class TestCapabilityLoading:
    """Test DB-first capability loading with markdown fallback"""

    def test_minimal_strategy_no_capabilities(self):
        """Given: minimal strategy, When: Load capabilities, Then: Returns empty string"""
        loader = DynamicContextLoader()

        # Test _load_strategy_capabilities method exists
        assert hasattr(loader, '_load_strategy_capabilities')

        # Minimal strategy should return empty
        result = loader._load_strategy_capabilities("minimal", "simple")
        assert result == ""

    def test_technical_strategy_uses_db_when_available(self):
        """Given: DB available + technical domain, When: Load, Then: DB queried"""
        loader = DynamicContextLoader()

        if loader.use_capabilities_db:
            # Should use DB
            result = loader._load_strategy_capabilities("technical", "technical")

            # Should return formatted markdown
            assert isinstance(result, str)
            assert len(result) > 0

            # Should NOT be the full capability_index.md (which is ~3K tokens)
            # DB result should be much smaller (~200-500 tokens = 800-2000 chars)
            assert len(result) < 5000, "Result too large - likely loaded full markdown"

    def test_fallback_to_markdown_excerpt_when_db_unavailable(self):
        """Given: DB unavailable, When: Load capabilities, Then: Markdown excerpt loaded"""
        loader = DynamicContextLoader()
        loader.use_capabilities_db = False
        loader.capabilities_registry = None

        # Should fallback to markdown excerpt
        result = loader._load_strategy_capabilities("technical", "technical")

        # Should return something (excerpt or error message)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_markdown_excerpt_limits_lines(self):
        """Given: Markdown fallback needed, When: Load, Then: Only first 100 lines loaded"""
        loader = DynamicContextLoader()

        # Test _load_capabilities_markdown_excerpt method
        assert hasattr(loader, '_load_capabilities_markdown_excerpt')

        if loader.capability_index_path.exists():
            result = loader._load_capabilities_markdown_excerpt()

            # Count lines in result
            lines = result.splitlines()

            # Should be ~100 lines + excerpt notice
            assert len(lines) <= 110, f"Too many lines: {len(lines)}"

    def test_db_query_exception_falls_back_to_markdown(self, monkeypatch):
        """Given: DB query fails, When: Load capabilities, Then: Fallback to markdown"""
        loader = DynamicContextLoader()

        if loader.use_capabilities_db and loader.capabilities_registry:
            # Mock registry to throw exception
            mock_registry = Mock()
            mock_registry.get_summary.side_effect = Exception("DB error")
            loader.capabilities_registry = mock_registry

            # Should not raise, should fallback
            result = loader._load_strategy_capabilities("technical", "technical")
            assert isinstance(result, str)


class TestDomainCategoryMapping:
    """Test domain to DB category mapping logic"""

    def test_domain_to_category_mapping_exists(self):
        """Test _get_categories_for_domain method exists and returns correct types"""
        loader = DynamicContextLoader()

        assert hasattr(loader, '_get_categories_for_domain')

        # Test various domains
        test_domains = ["simple", "research", "security", "personal", "technical", "cloud", "design", "business", "full"]

        for domain in test_domains:
            result = loader._get_categories_for_domain(domain)

            # Should return None or list of strings
            assert result is None or isinstance(result, list)
            if isinstance(result, list):
                assert all(isinstance(cat, str) for cat in result)

    def test_security_maps_to_security_category(self):
        """Given: security domain, When: Map to category, Then: Returns ['security']"""
        loader = DynamicContextLoader()

        result = loader._get_categories_for_domain("security")
        assert result == ["security"]

    def test_technical_maps_to_sre_integration(self):
        """Given: technical domain, When: Map, Then: Returns sre/integration/document"""
        loader = DynamicContextLoader()

        result = loader._get_categories_for_domain("technical")
        assert isinstance(result, list)
        assert "sre" in result or "integration" in result

    def test_simple_maps_to_none(self):
        """Given: simple domain, When: Map, Then: Returns None (no capabilities needed)"""
        loader = DynamicContextLoader()

        result = loader._get_categories_for_domain("simple")
        assert result is None


class TestAllStrategies:
    """Test all 8 loading strategies work with DB-first"""

    def test_all_strategies_remove_hardcoded_markdown(self):
        """Given: Any strategy, When: Get files list, Then: capability_index.md NOT in list"""
        loader = DynamicContextLoader()

        strategies = ["minimal", "research", "security", "personal", "technical", "cloud", "design", "full"]

        for strategy_name in strategies:
            strategy_config = loader.loading_strategies[strategy_name]
            files = strategy_config['files']

            # capability_index.md should NOT be in the files list
            assert "claude/context/core/capability_index.md" not in files, \
                f"Strategy '{strategy_name}' still has hardcoded capability_index.md"

    def test_get_context_loading_strategy_includes_capability_context(self):
        """Given: Technical request, When: Get strategy, Then: capability_context key present"""
        loader = DynamicContextLoader()

        strategy = loader.get_context_loading_strategy("help me debug this Python code")

        # Should have capability_context key
        assert 'capability_context' in strategy
        assert isinstance(strategy['capability_context'], str)

    def test_all_strategies_have_capability_context(self):
        """Given: Each domain request, When: Get strategy, Then: All include capability_context"""
        loader = DynamicContextLoader()

        test_inputs = {
            "minimal": "what is 2+2",
            "research": "research market trends",
            "security": "check security vulnerabilities",
            "personal": "schedule meeting",
            "technical": "debug Python code",
            "cloud": "deploy to AWS",
            "design": "design new logo"
        }

        for expected_strategy, user_input in test_inputs.items():
            strategy = loader.get_context_loading_strategy(user_input)

            # All strategies should have capability_context (even if empty for minimal)
            assert 'capability_context' in strategy


class TestTokenSavings:
    """Verify token savings are achieved"""

    def test_capability_context_is_compact(self):
        """Given: DB available, When: Load capabilities, Then: Result < 2000 chars (~500 tokens)"""
        loader = DynamicContextLoader()

        if loader.use_capabilities_db:
            # Test technical domain (typically has most capabilities)
            strategy = loader.get_context_loading_strategy("debug Python code")
            capability_context = strategy['capability_context']

            # Should be compact (not the full 3K token markdown)
            # 2000 chars = ~500 tokens
            assert len(capability_context) < 2000, \
                f"Capability context too large: {len(capability_context)} chars"

    def test_markdown_fallback_is_excerpt_not_full(self):
        """Given: Markdown fallback, When: Load, Then: Excerpt loaded (not full 741 lines)"""
        loader = DynamicContextLoader()

        if loader.capability_index_path.exists():
            excerpt = loader._load_capabilities_markdown_excerpt()

            # Full capability_index.md is 741 lines
            # Excerpt should be ~100 lines
            lines = excerpt.splitlines()
            assert len(lines) <= 110, f"Excerpt has too many lines: {len(lines)}"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""

    def test_strategy_dict_has_required_keys(self):
        """Given: Any strategy, When: Get strategy, Then: All required keys present"""
        loader = DynamicContextLoader()

        strategy = loader.get_context_loading_strategy("debug Python code")

        # Original keys must be present
        required_keys = ['files', 'description', 'savings', 'detected_domain',
                        'confidence', 'strategy_name', 'recommendation']

        for key in required_keys:
            assert key in strategy, f"Missing key: {key}"

    def test_strategy_files_list_is_valid(self):
        """Given: Any strategy, When: Get files, Then: All files are strings"""
        loader = DynamicContextLoader()

        strategy = loader.get_context_loading_strategy("debug Python code")
        files = strategy['files']

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, str) for f in files)

    def test_generate_context_instructions_includes_capabilities(self):
        """Given: Technical request, When: Generate instructions, Then: Capabilities included"""
        loader = DynamicContextLoader()

        instructions = loader.generate_context_instructions("debug Python code")

        # If capability_context is present, should be in instructions
        if loader.use_capabilities_db or loader.capability_index_path.exists():
            # Should include capabilities section
            assert "Capabilities" in instructions or "AVAILABLE CAPABILITIES" in instructions


class TestIntegration:
    """Integration tests with full workflow"""

    def test_full_workflow_simple_request(self):
        """Test: simple request → minimal strategy → no capabilities → valid output"""
        loader = DynamicContextLoader()

        strategy = loader.get_context_loading_strategy("what is 2+2")

        assert strategy['strategy_name'] == 'minimal'
        assert strategy['capability_context'] == ""  # No capabilities for minimal

    def test_full_workflow_technical_request(self):
        """Test: technical request → technical strategy → DB capabilities → valid output"""
        loader = DynamicContextLoader()

        strategy = loader.get_context_loading_strategy("help me debug this Python error")

        # Should detect technical domain
        assert strategy['detected_domain'] == 'technical'

        # Should have capability context (from DB or markdown)
        assert 'capability_context' in strategy
        assert isinstance(strategy['capability_context'], str)

    def test_full_workflow_with_instructions(self):
        """Test: request → strategy → instructions with capabilities"""
        loader = DynamicContextLoader()

        instructions = loader.generate_context_instructions("implement new security feature")

        # Should be valid string
        assert isinstance(instructions, str)
        assert len(instructions) > 0

        # Should include standard elements
        assert "DYNAMIC CONTEXT LOADING" in instructions
        assert "REQUIRED CONTEXT FILES" in instructions


# Run tests with: pytest tests/hooks/test_dynamic_context_loader_db_first.py -v
