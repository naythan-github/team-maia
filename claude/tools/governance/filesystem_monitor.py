#!/usr/bin/env python3
"""
File System Monitor - Phase 2 Component
Real-time monitoring for file sprawl prevention
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SprawlEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
        self.violations = []
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.check_file_placement(event.src_path, "created")
    
    def on_moved(self, event):
        if not event.is_directory:
            self.monitor.check_file_placement(event.dest_path, "moved")

class FileSystemMonitor:
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.observer = Observer()
        self.violations_log = []
        self.policy_rules = self._load_policy_rules()
        
    def _load_policy_rules(self) -> Dict:
        """Load file placement policy rules"""
        return {
            "max_root_files": 20,
            "forbidden_root_extensions": [".tmp", ".log", ".backup"],
            "required_tool_categories": ["core", "automation", "research", "communication", "monitoring", "data", "security", "business"],
            "forbidden_directories": ["temp", "tmp", "backup", "old", "legacy"],
            "archive_locations": ["archive/", "claude/tools/archive/"]
        }
    
    def start_monitoring(self):
        """Start real-time file system monitoring"""
        print("🔍 Starting file system monitoring...")
        
        event_handler = SprawlEventHandler(self)
        self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
        self.observer.start()
        
        print(f"✅ Monitoring active for: {self.repo_path}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        self.observer.stop()
        self.observer.join()
        print("🛑 File system monitoring stopped")
    
    def check_file_placement(self, file_path: str, action: str = "check") -> Dict:
        """Check if file placement violates sprawl prevention rules"""
        path = Path(file_path)
        
        try:
            relative_path = path.relative_to(self.repo_path)
        except ValueError:
            # File outside repository, ignore
            return {"file_path": str(path), "violations": [], "compliant": True}
        
        violations = []
        
        # Check root directory files
        if len(relative_path.parts) == 1:
            if path.suffix in self.policy_rules["forbidden_root_extensions"]:
                violations.append({
                    "type": "forbidden_root_extension",
                    "severity": "high",
                    "message": f"Forbidden file extension in root: {path.suffix}"
                })
        
        # Check for forbidden directory names
        for part in relative_path.parts:
            if part.lower() in self.policy_rules["forbidden_directories"]:
                violations.append({
                    "type": "forbidden_directory",
                    "severity": "medium", 
                    "message": f"Forbidden directory name: {part}"
                })
        
        # Log violations
        if violations:
            violation_record = {
                "timestamp": datetime.now().isoformat(),
                "file_path": str(relative_path),
                "action": action,
                "violations": violations
            }
            self.violations_log.append(violation_record)
            self._alert_violation(violation_record)
        
        return {
            "file_path": str(relative_path),
            "violations": violations,
            "compliant": len(violations) == 0
        }
    
    def _alert_violation(self, violation: Dict):
        """Alert about policy violation"""
        severity = violation["violations"][0]["severity"]
        
        if severity == "high":
            print(f"🚨 HIGH SEVERITY VIOLATION: {violation['file_path']}")
        else:
            print(f"⚠️  {severity.upper()} VIOLATION: {violation['file_path']}")
        
        for v in violation["violations"]:
            print(f"   📋 {v['message']}")
    
    def get_violations_summary(self) -> Dict:
        """Get summary of detected violations"""
        total_violations = len(self.violations_log)
        high_severity = sum(1 for v in self.violations_log 
                           if any(viol["severity"] == "high" for viol in v["violations"]))
        
        return {
            "total_violations": total_violations,
            "high_severity_count": high_severity,
            "recent_violations": self.violations_log[-10:] if self.violations_log else []
        }
    
    def scan_repository(self) -> Dict:
        """One-time scan of entire repository"""
        print("🔍 Scanning repository for policy violations...")
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "total_files_scanned": 0,
            "violations_found": 0,
            "files_with_violations": []
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git directory
            if '.git' in Path(root).parts:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                scan_results["total_files_scanned"] += 1
                
                check_result = self.check_file_placement(file_path, "scan")
                
                if not check_result["compliant"]:
                    scan_results["violations_found"] += 1
                    scan_results["files_with_violations"].append({
                        "file": check_result["file_path"],
                        "violations": check_result["violations"]
                    })
        
        return scan_results

def main():
    monitor = FileSystemMonitor()
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "scan":
        # One-time scan mode
        results = monitor.scan_repository()
        print(f"\n📊 Scan Results:")
        print(f"   Files Scanned: {results['total_files_scanned']}")
        print(f"   Violations Found: {results['violations_found']}")
        
        if results['violations_found'] > 0:
            print(f"\n⚠️  Files with Violations:")
            for item in results['files_with_violations'][:10]:  # Show first 10
                print(f"   📄 {item['file']}")
                for violation in item['violations']:
                    print(f"      🔴 {violation['message']}")
        else:
            print("   ✅ No policy violations detected")
    else:
        # Real-time monitoring mode
        print("🎯 Real-time monitoring mode")
        print("   Press Ctrl+C to stop monitoring")
        monitor.start_monitoring()

if __name__ == "__main__":
    main()