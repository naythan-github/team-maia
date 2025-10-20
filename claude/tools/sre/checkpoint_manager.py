#!/usr/bin/env python3
"""
Checkpoint Manager - Resume-on-failure for long-running operations

NEW - Option B: Personal Mac Reliability
Provides checkpoint/resume capability for interrupted processing operations

Usage:
    from claude.tools.sre.checkpoint_manager import CheckpointManager

    checkpoint_mgr = CheckpointManager("vtt_processing")

    # Before starting work
    checkpoint = checkpoint_mgr.get_checkpoint(file_path)
    if checkpoint:
        # Resume from last successful stage
        start_from = checkpoint['stage']

    # Save progress at each stage
    checkpoint_mgr.save_checkpoint(file_path, 'parsing', {'lines': 100})
    checkpoint_mgr.save_checkpoint(file_path, 'summarizing', {'transcript_size': 5000})

    # Clear on success
    checkpoint_mgr.clear_checkpoint(file_path)

Author: SRE Principal Engineer Agent
Date: 2025-10-20
Phase: Personal Mac Reliability - Option B Implementation
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manage processing checkpoints for resume-on-failure capability.

    Stores checkpoints as JSON with:
    - file_path: Item being processed
    - stage: Current processing stage
    - timestamp: When checkpoint was saved
    - data: Stage-specific data
    - retry_count: Number of retries attempted
    """

    def __init__(self, checkpoint_name: str):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_name: Unique name for this checkpoint file
                           (e.g., 'vtt_processing', 'email_indexing')
        """
        self.checkpoint_dir = Path.home() / ".maia" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        self.checkpoints = self._load_checkpoints()

    def _load_checkpoints(self) -> Dict[str, Dict]:
        """Load existing checkpoints from disk"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load checkpoints: {e}")
                return {}
        return {}

    def _save_checkpoints(self):
        """Save checkpoints to disk"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoints, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checkpoints: {e}")

    def save_checkpoint(self, item_id: str, stage: str, data: Optional[Dict[str, Any]] = None):
        """
        Save processing checkpoint.

        Args:
            item_id: Unique identifier for item (file path, message ID, etc)
            stage: Current processing stage (e.g., 'parsing', 'summarizing')
            data: Optional stage-specific data
        """
        checkpoint = {
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'data': data or {},
            'retry_count': self.checkpoints.get(item_id, {}).get('retry_count', 0)
        }

        self.checkpoints[item_id] = checkpoint
        self._save_checkpoints()

        logger.info(f"Checkpoint saved: {item_id} @ {stage}")

    def get_checkpoint(self, item_id: str) -> Optional[Dict]:
        """
        Get existing checkpoint for item.

        Args:
            item_id: Item identifier

        Returns:
            Checkpoint dict or None if no checkpoint exists
        """
        return self.checkpoints.get(item_id)

    def clear_checkpoint(self, item_id: str):
        """
        Clear checkpoint after successful completion.

        Args:
            item_id: Item identifier
        """
        if item_id in self.checkpoints:
            del self.checkpoints[item_id]
            self._save_checkpoints()
            logger.info(f"Checkpoint cleared: {item_id}")

    def increment_retry(self, item_id: str) -> int:
        """
        Increment retry count for item.

        Args:
            item_id: Item identifier

        Returns:
            New retry count
        """
        if item_id in self.checkpoints:
            self.checkpoints[item_id]['retry_count'] = \
                self.checkpoints[item_id].get('retry_count', 0) + 1
            self._save_checkpoints()
            return self.checkpoints[item_id]['retry_count']
        return 0

    def should_give_up(self, item_id: str, max_retries: int = 3) -> bool:
        """
        Check if item has exceeded max retries.

        Args:
            item_id: Item identifier
            max_retries: Maximum retry attempts

        Returns:
            True if should give up, False to continue
        """
        checkpoint = self.get_checkpoint(item_id)
        if checkpoint:
            return checkpoint.get('retry_count', 0) >= max_retries
        return False

    def list_pending_items(self) -> list:
        """
        Get list of items with pending checkpoints.

        Returns:
            List of item IDs with incomplete processing
        """
        return list(self.checkpoints.keys())

    def get_checkpoint_age_hours(self, item_id: str) -> Optional[float]:
        """
        Get age of checkpoint in hours.

        Args:
            item_id: Item identifier

        Returns:
            Hours since checkpoint or None if no checkpoint
        """
        checkpoint = self.get_checkpoint(item_id)
        if checkpoint and 'timestamp' in checkpoint:
            try:
                checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
                age = datetime.now() - checkpoint_time
                return age.total_seconds() / 3600
            except Exception:
                return None
        return None

    def cleanup_old_checkpoints(self, max_age_hours: int = 168):
        """
        Remove checkpoints older than max_age.

        Args:
            max_age_hours: Maximum checkpoint age in hours (default: 7 days)

        Returns:
            Number of checkpoints removed
        """
        removed = 0
        to_remove = []

        for item_id in self.checkpoints.keys():
            age = self.get_checkpoint_age_hours(item_id)
            if age and age > max_age_hours:
                to_remove.append(item_id)

        for item_id in to_remove:
            del self.checkpoints[item_id]
            removed += 1

        if removed > 0:
            self._save_checkpoints()
            logger.info(f"Cleaned up {removed} old checkpoints")

        return removed


def retry_with_backoff(func, *args, max_retries=3, base_delay=5, **kwargs):
    """
    Retry function with exponential backoff.

    NEW - Option B: Simple retry for external APIs

    Args:
        func: Function to retry
        *args: Positional arguments for func
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds (multiplied by attempt number)
        **kwargs: Keyword arguments for func

    Returns:
        Function result if successful

    Raises:
        Last exception if all retries exhausted
    """
    import time
    import requests

    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)

        except (requests.Timeout, requests.ConnectionError, ConnectionRefusedError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = base_delay * (attempt + 1)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")

        except Exception as e:
            # Don't retry on non-transient errors
            logger.error(f"Non-retryable error: {e}")
            raise

    raise last_exception


# Example usage
if __name__ == "__main__":
    # Demo checkpoint manager
    checkpoint_mgr = CheckpointManager("demo")

    # Simulate processing with checkpoints
    item_id = "/path/to/file.vtt"

    # Check for existing checkpoint
    checkpoint = checkpoint_mgr.get_checkpoint(item_id)
    if checkpoint:
        print(f"Resuming from checkpoint: {checkpoint['stage']}")
    else:
        print("Starting fresh processing")

    # Save checkpoints at each stage
    checkpoint_mgr.save_checkpoint(item_id, "parsing", {"lines": 100})
    checkpoint_mgr.save_checkpoint(item_id, "summarizing", {"size": 5000})
    checkpoint_mgr.save_checkpoint(item_id, "saving", {})

    # Success - clear checkpoint
    checkpoint_mgr.clear_checkpoint(item_id)

    print("\n✅ Checkpoint manager demo complete")
