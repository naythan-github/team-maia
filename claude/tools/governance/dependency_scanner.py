#!/usr/bin/env python3
"""
Dependency Scanner - System Integrity Validation
Comprehensive scanning for broken imports, missing files, and system dependencies
"""

import os
import re
import ast
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import importlib.util
import sys

# Add MAIA root to path for imports
_maia_root = Path(__file__).resolve().parents[3]
if str(_maia_root) not in sys.path:
    sys.path.insert(0, str(_maia_root))

try:
    from claude.tools.core.path_manager import get_maia_root
except ImportError:
    # Fallback if path_manager not available
    def get_maia_root():
        return str(_maia_root)

class DependencyScanner:
    def __init__(self, repo_path: str = None):
        # Calculate repo path: this file is at claude/tools/governance/dependency_scanner.py
        # So parents[3] = maia root
        if repo_path is None:
            repo_path = str(Path(__file__).resolve().parents[3])
        self.repo_path = Path(repo_path)
        self.scan_results = {}
        
        # Define patterns for different types of dependencies
        self.import_patterns = [
            r"^import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)",
            r"^from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import",
            r"importlib\.import_module\([\"']([^\"']+)[\"']\)",
        ]
        
        # File reference patterns
        self.file_reference_patterns = [
            r"[\"']([^\"']*\.py)[\"']",
            r"[\"']([^\"']*\.json)[\"']",
            r"[\"']([^\"']*\.md)[\"']",
            r"Path\([\"']([^\"']+)[\"']\)",
            r"open\([\"']([^\"']+)[\"']\)",
        ]
        
        # Exclude patterns (don't scan these)
        self.exclude_patterns = [
            r"\.git/",
            r"__pycache__/",
            r"\.pyc$",
            r"archive/historical/",  # Skip archived files
            r"node_modules/",
            r"\.DS_Store",
        ]
    
    def scan_all_dependencies(self) -> Dict:
        """Comprehensive dependency scan of entire repository"""
        print("🔍 Starting comprehensive dependency scan...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "scan_summary": {},
            "broken_imports": [],
            "missing_files": [],
            "orphaned_references": [],
            "system_integrity_issues": [],
            "recommendations": []
        }
        
        # Phase 1: Scan Python imports
        print("📊 Phase 1: Scanning Python imports...")
        broken_imports = self._scan_python_imports()
        results["broken_imports"] = broken_imports
        
        # Phase 2: Scan file references
        print("📊 Phase 2: Scanning file references...")
        missing_files = self._scan_file_references()
        results["missing_files"] = missing_files
        
        # Phase 3: Scan for orphaned references
        print("📊 Phase 3: Scanning for orphaned references...")
        orphaned_refs = self._scan_orphaned_references()
        results["orphaned_references"] = orphaned_refs
        
        # Phase 4: System integrity check
        print("📊 Phase 4: System integrity validation...")
        integrity_issues = self._validate_system_integrity()
        results["system_integrity_issues"] = integrity_issues
        
        # Phase 5: Generate recommendations
        print("📊 Phase 5: Generating repair recommendations...")
        recommendations = self._generate_repair_recommendations(results)
        results["recommendations"] = recommendations
        
        # Enhanced Summary with try-protection awareness
        try_protected_imports = len([imp for imp in broken_imports if imp.get('try_protected')])
        unprotected_imports = len(broken_imports) - try_protected_imports
        
        results["scan_summary"] = {
            "total_broken_imports": len(broken_imports),
            "unprotected_broken_imports": unprotected_imports,
            "try_protected_imports": try_protected_imports,
            "total_missing_files": len(missing_files),
            "total_orphaned_references": len(orphaned_refs),
            "total_integrity_issues": len(integrity_issues),
            "total_recommendations": len(recommendations),
            "system_health_status": self._calculate_system_health(results)
        }
        
        self.scan_results = results
        return results
    
    def _scan_python_imports(self) -> List[Dict]:
        """Scan all Python files for broken imports"""
        broken_imports = []
        python_files = list(self.repo_path.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_exclude_file(py_file):
                continue
                
            try:
                broken_in_file = self._check_imports_in_file(py_file)
                broken_imports.extend(broken_in_file)
            except Exception as e:
                broken_imports.append({
                    "file": str(py_file.relative_to(self.repo_path)),
                    "import_statement": "FILE_READ_ERROR",
                    "error": str(e),
                    "severity": "high",
                    "category": "file_access_error"
                })
        
        return broken_imports
    
    def _check_imports_in_file(self, file_path: Path) -> List[Dict]:
        """Check all imports in a specific Python file"""
        broken_imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Parse AST to get imports
            try:
                tree = ast.parse(content)
                imports = self._extract_imports_from_ast(tree)
            except SyntaxError:
                # Fall back to regex parsing for files with syntax issues
                imports = self._extract_imports_from_regex(content)
            
            # Test each import with enhanced logic
            for import_info in imports:
                # Skip try-protected imports that have fallback patterns
                if import_info.get('is_try_protected') and self._has_import_fallback(imports, import_info):
                    continue
                    
                if not self._can_import_module(import_info['module']):
                    # Determine if this is a real issue or handled gracefully
                    severity = self._classify_import_severity(import_info['module'])
                    if import_info.get('is_try_protected'):
                        severity = "low"  # Downgrade severity for protected imports
                        
                    broken_imports.append({
                        "file": str(file_path.relative_to(self.repo_path)),
                        "line_number": import_info.get('line_number', 'unknown'),
                        "import_statement": import_info['statement'],
                        "module": import_info['module'],
                        "error": f"Cannot import module: {import_info['module']}",
                        "severity": severity,
                        "category": "broken_import",
                        "try_protected": import_info.get('is_try_protected', False)
                    })
                    
        except Exception as e:
            broken_imports.append({
                "file": str(file_path.relative_to(self.repo_path)),
                "import_statement": "FILE_ANALYSIS_ERROR",
                "error": str(e),
                "severity": "medium",
                "category": "analysis_error"
            })
        
        return broken_imports
    
    def _extract_imports_from_ast(self, tree: ast.AST) -> List[Dict]:
        """Extract import information using AST parsing with try/except context awareness"""
        imports = []
        
        # Track try/except blocks to identify protected imports
        try_blocks = []
        
        for node in ast.walk(tree):
            # Map try/except blocks
            if isinstance(node, ast.Try):
                try_blocks.append({
                    'try_start': node.lineno,
                    'try_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10,
                    'has_except': len(node.handlers) > 0,
                    'except_handlers': [handler.lineno for handler in node.handlers]
                })
            
            # Process import statements with context
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_info = {
                        'module': alias.name,
                        'statement': f"import {alias.name}",
                        'line_number': node.lineno,
                        'type': 'import',
                        'is_try_protected': self._is_in_try_block(node.lineno, try_blocks)
                    }
                    imports.append(import_info)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_info = {
                        'module': node.module,
                        'statement': f"from {node.module} import {', '.join(alias.name for alias in node.names)}",
                        'line_number': node.lineno,
                        'type': 'from_import',
                        'is_try_protected': self._is_in_try_block(node.lineno, try_blocks)
                    }
                    imports.append(import_info)
        
        return imports
    
    def _is_in_try_block(self, line_number: int, try_blocks: List[Dict]) -> bool:
        """Check if a line number is within a try block that has except handlers"""
        for try_block in try_blocks:
            if (try_block['try_start'] <= line_number <= try_block['try_end'] and 
                try_block['has_except']):
                return True
        return False
    
    def _has_import_fallback(self, imports: List[Dict], target_import: Dict) -> bool:
        """Check if a try-protected import has a working fallback in the same file"""
        if not target_import.get('is_try_protected'):
            return False
            
        # Look for absolute import fallback patterns
        target_module = target_import['module']
        
        # Common fallback patterns for ServiceDesk FOBs
        fallback_patterns = [
            f"claude.tools.servicedesk.{target_module}",
            f"claude.tools.{target_module}",
        ]
        
        # Check if any other import in the file provides a fallback
        for imp in imports:
            if imp['module'] in fallback_patterns and self._can_import_module(imp['module']):
                return True
                
        return False
    
    def _extract_imports_from_regex(self, content: str) -> List[Dict]:
        """Fallback regex-based import extraction"""
        imports = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            for pattern in self.import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1)
                    imports.append({
                        'module': module,
                        'statement': line,
                        'line_number': line_num,
                        'type': 'regex_match'
                    })
        
        return imports
    
    def _can_import_module(self, module_name: str) -> bool:
        """Test if a module can be imported"""
        try:
            # Handle relative imports and local modules specially
            if module_name.startswith('.'):
                return True  # Skip relative imports for now
            
            if module_name.startswith('claude.'):
                # Check if it's a local claude module
                module_path = module_name.replace('claude.', '')
                local_path = self.repo_path / 'claude' / f"{module_path.replace('.', '/')}.py"
                if local_path.exists():
                    return True
                # Also check for package
                local_dir = self.repo_path / 'claude' / module_path.replace('.', '/')
                if local_dir.exists() and (local_dir / '__init__.py').exists():
                    return True
                return False
            
            # Try importing standard/installed modules
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            return False
    
    def _classify_import_severity(self, module_name: str) -> str:
        """Classify the severity of a broken import"""
        if module_name.startswith('claude.tools'):
            return "critical"  # Core tool imports
        elif module_name.startswith('claude.'):
            return "high"  # Other claude modules
        elif any(core in module_name.lower() for core in ['fob', 'servicedesk', 'governance']):
            return "critical"  # Key system components
        else:
            return "medium"
    
    def _scan_file_references(self) -> List[Dict]:
        """Scan for references to missing files"""
        missing_files = []
        
        # Scan all text files for file references
        text_files = []
        text_files.extend(self.repo_path.rglob("*.py"))
        text_files.extend(self.repo_path.rglob("*.md"))
        text_files.extend(self.repo_path.rglob("*.json"))
        text_files.extend(self.repo_path.rglob("*.yml"))
        text_files.extend(self.repo_path.rglob("*.yaml"))
        
        for file_path in text_files:
            if self._should_exclude_file(file_path):
                continue
                
            try:
                missing_in_file = self._check_file_references_in_file(file_path)
                missing_files.extend(missing_in_file)
            except Exception as e:
                missing_files.append({
                    "referencing_file": str(file_path.relative_to(self.repo_path)),
                    "referenced_file": "FILE_SCAN_ERROR",
                    "error": str(e),
                    "severity": "low",
                    "category": "scan_error"
                })
        
        return missing_files
    
    def _check_file_references_in_file(self, file_path: Path) -> List[Dict]:
        """Check file references in a specific file"""
        missing_files = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.file_reference_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if self._looks_like_file_path(match):
                            referenced_file = self._resolve_file_path(match, file_path)
                            if referenced_file and not referenced_file.exists():
                                missing_files.append({
                                    "referencing_file": str(file_path.relative_to(self.repo_path)),
                                    "line_number": line_num,
                                    "referenced_file": match,
                                    "resolved_path": str(referenced_file),
                                    "line_content": line.strip(),
                                    "severity": self._classify_file_reference_severity(match),
                                    "category": "missing_file"
                                })
        except Exception as e:
            pass  # Skip files we can't read
            
        return missing_files
    
    def _looks_like_file_path(self, text: str) -> bool:
        """Determine if text looks like a file path"""
        if len(text) < 3:
            return False
        if '/' not in text and '\\' not in text:
            return False
        if text.startswith('http'):
            return False
        return True
    
    def _resolve_file_path(self, file_ref: str, referencing_file: Path) -> Optional[Path]:
        """Resolve a file reference to absolute path"""
        try:
            if file_ref.startswith('/'):
                # Absolute path
                return Path(file_ref)
            else:
                # Relative path
                return referencing_file.parent / file_ref
        except Exception:
            return None
    
    def _classify_file_reference_severity(self, file_ref: str) -> str:
        """Classify severity of missing file reference"""
        if any(ext in file_ref.lower() for ext in ['.py', '.json']):
            return "high"
        elif any(ext in file_ref.lower() for ext in ['.md', '.txt']):
            return "medium"
        else:
            return "low"
    
    def _scan_orphaned_references(self) -> List[Dict]:
        """Scan for references to files that were moved to archive"""
        orphaned_refs = []
        
        # Check for references to archived files
        archived_files = list((self.repo_path / "archive/historical/2025").rglob("*.py"))
        archived_basenames = [f.name for f in archived_files]
        
        # Scan active codebase for references to archived files
        active_files = []
        for pattern in ["*.py", "*.md", "*.json"]:
            active_files.extend(self.repo_path.rglob(pattern))
        
        for active_file in active_files:
            if self._should_exclude_file(active_file):
                continue
            if "archive" in str(active_file):
                continue
                
            try:
                with open(active_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for archived_file in archived_basenames:
                    module_name = archived_file.replace('.py', '')
                    if module_name in content:
                        # Found potential reference to archived file
                        orphaned_refs.append({
                            "active_file": str(active_file.relative_to(self.repo_path)),
                            "referenced_archived_file": archived_file,
                            "severity": "critical" if "fob" in module_name.lower() else "high",
                            "category": "orphaned_reference"
                        })
            except Exception:
                continue
        
        return orphaned_refs
    
    def _validate_system_integrity(self) -> List[Dict]:
        """Validate critical system endpoints and imports"""
        integrity_issues = []
        
        # Test critical imports
        critical_imports = [
            "claude.tools.servicedesk_analytics_fob",
            "claude.tools.governance.repository_analyzer",
            "claude.tools.governance.root_directory_cleanup", 
            "claude.tools.governance.archive_consolidator",
        ]
        
        for import_module in critical_imports:
            if not self._can_import_module(import_module):
                integrity_issues.append({
                    "type": "critical_import_failure",
                    "module": import_module,
                    "severity": "critical",
                    "category": "system_integrity"
                })
        
        # Test critical file existence
        critical_files = [
            "claude/tools/governance/repository_analyzer.py",
            "claude/tools/governance/root_directory_cleanup.py",
            "claude/tools/governance/archive_consolidator.py",
            "README.md",
            "CLAUDE.md",
            "SYSTEM_STATE.md",
        ]
        
        for file_path in critical_files:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                integrity_issues.append({
                    "type": "critical_file_missing",
                    "file": file_path,
                    "severity": "critical",
                    "category": "system_integrity"
                })
        
        return integrity_issues
    
    def _generate_repair_recommendations(self, scan_results: Dict) -> List[Dict]:
        """Generate specific repair recommendations based on scan results"""
        recommendations = []
        
        # Group issues by type and generate targeted fixes
        broken_imports = scan_results["broken_imports"]
        missing_files = scan_results["missing_files"]
        orphaned_refs = scan_results["orphaned_references"]
        
        # Critical import fixes
        critical_imports = [bi for bi in broken_imports if bi["severity"] == "critical"]
        if critical_imports:
            recommendations.append({
                "priority": "critical",
                "category": "import_restoration",
                "title": "Restore Critical Module Imports",
                "description": f"Restore {len(critical_imports)} critical imports that are breaking core functionality",
                "affected_modules": [bi["module"] for bi in critical_imports],
                "repair_action": "move_from_archive_to_active",
                "estimated_effort": "high",
                "files_to_restore": self._identify_files_to_restore(critical_imports)
            })
        
        # ServiceDesk FOB restoration
        servicedesk_issues = [bi for bi in broken_imports if "servicedesk" in bi.get("module", "").lower()]
        if servicedesk_issues:
            recommendations.append({
                "priority": "critical",
                "category": "servicedesk_restoration", 
                "title": "Restore ServiceDesk FOB Ecosystem",
                "description": "ServiceDesk Analytics FOBs were incorrectly archived while still being actively used",
                "affected_files": [si["file"] for si in servicedesk_issues],
                "repair_action": "restore_servicedesk_fobs",
                "estimated_effort": "medium",
                "specific_fobs_needed": [
                    "servicedesk_analytics_fob.py",
                    "servicedesk/core_analytics_fob.py",
                    "servicedesk/temporal_analytics_fob.py",
                    "servicedesk/client_intelligence_fob.py",
                    "servicedesk/automation_intelligence_fob.py",
                    "servicedesk/training_intelligence_fob.py",
                    "servicedesk/escalation_intelligence_fob.py",
                    "servicedesk/base_fob.py",
                    "servicedesk/orchestrator_fob.py"
                ]
            })
        
        # File reference fixes
        high_priority_missing = [mf for mf in missing_files if mf["severity"] in ["critical", "high"]]
        if high_priority_missing:
            recommendations.append({
                "priority": "high",
                "category": "file_reference_repair",
                "title": "Fix Missing File References",
                "description": f"Update {len(high_priority_missing)} file references to point to correct locations",
                "repair_action": "update_file_paths",
                "estimated_effort": "medium"
            })
        
        return recommendations
    
    def _identify_files_to_restore(self, critical_imports: List[Dict]) -> List[str]:
        """Identify archived files that need to be restored"""
        files_to_restore = []
        archive_path = self.repo_path / "archive/historical/2025/tools_old"
        
        for import_issue in critical_imports:
            module = import_issue["module"]
            if module.startswith("claude.tools."):
                # Convert module path to file path
                module_path = module.replace("claude.tools.", "").replace(".", "/")
                archived_file = archive_path / f"{module_path}.py"
                if archived_file.exists():
                    files_to_restore.append(str(archived_file.relative_to(self.repo_path)))
        
        return files_to_restore
    
    def _calculate_system_health(self, scan_results: Dict) -> str:
        """Calculate overall system health based on scan results"""
        critical_issues = 0
        high_issues = 0
        
        for category in ["broken_imports", "missing_files", "system_integrity_issues"]:
            for issue in scan_results.get(category, []):
                severity = issue.get("severity")
                # Don't count try-protected imports as severe issues
                if issue.get("try_protected") and severity in ["medium", "low"]:
                    continue
                    
                if severity == "critical":
                    critical_issues += 1
                elif severity == "high":
                    high_issues += 1
        
        if critical_issues > 0:
            return "critical_failure"
        elif high_issues > 5:
            return "degraded"
        elif high_issues > 0:
            return "minor_issues"
        else:
            return "healthy"
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning"""
        file_str = str(file_path)
        return any(re.search(pattern, file_str) for pattern in self.exclude_patterns)
    
    def save_scan_results(self, output_file: str = None) -> str:
        """Save scan results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"${MAIA_ROOT}/claude/context/session/governance_analysis/dependency_scan_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.scan_results, f, indent=2)
        
        return output_file
    
    def print_summary(self):
        """Print a summary of scan results"""
        if not self.scan_results:
            print("❌ No scan results available")
            return
            
        summary = self.scan_results["scan_summary"]
        
        print("\n" + "="*60)
        print("📊 DEPENDENCY SCAN SUMMARY")
        print("="*60)
        
        print(f"🔍 System Health Status: {summary['system_health_status'].upper()}")
        print(f"⚠️  Broken Imports: {summary['total_broken_imports']} ({summary.get('unprotected_broken_imports', 0)} unprotected, {summary.get('try_protected_imports', 0)} try-protected)")
        print(f"📁 Missing Files: {summary['total_missing_files']}")  
        print(f"🔗 Orphaned References: {summary['total_orphaned_references']}")
        print(f"🏛️ System Integrity Issues: {summary['total_integrity_issues']}")
        print(f"🔧 Repair Recommendations: {summary['total_recommendations']}")
        
        # Show critical issues
        print("\n🚨 CRITICAL ISSUES:")
        critical_count = 0
        for category in ["broken_imports", "missing_files", "system_integrity_issues"]:
            for issue in self.scan_results.get(category, []):
                if issue.get("severity") == "critical":
                    critical_count += 1
                    print(f"   ❌ {issue.get('category', 'unknown')}: {issue.get('module', issue.get('file', 'unknown'))}")
        
        if critical_count == 0:
            print("   ✅ No critical issues found")
        
        print("\n📋 TOP RECOMMENDATIONS:")
        for rec in self.scan_results.get("recommendations", [])[:3]:
            print(f"   🔧 {rec['title']} (Priority: {rec['priority']})")

def main():
    import sys
    
    scanner = DependencyScanner()
    
    if len(sys.argv) < 2:
        print("Dependency Scanner - System Integrity Validation")
        print("Commands:")
        print("  scan     - Run comprehensive dependency scan")
        print("  summary  - Show summary of last scan")
        print("  save     - Save scan results to file")
        return
    
    command = sys.argv[1]
    
    if command == "scan":
        print("🚀 Starting comprehensive dependency scan...")
        results = scanner.scan_all_dependencies()
        scanner.print_summary()
        
        # Auto-save results
        output_file = scanner.save_scan_results()
        print(f"\n💾 Scan results saved to: {output_file}")
        
    elif command == "summary":
        # Try to load most recent scan
        try:
            scan_files = list(Path("${MAIA_ROOT}/claude/context/session/governance_analysis").glob("dependency_scan_*.json"))
            if scan_files:
                latest_scan = max(scan_files, key=lambda x: x.stat().st_mtime)
                with open(latest_scan, 'r') as f:
                    scanner.scan_results = json.load(f)
                scanner.print_summary()
            else:
                print("❌ No previous scan results found. Run 'scan' first.")
        except Exception as e:
            print(f"❌ Error loading scan results: {e}")
            
    elif command == "save":
        if scanner.scan_results:
            output_file = scanner.save_scan_results()
            print(f"💾 Scan results saved to: {output_file}")
        else:
            print("❌ No scan results to save. Run 'scan' first.")

if __name__ == "__main__":
    main()