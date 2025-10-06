#!/usr/bin/env python3
"""
Downloads VTT File Mover - Automatic VTT File Transfer
Monitors Downloads folder for new VTT files and moves them to processing folder
Designed to run continuously via LaunchAgent
"""

import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import json

# Configure logging
LOG_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "downloads_vtt_mover.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DOWNLOADS_DIR = Path.home() / "Downloads"
VTT_DESTINATION = Path.home() / "Library" / "CloudStorage" / "OneDrive-ORROPTYLTD" / "Documents" / "1-VTT"
MOVED_TRACKER = Path.home() / "git" / "maia" / "claude" / "data" / "vtt_moved.json"

# Ensure destination exists
VTT_DESTINATION.mkdir(parents=True, exist_ok=True)


class DownloadsVTTHandler(FileSystemEventHandler):
    """Handle VTT file events in Downloads folder"""

    def __init__(self):
        self.moved_files = self._load_moved_files()

    def _load_moved_files(self):
        """Load list of already moved files"""
        if MOVED_TRACKER.exists():
            try:
                with open(MOVED_TRACKER, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load moved files tracker: {e}")
                return set()
        return set()

    def _save_moved_file(self, file_path: str):
        """Mark file as moved"""
        self.moved_files.add(file_path)
        try:
            with open(MOVED_TRACKER, 'w') as f:
                json.dump(list(self.moved_files), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save moved file tracker: {e}")

    def on_created(self, event):
        """Handle new file creation in Downloads"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already moved
        if str(file_path) in self.moved_files:
            logger.info(f"Skipping already moved file: {file_path.name}")
            return

        # Wait a moment for file to be fully downloaded
        time.sleep(3)

        logger.info(f"New VTT file detected in Downloads: {file_path.name}")
        self.move_vtt_file(file_path)

    def on_modified(self, event):
        """Handle file modifications (download completion)"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already moved
        if str(file_path) in self.moved_files:
            return

        # Skip .download or .crdownload files (Chrome partial downloads)
        if '.download' in file_path.name.lower() or '.crdownload' in file_path.name.lower():
            return

        # Wait a moment to ensure download complete
        time.sleep(3)

        # Check file still exists (wasn't moved already)
        if not file_path.exists():
            return

        logger.info(f"VTT file download completed: {file_path.name}")
        self.move_vtt_file(file_path)

    def move_vtt_file(self, file_path: Path):
        """Move VTT file from Downloads to processing folder"""
        try:
            if not file_path.exists():
                logger.warning(f"File no longer exists: {file_path.name}")
                return

            # Check file size to ensure download complete
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.warning(f"File is empty, skipping: {file_path.name}")
                return

            # Destination path
            destination = VTT_DESTINATION / file_path.name

            # Handle duplicate names
            counter = 1
            while destination.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                destination = VTT_DESTINATION / f"{stem} ({counter}){suffix}"
                counter += 1

            # Move file
            logger.info(f"Moving: {file_path.name} -> {destination.parent.name}/{destination.name}")
            shutil.move(str(file_path), str(destination))

            # Mark as moved
            self._save_moved_file(str(file_path))

            logger.info(f"✅ Successfully moved: {destination.name}")

            # Send notification
            self._send_notification(file_path.name, destination)

        except Exception as e:
            logger.error(f"Failed to move {file_path.name}: {e}", exc_info=True)

    def _send_notification(self, filename: str, destination: Path):
        """Send macOS notification"""
        try:
            import subprocess
            subprocess.run([
                'osascript', '-e',
                f'display notification "VTT file moved to processing folder" with title "VTT File Moved" subtitle "{filename}"'
            ], check=False, capture_output=True)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")


def scan_existing_files(handler: DownloadsVTTHandler):
    """Scan Downloads for existing VTT files and move them"""
    logger.info("Scanning Downloads for existing VTT files...")

    vtt_files = list(DOWNLOADS_DIR.glob("*.vtt"))

    if not vtt_files:
        logger.info("No VTT files found in Downloads")
        return

    logger.info(f"Found {len(vtt_files)} VTT file(s) in Downloads")

    for vtt_file in vtt_files:
        if str(vtt_file) not in handler.moved_files:
            logger.info(f"Moving existing file: {vtt_file.name}")
            handler.move_vtt_file(vtt_file)
        else:
            logger.info(f"Skipping already moved: {vtt_file.name}")


def main():
    """Main entry point"""
    logger.info(f"Starting Downloads VTT Mover")
    logger.info(f"Monitoring: {DOWNLOADS_DIR}")
    logger.info(f"Destination: {VTT_DESTINATION}")

    # Check directories exist
    if not DOWNLOADS_DIR.exists():
        logger.error(f"Downloads directory does not exist: {DOWNLOADS_DIR}")
        sys.exit(1)

    if not VTT_DESTINATION.exists():
        logger.error(f"VTT destination does not exist: {VTT_DESTINATION}")
        sys.exit(1)

    # Create event handler and observer
    event_handler = DownloadsVTTHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DOWNLOADS_DIR), recursive=False)

    # Scan and move any existing VTT files
    scan_existing_files(event_handler)

    # Start watching
    observer.start()
    logger.info("✅ Downloads VTT Mover is running (Press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Downloads VTT Mover...")
        observer.stop()

    observer.join()
    logger.info("Downloads VTT Mover stopped")


if __name__ == "__main__":
    main()
