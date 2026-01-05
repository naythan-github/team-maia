#!/usr/bin/env python3
"""
Tests for Learning Extraction Engine
Phase 237: Pre-Compaction Learning Capture

Test Coverage:
- Pattern matching for all learning types
- Metadata extraction (tools, agents, errors)
- Context building
- Confidence scoring
- Edge cases (empty, malformed, no learnings)

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import pytest
from claude.tools.learning.extraction import (
    LearningExtractor,
    LearningMoment,
    ConversationMetadata,
    LEARNING_PATTERNS,
    get_extractor
)


@pytest.fixture
def extractor():
    """Create learning extractor instance."""
    return LearningExtractor()


@pytest.fixture
def sample_transcript_with_decision():
    """Transcript containing decision pattern."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Should we use SQLite or Postgres?',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'I decided to use SQLite because it requires no external service and is simpler to deploy.',
            'timestamp': '2026-01-06T10:00:05Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


@pytest.fixture
def sample_transcript_with_solution():
    """Transcript containing solution pattern."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Database connection is failing',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'Fixed the database timeout error by increasing the connection pool size from 5 to 20.',
            'timestamp': '2026-01-06T10:00:05Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


@pytest.fixture
def sample_transcript_with_tools():
    """Transcript with tool usage."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Create a new file',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Write',
            'content': 'Writing file...',
            'timestamp': '2026-01-06T10:00:05Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Read',
            'content': 'Reading file...',
            'timestamp': '2026-01-06T10:00:10Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Edit',
            'content': 'Editing file...',
            'timestamp': '2026-01-06T10:00:15Z'
        },
        {
            'type': 'assistant_message',
            'content': '✅ File created successfully',
            'timestamp': '2026-01-06T10:00:20Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_decision_pattern(extractor, sample_transcript_with_decision):
    """Test extraction of decision learning."""
    result = extractor.extract_from_transcript(sample_transcript_with_decision)

    learnings = result['learnings']
    assert len(learnings) > 0

    # Find decision learning
    decision = next((l for l in learnings if l['type'] == 'decision'), None)
    assert decision is not None
    assert 'SQLite' in decision['content'] or 'decided' in decision['content'].lower()
    assert decision['confidence'] >= 0.8


def test_extract_solution_pattern(extractor, sample_transcript_with_solution):
    """Test extraction of solution learning."""
    result = extractor.extract_from_transcript(sample_transcript_with_solution)

    learnings = result['learnings']
    assert len(learnings) > 0

    # Find solution learning
    solution = next((l for l in learnings if l['type'] == 'solution'), None)
    assert solution is not None
    assert 'fixed' in solution['content'].lower()
    assert solution['confidence'] >= 0.8


def test_extract_outcome_success(extractor):
    """Test extraction of successful outcome."""
    transcript = json.dumps({
        'type': 'assistant_message',
        'content': '✅ Tests passed successfully',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    outcome = next((l for l in learnings if l['type'] == 'outcome'), None)
    assert outcome is not None
    assert '✅' in outcome['content'] or 'passed' in outcome['content'].lower()


def test_extract_outcome_failure(extractor):
    """Test extraction of failed outcome."""
    transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'Test failed because the database connection timed out after 30 seconds.',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    outcome = next((l for l in learnings if l['type'] == 'outcome'), None)
    assert outcome is not None
    assert 'failed' in outcome['content'].lower()


def test_extract_handoff_pattern(extractor):
    """Test extraction of agent handoff."""
    transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'HANDOFF DECLARATION:\\nTo: python_code_reviewer_agent\\nReason: Code review required',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    handoff = next((l for l in learnings if l['type'] == 'handoff'), None)
    assert handoff is not None
    assert 'HANDOFF' in handoff['content']
    assert handoff['confidence'] == 1.0  # High confidence for handoffs


def test_extract_checkpoint_pattern(extractor):
    """Test extraction of checkpoint events."""
    transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'Let me save state before continuing. Running git commit...',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    checkpoint = next((l for l in learnings if l['type'] == 'checkpoint'), None)
    assert checkpoint is not None
    assert 'save state' in checkpoint['content'].lower() or 'git commit' in checkpoint['content'].lower()


def test_metadata_extraction_tool_usage(extractor, sample_transcript_with_tools):
    """Test tool usage frequency extraction."""
    result = extractor.extract_from_transcript(sample_transcript_with_tools)

    metadata = result['metadata']
    assert metadata['tool_usage']['Write'] == 1
    assert metadata['tool_usage']['Read'] == 1
    assert metadata['tool_usage']['Edit'] == 1
    assert metadata['tool_call_count'] == 3


def test_metadata_extraction_message_counts(extractor, sample_transcript_with_tools):
    """Test message count extraction."""
    result = extractor.extract_from_transcript(sample_transcript_with_tools)

    metadata = result['metadata']
    assert metadata['message_count'] == 5
    assert metadata['user_message_count'] == 1
    assert metadata['assistant_message_count'] == 1


def test_metadata_extraction_agents(extractor):
    """Test agent extraction from conversation."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Using sre_principal_engineer_agent for this task',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'Handing off to python_code_reviewer_agent',
            'timestamp': '2026-01-06T10:00:05Z'
        }
    ]
    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    result = extractor.extract_from_transcript(transcript)
    metadata = result['metadata']

    assert 'sre_principal_engineer_agent' in metadata['agents_used']
    assert 'python_code_reviewer_agent' in metadata['agents_used']


def test_metadata_extraction_error_count(extractor):
    """Test error counting."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Error: Connection refused',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'Failed to connect to database',
            'timestamp': '2026-01-06T10:00:05Z'
        },
        {
            'type': 'assistant_message',
            'content': 'Success!',
            'timestamp': '2026-01-06T10:00:10Z'
        }
    ]
    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    result = extractor.extract_from_transcript(transcript)
    metadata = result['metadata']

    assert metadata['error_count'] == 2


def test_empty_conversation(extractor):
    """Test handling of empty conversation."""
    result = extractor.extract_from_transcript("")

    assert result['learnings'] == []
    assert result['metadata']['message_count'] == 0
    assert result['metadata']['tool_call_count'] == 0


def test_malformed_jsonl(extractor):
    """Test handling of corrupted JSONL."""
    malformed = """
{"type": "user_message", "content": "Hello"}
This is not JSON
{"type": "assistant_message", "content": "I decided to use Python"}
{invalid json
"""

    result = extractor.extract_from_transcript(malformed)

    # Should skip malformed lines but process valid ones
    assert result['metadata']['message_count'] == 2
    assert len(result['learnings']) > 0  # Should find "decided to use"


def test_conversation_with_no_learnings(extractor):
    """Test conversation that contains no learning patterns."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Hello',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'Hi there! How can I help?',
            'timestamp': '2026-01-06T10:00:05Z'
        }
    ]
    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    result = extractor.extract_from_transcript(transcript)

    assert result['learnings'] == []
    assert result['metadata']['message_count'] == 2


def test_context_building(extractor):
    """Test that context includes surrounding messages and tools."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Create a database schema',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Write',
            'content': 'Writing schema...',
            'timestamp': '2026-01-06T10:00:05Z'
        },
        {
            'type': 'assistant_message',
            'content': 'I decided to use SQLite for simplicity.',
            'timestamp': '2026-01-06T10:00:10Z'
        }
    ]
    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    assert len(learnings) > 0
    decision = learnings[0]

    # Context should include previous message
    assert decision['context']['previous_message'] is not None
    # Context should include recent tools
    assert 'Write' in decision['context']['recent_tools']


