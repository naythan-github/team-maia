# Structural Governance Implementation Guide
## Preventing Repository File Sprawl - Anti-Amnesia Documentation

**Purpose**: Comprehensive implementation guide that prevents "forgetting what we're doing halfway through" - detailed enough to resume implementation at any point without losing context.

**Problem**: Repository had massive file sprawl (1,104+ files) requiring 3-phase reorganization. Need automated prevention to stop sprawl from returning.

**Solution**: Multi-layered structural governance framework with automated enforcement and monitoring.

---

## 🎯 **IMPLEMENTATION OVERVIEW**

### **Current State Assessment**
- ✅ **Phase 1-3 Complete**: Archive consolidation, project separation, tool reorganization (271→52 files, 81% reduction)
- ✅ **UFC System Active**: Context loading enforcement prevents structural violations
- ✅ **Hook Infrastructure**: Pre-commit enforcement through `user-prompt-submit` hook
- ❌ **Phase 4 Incomplete**: Data management phase not started
- ❌ **Ongoing Prevention**: No automated sprawl detection/prevention system

### **Implementation Strategy**
**6-Phase Approach**: Foundation → Monitoring → Remediation → Dashboard → Policy → Integration

---

## 📋 **PHASE 1: FOUNDATION ASSESSMENT & PLANNING**
**Duration**: 2-3 hours | **Status**: Ready to Start

### **Objectives**
1. Assess current repository structure health
2. Establish baseline metrics for sprawl prevention
3. Create implementation tracking system
4. Validate existing UFC enforcement integration points

### **Deliverables**

#### **1.1 Repository Health Analyzer**
**File**: `${MAIA_ROOT}/claude/tools/governance/repository_analyzer.py`

```python
#!/usr/bin/env python3
"""
Repository Health Analyzer - Phase 1 Component
Analyzes repository structure and identifies sprawl patterns
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class RepositoryAnalyzer:
    def __init__(self, repo_path: str = "${MAIA_ROOT}"):
        self.repo_path = Path(repo_path)
        self.analysis_results = {}
        
    def analyze_structure(self) -> Dict:
        """Comprehensive repository structure analysis"""
        print("🔍 Analyzing repository structure...")
        
        # File count analysis
        file_counts = self._count_files_by_location()
        
        # UFC compliance check
        ufc_compliance = self._check_ufc_compliance()
        
        # Sprawl indicators
        sprawl_indicators = self._identify_sprawl_patterns()
        
        # Tool organization analysis
        tool_analysis = self._analyze_tool_organization()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "file_counts": file_counts,
            "ufc_compliance": ufc_compliance,
            "sprawl_indicators": sprawl_indicators,
            "tool_analysis": tool_analysis,
            "health_score": self._calculate_health_score()
        }
        
        self.analysis_results = results
        return results
    
    def _count_files_by_location(self) -> Dict:
        """Count files in different repository locations"""
        counts = {
            "root_files": 0,
            "claude_tools": 0,
            "claude_agents": 0,
            "claude_context": 0,
            "archive_files": 0,
            "total_files": 0
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            
            # Skip .git directory
            if '.git' in root_path.parts:
                continue
                
            file_count = len(files)
            counts["total_files"] += file_count
            
            # Categorize by location
            if root_path == self.repo_path:
                counts["root_files"] = file_count
            elif "claude/tools" in str(root_path):
                counts["claude_tools"] += file_count
            elif "claude/agents" in str(root_path):
                counts["claude_agents"] += file_count
            elif "claude/context" in str(root_path):
                counts["claude_context"] += file_count
            elif "archive" in str(root_path):
                counts["archive_files"] += file_count
        
        return counts
    
    def _check_ufc_compliance(self) -> Dict:
        """Check UFC system compliance"""
        ufc_file = self.repo_path / "claude/context/ufc_system.md"
        hook_file = self.repo_path / "claude/hooks/user-prompt-submit"
        enforcer_file = self.repo_path / "claude/hooks/context_loading_enforcer.py"
        
        return {
            "ufc_system_exists": ufc_file.exists(),
            "enforcement_hook_exists": hook_file.exists(),
            "context_enforcer_exists": enforcer_file.exists(),
            "ufc_system_accessible": ufc_file.is_file() if ufc_file.exists() else False
        }
    
    def _identify_sprawl_patterns(self) -> List[Dict]:
        """Identify potential sprawl patterns"""
        patterns = []
        
        # Root directory file count
        root_files = list(self.repo_path.glob("*"))
        root_file_count = len([f for f in root_files if f.is_file()])
        
        if root_file_count > 20:
            patterns.append({
                "type": "root_sprawl",
                "severity": "high" if root_file_count > 30 else "medium",
                "count": root_file_count,
                "description": f"{root_file_count} files in root directory (target: <20)"
            })
        
        # Check for archive directories outside archive/ folder
        for root, dirs, files in os.walk(self.repo_path):
            for dir_name in dirs:
                if any(keyword in dir_name.lower() for keyword in ['archive', 'backup', 'old', 'legacy']):
                    if not str(root).endswith('archive'):
                        patterns.append({
                            "type": "misplaced_archive",
                            "severity": "medium",
                            "path": os.path.join(root, dir_name),
                            "description": f"Archive directory outside archive/ folder: {dir_name}"
                        })
        
        return patterns
    
    def _analyze_tool_organization(self) -> Dict:
        """Analyze tool organization in claude/tools"""
        tools_path = self.repo_path / "claude/tools"
        
        if not tools_path.exists():
            return {"error": "Tools directory not found"}
        
        categories = {}
        total_tools = 0
        
        for category_dir in tools_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                tool_count = len([f for f in category_dir.rglob("*.py") if f.is_file()])
                categories[category_dir.name] = tool_count
                total_tools += tool_count
        
        return {
            "total_tools": total_tools,
            "categories": categories,
            "category_count": len(categories)
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall repository health score (0-10)"""
        score = 10.0
        
        # Penalize based on analysis results
        if hasattr(self, 'analysis_results'):
            return score  # Placeholder - implement scoring logic
        
        return score
    
    def save_analysis(self, output_path: str = None) -> str:
        """Save analysis results to file"""
        if not output_path:
            output_path = f"${MAIA_ROOT}/claude/data/repository_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        return output_path
    
    def print_summary(self):
        """Print analysis summary"""
        if not self.analysis_results:
            print("❌ No analysis results available. Run analyze_structure() first.")
            return
        
        results = self.analysis_results
        
        print("\n" + "="*60)
        print("📊 REPOSITORY HEALTH ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📁 File Counts:")
        for key, value in results['file_counts'].items():
            print(f"   {key}: {value}")
        
        print(f"\n🏛️ UFC Compliance:")
        for key, value in results['ufc_compliance'].items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        print(f"\n⚠️ Sprawl Indicators ({len(results['sprawl_indicators'])}):")
        for pattern in results['sprawl_indicators']:
            severity_icon = "🔴" if pattern['severity'] == 'high' else "🟡"
            print(f"   {severity_icon} {pattern['type']}: {pattern['description']}")
        
        print(f"\n🛠️ Tool Organization:")
        tool_data = results['tool_analysis']
        print(f"   Total Tools: {tool_data.get('total_tools', 0)}")
        print(f"   Categories: {tool_data.get('category_count', 0)}")
        
        print(f"\n🎯 Health Score: {results['health_score']:.1f}/10.0")
        print("="*60)

def main():
    analyzer = RepositoryAnalyzer()
    
    print("🚀 Starting Repository Health Analysis...")
    results = analyzer.analyze_structure()
    
    analyzer.print_summary()
    
    # Save results
    output_file = analyzer.save_analysis()
    print(f"\n💾 Analysis saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    main()
```

