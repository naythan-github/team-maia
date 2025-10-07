#!/usr/bin/env python3
"""
Intelligent Downloads Router - Smart File Organization
Monitors Downloads folder and intelligently routes files based on type, content, and context
Replaces simple VTT-only mover with comprehensive file classification

Author: Maia Personal Assistant Agent
Phase: 92 - Intelligent File Management
Date: 2025-10-07
"""

import os
import sys
import time
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import json
from typing import Dict, Optional, List

# Configure logging
LOG_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "intelligent_downloads_router.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DOWNLOADS_DIR = Path.home() / "Downloads"
PROCESSED_TRACKER = Path.home() / "git" / "maia" / "claude" / "data" / "downloads_processed.json"

# Routing rules configuration
ROUTING_RULES = {
    # Meeting transcripts
    "vtt": {
        "destination": Path.home() / "Documents" / "VTT",
        "action": "move",
        "trigger_pipeline": "vtt_intelligence",
        "description": "Meeting transcript files"
    },

    # Data files
    "csv": {
        "destination": Path.home() / "Documents" / "Data",
        "action": "move",
        "subfolder_by": "date",  # Create YYYY-MM subfolders
        "description": "CSV data exports"
    },
    "xlsx": {
        "destination": Path.home() / "Documents" / "Data",
        "action": "move",
        "subfolder_by": "date",
        "description": "Excel spreadsheets"
    },
    "json": {
        "destination": Path.home() / "Documents" / "Data",
        "action": "move",
        "subfolder_by": "date",
        "description": "JSON data files"
    },

    # Documents
    "pdf": {
        "destination": Path.home() / "Documents" / "PDFs",
        "action": "move",
        "subfolder_by": "date",
        "description": "PDF documents"
    },
    "md": {
        "destination": Path.home() / "Documents" / "Markdown",
        "action": "move",
        "description": "Markdown documents"
    },

    # Archives
    "zip": {
        "destination": Path.home() / "Documents" / "Archives",
        "action": "move",
        "description": "ZIP archives"
    },
    "gz": {
        "destination": Path.home() / "Documents" / "Archives",
        "action": "move",
        "description": "Gzip archives"
    },
    "tar": {
        "destination": Path.home() / "Documents" / "Archives",
        "action": "move",
        "description": "TAR archives"
    },

    # Installers (keep in Downloads)
    "dmg": {
        "action": "keep",
        "description": "macOS disk images - kept in Downloads"
    },
    "pkg": {
        "action": "keep",
        "description": "macOS packages - kept in Downloads"
    },

    # Images
    "png": {
        "destination": Path.home() / "Pictures" / "Downloads",
        "action": "move",
        "description": "PNG images"
    },
    "jpg": {
        "destination": Path.home() / "Pictures" / "Downloads",
        "action": "move",
        "description": "JPEG images"
    },
    "jpeg": {
        "destination": Path.home() / "Pictures" / "Downloads",
        "action": "move",
        "description": "JPEG images"
    },

    # Code
    "py": {
        "destination": Path.home() / "Documents" / "Code",
        "action": "move",
        "description": "Python scripts"
    },
    "js": {
        "destination": Path.home() / "Documents" / "Code",
        "action": "move",
        "description": "JavaScript files"
    },
}