def test_confidence_calculation(extractor):
    """Test confidence scoring for different patterns."""
    # Handoff should have highest confidence (1.0)
    handoff_transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'HANDOFF DECLARATION: To: test_agent',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(handoff_transcript)
    handoff = next((l for l in result['learnings'] if l['type'] == 'handoff'), None)
    assert handoff is not None
    assert handoff['confidence'] == 1.0

    # Solution should have high confidence (0.95)
    solution_transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'Fixed the bug by updating the config.',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(solution_transcript)
    solution = next((l for l in result['learnings'] if l['type'] == 'solution'), None)
    assert solution is not None
    assert solution['confidence'] >= 0.9


def test_multiple_learnings_in_single_message(extractor):
    """Test extraction of multiple learnings from one message."""
    transcript = json.dumps({
        'type': 'assistant_message',
        'content': '''I decided to use SQLite because it's simpler.
        Fixed the connection timeout by increasing the pool size.
        ✅ All tests passed successfully.''',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    # Should extract decision, solution, and outcome
    assert len(learnings) >= 3

    learning_types = [l['type'] for l in learnings]
    assert 'decision' in learning_types
    assert 'solution' in learning_types
    assert 'outcome' in learning_types


def test_custom_patterns(extractor):
    """Test extractor with custom patterns."""
    custom_patterns = {
        'custom_category': [
            r'discovered (.*?)[\.\n]',
        ]
    }

    custom_extractor = LearningExtractor(patterns=custom_patterns)

    transcript = json.dumps({
        'type': 'assistant_message',
        'content': 'Discovered that caching improves performance by 50%.',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = custom_extractor.extract_from_transcript(transcript)
    learnings = result['learnings']

    assert len(learnings) > 0
    assert learnings[0]['type'] == 'custom_category'


def test_singleton_pattern():
    """Test that get_extractor returns same instance."""
    extractor1 = get_extractor()
    extractor2 = get_extractor()

    assert extractor1 is extractor2


def test_context_id_passthrough(extractor):
    """Test that context_id is passed through to result."""
    transcript = json.dumps({
        'type': 'user_message',
        'content': 'Test message',
        'timestamp': '2026-01-06T10:00:00Z'
    })

    result = extractor.extract_from_transcript(transcript, context_id='test_context_123')

    assert result['context_id'] == 'test_context_123'


def test_large_conversation_performance(extractor):
    """Test extraction performance on large conversation."""
    import time

    # Create large conversation (1000 messages)
    messages = []
    for i in range(1000):
        messages.append({
            'type': 'assistant_message' if i % 2 else 'user_message',
            'content': f'Message {i}: I decided to use approach {i % 10} because it works best.',
            'timestamp': f'2026-01-06T10:{i // 60:02d}:{i % 60:02d}Z'
        })

    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    start_time = time.time()
    result = extractor.extract_from_transcript(transcript)
    extraction_time = time.time() - start_time

    # Should complete in reasonable time (<5s for 1000 messages)
    assert extraction_time < 5.0

    # Should extract learnings
    assert len(result['learnings']) > 0
    assert result['metadata']['message_count'] == 1000
