#!/usr/bin/env python3
"""
Tool Output Capture Hook

Phase 234: PostToolUse hook that captures tool outputs to UOCS.
Phase 264.1: Added tool counter auto-checkpoint (PreCompact workaround).

This hook is triggered after each tool execution and:
1. Captures the output for learning and analysis (UOCS)
2. Auto-saves checkpoint every CHECKPOINT_INTERVAL tools (default: 30)

The auto-checkpoint compensates for unreliable PreCompact hooks
(see GitHub issues #13572, #13668, #10814, #16047).

Install by adding to .claude/settings.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $CLAUDE_PROJECT_DIR/claude/hooks/tool_output_capture.py"
          }
        ]
      }
    ]
  }
}

Environment Variables:
  MAIA_CHECKPOINT_INTERVAL: Tool count between auto-checkpoints (default: 50)
  MAIA_CHECKPOINT_ENABLED: Set to "0" to disable auto-checkpoints (default: "1")
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def process_tool_output(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process tool output from PostToolUse hook.

    Args:
        input_data: Hook input with tool_name, tool_input, tool_response, session_id

    Returns:
        Processing result dict
    """
    result = {
        'processed': True,
        'decision': 'allow',  # PostToolUse hooks should not block
    }

    session_id = input_data.get('session_id', 'unknown')

    # Capture to UOCS
    try:
        capture_result = capture_to_uocs(input_data)
        result.update(capture_result)
    except Exception as e:
        result['error'] = str(e)
        result['captured'] = False

    # Phase 264.1: Check if auto-checkpoint needed
    try:
        checkpoint_result = maybe_auto_checkpoint(session_id)
        result['checkpoint'] = checkpoint_result
    except Exception as e:
        result['checkpoint_error'] = str(e)

    return result


