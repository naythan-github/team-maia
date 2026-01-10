#!/usr/bin/env python3
"""
Continuous Capture Daemon for PAI Learning

Orchestrates continuous learning capture by polling Claude projects
every 2-3 minutes. Survives context compactions by using file-based
queue and high-water mark tracking.

Architecture:
1. Scan all active Claude projects (~/.claude/projects/*/transcript.jsonl)
2. For each project:
   - Load state (high-water mark)
   - Count messages, detect compaction
   - Extract learnings from new messages only
   - Write to queue file
   - Update high-water mark
3. Sleep configured interval
4. Repeat

Features:
- Graceful error handling (per-project failures don't stop daemon)
- Clean shutdown (signal handling)
- Configurable scan interval
- Integration with all Phase 1-5 components
"""

# Add MAIA_ROOT to sys.path for imports (LaunchAgent compatibility)
import sys
from pathlib import Path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
if str(MAIA_ROOT) not in sys.path:
    sys.path.insert(0, str(MAIA_ROOT))

import time
import logging
import signal
import threading
from typing import Optional, List, Dict, Any

from claude.tools.learning.continuous_capture.state_manager import CaptureStateManager
from claude.tools.learning.continuous_capture.incremental_extractor import IncrementalExtractor
from claude.tools.learning.continuous_capture.queue_writer import QueueWriter


