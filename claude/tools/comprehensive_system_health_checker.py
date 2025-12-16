#!/usr/bin/env python3
"""
Comprehensive System Health Checker
Purpose: Understand what's actually broken vs working before fixing anything
Created: 2025-09-30 - Phase 1 Anti-Sprawl Implementation
"""

import os
import sys
import json
import ast
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import importlib.util
import re

class ComprehensiveSystemHealthChecker:
    def __init__(self, base_path=None):
        # Calculate MAIA root: this file is at claude/tools/comprehensive_system_health_checker.py
        # So parents[2] = maia root
        if base_path is None:
            base_path = str(Path(__file__).resolve().parents[2])
        self.base_path = Path(base_path)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(base_path),
            'checks': {},
            'summary': {},
            'issues': [],
            'recommendations': []
        }

    def run_all_checks(self):
        """Run complete health assessment"""
        print("🏥 COMPREHENSIVE SYSTEM HEALTH CHECK")
        print("=" * 70)

        checks = [
            ("Python Import Validation", self.check_python_imports),
            ("File Reference Validation", self.check_file_references),
            ("Agent Discovery", self.check_agent_discovery),
            ("Tool Functionality", self.check_tool_functionality),
            ("Context Loading System", self.check_context_loading),
            ("Database Connectivity", self.check_databases),
            ("Command File Validation", self.check_commands),
            ("Core File Integrity", self.check_core_files),
        ]

        for check_name, check_func in checks:
            print(f"\n🔍 Running: {check_name}...")
            try:
                result = check_func()
                self.results['checks'][check_name] = result
                self._print_check_result(check_name, result)
            except Exception as e:
                error_result = {
                    'status': 'error',
                    'error': str(e),
                    'passed': False
                }
                self.results['checks'][check_name] = error_result
                print(f"   ❌ ERROR: {e}")

        self._generate_summary()
        self._generate_recommendations()
        return self.results

    def check_python_imports(self) -> Dict:
        """Check if Python files can import correctly"""
        result = {
            'total_files': 0,
            'importable': 0,
            'broken_imports': [],
            'syntax_errors': [],
            'passed': True
        }

        for py_file in self.base_path.glob('claude/**/*.py'):
            if '__pycache__' in str(py_file) or 'archive/' in str(py_file):
                continue

            result['total_files'] += 1

            # Check syntax
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
                result['importable'] += 1
            except SyntaxError as e:
                result['syntax_errors'].append({
                    'file': str(py_file.relative_to(self.base_path)),
                    'error': str(e)
                })
                result['passed'] = False
            except Exception as e:
                result['broken_imports'].append({
                    'file': str(py_file.relative_to(self.base_path)),
                    'error': str(e)
                })

        result['import_success_rate'] = (
            result['importable'] / result['total_files'] * 100
            if result['total_files'] > 0 else 0
        )

        return result

    def check_file_references(self) -> Dict:
        """Check if referenced files actually exist"""
        result = {
            'files_checked': 0,
            'references_found': 0,
            'broken_references': [],
            'passed': True
        }

        # Check markdown files for file references
        reference_patterns = [
            r'`([^`]+\.(py|md))`',  # Backtick references
            r'\[([^\]]+)\]\(([^)]+\.(py|md))\)',  # Markdown links
            r'claude/[a-z/]+\.(py|md)',  # Direct paths
        ]

        for md_file in self.base_path.glob('claude/**/*.md'):
            if 'archive/' in str(md_file):
                continue

            result['files_checked'] += 1

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in reference_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            ref_path = match[1] if len(match) > 1 else match[0]
                        else:
                            ref_path = match

                        result['references_found'] += 1

                        # Check if referenced file exists
                        full_path = self.base_path / ref_path
                        if not full_path.exists():
                            result['broken_references'].append({
                                'source': str(md_file.relative_to(self.base_path)),
                                'missing_file': ref_path
                            })
                            result['passed'] = False
            except Exception as e:
                pass  # Skip files we can't read

        return result

    def check_agent_discovery(self) -> Dict:
        """Check agent files and discoverability"""
        result = {
            'total_agents': 0,
            'valid_agents': 0,
            'invalid_agents': [],
            'naming_violations': [],
            'passed': True
        }

        agent_dir = self.base_path / 'claude' / 'agents'
        if not agent_dir.exists():
            result['passed'] = False
            result['error'] = "Agent directory not found"
            return result

        for agent_file in agent_dir.glob('*.md'):
            result['total_agents'] += 1

            # Check naming convention
            if not agent_file.name.endswith('_agent.md'):
                result['naming_violations'].append(str(agent_file.name))
                result['passed'] = False

            # Check if file is readable and has content
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 100:  # Has meaningful content
                        result['valid_agents'] += 1
                    else:
                        result['invalid_agents'].append({
                            'file': str(agent_file.name),
                            'reason': 'Empty or minimal content'
                        })
            except Exception as e:
                result['invalid_agents'].append({
                    'file': str(agent_file.name),
                    'reason': f'Read error: {e}'
                })

        result['discovery_rate'] = (
            result['valid_agents'] / result['total_agents'] * 100
            if result['total_agents'] > 0 else 0
        )

        return result

    def check_tool_functionality(self) -> Dict:
        """Check tool files for basic functionality indicators"""
        result = {
            'total_tools': 0,
            'tools_with_main': 0,
            'tools_with_docstrings': 0,
            'potentially_broken': [],
            'passed': True
        }

        for tool_file in self.base_path.glob('claude/tools/**/*.py'):
            if '__pycache__' in str(tool_file) or tool_file.name == '__init__.py':
                continue

            result['total_tools'] += 1

            try:
                with open(tool_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for main function or if __name__ == "__main__"
                if 'if __name__' in content or 'def main(' in content:
                    result['tools_with_main'] += 1

                # Check for docstrings
                if '"""' in content or "'''" in content:
                    result['tools_with_docstrings'] += 1

                # Check for obvious issues
                if 'TODO: FIX' in content or 'BROKEN' in content:
                    result['potentially_broken'].append(str(tool_file.relative_to(self.base_path)))

            except Exception:
                pass

        return result

    def check_context_loading(self) -> Dict:
        """Check UFC context loading system"""
        result = {
            'core_files_exist': True,
            'missing_files': [],
            'passed': True
        }

        core_files = [
            'claude/context/ufc_system.md',
            'claude/context/core/identity.md',
            'claude/context/core/systematic_thinking_protocol.md',
            'claude/context/core/model_selection_strategy.md',
            'claude/context/core/smart_context_loading.md',
            'CLAUDE.md'
        ]

        for core_file in core_files:
            full_path = self.base_path / core_file
            if not full_path.exists():
                result['missing_files'].append(core_file)
                result['core_files_exist'] = False
                result['passed'] = False

        result['core_files_count'] = len(core_files) - len(result['missing_files'])

        return result

    def check_databases(self) -> Dict:
        """Check database files for connectivity"""
        result = {
            'total_databases': 0,
            'accessible_databases': 0,
            'corrupted_databases': [],
            'passed': True
        }

        for db_file in self.base_path.glob('claude/data/**/*.db'):
            result['total_databases'] += 1

            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()

                if len(tables) > 0:
                    result['accessible_databases'] += 1
                else:
                    result['corrupted_databases'].append({
                        'file': str(db_file.relative_to(self.base_path)),
                        'reason': 'No tables found'
                    })
            except Exception as e:
                result['corrupted_databases'].append({
                    'file': str(db_file.relative_to(self.base_path)),
                    'reason': str(e)
                })
                result['passed'] = False

        return result

    def check_commands(self) -> Dict:
        """Check command files for validity"""
        result = {
            'total_commands': 0,
            'valid_commands': 0,
            'issues': [],
            'passed': True
        }

        command_dir = self.base_path / 'claude' / 'commands'
        if not command_dir.exists():
            result['passed'] = False
            return result

        for cmd_file in command_dir.glob('*.md'):
            result['total_commands'] += 1

            try:
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if len(content) > 50:  # Has meaningful content
                    result['valid_commands'] += 1
                else:
                    result['issues'].append({
                        'file': str(cmd_file.name),
                        'reason': 'Minimal content'
                    })
            except Exception as e:
                result['issues'].append({
                    'file': str(cmd_file.name),
                    'reason': f'Read error: {e}'
                })
                result['passed'] = False

        return result

    def check_core_files(self) -> Dict:
        """Check integrity of absolutely protected core files"""
        result = {
            'total_core_files': 0,
            'accessible': 0,
            'missing': [],
            'passed': True
        }

        # Load immutable paths config
        try:
            with open(self.base_path / 'claude/data/immutable_paths.json', 'r') as f:
                config = json.load(f)
                core_files = config['immutable_core']['absolute_immutability']
        except:
            result['passed'] = False
            result['error'] = 'Could not load immutable_paths.json'
            return result

        for core_file in core_files:
            result['total_core_files'] += 1
            full_path = self.base_path / core_file

            if full_path.exists():
                result['accessible'] += 1
            else:
                result['missing'].append(core_file)
                result['passed'] = False

        return result

    def _print_check_result(self, check_name: str, result: Dict):
        """Print formatted check result"""
        status = "✅ PASS" if result.get('passed', True) else "❌ FAIL"
        print(f"   {status}")

        # Print key metrics
        for key, value in result.items():
            if key in ['passed', 'error']:
                continue
            if isinstance(value, (int, float)):
                print(f"      {key}: {value}")
            elif isinstance(value, list) and len(value) > 0 and len(value) <= 3:
                print(f"      {key}: {len(value)} items")

    def _generate_summary(self):
        """Generate overall health summary"""
        checks = self.results['checks']

        total_checks = len(checks)
        passed_checks = sum(1 for c in checks.values() if c.get('passed', True))

        self.results['summary'] = {
            'overall_health': f"{passed_checks}/{total_checks} checks passed",
            'health_percentage': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            'critical_issues': [],
            'warnings': []
        }

        # Identify critical issues
        if not checks.get('Context Loading System', {}).get('passed', True):
            self.results['summary']['critical_issues'].append(
                'Context loading system has missing files'
            )

        if not checks.get('Core File Integrity', {}).get('passed', True):
            self.results['summary']['critical_issues'].append(
                'Core immutable files are missing or inaccessible'
            )

        # Identify warnings
        agent_check = checks.get('Agent Discovery', {})
        if agent_check.get('naming_violations', []):
            self.results['summary']['warnings'].append(
                f"{len(agent_check['naming_violations'])} agents have naming violations"
            )

    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        checks = self.results['checks']

        # Agent naming violations
        agent_check = checks.get('Agent Discovery', {})
        if agent_check.get('naming_violations'):
            self.results['recommendations'].append({
                'priority': 'high',
                'category': 'agents',
                'action': f"Rename {len(agent_check['naming_violations'])} agents to follow {'{function}_agent.md'} convention",
                'files': agent_check['naming_violations']
            })

        # Broken file references
        ref_check = checks.get('File Reference Validation', {})
        if ref_check.get('broken_references'):
            self.results['recommendations'].append({
                'priority': 'medium',
                'category': 'references',
                'action': f"Fix or remove {len(ref_check['broken_references'])} broken file references",
                'count': len(ref_check['broken_references'])
            })

        # Database issues
        db_check = checks.get('Database Connectivity', {})
        if db_check.get('corrupted_databases'):
            self.results['recommendations'].append({
                'priority': 'low',
                'category': 'databases',
                'action': f"Investigate {len(db_check['corrupted_databases'])} database issues",
                'count': len(db_check['corrupted_databases'])
            })

    def save_report(self, output_path: str = None):
        """Save comprehensive report"""
        if output_path is None:
            output_path = self.base_path / 'claude/data/system_health_report.json'

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Report saved: {output_path}")
        return output_path

    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "=" * 70)
        print("📊 SYSTEM HEALTH SUMMARY")
        print("=" * 70)

        summary = self.results['summary']
        print(f"\n🏥 Overall Health: {summary['health_percentage']:.1f}%")
        print(f"   {summary['overall_health']}")

        if summary['critical_issues']:
            print(f"\n🔴 Critical Issues ({len(summary['critical_issues'])}):")
            for issue in summary['critical_issues']:
                print(f"   • {issue}")

        if summary['warnings']:
            print(f"\n⚠️  Warnings ({len(summary['warnings'])}):")
            for warning in summary['warnings']:
                print(f"   • {warning}")

        if self.results['recommendations']:
            print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
            for rec in self.results['recommendations']:
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[rec['priority']]
                print(f"   {priority_icon} {rec['action']}")

def main():
    checker = ComprehensiveSystemHealthChecker()
    checker.run_all_checks()
    checker.print_summary()
    checker.save_report()

    print("\n✅ Health check complete!")
    print("📄 Detailed report: claude/data/system_health_report.json")

if __name__ == "__main__":
    main()