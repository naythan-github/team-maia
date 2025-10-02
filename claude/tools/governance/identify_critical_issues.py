#!/usr/bin/env python3
"""
Quick identification of critical dependency issues
Focus on real system-breaking imports
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from claude.tools.governance.dependency_scanner import DependencyScanner

def identify_critical_issues():
    """Find the most critical import failures that need immediate attention"""
    scanner = DependencyScanner()
    
    # Focus on key system directories
    critical_paths = [
        "claude/tools/governance",
        "claude/tools/core", 
        "claude/tools/research",
        "claude/commands",
        "claude/agents"
    ]
    
    critical_issues = []
    
    for path_str in critical_paths:
        path = Path(path_str)
        if not path.exists():
            continue
            
        print(f"🔍 Scanning: {path_str}")
        
        for py_file in path.glob("*.py"):
            if scanner._should_exclude_file(py_file):
                continue
                
            issues = scanner._check_imports_in_file(py_file)
            
            for issue in issues:
                # Focus on critical, unprotected imports in core systems
                if (issue.get('severity') in ['critical', 'high'] and 
                    not issue.get('try_protected', False)):
                    critical_issues.append(issue)
                    print(f"  ❌ {py_file.name}:{issue['line_number']} - {issue['module']}")
    
    print(f"\n🚨 Found {len(critical_issues)} critical unprotected import issues")
    
    # Group by missing module
    missing_modules = {}
    for issue in critical_issues:
        module = issue['module']
        if module not in missing_modules:
            missing_modules[module] = []
        missing_modules[module].append(issue['file'])
    
    print(f"\n📊 Missing modules by frequency:")
    for module, files in sorted(missing_modules.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {module}: {len(files)} files affected")
        for file_path in files[:3]:  # Show first 3 files
            print(f"    - {file_path}")
        if len(files) > 3:
            print(f"    ... and {len(files)-3} more")

if __name__ == "__main__":
    identify_critical_issues()