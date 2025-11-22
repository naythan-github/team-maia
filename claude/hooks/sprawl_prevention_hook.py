#!/usr/bin/env python3
"""
Sprawl Prevention Hook - Phase 2 Component
Integrates with existing hook system for real-time prevention
"""

import os
import sys
from pathlib import Path

# Add governance tools to path
sys.path.append(str(Path(__file__).resolve().parents[4 if 'claude/tools' in str(__file__) else 0] / 'claude' / 'tools' / 'governance'))

try:
    from filesystem_monitor import FileSystemMonitor
except ImportError:
    print("⚠️  Governance system not installed - skipping sprawl prevention")
    sys.exit(0)

def check_commit_for_sprawl():
    """Check staged files for sprawl violations"""
    print("🔍 SPRAWL PREVENTION CHECK...")
    
    monitor = FileSystemMonitor()
    
    # For now, just run a quick validation check
    # In full implementation, this would integrate with git to check staged files
    violations_found = False
    violation_details = []
    
    # Quick check for common violations in root directory
    repo_path = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
    root_files = [f for f in repo_path.iterdir() if f.is_file()]
    
    # Check for forbidden extensions in root
    forbidden_extensions = [".tmp", ".log", ".backup"]
    for file in root_files:
        if file.suffix in forbidden_extensions:
            violations_found = True
            violation_details.append({
                "file": file.name,
                "message": f"Forbidden extension {file.suffix} in root directory"
            })
    
    # Check root file count
    if len(root_files) > 20:
        violations_found = True
        violation_details.append({
            "file": "root directory",
            "message": f"Too many files in root ({len(root_files)} > 20)"
        })
    
    if violations_found:
        print("🚨 SPRAWL PREVENTION VIOLATIONS DETECTED:")
        for violation in violation_details:
            print(f"   📄 {violation['file']}: {violation['message']}")
        print("")
        print("❌ COMMIT BLOCKED - Fix violations before committing")
        return False
    else:
        print("✅ No sprawl violations detected")
        return True

def main():
    """Main hook function"""
    if not check_commit_for_sprawl():
        sys.exit(1)  # Block commit
    
    sys.exit(0)  # Allow commit

if __name__ == "__main__":
    main()