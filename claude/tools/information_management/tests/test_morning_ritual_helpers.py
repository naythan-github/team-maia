"""
Tests for executive_information_manager.py morning ritual helper functions.

TDD: Phase 4 refactoring - decompose generate_morning_ritual (148 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import sqlite3
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    def test_build_tier1_section_exists(self):
        """Helper for building Tier 1 critical items section."""
        from executive_information_manager import ExecutiveInformationManager
        # Use temp db to avoid real db
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            assert hasattr(manager, '_build_tier1_section')
            assert callable(manager._build_tier1_section)

    def test_build_tier2_section_exists(self):
        """Helper for building Tier 2 high priority section."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            assert hasattr(manager, '_build_tier2_section')
            assert callable(manager._build_tier2_section)

    def test_build_meetings_section_exists(self):
        """Helper for building today's meetings section."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            assert hasattr(manager, '_build_meetings_section')
            assert callable(manager._build_meetings_section)

    def test_build_system_status_section_exists(self):
        """Helper for building system status section."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            assert hasattr(manager, '_build_system_status_section')
            assert callable(manager._build_system_status_section)


class TestBuildTier1Section:
    """Test _build_tier1_section helper."""

    def test_returns_list_of_strings(self):
        """Should return list of markdown strings."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            conn = sqlite3.connect(f.name)
            cursor = conn.cursor()

            # No items - should still return section header
            lines, items = manager._build_tier1_section(cursor)
            assert isinstance(lines, list)
            assert all(isinstance(line, str) for line in lines)
            assert any('Tier 1' in line for line in lines)
            conn.close()


class TestBuildTier2Section:
    """Test _build_tier2_section helper."""

    def test_returns_list_of_strings(self):
        """Should return list of markdown strings."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            conn = sqlite3.connect(f.name)
            cursor = conn.cursor()

            lines, items = manager._build_tier2_section(cursor)
            assert isinstance(lines, list)
            assert any('Tier 2' in line for line in lines)
            conn.close()


class TestBuildMeetingsSection:
    """Test _build_meetings_section helper."""

    @patch('executive_information_manager.import_module_from_path')
    def test_handles_no_calendar(self, mock_import):
        """Should gracefully handle missing calendar."""
        mock_import.side_effect = Exception("No calendar")

        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            lines = manager._build_meetings_section()
            assert isinstance(lines, list)
            assert any('Meetings' in line for line in lines)


class TestBuildSystemStatusSection:
    """Test _build_system_status_section helper."""

    def test_shows_counts(self):
        """Should show inbox and active item counts."""
        from executive_information_manager import ExecutiveInformationManager
        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            manager = ExecutiveInformationManager(db_path=Path(f.name))
            conn = sqlite3.connect(f.name)
            cursor = conn.cursor()

            lines = manager._build_system_status_section(cursor, 0, 0)
            assert isinstance(lines, list)
            assert any('System Status' in line for line in lines)
            conn.close()
