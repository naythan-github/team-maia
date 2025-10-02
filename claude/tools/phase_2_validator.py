#!/usr/bin/env python3
"""Phase 2 Validator - Validates Phase 2 completion"""
import subprocess
from pathlib import Path

def validate_phase_2() -> bool:
    """Validate all Phase 2 components"""
    checks = []
    
    # Extension zones
    zones = ['claude/extensions/experimental', 'claude/extensions/personal', 'claude/extensions/archive']
    for zone in zones:
        checks.append(('Extension zone: ' + zone, Path(zone).exists()))
    
    # Enhanced lifecycle manager
    lifecycle = Path('claude/tools/file_lifecycle_manager.py')
    checks.append(('Lifecycle manager', lifecycle.exists() and 'extension_zones' in lifecycle.read_text()))
    
    # Semantic naming enforcer
    naming = Path('claude/tools/semantic_naming_enforcer.py')
    checks.append(('Semantic naming enforcer', naming.exists()))
    
    # Intelligent organizer
    organizer = Path('claude/tools/intelligent_file_organizer.py')
    checks.append(('Intelligent file organizer', organizer.exists()))
    
    # Print results
    print("🔍 Phase 2 Validation")
    print("=" * 50)
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
    print("=" * 50)
    
    all_passed = all(p for _, p in checks)
    if all_passed:
        print("🎉 Phase 2: ALL CHECKS PASSED")
    else:
        print("⚠️  Phase 2: SOME CHECKS FAILED")
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = validate_phase_2()
    sys.exit(0 if success else 1)