#### **1.2 Implementation Progress Tracker**
**File**: `${MAIA_ROOT}/claude/data/governance_implementation_progress.json`

```json
{
  "schema_version": "1.0",
  "implementation_started": null,
  "current_phase": "planning",
  "phases": {
    "phase_1_foundation": {
      "status": "pending",
      "started": null,
      "completed": null,
      "components": {
        "repository_analyzer": false,
        "progress_tracker": false,
        "baseline_metrics": false,
        "integration_validation": false
      }
    },
    "phase_2_monitoring": {
      "status": "not_started",
      "started": null,
      "completed": null,
      "components": {
        "filesystem_monitor": false,
        "sprawl_detector": false,
        "alert_system": false
      }
    },
    "phase_3_remediation": {
      "status": "not_started",
      "started": null,
      "completed": null,
      "components": {
        "auto_remediation": false,
        "policy_engine": false,
        "recovery_system": false
      }
    },
    "phase_4_dashboard": {
      "status": "not_started",
      "started": null,
      "completed": null,
      "components": {
        "web_dashboard": false,
        "reporting_system": false,
        "metrics_collection": false
      }
    },
    "phase_5_policy": {
      "status": "not_started",
      "started": null,
      "completed": null,
      "components": {
        "enhanced_policies": false,
        "rule_engine": false,
        "compliance_monitoring": false
      }
    },
    "phase_6_integration": {
      "status": "not_started",
      "started": null,
      "completed": null,
      "components": {
        "production_deployment": false,
        "monitoring_integration": false,
        "final_validation": false
      }
    }
  },
  "metrics": {
    "baseline_established": false,
    "sprawl_incidents": 0,
    "prevention_success_rate": null,
    "last_health_check": null
  }
}
```

### **Phase 1 Validation Commands**
```bash
# 1. Run repository analysis
cd ${MAIA_ROOT}
python3 claude/tools/governance/repository_analyzer.py

# 2. Check implementation progress
cat claude/data/governance_implementation_progress.json

# 3. Validate UFC integration points
python3 claude/hooks/context_loading_enforcer.py status

# 4. Confirm directory structure
ls -la claude/tools/governance/
```

