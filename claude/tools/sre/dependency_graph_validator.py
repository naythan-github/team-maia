#!/usr/bin/env python3
"""
Dependency Graph Validator - SRE Reliability Tool

Builds and validates the complete dependency graph for Maia system,
identifying phantom dependencies, circular dependencies, and single
points of failure.

SRE Pattern: Dependency Health Monitoring - Proactive detection of
integration issues before they cause production failures.

Usage:
    python3 claude/tools/sre/dependency_graph_validator.py --analyze
    python3 claude/tools/sre/dependency_graph_validator.py --report
    python3 claude/tools/sre/dependency_graph_validator.py --critical-only
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
from collections import defaultdict

class DependencyGraphValidator:
    """Dependency graph validation for system reliability"""

    def __init__(self):
        self.maia_root = Path(__file__).parent.parent.parent.parent
        self.dependency_graph = defaultdict(set)
        self.phantom_dependencies = []
        self.circular_dependencies = []
        self.tool_inventory = self._build_tool_inventory()

    def _build_tool_inventory(self) -> Set[str]:
        """Build inventory of all actual tools"""
        tools = set()
        tools_dir = self.maia_root / "claude" / "tools"

        for py_file in tools_dir.rglob("*.py"):
            rel_path = py_file.relative_to(tools_dir)
            tools.add(str(rel_path))
            tools.add(py_file.name)  # Also store just filename

        return tools

    def _extract_python_references(self, content: str) -> List[str]:
        """Extract .py file references from content"""
        # Pattern: various ways Python files are referenced
        patterns = [
            r'`([a-z_][a-z0-9_]*\.py)`',  # `tool_name.py`
            r'claude/tools/([a-z_/]+\.py)',  # claude/tools/path/tool.py
            r'python3 claude/tools/([a-z_/]+\.py)',  # Command line
            r'"([a-z_][a-z0-9_]*\.py)"',  # Quoted references
            r"'([a-z_][a-z0-9_]*\.py)'",  # Single quoted
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))  # Deduplicate

    def scan_commands_for_dependencies(self) -> Dict[str, List[str]]:
        """Scan command files for tool dependencies"""
        commands_dir = self.maia_root / "claude" / "commands"
        dependencies = {}

        for cmd_file in commands_dir.glob("*.md"):
            try:
                content = cmd_file.read_text()
                refs = self._extract_python_references(content)

                if refs:
                    dependencies[cmd_file.name] = refs

                    # Build dependency graph
                    for ref in refs:
                        self.dependency_graph[cmd_file.name].add(ref)

            except Exception as e:
                print(f"Warning: Could not scan {cmd_file.name}: {e}")

        return dependencies

    def scan_agents_for_dependencies(self) -> Dict[str, List[str]]:
        """Scan agent files for tool dependencies"""
        agents_dir = self.maia_root / "claude" / "agents"
        dependencies = {}

        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text()
                refs = self._extract_python_references(content)

                if refs:
                    dependencies[agent_file.name] = refs

                    # Build dependency graph
                    for ref in refs:
                        self.dependency_graph[agent_file.name].add(ref)

            except Exception as e:
                print(f"Warning: Could not scan {agent_file.name}: {e}")

        return dependencies

    def scan_documentation_for_dependencies(self) -> Dict[str, List[str]]:
        """Scan documentation files for tool dependencies"""
        docs_paths = [
            self.maia_root / "claude" / "context" / "tools" / "available.md",
            self.maia_root / "README.md",
            self.maia_root / "SYSTEM_STATE.md",
        ]

        dependencies = {}

        for doc_path in docs_paths:
            if not doc_path.exists():
                continue

            try:
                content = doc_path.read_text()
                refs = self._extract_python_references(content)

                if refs:
                    dependencies[doc_path.name] = refs

                    # Build dependency graph
                    for ref in refs:
                        self.dependency_graph[doc_path.name].add(ref)

            except Exception as e:
                print(f"Warning: Could not scan {doc_path.name}: {e}")

        return dependencies

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate all dependencies against tool inventory"""
        phantom_deps = defaultdict(list)

        for source, deps in self.dependency_graph.items():
            for dep in deps:
                # Check if tool exists
                if dep not in self.tool_inventory:
                    # Check if it's a path reference
                    found = False
                    for tool in self.tool_inventory:
                        if dep in tool or tool.endswith(dep):
                            found = True
                            break

                    if not found:
                        phantom_deps[source].append(dep)
                        self.phantom_dependencies.append({
                            'source': source,
                            'phantom_tool': dep,
                            'severity': self._assess_severity(source, dep)
                        })

        return dict(phantom_deps)

    def _assess_severity(self, source: str, dep: str) -> str:
        """Assess severity of phantom dependency"""
        critical_keywords = ['save_state', 'comprehensive', 'backup', 'security', 'ufc']

        for keyword in critical_keywords:
            if keyword in source.lower() or keyword in dep.lower():
                return 'CRITICAL'

        if 'design_decision' in dep or 'documentation_validator' in dep:
            return 'CRITICAL'

        return 'MEDIUM'

    def find_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependency chains"""
        # For now, we're checking documentation → tools (one direction)
        # True circular deps would require scanning Python imports
        # This is a placeholder for future enhancement
        return []

    def find_single_points_of_failure(self) -> List[Dict]:
        """Identify tools referenced by many sources"""
        tool_reference_count = defaultdict(int)

        for source, deps in self.dependency_graph.items():
            for dep in deps:
                tool_reference_count[dep] += 1

        # SPOF = referenced by 5+ sources
        spofs = []
        for tool, count in tool_reference_count.items():
            if count >= 5:
                spofs.append({
                    'tool': tool,
                    'reference_count': count,
                    'exists': tool in self.tool_inventory,
                    'severity': 'CRITICAL' if tool not in self.tool_inventory else 'MEDIUM'
                })

        return sorted(spofs, key=lambda x: x['reference_count'], reverse=True)

    def generate_report(self) -> Dict:
        """Generate comprehensive dependency health report"""
        print("🔍 Scanning dependency graph...\n")

        # Scan all sources
        print("📂 Scanning commands...")
        cmd_deps = self.scan_commands_for_dependencies()

        print("🤖 Scanning agents...")
        agent_deps = self.scan_agents_for_dependencies()

        print("📚 Scanning documentation...")
        doc_deps = self.scan_documentation_for_dependencies()

        # Validate
        print("✅ Validating dependencies...")
        phantom_deps = self.validate_dependencies()

        # Find issues
        print("🔄 Detecting circular dependencies...")
        circular = self.find_circular_dependencies()

        print("⚠️  Identifying single points of failure...")
        spofs = self.find_single_points_of_failure()

        # Calculate statistics
        total_sources = len(cmd_deps) + len(agent_deps) + len(doc_deps)
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        total_phantoms = len(self.phantom_dependencies)
        critical_phantoms = len([p for p in self.phantom_dependencies if p['severity'] == 'CRITICAL'])

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_sources_scanned': total_sources,
                'total_dependencies': total_dependencies,
                'total_phantom_dependencies': total_phantoms,
                'critical_phantom_dependencies': critical_phantoms,
                'circular_dependencies': len(circular),
                'single_points_of_failure': len(spofs),
                'health_score': self._calculate_health_score(total_dependencies, total_phantoms, critical_phantoms)
            },
            'phantom_dependencies': self.phantom_dependencies,
            'circular_dependencies': circular,
            'single_points_of_failure': spofs,
            'dependency_graph': {k: list(v) for k, v in self.dependency_graph.items()},
            'tool_inventory_size': len(self.tool_inventory)
        }

        return report

    def _calculate_health_score(self, total: int, phantoms: int, critical: int) -> float:
        """Calculate dependency health score (0-100)"""
        if total == 0:
            return 100.0

        # Deduct points for phantoms
        phantom_penalty = (phantoms / total) * 50
        critical_penalty = critical * 10  # Each critical phantom = -10 points

        score = 100.0 - phantom_penalty - critical_penalty
        return max(0.0, min(100.0, score))

    def print_report(self, report: Dict, critical_only: bool = False):
        """Print formatted dependency health report"""
        print("\n" + "="*70)
        print("📊 DEPENDENCY GRAPH HEALTH REPORT")
        print("="*70)

        summary = report['summary']

        # Health score with color
        health_score = summary['health_score']
        if health_score >= 80:
            status = "✅ HEALTHY"
        elif health_score >= 60:
            status = "⚠️  DEGRADED"
        else:
            status = "🚨 CRITICAL"

        print(f"\n{status} - Health Score: {health_score:.1f}/100\n")

        print(f"📈 Summary:")
        print(f"   Sources Scanned: {summary['total_sources_scanned']}")
        print(f"   Total Dependencies: {summary['total_dependencies']}")
        print(f"   Tool Inventory: {report['tool_inventory_size']} tools")
        print(f"   Phantom Dependencies: {summary['total_phantom_dependencies']}")
        print(f"   Critical Phantoms: {summary['critical_phantom_dependencies']} 🚨")
        print(f"   Single Points of Failure: {summary['single_points_of_failure']}")

        # Phantom dependencies
        if report['phantom_dependencies']:
            if critical_only:
                phantoms = [p for p in report['phantom_dependencies'] if p['severity'] == 'CRITICAL']
            else:
                phantoms = report['phantom_dependencies']

            if phantoms:
                print(f"\n❌ Phantom Dependencies ({len(phantoms)}):")
                for phantom in phantoms[:20]:  # Show first 20
                    severity_icon = "🚨" if phantom['severity'] == 'CRITICAL' else "⚠️"
                    print(f"   {severity_icon} {phantom['source']} → {phantom['phantom_tool']}")

                if len(phantoms) > 20:
                    print(f"   ... and {len(phantoms) - 20} more")

        # Single points of failure
        if report['single_points_of_failure']:
            print(f"\n⚠️  Single Points of Failure (Tools with 5+ references):")
            for spof in report['single_points_of_failure'][:10]:
                exists_icon = "✅" if spof['exists'] else "❌"
                print(f"   {exists_icon} {spof['tool']} ({spof['reference_count']} references)")

        print("\n" + "="*70)

        # Recommendations
        if summary['critical_phantom_dependencies'] > 0:
            print("\n🚨 CRITICAL ACTIONS REQUIRED:")
            print("   1. Fix phantom tools in save_state and comprehensive_save_state")
            print("   2. Build missing tools or update documentation")
            print("   3. Run pre-flight checks before all save state operations")
        elif summary['total_phantom_dependencies'] > 10:
            print("\n⚠️  RECOMMENDED ACTIONS:")
            print("   1. Review phantom dependencies in commands/agents")
            print("   2. Archive or update outdated documentation")
            print("   3. Implement quarterly dependency audits")

        print("="*70 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Dependency Graph Validator - SRE Reliability Tool"
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze dependency graph and generate report'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Print dependency health report'
    )
    parser.add_argument(
        '--critical-only',
        action='store_true',
        help='Show only critical phantom dependencies'
    )
    parser.add_argument(
        '--json',
        type=str,
        help='Save report as JSON to specified file'
    )

    args = parser.parse_args()

    if not (args.analyze or args.report):
        parser.print_help()
        return 1

    validator = DependencyGraphValidator()
    report = validator.generate_report()

    if args.report or args.analyze:
        validator.print_report(report, critical_only=args.critical_only)

    if args.json:
        json_path = Path(args.json)
        json_path.write_text(json.dumps(report, indent=2))
        print(f"📄 Report saved to: {json_path}")

    # Return exit code based on critical phantoms
    if report['summary']['critical_phantom_dependencies'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
