#!/usr/bin/env python3
"""
Root Directory Cleanup Tool
Systematic cleanup of repository root to achieve target file count
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class RootDirectoryCleanup:
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.target_files = 20
        self.backup_dir = self.repo_path / "claude/data/governance_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Define organization rules
        self.organization_rules = {
            'config': {
                'patterns': ['.gitignore', '*.ini', '*.cfg', '*.conf', 'config.*', 'requirements.txt'],
                'target_dir': 'config'
            },
            'archive': {
                'patterns': ['*backup*', '*old*', '*deprecated*', '*_20[0-9][0-9]*', '*.json', '*.db'],
                'target_dir': 'archive/historical/2025'
            },
            'scripts': {
                'patterns': ['*.py', '*.sh', 'run_*', 'start_*', 'stop_*', 'cleanup_*', 'restore_*', 'test_*', 'launch_*', 'voice_*', 'dashboard', 'governance', 'rag_service*'],
                'target_dir': 'scripts'
            },
            'documentation': {
                'patterns': ['*.md'],
                'target_dir': 'docs',
                'keep_in_root': ['README.md', 'CLAUDE.md', 'SYSTEM_STATE.md']  # Essential root docs
            },
            'media': {
                'patterns': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.pdf'],
                'target_dir': 'docs/media'
            }
        }
    
    def analyze_root_directory(self) -> Dict:
        """Analyze current root directory state"""
        root_files = []
        root_dirs = []
        
        for item in self.repo_path.iterdir():
            if item.name.startswith('.'):
                continue
                
            if item.is_file():
                root_files.append({
                    'name': item.name,
                    'size': item.stat().st_size,
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    'category': self._classify_file(item.name)
                })
            elif item.is_dir():
                root_dirs.append({
                    'name': item.name,
                    'size': sum(f.stat().st_size for f in item.rglob('*') if f.is_file()),
                    'file_count': len(list(item.rglob('*'))),
                    'category': self._classify_directory(item.name)
                })
        
        return {
            'current_file_count': len(root_files),
            'current_dir_count': len(root_dirs),
            'target_file_count': self.target_files,
            'reduction_needed': max(0, len(root_files) - self.target_files),
            'files': root_files,
            'directories': root_dirs,
            'timestamp': datetime.now().isoformat()
        }
    
    def _classify_file(self, filename: str) -> str:
        """Classify file into organization category"""
        filename_lower = filename.lower()
        
        for category, rules in self.organization_rules.items():
            for pattern in rules['patterns']:
                if self._matches_pattern(filename_lower, pattern.lower()):
                    return category
        
        return 'uncategorized'
    
    def _classify_directory(self, dirname: str) -> str:
        """Classify directory for organization"""
        dirname_lower = dirname.lower()
        
        for category, rules in self.organization_rules.items():
            for pattern in rules['patterns']:
                if self._matches_pattern(dirname_lower, pattern.lower()):
                    return category
        
        return 'keep_in_root'
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Simple pattern matching with wildcards"""
        if '*' not in pattern:
            return text == pattern
        
        # Simple wildcard matching
        if pattern.startswith('*') and pattern.endswith('*'):
            return pattern[1:-1] in text
        elif pattern.startswith('*'):
            return text.endswith(pattern[1:])
        elif pattern.endswith('*'):
            return text.startswith(pattern[:-1])
        
        return text == pattern
    
    def generate_cleanup_plan(self, analysis: Dict) -> Dict:
        """Generate specific cleanup actions"""
        actions = []
        files_to_move = 0
        
        for file_info in analysis['files']:
            category = file_info['category']
            filename = file_info['name']
            
            if category != 'uncategorized' and category in self.organization_rules:
                # Check if file should stay in root
                if category == 'documentation':
                    keep_in_root = self.organization_rules[category].get('keep_in_root', [])
                    if filename in keep_in_root:
                        continue  # Skip moving essential root docs
                
                target_dir = self.organization_rules[category]['target_dir']
                
                action = {
                    'type': 'move_file',
                    'source': filename,
                    'target_dir': target_dir,
                    'category': category,
                    'size': file_info['size']
                }
                actions.append(action)
                files_to_move += 1
        
        # Handle documentation consolidation
        readme_files = [f for f in analysis['files'] if f['name'].lower().startswith('readme')]
        if len(readme_files) > 1:
            actions.append({
                'type': 'consolidate_documentation',
                'files': [f['name'] for f in readme_files],
                'target': 'README.md',
                'category': 'documentation'
            })
        
        final_file_count = analysis['current_file_count'] - files_to_move
        success_likelihood = "high" if final_file_count <= self.target_files else "medium"
        
        return {
            'actions': actions,
            'files_to_move': files_to_move,
            'estimated_final_count': final_file_count,
            'target_achieved': final_file_count <= self.target_files,
            'success_likelihood': success_likelihood,
            'backup_required': True
        }
    
    def execute_cleanup(self, plan: Dict, dry_run: bool = True) -> Dict:
        """Execute the cleanup plan"""
        if not dry_run:
            # Create backup first
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"root_cleanup_backup_{backup_timestamp}"
            backup_path.mkdir(exist_ok=True)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'actions_attempted': 0,
            'actions_successful': 0,
            'actions_failed': 0,
            'errors': []
        }
        
        for action in plan['actions']:
            results['actions_attempted'] += 1
            
            try:
                if action['type'] == 'move_file':
                    success = self._execute_move_file(action, dry_run, backup_path if not dry_run else None)
                elif action['type'] == 'consolidate_documentation':
                    success = self._execute_consolidate_docs(action, dry_run, backup_path if not dry_run else None)
                else:
                    success = False
                    results['errors'].append(f"Unknown action type: {action['type']}")
                
                if success:
                    results['actions_successful'] += 1
                else:
                    results['actions_failed'] += 1
                    
            except Exception as e:
                results['actions_failed'] += 1
                results['errors'].append(f"Error executing {action}: {str(e)}")
        
        return results
    
    def _execute_move_file(self, action: Dict, dry_run: bool, backup_path: Path = None) -> bool:
        """Execute file move action"""
        source = self.repo_path / action['source']
        target_dir = self.repo_path / action['target_dir']
        target_file = target_dir / action['source']
        
        if dry_run:
            print(f"DRY RUN: Would move {source} -> {target_file}")
            return True
        
        try:
            # Create backup
            if backup_path:
                shutil.copy2(source, backup_path / action['source'])
            
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source), str(target_file))
            print(f"✅ Moved {action['source']} -> {action['target_dir']}/")
            return True
            
        except Exception as e:
            print(f"❌ Failed to move {action['source']}: {e}")
            return False
    
    def _execute_consolidate_docs(self, action: Dict, dry_run: bool, backup_path: Path = None) -> bool:
        """Execute documentation consolidation"""
        if dry_run:
            print(f"DRY RUN: Would consolidate {action['files']} -> {action['target']}")
            return True
        
        try:
            # Create backup of all README files
            if backup_path:
                for filename in action['files']:
                    source = self.repo_path / filename
                    if source.exists():
                        shutil.copy2(source, backup_path / filename)
            
            # For now, just keep the main README.md and archive others
            main_readme = self.repo_path / "README.md"
            archive_dir = self.repo_path / "archive/historical/2025/documentation"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            for filename in action['files']:
                if filename != "README.md":
                    source = self.repo_path / filename
                    if source.exists():
                        shutil.move(str(source), str(archive_dir / filename))
                        print(f"✅ Archived {filename} -> archive/historical/2025/documentation/")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to consolidate documentation: {e}")
            return False