class ContinuousCaptureDaemon:
    """
    Background daemon that continuously captures learnings from Claude projects.

    Polls projects at regular intervals, extracts learnings incrementally,
    and writes to queue files for async processing.
    """

    def __init__(
        self,
        projects_dir: Optional[Path] = None,
        queue_dir: Optional[Path] = None,
        state_dir: Optional[Path] = None,
        scan_interval: float = 180.0,  # 3 minutes default
        log_file: Optional[Path] = None
    ):
        """
        Initialize continuous capture daemon.

        Args:
            projects_dir: Directory containing Claude projects (default: ~/.claude/projects/)
            queue_dir: Directory for queue files (default: ~/.maia/learning_queue/)
            state_dir: Directory for state files (default: ~/.maia/capture_state/)
            scan_interval: Seconds between scans (default: 180 = 3 minutes)
            log_file: Optional log file path
        """
        # Paths
        self.projects_dir = projects_dir or Path.home() / '.claude' / 'projects'

        # Initialize component directories (set defaults if not provided)
        if queue_dir is None:
            self.queue_dir = Path.home() / '.maia' / 'learning_queue'
        else:
            self.queue_dir = queue_dir

        if state_dir is None:
            self.state_dir = Path.home() / '.maia' / 'capture_state'
        else:
            self.state_dir = state_dir

        self.scan_interval = scan_interval

        # State (thread-safe)
        self.shutdown_requested = False
        self.cycles_completed = 0
        self._cycles_lock = threading.Lock()  # Protect cycles_completed

        # Initialize components
        self.state_manager = CaptureStateManager(state_dir=self.state_dir)
        self.extractor = IncrementalExtractor()
        self.queue_writer = QueueWriter(queue_dir=self.queue_dir)

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)

        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (signal-safe)."""
        # Note: Avoid logging here (not signal-safe). Set flag only.
        self.shutdown_requested = True

    def scan_projects(self) -> List[Dict[str, Any]]:
        """
        Scan projects directory for active Claude projects.

        Returns:
            List of project metadata dicts with context_id and transcript_path
        """
        projects = []

        if not self.projects_dir.exists():
            self.logger.warning(f"Projects directory not found: {self.projects_dir}")
            return projects

        # Find all .jsonl transcript files in project directories
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Look for .jsonl files (UUID-named transcripts)
            transcript_files = list(project_dir.glob('*.jsonl'))
            if not transcript_files:
                continue

            # Use the most recently modified transcript if multiple exist
            transcript_path = max(transcript_files, key=lambda p: p.stat().st_mtime)

            # Extract context ID from directory name
            context_id = project_dir.name

            projects.append({
                'context_id': context_id,
                'transcript_path': transcript_path,
                'project_dir': project_dir
            })

        return projects

    def capture_cycle(self):
        """
        Execute one complete capture cycle across all projects.

        For each project:
        1. Load state (high-water mark)
        2. Count messages
        3. Detect compaction
        4. Extract learnings from new messages
        5. Write to queue
        6. Update state
        """
        try:
            projects = self.scan_projects()

            if not projects:
                self.logger.debug("No active projects found")
                return

            self.logger.info(f"Scanning {len(projects)} projects...")

            for project in projects:
                try:
                    self._process_project(project)
                except Exception as e:
                    # Per-project errors should not crash daemon
                    self.logger.error(
                        f"Error processing project {project['context_id']}: {e}",
                        exc_info=True
                    )
                    continue
        finally:
            # Always increment cycle count, even if no projects or errors (thread-safe)
            with self._cycles_lock:
                self.cycles_completed += 1

    def _process_project(self, project: Dict[str, Any]):
        """
        Process a single project: load state, extract, queue, update.

        Args:
            project: Project metadata dict
        """
        context_id = project['context_id']
        transcript_path = project['transcript_path']

        # Load current state
        state = self.state_manager.load_state(context_id)

        # Count current messages
        current_count = self._count_messages(transcript_path)

        if current_count == 0:
            self.logger.debug(f"Project {context_id} has no messages, skipping")
            return

        # Detect compaction
        compaction_detected = False
        if state['last_message_count'] > 0 and current_count < state['last_message_count']:
            self.logger.info(
                f"Compaction detected in {context_id}: "
                f"{state['last_message_count']} → {current_count} messages"
            )
            compaction_detected = True
            state['compaction_count'] += 1
            state['last_message_index'] = 0  # Reset high-water mark

        # Check if there are new messages to process
        if not compaction_detected and current_count <= state['last_message_index']:
            self.logger.debug(f"No new messages in {context_id}")
            return

        # Extract learnings from new messages
        learnings = self.extractor.extract_from_transcript(
            transcript_path=transcript_path,
            start_index=state['last_message_index'],
            end_index=current_count
        )

        # Write to queue if learnings extracted
        if learnings:
            self.logger.info(
                f"Extracted {len(learnings)} learnings from {context_id} "
                f"(messages {state['last_message_index']}→{current_count})"
            )

            self.queue_writer.write_queue_file(
                context_id=context_id,
                learnings=learnings,
                metadata={
                    'compaction_number': state['compaction_count'],
                    'message_range': [state['last_message_index'], current_count]
                }
            )
        else:
            self.logger.debug(f"No learnings extracted from {context_id}")

        # Update state
        state['last_message_index'] = current_count
        state['last_message_count'] = current_count

        # Save state (unpack dict to parameters)
        self.state_manager.save_state(
            context_id=context_id,
            last_message_index=state['last_message_index'],
            last_message_count=state['last_message_count'],
            compaction_count=state['compaction_count']
        )

    def _count_messages(self, transcript_path: Path) -> int:
        """
        Count messages in transcript file.

        Args:
            transcript_path: Path to transcript.jsonl

        Returns:
            Number of messages
        """
        if not transcript_path.exists():
            return 0

        count = 0
        try:
            with open(transcript_path, 'r') as f:
                for line in f:
                    if line.strip():  # Non-empty line
                        count += 1
        except Exception as e:
            self.logger.error(f"Error counting messages in {transcript_path}: {e}")
            return 0

        return count

    def run(self):
        """
        Main daemon loop: capture cycle → sleep → repeat.

        Runs until shutdown_requested is set.
        """
        self.logger.info(
            f"Continuous capture daemon starting (interval: {self.scan_interval}s)"
        )

        try:
            while not self.shutdown_requested:
                try:
                    self.capture_cycle()
                except Exception as e:
                    # Capture cycle errors should not crash daemon
                    self.logger.error(f"Error in capture cycle: {e}", exc_info=True)

                # Sleep with early-exit on shutdown
                for _ in range(int(self.scan_interval * 10)):
                    if self.shutdown_requested:
                        break
                    time.sleep(0.1)
        finally:
            self.logger.info("Continuous capture daemon stopped")

    def stop(self):
        """Request daemon shutdown and cleanup resources."""
        self.shutdown_requested = True

        # Close logging handlers to release file descriptors
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
