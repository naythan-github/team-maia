#!/usr/bin/env python3
"""
Remediation Engine - Phase 3 Component
Automated fix system for repository sprawl violations
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class RemediationEngine:
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.safe_mode = True
        self.backup_dir = self.repo_path / "claude/data/governance_backups"
        self.remediation_log = []
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_and_fix(self, violations: List[Dict]) -> Dict:
        """Analyze violations and apply appropriate fixes"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "violations_processed": 0,
            "successful_fixes": 0,
            "manual_review_required": 0,
            "failed_fixes": 0,
            "actions_taken": []
        }
        
        for violation in violations:
            fix_result = self._fix_violation(violation)
            results["violations_processed"] += 1
            
            if fix_result["status"] == "fixed":
                results["successful_fixes"] += 1
            elif fix_result["status"] == "manual_review":
                results["manual_review_required"] += 1
            else:
                results["failed_fixes"] += 1
            
            results["actions_taken"].append(fix_result)
        
        return results
    
    def _fix_violation(self, violation: Dict) -> Dict:
        """Fix individual violation"""
        violation_type = violation.get("type", "unknown")
        file_path = Path(violation.get("file_path", ""))
        
        fix_result = {
            "violation_type": violation_type,
            "file_path": str(file_path),
            "status": "failed",
            "action": "none",
            "backup_created": False,
            "details": ""
        }
        
        try:
            if violation_type == "forbidden_root_extension":
                return self._fix_forbidden_root_file(file_path, fix_result)
            elif violation_type == "misplaced_archive":
                return self._fix_misplaced_archive(file_path, fix_result)
            elif violation_type == "root_sprawl":
                return self._fix_root_sprawl(file_path, fix_result)
            else:
                fix_result["status"] = "manual_review"
                fix_result["details"] = f"Unknown violation type: {violation_type}"
                
        except Exception as e:
            fix_result["status"] = "failed"
            fix_result["details"] = f"Error during fix: {str(e)}"
        
        return fix_result
    
    def _fix_forbidden_root_file(self, file_path: Path, fix_result: Dict) -> Dict:
        """Fix forbidden file in root directory"""
        abs_path = self.repo_path / file_path
        
        if not abs_path.exists():
            fix_result["status"] = "already_resolved"
            fix_result["details"] = "File no longer exists"
            return fix_result
        
        # Create backup
        backup_path = self._create_backup(abs_path)
        fix_result["backup_created"] = backup_path is not None
        
        # Determine appropriate action based on file type
        if abs_path.suffix in [".tmp", ".log"]:
            # Safe to delete temporary files
            abs_path.unlink()
            fix_result["status"] = "fixed"
            fix_result["action"] = "deleted"
            fix_result["details"] = "Temporary file deleted safely"
        else:
            # Move to appropriate location
            target_dir = self._determine_target_directory(abs_path)
            if target_dir:
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / abs_path.name
                shutil.move(str(abs_path), str(target_path))
                fix_result["status"] = "fixed"
                fix_result["action"] = "moved"
                fix_result["details"] = f"Moved to {target_path}"
            else:
                fix_result["status"] = "manual_review"
                fix_result["action"] = "none"
                fix_result["details"] = "Could not determine appropriate location"
        
        return fix_result
    
    def _fix_misplaced_archive(self, dir_path: Path, fix_result: Dict) -> Dict:
        """Fix misplaced archive directory"""
        abs_path = self.repo_path / dir_path
        
        if not abs_path.exists():
            fix_result["status"] = "already_resolved"
            return fix_result
        
        # Move to archive directory
        archive_dir = self.repo_path / "archive/historical/2025"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = archive_dir / abs_path.name
        
        # Create backup
        backup_path = self._create_backup(abs_path)
        fix_result["backup_created"] = backup_path is not None
        
        # Move directory
        shutil.move(str(abs_path), str(target_path))
        
        fix_result["status"] = "fixed"
        fix_result["action"] = "moved_to_archive"
        fix_result["details"] = f"Moved to {target_path}"
        
        return fix_result
    
    def _fix_root_sprawl(self, file_path: Path, fix_result: Dict) -> Dict:
        """Fix root directory sprawl"""
        # This would implement logic to organize root files
        fix_result["status"] = "manual_review"
        fix_result["details"] = "Root sprawl requires manual review"
        return fix_result
    
    def _create_backup(self, source_path: Path) -> Optional[Path]:
        """Create backup of file/directory before modification"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.name}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            if source_path.is_file():
                shutil.copy2(str(source_path), str(backup_path))
            else:
                shutil.copytree(str(source_path), str(backup_path))
            
            return backup_path
        except Exception as e:
            print(f"⚠️  Backup failed for {source_path}: {e}")
            return None
    
    def _determine_target_directory(self, file_path: Path) -> Optional[Path]:
        """Determine appropriate target directory for misplaced file"""
        # Implement logic to suggest appropriate location
        # Based on file extension, content analysis, etc.
        
        if file_path.suffix == ".py":
            return self.repo_path / "claude/tools/data"
        elif file_path.suffix == ".md":
            return self.repo_path / "claude/context/knowledge"
        elif file_path.suffix in [".json", ".yaml", ".yml"]:
            return self.repo_path / "claude/data"
        
        return None
    
    def rollback_changes(self, action_id: str) -> Dict:
        """Rollback specific remediation action"""
        # Implementation for rolling back changes
        return {
            "status": "not_implemented",
            "message": "Rollback functionality to be implemented"
        }

    def fix_current_violations(self) -> Dict:
        """Find and fix current repository violations"""
        print("🔍 Scanning for current violations...")
        
        # Import filesystem monitor to detect violations
        import sys
        sys.path.append(str(self.repo_path / "claude/tools/governance"))
        
        try:
            from claude.tools.governance.filesystem_monitor import FileSystemMonitor
            monitor = FileSystemMonitor()
            scan_results = monitor.scan_repository()
            
            if scan_results["violations_found"] == 0:
                return {
                    "message": "No violations found to fix",
                    "violations_processed": 0,
                    "successful_fixes": 0
                }
            
            # Convert scan results to violation format
            violations = []
            for item in scan_results["files_with_violations"]:
                for violation in item["violations"]:
                    violations.append({
                        "type": violation["type"],
                        "file_path": item["file"],
                        "severity": violation["severity"],
                        "message": violation["message"]
                    })
            
            # Apply fixes
            print(f"📋 Found {len(violations)} violations to fix")
            return self.analyze_and_fix(violations)
            
        except ImportError:
            return {
                "error": "FileSystemMonitor not available",
                "message": "Cannot scan for violations"
            }

def main():
    """CLI interface for remediation engine"""
    engine = RemediationEngine()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == "fix":
            results = engine.fix_current_violations()
            print("\n📊 Remediation Results:")
            print(json.dumps(results, indent=2))
        
        elif command == "test":
            # Test with sample violations
            sample_violations = [
                {
                    "type": "forbidden_root_extension",
                    "file_path": "test_file.tmp",
                    "severity": "high"
                }
            ]
            
            results = engine.analyze_and_fix(sample_violations)
            print("🧪 Test Results:")
            print(json.dumps(results, indent=2))
        
        else:
            print(f"Unknown command: {command}")
    else:
        print("Remediation Engine Commands:")
        print("  fix  - Fix current repository violations")
        print("  test - Run test with sample violations")

if __name__ == "__main__":
    main()