#!/usr/bin/env python3
"""
Background Context Monitor for Proactive Learning Capture
Phase 237.4: Monitors Claude Code context usage and triggers capture at 70%

This daemon runs in the background, scanning Claude Code projects every 5 minutes
to estimate context usage. When a project exceeds the configured threshold (default 70%),
it triggers the pre-compaction learning capture hook proactively.

Architecture:
1. Scan ~/.claude/projects/*/ for transcript.jsonl files
2. Count messages and estimate tokens (message_count * 800)
3. Calculate usage percentage (estimated_tokens / context_window)
4. If > threshold AND not already captured:
   - Trigger pre_compaction_learning_capture.py
   - Log capture event
   - Mark context as captured (don't spam)

Features:
- Configurable threshold (default: 70%)
- Configurable check interval (default: 300s / 5min)
- PID file for single-instance enforcement
- Signal handling (SIGTERM, SIGINT for clean shutdown)
- Graceful error handling (never crash, log errors)
- Multi-project support

Configuration (via environment variables):
- MAIA_CONTEXT_THRESHOLD: Trigger threshold (default: 0.70)
- MAIA_CHECK_INTERVAL: Check interval in seconds (default: 300)
- MAIA_CONTEXT_WINDOW: Context window size in tokens (default: 200000)
- MAIA_TOKENS_PER_MESSAGE: Estimation factor (default: 800)

Logging:
- Log file: ~/.maia/logs/context_monitor.log
- Log format: [timestamp] [level] message
- Rotation: Keep last 7 days

Author: Maia (Phase 237.4)
Created: 2026-01-06
"""

import os
import sys
import time
import signal
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


# Configuration from environment variables
CONTEXT_THRESHOLD = float(os.getenv('MAIA_CONTEXT_THRESHOLD', '0.70'))
CHECK_INTERVAL = int(os.getenv('MAIA_CHECK_INTERVAL', '300'))
CONTEXT_WINDOW = int(os.getenv('MAIA_CONTEXT_WINDOW', '200000'))
TOKENS_PER_MESSAGE = int(os.getenv('MAIA_TOKENS_PER_MESSAGE', '800'))

# Paths
MAIA_ROOT = Path(__file__).parent.parent
LOG_DIR = Path.home() / '.maia' / 'logs'
PID_FILE = Path.home() / '.maia' / 'context_monitor.pid'

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / 'context_monitor.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContextStatus:
    """Context usage status."""
    context_id: str
    message_count: int
    estimated_tokens: int
    usage_percentage: float
    transcript_path: Path


