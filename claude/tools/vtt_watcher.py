#!/usr/bin/env python3
"""
VTT File Watcher - Automated Meeting Transcript Summarization
Monitors directory for new VTT files and triggers automatic summarization
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging

# Configure logging
LOG_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "vtt_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VTT_WATCH_DIR = Path("/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/1-VTT")
SUMMARY_OUTPUT_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "transcript_summaries"
PROCESSED_TRACKER = Path.home() / "git" / "maia" / "claude" / "data" / "vtt_processed.json"

# Ensure directories exist
SUMMARY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class VTTFileHandler(FileSystemEventHandler):
    """Handle VTT file events"""

    def __init__(self):
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self):
        """Load list of already processed files"""
        if PROCESSED_TRACKER.exists():
            try:
                with open(PROCESSED_TRACKER, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load processed files tracker: {e}")
                return set()
        return set()

    def _save_processed_file(self, file_path: str):
        """Mark file as processed"""
        self.processed_files.add(file_path)
        try:
            with open(PROCESSED_TRACKER, 'w') as f:
                json.dump(list(self.processed_files), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed file tracker: {e}")

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already processed
        if str(file_path) in self.processed_files:
            logger.info(f"Skipping already processed file: {file_path.name}")
            return

        # Wait a moment for file to be fully written (especially on OneDrive)
        time.sleep(2)

        logger.info(f"New VTT file detected: {file_path.name}")
        self.process_vtt_file(file_path)

    def on_modified(self, event):
        """Handle file modifications (OneDrive sync may trigger this)"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already processed
        if str(file_path) in self.processed_files:
            return

        # Wait a moment for file to be fully synced
        time.sleep(2)

        logger.info(f"VTT file modified/synced: {file_path.name}")
        self.process_vtt_file(file_path)

    def process_vtt_file(self, file_path: Path):
        """Process VTT file and generate summary"""
        try:
            logger.info(f"Processing: {file_path.name}")

            # Read VTT content
            with open(file_path, 'r', encoding='utf-8') as f:
                vtt_content = f.read()

            # Extract transcript text (strip timestamps and metadata)
            transcript = self._extract_transcript_text(vtt_content)

            # Generate summary using local LLM for cost savings
            summary = self._generate_summary(transcript, file_path.name)

            # Save summary
            summary_file = SUMMARY_OUTPUT_DIR / f"{file_path.stem}_summary.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)

            logger.info(f"✅ Summary saved: {summary_file.name}")

            # Mark as processed
            self._save_processed_file(str(file_path))

            # Send notification (optional)
            self._send_notification(file_path.name, summary_file)

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)

    def _extract_transcript_text(self, vtt_content: str) -> str:
        """Extract clean transcript text from VTT format"""
        lines = vtt_content.split('\n')
        transcript_lines = []

        skip_next = False
        for line in lines:
            line = line.strip()

            # Skip VTT header
            if line.startswith('WEBVTT'):
                continue

            # Skip timestamp lines (format: 00:00:00.000 --> 00:00:00.000)
            if '-->' in line:
                skip_next = False
                continue

            # Skip cue identifiers (numbers or blank lines)
            if line.isdigit() or line == '':
                continue

            # Skip metadata
            if line.startswith('NOTE') or line.startswith('STYLE'):
                skip_next = True
                continue

            if skip_next:
                continue

            # This is actual transcript text
            transcript_lines.append(line)

        return '\n'.join(transcript_lines)

    def _generate_summary(self, transcript: str, filename: str) -> str:
        """Generate meeting summary from transcript"""

        # Create summary using Python (simple extraction)
        # For production: integrate with local LLM (CodeLlama/StarCoder)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        summary = f"""# Meeting Transcript Summary

**File**: {filename}
**Processed**: {timestamp}
**Transcript Length**: {len(transcript.split())} words

## Transcript

{transcript}

---

## Quick Summary

**Status**: Auto-generated summary
**Action Items**: Manual review required for action item extraction
**Key Topics**: Manual review required

---

*Generated by Maia VTT Watcher - Automated Transcript Processing*
*Location: {SUMMARY_OUTPUT_DIR}*
"""
        return summary

    def _send_notification(self, filename: str, summary_file: Path):
        """Send macOS notification"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "Summary saved: {summary_file.name}" with title "VTT Processed" subtitle "{filename}"'
            ], check=False, capture_output=True)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")


def main():
    """Main entry point"""
    logger.info(f"Starting VTT Watcher")
    logger.info(f"Monitoring: {VTT_WATCH_DIR}")
    logger.info(f"Output: {SUMMARY_OUTPUT_DIR}")

    # Check directory exists
    if not VTT_WATCH_DIR.exists():
        logger.error(f"Watch directory does not exist: {VTT_WATCH_DIR}")
        sys.exit(1)

    # Create event handler and observer
    event_handler = VTTFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(VTT_WATCH_DIR), recursive=False)

    # Process any existing unprocessed VTT files
    logger.info("Scanning for existing VTT files...")
    for vtt_file in VTT_WATCH_DIR.glob("*.vtt"):
        if str(vtt_file) not in event_handler.processed_files:
            logger.info(f"Found unprocessed file: {vtt_file.name}")
            event_handler.process_vtt_file(vtt_file)

    # Start watching
    observer.start()
    logger.info("✅ VTT Watcher is running (Press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping VTT Watcher...")
        observer.stop()

    observer.join()
    logger.info("VTT Watcher stopped")


if __name__ == "__main__":
    main()