def main():
    import sys
    
    cleanup = RootDirectoryCleanup()
    
    if len(sys.argv) < 2:
        print("Root Directory Cleanup Tool")
        print("Commands:")
        print("  analyze  - Analyze current root directory state")
        print("  plan     - Generate cleanup plan")
        print("  execute  - Execute cleanup (dry run)")
        print("  execute --live - Execute cleanup (live mode)")
        return
    
    command = sys.argv[1]
    
    if command == "analyze":
        analysis = cleanup.analyze_root_directory()
        print(json.dumps(analysis, indent=2))
        
    elif command == "plan":
        analysis = cleanup.analyze_root_directory()
        plan = cleanup.generate_cleanup_plan(analysis)
        print(json.dumps(plan, indent=2))
        
    elif command == "execute":
        live_mode = "--live" in sys.argv
        analysis = cleanup.analyze_root_directory()
        plan = cleanup.generate_cleanup_plan(analysis)
        
        print(f"🔍 Root Directory Cleanup - {'LIVE MODE' if live_mode else 'DRY RUN'}")
        print(f"📊 Current files: {analysis['current_file_count']}")
        print(f"🎯 Target files: {cleanup.target_files}")
        print(f"📦 Actions planned: {len(plan['actions'])}")
        
        if live_mode:
            print("⚠️  Executing live cleanup (auto-confirmed)")
            # Auto-confirm for automation environments
        
        results = cleanup.execute_cleanup(plan, dry_run=not live_mode)
        print(json.dumps(results, indent=2))
        
        if live_mode:
            # Re-analyze to show results
            new_analysis = cleanup.analyze_root_directory()
            print(f"\n✅ Cleanup complete!")
            print(f"📊 Final file count: {new_analysis['current_file_count']}")
            print(f"🎯 Target achieved: {'Yes' if new_analysis['current_file_count'] <= cleanup.target_files else 'No'}")

if __name__ == "__main__":
    main()