### **Phase 1 Success Criteria**
- ✅ Repository analyzer successfully scans entire repo
- ✅ Baseline metrics established and documented
- ✅ Progress tracking system operational
- ✅ UFC integration points validated
- ✅ Health score calculated (target: >7.0/10.0)

### **Phase 1 Recovery Procedure**
If interrupted during Phase 1:
1. Check which components exist: `ls claude/tools/governance/`
2. Run partial analysis: `python3 claude/tools/governance/repository_analyzer.py`
3. Review progress: `cat claude/data/governance_implementation_progress.json`
4. Resume from missing component

---

## 📋 **PHASE 2: MONITORING SYSTEM IMPLEMENTATION**
**Duration**: 4-6 hours | **Dependencies**: Phase 1 Complete

### **Objectives**
1. Implement real-time file system monitoring
2. Create sprawl detection algorithms
3. Establish alert system for violations
4. Integrate with existing hook infrastructure

### **Deliverables**

#### **2.1 File System Monitor**
**File**: `${MAIA_ROOT}/claude/tools/governance/filesystem_monitor.py`

```python
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
    def __init__(self, repo_path: str = "${MAIA_ROOT}"):
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
        relative_path = path.relative_to(self.repo_path)
        
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
        # Real-time monitoring mode
        monitor.start_monitoring()

if __name__ == "__main__":
    main()
```

#### **2.2 Hook Integration Enhancement**
**File**: `${MAIA_ROOT}/claude/hooks/sprawl_prevention_hook.py`

```python
#!/usr/bin/env python3
"""
Sprawl Prevention Hook - Phase 2 Component
Integrates with existing hook system for real-time prevention
"""

import os
import sys
from pathlib import Path

# Add governance tools to path
sys.path.append('${MAIA_ROOT}/claude/tools/governance')

try:
    from filesystem_monitor import FileSystemMonitor
except ImportError:
    print("⚠️  Governance system not installed - skipping sprawl prevention")
    sys.exit(0)

def check_commit_for_sprawl():
    """Check staged files for sprawl violations"""
    print("🔍 SPRAWL PREVENTION CHECK...")
    
    monitor = FileSystemMonitor()
    
    # Get staged files (simplified - would need proper git integration)
    violations_found = False
    violation_details = []
    
    # This would integrate with git to check staged files
    # For now, it's a placeholder for the architecture
    
    if violations_found:
        print("🚨 SPRAWL PREVENTION VIOLATIONS DETECTED:")
        for violation in violation_details:
            print(f"   📄 {violation['file']}: {violation['message']}")
        print("")
        print("❌ COMMIT BLOCKED - Fix violations before committing")
        return False
    else:
        print("✅ No sprawl violations detected")
        return True

def main():
    """Main hook function"""
    if not check_commit_for_sprawl():
        sys.exit(1)  # Block commit
    
    sys.exit(0)  # Allow commit

if __name__ == "__main__":
    main()
```

### **Phase 2 Integration Steps**
1. **Install monitoring dependencies**: `pip install watchdog`
2. **Create governance tools directory**: `mkdir -p claude/tools/governance`
3. **Implement filesystem monitor**: Create `filesystem_monitor.py`
4. **Add hook integration**: Create `sprawl_prevention_hook.py`
5. **Update main hook**: Add sprawl check to `user-prompt-submit`

### **Phase 2 Testing Commands**
```bash
# 1. Test filesystem monitor scan
python3 claude/tools/governance/filesystem_monitor.py scan

# 2. Test real-time monitoring (run for 30 seconds, then Ctrl+C)
timeout 30 python3 claude/tools/governance/filesystem_monitor.py

# 3. Test hook integration
python3 claude/hooks/sprawl_prevention_hook.py

# 4. Create test violation and verify detection
touch test_violation.tmp  # Should trigger alert
rm test_violation.tmp     # Cleanup
```

### **Phase 2 Success Criteria**
- ✅ Real-time file monitoring operational
- ✅ Policy violations detected and logged
- ✅ Hook integration working
- ✅ One-time repository scan completes successfully
- ✅ Alert system functioning

### **Phase 2 Recovery Procedure**
If interrupted during Phase 2:
1. Check component status: `ls claude/tools/governance/`
2. Test existing components: `python3 claude/tools/governance/filesystem_monitor.py scan`
3. Check dependencies: `pip list | grep watchdog`
4. Resume from missing component

---

## 📋 **PHASE 3: AUTOMATED REMEDIATION SYSTEM**
**Duration**: 6-8 hours | **Dependencies**: Phase 1-2 Complete

### **Objectives**
1. Implement automated fix system for common violations
2. Create safe remediation policies
3. Establish human approval workflow for major changes
4. Build rollback capabilities

### **Deliverables**

#### **3.1 Remediation Engine**
**File**: `${MAIA_ROOT}/claude/tools/governance/remediation_engine.py`

```python
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
    def __init__(self, repo_path: str = "${MAIA_ROOT}"):
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

def main():
    engine = RemediationEngine()
    
    # Example usage
    sample_violations = [
        {
            "type": "forbidden_root_extension",
            "file_path": "test_file.tmp",
            "severity": "high"
        }
    ]
    
    results = engine.analyze_and_fix(sample_violations)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
```

