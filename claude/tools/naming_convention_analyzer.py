#!/usr/bin/env python3
import re
import json
from pathlib import Path
from datetime import datetime

class NamingConventionAnalyzer:
    def __init__(self):
        self.violations = []
        self.patterns = {
            'agents': r'^[a-z]+(_[a-z]+)*_agent\.md$',
            'tools': r'^[a-z0-9]+(_[a-z0-9]+)*\.(py|md)$',
            'commands': r'^[a-z]+(_[a-z]+)*\.md$'
        }
        self.anti_patterns = [
            (r'.*v\d+.*', 'Version numbers in filename'),
            (r'.*_new[_\.].*', '"new" prefix/suffix'),
            (r'.*_old[_\.].*', '"old" prefix/suffix'),
            (r'.*_temp[_\.].*', '"temp" prefix'),
            (r'.*_test[_\.].*', '"test" prefix'),
            (r'.*_backup[_\.].*', '"backup" suffix'),
            (r'.*_final[_\.].*', '"final" suffix'),
            (r'.*_updated[_\.].*', '"updated" suffix'),
            (r'.*_improved[_\.].*', '"improved" suffix'),
            (r'.*_copy[_\.].*', '"copy" suffix'),
            (r'.*_draft[_\.].*', '"draft" suffix'),
            (r'.*_wip[_\.].*', '"wip" suffix'),
            (r'.*_latest[_\.].*', '"latest" suffix'),
            (r'.*_version\d+.*', 'Version number indicator'),
        ]

    def analyze_file(self, filepath):
        """Check if file follows naming conventions"""
        path = Path(filepath)
        filename = path.name.lower()

        violations = []

        # Skip archive directory - those are intentionally historical
        if '/archive/' in str(path):
            return violations

        # Skip data directory - dynamic content
        if '/claude/data/' in str(path):
            return violations

        # Check for anti-patterns
        for anti_pattern, description in self.anti_patterns:
            if re.match(anti_pattern, filename):
                violations.append({
                    'type': 'anti_pattern',
                    'pattern': anti_pattern,
                    'description': description
                })

        # Check specific directory conventions
        if '/agents/' in str(path) and path.suffix == '.md':
            if not re.match(self.patterns['agents'], filename):
                violations.append({
                    'type': 'convention',
                    'description': 'Agent naming violation: should be {function}_agent.md'
                })

        elif '/tools/' in str(path) and path.suffix == '.py':
            if not re.match(self.patterns['tools'], filename):
                violations.append({
                    'type': 'convention',
                    'description': 'Tool naming violation: should be {function}.py'
                })

        elif '/commands/' in str(path) and path.suffix == '.md':
            if not re.match(self.patterns['commands'], filename):
                violations.append({
                    'type': 'convention',
                    'description': 'Command naming violation: should be {workflow}.md'
                })

        return violations

    def suggest_correction(self, filepath, violations):
        """Suggest corrected filename"""
        path = Path(filepath)
        filename = path.name

        # Remove version indicators
        corrected = re.sub(r'_v\d+', '', filename)
        corrected = re.sub(r'_version\d+', '', corrected)
        corrected = re.sub(r'_new', '', corrected)
        corrected = re.sub(r'_old', '', corrected)
        corrected = re.sub(r'_temp', '', corrected)
        corrected = re.sub(r'_test', '', corrected)
        corrected = re.sub(r'_backup', '', corrected)
        corrected = re.sub(r'_final', '', corrected)
        corrected = re.sub(r'_updated', '', corrected)
        corrected = re.sub(r'_improved', '', corrected)
        corrected = re.sub(r'_copy', '', corrected)
        corrected = re.sub(r'_draft', '', corrected)
        corrected = re.sub(r'_wip', '', corrected)
        corrected = re.sub(r'_latest', '', corrected)

        # Apply directory-specific conventions
        if '/agents/' in str(path) and not corrected.endswith('_agent.md'):
            corrected = corrected.replace('.md', '_agent.md')

        return corrected

    def analyze_directory(self, base_path):
        """Analyze all files for naming violations"""
        base = Path(base_path)
        violations_report = []

        for pattern in ['**/*.md', '**/*.py']:
            for filepath in base.glob(pattern):
                if any(exclude in str(filepath) for exclude in ['.git', '__pycache__', '.pyc']):
                    continue

                violations = self.analyze_file(filepath)
                if violations:
                    correction = self.suggest_correction(filepath, violations)
                    violations_report.append({
                        'file': str(filepath),
                        'violations': violations,
                        'suggested_name': correction,
                        'suggested_path': str(filepath.parent / correction),
                        'severity': self.calculate_severity(filepath, violations)
                    })

        return violations_report

    def calculate_severity(self, filepath, violations):
        """Calculate severity of violations"""
        path_str = str(filepath)

        # Core files are critical
        if '/context/core/' in path_str or '/agents/' in path_str:
            return 'high'
        # Tools and commands are medium
        elif '/tools/' in path_str or '/commands/' in path_str:
            return 'medium'
        # Everything else is low
        else:
            return 'low'

    def generate_report(self, violations, output_file):
        """Generate violations report with action plan"""
        with open(output_file, 'w') as f:
            f.write("# Naming Convention Violations Report\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Violations**: {len(violations)}\n\n")

            # Summary by severity
            high = len([v for v in violations if v['severity'] == 'high'])
            medium = len([v for v in violations if v['severity'] == 'medium'])
            low = len([v for v in violations if v['severity'] == 'low'])

            f.write("## Summary by Severity\n\n")
            f.write(f"- 🔴 **High Priority**: {high} files (core system, agents)\n")
            f.write(f"- 🟡 **Medium Priority**: {medium} files (tools, commands)\n")
            f.write(f"- 🟢 **Low Priority**: {low} files (other)\n\n")

            # Violations by category
            f.write("## Violations and Corrections\n\n")

            # Sort by severity
            sorted_violations = sorted(violations, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']])

            for violation in sorted_violations:
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[violation['severity']]
                f.write(f"### {severity_icon} {violation['file']}\n")
                f.write(f"**Severity**: {violation['severity'].upper()}\n\n")
                f.write("**Violations:**\n")
                for v in violation['violations']:
                    f.write(f"- {v['description']}\n")
                f.write(f"\n**Suggested correction:** `{violation['suggested_path']}`\n\n")
                f.write("---\n\n")

            # Action plan
            f.write("## Action Plan\n\n")
            f.write("### Phase A: High Priority Fixes (Core System)\n")
            f.write("```bash\n")
            for violation in [v for v in sorted_violations if v['severity'] == 'high']:
                old_path = violation['file']
                new_path = violation['suggested_path']
                if old_path != new_path:
                    f.write(f"# Fix: {old_path}\n")
                    f.write(f"git mv \"{old_path}\" \"{new_path}\"\n\n")
            f.write("```\n\n")

            f.write("### Phase B: Medium Priority Fixes (Tools & Commands)\n")
            f.write("```bash\n")
            for violation in [v for v in sorted_violations if v['severity'] == 'medium']:
                old_path = violation['file']
                new_path = violation['suggested_path']
                if old_path != new_path:
                    f.write(f"# Fix: {old_path}\n")
                    f.write(f"git mv \"{old_path}\" \"{new_path}\"\n\n")
            f.write("```\n\n")

            f.write("### Phase C: Low Priority Fixes (Other)\n")
            f.write("```bash\n")
            for violation in [v for v in sorted_violations if v['severity'] == 'low']:
                old_path = violation['file']
                new_path = violation['suggested_path']
                if old_path != new_path:
                    f.write(f"# Fix: {old_path}\n")
                    f.write(f"git mv \"{old_path}\" \"{new_path}\"\n\n")
            f.write("```\n\n")

            # Validation steps
            f.write("## Post-Fix Validation\n\n")
            f.write("After each rename:\n")
            f.write("1. Test context loading: `python3 -c 'from claude.context import ufc_system'`\n")
            f.write("2. Check for broken references: `grep -r 'old_filename' claude/`\n")
            f.write("3. Validate system health: `python3 claude/tools/maia_system_health_checker.py quick-check`\n")
            f.write("4. Commit changes: `git add -A && git commit -m 'fix: rename file to follow naming conventions'`\n\n")

if __name__ == "__main__":
    analyzer = NamingConventionAnalyzer()
    violations = analyzer.analyze_directory(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
    analyzer.generate_report(violations, "claude/data/naming_violations_report.md")

    print(f"✅ Analysis complete")
    print(f"📊 Found {len(violations)} violations")
    print(f"📄 Report saved to: claude/data/naming_violations_report.md")
    print(f"\n📈 Breakdown:")

    high = len([v for v in violations if v['severity'] == 'high'])
    medium = len([v for v in violations if v['severity'] == 'medium'])
    low = len([v for v in violations if v['severity'] == 'low'])

    print(f"   🔴 High Priority: {high}")
    print(f"   🟡 Medium Priority: {medium}")
    print(f"   🟢 Low Priority: {low}")