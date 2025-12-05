#!/usr/bin/env python3
"""
Focused test of LLM-enhanced dependency scanner on ServiceDesk FOBs only
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from llm_enhanced_dependency_scanner import LLMEnhancedDependencyScanner

def test_focused_scan():
    """Test LLM analysis on ServiceDesk FOBs specifically"""
    scanner = LLMEnhancedDependencyScanner()
    
    # Focus on ServiceDesk directory only
    servicedesk_path = Path(str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "tools" / "servicedesk"))
    
    if not servicedesk_path.exists():
        print("❌ ServiceDesk directory not found")
        return
    
    print("🔍 Testing LLM-enhanced analysis on ServiceDesk FOBs...")
    
    # Analyze just the ServiceDesk FOB files
    python_files = list(servicedesk_path.glob("*.py"))
    print(f"📁 Found {len(python_files)} Python files in ServiceDesk")
    
    total_issues = 0
    total_enhanced = 0
    
    for py_file in python_files:
        print(f"\n📄 Analyzing: {py_file.name}")
        
        # Get import analysis
        import_issues = scanner._check_imports_in_file(py_file)
        
        if import_issues:
            print(f"   ⚠️  Found {len(import_issues)} import issues")
            total_issues += len(import_issues)
            
            # Count LLM-enhanced issues
            enhanced_issues = [i for i in import_issues if 'llm_status' in i]
            total_enhanced += len(enhanced_issues)
            
            # Show sample LLM analysis
            for issue in enhanced_issues[:2]:  # Show first 2 LLM analyses
                print(f"   🤖 LLM Analysis:")
                print(f"      Status: {issue.get('llm_status', 'N/A')}")
                print(f"      Priority: {issue.get('llm_priority', 'N/A')}")
                print(f"      Fix: {issue.get('llm_fix_suggestion', 'N/A')[:100]}...")
        else:
            print(f"   ✅ No import issues found")
    
    print(f"\n📊 Summary:")
    print(f"   Total import issues: {total_issues}")
    print(f"   LLM-enhanced analyses: {total_enhanced}")
    print(f"   Enhancement rate: {(total_enhanced/max(total_issues,1)*100):.1f}%")

if __name__ == "__main__":
    test_focused_scan()