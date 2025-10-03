#!/usr/bin/env python3
"""
Anti-Sprawl Validator - Pre-Commit Sprawl Detection
Created: 2025-10-02 (Phase 81)

Validates system state before git commits to prevent sprawl from being permanently committed.
Integrated into save_state.md workflow as Phase 2.5.

Checks:
1. Old experimental files (>7 days) - should be graduated or archived
2. Naming violations in production - version indicators, temporal markers
3. New production files without documentation
4. Duplicate/similar files in production
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict, Tuple

class AntiSprawlValidator:
    def __init__(self):
        self.maia_root = Path(__file__).resolve().parents[2]
        self.experimental_dir = self.maia_root / "claude" / "extensions" / "experimental"
        self.production_dirs = [
            self.maia_root / "claude" / "tools",
            self.maia_root / "claude" / "agents",
            self.maia_root / "claude" / "commands"
        ]

        # Load naming rules
        self.immutable_paths = self.maia_root / "claude" / "data" / "immutable_paths.json"
        self.prohibited_patterns = []
        self.load_naming_rules()

        self.violations = []
        self.warnings = []

    def load_naming_rules(self):
        """Load prohibited naming patterns from immutable_paths.json"""
        if self.immutable_paths.exists():
            with open(self.immutable_paths, 'r') as f:
                config = json.load(f)
                self.prohibited_patterns = config.get('naming_conventions', {}).get('prohibited_patterns', [])

    def check_experimental_age(self) -> List[Dict]:
        """Check for experimental files older than 7 days"""
        old_files = []

        if not self.experimental_dir.exists():
            return old_files

        cutoff_date = datetime.now() - timedelta(days=7)

        for file_path in self.experimental_dir.rglob("*.py"):
            if file_path.name == "README.md":
                continue

            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff_date:
                age_days = (datetime.now() - mtime).days
                old_files.append({
                    'file': str(file_path.relative_to(self.maia_root)),
                    'age_days': age_days,
                    'type': 'warning',
                    'message': f'Experimental file is {age_days} days old - graduate or archive?'
                })

        return old_files

    def check_naming_violations(self) -> List[Dict]:
        """Check for naming convention violations in production directories"""
        violations = []

        # Prohibited patterns - version/temporal indicators, not semantic words
        # Note: 'validator', 'backup', 'manager' are SEMANTIC (describe function) - not violations
        patterns = {
            '_v[0-9]': r'_v\d+',  # Version indicators: file_v1.py, file_v2.py
            '_new': '_new',        # Temporal: new_feature.py, feature_new.py
            '_old': '_old',        # Temporal: old_feature.py, feature_old.py
            '_updated': '_updated', # Temporal: feature_updated.py
            '_final': '_final',    # Temporal: feature_final.py
            '_copy': '_copy',      # Duplicates: feature_copy.py
        }

        # Semantic exceptions - these words describe FUNCTION, not version/state
        semantic_words = [
            'validator', 'validation',  # Validates something
            'backup', 'backups',        # Handles backups
            'manager', 'management',    # Manages something
            'test', 'testing',          # Test harness/framework (not temp test files)
            'template', 'templates',    # Template system (not temporary)
            'temp', 'temporary'         # If part of semantic name (temporary_storage.py)
        ]

        for prod_dir in self.production_dirs:
            if not prod_dir.exists():
                continue

            for file_path in prod_dir.rglob("*.py"):
                filename = file_path.stem

                # Check each prohibited pattern
                for pattern_name, pattern in patterns.items():
                    # Only flag if it's a clear version/temporal indicator
                    # Not if it's part of a semantic word
                    if pattern_name in filename:
                        # Check if it's actually a semantic word being used correctly
                        is_semantic = False
                        for semantic in semantic_words:
                            if semantic in filename:
                                is_semantic = True
                                break

                        # Only flag if NOT semantic and pattern matches
                        if not is_semantic:
                            violations.append({
                                'file': str(file_path.relative_to(self.maia_root)),
                                'pattern': pattern_name,
                                'type': 'error',
                                'message': f'Naming violation: contains "{pattern_name}" (version/temporal indicator)'
                            })
                            break

        return violations

    def check_similar_files(self) -> List[Dict]:
        """Check for potentially duplicate files (similar names)"""
        duplicates = []

        for prod_dir in self.production_dirs:
            if not prod_dir.exists():
                continue

            files = {}
            for file_path in prod_dir.rglob("*.py"):
                if file_path.name == "__init__.py":
                    continue

                # Extract base name (remove suffixes like _v1, _new, etc.)
                base_name = file_path.stem
                for suffix in ['_v1', '_v2', '_v3', '_new', '_old', '_updated', '_enhanced']:
                    base_name = base_name.replace(suffix, '')

                if base_name not in files:
                    files[base_name] = []
                files[base_name].append(file_path)

            # Find bases with multiple files
            for base_name, file_list in files.items():
                if len(file_list) > 1:
                    duplicates.append({
                        'base_name': base_name,
                        'files': [str(f.relative_to(self.maia_root)) for f in file_list],
                        'type': 'warning',
                        'message': f'Multiple similar files found: {len(file_list)} files with base "{base_name}"'
                    })

        return duplicates

    def check_documentation_updates(self) -> List[Dict]:
        """Check if SYSTEM_STATE.md was updated with new production files"""
        missing_docs = []

        # Get recently modified production files (last 24 hours)
        cutoff_date = datetime.now() - timedelta(hours=24)
        recent_files = []

        for prod_dir in self.production_dirs:
            if not prod_dir.exists():
                continue

            for file_path in prod_dir.rglob("*.py"):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > cutoff_date:
                    recent_files.append(file_path)

        if recent_files:
            # Check if SYSTEM_STATE.md was also updated
            system_state = self.maia_root / "SYSTEM_STATE.md"
            if system_state.exists():
                state_mtime = datetime.fromtimestamp(system_state.stat().st_mtime)

                if state_mtime < cutoff_date:
                    for f in recent_files:
                        missing_docs.append({
                            'file': str(f.relative_to(self.maia_root)),
                            'type': 'warning',
                            'message': 'New production file but SYSTEM_STATE.md not updated'
                        })

        return missing_docs

    def validate(self) -> Tuple[bool, Dict]:
        """Run all validation checks"""
        results = {
            'old_experimental': self.check_experimental_age(),
            'naming_violations': self.check_naming_violations(),
            'similar_files': self.check_similar_files(),
            'missing_docs': self.check_documentation_updates()
        }

        # Count errors vs warnings
        errors = []
        warnings = []

        for check_name, items in results.items():
            for item in items:
                if item.get('type') == 'error':
                    errors.append(item)
                else:
                    warnings.append(item)

        has_errors = len(errors) > 0

        return not has_errors, {
            'errors': errors,
            'warnings': warnings,
            'summary': {
                'total_errors': len(errors),
                'total_warnings': len(warnings),
                'checks_run': len(results)
            }
        }

    def format_report(self, results: Dict) -> str:
        """Format validation results as readable report"""
        errors = results['errors']
        warnings = results['warnings']
        summary = results['summary']

        report = []
        report.append("=" * 60)
        report.append("🔍 Anti-Sprawl Validation Report")
        report.append("=" * 60)
        report.append("")

        # Summary
        if summary['total_errors'] == 0 and summary['total_warnings'] == 0:
            report.append("✅ No sprawl violations detected")
            report.append("")
            return "\n".join(report)

        report.append(f"Errors: {summary['total_errors']}")
        report.append(f"Warnings: {summary['total_warnings']}")
        report.append("")

        # Errors (blocking)
        if errors:
            report.append("❌ ERRORS (Must Fix Before Commit):")
            report.append("-" * 60)
            for error in errors:
                report.append(f"  File: {error['file']}")
                report.append(f"  Issue: {error['message']}")
                report.append("")

        # Warnings (should review)
        if warnings:
            report.append("⚠️  WARNINGS (Should Review):")
            report.append("-" * 60)
            for warning in warnings:
                if 'files' in warning:  # Similar files warning
                    report.append(f"  Base: {warning['base_name']}")
                    report.append(f"  Files:")
                    for f in warning['files']:
                        report.append(f"    - {f}")
                else:
                    report.append(f"  File: {warning['file']}")
                report.append(f"  Issue: {warning['message']}")
                report.append("")

        # Recommendations
        report.append("💡 Recommendations:")
        report.append("-" * 60)

        if errors:
            report.append("  1. Fix naming violations (remove version indicators from production)")
            report.append("  2. Move versioned files to experimental/ or archive/")

        if warnings:
            report.append("  3. Graduate or archive old experimental files")
            report.append("  4. Consolidate similar files (choose one winner)")
            report.append("  5. Update SYSTEM_STATE.md with new production changes")

        report.append("")
        return "\n".join(report)


def main():
    """CLI interface for anti-sprawl validation"""
    validator = AntiSprawlValidator()

    print("🔍 Running anti-sprawl validation...\n")

    passed, results = validator.validate()
    report = validator.format_report(results)

    print(report)

    if not passed:
        print("❌ Validation FAILED - Fix errors before committing")
        sys.exit(1)
    elif results['warnings']:
        print("⚠️  Validation PASSED with warnings - Review recommended")
        sys.exit(0)
    else:
        print("✅ Validation PASSED - No sprawl detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