class IntelligentDownloadsRouter(FileSystemEventHandler):
    """Intelligent file router with classification and context-aware routing"""

    def __init__(self):
        self.processed_files = self._load_processed_files()
        self._ensure_destinations()

    def _load_processed_files(self) -> set:
        """Load list of already processed files"""
        if PROCESSED_TRACKER.exists():
            try:
                with open(PROCESSED_TRACKER, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed', []))
            except Exception as e:
                logger.error(f"Failed to load processed files tracker: {e}")
                return set()
        return set()

    def _save_processed_file(self, file_path: str, action: str, destination: Optional[str] = None):
        """Mark file as processed"""
        self.processed_files.add(file_path)

        # Load existing data
        data = {"processed": [], "history": []}
        if PROCESSED_TRACKER.exists():
            try:
                with open(PROCESSED_TRACKER, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass

        # Update
        data['processed'] = list(self.processed_files)
        data.setdefault('history', []).append({
            "file": file_path,
            "action": action,
            "destination": destination,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 1000 history entries
        data['history'] = data['history'][-1000:]

        try:
            with open(PROCESSED_TRACKER, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed file tracker: {e}")

    def _ensure_destinations(self):
        """Ensure all destination directories exist"""
        for rule in ROUTING_RULES.values():
            if rule['action'] == 'move' and 'destination' in rule:
                rule['destination'].mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip already processed
        if str(file_path) in self.processed_files:
            return

        # Wait for file to be fully downloaded
        time.sleep(2)

        if file_path.exists():
            logger.info(f"New file detected: {file_path.name}")
            self.route_file(file_path)

    def on_modified(self, event):
        """Handle file modifications (download completion)"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip already processed
        if str(file_path) in self.processed_files:
            return

        # Skip partial downloads
        if any(partial in file_path.name.lower() for partial in ['.download', '.crdownload', '.part']):
            return

        # Wait for download completion
        time.sleep(2)

        if not file_path.exists():
            return

        logger.info(f"File download completed: {file_path.name}")
        self.route_file(file_path)

    def route_file(self, file_path: Path):
        """Intelligently route file based on type and content"""
        try:
            if not file_path.exists():
                logger.warning(f"File no longer exists: {file_path.name}")
                return

            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.warning(f"File is empty, skipping: {file_path.name}")
                return

            # Get file extension
            extension = file_path.suffix.lstrip('.').lower()

            # Get routing rule
            rule = ROUTING_RULES.get(extension)

            if not rule:
                logger.info(f"No routing rule for .{extension} files, keeping in Downloads: {file_path.name}")
                self._save_processed_file(str(file_path), "keep", str(file_path))
                return

            # Execute routing action
            if rule['action'] == 'keep':
                logger.info(f"📌 Keeping in Downloads: {file_path.name} ({rule['description']})")
                self._save_processed_file(str(file_path), "keep", str(file_path))

            elif rule['action'] == 'move':
                destination = self._get_destination(file_path, rule)
                self._move_file(file_path, destination, rule)

                # Trigger pipeline if specified
                if 'trigger_pipeline' in rule:
                    self._trigger_pipeline(rule['trigger_pipeline'], destination)

        except Exception as e:
            logger.error(f"Failed to route {file_path.name}: {e}", exc_info=True)

    def _get_destination(self, file_path: Path, rule: Dict) -> Path:
        """Calculate destination path based on rule"""
        base_destination = rule['destination']

        # Apply subfolder logic
        if rule.get('subfolder_by') == 'date':
            # Create YYYY-MM subfolder
            subfolder = datetime.now().strftime("%Y-%m")
            destination_dir = base_destination / subfolder
            destination_dir.mkdir(parents=True, exist_ok=True)
        else:
            destination_dir = base_destination

        # Calculate final destination with duplicate handling
        destination = destination_dir / file_path.name
        counter = 1
        while destination.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            destination = destination_dir / f"{stem} ({counter}){suffix}"
            counter += 1

        return destination

    def _move_file(self, source: Path, destination: Path, rule: Dict):
        """Move file to destination"""
        try:
            logger.info(f"📦 Moving: {source.name} → {destination.parent.name}/{destination.name}")
            logger.info(f"   Reason: {rule['description']}")

            shutil.move(str(source), str(destination))

            self._save_processed_file(str(source), "move", str(destination))

            logger.info(f"✅ Successfully moved: {destination}")

            # Send notification
            self._send_notification(source.name, destination, rule['description'])

        except Exception as e:
            logger.error(f"Failed to move {source.name}: {e}", exc_info=True)

    def _trigger_pipeline(self, pipeline_name: str, file_path: Path):
        """Trigger processing pipeline for specific file types"""
        logger.info(f"🚀 Triggering pipeline: {pipeline_name} for {file_path.name}")

        if pipeline_name == "vtt_intelligence":
            # VTT intelligence pipeline is already triggered by vtt_watcher
            # Just log that it will be picked up
            logger.info(f"   VTT intelligence pipeline will process this file automatically")

    def _send_notification(self, filename: str, destination: Path, description: str):
        """Send macOS notification"""
        try:
            import subprocess
            subprocess.run([
                'osascript', '-e',
                f'display notification "{description}" with title "File Organized" subtitle "{filename}"'
            ], check=False, capture_output=True)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")


def scan_existing_files(handler: IntelligentDownloadsRouter):
    """Scan Downloads for existing files and route them"""
    logger.info("🔍 Scanning Downloads for existing files...")

    # Get all files in Downloads
    all_files = [f for f in DOWNLOADS_DIR.iterdir() if f.is_file()]

    if not all_files:
        logger.info("No files found in Downloads")
        return

    logger.info(f"Found {len(all_files)} file(s) in Downloads")

    # Group by extension
    by_extension = {}
    for file in all_files:
        ext = file.suffix.lstrip('.').lower()
        by_extension.setdefault(ext, []).append(file)

    logger.info(f"File types: {', '.join(f'.{ext} ({len(files)})' for ext, files in by_extension.items())}")

    # Route each file
    for file in all_files:
        if str(file) not in handler.processed_files:
            logger.info(f"Processing existing file: {file.name}")
            handler.route_file(file)
        else:
            logger.debug(f"Skipping already processed: {file.name}")


def main():
    """Main entry point"""
    logger.info("="*70)
    logger.info("🤖 Starting Intelligent Downloads Router")
    logger.info("="*70)
    logger.info(f"Monitoring: {DOWNLOADS_DIR}")
    logger.info(f"Routing rules loaded: {len(ROUTING_RULES)} file types")

    # Show routing summary
    logger.info("\n📋 Routing Configuration:")
    for ext, rule in sorted(ROUTING_RULES.items()):
        if rule['action'] == 'move':
            logger.info(f"  .{ext:6s} → {rule['destination']} ({rule['description']})")
        else:
            logger.info(f"  .{ext:6s} → KEEP in Downloads ({rule['description']})")

    logger.info("")

    # Check directories exist
    if not DOWNLOADS_DIR.exists():
        logger.error(f"Downloads directory does not exist: {DOWNLOADS_DIR}")
        sys.exit(1)

    # Create event handler and observer
    event_handler = IntelligentDownloadsRouter()
    observer = Observer()
    observer.schedule(event_handler, str(DOWNLOADS_DIR), recursive=False)

    # Scan and route any existing files
    scan_existing_files(event_handler)

    # Start watching
    observer.start()
    logger.info("✅ Intelligent Downloads Router is running (Press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Intelligent Downloads Router...")
        observer.stop()

    observer.join()
    logger.info("Intelligent Downloads Router stopped")


if __name__ == "__main__":
    main()
