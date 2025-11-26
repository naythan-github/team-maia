#!/usr/bin/env python3
"""
Phantom Tool Auditor - Documentation Quality Validator

Scans command files for references to non-existent tools with smart filtering
to distinguish between template placeholders, documentation examples, and
actual phantom references.

SRE Pattern: Quality Audit - Periodic validation to detect documentation drift

Usage:
    python3 claude/tools/sre/phantom_tool_auditor.py                    # Full audit
    python3 claude/tools/sre/phantom_tool_auditor.py --summary          # Quick summary
    python3 claude/tools/sre/phantom_tool_auditor.py --report out.json  # JSON output
    python3 claude/tools/sre/phantom_tool_auditor.py --quick            # Changed files only
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
from collections import defaultdict

class PhantomToolAuditor:
    """Audit command files for phantom tool references"""

    # Template placeholders to ignore (known false positives)
    TEMPLATE_PLACEHOLDERS = {
        'tool_name.py',
        'agent_name.py',
        'script_name.py',
        'module_name.py',
        'your_tool.py',
    }

    # Documentation example patterns to skip
    EXAMPLE_PATTERNS = [
        r'\[tool_name\.py\]',           # Markdown placeholder
        r'\[.*_name\.py\]',              # Generic name placeholders
        r'find.*-name.*\.py',            # Find command examples
        r'example.*\.py',                # Example references
        r'your_.*\.py',                  # User placeholder
    ]

    def __init__(self):
        self.maia_root = Path(__file__).parent.parent.parent.parent
        self.phantom_refs = defaultdict(list)  # {tool_name: [(file, line_num, context)]}
        self.valid_tools = set()
        self.scanned_files = 0
        self.total_refs = 0

    def discover_all_tools(self) -> Set[str]:
        """Discover all .py files across Maia directories"""
        valid_tools = set()
        search_dirs = [
            'claude/tools',
            'claude/hooks',
            'claude/commands',
            'claude/agents',
            'claude/data',
        ]

        for search_dir in search_dirs:
            dir_path = self.maia_root / search_dir
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    # Store just the filename for simple matching
                    valid_tools.add(py_file.name)
                    # Also store relative path from maia_root for full path matching
                    rel_path = py_file.relative_to(self.maia_root)
                    valid_tools.add(str(rel_path))

        return valid_tools

    def is_template_placeholder(self, tool_ref: str, context: str) -> bool:
        """Check if reference is a template placeholder"""
        # Direct placeholder match
        if tool_ref in self.TEMPLATE_PLACEHOLDERS:
            return True

        # Pattern-based matching
        for pattern in self.EXAMPLE_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE):
                return True

        return False

    def is_comment_or_todo(self, context: str) -> bool:
        """Check if reference is in a comment or TODO"""
        context_lower = context.lower()
        return any([
            context.strip().startswith('#'),
            'todo:' in context_lower,
            'fixme:' in context_lower,
            'not yet implemented' in context_lower,
            'not implemented' in context_lower,
        ])

    def extract_tool_references(self, content: str, file_path: Path) -> List[Tuple[str, int, str]]:
        """Extract .py references from markdown content with line numbers"""
        references = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Find all .py references in line
            py_refs = re.findall(r'([a-z_][a-z0-9_]*\.py)', line, re.IGNORECASE)

            # Also find path-based references like claude/hooks/tool.py
            path_refs = re.findall(r'(claude/[a-z_/]+\.py)', line, re.IGNORECASE)

            for ref in py_refs + path_refs:
                # Get context (30 chars before and after)
                ref_pos = line.find(ref)
                context_start = max(0, ref_pos - 30)
                context_end = min(len(line), ref_pos + len(ref) + 30)
                context = line[context_start:context_end].strip()

                references.append((ref, line_num, context))

        return references

    def scan_command_files(self) -> None:
        """Scan all command files for tool references"""
        commands_dir = self.maia_root / "claude" / "commands"

        if not commands_dir.exists():
            print(f"❌ Commands directory not found: {commands_dir}")
            return

        for cmd_file in sorted(commands_dir.glob("*.md")):
            try:
                content = cmd_file.read_text()
                self.scanned_files += 1

                references = self.extract_tool_references(content, cmd_file)

                for tool_ref, line_num, context in references:
                    self.total_refs += 1

                    # Skip template placeholders
                    if self.is_template_placeholder(tool_ref, context):
                        continue

                    # Skip comments/TODOs (informational, not actionable)
                    if self.is_comment_or_todo(context):
                        continue

                    # Extract just filename for comparison
                    tool_filename = Path(tool_ref).name

                    # Check if tool exists (filename or full path)
                    if tool_filename not in self.valid_tools and tool_ref not in self.valid_tools:
                        self.phantom_refs[tool_ref].append({
                            'file': cmd_file.name,
                            'line': line_num,
                            'context': context
                        })

            except Exception as e:
                print(f"⚠️  Could not scan {cmd_file.name}: {e}")

    def get_severity_level(self, phantom_count: int) -> Tuple[str, str]:
        """Determine severity level based on phantom count"""
        if phantom_count <= 200:
            return "INFO", "🟢"
        elif phantom_count <= 400:
            return "WARN", "🟡"
        else:
            return "ALERT", "🔴"

    def generate_summary(self) -> Dict:
        """Generate audit summary"""
        phantom_count = sum(len(refs) for refs in self.phantom_refs.values())
        unique_phantoms = len(self.phantom_refs)
        severity, emoji = self.get_severity_level(phantom_count)

        return {
            'timestamp': datetime.now().isoformat(),
            'scanned_files': self.scanned_files,
            'total_references': self.total_refs,
            'phantom_references': phantom_count,
            'unique_phantoms': unique_phantoms,
            'severity': severity,
            'severity_emoji': emoji,
            'valid_tools_discovered': len(self.valid_tools),
            'phantom_details': dict(self.phantom_refs)
        }

    def print_summary_report(self, summary: Dict):
        """Print concise summary report"""
        print("\n" + "="*60)
        print("📊 PHANTOM TOOL AUDIT SUMMARY")
        print("="*60)
        print(f"{summary['severity_emoji']} Status: {summary['severity']}")
        print(f"📁 Files Scanned: {summary['scanned_files']}")
        print(f"🔍 Total References: {summary['total_references']}")
        print(f"✅ Valid Tools Found: {summary['valid_tools_discovered']}")
        print(f"👻 Phantom References: {summary['phantom_references']} ({summary['unique_phantoms']} unique)")
        print("="*60)

        # Severity interpretation
        if summary['severity'] == 'INFO':
            print("✅ Documentation quality is good (baseline noise)")
        elif summary['severity'] == 'WARN':
            print("⚠️  Documentation debt accumulating (cleanup recommended)")
        else:
            print("🚨 Significant documentation drift detected (cleanup required)")

    def print_detailed_report(self, summary: Dict):
        """Print detailed report with all phantoms"""
        self.print_summary_report(summary)

        if summary['unique_phantoms'] > 0:
            print("\n" + "="*60)
            print("👻 PHANTOM TOOL DETAILS")
            print("="*60)

            # Sort by frequency (most referenced phantoms first)
            sorted_phantoms = sorted(
                self.phantom_refs.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )

            for tool_name, occurrences in sorted_phantoms[:20]:  # Top 20
                print(f"\n❌ {tool_name} ({len(occurrences)} references)")
                for occ in occurrences[:3]:  # Show first 3 occurrences
                    print(f"   📄 {occ['file']}:{occ['line']}")
                    print(f"      {occ['context']}")
                if len(occurrences) > 3:
                    print(f"   ... and {len(occurrences) - 3} more")

            if len(sorted_phantoms) > 20:
                print(f"\n... and {len(sorted_phantoms) - 20} more phantom tools")

        print("\n" + "="*60)

    def save_json_report(self, summary: Dict, output_path: str):
        """Save detailed JSON report"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📄 JSON report saved: {output_file}")

    def run_audit(self, mode: str = 'detailed', output_path: str = None) -> Dict:
        """Run complete audit"""
        print("🔍 Discovering valid tools...")
        self.valid_tools = self.discover_all_tools()
        print(f"   Found {len(self.valid_tools)} valid tools")

        print("\n📖 Scanning command files...")
        self.scan_command_files()
        print(f"   Scanned {self.scanned_files} command files")

        print("\n📊 Generating report...")
        summary = self.generate_summary()

        if mode == 'summary':
            self.print_summary_report(summary)
        elif mode == 'detailed':
            self.print_detailed_report(summary)

        if output_path:
            self.save_json_report(summary, output_path)

        return summary


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Phantom Tool Auditor - Documentation Quality Validator"
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary only (no details)'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Save JSON report to specified path'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode (same as full for now, placeholder for future optimization)'
    )

    args = parser.parse_args()

    auditor = PhantomToolAuditor()
    mode = 'summary' if args.summary else 'detailed'
    summary = auditor.run_audit(mode=mode, output_path=args.report)

    # Exit code based on severity
    severity_exit_codes = {'INFO': 0, 'WARN': 0, 'ALERT': 1}
    return severity_exit_codes.get(summary['severity'], 0)


if __name__ == "__main__":
    sys.exit(main())
