#!/usr/bin/env python3
"""
Test Before and After Changes Protocol
Ensures all system modifications are tested before and after implementation
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class TestProtocol:
    def __init__(self):
        self.test_results = {
            'pre_change': {},
            'post_change': {},
            'comparison': {}
        }
        
    def run_core_system_tests(self, phase="pre_change"):
        """Run comprehensive core system tests"""
        print(f"🧪 Running {phase} system tests...")
        
        tests = {
            'progress_tracker': self.test_progress_tracker,
            'health_checker': self.test_health_checker,
            'backup_manager': self.test_backup_manager,
            'file_structure': self.test_file_structure,
            'core_files': self.test_core_files
        }
        
        results = {}
        for test_name, test_func in tests.items():
            try:
                result = test_func()
                results[test_name] = {
                    'success': result,
                    'timestamp': datetime.now().isoformat()
                }
                status = "✅" if result else "❌"
                print(f"  {status} {test_name}")
            except Exception as e:
                results[test_name] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"  ❌ {test_name} - ERROR: {e}")
        
        self.test_results[phase] = results
        return results
    
    def test_progress_tracker(self):
        """Test anti-sprawl progress tracker"""
        try:
            result = subprocess.run([
                'python3', 'claude/tools/anti_sprawl_progress_tracker.py', 'status'
            ], capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and 'Implementation Progress' in result.stdout
        except:
            return False
    
    def test_health_checker(self):
        """Test system health checker"""
        try:
            result = subprocess.run([
                'python3', 'claude/tools/maia_system_health_checker.py', '--help'
            ], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def test_backup_manager(self):
        """Test backup manager"""
        try:
            result = subprocess.run([
                'python3', 'claude/tools/system_backup_manager.py', 'list'
            ], capture_output=True, text=True, timeout=10)
            # Return code should be 0 and should show either checkpoints or "No checkpoints found"
            return result.returncode == 0 and ('checkpoints' in result.stdout.lower() or 'no checkpoints' in result.stdout.lower())
        except:
            return False
    
    def test_file_structure(self):
        """Test core file structure integrity"""
        critical_paths = [
            'claude/context/core',
            'claude/tools',
            'claude/agents',
            'claude/commands'
        ]
        
        for path in critical_paths:
            if not Path(path).exists():
                return False
        return True
    
    def test_core_files(self):
        """Test core configuration files"""
        core_files = [
            'claude/context/ufc_system.md',
            'claude/context/core/anti_sprawl_master_implementation_plan.md'
        ]
        
        for file_path in core_files:
            path = Path(file_path)
            if not path.exists() or path.stat().st_size == 0:
                return False
        return True
    
    def compare_results(self):
        """Compare pre and post change results"""
        if not self.test_results['pre_change'] or not self.test_results['post_change']:
            print("❌ Cannot compare - missing test results")
            return False
        
        print("\n📊 Comparing Pre/Post Change Results:")
        all_same = True
        
        for test_name in self.test_results['pre_change']:
            pre_success = self.test_results['pre_change'][test_name]['success']
            post_success = self.test_results['post_change'].get(test_name, {}).get('success', False)
            
            if pre_success and post_success:
                print(f"  ✅ {test_name}: Working before and after")
            elif not pre_success and not post_success:
                print(f"  ⚠️  {test_name}: Broken before and after")
            elif pre_success and not post_success:
                print(f"  ❌ {test_name}: REGRESSION - worked before, broken after")
                all_same = False
            elif not pre_success and post_success:
                print(f"  🎉 {test_name}: IMPROVEMENT - fixed by changes")
        
        return all_same
    
    def save_results(self):
        """Save test results to file"""
        results_file = Path('claude/data/test_protocol_results.json')
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📄 Test results saved to {results_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_before_after_protocol.py <command>")
        print("Commands:")
        print("  pre-change     - Run tests before making changes")
        print("  post-change    - Run tests after making changes")
        print("  compare        - Compare pre/post results")
        print("  full-cycle     - Run complete test cycle")
        return
    
    command = sys.argv[1]
    protocol = TestProtocol()
    
    # Load existing results if they exist
    results_file = Path('claude/data/test_protocol_results.json')
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                protocol.test_results = json.load(f)
        except:
            pass
    
    if command == 'pre-change':
        protocol.run_core_system_tests('pre_change')
        protocol.save_results()
        print("\n✅ Pre-change testing complete. Make your changes, then run 'post-change'")
    
    elif command == 'post-change':
        if not protocol.test_results.get('pre_change'):
            print("❌ No pre-change results found. Run 'pre-change' first.")
            return
        
        protocol.run_core_system_tests('post_change')
        no_regressions = protocol.compare_results()
        protocol.save_results()
        
        if no_regressions:
            print("\n✅ POST-CHANGE VALIDATION: No regressions detected")
        else:
            print("\n❌ POST-CHANGE VALIDATION: REGRESSIONS DETECTED")
            sys.exit(1)
    
    elif command == 'compare':
        if protocol.test_results.get('pre_change') and protocol.test_results.get('post_change'):
            protocol.compare_results()
        else:
            print("❌ Missing pre or post change results")
    
    elif command == 'full-cycle':
        print("🔄 Running full test cycle...")
        protocol.run_core_system_tests('pre_change')
        print("\n⏸️  Ready for changes. Run with 'post-change' after modifications")
        protocol.save_results()

if __name__ == "__main__":
    main()