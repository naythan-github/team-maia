"""
Tests for feature_tracker.py main() helper functions.

TDD: Phase 4 refactoring - decompose main (133 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    def test_create_argument_parser_exists(self):
        """Helper for creating argument parser."""
        from feature_tracker import _create_argument_parser
        assert callable(_create_argument_parser)

    def test_handle_command_exists(self):
        """Helper for dispatching commands."""
        from feature_tracker import _handle_command
        assert callable(_handle_command)


class TestCreateArgumentParser:
    """Test _create_argument_parser helper."""

    def test_returns_parser(self):
        """Should return ArgumentParser instance."""
        import argparse
        from feature_tracker import _create_argument_parser
        parser = _create_argument_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_has_subcommands(self):
        """Should have required subcommands."""
        from feature_tracker import _create_argument_parser
        parser = _create_argument_parser()
        # Parse with init command
        args = parser.parse_args(['init', 'test_project'])
        assert args.command == 'init'
        assert args.project == 'test_project'


class TestHandleCommand:
    """Test _handle_command helper."""

    def test_handles_init(self):
        """Should handle init command."""
        from feature_tracker import _handle_command
        mock_tracker = MagicMock()
        mock_tracker.init.return_value = {'success': True, 'file': '/tmp/test.json'}

        args = MagicMock()
        args.command = 'init'
        args.project = 'test'
        args.force = False

        # Should not raise
        _handle_command(mock_tracker, args)
        mock_tracker.init.assert_called_once()

    def test_handles_summary(self):
        """Should handle summary command."""
        from feature_tracker import _handle_command
        mock_tracker = MagicMock()
        mock_tracker.summary.return_value = {
            'total': 10,
            'passing': 5,
            'failing': 3,
            'blocked': 2,
            'completion_percentage': 50
        }

        args = MagicMock()
        args.command = 'summary'
        args.project = 'test'

        # Should not raise
        _handle_command(mock_tracker, args)
        mock_tracker.summary.assert_called_once()