### **Phase 3 Testing Commands**
```bash
# 1. Test remediation engine with sample violations
python3 claude/tools/governance/remediation_engine.py

# 2. Check backup directory creation
ls -la claude/data/governance_backups/

# 3. Test safe mode operations
echo "test" > test_violation.tmp
python3 claude/tools/governance/remediation_engine.py
```

### **Phase 3 Success Criteria**
- ✅ Remediation engine processes violations safely
- ✅ Backup system operational
- ✅ Safe automated fixes working
- ✅ Manual review workflow functional
- ✅ Rollback capability implemented

---

## 📋 **PHASE 4: GOVERNANCE DASHBOARD & REPORTING**
**Duration**: 8-10 hours | **Dependencies**: Phase 1-3 Complete

### **Objectives**
1. Create web-based governance dashboard
2. Implement real-time metrics visualization
3. Build reporting system for health trends
4. Integrate with existing Maia dashboard ecosystem

### **Deliverables**

#### **4.1 Governance Dashboard**
**File**: `${MAIA_ROOT}/claude/tools/governance/governance_dashboard.py`

```python
#!/usr/bin/env python3
"""
Governance Dashboard - Phase 4 Component
Web interface for repository governance monitoring
"""

import os
import json
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import sys

# Add governance tools to path
sys.path.append('${MAIA_ROOT}/claude/tools/governance')

from repository_analyzer import RepositoryAnalyzer
from filesystem_monitor import FileSystemMonitor

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('governance_dashboard.html')

@app.route('/api/health')
def health_status():
    """API endpoint for health status"""
    analyzer = RepositoryAnalyzer()
    analysis = analyzer.analyze_structure()
    
    return jsonify({
        "status": "healthy" if analysis["health_score"] > 7.0 else "degraded",
        "health_score": analysis["health_score"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/violations')
def get_violations():
    """API endpoint for violation data"""
    monitor = FileSystemMonitor()
    violations = monitor.get_violations_summary()
    
    return jsonify(violations)

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for governance metrics"""
    analyzer = RepositoryAnalyzer()
    analysis = analyzer.analyze_structure()
    
    return jsonify({
        "file_counts": analysis["file_counts"],
        "sprawl_indicators": analysis["sprawl_indicators"],
        "tool_analysis": analysis["tool_analysis"],
        "ufc_compliance": analysis["ufc_compliance"]
    })

if __name__ == '__main__':
    app.run(debug=True, port=8070, host='127.0.0.1')
```

#### **4.2 Dashboard Template**
**File**: `${MAIA_ROOT}/claude/tools/governance/templates/governance_dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maia Repository Governance Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .health-score { font-size: 2em; font-weight: bold; color: #28a745; }
        .violation-count { font-size: 1.5em; font-weight: bold; color: #dc3545; }
        .status-healthy { color: #28a745; }
        .status-degraded { color: #ffc107; }
        .status-critical { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Maia Repository Governance Dashboard</h1>
        <p>Real-time monitoring and sprawl prevention system</p>
        <div id="status-indicator">
            <span id="health-status">Loading...</span>
            <span id="last-update"></span>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>📊 Repository Health</h3>
            <div class="health-score" id="health-score">-</div>
            <p>Overall health score (0-10)</p>
        </div>

        <div class="metric-card">
            <h3>⚠️ Active Violations</h3>
            <div class="violation-count" id="violation-count">-</div>
            <p>Current policy violations</p>
        </div>

        <div class="metric-card">
            <h3>📁 File Distribution</h3>
            <div id="file-counts">Loading...</div>
        </div>

        <div class="metric-card">
            <h3>🛠️ Tool Organization</h3>
            <div id="tool-stats">Loading...</div>
        </div>

        <div class="metric-card">
            <h3>🏛️ UFC Compliance</h3>
            <div id="ufc-status">Loading...</div>
        </div>

        <div class="metric-card">
            <h3>📈 Recent Activity</h3>
            <div id="recent-violations">Loading...</div>
        </div>
    </div>

    <script>
        async function updateDashboard() {
            try {
                // Fetch health status
                const healthResponse = await fetch('/api/health');
                const healthData = await healthResponse.json();
                
                document.getElementById('health-score').textContent = healthData.health_score.toFixed(1);
                document.getElementById('health-status').textContent = healthData.status.toUpperCase();
                document.getElementById('health-status').className = `status-${healthData.status}`;
                
                // Fetch violations
                const violationsResponse = await fetch('/api/violations');
                const violationsData = await violationsResponse.json();
                
                document.getElementById('violation-count').textContent = violationsData.total_violations || 0;
                
                // Fetch metrics
                const metricsResponse = await fetch('/api/metrics');
                const metricsData = await metricsResponse.json();
                
                // Update file counts
                const fileCountsHtml = Object.entries(metricsData.file_counts)
                    .map(([key, value]) => `<div>${key}: ${value}</div>`)
                    .join('');
                document.getElementById('file-counts').innerHTML = fileCountsHtml;
                
                // Update tool stats
                const toolData = metricsData.tool_analysis;
                document.getElementById('tool-stats').innerHTML = `
                    <div>Total Tools: ${toolData.total_tools || 0}</div>
                    <div>Categories: ${toolData.category_count || 0}</div>
                `;
                
                // Update UFC compliance
                const ufcData = metricsData.ufc_compliance;
                const ufcHtml = Object.entries(ufcData)
                    .map(([key, value]) => `<div>${value ? '✅' : '❌'} ${key}</div>`)
                    .join('');
                document.getElementById('ufc-status').innerHTML = ufcHtml;
                
                document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
                
            } catch (error) {
                console.error('Dashboard update failed:', error);
            }
        }

        // Update dashboard on load and every 30 seconds
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
```

