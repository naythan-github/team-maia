#!/usr/bin/env python3
"""
Pre-Compaction Learning Capture Hook
Phase 237: Intelligent Context Compaction with Learning Preservation

This hook is triggered by Claude Code before context compaction.
It extracts learnings and archives the full conversation to prevent data loss.

Hook Lifecycle:
1. Claude Code detects context near limit
2. Triggers PreCompact hook (this script)
3. Script extracts learnings + archives conversation
4. Returns success/failure
5. Claude Code proceeds with compaction

Input (from Claude Code via stdin):
{
    "session_id": "abc123",
    "transcript_path": "~/.claude/projects/.../abc123.jsonl",
    "hook_event_name": "PreCompact",
    "trigger": "auto" | "manual",
    "permission_mode": "default"
}

Output:
- Silent success (exit 0)
- Errors logged to ~/.maia/logs/pre_compaction_errors.log
- Metrics logged to compaction_metrics table

Design Principles:
- Non-blocking: Complete in <5s for 1000-message conversations
- Resilient: 3 retry attempts with exponential backoff
- Graceful degradation: Never block compaction on failure
- Observable: Comprehensive logging and metrics

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


def _setup_paths():
    """Set up Python paths for MAIA imports."""
    # Find MAIA root
    maia_root = Path(__file__).parent.parent.parent
    if str(maia_root) not in sys.path:
        sys.path.insert(0, str(maia_root))


_setup_paths()


from claude.tools.learning.extraction import get_extractor
from claude.tools.learning.archive import get_archive
from claude.tools.learning.pai_v2_bridge import get_pai_v2_bridge
from claude.tools.sre.checkpoint import CheckpointGenerator, DURABLE_CHECKPOINT_DIR


class PreCompactionHook:
    """
    Pre-compaction hook handler.

    Orchestrates learning extraction and conversation archival.
    """

    def __init__(self):
        """Initialize hook handler."""
        self.log_dir = Path.home() / ".maia" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.error_log = self.log_dir / "pre_compaction_errors.log"
        self.debug_log = self.log_dir / "pre_compaction_debug.log"

        self.extractor = get_extractor()
        self.archive = get_archive()
        self.pai_v2_bridge = get_pai_v2_bridge()
        self.checkpoint_generator = CheckpointGenerator()

    def process(
        self,
        hook_input: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Process pre-compaction hook.

        Args:
            hook_input: Hook data from Claude Code
            max_retries: Maximum retry attempts

        Returns:
            {
                'success': bool,
                'snapshot_id': int or None,
                'learnings_captured': int,
                'execution_time_ms': int,
                'error_message': str or None
            }
        """
        start_time = time.time()

        context_id = hook_input.get('session_id')
        transcript_path = Path(hook_input['transcript_path']).expanduser()
        trigger_type = hook_input.get('trigger', 'auto')

        self._log_debug(f"Processing hook for context {context_id}, trigger: {trigger_type}")

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                result = self._process_attempt(
                    context_id=context_id,
                    transcript_path=transcript_path,
                    trigger_type=trigger_type
                )

                execution_time_ms = int((time.time() - start_time) * 1000)
                result['execution_time_ms'] = execution_time_ms

                # Log success metric
                self._log_metric(
                    context_id=context_id,
                    trigger_type=trigger_type,
                    execution_time_ms=execution_time_ms,
                    success=True,
                    snapshot_id=result['snapshot_id'],
                    learnings_captured=result['learnings_captured'],
                    messages_processed=result['messages_processed']
                )

                self._log_debug(
                    f"Success: snapshot_id={result['snapshot_id']}, "
                    f"learnings={result['learnings_captured']}, "
                    f"time={execution_time_ms}ms"
                )

                return result

            except Exception as e:
                last_error = e
                self._log_error(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}"
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    sleep_time = 0.1 * (2 ** attempt)
                    time.sleep(sleep_time)
                    self._log_debug(f"Retrying after {sleep_time}s...")

        # All retries failed - graceful degradation
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_message = f"{type(last_error).__name__}: {last_error}"

        self._log_error(f"All retries failed. Final error: {error_message}")

        # Log failure metric
        self._log_metric(
            context_id=context_id,
            trigger_type=trigger_type,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=error_message
        )

        return {
            'success': False,
            'snapshot_id': None,
            'learnings_captured': 0,
            'execution_time_ms': execution_time_ms,
            'error_message': error_message
        }

    def _process_attempt(
        self,
        context_id: str,
        transcript_path: Path,
        trigger_type: str
    ) -> Dict[str, Any]:
        """
        Single processing attempt.

        Args:
            context_id: Claude context window ID
            transcript_path: Path to JSONL transcript
            trigger_type: 'auto' or 'manual'

        Returns:
            {
                'success': True,
                'snapshot_id': int,
                'learnings_captured': int,
                'messages_processed': int
            }

        Raises:
            Exception: On any processing error
        """
        # Read transcript
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        with open(transcript_path) as f:
            transcript = f.read()

        # Extract learnings and metadata
        extraction_result = self.extractor.extract_from_transcript(
            transcript,
            context_id=context_id
        )

        learnings = extraction_result['learnings']
        metadata = extraction_result['metadata']

        # Save learnings to PAI v2 patterns database
        try:
            pattern_ids = self.pai_v2_bridge.save_learnings_as_patterns(
                learnings=learnings,
                context_id=context_id,
                session_id=None,  # Session ID not available in hook context
                domain=None  # Could be inferred from agent_used if available
            )
        except Exception as e:
            # Don't fail hook on PAI v2 error - log and continue
            self._log_error(f"PAI v2 integration failed: {e}")
            pattern_ids = []

        # Prepare archive metadata
        archive_metadata = {
            'learning_count': len(learnings),
            'learning_ids': pattern_ids,  # PAI v2 pattern IDs for cross-reference
            'tool_usage': metadata['tool_usage'],
            'agents_used': metadata['agents_used'],
            'error_count': metadata['error_count'],
            'topics': self._extract_topics(learnings)
        }

        # Archive conversation
        snapshot_id = self.archive.archive_conversation(
            context_id=context_id,
            full_conversation=transcript,
            trigger_type=trigger_type,
            transcript_path=str(transcript_path),
            metadata=archive_metadata
        )

        # Phase 264: Auto-save durable checkpoint for post-compaction resume
        self._save_pre_compaction_checkpoint(context_id)

        return {
            'success': True,
            'snapshot_id': snapshot_id,
            'learnings_captured': len(learnings),
            'messages_processed': metadata['message_count']
        }

    def _save_pre_compaction_checkpoint(self, context_id: str):
        """
        Auto-save durable checkpoint before compaction.

        Phase 264: Ensures checkpoint is saved for post-compaction resume.
        FAILS LOUDLY if checkpoint cannot be saved - silent failure leads to
        hours of lost context and degraded code quality.

        Args:
            context_id: Claude context window ID

        Raises:
            Exception: Re-raises if checkpoint save fails (no graceful degradation)
        """
        # Gather current project state
        state = self.checkpoint_generator.gather_state()

        # Set auto-detected phase info
        state.phase_name = "Pre-compaction auto-checkpoint"
        state.percent_complete = 50  # Unknown, assume mid-project
        state.tdd_phase = "P4"  # Default to implementation phase

        # Save durable checkpoint - MUST succeed
        result = self.checkpoint_generator.save_durable_checkpoint(state)

        if result:
            self._log_debug(f"Pre-compaction checkpoint saved: {result}")
        else:
            # Checkpoint save returned None - this is a failure
            error_msg = "CRITICAL: Pre-compaction checkpoint save failed! Context will be lost after compaction."
            self._log_error(error_msg)
            # Print to stderr so it's visible
            import sys
            print(f"\n{'='*60}", file=sys.stderr)
            print("WARNING: CHECKPOINT SAVE FAILED", file=sys.stderr)
            print("Context may be lost after compaction!", file=sys.stderr)
            print(f"Run '/checkpoint' manually before proceeding.", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)
            raise RuntimeError(error_msg)

    def _extract_topics(self, learnings: list) -> list:
        """
        Extract topic keywords from learnings.

        Simple keyword extraction - can be enhanced later with NLP.

        Args:
            learnings: List of learning dictionaries

        Returns:
            List of topic keywords
        """
        topics = set()
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

        for learning in learnings:
            content = learning.get('content', '').lower()
            # Simple word extraction
            words = content.split()
            for word in words:
                # Remove punctuation
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 3 and word not in common_words:
                    topics.add(word)

        return list(topics)[:10]  # Top 10 topics

    def _log_metric(
        self,
        context_id: str,
        trigger_type: str,
        execution_time_ms: int,
        success: bool,
        snapshot_id: Optional[int] = None,
        learnings_captured: int = 0,
        messages_processed: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Log compaction metrics to database.

        Args:
            context_id: Claude context window ID
            trigger_type: 'auto' or 'manual'
            execution_time_ms: Hook execution time
            success: Whether hook succeeded
            snapshot_id: Archive snapshot ID (if successful)
            learnings_captured: Number of learnings extracted
            messages_processed: Number of messages processed
            error_message: Error details (if failed)
        """
        try:
            self.archive.log_compaction_metric(
                context_id=context_id,
                trigger_type=trigger_type,
                execution_time_ms=execution_time_ms,
                messages_processed=messages_processed,
                learnings_extracted=learnings_captured,
                success=success,
                snapshot_id=snapshot_id,
                error_message=error_message
            )
        except Exception as e:
            # Don't fail hook on metrics logging error
            self._log_error(f"Failed to log metric: {e}")

    def _log_error(self, message: str):
        """Log error message."""
        try:
            timestamp = datetime.now().isoformat()
            with open(self.error_log, 'a') as f:
                f.write(f"{timestamp} [ERROR] {message}\n")
        except Exception:
            pass  # Never fail on logging

    def _log_debug(self, message: str):
        """Log debug message."""
        try:
            timestamp = datetime.now().isoformat()
            with open(self.debug_log, 'a') as f:
                f.write(f"{timestamp} [DEBUG] {message}\n")
        except Exception:
            pass  # Never fail on logging


def main():
    """
    Main entry point for hook.

    Reads hook input from stdin, processes, and exits silently.
    """
    try:
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)

        # Process hook
        hook = PreCompactionHook()
        result = hook.process(hook_input)

        # Silent exit on success
        # (Claude Code proceeds with compaction)
        sys.exit(0 if result['success'] else 0)  # Always exit 0 (graceful degradation)

    except Exception as e:
        # Emergency error logging
        try:
            log_dir = Path.home() / ".maia" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            error_log = log_dir / "pre_compaction_errors.log"

            with open(error_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()} [CRITICAL] Hook crashed: {type(e).__name__}: {e}\n")
        except Exception:
            pass

        # Never block compaction - exit cleanly
        sys.exit(0)


if __name__ == "__main__":
    main()
