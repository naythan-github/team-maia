#!/usr/bin/env python3
"""
Preference Detection Module

Phase 234: Detect user corrections and preferences from conversation patterns.
"""

import re
from typing import Dict, Any, List, Optional, Pattern


def _compile_patterns(patterns: List[str]) -> List[Pattern]:
    """Compile a list of regex patterns with IGNORECASE flag."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Correction signal patterns (pre-compiled for performance)
EXPLICIT_REJECTION_PATTERNS = _compile_patterns([
    r'^no[,.\s]',
    r'^nope',
    r"^that'?s? (?:wrong|incorrect|not (?:right|correct|what))",
    r'^wrong',
    r'^incorrect',
])

REDIRECT_PATTERNS = _compile_patterns([
    r'^actually[,\s]',
    r'^wait[,\s]',
    r'^hold on',
    r'instead[,.\s]',
    r'rather[,.\s]',
    r'not that[,.\s]',
])

# Explicit preference patterns (pre-compiled)
PREFERENCE_PATTERNS = {
    'stated_preference': _compile_patterns([
        r'i prefer\s+(.+)',
        r'i like\s+(.+?)(?:\s+better|\s+more)?',
        r'i\'?d? rather\s+(.+)',
        r'my preference is\s+(.+)',
    ]),
    'rule': _compile_patterns([
        r'always\s+(.+)',
        r'make sure (?:to\s+)?(.+)',
        r'please always\s+(.+)',
    ]),
    'prohibition': _compile_patterns([
        r'never\s+(.+)',
        r"don'?t\s+(.+)",
        r'do not\s+(.+)',
        r'avoid\s+(.+)',
        r'no\s+(.+?)(?:\s+please)?$',
    ]),
}

# Category detection patterns (pre-compiled)
CATEGORY_PATTERNS = {
    'coding_style': _compile_patterns([
        r'indent', r'spacing', r'format', r'style', r'naming',
        r'tabs?', r'spaces?', r'quotes?', r'semicolons?',
    ]),
    'tool_choice': _compile_patterns([
        r'npm', r'yarn', r'pnpm', r'pip', r'cargo', r'brew',
        r'use\s+\w+\s+instead', r'switch to', r'migrate to',
    ]),
    'language': _compile_patterns([
        r'typescript', r'javascript', r'python', r'rust', r'go',
        r'java', r'kotlin', r'swift', r'ruby',
    ]),
    'communication': _compile_patterns([
        r'brief', r'concise', r'detailed', r'explain', r'verbose',
        r'just (?:show|give)', r'no (?:need|explanation)',
    ]),
}


def detect_correction(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect if the latest user message is a correction.

    Args:
        messages: List of message dicts with 'role' and 'content'

    Returns:
        Dict with is_correction, correction_type, and details
    """
    if len(messages) < 2:
        return {'is_correction': False}

    # Get the last user message
    last_user_msg = None
    prev_assistant_msg = None

    for i in range(len(messages) - 1, -1, -1):
        if messages[i]['role'] == 'user' and last_user_msg is None:
            last_user_msg = messages[i]['content'].lower().strip()
        elif messages[i]['role'] == 'assistant' and last_user_msg is not None:
            prev_assistant_msg = messages[i]['content'].lower().strip()
            break

    if not last_user_msg or not prev_assistant_msg:
        return {'is_correction': False}

    # Check for explicit rejection
    for pattern in EXPLICIT_REJECTION_PATTERNS:
        if pattern.search(last_user_msg):
            return {
                'is_correction': True,
                'correction_type': 'explicit_rejection',
                'original': prev_assistant_msg[:200],
                'correction': last_user_msg,
            }

    # Check for redirect
    for pattern in REDIRECT_PATTERNS:
        if pattern.search(last_user_msg):
            return {
                'is_correction': True,
                'correction_type': 'redirect',
                'original': prev_assistant_msg[:200],
                'correction': last_user_msg,
            }

    return {'is_correction': False}


def detect_preference(message: str) -> Dict[str, Any]:
    """
    Detect explicit preference statements in a message.

    Args:
        message: User message text

    Returns:
        Dict with has_preference, preference_type, and value
    """
    message_lower = message.lower().strip()

    for pref_type, patterns in PREFERENCE_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(message_lower)
            if match:
                return {
                    'has_preference': True,
                    'preference_type': pref_type,
                    'value': match.group(1) if match.groups() else message,
                    'raw': message,
                }

    return {'has_preference': False}