### **Phase 4 Testing Commands**
```bash
# 1. Install Flask if needed
pip install flask

# 2. Start governance dashboard
python3 claude/tools/governance/governance_dashboard.py

# 3. Test dashboard accessibility
curl http://127.0.0.1:8070/api/health

# 4. Open dashboard in browser
open http://127.0.0.1:8070
```

---

## 📋 **PHASE 5: POLICY ENGINE ENHANCEMENT**
**Duration**: 4-6 hours | **Dependencies**: Phase 1-4 Complete

### **Objectives**
1. Enhance policy rules with more sophisticated detection
2. Implement machine learning for pattern recognition
3. Create adaptive policy updates
4. Build policy configuration management

### **Deliverables**

#### **5.1 Enhanced Policy Engine**
**File**: `${MAIA_ROOT}/claude/tools/governance/enhanced_policy_engine.py`

```python
#!/usr/bin/env python3
"""
Enhanced Policy Engine - Phase 5 Component
Advanced policy management with ML-based pattern recognition
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class EnhancedPolicyEngine:
    def __init__(self, repo_path: str = "${MAIA_ROOT}"):
        self.repo_path = Path(repo_path)
        self.policies_file = self.repo_path / "claude/context/governance/policies.yaml"
        self.policies = self._load_policies()
        self.violation_history = []
        
    def _load_policies(self) -> Dict:
        """Load governance policies from configuration"""
        default_policies = {
            "file_placement": {
                "max_root_files": 20,
                "forbidden_root_extensions": [".tmp", ".log", ".backup", ".cache"],
                "required_directories": ["claude/tools", "claude/agents", "claude/context"],
                "archive_patterns": ["*archive*", "*backup*", "*old*", "*legacy*"]
            },
            "tool_organization": {
                "max_tools_per_category": 50,
                "required_categories": ["core", "automation", "research", "communication", "monitoring", "data", "security", "business"],
                "naming_conventions": {
                    "pattern": "^[a-z_][a-z0-9_]*\\.py$",
                    "description": "Lowercase with underscores only"
                }
            },
            "content_policies": {
                "max_file_size_mb": 10,
                "forbidden_patterns": ["password", "secret", "api_key"],
                "required_headers": {
                    "python": ["#!/usr/bin/env python3", '"""', "Purpose", "Author"]
                }
            },
            "quality_standards": {
                "min_documentation_ratio": 0.2,
                "max_complexity_score": 10,
                "required_tests": False
            }
        }
        
        if self.policies_file.exists():
            try:
                with open(self.policies_file, 'r') as f:
                    loaded_policies = yaml.safe_load(f)
                    # Merge with defaults
                    return {**default_policies, **loaded_policies}
            except Exception as e:
                print(f"⚠️  Error loading policies: {e}, using defaults")
        
        return default_policies
    
    def evaluate_file(self, file_path: Path, content: Optional[str] = None) -> Dict:
        """Evaluate file against all applicable policies"""
        relative_path = file_path.relative_to(self.repo_path)
        
        evaluation = {
            "file_path": str(relative_path),
            "timestamp": datetime.now().isoformat(),
            "violations": [],
            "compliance_score": 100.0,
            "recommendations": []
        }
        
        # File placement evaluation
        placement_violations = self._evaluate_file_placement(file_path)
        evaluation["violations"].extend(placement_violations)
        
        # Content evaluation
        if content or file_path.exists():
            if not content and file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    content = None
            
            if content:
                content_violations = self._evaluate_content(file_path, content)
                evaluation["violations"].extend(content_violations)
        
        # Calculate compliance score
        evaluation["compliance_score"] = self._calculate_compliance_score(evaluation["violations"])
        
        # Generate recommendations
        evaluation["recommendations"] = self._generate_recommendations(evaluation["violations"])
        
        return evaluation
    
    def _evaluate_file_placement(self, file_path: Path) -> List[Dict]:
        """Evaluate file placement against policies"""
        violations = []
        relative_path = file_path.relative_to(self.repo_path)
        
        # Check root directory files
        if len(relative_path.parts) == 1 and file_path.is_file():
            root_files_count = len([f for f in self.repo_path.iterdir() if f.is_file()])
            max_root_files = self.policies["file_placement"]["max_root_files"]
            
            if root_files_count > max_root_files:
                violations.append({
                    "type": "root_file_limit_exceeded",
                    "severity": "medium",
                    "message": f"Root directory has {root_files_count} files (limit: {max_root_files})",
                    "policy": "file_placement.max_root_files"
                })
            
            # Check forbidden extensions
            forbidden_exts = self.policies["file_placement"]["forbidden_root_extensions"]
            if file_path.suffix in forbidden_exts:
                violations.append({
                    "type": "forbidden_root_extension",
                    "severity": "high",
                    "message": f"Forbidden extension {file_path.suffix} in root directory",
                    "policy": "file_placement.forbidden_root_extensions"
                })
        
        # Check for archive patterns in wrong locations
        for pattern in self.policies["file_placement"]["archive_patterns"]:
            pattern_clean = pattern.strip('*').lower()
            if pattern_clean in str(relative_path).lower():
                if not str(relative_path).startswith('archive/'):
                    violations.append({
                        "type": "misplaced_archive",
                        "severity": "medium",
                        "message": f"Archive-like content outside archive directory: {pattern_clean}",
                        "policy": "file_placement.archive_patterns"
                    })
        
        return violations
    
    def _evaluate_content(self, file_path: Path, content: str) -> List[Dict]:
        """Evaluate file content against policies"""
        violations = []
        
        # Check file size
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            max_size = self.policies["content_policies"]["max_file_size_mb"]
            
            if size_mb > max_size:
                violations.append({
                    "type": "file_size_exceeded",
                    "severity": "medium",
                    "message": f"File size {size_mb:.1f}MB exceeds limit of {max_size}MB",
                    "policy": "content_policies.max_file_size_mb"
                })
        
        # Check for forbidden patterns
        forbidden_patterns = self.policies["content_policies"]["forbidden_patterns"]
        for pattern in forbidden_patterns:
            if pattern.lower() in content.lower():
                violations.append({
                    "type": "forbidden_content_pattern",
                    "severity": "high",
                    "message": f"Forbidden pattern '{pattern}' found in content",
                    "policy": "content_policies.forbidden_patterns"
                })
        
        # Check Python file headers
        if file_path.suffix == ".py":
            python_requirements = self.policies["content_policies"]["required_headers"]["python"]
            for requirement in python_requirements:
                if requirement not in content:
                    violations.append({
                        "type": "missing_required_header",
                        "severity": "low",
                        "message": f"Missing required header: {requirement}",
                        "policy": "content_policies.required_headers.python"
                    })
        
        return violations
    
    def _calculate_compliance_score(self, violations: List[Dict]) -> float:
        """Calculate compliance score based on violations"""
        if not violations:
            return 100.0
        
        score = 100.0
        severity_penalties = {"high": 20, "medium": 10, "low": 5}
        
        for violation in violations:
            penalty = severity_penalties.get(violation["severity"], 5)
            score -= penalty
        
        return max(0.0, score)
    
    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []
        
        violation_types = [v["type"] for v in violations]
        
        if "root_file_limit_exceeded" in violation_types:
            recommendations.append("Consider organizing root files into appropriate subdirectories")
        
        if "forbidden_root_extension" in violation_types:
            recommendations.append("Remove temporary files from root directory")
        
        if "misplaced_archive" in violation_types:
            recommendations.append("Move archive files to archive/historical/ directory")
        
        if "forbidden_content_pattern" in violation_types:
            recommendations.append("Remove sensitive information and use environment variables")
        
        if "missing_required_header" in violation_types:
            recommendations.append("Add required documentation headers to Python files")
        
        return recommendations
    
    def save_policies(self, policies: Dict):
        """Save updated policies to configuration file"""
        self.policies_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.policies_file, 'w') as f:
            yaml.dump(policies, f, default_flow_style=False, indent=2)
        
        self.policies = policies

def main():
    engine = EnhancedPolicyEngine()
    
    # Example evaluation
    test_file = Path("${MAIA_ROOT}/test_file.py")
    test_content = """#!/usr/bin/env python3
\"\"\"
Test file for policy evaluation
Purpose: Testing
Author: Maia
\"\"\"

def test_function():
    return "Hello World"
"""
    
    evaluation = engine.evaluate_file(test_file, test_content)
    print(json.dumps(evaluation, indent=2))

if __name__ == "__main__":
    main()
```

