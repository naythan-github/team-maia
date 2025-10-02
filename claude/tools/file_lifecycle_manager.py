#!/usr/bin/env python3
"""
File Lifecycle Manager
Purpose: Protect immutable core files and enforce naming conventions
Created: 2025-09-30 - Phase 1 Anti-Sprawl Implementation
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class FileLifecycleManager:
    def __init__(self, base_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.base_path = Path(base_path)
        self.config_file = self.base_path / "claude/data/immutable_paths.json"
        self.bypass_flag = self.base_path / "claude/data/protection_bypass.flag"
        self.extension_zones = {
            'experimental': self.base_path / 'claude/extensions/experimental',
            'personal': self.base_path / 'claude/extensions/personal',
            'archive': self.base_path / 'claude/extensions/archive'
        }
        self.load_configuration()

    def load_configuration(self):
        """Load immutable paths configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in configuration: {e}")

    def is_bypass_active(self) -> bool:
        """Check if emergency bypass is active"""
        return self.bypass_flag.exists()

    def is_core_path(self, filepath: str) -> Optional[str]:
        """
        Check if path is in core system
        Returns: protection level ('absolute', 'high', 'medium') or None
        """
        # Normalize path to relative from base
        try:
            path_obj = Path(filepath)
            if path_obj.is_absolute():
                rel_path = str(path_obj.relative_to(self.base_path))
            else:
                rel_path = str(path_obj)
        except (ValueError, OSError):
            rel_path = str(filepath)

        # Check absolute immutability
        for protected_path in self.config['immutable_core']['absolute_immutability']:
            if rel_path == protected_path or rel_path.endswith(protected_path):
                return 'absolute'

        # Check high immutability (directory level)
        for protected_dir in self.config['immutable_core']['high_immutability']:
            if rel_path.startswith(protected_dir):
                return 'high'

        # Check medium immutability
        for protected_dir in self.config['immutable_core']['medium_immutability']:
            if rel_path.startswith(protected_dir):
                return 'medium'

        return None

    def validate_file_operation(
        self,
        operation: str,
        old_path: str,
        new_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate if file operation is allowed
        Returns: (allowed: bool, message: str)
        """
        # Check emergency bypass
        if self.is_bypass_active():
            return True, f"⚠️  BYPASS ACTIVE - Operation allowed (bypass flag present)"

        old_protection = self.is_core_path(old_path)

        if operation == 'delete':
            if old_protection == 'absolute':
                return False, f"❌ BLOCKED: Cannot delete core system file: {old_path}"
            elif old_protection == 'high':
                return False, f"❌ WARNING: Attempting to delete high-importance file: {old_path}"

        elif operation in ['move', 'rename']:
            if old_protection == 'absolute':
                return False, f"❌ BLOCKED: Cannot move/rename core system file: {old_path}"
            elif old_protection == 'high':
                if new_path:
                    new_protection = self.is_core_path(new_path)
                    if not new_protection:
                        return False, f"❌ BLOCKED: Cannot move core file outside core system: {old_path} → {new_path}"

        return True, "✅ Operation allowed"

    def suggest_alternative_action(self, operation: str, filepath: str, target_path: Optional[str] = None) -> List[Dict]:
        """Provide intelligent alternative suggestions for blocked operations"""
        suggestions = []
        protection = self.is_core_path(filepath)

        if not protection:
            return suggestions

        if operation in ['move', 'rename']:
            # Suggest copying to experimental zone
            filename = Path(filepath).name
            suggestions.append({
                'action': 'copy_to_experimental',
                'command': f'cp "{filepath}" "{self.extension_zones["experimental"] / filename}"',
                'description': 'Copy to experimental zone for modification without affecting core'
            })

        elif operation == 'delete':
            # Suggest archiving instead
            filename = Path(filepath).name
            suggestions.append({
                'action': 'archive',
                'command': f'mv "{filepath}" "{self.extension_zones["archive"] / filename}"',
                'description': 'Archive file for historical reference instead of deleting'
            })

        return suggestions

    def suggest_alternative(self, operation: str, filepath: str) -> List[str]:
        """Suggest alternative action for blocked operations"""
        suggestions = []

        if operation in ['move', 'rename']:
            suggestions.append(f"💡 Copy to extension zone: claude/extensions/experimental/")
            suggestions.append(f"💡 Create new file with improved name instead")
            suggestions.append(f"💡 Update content in place (core paths are immutable)")

        elif operation == 'delete':
            suggestions.append(f"💡 Move to archive: archive/deprecated/")
            suggestions.append(f"💡 Comment out content instead of deleting")
            suggestions.append(f"💡 Document deprecation in file header")

        return suggestions

    def validate_git_changes(self, git_status_output: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate pending git changes
        Returns: (all_valid: bool, violations: List[str])
        """
        if git_status_output is None:
            import subprocess
            try:
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=self.base_path,
                    capture_output=True,
                    text=True
                )
                git_status_output = result.stdout
            except Exception as e:
                return False, [f"Failed to get git status: {e}"]

        violations = []
        for line in git_status_output.strip().split('\n'):
            if not line:
                continue

            status = line[:2]
            filepath = line[3:].strip()

            # Handle renamed files
            if ' -> ' in filepath:
                old_path, new_path = filepath.split(' -> ')
                allowed, message = self.validate_file_operation('move', old_path.strip(), new_path.strip())
                if not allowed:
                    violations.append(message)
                    suggestions = self.suggest_alternative('move', old_path.strip())
                    violations.extend(suggestions)

            # Handle deleted files
            elif status.startswith('D'):
                allowed, message = self.validate_file_operation('delete', filepath)
                if not allowed:
                    violations.append(message)
                    suggestions = self.suggest_alternative('delete', filepath)
                    violations.extend(suggestions)

        return (len(violations) == 0), violations

    def check_naming_convention(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """
        Check if file follows naming conventions
        Returns: (valid: bool, suggestion: Optional[str])
        """
        path = Path(filepath)

        # Skip archive and data directories
        if '/archive/' in str(path) or '/claude/data/' in str(path):
            return True, None

        # Get anti-patterns from config
        anti_patterns = []
        for pattern_list in self.config.get('anti_patterns', {}).values():
            anti_patterns.extend(pattern_list)

        import re
        for pattern in anti_patterns:
            if re.search(pattern, path.name):
                suggestion = path.name
                # Remove anti-pattern indicators
                for ap in ['_v\\d+', '_version\\d+', '_new', '_old', '_temp', '_backup', '_final', '_latest']:
                    suggestion = re.sub(ap, '', suggestion)
                return False, f"Naming violation: {path.name} → suggested: {suggestion}"

        return True, None

    def validate_pre_commit(self) -> int:
        """
        Validate changes before commit
        Returns: 0 if valid, 1 if violations found
        """
        print("🔍 Validating file changes...")

        # Check for bypass
        if self.is_bypass_active():
            print("⚠️  WARNING: Emergency bypass is active!")
            print(f"   Remove bypass flag to restore protection: rm {self.bypass_flag}")
            return 0

        # Validate git changes
        valid, violations = self.validate_git_changes()

        if not valid:
            print("\n❌ COMMIT BLOCKED - Core file protection violations detected:\n")
            for violation in violations:
                print(f"   {violation}")
            print(f"\n📖 See {self.base_path / 'claude/context/core/immutable_core_structure.md'} for guidelines")
            print(f"\n🚨 Emergency bypass (use only for disaster recovery):")
            print(f"   touch {self.bypass_flag}")
            return 1

        print("✅ File lifecycle validation passed")
        return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 file_lifecycle_manager.py <command>")
        print("\nCommands:")
        print("  validate-changes     - Validate pending git changes")
        print("  check-file <path>    - Check protection level of file")
        print("  test                 - Run test suite")
        print("  pre-commit           - Run pre-commit validation")
        return 1

    try:
        manager = FileLifecycleManager()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1

    command = sys.argv[1]

    if command == 'validate-changes':
        valid, violations = manager.validate_git_changes()
        if not valid:
            print("❌ VIOLATIONS DETECTED:")
            for violation in violations:
                print(f"  {violation}")
            return 1
        else:
            print("✅ All changes validated")
            return 0

    elif command == 'check-file':
        if len(sys.argv) < 3:
            print("Usage: check-file <filepath>")
            return 1

        filepath = sys.argv[2]
        protection = manager.is_core_path(filepath)

        if protection:
            print(f"🔒 File: {filepath}")
            print(f"   Protection level: {protection.upper()}")
        else:
            print(f"📂 File: {filepath}")
            print(f"   Not protected (can be modified)")
        return 0

    elif command == 'test':
        print("🧪 Running test suite...\n")

        # Test core files
        test_files = [
            ('claude/context/core/identity.md', 'absolute'),
            ('claude/context/core/ufc_system.md', 'absolute'),
            ('CLAUDE.md', 'absolute'),
            ('claude/agents/jobs_agent.md', 'medium'),
            ('claude/tools/backup_manager.py', 'medium'),
            ('claude/extensions/experimental/test.md', None),
            ('archive/old_code.py', None),
        ]

        all_passed = True
        for test_file, expected_protection in test_files:
            actual_protection = manager.is_core_path(test_file)
            status = "✅" if actual_protection == expected_protection else "❌"
            print(f"{status} {test_file}: {actual_protection or 'not protected'} (expected: {expected_protection or 'not protected'})")
            if actual_protection != expected_protection:
                all_passed = False

        # Test operations
        print("\n🧪 Testing operations...\n")

        test_ops = [
            ('delete', 'claude/context/core/identity.md', None, False),
            ('move', 'claude/agents/test.md', 'archive/test.md', True),
            ('move', 'CLAUDE.md', 'backup/CLAUDE.md', False),
        ]

        for operation, old_path, new_path, should_allow in test_ops:
            allowed, message = manager.validate_file_operation(operation, old_path, new_path)
            status = "✅" if allowed == should_allow else "❌"
            print(f"{status} {operation} {old_path}: {message}")
            if allowed != should_allow:
                all_passed = False

        print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
        return 0 if all_passed else 1

    elif command == 'pre-commit':
        return manager.validate_pre_commit()

    elif command == 'init-zones':
        """Initialize extension zones"""
        for zone_name, zone_path in manager.extension_zones.items():
            if zone_path.exists():
                print(f"✅ Extension zone exists: {zone_path}")
            else:
                print(f"❌ Extension zone missing: {zone_path}")
                return 1
        print("✅ All extension zones validated")
        return 0

    elif command == 'suggest-alternatives':
        if len(sys.argv) < 4:
            print("Usage: suggest-alternatives <operation> <filepath>")
            return 1

        operation = sys.argv[2]
        filepath = sys.argv[3]

        suggestions = manager.suggest_alternative_action(operation, filepath)
        if suggestions:
            print(f"💡 Alternatives for {operation} on {filepath}:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n{i}. {suggestion['description']}")
                print(f"   Command: {suggestion['command']}")
        else:
            print(f"✅ Operation {operation} on {filepath} is allowed")
        return 0

    else:
        print(f"❌ Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())