#!/usr/bin/env python3
"""
Learning Extraction Engine
Phase 237: Pre-Compaction Learning Capture

Responsibilities:
- Parse JSONL conversation transcripts
- Identify learning moments via pattern matching
- Extract conversation metadata (tools, agents, errors)
- Classify learnings using PAI v2 UOC taxonomy

Learning Categories:
- Decisions: Choice made with reasoning
- Solutions: Problem fixed with method
- Outcomes: Result of action (success/failure)
- Handoffs: Agent transitions
- Checkpoints: Save state, commits, deploys

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


# Learning pattern definitions
LEARNING_PATTERNS = {
    'decision': [
        r'decided to (\w+)',
        r'chose (\w+) over (\w+)',
        r'went with (\w+)',
        r'using (\w+) because',
        r'selected (\w+)',
    ],
    'solution': [
        r'fixed (.*?) by (.*?)[\.\n]',
        r'root cause was (.*?)[\.\n]',
        r'resolved by (.*?)[\.\n]',
        r'solved (.*?) with (.*?)[\.\n]',
        r'debugged (.*?)[\.\n]',
    ],
    'outcome': [
        r'✅.*?worked',
        r'✅.*?complete',
        r'✅.*?passed',
        r'failed because (.*?)[\.\n]',
        r'blocked by (.*?)[\.\n]',
        r'error:? (.*?)[\.\n]',
    ],
    'handoff': [
        r'HANDOFF DECLARATION:',
        r'To: (\w+)_agent',
        r'handing off to (\w+)',
    ],
    'checkpoint': [
        r'save state',
        r'git commit',
        r'deployed to',
        r'git push',
        r'✅.*?committed',
    ],
}


@dataclass
class LearningMoment:
    """Represents a single learning extracted from conversation."""
    type: str  # decision, solution, outcome, handoff, checkpoint
    content: str  # The actual learning content
    timestamp: str  # ISO timestamp
    context: Dict[str, Any]  # Surrounding messages, agent, tools used
    confidence: float = 1.0  # Pattern match confidence (0-1)


@dataclass
class ConversationMetadata:
    """Metadata extracted from conversation."""
    tool_usage: Dict[str, int]  # Tool name -> count
    agents_used: List[str]  # List of agents mentioned
    error_count: int  # Number of errors encountered
    message_count: int  # Total messages
    assistant_message_count: int  # Assistant messages only
    user_message_count: int  # User messages only
    tool_call_count: int  # Tool invocations


class LearningExtractor:
    """
    Extracts learnings and metadata from conversation transcripts.

    Uses regex pattern matching to identify UOCs (Units of Conscious Insight)
    and conversation metadata for archival and retrieval.
    """

    def __init__(self, patterns: Optional[Dict[str, List[str]]] = None):
        """
        Initialize extractor with learning patterns.

        Args:
            patterns: Custom pattern dictionary (default: LEARNING_PATTERNS)
        """
        self.patterns = patterns or LEARNING_PATTERNS

        # Compile regex patterns for performance
        self.compiled_patterns = {}
        for category, pattern_list in self.patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in pattern_list
            ]

    def extract_from_transcript(
        self,
        transcript: str,
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract learnings and metadata from JSONL transcript.

        Args:
            transcript: JSONL formatted conversation
            context_id: Optional context ID for tracking

        Returns:
            {
                'learnings': List[LearningMoment],
                'metadata': ConversationMetadata,
                'context_id': str
            }
        """
        messages = self._parse_transcript(transcript)

        learnings = []
        metadata = self._extract_metadata(messages)

        # Extract learnings from each message
        for i, message in enumerate(messages):
            if message.get('type') == 'assistant_message':
                content = message.get('content', '')
                timestamp = message.get('timestamp', datetime.now().isoformat())

                # Check each learning category
                for category in self.compiled_patterns:
                    for pattern in self.compiled_patterns[category]:
                        matches = pattern.finditer(content)
                        for match in matches:
                            learning = LearningMoment(
                                type=category,
                                content=self._extract_learning_content(content, match),
                                timestamp=timestamp,
                                context=self._build_context(messages, i, message),
                                confidence=self._calculate_confidence(category, match)
                            )
                            learnings.append(learning)

        return {
            'learnings': [asdict(l) for l in learnings],
            'metadata': asdict(metadata),
            'context_id': context_id
        }

    def _parse_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Parse JSONL transcript into message list.

        Args:
            transcript: JSONL formatted conversation

        Returns:
            List of message dictionaries
        """
        messages = []
        for line in transcript.strip().split('\n'):
            if line.strip():
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return messages

    def _extract_metadata(self, messages: List[Dict[str, Any]]) -> ConversationMetadata:
        """
        Extract conversation metadata.

        Args:
            messages: List of parsed messages

        Returns:
            ConversationMetadata object
        """
        tool_usage = {}
        agents_used = set()
        error_count = 0
        tool_call_count = 0
        assistant_count = 0
        user_count = 0

        for message in messages:
            msg_type = message.get('type', '')
            content = message.get('content', '')

            # Count message types
            if msg_type == 'assistant_message':
                assistant_count += 1

                # Extract agent mentions
                agent_pattern = re.compile(r'(\w+)_agent', re.IGNORECASE)
                for match in agent_pattern.finditer(content):
                    agents_used.add(match.group(0))

                # Count errors
                if any(err in content.lower() for err in ['error', 'failed', 'exception']):
                    error_count += 1

            elif msg_type == 'user_message':
                user_count += 1

            elif msg_type == 'tool_use' or msg_type == 'tool_call':
                tool_call_count += 1
                tool_name = message.get('tool', 'unknown')
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        return ConversationMetadata(
            tool_usage=tool_usage,
            agents_used=list(agents_used),
            error_count=error_count,
            message_count=len(messages),
            assistant_message_count=assistant_count,
            user_message_count=user_count,
            tool_call_count=tool_call_count
        )

    def _extract_learning_content(
        self,
        full_content: str,
        match: re.Match
    ) -> str:
        """
        Extract learning content from regex match.

        Gets the matched text plus surrounding context (up to 200 chars).

        Args:
            full_content: Full message content
            match: Regex match object

        Returns:
            Learning content string
        """
        start = max(0, match.start() - 50)
        end = min(len(full_content), match.end() + 150)

        excerpt = full_content[start:end].strip()

        # Clean up excerpt
        if start > 0:
            excerpt = '...' + excerpt
        if end < len(full_content):
            excerpt = excerpt + '...'

        return excerpt

    def _build_context(
        self,
        messages: List[Dict[str, Any]],
        current_index: int,
        current_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build context for a learning moment.

        Includes surrounding messages, active tools, etc.

        Args:
            messages: All messages
            current_index: Index of current message
            current_message: The message containing the learning

        Returns:
            Context dictionary
        """
        # Get previous message for context
        previous_message = None
        if current_index > 0:
            previous_message = messages[current_index - 1]

        # Find recent tool uses
        recent_tools = []
        for i in range(max(0, current_index - 5), current_index):
            msg = messages[i]
            if msg.get('type') in ['tool_use', 'tool_call']:
                recent_tools.append(msg.get('tool', 'unknown'))

        return {
            'previous_message': previous_message.get('content', '')[:200] if previous_message else None,
            'message_index': current_index,
            'recent_tools': recent_tools[-3:],  # Last 3 tools
        }

    def _calculate_confidence(
        self,
        category: str,
        match: re.Match
    ) -> float:
        """
        Calculate confidence score for a learning match.

        Higher confidence for more specific patterns.

        Args:
            category: Learning category
            match: Regex match

        Returns:
            Confidence score (0-1)
        """
        # More specific categories get higher confidence
        confidence_by_category = {
            'decision': 0.9,
            'solution': 0.95,
            'outcome': 0.85,
            'handoff': 1.0,  # Very specific pattern
            'checkpoint': 0.9,
        }

        base_confidence = confidence_by_category.get(category, 0.8)

        # Boost confidence if match has multiple groups (more specific)
        if len(match.groups()) > 1:
            base_confidence = min(1.0, base_confidence + 0.05)

        return base_confidence


def get_extractor(patterns: Optional[Dict[str, List[str]]] = None) -> LearningExtractor:
    """
    Get learning extractor instance (singleton pattern).

    Args:
        patterns: Optional custom patterns

    Returns:
        LearningExtractor instance
    """
    if not hasattr(get_extractor, '_instance') or patterns is not None:
        get_extractor._instance = LearningExtractor(patterns)
    return get_extractor._instance
