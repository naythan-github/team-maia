#!/usr/bin/env python3
"""
Phase 4: Queue File Writer - TDD Tests

Tests for QueueWriter that writes learnings to durable queue files
before any database operations.
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime

from claude.tools.learning.continuous_capture.queue_writer import QueueWriter


class TestQueueWriter:
    """Test queue file writing for durable learning capture."""

    def test_writes_to_correct_directory(self, tmp_path):
        """Queue files should be written to ~/.maia/learning_queue/ (or override)."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'decision', 'content': 'test learning', 'timestamp': datetime.now().isoformat(), 'context': {}}
        ]

        writer.write_queue_file(
            context_id='test_ctx',
            learnings=learnings,
            metadata={}
        )

        # Verify queue directory was created
        assert queue_dir.exists(), "Queue directory should be created"
        assert queue_dir.is_dir(), "Queue directory should be a directory"

        # Verify file was written
        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 1, "Should create one queue file"

    def test_file_naming_convention(self, tmp_path):
        """Queue files should follow {timestamp}_{context_id}.json format."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'solution', 'content': 'test', 'timestamp': datetime.now().isoformat(), 'context': {}}
        ]

        before_write = time.time()
        filename = writer.write_queue_file(
            context_id='my_context_123',
            learnings=learnings,
            metadata={}
        )
        after_write = time.time()

        # Parse filename
        assert filename.endswith('.json'), "Should have .json extension"

        # Remove .json extension and split
        filename_base = filename.replace('.json', '')
        parts = filename_base.split('_', 1)
        assert len(parts) == 2, "Should have timestamp_context format"

        timestamp_str, context_part = parts

        # Verify timestamp is reasonable (within test execution window)
        timestamp = int(timestamp_str)
        assert int(before_write) <= timestamp <= int(after_write) + 1, "Timestamp should be within test window"

        # Verify context ID
        assert context_part == 'my_context_123', "Should include context ID"

    def test_atomic_write_no_partial_files(self, tmp_path):
        """Writes should be atomic - no partial files if interrupted."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'test', 'content': 'atomic test', 'timestamp': datetime.now().isoformat(), 'context': {}}
        ]

        filename = writer.write_queue_file(
            context_id='atomic_test',
            learnings=learnings,
            metadata={}
        )

        # Verify no .tmp files left behind
        tmp_files = list(queue_dir.glob('*.tmp'))
        assert len(tmp_files) == 0, "Should not leave .tmp files"

        # Verify file is complete and readable
        queue_file = queue_dir / filename
        assert queue_file.exists()

        with open(queue_file) as f:
            data = json.load(f)
            assert 'learnings' in data
            assert len(data['learnings']) == 1

    def test_self_contained_queue_file(self, tmp_path):
        """Each queue file should contain all necessary information."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {
                'type': 'breakthrough',
                'content': 'discovered continuous capture pattern',
                'timestamp': '2026-01-10T12:00:00Z',
                'context': {'agent': 'sre'}
            }
        ]

        metadata = {
            'agent': 'sre_principal_engineer_agent',
            'compaction_number': 3,
            'message_range': [10, 20]
        }

        filename = writer.write_queue_file(
            context_id='self_contained_test',
            learnings=learnings,
            metadata=metadata
        )

        # Read and verify structure
        queue_file = queue_dir / filename
        with open(queue_file) as f:
            data = json.load(f)

        # Required fields
        assert 'capture_id' in data, "Should have unique capture ID"
        assert 'context_id' in data, "Should have context ID"
        assert 'captured_at' in data, "Should have capture timestamp"
        assert 'learnings' in data, "Should have learnings array"
        assert 'metadata' in data, "Should have metadata"

        # Verify content
        assert data['context_id'] == 'self_contained_test'
        assert len(data['learnings']) == 1
        assert data['learnings'][0]['type'] == 'breakthrough'
        assert data['metadata']['agent'] == 'sre_principal_engineer_agent'
        assert data['metadata']['compaction_number'] == 3

    def test_handles_empty_learnings(self, tmp_path):
        """Should handle empty learnings list gracefully."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Empty learnings - should still create file or skip?
        # Design decision: Skip writing if no learnings
        filename = writer.write_queue_file(
            context_id='empty_test',
            learnings=[],
            metadata={}
        )

        # Should return None or skip writing
        assert filename is None, "Should not create file for empty learnings"

        # Verify no files created
        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 0, "Should not create file for empty learnings"

    def test_multiple_learnings_in_one_file(self, tmp_path):
        """Single queue file should handle multiple learnings."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'decision', 'content': 'learning 1', 'timestamp': datetime.now().isoformat(), 'context': {}},
            {'type': 'solution', 'content': 'learning 2', 'timestamp': datetime.now().isoformat(), 'context': {}},
            {'type': 'optimization', 'content': 'learning 3', 'timestamp': datetime.now().isoformat(), 'context': {}},
        ]

        filename = writer.write_queue_file(
            context_id='multi_learning',
            learnings=learnings,
            metadata={}
        )

        queue_file = queue_dir / filename
        with open(queue_file) as f:
            data = json.load(f)

        assert len(data['learnings']) == 3
        assert data['learnings'][0]['type'] == 'decision'
        assert data['learnings'][1]['type'] == 'solution'
        assert data['learnings'][2]['type'] == 'optimization'

    def test_concurrent_writes_different_contexts(self, tmp_path):
        """Multiple concurrent writes for different contexts should work."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Simulate concurrent writes
        contexts = ['ctx_1', 'ctx_2', 'ctx_3']
        filenames = []

        for ctx in contexts:
            learnings = [
                {'type': 'test', 'content': f'learning from {ctx}', 'timestamp': datetime.now().isoformat(), 'context': {}}
            ]
            filename = writer.write_queue_file(
                context_id=ctx,
                learnings=learnings,
                metadata={'context': ctx}
            )
            filenames.append(filename)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Verify all files created
        assert len(filenames) == 3
        assert len(set(filenames)) == 3, "All filenames should be unique"

        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 3

    def test_queue_file_is_valid_json(self, tmp_path):
        """Queue file should be valid JSON that can be parsed."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'security', 'content': 'fixed XSS vulnerability', 'timestamp': datetime.now().isoformat(), 'context': {}}
        ]

        filename = writer.write_queue_file(
            context_id='json_test',
            learnings=learnings,
            metadata={}
        )

        queue_file = queue_dir / filename

        # Should parse without error
        with open(queue_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert isinstance(data['learnings'], list)


class TestQueueFileCleanup:
    """Test cleanup of processed queue files."""

    def test_cleanup_processed_files(self, tmp_path):
        """Should delete specified processed files."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Create multiple queue files
        filenames = []
        for i in range(3):
            learnings = [
                {'type': 'test', 'content': f'test {i}', 'timestamp': datetime.now().isoformat(), 'context': {}}
            ]
            filename = writer.write_queue_file(
                context_id=f'cleanup_test_{i}',
                learnings=learnings,
                metadata={}
            )
            filenames.append(filename)
            time.sleep(0.01)

        # Cleanup first two files
        writer.cleanup_files([filenames[0], filenames[1]])

        # Verify only last file remains
        remaining_files = list(queue_dir.glob('*.json'))
        assert len(remaining_files) == 1
        assert remaining_files[0].name == filenames[2]

    def test_preserves_unprocessed_files(self, tmp_path):
        """Cleanup should only delete specified files."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Create 3 files
        filenames = []
        for i in range(3):
            learnings = [
                {'type': 'test', 'content': f'test {i}', 'timestamp': datetime.now().isoformat(), 'context': {}}
            ]
            filename = writer.write_queue_file(
                context_id=f'preserve_test_{i}',
                learnings=learnings,
                metadata={}
            )
            filenames.append(filename)
            time.sleep(0.01)

        # Cleanup only middle file
        writer.cleanup_files([filenames[1]])

        # Verify first and last remain
        remaining_files = sorted([f.name for f in queue_dir.glob('*.json')])
        assert len(remaining_files) == 2
        assert filenames[0] in remaining_files
        assert filenames[2] in remaining_files
        assert filenames[1] not in remaining_files

    def test_cleanup_handles_missing_files(self, tmp_path):
        """Cleanup should handle files that don't exist."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Try to cleanup non-existent files - should not error
        writer.cleanup_files(['nonexistent.json', 'also_missing.json'])

        # Should complete without error


