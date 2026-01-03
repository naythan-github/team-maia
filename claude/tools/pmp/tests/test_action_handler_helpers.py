"""
Tests for pmp_action_handler.py main() helper functions.

TDD: Phase 4 refactoring - decompose main (140 lines)
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
        from pmp_action_handler import _create_argument_parser
        assert callable(_create_argument_parser)

    def test_parse_ids_exists(self):
        """Helper for parsing comma-separated IDs."""
        from pmp_action_handler import _parse_ids
        assert callable(_parse_ids)

    def test_handle_action_exists(self):
        """Helper for dispatching actions."""
        from pmp_action_handler import _handle_action
        assert callable(_handle_action)


class TestCreateArgumentParser:
    """Test _create_argument_parser helper."""

    def test_returns_parser(self):
        """Should return ArgumentParser instance."""
        import argparse
        from pmp_action_handler import _create_argument_parser
        parser = _create_argument_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_has_action_argument(self):
        """Should have action positional argument."""
        from pmp_action_handler import _create_argument_parser
        parser = _create_argument_parser()
        args = parser.parse_args(['approve', '--patch-ids', '123'])
        assert args.action == 'approve'


class TestParseIds:
    """Test _parse_ids helper."""

    def test_parses_comma_separated(self):
        """Should parse comma-separated IDs."""
        from pmp_action_handler import _parse_ids
        result = _parse_ids('1,2,3')
        assert result == [1, 2, 3]

    def test_handles_none(self):
        """Should return empty list for None."""
        from pmp_action_handler import _parse_ids
        result = _parse_ids(None)
        assert result == []

    def test_handles_empty_string(self):
        """Should return empty list for empty string."""
        from pmp_action_handler import _parse_ids
        result = _parse_ids('')
        assert result == []


class TestHandleAction:
    """Test _handle_action helper."""

    @patch('pmp_action_handler.PMPActionHandler')
    def test_returns_result_or_exit_code(self, mock_handler):
        """Should return result dict or exit code."""
        mock_instance = MagicMock()
        mock_instance.get_db_update_status.return_value = {'status': 'ok'}
        mock_handler.return_value = mock_instance

        from pmp_action_handler import _handle_action
        args = MagicMock()
        args.action = 'db-status'
        args.patch_ids = None
        args.resource_ids = None

        result = _handle_action(mock_instance, args, [], [])
        assert result is not None
