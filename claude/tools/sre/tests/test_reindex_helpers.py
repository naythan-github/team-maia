"""
Tests for reindex_comments_with_quality.py helper functions.

TDD: Phase 3 refactoring - decompose reindex_with_checkpoints (189 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    def test_prepare_document_batch_exists(self):
        """Helper for preparing a batch of documents."""
        from reindex_comments_with_quality import ResumableReIndexer
        # Method should exist on class
        assert hasattr(ResumableReIndexer, '_prepare_document_batch')

    def test_index_single_batch_exists(self):
        """Helper for indexing a single batch."""
        from reindex_comments_with_quality import ResumableReIndexer
        assert hasattr(ResumableReIndexer, '_index_single_batch')

    def test_print_completion_stats_exists(self):
        """Helper for printing completion statistics."""
        from reindex_comments_with_quality import ResumableReIndexer
        assert hasattr(ResumableReIndexer, '_print_completion_stats')


class TestPrepareDocumentBatch:
    """Test _prepare_document_batch helper."""

    def test_returns_ids_texts_metadatas(self):
        """Should return tuple of (ids, texts, metadatas)."""
        from reindex_comments_with_quality import ResumableReIndexer

        # Create mock indexer
        mock_indexer = MagicMock()
        reindexer = ResumableReIndexer(mock_indexer)

        # Test with sample documents
        docs = [
            {'id': '1', 'text': 'test text', 'ticket_id': 'T001'},
            {'id': '2', 'text': 'another text', 'ticket_id': 'T002'}
        ]

        ids, texts, metadatas = reindexer._prepare_document_batch(docs)

        assert ids == ['1', '2']
        assert texts == ['test text', 'another text']
        assert len(metadatas) == 2

    def test_truncates_long_texts(self):
        """Should truncate texts longer than 5000 chars."""
        from reindex_comments_with_quality import ResumableReIndexer

        mock_indexer = MagicMock()
        reindexer = ResumableReIndexer(mock_indexer)

        long_text = 'x' * 6000
        docs = [{'id': '1', 'text': long_text}]

        ids, texts, metadatas = reindexer._prepare_document_batch(docs)

        assert len(texts[0]) < 6000
        assert '[truncated]' in texts[0]


class TestIndexSingleBatch:
    """Test _index_single_batch helper."""

    def test_adds_to_collection(self):
        """Should call collection.add with embeddings."""
        from reindex_comments_with_quality import ResumableReIndexer

        mock_indexer = MagicMock()
        mock_collection = MagicMock()

        # Mock model.encode to return embeddings
        mock_indexer.model.encode.return_value = MagicMock(tolist=lambda: [[0.1, 0.2], [0.3, 0.4]])
        mock_indexer.batch_size = 32

        reindexer = ResumableReIndexer(mock_indexer)

        ids = ['1', '2']
        texts = ['text1', 'text2']
        metadatas = [{'key': 'val1'}, {'key': 'val2'}]

        reindexer._index_single_batch(mock_collection, ids, texts, metadatas)

        # Verify collection.add was called
        mock_collection.add.assert_called_once()
