#!/usr/bin/env python3
"""
Queue File Writer for Continuous Learning Capture

Writes learnings to durable queue files before database operations.
Ensures no data loss even if database writes fail.
"""

import json
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class QueueWriter:
    """
    Writes learning captures to durable queue files.

    Queue files serve as a write-ahead log ensuring learnings are preserved
    on disk before attempting database operations. This makes the system
    resilient to database failures and allows async processing.

    File format: {timestamp}_{context_id}.json
    Location: ~/.maia/learning_queue/ (default)
    """

    def __init__(self, queue_dir: Optional[Path] = None):
        """
        Initialize queue writer.

        Args:
            queue_dir: Directory for queue files (default: ~/.maia/learning_queue/)
        """
        if queue_dir is None:
            queue_dir = Path.home() / ".maia" / "learning_queue"

        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def write_queue_file(
        self,
        context_id: str,
        learnings: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Write learnings to a queue file.

        Args:
            context_id: Context identifier
            learnings: List of extracted learning dictionaries
            metadata: Additional metadata (agent, compaction number, etc.)

        Returns:
            Filename of created queue file, or None if no learnings
        """
        # Skip if no learnings
        if not learnings:
            return None

        # Generate unique capture ID
        capture_id = f"cap_{uuid.uuid4().hex[:12]}"

        # Create queue data structure
        queue_data = {
            'capture_id': capture_id,
            'context_id': context_id,
            'captured_at': datetime.now().isoformat(),
            'learnings': learnings,
            'metadata': metadata
        }

        # Generate filename: {timestamp}_{context_id}.json
        timestamp = int(time.time())
        safe_context = context_id.replace("/", "-").replace(":", "-")
        filename = f"{timestamp}_{safe_context}.json"

        queue_file = self.queue_dir / filename

        # Atomic write using temp file
        temp_file = queue_file.with_suffix('.tmp')

        try:
            # Write to temp file
            with open(temp_file, 'w') as f:
                json.dump(queue_data, f, indent=2)

            # Atomic rename
            temp_file.replace(queue_file)

            return filename

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise RuntimeError(f"Failed to write queue file: {e}") from e

    def get_unprocessed_files(self) -> List[Path]:
        """
        Get list of unprocessed queue files, oldest first.

        Returns:
            List of Path objects for queue files, sorted chronologically
        """
        if not self.queue_dir.exists():
            return []

        # Get all .json files
        queue_files = list(self.queue_dir.glob('*.json'))

        # Sort by filename (timestamp prefix ensures chronological order)
        queue_files.sort()

        return queue_files

    def cleanup_files(self, filenames: List[str]) -> None:
        """
        Delete processed queue files.

        Args:
            filenames: List of filenames (not full paths) to delete
        """
        for filename in filenames:
            queue_file = self.queue_dir / filename

            try:
                if queue_file.exists():
                    queue_file.unlink()
            except Exception:
                # Ignore errors during cleanup
                # File might already be deleted or inaccessible
                pass

    def read_queue_file(self, filename: str) -> Dict[str, Any]:
        """
        Read and parse a queue file.

        Args:
            filename: Queue filename (not full path)

        Returns:
            Parsed queue data dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        queue_file = self.queue_dir / filename

        with open(queue_file, 'r') as f:
            return json.load(f)

    def count_unprocessed(self) -> int:
        """
        Count number of unprocessed queue files.

        Returns:
            Number of queue files waiting to be processed
        """
        return len(self.get_unprocessed_files())
