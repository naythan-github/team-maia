#!/usr/bin/env python3
"""
Documentation Enforcement Hook

Pre-commit hook that enforces documentation standards and compliance.
Prevents commits with inadequate documentation and provides improvement guidance.

Integration Points:
- Git pre-commit hook
- Real-time file monitoring
- Claude Code submission validation
- System change verification

Enforcement Levels:
- STRICT: Block commits below compliance threshold
- WARNING: Allow commits with warnings
- ADVISORY: Informational only
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from claude.tools.advanced_documentation_intelligence import DocumentationIntelligenceSystem
    from claude.tools.path_manager import get_path_manager
    DOCUMENTATION_SYSTEM_AVAILABLE = True
except ImportError:
    DOCUMENTATION_SYSTEM_AVAILABLE = False


class DocumentationEnforcementHook:
    """Documentation enforcement hook for git and system integration"""
    
    def __init__(self, enforcement_level: str = "WARNING"):
        self.enforcement_level = enforcement_level  # STRICT, WARNING, ADVISORY
        self.min_compliance_score = 0.6
        self.path_manager = None
        self.doc_system = None
        
        if DOCUMENTATION_SYSTEM_AVAILABLE:
            self.path_manager = get_path_manager()
            self.doc_system = DocumentationIntelligenceSystem()
    
    def check_pre_commit(self) -> Tuple[bool, str]:
        """Check documentation compliance before commit"""
        if not DOCUMENTATION_SYSTEM_AVAILABLE:
            return True, "⚠️  Documentation system not available"
        
        try:
            # Get staged files
            staged_files = self._get_staged_files()
            if not staged_files:
                return True, "✅ No files to check"
            
            # Filter for documentation-relevant files
            relevant_files = [f for f in staged_files if f.endswith(('.py', '.md'))]
            if not relevant_files:
                return True, "✅ No documentation-relevant files"
            
            # Check compliance for each file
            violations = []
            warnings = []
            
            for file_path in relevant_files:
                if os.path.exists(file_path):
                    metrics = self.doc_system.tracker.assess_file_compliance(file_path)
                    
                    if metrics.compliance_score < self.min_compliance_score:
                        violation = {
                            'file': file_path,
                            'score': metrics.compliance_score,
                            'issues': metrics.quality_issues,
                            'suggestions': metrics.improvement_suggestions
                        }
                        
                        if self.enforcement_level == "STRICT":
                            violations.append(violation)
                        else:
                            warnings.append(violation)
            
            # Generate report
            return self._generate_enforcement_report(violations, warnings, relevant_files)
            
        except Exception as e:
            return True, f"⚠️  Documentation check error: {e}"
    
    def _get_staged_files(self) -> List[str]:
        """Get list of staged files from git"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []
    
    def _generate_enforcement_report(self, violations: List[Dict], warnings: List[Dict], 
                                   total_files: List[str]) -> Tuple[bool, str]:
        """Generate enforcement report"""
        
        # Determine if commit should be blocked
        should_block = len(violations) > 0
        
        report_lines = []
        report_lines.append("📋 DOCUMENTATION COMPLIANCE REPORT")
        report_lines.append("=" * 50)
        
        if violations:
            report_lines.append(f"\n❌ COMPLIANCE VIOLATIONS ({len(violations)} files):")
            for v in violations:
                file_name = Path(v['file']).name
                report_lines.append(f"   • {file_name}: {v['score']:.1%} compliance")
                for issue in v['issues'][:2]:
                    report_lines.append(f"     - {issue}")
                if v['suggestions']:
                    report_lines.append(f"     → {v['suggestions'][0]}")
        
        if warnings:
            report_lines.append(f"\n⚠️  COMPLIANCE WARNINGS ({len(warnings)} files):")
            for w in warnings:
                file_name = Path(w['file']).name
                report_lines.append(f"   • {file_name}: {w['score']:.1%} compliance")
        
        # Summary
        total_checked = len([f for f in total_files if f.endswith(('.py', '.md'))])
        report_lines.append(f"\n📊 SUMMARY:")
        report_lines.append(f"   • Files checked: {total_checked}")
        report_lines.append(f"   • Violations: {len(violations)}")
        report_lines.append(f"   • Warnings: {len(warnings)}")
        report_lines.append(f"   • Enforcement: {self.enforcement_level}")
        
        if should_block:
            report_lines.append(f"\n🚫 COMMIT BLOCKED")
            report_lines.append(f"   • Fix documentation issues above minimum {self.min_compliance_score:.1%}")
            report_lines.append(f"   • Run: python claude/tools/advanced_documentation_intelligence.py")
            report_lines.append(f"   • Or set enforcement to WARNING in hook configuration")
        elif warnings:
            report_lines.append(f"\n✅ COMMIT ALLOWED (with warnings)")
            report_lines.append(f"   • Consider improving documentation quality")
        else:
            report_lines.append(f"\n✅ DOCUMENTATION COMPLIANCE PASSED")
        
        return not should_block, "\n".join(report_lines)
    
    def install_git_hook(self) -> bool:
        """Install as git pre-commit hook"""
        try:
            git_root = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            hooks_dir = Path(git_root) / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            
            hook_path = hooks_dir / "pre-commit"
            
            hook_content = f'''#!/bin/bash
# Documentation Enforcement Pre-commit Hook
# Auto-generated by Maia Documentation Intelligence System

python3 "{__file__}" --pre-commit
exit $?
'''
            
            with open(hook_path, 'w') as f:
                f.write(hook_content)
            
            # Make executable
            os.chmod(hook_path, 0o755)
            
            print(f"✅ Documentation enforcement hook installed: {hook_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install git hook: {e}")
            return False
    
    def check_system_compliance(self) -> Dict[str, any]:
        """Check overall system documentation compliance"""
        if not DOCUMENTATION_SYSTEM_AVAILABLE:
            return {'error': 'Documentation system not available'}
        
        try:
            compliance_report = self.doc_system.analyze_system_documentation()
            
            # Add enforcement recommendations
            compliance_report['enforcement_recommendations'] = []
            
            if compliance_report['overall_compliance'] < 0.4:
                compliance_report['enforcement_recommendations'].append(
                    "URGENT: System compliance critically low - implement immediate documentation improvement"
                )
            elif compliance_report['overall_compliance'] < 0.6:
                compliance_report['enforcement_recommendations'].append(
                    "RECOMMENDED: Systematic documentation improvement needed"
                )
            
            return compliance_report
            
        except Exception as e:
            return {'error': f'Compliance check failed: {e}'}


