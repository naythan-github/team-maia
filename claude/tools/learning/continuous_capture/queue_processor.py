#!/usr/bin/env python3
"""
Queue Processor for Continuous Learning Capture

Reads queue files, inserts learnings to PAI v2 database, and deletes
processed files. Includes retry logic for resilience.
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from claude.tools.learning.continuous_capture.queue_writer import QueueWriter
from claude.tools.learning.pai_v2_bridge import PAIv2Bridge


class QueueProcessor:
    """
    Processes queue files by inserting learnings to database.

    Implements retry logic with exponential backoff and only deletes
    queue files after confirmed database insertion.
    """

    def __init__(
        self,
        queue_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
        max_retries: int = 3,
        log_file: Optional[Path] = None
    ):
        """
        Initialize queue processor.

        Args:
            queue_dir: Directory containing queue files (default: ~/.maia/learning_queue/)
            db_path: Path to learning database (default: ~/.maia/learning/learning.db)
            max_retries: Maximum retry attempts for failed insertions
            log_file: Optional log file path
        """
        self.queue_writer = QueueWriter(queue_dir=queue_dir)
        self.max_retries = max_retries

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers to prevent duplicates (each instance configures independently)
        self.logger.handlers.clear()

        # Add handler based on configuration
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
        else:
            # Default to console if no log file
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)

        # Initialize PAI v2 bridge with custom DB path if provided
        self.bridge = PAIv2Bridge()
        if db_path:
            self.bridge.db_path = db_path

    def process_queue_files(self) -> int:
        """
        Process all unprocessed queue files.

        Returns:
            Number of successfully processed files
        """
        queue_files = self.queue_writer.get_unprocessed_files()
        processed_count = 0

        for queue_file in queue_files:
            if self._process_single_file(queue_file):
                processed_count += 1

        return processed_count

    def _process_single_file(self, queue_file: Path) -> bool:
        """
        Process a single queue file with retry logic.

        Args:
            queue_file: Path to queue file

        Returns:
            True if successfully processed and deleted, False otherwise
        """
        filename = queue_file.name

        # Attempt to process with retries
        for attempt in range(self.max_retries):
            try:
                # Read queue file
                queue_data = self.queue_writer.read_queue_file(filename)

                # Extract fields
                context_id = queue_data.get('context_id', 'unknown')
                learnings = queue_data.get('learnings', [])
                metadata = queue_data.get('metadata', {})

                if not learnings:
                    self.logger.warning(f"Queue file {filename} has no learnings, skipping")
                    # Delete empty queue file
                    self.queue_writer.cleanup_files([filename])
                    return True

                # Insert to database via PAI v2 bridge
                pattern_ids = self.bridge.save_learnings_as_patterns(
                    learnings=learnings,
                    context_id=context_id,
                    session_id=metadata.get('session_id'),
                    domain=metadata.get('domain')
                )

                # Verify insertion successful
                if pattern_ids:
                    self.logger.info(
                        f"Successfully processed {filename}: "
                        f"{len(pattern_ids)} patterns inserted"
                    )

                    # Delete queue file only after confirmed insertion
                    self.queue_writer.cleanup_files([filename])
                    return True
                else:
                    raise RuntimeError("No pattern IDs returned from database insert")

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {filename}: {e}"
                )

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    backoff_time = 2 ** attempt  # 1s, 2s, 4s
                    self.logger.info(f"Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                else:
                    # Final attempt failed
                    self.logger.error(
                        f"FAILED to process {filename} after {self.max_retries} attempts: {e}"
                    )
                    return False

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Dictionary with queue statistics
        """
        unprocessed = self.queue_writer.get_unprocessed_files()

        return {
            'unprocessed_count': len(unprocessed),
            'oldest_file': unprocessed[0].name if unprocessed else None,
            'queue_dir': str(self.queue_writer.queue_dir)
        }