class TestQueueFileRetrieval:
    """Test retrieving unprocessed queue files."""

    def test_get_unprocessed_files_oldest_first(self, tmp_path):
        """Should return queue files in chronological order (oldest first)."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        # Create files with delays to ensure different timestamps
        filenames = []
        for i in range(3):
            learnings = [
                {'type': 'test', 'content': f'test {i}', 'timestamp': datetime.now().isoformat(), 'context': {}}
            ]
            filename = writer.write_queue_file(
                context_id=f'order_test_{i}',
                learnings=learnings,
                metadata={}
            )
            filenames.append(filename)
            time.sleep(0.01)  # Ensure different timestamps

        # Get unprocessed files
        unprocessed = writer.get_unprocessed_files()

        # Should return in order
        assert len(unprocessed) == 3
        assert [f.name for f in unprocessed] == filenames, "Should be in chronological order"

    def test_get_unprocessed_returns_path_objects(self, tmp_path):
        """Should return Path objects for easy manipulation."""
        queue_dir = tmp_path / "queue"
        writer = QueueWriter(queue_dir=queue_dir)

        learnings = [
            {'type': 'test', 'content': 'path test', 'timestamp': datetime.now().isoformat(), 'context': {}}
        ]
        writer.write_queue_file(
            context_id='path_test',
            learnings=learnings,
            metadata={}
        )

        unprocessed = writer.get_unprocessed_files()
        assert len(unprocessed) == 1
        assert isinstance(unprocessed[0], Path)
        assert unprocessed[0].exists()
