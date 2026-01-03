#!/usr/bin/env python3
import json
import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class MaiaSystemHealthChecker:
    def __init__(self):
        self.health_db = "claude/data/system_health.db"
        self.baseline_file = "claude/data/system_baseline.json"
        self.critical_files = [
            'claude/context/core/identity.md',
            'claude/context/core/systematic_thinking_protocol.md',
            'claude/context/core/model_selection_strategy.md',
            'claude/context/core/ufc_system.md',
            'claude/context/core/smart_context_loading.md'
        ]
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize health monitoring database"""
        Path("claude/data").mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL,
                check_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                baseline_comparison TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_integrity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                last_modified TEXT NOT NULL,
                status TEXT DEFAULT 'healthy',
                check_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dependency_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                target_file TEXT NOT NULL,
                reference_type TEXT NOT NULL,
                line_number INTEGER,
                discovered_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_baseline(self) -> Dict:
        """Create system baseline before implementation"""
        baseline = {
            'created_date': datetime.now().isoformat(),
            'file_structure': self.scan_file_structure(),
            'critical_files': self.check_critical_files(),
            'context_loading': self.test_context_loading(),
            'agent_discovery': self.test_agent_discovery(),
            'tool_accessibility': self.test_tool_accessibility(),
            'dependencies': self.map_dependencies(),
            'git_status': self.get_git_status()
        }
        
        # Save baseline
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        # Record in database
        self.record_health_check('baseline_creation', 'success', baseline)
        
        return baseline
    
    def scan_file_structure(self) -> Dict:
        """Scan current file structure"""
        structure = {
            'total_files': 0,
            'directories': {},
            'file_types': {},
            'size_distribution': {}
        }
        
        # Key directories to monitor
        directories = [
            'claude/context', 'claude/agents', 'claude/tools', 
            'claude/commands', 'claude/hooks', 'claude/data'
        ]
        
        for directory in directories:
            if Path(directory).exists():
                files = list(Path(directory).rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                structure['directories'][directory] = {
                    'file_count': file_count,
                    'total_size': sum(f.stat().st_size for f in files if f.is_file()),
                    'subdirectories': len([f for f in files if f.is_dir()])
                }
                structure['total_files'] += file_count
        
        return structure
    
    def check_critical_files(self) -> Dict:
        """Check integrity of critical system files"""
        results = {}
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                file_stat = Path(file_path).stat()
                results[file_path] = {
                    'exists': True,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'readable': self.test_file_readability(file_path)
                }
            else:
                results[file_path] = {
                    'exists': False,
                    'size': 0,
                    'modified': None,
                    'readable': False
                }
        
        return results
    
    def test_file_readability(self, file_path: str) -> bool:
        """Test if file can be read successfully"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                return len(content) > 0
        except OSError:
            return False
    
    def test_context_loading(self) -> Dict:
        """Test UFC context loading system"""
        result = {
            'ufc_accessible': False,
            'core_files_loadable': False,
            'smart_loading_functional': False,
            'errors': []
        }
        
        try:
            # Test UFC system file access
            ufc_file = Path('claude/context/core/ufc_system.md')
            if ufc_file.exists():
                result['ufc_accessible'] = True
            else:
                result['errors'].append("UFC system file not found")
            
            # Test core file loading
            all_core_accessible = True
            for file_path in self.critical_files:
                if not Path(file_path).exists() or not self.test_file_readability(file_path):
                    all_core_accessible = False
                    result['errors'].append(f"Core file not accessible: {file_path}")
            
            result['core_files_loadable'] = all_core_accessible
            
            # Test smart loading system
            smart_loading_file = Path('claude/context/core/smart_context_loading.md')
            if smart_loading_file.exists() and self.test_file_readability(str(smart_loading_file)):
                result['smart_loading_functional'] = True
            else:
                result['errors'].append("Smart context loading system not functional")
        
        except Exception as e:
            result['errors'].append(f"Context loading test failed: {e}")
        
        return result
    
    def test_agent_discovery(self) -> Dict:
        """Test agent discovery and accessibility"""
        result = {
            'agents_directory_exists': False,
            'agents_discoverable': 0,
            'agents_accessible': 0,
            'total_agents': 0,
            'errors': []
        }
        
        try:
            agents_dir = Path('claude/agents')
            if agents_dir.exists():
                result['agents_directory_exists'] = True
                
                agent_files = list(agents_dir.glob('*.md'))
                result['total_agents'] = len(agent_files)
                
                for agent_file in agent_files:
                    if agent_file.exists():
                        result['agents_discoverable'] += 1
                        
                        if self.test_file_readability(str(agent_file)):
                            result['agents_accessible'] += 1
                        else:
                            result['errors'].append(f"Agent not readable: {agent_file.name}")
            else:
                result['errors'].append("Agents directory not found")
        
        except Exception as e:
            result['errors'].append(f"Agent discovery test failed: {e}")
        
        return result
    
    def test_tool_accessibility(self) -> Dict:
        """Test tool accessibility and functionality"""
        result = {
            'tools_directory_exists': False,
            'tools_discoverable': 0,
            'tools_executable': 0,
            'total_tools': 0,
            'errors': []
        }
        
        try:
            tools_dir = Path('claude/tools')
            if tools_dir.exists():
                result['tools_directory_exists'] = True
                
                tool_files = list(tools_dir.glob('*.py'))
                result['total_tools'] = len(tool_files)
                
                for tool_file in tool_files:
                    if tool_file.exists():
                        result['tools_discoverable'] += 1
                        
                        # Test basic executability (syntax check)
                        try:
                            subprocess.run([
                                'python3', '-m', 'py_compile', str(tool_file)
                            ], check=True, capture_output=True)
                            result['tools_executable'] += 1
                        except subprocess.CalledProcessError:
                            result['errors'].append(f"Tool syntax error: {tool_file.name}")
            else:
                result['errors'].append("Tools directory not found")
        
        except Exception as e:
            result['errors'].append(f"Tool accessibility test failed: {e}")
        
        return result
    
    def map_dependencies(self) -> Dict:
        """Map file dependencies across the system"""
        dependencies = {
            'total_references': 0,
            'file_references': {},
            'broken_references': [],
            'critical_dependencies': []
        }
        
        try:
            # Scan for file references
            reference_patterns = [
                r'claude/[a-zA-Z0-9_/.-]+\.(?:md|py)',
                r'[a-zA-Z0-9_/.-]+\.(?:md|py)',
            ]
            
            # Search in key files
            search_dirs = ['claude/context', 'claude/agents', 'claude/tools', 'claude/commands']
            
            for search_dir in search_dirs:
                if Path(search_dir).exists():
                    for file_path in Path(search_dir).rglob('*.md'):
                        references = self.find_file_references(file_path)
                        if references:
                            dependencies['file_references'][str(file_path)] = references
                            dependencies['total_references'] += len(references)
                            
                            # Check if references are valid
                            for ref in references:
                                if not Path(ref).exists():
                                    dependencies['broken_references'].append({
                                        'source': str(file_path),
                                        'missing_reference': ref
                                    })
        
        except Exception as e:
            dependencies['error'] = f"Dependency mapping failed: {e}"
        
        return dependencies
    
    def find_file_references(self, file_path: Path) -> List[str]:
        """Find file references within a file"""
        references = []
        
        try:
            content = file_path.read_text()
            
            # Look for common file reference patterns
            import re
            patterns = [
                r'claude/[a-zA-Z0-9_/.-]+\.(?:md|py)',  # Claude file paths
                r'`[a-zA-Z0-9_/.-]+\.(?:md|py)`',        # Backtick file references
                r'\[[^\]]+\]\([a-zA-Z0-9_/.-]+\.(?:md|py)\)',  # Markdown links
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the match
                    clean_match = match.strip('`[]()').strip()
                    if clean_match and clean_match not in references:
                        references.append(clean_match)
        
        except Exception:
            pass  # Skip files that can't be read
        
        return references
    
    def get_git_status(self) -> Dict:
        """Get git repository status"""
        git_status = {
            'is_repo': False,
            'clean_working_directory': False,
            'current_branch': None,
            'uncommitted_changes': 0,
            'error': None
        }
        
        try:
            # Check if git repo
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                git_status['is_repo'] = True
                
                # Get current branch
                branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                             capture_output=True, text=True)
                if branch_result.returncode == 0:
                    git_status['current_branch'] = branch_result.stdout.strip()
                
                # Check for uncommitted changes
                status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                             capture_output=True, text=True)
                if status_result.returncode == 0:
                    changes = [line for line in status_result.stdout.strip().split('\n') if line]
                    git_status['uncommitted_changes'] = len(changes)
                    git_status['clean_working_directory'] = len(changes) == 0
        
        except Exception as e:
            git_status['error'] = str(e)
        
        return git_status
    
    def compare_with_baseline(self, current_check: Dict) -> Dict:
        """Compare current system state with baseline"""
        if not Path(self.baseline_file).exists():
            return {'error': 'No baseline found. Create baseline first.'}
        
        try:
            with open(self.baseline_file, 'r') as f:
                baseline = json.load(f)
        except Exception as e:
            return {'error': f'Cannot load baseline: {e}'}
        
        comparison = {
            'baseline_date': baseline.get('created_date'),
            'comparison_date': datetime.now().isoformat(),
            'changes_detected': [],
            'critical_changes': [],
            'health_status': 'healthy'
        }
        
        # Compare critical files
        baseline_critical = baseline.get('critical_files', {})
        current_critical = current_check.get('critical_files', {})
        
        for file_path in self.critical_files:
            baseline_file = baseline_critical.get(file_path, {})
            current_file = current_critical.get(file_path, {})
            
            if baseline_file.get('exists') and not current_file.get('exists'):
                comparison['critical_changes'].append(f"Critical file missing: {file_path}")
                comparison['health_status'] = 'critical'
            elif baseline_file.get('size', 0) != current_file.get('size', 0):
                comparison['changes_detected'].append(f"File size changed: {file_path}")
        
        # Compare file structure
        baseline_structure = baseline.get('file_structure', {})
        current_structure = current_check.get('file_structure', {})
        
        baseline_total = baseline_structure.get('total_files', 0)
        current_total = current_structure.get('total_files', 0)
        
        if abs(current_total - baseline_total) > (baseline_total * 0.1):  # >10% change
            comparison['changes_detected'].append(
                f"Significant file count change: {baseline_total} → {current_total}"
            )
        
        # Compare context loading
        baseline_context = baseline.get('context_loading', {})
        current_context = current_check.get('context_loading', {})
        
        if baseline_context.get('core_files_loadable') and not current_context.get('core_files_loadable'):
            comparison['critical_changes'].append("Context loading system degraded")
            comparison['health_status'] = 'critical'
        
        # Determine overall health
        if comparison['critical_changes']:
            comparison['health_status'] = 'critical'
        elif len(comparison['changes_detected']) > 5:
            comparison['health_status'] = 'warning'
        
        return comparison
    
    def run_health_check(self, check_type: str = 'full') -> Dict:
        """Run comprehensive health check"""
        health_check = {
            'check_type': check_type,
            'check_date': datetime.now().isoformat(),
            'file_structure': self.scan_file_structure(),
            'critical_files': self.check_critical_files(),
            'context_loading': self.test_context_loading(),
            'agent_discovery': self.test_agent_discovery(),
            'tool_accessibility': self.test_tool_accessibility(),
            'git_status': self.get_git_status(),
            'overall_health': 'healthy',
            'critical_issues': [],
            'warnings': []
        }
        
        # Analyze results for issues
        # Critical file issues
        for file_path, file_info in health_check['critical_files'].items():
            if not file_info['exists']:
                health_check['critical_issues'].append(f"Critical file missing: {file_path}")
            elif not file_info['readable']:
                health_check['critical_issues'].append(f"Critical file unreadable: {file_path}")
        
        # Context loading issues
        context_result = health_check['context_loading']
        if not context_result['core_files_loadable']:
            health_check['critical_issues'].append("Core files not loadable")
        if not context_result['ufc_accessible']:
            health_check['critical_issues'].append("UFC system not accessible")
        
        # Agent issues
        agent_result = health_check['agent_discovery']
        if not agent_result['agents_directory_exists']:
            health_check['warnings'].append("Agents directory missing")
        elif agent_result['agents_accessible'] < agent_result['agents_discoverable']:
            health_check['warnings'].append("Some agents not accessible")
        
        # Tool issues
        tool_result = health_check['tool_accessibility']
        if not tool_result['tools_directory_exists']:
            health_check['warnings'].append("Tools directory missing")
        elif tool_result['tools_executable'] < tool_result['tools_discoverable']:
            health_check['warnings'].append("Some tools have syntax errors")
        
        # Determine overall health
        if health_check['critical_issues']:
            health_check['overall_health'] = 'critical'
        elif health_check['warnings']:
            health_check['overall_health'] = 'warning'
        
        # Record in database
        self.record_health_check(check_type, health_check['overall_health'], health_check)
        
        return health_check
    
    def record_health_check(self, check_type: str, status: str, details: Dict):
        """Record health check in database"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_checks (check_date, check_type, status, details)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            check_type,
            status,
            json.dumps(details)
        ))
        
        conn.commit()
        conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 maia_system_health_checker.py <command>")
        print("Commands:")
        print("  baseline             - Create system baseline")
        print("  check               - Run health check")
        print("  compare-baseline    - Compare current state with baseline")
        print("  quick-check         - Run quick health validation")
        print("  full-validation     - Run comprehensive validation")
        print("  status              - Show current system health status")
        return
    
    command = sys.argv[1]
    checker = MaiaSystemHealthChecker()
    
    if command == 'baseline':
        print("📊 Creating system baseline...")
        baseline = checker.create_baseline()
        print("✅ Baseline created successfully")
        print(f"   Total files: {baseline['file_structure']['total_files']}")
        print(f"   Critical files: {len([f for f in baseline['critical_files'].values() if f['exists']])}/{len(checker.critical_files)}")
        print(f"   Context loading: {'✅' if baseline['context_loading']['core_files_loadable'] else '❌'}")
        print(f"   Agents: {baseline['agent_discovery']['agents_accessible']}/{baseline['agent_discovery']['total_agents']}")
        print(f"   Tools: {baseline['tool_accessibility']['tools_executable']}/{baseline['tool_accessibility']['total_tools']}")
    
    elif command == 'check':
        print("🔍 Running system health check...")
        health = checker.run_health_check()
        
        status_emoji = {'healthy': '✅', 'warning': '⚠️', 'critical': '❌'}
        print(f"Overall Health: {status_emoji[health['overall_health']]} {health['overall_health'].upper()}")
        
        if health['critical_issues']:
            print("\n❌ Critical Issues:")
            for issue in health['critical_issues']:
                print(f"   • {issue}")
        
        if health['warnings']:
            print("\n⚠️ Warnings:")
            for warning in health['warnings']:
                print(f"   • {warning}")
        
        if health['overall_health'] == 'healthy':
            print("\n🎉 System is healthy and fully functional")
    
    elif command == 'compare-baseline':
        print("📊 Comparing with baseline...")
        health = checker.run_health_check()
        comparison = checker.compare_with_baseline(health)
        
        if 'error' in comparison:
            print(f"❌ {comparison['error']}")
            return
        
        print(f"Baseline: {comparison['baseline_date'][:10]}")
        print(f"Current:  {comparison['comparison_date'][:10]}")
        print(f"Health:   {comparison['health_status'].upper()}")
        
        if comparison['critical_changes']:
            print("\n❌ Critical Changes:")
            for change in comparison['critical_changes']:
                print(f"   • {change}")
        
        if comparison['changes_detected']:
            print("\n📝 Changes Detected:")
            for change in comparison['changes_detected']:
                print(f"   • {change}")
        
        if not comparison['critical_changes'] and not comparison['changes_detected']:
            print("\n✅ No significant changes detected")
    
    elif command == 'quick-check':
        print("⚡ Running quick health check...")
        health = checker.run_health_check('quick')
        
        # Show just the essentials
        context_ok = health['context_loading']['core_files_loadable']
        agents_ok = health['agent_discovery']['agents_directory_exists']
        tools_ok = health['tool_accessibility']['tools_directory_exists']
        
        print(f"Context Loading: {'✅' if context_ok else '❌'}")
        print(f"Agent Discovery: {'✅' if agents_ok else '❌'}")
        print(f"Tool Access:     {'✅' if tools_ok else '❌'}")
        
        if health['critical_issues']:
            print(f"\n❌ {len(health['critical_issues'])} critical issues detected")
            return 1
        else:
            print("\n✅ Quick check passed")
            return 0
    
    elif command == 'full-validation':
        print("🔍 Running full system validation...")
        health = checker.run_health_check('full_validation')
        
        print("\n📊 Detailed Results:")
        print(f"   Critical Files: {len([f for f in health['critical_files'].values() if f['exists']])}/{len(checker.critical_files)} accessible")
        print(f"   Context System: {'Functional' if health['context_loading']['core_files_loadable'] else 'Broken'}")
        print(f"   Agents: {health['agent_discovery']['agents_accessible']}/{health['agent_discovery']['total_agents']} accessible")
        print(f"   Tools: {health['tool_accessibility']['tools_executable']}/{health['tool_accessibility']['total_tools']} executable")
        
        if health['overall_health'] == 'critical':
            print("\n❌ SYSTEM CRITICAL - Implementation should not proceed")
            return 1
        elif health['overall_health'] == 'warning':
            print("\n⚠️ WARNINGS DETECTED - Proceed with caution")
            return 2
        else:
            print("\n✅ SYSTEM HEALTHY - Safe to proceed with implementation")
            return 0
    
    elif command == 'status':
        # Quick status without full check
        if Path(checker.baseline_file).exists():
            print("📊 System baseline exists")
        else:
            print("⚠️ No system baseline - run 'baseline' command first")
        
        # Quick critical file check
        missing_critical = []
        for file_path in checker.critical_files:
            if not Path(file_path).exists():
                missing_critical.append(file_path)
        
        if missing_critical:
            print(f"❌ {len(missing_critical)} critical files missing")
            for file_path in missing_critical:
                print(f"   • {file_path}")
        else:
            print("✅ All critical files present")

if __name__ == "__main__":
    sys.exit(main() or 0)