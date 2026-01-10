#!/usr/bin/env python3
"""
Phase 5: Queue Processor - TDD Tests

Tests for QueueProcessor that reads queue files and inserts learnings
to PAI v2 database with retry logic and error handling.
"""

import pytest
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime

from claude.tools.learning.continuous_capture.queue_writer import QueueWriter
from claude.tools.learning.continuous_capture.queue_processor import QueueProcessor


class TestQueueProcessorBasics:
    """Test basic queue processing functionality."""

    def test_processes_oldest_files_first(self, tmp_path):
        """Should process queue files in chronological order (oldest first)."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Create learning database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create 3 queue files with delays to ensure different timestamps
        writer = QueueWriter(queue_dir=queue_dir)

        filenames = []
        for i in range(3):
            learnings = [
                {
                    'type': 'decision',
                    'content': f'decision {i}',
                    'timestamp': datetime.now().isoformat(),
                    'context': {'order': i}
                }
            ]
            filename = writer.write_queue_file(
                context_id=f'ctx_{i}',
                learnings=learnings,
                metadata={'order': i}
            )
            filenames.append(filename)
            time.sleep(0.02)  # Ensure different timestamps

        # Process queue
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        # Should process all 3 files
        assert processed == 3, "Should process all queue files"

        # Verify files processed in order by checking DB insertion order
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT description FROM patterns ORDER BY first_seen ASC"
        )
        descriptions = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Should be in order: decision 0, decision 1, decision 2
        assert 'decision 0' in descriptions[0], "First file should be processed first"
        assert 'decision 1' in descriptions[1], "Second file should be processed second"
        assert 'decision 2' in descriptions[2], "Third file should be processed third"

    def test_inserts_to_database_correctly(self, tmp_path):
        """Should insert learnings to PAI v2 database with correct format."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Create learning database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create queue file with learning
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'solution',
                'content': 'Fixed bug by using exponential backoff',
                'timestamp': datetime.now().isoformat(),
                'context': {'agent': 'sre_principal_engineer_agent'}
            }
        ]

        writer.write_queue_file(
            context_id='test_ctx_123',
            learnings=learnings,
            metadata={'agent': 'sre_principal_engineer_agent'}
        )

        # Process queue
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        assert processed == 1, "Should process one file"

        # Verify database insertion
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT description FROM patterns")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1, "Should insert one pattern"

        # Verify content
        description = rows[0][0]
        assert 'exponential backoff' in description, "Should contain learning content"

    def test_deletes_only_after_confirmed_insert(self, tmp_path):
        """Should delete queue file only after successful database insertion."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Create learning database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create queue file
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'test',
                'content': 'All tests passing after TDD cycle',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        filename = writer.write_queue_file(
            context_id='delete_test',
            learnings=learnings,
            metadata={}
        )

        # Verify file exists before processing
        queue_file = queue_dir / filename
        assert queue_file.exists(), "Queue file should exist before processing"

        # Process queue
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        assert processed == 1, "Should process one file"

        # Verify file deleted after successful insert
        assert not queue_file.exists(), "Queue file should be deleted after processing"

        # Verify data in database (confirms insert happened before delete)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM patterns")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1, "Pattern should be in database"


class TestQueueProcessorErrorHandling:
    """Test error handling and retry logic."""

    def test_retries_on_database_failure(self, tmp_path):
        """Should retry failed insertions with exponential backoff."""
        queue_dir = tmp_path / "queue"

        # Create queue file but no database (will cause failure)
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'error_recovery',
                'content': 'Retry logic implementation',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        filename = writer.write_queue_file(
            context_id='retry_test',
            learnings=learnings,
            metadata={}
        )

        # Attempt to process with non-existent DB
        db_path = tmp_path / "nonexistent.db"
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path, max_retries=2)

        # Should fail but not crash
        processed = processor.process_queue_files()

        # Should process 0 files (failed)
        assert processed == 0, "Should not process files when DB unavailable"

        # Queue file should still exist (not deleted due to failure)
        queue_file = queue_dir / filename
        assert queue_file.exists(), "Queue file should remain after failure"

    def test_preserves_queue_on_partial_failure(self, tmp_path):
        """Should not delete queue file if database insertion fails."""
        queue_dir = tmp_path / "queue"

        # Create queue file
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'security',
                'content': 'Added input validation to prevent XSS',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        filename = writer.write_queue_file(
            context_id='partial_failure_test',
            learnings=learnings,
            metadata={}
        )

        # Process with missing database
        db_path = tmp_path / "missing.db"
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path, max_retries=1)
        processor.process_queue_files()

        # File should still exist
        queue_file = queue_dir / filename
        assert queue_file.exists(), "Queue file should not be deleted on failure"

    def test_logs_persistent_failures(self, tmp_path):
        """Should log alerts on persistent failures."""
        queue_dir = tmp_path / "queue"
        log_file = tmp_path / "processor.log"

        # Create queue file
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'optimization',
                'content': 'Reduced latency from 2s to 50ms',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        writer.write_queue_file(
            context_id='log_test',
            learnings=learnings,
            metadata={}
        )

        # Process with missing DB (will fail)
        db_path = tmp_path / "missing.db"
        processor = QueueProcessor(
            queue_dir=queue_dir,
            db_path=db_path,
            max_retries=2,
            log_file=log_file
        )
        processor.process_queue_files()

        # Verify log file created and contains error
        assert log_file.exists(), "Log file should be created"

        log_content = log_file.read_text()
        assert 'ERROR' in log_content or 'FAILED' in log_content, "Should log error"


class TestQueueProcessorEndToEnd:
    """Test end-to-end queue → database flow."""

    def test_end_to_end_queue_to_database(self, tmp_path):
        """Complete flow: write queue → process → verify database."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Initialize database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create multiple learnings in queue file
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'decision',
                'content': 'Decided to use queue-based architecture for durability',
                'timestamp': datetime.now().isoformat(),
                'context': {'agent': 'sre_principal_engineer_agent'}
            },
            {
                'type': 'solution',
                'content': 'Fixed sqlite3.Connection bug by using sqlite3.connect',
                'timestamp': datetime.now().isoformat(),
                'context': {'agent': 'sre_principal_engineer_agent'}
            },
            {
                'type': 'breakthrough',
                'content': 'Discovered PreCompact hooks have known bug',
                'timestamp': datetime.now().isoformat(),
                'context': {'agent': 'sre_principal_engineer_agent'}
            }
        ]

        writer.write_queue_file(
            context_id='e2e_test_ctx',
            learnings=learnings,
            metadata={'agent': 'sre_principal_engineer_agent', 'compaction_number': 1}
        )

        # Process queue
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        assert processed == 1, "Should process one queue file"

        # Verify all learnings in database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT description FROM patterns ORDER BY first_seen ASC")
        descriptions = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert len(descriptions) == 3, "Should have 3 patterns in database"

        # Verify content
        assert any('queue-based architecture' in d for d in descriptions), "Should have decision learning"
        assert any('sqlite3.Connection' in d for d in descriptions), "Should have solution learning"
        assert any('PreCompact hooks' in d for d in descriptions), "Should have breakthrough learning"

        # Verify queue file deleted
        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 0, "Queue file should be deleted after processing"

    def test_handles_multiple_queue_files(self, tmp_path):
        """Should process multiple queue files in sequence."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Initialize database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create 3 queue files
        writer = QueueWriter(queue_dir=queue_dir)

        for i in range(3):
            learnings = [
                {
                    'type': 'test',
                    'content': f'Test batch {i} passed',
                    'timestamp': datetime.now().isoformat(),
                    'context': {}
                }
            ]
            writer.write_queue_file(
                context_id=f'batch_{i}',
                learnings=learnings,
                metadata={}
            )
            time.sleep(0.01)  # Ensure different timestamps

        # Process all
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        assert processed == 3, "Should process all 3 queue files"

        # Verify all in database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM patterns")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3, "Should have 3 patterns in database"

        # Verify all queue files deleted
        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 0, "All queue files should be deleted"

    def test_no_duplicate_insertions_on_reprocess(self, tmp_path):
        """Should not create duplicates if queue file reprocessed (idempotency test)."""
        queue_dir = tmp_path / "queue"
        db_path = tmp_path / "learning.db"

        # Initialize database
        from claude.tools.learning.schema import init_learning_db
        conn = init_learning_db(db_path)
        conn.close()

        # Create queue file
        writer = QueueWriter(queue_dir=queue_dir)
        learnings = [
            {
                'type': 'learning',
                'content': 'Unique learning content for deduplication test',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }
        ]

        filename = writer.write_queue_file(
            context_id='dedup_test',
            learnings=learnings,
            metadata={}
        )

        # Process queue
        processor = QueueProcessor(queue_dir=queue_dir, db_path=db_path)
        processed = processor.process_queue_files()

        assert processed == 1, "Should process one file"

        # Verify single entry
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM patterns WHERE description LIKE '%deduplication test%'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1, "Should have exactly one pattern (no duplicates)"

        # Queue file should be deleted, so reprocessing shouldn't happen
        queue_files = list(queue_dir.glob('*.json'))
        assert len(queue_files) == 0, "Queue file should be deleted"
