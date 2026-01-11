"""
Tests for Feature 5.4: Feature Flag & Rollout (F022)
Add feature flag for gradual rollout.
"""

def test_handoffs_disabled_by_default():
    """Handoffs are disabled by default."""
    from claude.tools.orchestration.feature_flags import is_handoffs_enabled

    # Default should be False for safe rollout
    enabled = is_handoffs_enabled()
    assert enabled == False

def test_handoffs_can_be_enabled():
    """Handoffs can be enabled via user preferences."""
    from claude.tools.orchestration.feature_flags import is_handoffs_enabled, set_handoffs_enabled
    import tempfile
    import json
    from pathlib import Path

    # Create temp preferences file
    prefs_file = Path(tempfile.gettempdir()) / "test_user_prefs.json"
    prefs_file.write_text(json.dumps({"handoffs_enabled": True}))

    enabled = is_handoffs_enabled(prefs_file=prefs_file)
    assert enabled == True

def test_handoff_events_logged():
    """Handoff events are logged for monitoring."""
    from claude.tools.orchestration.feature_flags import log_handoff_event
    import tempfile
    from pathlib import Path

    log_file = Path(tempfile.gettempdir()) / "handoff_events.jsonl"

    log_handoff_event(
        event_type="handoff_triggered",
        from_agent="sre",
        to_agent="security",
        log_file=log_file
    )

    assert log_file.exists()
    content = log_file.read_text()
    assert "handoff_triggered" in content
