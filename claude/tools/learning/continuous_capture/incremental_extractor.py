#!/usr/bin/env python3
"""
Incremental Learning Extractor

Extracts learnings from transcript slices (start to end index) rather than
full transcripts. Designed to work with high-water mark tracking for
continuous capture.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from claude.tools.learning.extraction import LearningExtractor, LEARNING_PATTERNS


# Re-export pattern types for testing
PATTERN_TYPES = list(LEARNING_PATTERNS.keys())


class IncrementalExtractor:
    """
    Extract learnings from a slice of conversation transcript.

    Unlike the full extraction.py which processes entire conversations,
    this extracts only messages in the specified index range.
    """

    def __init__(self):
        """Initialize with standard learning patterns."""
        self.extractor = LearningExtractor()

    def extract_from_transcript(
        self,
        transcript_path: Path,
        start_index: int,
        end_index: int,
        context_id: Optional[str] = None,
        agent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract learnings from message range [start_index:end_index].

        Args:
            transcript_path: Path to JSONL transcript
            start_index: Start index (inclusive, 0-based)
            end_index: End index (exclusive, 0-based)
            context_id: Optional context identifier
            agent: Optional agent name

        Returns:
            List of learning dictionaries with structure:
            {
                'type': str,
                'content': str,
                'timestamp': str,
                'context': dict
            }
        """
        # Handle nonexistent or empty file
        if not transcript_path.exists():
            return []

        # Read and parse transcript
        messages = self._read_transcript(transcript_path)

        if not messages:
            return []

        # No new messages to process
        if start_index >= end_index:
            return []

        # Slice messages to range
        message_slice = messages[start_index:end_index]

        if not message_slice:
            return []

        # Convert slice back to JSONL for extractor
        jsonl_slice = '\n'.join(json.dumps(msg) for msg in message_slice)

        # Extract learnings using existing extractor
        result = self.extractor.extract_from_transcript(
            transcript=jsonl_slice,
            context_id=context_id
        )

        learnings = result.get('learnings', [])

        # Add agent to context if provided
        if agent:
            for learning in learnings:
                if 'context' not in learning:
                    learning['context'] = {}
                learning['context']['agent'] = agent

        # Add context_id if provided
        if context_id:
            for learning in learnings:
                if 'context' not in learning:
                    learning['context'] = {}
                learning['context']['context_id'] = context_id

        return learnings

    def _read_transcript(self, transcript_path: Path) -> List[Dict[str, Any]]:
        """
        Read and parse JSONL transcript file.

        Args:
            transcript_path: Path to transcript

        Returns:
            List of parsed message dictionaries
        """
        messages = []

        try:
            with open(transcript_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

        except (IOError, OSError):
            # File read error - return empty
            return []

        return messages

    def extract_from_messages(
        self,
        messages: List[Dict[str, Any]],
        context_id: Optional[str] = None,
        agent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract learnings directly from message list.

        Alternative to file-based extraction for testing or
        in-memory processing.

        Args:
            messages: List of message dictionaries
            context_id: Optional context identifier
            agent: Optional agent name

        Returns:
            List of learning dictionaries
        """
        if not messages:
            return []

        # Convert to JSONL
        jsonl = '\n'.join(json.dumps(msg) for msg in messages)

        # Extract
        result = self.extractor.extract_from_transcript(
            transcript=jsonl,
            context_id=context_id
        )

        learnings = result.get('learnings', [])

        # Add metadata
        if agent:
            for learning in learnings:
                if 'context' not in learning:
                    learning['context'] = {}
                learning['context']['agent'] = agent

        if context_id:
            for learning in learnings:
                if 'context' not in learning:
                    learning['context'] = {}
                learning['context']['context_id'] = context_id

        return learnings

    def count_messages(self, transcript_path: Path) -> int:
        """
        Count total messages in transcript.

        Args:
            transcript_path: Path to transcript

        Returns:
            Number of messages
        """
        messages = self._read_transcript(transcript_path)
        return len(messages)