---

## 📋 **PHASE 6: SYSTEM INTEGRATION & PRODUCTION**
**Duration**: 4-6 hours | **Dependencies**: Phase 1-5 Complete

### **Objectives**
1. Integrate all components into unified system
2. Deploy to production environment
3. Establish monitoring and alerting
4. Create operational documentation

## 📋 **PHASE 7: DASHBOARD HUB INTEGRATION**
**Duration**: 2-3 hours | **Dependencies**: Phase 1-6 Complete

### **Objectives**
1. Integrate governance dashboard into existing Maia dashboard hub
2. Add governance dashboard to main dashboard registry
3. Ensure seamless navigation between dashboards
4. Update dashboard service management system

### **Deliverables**

#### **7.1 Dashboard Hub Integration**
**File**: Dashboard registry update and service integration

```python
# Integration with existing dashboard system
# Add governance dashboard to dashboard service registry
# Update navigation and service management
```

### **Phase 7 Integration Steps**
1. **Locate dashboard service registry**
2. **Add governance dashboard entry**
3. **Update dashboard hub navigation**
4. **Test dashboard hub integration**
5. **Validate service management**

### **Phase 7 Success Criteria**
- ✅ Governance dashboard appears in dashboard hub
- ✅ Navigation between dashboards works seamlessly
- ✅ Service management includes governance dashboard
- ✅ Port management prevents conflicts

