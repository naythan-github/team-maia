#!/usr/bin/env python3
"""
UFC Compliance Checker - Phase 103 Week 3 Task 3

Validates Unified Filesystem-based Context (UFC) system compliance:
- Directory nesting depth (max 4-5 levels)
- File naming conventions (lowercase, underscores, descriptive)
- Required directory structure exists
- No context pollution in project repos

Usage:
    python3 claude/tools/security/ufc_compliance_checker.py --check
    python3 claude/tools/security/ufc_compliance_checker.py --check --verbose
    python3 claude/tools/security/ufc_compliance_checker.py --check --json report.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# UFC System Requirements (from claude/context/ufc_system.md)
REQUIRED_DIRECTORIES = [
    "claude/context/core",
    "claude/context/tools",
    "claude/context/knowledge",
    "claude/agents",
    "claude/commands",
    "claude/tools",
    "claude/hooks",
    "claude/data"
]

RECOMMENDED_DIRECTORIES = [
    "claude/context/projects",
    "claude/context/personal"
]

MAX_NESTING_DEPTH = 5  # claude/context/knowledge/domain/subdomain = 5 levels
PREFERRED_NESTING_DEPTH = 3  # claude/context/core = 3 levels

# File naming conventions
VALID_FILE_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-.")
DISCOURAGED_PATTERNS = ["temp", "test", "old", "backup", "copy"]


class UFCComplianceChecker:
    """Validates UFC system compliance"""

    def __init__(self, maia_root: Path, verbose: bool = False):
        self.maia_root = maia_root
        self.verbose = verbose
        self.violations = []
        self.warnings = []
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "max_depth_found": 0,
            "files_exceeding_preferred_depth": 0,
            "files_exceeding_max_depth": 0,
            "naming_violations": 0,
            "missing_required_dirs": 0,
            "missing_recommended_dirs": 0
        }

    def check_required_directories(self) -> bool:
        """Validate required UFC directories exist"""
        all_exist = True

        for required_dir in REQUIRED_DIRECTORIES:
            dir_path = self.maia_root / required_dir
            if not dir_path.exists():
                self.violations.append({
                    "type": "MISSING_REQUIRED_DIR",
                    "severity": "CRITICAL",
                    "path": required_dir,
                    "message": f"Required UFC directory missing: {required_dir}"
                })
                self.stats["missing_required_dirs"] += 1
                all_exist = False
            elif self.verbose:
                print(f"✅ Required directory exists: {required_dir}")

        for recommended_dir in RECOMMENDED_DIRECTORIES:
            dir_path = self.maia_root / recommended_dir
            if not dir_path.exists():
                self.warnings.append({
                    "type": "MISSING_RECOMMENDED_DIR",
                    "severity": "LOW",
                    "path": recommended_dir,
                    "message": f"Recommended UFC directory missing: {recommended_dir}"
                })
                self.stats["missing_recommended_dirs"] += 1

        return all_exist

    def get_nesting_depth(self, path: Path) -> int:
        """Calculate nesting depth from maia_root"""
        try:
            relative_path = path.relative_to(self.maia_root)
            return len(relative_path.parts)
        except ValueError:
            return 0

    def check_nesting_depth(self) -> bool:
        """Validate directory nesting doesn't exceed limits"""
        compliant = True
        claude_dir = self.maia_root / "claude"

        if not claude_dir.exists():
            self.violations.append({
                "type": "MISSING_CLAUDE_DIR",
                "severity": "CRITICAL",
                "path": "claude/",
                "message": "Claude directory not found - UFC system not initialized"
            })
            return False

        for root, dirs, files in os.walk(claude_dir):
            root_path = Path(root)
            depth = self.get_nesting_depth(root_path)

            self.stats["total_dirs"] += 1
            self.stats["max_depth_found"] = max(self.stats["max_depth_found"], depth)

            # Check files in this directory
            for file in files:
                file_path = root_path / file
                file_depth = self.get_nesting_depth(file_path)
                self.stats["total_files"] += 1

                if file_depth > MAX_NESTING_DEPTH:
                    self.violations.append({
                        "type": "EXCESSIVE_NESTING",
                        "severity": "HIGH",
                        "path": str(file_path.relative_to(self.maia_root)),
                        "depth": file_depth,
                        "message": f"File exceeds max nesting depth of {MAX_NESTING_DEPTH} (depth: {file_depth})"
                    })
                    self.stats["files_exceeding_max_depth"] += 1
                    compliant = False

                elif file_depth > PREFERRED_NESTING_DEPTH:
                    self.warnings.append({
                        "type": "DEEP_NESTING",
                        "severity": "LOW",
                        "path": str(file_path.relative_to(self.maia_root)),
                        "depth": file_depth,
                        "message": f"File exceeds preferred nesting depth of {PREFERRED_NESTING_DEPTH} (depth: {file_depth}) - acceptable for complex domains"
                    })
                    self.stats["files_exceeding_preferred_depth"] += 1

        return compliant

    def check_file_naming(self) -> bool:
        """Validate file naming conventions"""
        compliant = True
        claude_dir = self.maia_root / "claude"

        if not claude_dir.exists():
            return False

        for root, dirs, files in os.walk(claude_dir):
            root_path = Path(root)

            for file in files:
                # Skip hidden files and special files
                if file.startswith('.') or file == '__init__.py':
                    continue

                file_path = root_path / file
                relative_path = str(file_path.relative_to(self.maia_root))

                # Check for uppercase letters
                if any(c.isupper() for c in file):
                    self.warnings.append({
                        "type": "UPPERCASE_FILENAME",
                        "severity": "LOW",
                        "path": relative_path,
                        "message": f"File uses uppercase (prefer lowercase): {file}"
                    })
                    self.stats["naming_violations"] += 1

                # Check for invalid characters
                filename_lower = file.lower()
                invalid_chars = set(filename_lower) - VALID_FILE_CHARS
                if invalid_chars:
                    self.violations.append({
                        "type": "INVALID_FILENAME_CHARS",
                        "severity": "MEDIUM",
                        "path": relative_path,
                        "chars": list(invalid_chars),
                        "message": f"File contains invalid characters: {invalid_chars}"
                    })
                    self.stats["naming_violations"] += 1
                    compliant = False

                # Check for discouraged patterns
                for pattern in DISCOURAGED_PATTERNS:
                    if pattern in filename_lower and not file.endswith('.md'):
                        self.warnings.append({
                            "type": "DISCOURAGED_PATTERN",
                            "severity": "LOW",
                            "path": relative_path,
                            "pattern": pattern,
                            "message": f"File contains discouraged pattern '{pattern}': {file}"
                        })

        return compliant

    def check_context_pollution(self) -> bool:
        """Check for UFC files in project repos (outside claude/)"""
        compliant = True

        # Look for .md files in project root that might be UFC pollution
        for item in self.maia_root.iterdir():
            if item.is_file() and item.suffix == '.md' and item.name not in ['README.md', 'LICENSE.md', 'CHANGELOG.md']:
                # Check if it looks like UFC content
                try:
                    content = item.read_text()
                    if any(keyword in content.lower() for keyword in ['context', 'ufc', 'claude', 'agent']):
                        self.warnings.append({
                            "type": "POSSIBLE_CONTEXT_POLLUTION",
                            "severity": "LOW",
                            "path": item.name,
                            "message": f"Possible UFC file in project root: {item.name} (should be in claude/context/)"
                        })
                except Exception:
                    pass

        return compliant

    def run_compliance_check(self) -> Dict:
        """Run all compliance checks"""
        print("🔍 Running UFC Compliance Check...")
        print(f"📂 MAIA_ROOT: {self.maia_root}")
        print()

        # Check 1: Required directories
        print("📋 Checking required UFC directories...")
        dirs_ok = self.check_required_directories()
        print(f"   {'✅' if dirs_ok else '❌'} Required directories: {'PASS' if dirs_ok else 'FAIL'}")
        print()

        # Check 2: Nesting depth
        print("📏 Checking directory nesting depth...")
        nesting_ok = self.check_nesting_depth()
        print(f"   {'✅' if nesting_ok else '❌'} Nesting depth: {'PASS' if nesting_ok else 'FAIL'}")
        print(f"   📊 Max depth found: {self.stats['max_depth_found']} (preferred: {PREFERRED_NESTING_DEPTH}, max: {MAX_NESTING_DEPTH})")
        print()

        # Check 3: File naming
        print("📝 Checking file naming conventions...")
        naming_ok = self.check_file_naming()
        print(f"   {'✅' if naming_ok else '❌'} File naming: {'PASS' if naming_ok else 'FAIL'}")
        print()

        # Check 4: Context pollution
        print("🧹 Checking for context pollution...")
        pollution_ok = self.check_context_pollution()
        print(f"   {'✅' if pollution_ok else '❌'} Context separation: {'PASS' if pollution_ok else 'FAIL'}")
        print()

        # Overall compliance
        all_checks_pass = dirs_ok and nesting_ok and naming_ok and pollution_ok

        print("=" * 70)
        print(f"{'✅ UFC COMPLIANCE: PASS' if all_checks_pass else '❌ UFC COMPLIANCE: FAIL'}")
        print("=" * 70)
        print()

        # Summary
        print("📊 Summary:")
        print(f"   Total Files: {self.stats['total_files']}")
        print(f"   Total Directories: {self.stats['total_dirs']}")
        print(f"   Max Nesting Depth: {self.stats['max_depth_found']}")
        print(f"   Violations (Critical/High): {len([v for v in self.violations if v['severity'] in ['CRITICAL', 'HIGH']])}")
        print(f"   Warnings (Medium/Low): {len(self.warnings) + len([v for v in self.violations if v['severity'] in ['MEDIUM', 'LOW']])}")
        print()

        # Show violations
        if self.violations:
            print("🚨 VIOLATIONS:")
            for violation in self.violations:
                severity_emoji = "🔴" if violation['severity'] in ['CRITICAL', 'HIGH'] else "⚠️"
                print(f"   {severity_emoji} [{violation['severity']}] {violation['type']}")
                print(f"      {violation['message']}")
                print(f"      Path: {violation['path']}")
                print()

        # Show warnings (only if verbose or if there are violations)
        if self.warnings and (self.verbose or self.violations):
            print("⚠️  WARNINGS:")
            for warning in self.warnings[:10]:  # Limit to 10
                print(f"   ⚠️  [{warning['severity']}] {warning['type']}")
                print(f"      {warning['message']}")
                print()
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings (use --verbose to see all)")
                print()

        return {
            "compliant": all_checks_pass,
            "violations": self.violations,
            "warnings": self.warnings,
            "stats": self.stats
        }


def main():
    parser = argparse.ArgumentParser(
        description="UFC Compliance Checker - Validate Unified Filesystem-based Context system"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run compliance check"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="FILE",
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--maia-root",
        type=str,
        default=os.environ.get("MAIA_ROOT", str(Path(__file__).parent.parent.parent.parent.resolve())),
        help="Path to Maia root directory (default: $MAIA_ROOT)"
    )

    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 1

    maia_root = Path(args.maia_root)
    if not maia_root.exists():
        print(f"❌ Error: MAIA_ROOT not found: {maia_root}")
        return 1

    checker = UFCComplianceChecker(maia_root, verbose=args.verbose)
    result = checker.run_compliance_check()

    # Export to JSON if requested
    if args.json:
        output_path = Path(args.json)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"📄 Results exported to: {output_path}")

    # Exit code: 0 if compliant, 1 if violations
    return 0 if result["compliant"] else 1


if __name__ == "__main__":
    sys.exit(main())
