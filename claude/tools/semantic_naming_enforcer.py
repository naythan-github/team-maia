#!/usr/bin/env python3
"""Semantic Naming Enforcer - Phase 2 Anti-Sprawl Implementation"""
import re
from pathlib import Path

class SemanticNamingEnforcer:
    def __init__(self):
        self.anti_patterns = [
            (r'.*v\d+.*', 'version_number'),
            (r'.*_new[_\.].*', 'temporal_new'),
            (r'.*_old[_\.].*', 'temporal_old'),
            (r'.*_temp.*', 'temporal_temp'),
            (r'.*_backup.*', 'temporal_backup'),
            (r'.*_final.*', 'temporal_final'),
        ]
    
    def check_file(self, filepath: str) -> tuple:
        """Check if file follows semantic naming (score 0-100)"""
        path = Path(filepath)
        filename = path.name.lower()
        
        # Skip archive/data
        if '/archive/' in str(path) or '/data/' in str(path):
            return (True, 100, "Archived/data file")
        
        score = 60  # Base score
        violations = []
        
        # Check anti-patterns (-30 each)
        for pattern, vtype in self.anti_patterns:
            if re.match(pattern, filename):
                violations.append(vtype)
                score -= 30
        
        # Agent naming convention (+20)
        if '/agents/' in str(path):
            if filename.endswith('_agent.md'):
                score += 20
            else:
                violations.append('agent_naming')
                score -= 20
        
        # Length check (+10 if good)
        name_len = len(path.stem)
        if 10 <= name_len <= 30:
            score += 10
        
        passed = score >= 70 and len(violations) == 0
        return (passed, max(0, min(100, score)), violations)
    
    def check_compliance(self, directory='claude/'):
        """Check overall compliance"""
        total = 0
        passed = 0
        
        for pattern in ['**/*.md', '**/*.py']:
            for filepath in Path(directory).glob(pattern):
                if '__pycache__' in str(filepath):
                    continue
                total += 1
                result, score, _ = self.check_file(str(filepath))
                if result:
                    passed += 1
        
        compliance = (passed / total * 100) if total > 0 else 100
        return compliance, total, passed

if __name__ == "__main__":
    import sys
    enforcer = SemanticNamingEnforcer()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check-compliance':
        compliance, total, passed = enforcer.check_compliance()
        print(f"📊 Compliance: {compliance:.1f}% ({passed}/{total})")
        sys.exit(0 if compliance >= 90 else 1)
    
    # Default: validate single file
    if len(sys.argv) > 1:
        result, score, violations = enforcer.check_file(sys.argv[1])
        print(f"Score: {score}/100 - {'✅ PASS' if result else '❌ FAIL'}")
        if violations:
            print(f"Violations: {', '.join(violations)}")
        sys.exit(0 if result else 1)
