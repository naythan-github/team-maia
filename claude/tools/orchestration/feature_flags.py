"""
Feature 5.4: Feature Flag & Rollout (F022)
Add feature flag for gradual rollout of automatic agent handoffs.

This module provides:
- Feature flag checking via user preferences
- Event logging for monitoring and rollout tracking
- Safe defaults (handoffs disabled by default)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_user_prefs_file() -> Path:
    """
    Get path to user preferences file.

    Returns:
        Path to claude/data/user_preferences.json
    """
    # Determine MAIA_ROOT from this file's location
    # claude/tools/orchestration/feature_flags.py -> go up 3 levels
    maia_root = Path(__file__).parent.parent.parent.parent.absolute()
    return maia_root / "claude" / "data" / "user_preferences.json"


def get_default_handoff_log_file() -> Path:
    """
    Get default path for handoff event logging.

    Returns:
        Path to claude/data/handoff_events.jsonl
    """
    maia_root = Path(__file__).parent.parent.parent.parent.absolute()
    log_dir = maia_root / "claude" / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "handoff_events.jsonl"


def is_handoffs_enabled(prefs_file: Optional[Path] = None) -> bool:
    """
    Check if agent handoffs feature is enabled.

    Reads from user_preferences.json. Handoffs are disabled by default
    for safe gradual rollout.

    Args:
        prefs_file: Optional path to preferences file (for testing)

    Returns:
        True if handoffs_enabled is True in preferences, False otherwise

    Performance: <5ms (single JSON read)
    Graceful: Never raises, returns False on any error
    """
    try:
        if prefs_file is None:
            prefs_file = get_user_prefs_file()

        if not prefs_file.exists():
            return False  # Default: disabled

        with open(prefs_file, 'r') as f:
            prefs = json.load(f)

        return prefs.get("handoffs_enabled", False)

    except (json.JSONDecodeError, IOError, KeyError):
        # Graceful degradation - default to disabled
        return False


def set_handoffs_enabled(enabled: bool, prefs_file: Optional[Path] = None) -> bool:
    """
    Enable or disable agent handoffs feature.

    Updates user_preferences.json with handoffs_enabled flag.

    Args:
        enabled: True to enable handoffs, False to disable
        prefs_file: Optional path to preferences file (for testing)

    Returns:
        True if successfully updated, False otherwise

    Performance: <10ms (read + write JSON)
    Graceful: Never raises, returns False on error
    """
    try:
        if prefs_file is None:
            prefs_file = get_user_prefs_file()

        # Load existing preferences or create new
        prefs = {}
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
            except (json.JSONDecodeError, IOError):
                prefs = {}

        # Update flag
        prefs["handoffs_enabled"] = enabled

        # Atomic write
        tmp_file = prefs_file.with_suffix(".tmp")
        with open(tmp_file, 'w') as f:
            json.dump(prefs, f, indent=2)
        tmp_file.replace(prefs_file)

        return True

    except (IOError, OSError):
        return False


def log_handoff_event(
    event_type: str,
    from_agent: str,
    to_agent: str,
    log_file: Optional[Path] = None,
    **kwargs
) -> bool:
    """
    Log a handoff event for monitoring and analysis.

    Events are logged in JSONL format (JSON Lines) for easy streaming
    and analysis. Each event includes timestamp and metadata.

    Args:
        event_type: Type of event (e.g., "handoff_triggered", "handoff_completed")
        from_agent: Agent handing off
        to_agent: Agent receiving handoff
        log_file: Optional path to log file (for testing)
        **kwargs: Additional event metadata

    Returns:
        True if logged successfully, False otherwise

    Performance: <10ms (append to file)
    Graceful: Never raises, returns False on error
    """
    try:
        if log_file is None:
            log_file = get_default_handoff_log_file()

        # Create event record
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "from_agent": from_agent,
            "to_agent": to_agent,
            **kwargs  # Include any additional metadata
        }

        # Append to JSONL file (each line is valid JSON)
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

        return True

    except (IOError, OSError):
        return False
