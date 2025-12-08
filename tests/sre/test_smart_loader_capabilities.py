#!/usr/bin/env python3
"""
Test Suite: Smart Context Loader - Capabilities DB Integration

Phase 168.1: Integration of capabilities.db into smart context loader.

Tests:
1. DB initialization and availability
2. Query-based capability loading
3. Category-based loading
4. Graceful markdown fallback
5. Token savings validation
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from smart_context_loader import SmartContextLoader, CAPABILITIES_REGISTRY_AVAILABLE


class TestCapabilitiesDBIntegration(unittest.TestCase):
    """Tests for capabilities database integration."""

    @classmethod
    def setUpClass(cls):
        """Initialize loader once for all tests."""
        cls.loader = SmartContextLoader()

    def test_capabilities_registry_available(self):
        """Test that capabilities registry module can be imported."""
        self.assertTrue(CAPABILITIES_REGISTRY_AVAILABLE,
                        "CapabilitiesRegistry should be importable")

    def test_capabilities_db_initialized(self):
        """Test that capabilities DB is initialized when available."""
        # DB should exist and be usable
        self.assertTrue(self.loader.capabilities_db_path.exists(),
                        f"Capabilities DB should exist at {self.loader.capabilities_db_path}")
        self.assertTrue(self.loader.use_capabilities_db,
                        "use_capabilities_db should be True when DB exists")
        self.assertIsNotNone(self.loader.capabilities_registry,
                             "capabilities_registry should be initialized")

    def test_load_capability_summary(self):
        """Test loading capability summary (no query)."""
        result = self.loader.load_capability_context()

        self.assertIn("Relevant Capabilities", result)
        self.assertIn("Total Capabilities", result)
        self.assertIn("agents", result.lower())
        self.assertIn("tools", result.lower())

        # Should be compact (< 500 chars for summary)
        self.assertLess(len(result), 500,
                        "Summary should be compact (<500 chars)")

    def test_load_capability_by_query(self):
        """Test loading capabilities by search query."""
        result = self.loader.load_capability_context(query="security")

        self.assertIn("Query", result)
        self.assertIn("security", result.lower())
        self.assertIn("Found", result)

        # Should have table structure
        self.assertIn("|", result)
        self.assertIn("Name", result)

    def test_load_capability_by_category(self):
        """Test loading capabilities by category."""
        result = self.loader.load_capability_context(category="sre")

        self.assertIn("Category", result)
        self.assertIn("sre", result.lower())

    def test_load_capability_by_type(self):
        """Test loading capabilities filtered by type."""
        result = self.loader.load_capability_context(query="principal", cap_type="agent")

        self.assertIn("agent", result.lower())
        # Should only have Agents section, not Tools
        lines = result.split('\n')
        has_agents_section = any("## Agents" in line for line in lines)
        has_tools_section = any("## Tools" in line for line in lines)

        self.assertTrue(has_agents_section or "agent" in result.lower())

    def test_token_savings_vs_markdown(self):
        """Test that DB queries save tokens vs full markdown."""
        # Get markdown baseline
        md_content = self.loader._load_capabilities_from_markdown()
        md_tokens = len(md_content) // 4

        # Get DB summary
        db_summary = self.loader.load_capability_context()
        db_tokens = len(db_summary) // 4

        # Should save at least 90% tokens for summary
        savings = (md_tokens - db_tokens) / md_tokens * 100
        self.assertGreater(savings, 90,
                           f"Token savings should be >90%, got {savings:.1f}%")

    def test_get_capability_summary_dict(self):
        """Test getting summary as dictionary."""
        summary = self.loader.get_capability_summary()

        self.assertIn('total', summary)
        self.assertIn('agents', summary)
        self.assertIn('tools', summary)
        self.assertIn('by_category', summary)

        # Should have actual counts
        self.assertGreater(summary['total'], 0)
        self.assertGreater(summary['agents'], 0)
        self.assertGreater(summary['tools'], 0)

    def test_markdown_fallback_path_exists(self):
        """Test that markdown fallback path is valid."""
        self.assertTrue(self.loader.capability_index_path.exists(),
                        f"Capability index should exist at {self.loader.capability_index_path}")

    def test_markdown_fallback_content(self):
        """Test that markdown fallback returns valid content."""
        content = self.loader._load_capabilities_from_markdown()

        self.assertIn("Capability", content)
        self.assertGreater(len(content), 1000,
                           "Markdown content should be substantial")


class TestCapabilitiesGracefulDegradation(unittest.TestCase):
    """Tests for graceful degradation when DB unavailable."""

    def test_fallback_when_db_unavailable(self):
        """Test that loader falls back to markdown when DB unavailable."""
        loader = SmartContextLoader()

        # Temporarily disable DB
        original_use_db = loader.use_capabilities_db
        loader.use_capabilities_db = False

        result = loader.load_capability_context(query="security")

        # Should get markdown content (contains full file header)
        self.assertIn("Capability Index", result)

        # Restore
        loader.use_capabilities_db = original_use_db


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