def capture_to_uocs(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture tool output to UOCS.

    Args:
        input_data: Hook input data

    Returns:
        Capture result dict
    """
    tool_name = input_data.get('tool_name', 'unknown')
    tool_input = input_data.get('tool_input', {})
    tool_response = input_data.get('tool_response', {})
    session_id = input_data.get('session_id', 'unknown')
    duration_ms = input_data.get('duration_ms', 0)

    # Determine success from response
    success = True
    if isinstance(tool_response, dict):
        success = tool_response.get('success', True)
        if 'error' in tool_response or 'Error' in str(tool_response):
            success = False

    try:
        from claude.tools.learning.uocs import get_uocs

        uocs = get_uocs(session_id)

        # Convert response to string for capture
        if isinstance(tool_response, dict):
            output_str = json.dumps(tool_response, default=str)
        else:
            output_str = str(tool_response)

        uocs.capture(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=output_str,
            success=success,
            latency_ms=duration_ms
        )

        return {
            'captured': True,
            'session_id': session_id,
            'tool_name': tool_name,
            'latency_ms': duration_ms,
        }

    except Exception as e:
        return {
            'captured': False,
            'error': str(e),
        }


# ============================================================================
# Phase 264.1: Tool Counter Auto-Checkpoint
# ============================================================================

COUNTER_DIR = Path.home() / ".maia" / "state"
CHECKPOINT_INTERVAL = int(os.environ.get('MAIA_CHECKPOINT_INTERVAL', '30'))
CHECKPOINT_ENABLED = os.environ.get('MAIA_CHECKPOINT_ENABLED', '1') != '0'


def get_counter_file(session_id: str) -> Path:
    """Get path to tool counter file for this session."""
    COUNTER_DIR.mkdir(parents=True, exist_ok=True)
    return COUNTER_DIR / f"tool_counter_{session_id}.json"


def get_tool_count(session_id: str) -> int:
    """Get current tool count for session."""
    try:
        counter_file = get_counter_file(session_id)
        if counter_file.exists():
            data = json.loads(counter_file.read_text())
            return data.get('count', 0)
    except Exception:
        pass
    return 0


def increment_tool_count(session_id: str) -> int:
    """Increment and return new tool count."""
    try:
        counter_file = get_counter_file(session_id)
        count = get_tool_count(session_id) + 1
        data = {
            'count': count,
            'last_updated': datetime.now().isoformat(),
            'session_id': session_id,
        }
        counter_file.write_text(json.dumps(data, indent=2))
        return count
    except Exception:
        return 0


def reset_tool_count(session_id: str):
    """Reset tool count after checkpoint."""
    try:
        counter_file = get_counter_file(session_id)
        data = {
            'count': 0,
            'last_updated': datetime.now().isoformat(),
            'last_checkpoint': datetime.now().isoformat(),
            'session_id': session_id,
        }
        counter_file.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def trigger_auto_checkpoint(session_id: str) -> bool:
    """
    Trigger durable checkpoint save.

    Returns:
        True if checkpoint saved successfully
    """
    try:
        from claude.tools.sre.checkpoint import CheckpointGenerator

        generator = CheckpointGenerator()
        state = generator.gather_state()

        # Set auto-checkpoint metadata
        state.phase_name = "Auto-checkpoint (tool counter)"
        state.percent_complete = 50  # Unknown, assume mid-project
        state.tdd_phase = "P4"  # Default to implementation phase
        state.context_id = session_id

        result = generator.save_durable_checkpoint(state)

        if result:
            # Log success
            log_dir = Path.home() / ".maia" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "auto_checkpoint.log", 'a') as f:
                f.write(f"{datetime.now().isoformat()} [INFO] Auto-checkpoint saved: {result}\n")
            return True
        return False

    except Exception as e:
        # Log error but don't fail
        try:
            log_dir = Path.home() / ".maia" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "auto_checkpoint.log", 'a') as f:
                f.write(f"{datetime.now().isoformat()} [ERROR] Auto-checkpoint failed: {e}\n")
        except Exception:
            pass
        return False


def maybe_auto_checkpoint(session_id: str) -> Dict[str, Any]:
    """
    Check if auto-checkpoint should be triggered and do it.

    Returns:
        Dict with checkpoint status
    """
    if not CHECKPOINT_ENABLED:
        return {'checkpoint_enabled': False}

    count = increment_tool_count(session_id)

    if count >= CHECKPOINT_INTERVAL:
        success = trigger_auto_checkpoint(session_id)
        if success:
            reset_tool_count(session_id)
            return {
                'checkpoint_triggered': True,
                'checkpoint_success': True,
                'tool_count': 0,
            }
        else:
            return {
                'checkpoint_triggered': True,
                'checkpoint_success': False,
                'tool_count': count,
            }

    return {
        'checkpoint_triggered': False,
        'tool_count': count,
        'next_checkpoint_in': CHECKPOINT_INTERVAL - count,
    }


def generate_hook_config() -> Dict[str, Any]:
    """
    Generate Claude Code hook configuration for this hook.

    Returns:
        Hook configuration dict for settings.json
    """
    hook_path = Path(__file__).resolve()

    return {
        'PostToolUse': [
            {
                'matcher': '*',
                'hooks': [
                    {
                        'type': 'command',
                        'command': f'python3 {hook_path}',
                        'timeout': 5000,  # 5 second timeout
                    }
                ]
            }
        ]
    }


def main():
    """Main entry point for hook execution."""
    try:
        # Read input from stdin
        input_text = sys.stdin.read()

        if not input_text.strip():
            sys.exit(0)

        try:
            input_data = json.loads(input_text)
        except json.JSONDecodeError:
            # Invalid JSON - don't block, just exit
            sys.exit(0)

        result = process_tool_output(input_data)

        # Output result as JSON
        print(json.dumps(result))

        sys.exit(0)

    except Exception:
        # Never block on errors
        sys.exit(0)


if __name__ == '__main__':
    main()


__all__ = [
    "process_tool_output",
    "capture_to_uocs",
    "generate_hook_config",
    "main",
    # Phase 264.1 exports
    "get_tool_count",
    "increment_tool_count",
    "reset_tool_count",
    "trigger_auto_checkpoint",
    "maybe_auto_checkpoint",
    "CHECKPOINT_INTERVAL",
    "CHECKPOINT_ENABLED",
]
