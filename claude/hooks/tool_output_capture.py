#!/usr/bin/env python3
"""
Tool Output Capture Hook

Phase 234: PostToolUse hook that captures tool outputs to UOCS.

This hook is triggered after each tool execution and captures
the output for learning and analysis.

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
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

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

    try:
        capture_result = capture_to_uocs(input_data)
        result.update(capture_result)
    except Exception as e:
        result['error'] = str(e)
        result['captured'] = False

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
]