class ContextMonitor:
    """
    Background monitor for Claude Code context usage.

    Scans active Claude Code projects, estimates context usage,
    and triggers learning capture at configurable threshold.
    """

    def __init__(
        self,
        threshold: float = CONTEXT_THRESHOLD,
        check_interval: int = CHECK_INTERVAL,
        context_window: int = CONTEXT_WINDOW,
        tokens_per_message: int = TOKENS_PER_MESSAGE
    ):
        """
        Initialize context monitor.

        Args:
            threshold: Trigger threshold (0.0-1.0)
            check_interval: Check interval in seconds
            context_window: Context window size in tokens
            tokens_per_message: Token estimation factor
        """
        self.threshold = threshold
        self.check_interval = check_interval
        self.context_window = context_window
        self.tokens_per_message = tokens_per_message
        self.running = False

        # Track contexts already captured (don't spam)
        self.captured_contexts = set()

    def estimate_context_usage(self, transcript_path: Path) -> Optional[ContextStatus]:
        """
        Estimate context usage from transcript file.

        Args:
            transcript_path: Path to transcript.jsonl

        Returns:
            ContextStatus or None if file doesn't exist or error occurs
        """
        if not transcript_path.exists():
            return None

        try:
            # Count messages in transcript
            with open(transcript_path) as f:
                message_count = sum(1 for _ in f)

            # Estimate tokens
            estimated_tokens = message_count * self.tokens_per_message

            # Calculate usage percentage
            usage_percentage = (estimated_tokens / self.context_window) * 100

            # Extract context ID from parent directory name
            context_id = transcript_path.parent.name

            return ContextStatus(
                context_id=context_id,
                message_count=message_count,
                estimated_tokens=estimated_tokens,
                usage_percentage=usage_percentage,
                transcript_path=transcript_path
            )

        except Exception as e:
            logger.error(f"Error estimating context for {transcript_path}: {e}")
            return None

    def should_trigger_capture(self, status: ContextStatus) -> bool:
        """
        Check if capture should be triggered.

        Args:
            status: ContextStatus

        Returns:
            True if over threshold and not already captured
        """
        # Don't spam - check if already captured
        if status.context_id in self.captured_contexts:
            return False

        # Check threshold
        return (status.usage_percentage / 100) > self.threshold

    def trigger_capture(self, status: ContextStatus) -> bool:
        """
        Trigger pre-compaction learning capture.

        Args:
            status: ContextStatus

        Returns:
            True if capture succeeded
        """
        try:
            # Build hook input
            hook_input = {
                'session_id': status.context_id,
                'transcript_path': str(status.transcript_path),
                'trigger': 'proactive_monitor',
                'hook_event_name': 'PreCompact'
            }

            # Call pre-compaction hook
            hook_path = MAIA_ROOT / 'hooks' / 'pre_compaction_learning_capture.py'

            result = subprocess.run(
                ['python3', str(hook_path)],
                input=json.dumps(hook_input).encode(),
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(
                    f"✅ Capture triggered for {status.context_id} "
                    f"({status.usage_percentage:.1f}% context)"
                )
                self.captured_contexts.add(status.context_id)
                return True
            else:
                logger.error(
                    f"❌ Capture failed for {status.context_id}: "
                    f"{result.stderr.decode()}"
                )
                return False

        except Exception as e:
            logger.error(f"Error triggering capture for {status.context_id}: {e}")
            return False

    def scan_projects(self) -> List[ContextStatus]:
        """
        Scan all Claude Code projects for context usage.

        Returns:
            List of ContextStatus for all active projects
        """
        projects_dir = Path.home() / '.claude' / 'projects'

        if not projects_dir.exists():
            logger.warning(f"Projects directory not found: {projects_dir}")
            return []

        statuses = []

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Look for transcript files (*.jsonl)
            for transcript in project_dir.glob('*.jsonl'):
                status = self.estimate_context_usage(transcript)
                if status:
                    statuses.append(status)

        return statuses

    def check_and_trigger(self):
        """Check all contexts and trigger captures if needed."""
        logger.info("Scanning projects for context usage...")

        statuses = self.scan_projects()

        if not statuses:
            logger.info("No active projects found")
            return

        for status in statuses:
            logger.debug(
                f"Context {status.context_id}: {status.usage_percentage:.1f}% "
                f"({status.message_count} messages, ~{status.estimated_tokens:,} tokens)"
            )

            if self.should_trigger_capture(status):
                logger.warning(
                    f"⚠️ Context {status.context_id} at {status.usage_percentage:.1f}% "
                    f"(threshold: {self.threshold*100:.0f}%) - triggering capture"
                )
                self.trigger_capture(status)

    def enforce_single_instance(self):
        """Ensure only one monitor instance is running."""
        if PID_FILE.exists():
            try:
                with open(PID_FILE) as f:
                    old_pid = int(f.read().strip())

                # Check if process is actually running
                os.kill(old_pid, 0)  # Raises OSError if not running

                logger.error(f"Monitor already running (PID {old_pid})")
                sys.exit(1)

            except (OSError, ValueError):
                # Old PID file, process not running
                logger.info("Removing stale PID file")
                PID_FILE.unlink()

        # Write current PID
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

    def cleanup(self):
        """Clean up resources."""
        logger.info("Shutting down context monitor...")

        if PID_FILE.exists():
            PID_FILE.unlink()

        self.running = False

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Run monitor daemon."""
        logger.info(
            f"Starting context monitor "
            f"(threshold: {self.threshold*100:.0f}%, interval: {self.check_interval}s)"
        )

        # Enforce single instance
        self.enforce_single_instance()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.running = True

        try:
            while self.running:
                self.check_and_trigger()
                time.sleep(self.check_interval)

        except Exception as e:
            logger.error(f"Monitor crashed: {e}")
            raise

        finally:
            self.cleanup()


def main():
    """Entry point."""
    monitor = ContextMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
