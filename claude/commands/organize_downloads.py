#!/usr/bin/env python3
"""
Organize Downloads - Manual trigger for intelligent file organization
Run this command to organize files in your Downloads folder
"""

from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path.home() / 'git' / 'maia'))
from claude.tools.intelligent_downloads_router import IntelligentDownloadsRouter

def main():
    router = IntelligentDownloadsRouter()
    downloads = Path.home() / 'Downloads'

    print("🔍 Scanning Downloads folder...\n")

    # Get all processable files
    files_by_type = {}
    for file in downloads.glob('*'):
        if file.is_file() and not file.name.startswith('.'):
            ext = file.suffix.lstrip('.').lower()
            files_by_type.setdefault(ext, []).append(file)

    if not files_by_type:
        print("✅ No files to organize")
        return

    print(f"📋 Found files: {', '.join(f'.{ext} ({len(files)})' for ext, files in files_by_type.items())}\n")

    # Process each file
    moved_count = 0
    kept_count = 0

    for files in files_by_type.values():
        for file in files:
            # Check if already processed
            if str(file) in router.processed_files:
                continue

            # Route the file
            router.route_file(file)

            # Check if it was moved
            if not file.exists():
                moved_count += 1
            else:
                kept_count += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Organized: {moved_count} files")
    print(f"   📌 Kept in Downloads: {kept_count} files")

if __name__ == "__main__":
    main()