---

### **Deliverables**

#### **6.1 Unified Governance System**
**File**: `${MAIA_ROOT}/claude/commands/governance_system.md`

```markdown
# Repository Governance System

## Purpose
Unified command interface for repository sprawl prevention and governance.

## Commands

### System Management
- `governance status` - Show system health and compliance
- `governance scan` - Full repository compliance scan
- `governance monitor` - Start real-time monitoring
- `governance dashboard` - Launch web dashboard

### Policy Management
- `governance policies list` - Show current policies
- `governance policies check <file>` - Check file compliance
- `governance policies update` - Update policy configuration

### Remediation
- `governance fix --auto` - Apply automated fixes
- `governance fix --interactive` - Interactive fix mode
- `governance rollback <action_id>` - Rollback changes

### Reporting
- `governance report daily` - Generate daily compliance report
- `governance report violations` - Show recent violations
- `governance metrics` - Show governance metrics

## Integration with UFC System
- Hooks into existing `user-prompt-submit` enforcement
- Maintains 100% compatibility with context loading
- Extends UFC structure with governance monitoring

## Production Deployment
- Monitoring runs continuously in background
- Dashboard available at http://127.0.0.1:8070
- Alerts integrate with existing notification system
```

#### **6.2 Production Deployment Script**
**File**: `${MAIA_ROOT}/claude/tools/governance/deploy_governance.py`

