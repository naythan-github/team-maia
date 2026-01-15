#!/usr/bin/env python3
"""
Prompt Capture Hook

Sprint: SPRINT-002-PROMPT-CAPTURE
UserPromptSubmit hook that captures all user prompts for learning and team sharing.

This hook is triggered on every user prompt submission and:
1. Captures the prompt text to memory.db
2. Stores session context for retrieval
3. Non-blocking (<50ms target)

Install by adding to ~/.claude/settings.json:
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $CLAUDE_PROJECT_DIR/claude/hooks/prompt_capture.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}

Environment Variables:
    CLAUDE_CONTEXT_ID - Context window ID
    CLAUDE_USER_MESSAGE - The user's prompt text (fallback)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def capture_prompt(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture user prompt from UserPromptSubmit hook.

    Args:
        input_data: Hook input with prompt_text, context_id, session_id

    Returns:
        Capture result dict
    """
    prompt_text = input_data.get('prompt_text', '') or input_data.get('user_message', '')
    context_id = input_data.get('context_id') or input_data.get('session_id', 'unknown')

    if not prompt_text:
        return {'captured': False, 'reason': 'empty_prompt'}

    # Resolve session_id from session files
    session_id = _resolve_session_id(context_id)

    if not session_id:
        return {'captured': False, 'reason': 'no_session'}

    try:
        from claude.tools.learning.memory import get_memory

        memory = get_memory()

        # Get active agent from session file if available
        agent_active = _get_active_agent(context_id)

        prompt_id = memory.capture_prompt(
            session_id=session_id,
            context_id=context_id,
            prompt_text=prompt_text,
            agent_active=agent_active
        )

        return {
            'captured': True,
            'prompt_id': prompt_id,
            'session_id': session_id,
            'char_count': len(prompt_text),
        }
    except Exception as e:
        _log_error(f"Capture failed: {e}")
        return {'captured': False, 'error': str(e)}


def _resolve_session_id(context_id: str) -> Optional[str]:
    """Resolve session_id from context_id using session files."""
    sessions_dir = Path.home() / ".maia" / "sessions"

    # Try learning session file first
    learning_file = sessions_dir / f"learning_session_{context_id}.json"
    if learning_file.exists():
        try:
            with open(learning_file) as f:
                data = json.load(f)
                return data.get('session_id')
        except Exception:
            pass

    # Try swarm session file
    swarm_file = sessions_dir / f"swarm_session_{context_id}.json"
    if swarm_file.exists():
        try:
            with open(swarm_file) as f:
                data = json.load(f)
                # Swarm sessions might not have session_id, generate one
                return data.get('session_id') or f"swarm_{context_id}"
        except Exception:
            pass

    return None


def _get_active_agent(context_id: str) -> Optional[str]:
    """Get currently active agent from session file."""
    sessions_dir = Path.home() / ".maia" / "sessions"

    swarm_file = sessions_dir / f"swarm_session_{context_id}.json"
    if swarm_file.exists():
        try:
            with open(swarm_file) as f:
                data = json.load(f)
                return data.get('current_agent')
        except Exception:
            pass

    return None


def _log_error(message: str):
    """Log error to file (non-blocking)."""
    try:
        log_dir = Path.home() / ".maia" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "prompt_capture.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} [ERROR] {message}\n")
    except Exception:
        pass


def _log_debug(message: str):
    """Log debug message (non-blocking)."""
    try:
        log_dir = Path.home() / ".maia" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "prompt_capture.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} [DEBUG] {message}\n")
    except Exception:
        pass


def process_prompt(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user prompt from UserPromptSubmit hook.

    Args:
        input_data: Hook input with prompt_text, context_id

    Returns:
        Processing result dict (always allows prompt)
    """
    result = {
        'processed': True,
        'decision': 'allow',  # Never block user prompts
    }

    try:
        capture_result = capture_prompt(input_data)
        result.update(capture_result)
        if capture_result.get('captured'):
            _log_debug(f"Captured prompt: {capture_result.get('prompt_id')} ({capture_result.get('char_count')} chars)")
    except Exception as e:
        result['error'] = str(e)
        result['captured'] = False
        _log_error(f"Process failed: {e}")

    return result


def generate_hook_config() -> Dict[str, Any]:
    """Generate Claude Code hook configuration for copy/paste."""
    hook_path = Path(__file__).resolve()

    return {
        'UserPromptSubmit': [
            {
                'matcher': '*',
                'hooks': [
                    {
                        'type': 'command',
                        'command': f'python3 {hook_path}',
                        'timeout': 5000,
                    }
                ]
            }
        ]
    }


def main():
    """Main entry point for hook execution."""
    try:
        input_text = sys.stdin.read()

        if not input_text.strip():
            # Fall back to environment variables
            input_data = {
                'prompt_text': os.environ.get('CLAUDE_USER_MESSAGE', ''),
                'context_id': os.environ.get('CLAUDE_CONTEXT_ID', 'unknown'),
            }
        else:
            try:
                input_data = json.loads(input_text)
            except json.JSONDecodeError:
                # Not valid JSON, try as plain text prompt
                input_data = {
                    'prompt_text': input_text,
                    'context_id': os.environ.get('CLAUDE_CONTEXT_ID', 'unknown'),
                }

        result = process_prompt(input_data)

        # Output result for Claude Code
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # Emergency error handling - never block
        try:
            _log_error(f"Hook crashed: {e}")
        except Exception:
            pass

        # Return allow to never block user
        print(json.dumps({'decision': 'allow', 'error': str(e)}))
        sys.exit(0)


if __name__ == '__main__':
    main()
