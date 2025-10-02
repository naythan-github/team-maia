#!/usr/bin/env python3
"""
Archive Consolidator - Phase 8 Component
Systematic consolidation of scattered archive directories
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class ArchiveConsolidator:
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.standard_archive = self.repo_path / "archive/historical/2025"
        self.backup_dir = self.repo_path / "claude/data/governance_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive patterns to identify scattered archives
        self.archive_patterns = [
            '*archive*', '*backup*', '*old*', '*deprecated*', 
            '*_20[0-9][0-9]*', 'governance_backups', 'backups-pre-*',
            'maia_backup_*', 'consolidated_*', 'archived_*'
        ]
        
        # Directories that should NOT be consolidated (but we'll look inside them)
        self.protected_directories = [
            'archive/historical',  # Standard location
            '.git'
        ]
    
    def scan_scattered_archives(self) -> Dict:
        """Scan repository for scattered archive directories"""
        scattered_archives = []
        total_size = 0
        total_files = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            relative_root = Path(root).relative_to(self.repo_path)
            
            # Skip protected directories
            if any(str(relative_root).startswith(protected) for protected in self.protected_directories):
                continue
            
            for dir_name in dirs:
                if self._is_archive_directory(dir_name):
                    archive_path = Path(root) / dir_name
                    relative_path = archive_path.relative_to(self.repo_path)
                    
                    # Calculate size and file count
                    size = 0
                    file_count = 0
                    try:
                        for file_path in archive_path.rglob('*'):
                            if file_path.is_file():
                                size += file_path.stat().st_size
                                file_count += 1
                    except PermissionError:
                        continue
                    
                    archive_info = {
                        'name': dir_name,
                        'path': str(relative_path),
                        'full_path': str(archive_path),
                        'size_bytes': size,
                        'size_mb': round(size / 1024 / 1024, 2),
                        'file_count': file_count,
                        'parent_dir': str(relative_root),
                        'consolidation_target': self._determine_consolidation_target(dir_name, relative_path)
                    }
                    
                    scattered_archives.append(archive_info)
                    total_size += size
                    total_files += file_count
        
        return {
            'scattered_archives': scattered_archives,
            'total_archives': len(scattered_archives),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'total_files': total_files,
            'standard_archive_location': str(self.standard_archive),
            'timestamp': datetime.now().isoformat()
        }
    
    def _is_archive_directory(self, dir_name: str) -> bool:
        """Check if directory name matches archive patterns"""
        dir_lower = dir_name.lower()
        
        for pattern in self.archive_patterns:
            if self._matches_pattern(dir_lower, pattern.lower()):
                return True
        
        return False
    
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
    
    def _determine_consolidation_target(self, dir_name: str, relative_path: Path) -> str:
        """Determine appropriate consolidation target directory"""
        dir_lower = dir_name.lower()
        
        # Specific consolidation rules
        if 'governance' in dir_lower:
            return 'archive/historical/2025/governance'
        elif 'backup' in dir_lower and 'root_cleanup' in dir_lower:
            return 'archive/historical/2025/root_cleanup_backups'
        elif 'maia_backup' in dir_lower:
            return 'archive/historical/2025/maia_backups'
        elif 'confluence' in dir_lower:
            return 'archive/historical/2025/confluence'
        elif 'tools' in dir_lower:
            return 'archive/historical/2025/tools'
        elif 'contact' in dir_lower:
            return 'archive/historical/2025/contact_systems'
        else:
            return 'archive/historical/2025/general'
    
    def generate_consolidation_plan(self, scan_results: Dict) -> Dict:
        """Generate consolidation execution plan"""
        actions = []
        target_dirs = set()
        
        for archive in scan_results['scattered_archives']:
            target_dir = archive['consolidation_target']
            target_dirs.add(target_dir)
            
            action = {
                'type': 'consolidate_archive',
                'source': archive['path'],
                'target_dir': target_dir,
                'archive_name': archive['name'],
                'size_mb': archive['size_mb'],
                'file_count': archive['file_count'],
                'safety_checks': self._generate_safety_checks(archive)
            }
            actions.append(action)
        
        return {
            'actions': actions,
            'total_actions': len(actions),
            'target_directories': sorted(list(target_dirs)),
            'estimated_space_consolidated': scan_results['total_size_mb'],
            'safety_backup_required': True,
            'dependency_check_required': True
        }
    
    def _generate_safety_checks(self, archive: Dict) -> List[str]:
        """Generate safety checks for archive consolidation"""
        checks = []
        
        # Check for recent modifications
        archive_path = Path(archive['full_path'])
        if archive_path.exists():
            latest_mod = 0
            for file_path in archive_path.rglob('*'):
                if file_path.is_file():
                    latest_mod = max(latest_mod, file_path.stat().st_mtime)
            
            days_since_mod = (datetime.now().timestamp() - latest_mod) / 86400
            if days_since_mod < 30:
                checks.append(f"Recent modifications: {int(days_since_mod)} days ago")
        
        # Check for large files
        if archive['size_mb'] > 100:
            checks.append(f"Large archive: {archive['size_mb']} MB")
        
        # Check for many files
        if archive['file_count'] > 1000:
            checks.append(f"Many files: {archive['file_count']} files")
        
        return checks
    
    def execute_consolidation(self, plan: Dict, dry_run: bool = True) -> Dict:
        """Execute archive consolidation plan"""
        if not dry_run:
            # Create backup timestamp
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"archive_consolidation_backup_{backup_timestamp}"
            backup_path.mkdir(exist_ok=True)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'actions_attempted': 0,
            'actions_successful': 0,
            'actions_failed': 0,
            'space_consolidated_mb': 0,
            'files_moved': 0,
            'errors': []
        }
        
        for action in plan['actions']:
            results['actions_attempted'] += 1
            
            try:
                success = self._execute_consolidation_action(
                    action, dry_run, backup_path if not dry_run else None
                )
                
                if success:
                    results['actions_successful'] += 1
                    results['space_consolidated_mb'] += action['size_mb']
                    results['files_moved'] += action['file_count']
                else:
                    results['actions_failed'] += 1
                    
            except Exception as e:
                results['actions_failed'] += 1
                results['errors'].append(f"Error consolidating {action['source']}: {str(e)}")
        
        return results
    
    def _execute_consolidation_action(self, action: Dict, dry_run: bool, backup_path: Path = None) -> bool:
        """Execute single consolidation action"""
        source_path = self.repo_path / action['source']
        target_dir = self.repo_path / action['target_dir']
        target_path = target_dir / action['archive_name']
        
        if dry_run:
            print(f"DRY RUN: Would consolidate {source_path} -> {target_path}")
            return True
        
        try:
            # Create backup if enabled
            if backup_path:
                backup_target = backup_path / action['archive_name']
                shutil.copytree(source_path, backup_target, dirs_exist_ok=True)
                print(f"📦 Backed up {action['archive_name']}")
            
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle naming conflicts
            if target_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_path = target_dir / f"{action['archive_name']}_{timestamp}"
            
            # Move archive
            shutil.move(str(source_path), str(target_path))
            print(f"✅ Consolidated {action['source']} -> {action['target_dir']}/{target_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to consolidate {action['source']}: {e}")
            return False
    
    def validate_consolidation(self) -> Dict:
        """Validate consolidation results"""
        post_scan = self.scan_scattered_archives()
        
        # Check standard archive structure
        standard_structure = {}
        if self.standard_archive.exists():
            for item in self.standard_archive.iterdir():
                if item.is_dir():
                    file_count = len(list(item.rglob('*')))
                    size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    standard_structure[item.name] = {
                        'file_count': file_count,
                        'size_mb': round(size / 1024 / 1024, 2)
                    }
        
        return {
            'remaining_scattered_archives': post_scan['total_archives'],
            'standard_archive_structure': standard_structure,
            'consolidation_success': post_scan['total_archives'] < 5,  # Allow a few remaining
            'timestamp': datetime.now().isoformat()
        }

def main():
    import sys
    
    consolidator = ArchiveConsolidator()
    
    if len(sys.argv) < 2:
        print("Archive Consolidator Tool")
        print("Commands:")
        print("  scan      - Scan for scattered archive directories")
        print("  plan      - Generate consolidation plan")
        print("  execute   - Execute consolidation (dry run)")
        print("  execute --live - Execute consolidation (live mode)")
        print("  validate  - Validate consolidation results")
        return
    
    command = sys.argv[1]
    
    if command == "scan":
        results = consolidator.scan_scattered_archives()
        print(json.dumps(results, indent=2))
        
    elif command == "plan":
        scan_results = consolidator.scan_scattered_archives()
        plan = consolidator.generate_consolidation_plan(scan_results)
        print(json.dumps(plan, indent=2))
        
    elif command == "execute":
        live_mode = "--live" in sys.argv
        scan_results = consolidator.scan_scattered_archives()
        plan = consolidator.generate_consolidation_plan(scan_results)
        
        print(f"🗂️  Archive Consolidation - {'LIVE MODE' if live_mode else 'DRY RUN'}")
        print(f"📊 Scattered archives: {scan_results['total_archives']}")
        print(f"💾 Total size: {scan_results['total_size_mb']} MB")
        print(f"📦 Actions planned: {len(plan['actions'])}")
        
        if live_mode:
            print("⚠️  Executing live consolidation (auto-confirmed)")
        
        results = consolidator.execute_consolidation(plan, dry_run=not live_mode)
        print(json.dumps(results, indent=2))
        
        if live_mode:
            # Validate results
            validation = consolidator.validate_consolidation()
            print(f"\n✅ Consolidation complete!")
            print(f"📊 Remaining scattered: {validation['remaining_scattered_archives']}")
            print(f"🎯 Success: {'Yes' if validation['consolidation_success'] else 'No'}")
            
    elif command == "validate":
        validation = consolidator.validate_consolidation()
        print(json.dumps(validation, indent=2))

if __name__ == "__main__":
    main()