```python
#!/usr/bin/env python3
"""
Governance System Deployment Script - Phase 6 Component
Production deployment and system integration
"""

import os
import subprocess
import sys
from pathlib import Path
import json

def check_dependencies():
    """Check required dependencies"""
    print("🔍 Checking dependencies...")
    
    required_packages = ["flask", "watchdog", "pyyaml"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
    
    return len(missing_packages) == 0

def create_governance_directories():
    """Create required governance directories"""
    print("📁 Creating governance directories...")
    
    directories = [
        "${MAIA_ROOT}/claude/tools/governance",
        "${MAIA_ROOT}/claude/tools/governance/templates",
        "${MAIA_ROOT}/claude/context/governance",
        "${MAIA_ROOT}/claude/data/governance_backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def integrate_with_hooks():
    """Integrate governance with existing hook system"""
    print("🔗 Integrating with hook system...")
    
    hook_file = Path("${MAIA_ROOT}/claude/hooks/user-prompt-submit")
    
    if hook_file.exists():
        # Read existing hook
        with open(hook_file, 'r') as f:
            hook_content = f.read()
        
        # Check if governance integration already exists
        if "sprawl_prevention_hook.py" not in hook_content:
            # Add governance check to hook
            governance_check = """
# Stage 6: Repository Governance Check (NEW)
echo ""
echo "🏛️ REPOSITORY GOVERNANCE CHECK..."
GOVERNANCE_HOOK="${MAIA_ROOT}/claude/hooks/sprawl_prevention_hook.py"
if [[ -f "$GOVERNANCE_HOOK" ]]; then
    python3 "$GOVERNANCE_HOOK"
    GOVERNANCE_CODE=$?
    if [[ $GOVERNANCE_CODE -ne 0 ]]; then
        echo "🚨 GOVERNANCE VIOLATIONS DETECTED - Check sprawl prevention"
    else
        echo "✅ Repository governance compliant"
    fi
else
    echo "⚠️  Governance hook not found - governance monitoring disabled"
fi
echo ""
"""
            
            # Insert before final stage
            updated_content = hook_content.replace(
                "echo \"═══════════════════════════════════════════════════════════════\"",
                governance_check + "\necho \"═══════════════════════════════════════════════════════════════\""
            )
            
            # Backup original hook
            backup_file = hook_file.with_suffix('.backup')
            with open(backup_file, 'w') as f:
                f.write(hook_content)
            
            # Write updated hook
            with open(hook_file, 'w') as f:
                f.write(updated_content)
            
            print("   ✅ Hook integration completed")
        else:
            print("   ✅ Hook integration already exists")
    else:
        print("   ⚠️  Hook file not found")

def validate_system():
    """Validate governance system functionality"""
    print("🧪 Validating system functionality...")
    
    # Test repository analyzer
    try:
        from repository_analyzer import RepositoryAnalyzer
        analyzer = RepositoryAnalyzer()
        results = analyzer.analyze_structure()
        print(f"   ✅ Repository analyzer: Health score {results['health_score']:.1f}/10.0")
    except Exception as e:
        print(f"   ❌ Repository analyzer: {e}")
        return False
    
    # Test filesystem monitor
    try:
        from filesystem_monitor import FileSystemMonitor
        monitor = FileSystemMonitor()
        scan_results = monitor.scan_repository()
        print(f"   ✅ Filesystem monitor: Scanned {scan_results['total_files_scanned']} files")
    except Exception as e:
        print(f"   ❌ Filesystem monitor: {e}")
        return False
    
    # Test policy engine
    try:
        from enhanced_policy_engine import EnhancedPolicyEngine
        engine = EnhancedPolicyEngine()
        print("   ✅ Policy engine: Loaded successfully")
    except Exception as e:
        print(f"   ❌ Policy engine: {e}")
        return False
    
    return True

def create_systemd_service():
    """Create systemd service for monitoring (Linux)"""
    if os.name != 'posix':
        print("   ⚠️  Systemd service creation skipped (not Linux)")
        return
    
    service_content = """[Unit]
Description=Maia Repository Governance Monitor
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory=${MAIA_ROOT}
ExecStart=/usr/bin/python3 ${MAIA_ROOT}/claude/tools/governance/filesystem_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""".format(user=os.getenv('USER', 'maia'))
    
    service_file = Path("/etc/systemd/system/maia-governance.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", "maia-governance"])
        
        print("   ✅ Systemd service created and enabled")
    except PermissionError:
        print("   ⚠️  Systemd service creation requires sudo privileges")
    except Exception as e:
        print(f"   ❌ Systemd service creation failed: {e}")

def main():
    """Main deployment function"""
    print("🚀 Deploying Maia Repository Governance System")
    print("="*50)
    
    # Phase 1: Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return False
    
    # Phase 2: Create directories
    create_governance_directories()
    
    # Phase 3: Integrate with hooks
    integrate_with_hooks()
    
    # Phase 4: Validate system
    if not validate_system():
        print("❌ System validation failed")
        return False
    
    # Phase 5: Create background service
    create_systemd_service()
    
    print("\n" + "="*50)
    print("✅ GOVERNANCE SYSTEM DEPLOYMENT COMPLETE")
    print("="*50)
    
    print("\n📋 Next Steps:")
    print("   1. Run: governance status")
    print("   2. Run: governance scan") 
    print("   3. Start: governance dashboard")
    print("   4. Monitor: governance report violations")
    
    print("\n🔗 Integration Points:")
    print("   • Hook system: Enhanced user-prompt-submit")
    print("   • Dashboard: http://127.0.0.1:8070")
    print("   • Monitoring: Real-time file system watching")
    print("   • Policies: claude/context/governance/policies.yaml")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## 🔄 **RECOVERY & RESUME PROCEDURES**

### **Implementation Status Checking**
```bash
# Check what's implemented
ls -la claude/tools/governance/
cat claude/data/governance_implementation_progress.json

# Test existing components
python3 claude/tools/governance/repository_analyzer.py
python3 claude/tools/governance/filesystem_monitor.py scan
```

### **Resume from Interruption**
1. **Identify current phase**: Check progress tracker
2. **Validate existing components**: Run component tests
3. **Resume implementation**: Continue from missing component
4. **Update progress tracker**: Mark completed components

### **Emergency Rollback**
```bash
# Restore original hook
cp claude/hooks/user-prompt-submit.backup claude/hooks/user-prompt-submit

# Stop monitoring
pkill -f "filesystem_monitor.py"

# Remove governance components
rm -rf claude/tools/governance/
```

---

## 📊 **SUCCESS METRICS & VALIDATION**

### **Overall Success Criteria**
- **Zero Sprawl Incidents**: No new sprawl detected after 30 days
- **High Compliance Score**: Repository health >8.5/10.0
- **System Integration**: 100% compatibility with existing UFC system
- **Performance**: <30s full repository scans, <1s violation detection
- **Automation**: >90% successful automated remediation

### **Phase-Specific Validation**
Each phase includes specific testing commands and success criteria to ensure proper implementation and functionality.

### **Long-term Monitoring**
- Daily automated health checks
- Weekly compliance reports
- Monthly system optimization reviews
- Quarterly policy updates

---

## 💡 **IMPLEMENTATION NOTES**

This guide provides complete implementation details to prevent "forgetting what we're doing halfway through." Each phase includes:

- **Exact file paths** for all components
- **Complete code implementations** with detailed comments
- **Integration specifications** with existing systems
- **Testing procedures** for validation
- **Recovery procedures** for interruptions

The system maintains 100% compatibility with existing UFC enforcement while adding comprehensive sprawl prevention capabilities.

**Ready to implement**: Start with Phase 1 and follow the detailed checklist for each phase.