"""
Tests for servicedesk_multi_rag_indexer.py helper functions.

TDD: Phase 4 refactoring - decompose index_collection (140 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_build_index_query_exists(self, mock_chroma):
        """Helper for building SQL query."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.collections = {}
        assert hasattr(indexer, '_build_index_query')
        assert callable(indexer._build_index_query)

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_process_row_to_document_exists(self, mock_chroma):
        """Helper for processing database row to document."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.collections = {}
        assert hasattr(indexer, '_process_row_to_document')
        assert callable(indexer._process_row_to_document)

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_print_index_completion_exists(self, mock_chroma):
        """Helper for printing completion summary."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.collections = {}
        assert hasattr(indexer, '_print_index_completion')
        assert callable(indexer._print_index_completion)


class TestBuildIndexQuery:
    """Test _build_index_query helper."""

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_returns_sql_string(self, mock_chroma):
        """Should return valid SQL query string."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.collections = {
            'test': {
                'table': 'tickets',
                'id_field': 'id',
                'text_field': 'description',
                'metadata_fields': ['title', 'status']
            }
        }

        query = indexer._build_index_query('test', None)
        assert isinstance(query, str)
        assert 'SELECT' in query
        assert 'FROM tickets' in query


class TestProcessRowToDocument:
    """Test _process_row_to_document helper."""

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_returns_tuple_or_none(self, mock_chroma):
        """Should return (id, text, metadata) tuple or None."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.collections = {
            'test': {
                'metadata_fields': ['title']
            }
        }

        # Create mock row
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda k: {
            'id': '123',
            'text': 'Sample text content',
            'title': 'Test Title'
        }.get(k))

        result = indexer._process_row_to_document(mock_row, 'test', set())
        # Should return tuple (id, text, metadata) or None
        assert result is None or isinstance(result, tuple)


class TestPrintIndexCompletion:
    """Test _print_index_completion helper."""

    @patch('servicedesk_multi_rag_indexer.chromadb')
    def test_prints_summary(self, mock_chroma, capsys):
        """Should print completion summary."""
        mock_chroma.PersistentClient.return_value = MagicMock()
        from servicedesk_multi_rag_indexer import ServiceDeskMultiRAGIndexer
        indexer = ServiceDeskMultiRAGIndexer.__new__(ServiceDeskMultiRAGIndexer)
        indexer.rag_db_path = '/tmp/test'
        indexer.collections = {}

        indexer._print_index_completion('test', 100, 10.0)

        captured = capsys.readouterr()
        assert '100' in captured.out or 'complete' in captured.out.lower()
