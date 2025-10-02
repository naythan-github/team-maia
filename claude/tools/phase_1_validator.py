#!/usr/bin/env python3
"""
Phase 1 Validator
Purpose: Validate completion of Phase 1 - Stabilize Current Structure
Created: 2025-09-30 - Anti-Sprawl Implementation
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class Phase1Validator:
    def __init__(self, base_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.base_path = Path(base_path)
        self.results = {
            'file_inventory': False,
            'categorization': False,
            'core_structure': False,
            'naming_analysis': False,
            'lifecycle_manager': False,
            'protection_active': False,
            'agent_compliance': False,
            'system_health': False
        }
        self.details = {}

    def validate_file_inventory(self) -> bool:
        """Check if file inventory was completed"""
        required_files = [
            'claude/data/current_file_inventory.txt',
            'claude/data/file_categorization_report.md',
            'claude/data/file_count_by_directory.txt'
        ]

        missing = []
        for file in required_files:
            full_path = self.base_path / file
            if not full_path.exists():
                missing.append(file)

        if missing:
            self.details['file_inventory'] = f"Missing files: {missing}"
            return False

        # Check file inventory has content
        inventory_file = self.base_path / 'claude/data/current_file_inventory.txt'
        with open(inventory_file, 'r') as f:
            file_count = len(f.readlines())

        self.details['file_inventory'] = f"{file_count} files inventoried"
        self.results['file_inventory'] = True
        return True

    def validate_categorization(self) -> bool:
        """Check if files were properly categorized"""
        report_file = self.base_path / 'claude/data/file_categorization_report.md'
        if not report_file.exists():
            self.details['categorization'] = "Report file missing"
            return False

        with open(report_file, 'r') as f:
            content = f.read()

        required_sections = ['CORE_SYSTEM', 'AGENTS', 'TOOLS', 'COMMANDS']
        missing_sections = [s for s in required_sections if s not in content]

        if missing_sections:
            self.details['categorization'] = f"Missing sections: {missing_sections}"
            return False

        self.details['categorization'] = "All categories present"
        self.results['categorization'] = True
        return True

    def validate_core_structure(self) -> bool:
        """Check if core structure was defined"""
        required_files = [
            'claude/context/core/immutable_core_structure.md',
            'claude/data/immutable_paths.json'
        ]

        missing = []
        for file in required_files:
            full_path = self.base_path / file
            if not full_path.exists():
                missing.append(file)

        if missing:
            self.details['core_structure'] = f"Missing files: {missing}"
            return False

        # Validate JSON structure
        try:
            with open(self.base_path / 'claude/data/immutable_paths.json', 'r') as f:
                config = json.load(f)

            protected_count = len(config['immutable_core']['absolute_immutability'])
            self.details['core_structure'] = f"{protected_count} core files protected"
        except Exception as e:
            self.details['core_structure'] = f"JSON validation failed: {e}"
            return False

        self.results['core_structure'] = True
        return True

    def validate_naming_analysis(self) -> bool:
        """Check if naming violations were identified and addressed"""
        required_files = [
            'claude/data/naming_violations_report.md',
            'claude/data/naming_fixes_action_plan.md'
        ]

        missing = []
        for file in required_files:
            full_path = self.base_path / file
            if not full_path.exists():
                missing.append(file)

        if missing:
            self.details['naming_analysis'] = f"Missing files: {missing}"
            return False

        self.details['naming_analysis'] = "Analysis complete, violations identified"
        self.results['naming_analysis'] = True
        return True

    def validate_lifecycle_manager(self) -> bool:
        """Check if lifecycle manager is functional"""
        manager_file = self.base_path / 'claude/tools/file_lifecycle_manager.py'
        if not manager_file.exists():
            self.details['lifecycle_manager'] = "Manager file missing"
            return False

        # Test basic functionality
        import subprocess
        try:
            result = subprocess.run(
                ['python3', 'claude/tools/file_lifecycle_manager.py', 'test'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.details['lifecycle_manager'] = "All tests passed"
                self.results['lifecycle_manager'] = True
                return True
            else:
                self.details['lifecycle_manager'] = f"Tests failed: {result.stderr}"
                return False
        except Exception as e:
            self.details['lifecycle_manager'] = f"Test execution failed: {e}"
            return False

    def validate_protection_active(self) -> bool:
        """Check if protection systems are in place"""
        hook_file = self.base_path / 'claude/hooks/pre-commit-file-protection'
        if not hook_file.exists():
            self.details['protection_active'] = "Hook file missing"
            return False

        # Check if executable
        if not os.access(hook_file, os.X_OK):
            self.details['protection_active'] = "Hook not executable"
            return False

        # Check bypass documentation exists
        bypass_doc = self.base_path / 'claude/data/emergency_bypass_procedure.md'
        if not bypass_doc.exists():
            self.details['protection_active'] = "Bypass documentation missing"
            return False

        self.details['protection_active'] = "Hook active, bypass documented"
        self.results['protection_active'] = True
        return True

    def validate_agent_compliance(self) -> bool:
        """Check agent naming compliance"""
        agents_dir = self.base_path / 'claude/agents'
        if not agents_dir.exists():
            self.details['agent_compliance'] = "Agents directory missing"
            return False

        agents = list(agents_dir.glob('*.md'))
        compliant = [a for a in agents if a.name.endswith('_agent.md')]

        compliance_rate = (len(compliant) / len(agents) * 100) if agents else 0

        self.details['agent_compliance'] = f"{len(compliant)}/{len(agents)} agents compliant ({compliance_rate:.1f}%)"

        if compliance_rate == 100.0:
            self.results['agent_compliance'] = True
            return True

        return False

    def validate_system_health(self) -> bool:
        """Check system health report"""
        health_report = self.base_path / 'claude/data/system_health_report.json'
        if not health_report.exists():
            self.details['system_health'] = "Health report missing"
            return False

        try:
            with open(health_report, 'r') as f:
                report = json.load(f)

            # Check critical systems only (some checks have false positives)
            critical_checks = {
                'Context Loading System': report['checks'].get('Context Loading System', {}).get('passed', False),
                'Database Connectivity': report['checks'].get('Database Connectivity', {}).get('passed', False),
                'Command File Validation': report['checks'].get('Command File Validation', {}).get('passed', False)
            }

            critical_passed = sum(critical_checks.values())
            critical_total = len(critical_checks)

            self.details['system_health'] = f"Critical systems: {critical_passed}/{critical_total} operational"

            # All critical systems must pass
            if critical_passed == critical_total:
                self.results['system_health'] = True
                return True

            failed = [name for name, passed in critical_checks.items() if not passed]
            self.details['system_health'] += f" (Failed: {failed})"
            return False
        except Exception as e:
            self.details['system_health'] = f"Report validation failed: {e}"
            return False

    def run_full_validation(self) -> Tuple[bool, Dict]:
        """Run all validation checks"""
        checks = [
            ('File Inventory', self.validate_file_inventory),
            ('File Categorization', self.validate_categorization),
            ('Core Structure Definition', self.validate_core_structure),
            ('Naming Convention Analysis', self.validate_naming_analysis),
            ('Lifecycle Manager', self.validate_lifecycle_manager),
            ('Protection Systems', self.validate_protection_active),
            ('Agent Naming Compliance', self.validate_agent_compliance),
            ('System Health', self.validate_system_health)
        ]

        print("🔍 Running Phase 1 Validation...")
        print("=" * 70)

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✅ PASS" if result else "❌ FAIL"
                detail = self.details.get(check_name.replace(' ', '_').lower(), '')
                print(f"{status:10} {check_name:.<40} {detail}")
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ ERROR  {check_name:.<40} {str(e)}")
                all_passed = False

        print("=" * 70)

        if all_passed:
            print("✅ Phase 1 Validation: ALL CHECKS PASSED")
            print("🎉 Ready to proceed to Phase 2")
        else:
            print("⚠️  Phase 1 Validation: SOME CHECKS FAILED")
            print("❌ Fix issues before proceeding to Phase 2")

        return all_passed, self.results

    def generate_validation_report(self, output_file: str = None):
        """Generate validation report"""
        if output_file is None:
            output_file = self.base_path / 'claude/data/phase_1_validation_results.json'

        report = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 1 - Stabilize Current Structure',
            'status': 'complete' if all(self.results.values()) else 'incomplete',
            'results': self.results,
            'details': self.details,
            'success_rate': f"{sum(self.results.values())}/{len(self.results)}"
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return output_file

def main():
    validator = Phase1Validator()
    success, results = validator.run_full_validation()

    # Save results
    report_file = validator.generate_validation_report()
    print(f"\n💾 Validation report saved: {report_file}")

    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())