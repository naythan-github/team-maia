#!/usr/bin/env python3
"""
Capture State Manager for Continuous Learning Capture

Tracks high-water marks (last processed message index) per context
to enable incremental learning capture that survives compaction.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class CaptureStateManager:
    """
    Manages capture state for each Claude context.

    Stores high-water marks to track which messages have been processed,
    detects compaction events, and resets state appropriately.

    State format:
    {
        "context_id": str,
        "last_message_index": int,  # Last processed message (0-indexed)
        "last_message_count": int,  # Total messages when last captured
        "last_capture_timestamp": str,  # ISO timestamp
        "compaction_count": int  # Number of compactions detected
    }
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            state_dir: Directory for state files (default: ~/.maia/capture_state/)
        """
        if state_dir is None:
            state_dir = Path.home() / ".maia" / "capture_state"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, context_id: str) -> Path:
        """Get path to state file for context."""
        # Sanitize context_id for filename
        safe_id = context_id.replace("/", "-").replace(":", "-")
        return self.state_dir / f"{safe_id}.json"

    def load_state(self, context_id: str) -> Dict[str, Any]:
        """
        Load state for a context.

        Args:
            context_id: Context identifier

        Returns:
            State dictionary with default values if not found
        """
        state_file = self._get_state_file(context_id)

        if not state_file.exists():
            # Return defaults for new context
            return {
                'context_id': context_id,
                'last_message_index': 0,
                'last_message_count': 0,
                'last_capture_timestamp': datetime.now().isoformat(),
                'compaction_count': 0
            }

        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Corrupted or unreadable - return defaults
            return {
                'context_id': context_id,
                'last_message_index': 0,
                'last_message_count': 0,
                'last_capture_timestamp': datetime.now().isoformat(),
                'compaction_count': 0
            }

    def save_state(
        self,
        context_id: str,
        last_message_index: int,
        last_message_count: int,
        compaction_count: int = 0
    ) -> None:
        """
        Save state for a context.

        Args:
            context_id: Context identifier
            last_message_index: Index of last processed message
            last_message_count: Total message count
            compaction_count: Number of compactions detected
        """
        state = {
            'context_id': context_id,
            'last_message_index': last_message_index,
            'last_message_count': last_message_count,
            'last_capture_timestamp': datetime.now().isoformat(),
            'compaction_count': compaction_count
        }

        state_file = self._get_state_file(context_id)

        # Atomic write using temp file
        temp_file = state_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2)

            # Atomic rename
            temp_file.replace(state_file)
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise RuntimeError(f"Failed to save state for {context_id}: {e}") from e

    def detect_compaction(self, context_id: str, current_message_count: int) -> bool:
        """
        Detect if compaction occurred by comparing message counts.

        Args:
            context_id: Context identifier
            current_message_count: Current number of messages

        Returns:
            True if compaction detected (count decreased), False otherwise
        """
        state = self.load_state(context_id)
        last_count = state['last_message_count']

        # First run - no previous state
        if last_count == 0:
            return False

        # Compaction = message count decreased
        return current_message_count < last_count

    def handle_compaction(self, context_id: str, new_message_count: int) -> None:
        """
        Handle compaction event by resetting high-water mark.

        Args:
            context_id: Context identifier
            new_message_count: New message count after compaction
        """
        state = self.load_state(context_id)

        # Reset high-water mark, increment compaction counter
        self.save_state(
            context_id=context_id,
            last_message_index=0,  # Reset to start
            last_message_count=new_message_count,
            compaction_count=state['compaction_count'] + 1
        )

    def update_high_water_mark(
        self,
        context_id: str,
        new_index: int,
        message_count: int
    ) -> None:
        """
        Update high-water mark after successful capture.

        Args:
            context_id: Context identifier
            new_index: New high-water mark index
            message_count: Current total message count
        """
        state = self.load_state(context_id)

        self.save_state(
            context_id=context_id,
            last_message_index=new_index,
            last_message_count=message_count,
            compaction_count=state['compaction_count']
        )

    def get_messages_to_process(
        self,
        context_id: str,
        current_message_count: int
    ) -> tuple[int, int]:
        """
        Get range of messages to process.

        Args:
            context_id: Context identifier
            current_message_count: Current total messages

        Returns:
            Tuple of (start_index, end_index) for messages to process
        """
        state = self.load_state(context_id)
        start_index = state['last_message_index']

        # Process from high-water mark to current count
        return (start_index, current_message_count)

    def reset_state(self, context_id: str) -> None:
        """
        Reset state for a context (for testing or manual intervention).

        Args:
            context_id: Context identifier
        """
        state_file = self._get_state_file(context_id)
        if state_file.exists():
            state_file.unlink()