def detect_implicit_correction(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect implicit corrections (re-asks, alternatives).

    Args:
        messages: List of message dicts

    Returns:
        Dict with is_implicit_correction and correction_type
    """
    if len(messages) < 3:
        return {'is_implicit_correction': False}

    # Look for pattern: user asks -> assistant responds -> user asks again with refinement
    user_messages = [m['content'].lower() for m in messages if m['role'] == 'user']

    if len(user_messages) < 2:
        return {'is_implicit_correction': False}

    last_user = user_messages[-1]
    prev_user = user_messages[-2] if len(user_messages) >= 2 else ""

    # Check if last message is a refinement of previous
    # Simple heuristic: significant word overlap + new constraints
    last_words = set(re.findall(r'\b\w+\b', last_user))
    prev_words = set(re.findall(r'\b\w+\b', prev_user))

    overlap = len(last_words & prev_words)
    new_words = last_words - prev_words

    # If there's overlap and new constraints, it's likely a refinement
    if overlap >= 2 and len(new_words) >= 1:
        return {
            'is_implicit_correction': True,
            'correction_type': 'refined_request',
            'refinement_words': list(new_words)[:5],
        }

    # Check for "no" followed by alternative
    if prev_user.strip() in ('no', 'nope', 'wrong'):
        return {
            'is_implicit_correction': True,
            'correction_type': 'alternative_after_rejection',
        }

    return {'is_implicit_correction': False}


def extract_preference(correction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured preference from a correction.

    Args:
        correction: Correction dict from detect_correction

    Returns:
        Dict with category, key, value
    """
    if not correction.get('is_correction'):
        return {}

    text = correction.get('correction', '')

    # Detect category
    category = 'general'
    for cat, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                category = cat
                break

    # Extract key (main subject)
    key = 'preference'
    for cat, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                key = match.group(0)
                break

    return {
        'category': category,
        'key': key,
        'value': text,
        'source': 'correction',
    }


def calculate_confidence(preference: Dict[str, Any]) -> float:
    """
    Calculate confidence score for a preference.

    Args:
        preference: Preference dict

    Returns:
        Confidence score between 0 and 1
    """
    base_confidence = 0.5

    # Explicit preferences have higher confidence
    if preference.get('source') == 'explicit':
        base_confidence = 0.8
    elif preference.get('source') == 'implicit':
        base_confidence = 0.5

    # Certain patterns are more confident
    pattern = preference.get('pattern', '')
    if pattern in ('I prefer', 'always', 'never'):
        base_confidence = max(base_confidence, 0.85)
    elif pattern == 'no':
        base_confidence = max(base_confidence, 0.7)

    # Repeated occurrences increase confidence
    occurrences = preference.get('occurrence_count', 1)
    if occurrences >= 3:
        base_confidence = min(base_confidence + 0.15, 0.95)
    elif occurrences >= 2:
        base_confidence = min(base_confidence + 0.1, 0.9)

    return base_confidence


def analyze_conversation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze a conversation for all preference types.

    Args:
        messages: List of message dicts

    Returns:
        Dict with preferences list and summary
    """
    preferences = []

    # Check each user message for explicit preferences
    for msg in messages:
        if msg['role'] != 'user':
            continue

        pref = detect_preference(msg['content'])
        if pref['has_preference']:
            preferences.append({
                'type': pref['preference_type'],
                'value': pref['value'],
                'raw': pref.get('raw', ''),
                'confidence': calculate_confidence({'source': 'explicit', 'pattern': pref['preference_type']}),
            })

    # Check for corrections (need message pairs)
    for i in range(1, len(messages)):
        if messages[i]['role'] == 'user':
            correction = detect_correction(messages[:i+1])
            if correction['is_correction']:
                extracted = extract_preference(correction)
                if extracted:
                    preferences.append({
                        'type': extracted['category'],
                        'value': extracted['value'],
                        'confidence': calculate_confidence({'source': 'correction', 'pattern': 'no'}),
                    })

    return {
        'preferences': preferences,
        'total_found': len(preferences),
    }


__all__ = [
    "detect_correction",
    "detect_preference",
    "detect_implicit_correction",
    "extract_preference",
    "calculate_confidence",
    "analyze_conversation",
]