def main():
    """Main hook execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Documentation Enforcement Hook')
    parser.add_argument('--pre-commit', action='store_true', 
                       help='Run as pre-commit hook')
    parser.add_argument('--install', action='store_true',
                       help='Install as git pre-commit hook')
    parser.add_argument('--check-system', action='store_true',
                       help='Check overall system compliance')
    parser.add_argument('--enforcement', choices=['STRICT', 'WARNING', 'ADVISORY'],
                       default='WARNING', help='Enforcement level')
    
    args = parser.parse_args()
    
    hook = DocumentationEnforcementHook(enforcement_level=args.enforcement)
    
    if args.install:
        success = hook.install_git_hook()
        sys.exit(0 if success else 1)
    
    elif args.pre_commit:
        success, report = hook.check_pre_commit()
        print(report)
        sys.exit(0 if success else 1)
    
    elif args.check_system:
        report = hook.check_system_compliance()
        print(json.dumps(report, indent=2, default=str))
        sys.exit(0)
    
    else:
        print("📋 Documentation Enforcement Hook")
        print("Available commands:")
        print("  --install       : Install as git pre-commit hook")
        print("  --pre-commit    : Run compliance check")
        print("  --check-system  : System-wide compliance report")
        print("  --enforcement   : Set enforcement level (STRICT/WARNING/ADVISORY)")


if __name__ == "__main__":
    main()