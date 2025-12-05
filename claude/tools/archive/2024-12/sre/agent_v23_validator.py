#!/usr/bin/env python3
"""
Agent v2.3 Template Validator
SRE Principal Engineer Agent - Automated Tier 1 Validation

Validates agents against v2.3 template requirements:
- Line count: 170-200 lines
- Pattern compliance: 5 required v2.2 patterns
- Section completeness: 11 required sections
- Handoff JSON validity
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    agent: str
    validation_tier: int
    timestamp: str
    line_count: int
    line_count_target: str  # "170-200"
    line_count_pass: bool
    patterns_found: int
    patterns_total: int
    patterns_pass: bool
    patterns_missing: list
    sections_found: int
    sections_total: int
    sections_pass: bool
    sections_missing: list
    handoff_json_valid: bool
    overall_pass: bool
    issues: list
    compression_needed: Optional[float] = None  # Percentage to compress


# Required v2.2 patterns with detection regexes
REQUIRED_PATTERNS = {
    "Self-Reflection & Review": r"Self-Reflection.*Review.*⭐|⭐.*Self-Reflection.*Review",
    "Test Frequently": r"test frequently|⭐\s*test",
    "Self-Reflection Checkpoint": r"Self-Reflection Checkpoint|SELF-REFLECTION|self-review",
    "Prompt Chaining": r"Prompt Chaining.*⭐|When to Use Prompt Chaining",
    "Explicit Handoff Declaration": r"HANDOFF DECLARATION|Handoff Declaration.*⭐",
}

# Required sections with detection regexes
REQUIRED_SECTIONS = {
    "Agent Overview": r"^##\s*(Agent )?Overview",
    "Core Behavior Principles": r"^##\s*Core Behavior",
    "Core Capabilities": r"^##\s*Core (Capabilities|Specialties)",
    "Key Commands": r"^##\s*Key Commands",
    "Few-Shot Example 1": r"^##\s*Few-Shot Example 1|Example 1:",
    "Few-Shot Example 2": r"^##\s*Few-Shot Example 2|Example 2:",
    "Problem-Solving": r"^##\s*Problem-Solving",
    "Integration Points": r"^##\s*Integration",
    "Domain Reference": r"^##\s*Domain (Reference|Expertise)",
    "Model Selection": r"^##\s*Model Selection",
    "Production Status": r"^##\s*Production Status|✅.*READY",
}


def validate_agent(filepath: Path, tier: int = 1) -> ValidationResult:
    """Validate a single agent file against v2.3 template requirements."""

    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    issues = []

    # Line count validation
    line_count_pass = 170 <= line_count <= 200
    compression_needed = None
    if line_count > 200:
        compression_needed = round((1 - 200 / line_count) * 100, 1)
        issues.append(f"Line count {line_count} exceeds 200 (need {compression_needed}% compression)")
    elif line_count < 170:
        issues.append(f"Line count {line_count} below 170 (may be missing content)")

    # Pattern validation
    patterns_found = []
    patterns_missing = []
    for pattern_name, regex in REQUIRED_PATTERNS.items():
        if re.search(regex, content, re.IGNORECASE | re.MULTILINE):
            patterns_found.append(pattern_name)
        else:
            patterns_missing.append(pattern_name)
            issues.append(f"Missing pattern: {pattern_name}")

    patterns_pass = len(patterns_missing) == 0

    # Section validation
    sections_found = []
    sections_missing = []
    for section_name, regex in REQUIRED_SECTIONS.items():
        if re.search(regex, content, re.MULTILINE):
            sections_found.append(section_name)
        else:
            sections_missing.append(section_name)
            issues.append(f"Missing section: {section_name}")

    sections_pass = len(sections_missing) == 0

    # Handoff JSON validation
    handoff_json_valid = True
    handoff_match = re.search(r'Key data:\s*(\{[^}]+\})', content, re.DOTALL)
    if handoff_match:
        try:
            json.loads(handoff_match.group(1))
        except json.JSONDecodeError:
            handoff_json_valid = False
            issues.append("Handoff JSON is invalid")

    # Overall pass (Tier 1 = automated checks only)
    overall_pass = line_count_pass and patterns_pass and sections_pass and handoff_json_valid

    return ValidationResult(
        agent=filepath.name,
        validation_tier=tier,
        timestamp=datetime.now().isoformat(),
        line_count=line_count,
        line_count_target="170-200",
        line_count_pass=line_count_pass,
        patterns_found=len(patterns_found),
        patterns_total=len(REQUIRED_PATTERNS),
        patterns_pass=patterns_pass,
        patterns_missing=patterns_missing,
        sections_found=len(sections_found),
        sections_total=len(REQUIRED_SECTIONS),
        sections_pass=sections_pass,
        sections_missing=sections_missing,
        handoff_json_valid=handoff_json_valid,
        overall_pass=overall_pass,
        issues=issues,
        compression_needed=compression_needed,
    )


def validate_directory(dirpath: Path, tier: int = 1) -> list[ValidationResult]:
    """Validate all agent files in a directory."""
    results = []
    for filepath in sorted(dirpath.glob("*.md")):
        # Skip non-agent files
        if not filepath.name.endswith("_agent.md") and "agent" not in filepath.name.lower():
            continue
        results.append(validate_agent(filepath, tier))
    return results


def generate_summary(results: list[ValidationResult]) -> dict:
    """Generate summary statistics from validation results."""
    total = len(results)
    passing = sum(1 for r in results if r.overall_pass)
    line_count_pass = sum(1 for r in results if r.line_count_pass)
    pattern_pass = sum(1 for r in results if r.patterns_pass)
    section_pass = sum(1 for r in results if r.sections_pass)

    # Calculate average compression needed for oversized agents
    oversized = [r for r in results if r.compression_needed is not None]
    avg_compression = sum(r.compression_needed for r in oversized) / len(oversized) if oversized else 0

    # Top issues by frequency
    all_issues = []
    for r in results:
        all_issues.extend(r.issues)
    issue_counts = {}
    for issue in all_issues:
        # Normalize issue text
        if "Missing pattern:" in issue:
            key = issue
        elif "Missing section:" in issue:
            key = issue
        elif "exceeds 200" in issue:
            key = "Line count exceeds 200"
        else:
            key = issue
        issue_counts[key] = issue_counts.get(key, 0) + 1

    top_issues = sorted(issue_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "total_agents": total,
        "passing": passing,
        "pass_rate": f"{passing/total*100:.1f}%" if total else "N/A",
        "line_count_compliant": f"{line_count_pass}/{total}",
        "pattern_compliant": f"{pattern_pass}/{total}",
        "section_compliant": f"{section_pass}/{total}",
        "oversized_agents": len(oversized),
        "avg_compression_needed": f"{avg_compression:.1f}%",
        "top_issues": top_issues,
    }


def print_results(results: list[ValidationResult], verbose: bool = False):
    """Print validation results to console."""
    summary = generate_summary(results)

    print("\n" + "=" * 60)
    print("AGENT v2.3 TEMPLATE VALIDATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Total Agents: {summary['total_agents']}")
    print(f"Pass Rate: {summary['pass_rate']} ({summary['passing']}/{summary['total_agents']})")
    print()
    print("COMPLIANCE BREAKDOWN:")
    print(f"  Line Count (170-200): {summary['line_count_compliant']}")
    print(f"  Patterns (5/5):       {summary['pattern_compliant']}")
    print(f"  Sections (11/11):     {summary['section_compliant']}")
    print()
    print(f"Oversized Agents: {summary['oversized_agents']}")
    print(f"Avg Compression Needed: {summary['avg_compression_needed']}")
    print()

    # Print top issues
    if summary['top_issues']:
        print("TOP ISSUES:")
        for issue, count in summary['top_issues']:
            print(f"  [{count}x] {issue}")
    print()

    # Print failing agents sorted by severity
    failing = [r for r in results if not r.overall_pass]
    if failing:
        print("FAILING AGENTS (sorted by line count):")
        for r in sorted(failing, key=lambda x: -x.line_count):
            status = "❌"
            compression = f" (need {r.compression_needed}% compression)" if r.compression_needed else ""
            print(f"  {status} {r.agent}: {r.line_count} lines{compression}")
            if verbose:
                for issue in r.issues[:3]:  # Show first 3 issues
                    print(f"      - {issue}")
    print()

    # Print passing agents
    passing = [r for r in results if r.overall_pass]
    if passing:
        print("PASSING AGENTS:")
        for r in sorted(passing, key=lambda x: x.line_count):
            print(f"  ✅ {r.agent}: {r.line_count} lines")
    print()


def main():
    parser = argparse.ArgumentParser(description="Validate agents against v2.3 template")
    parser.add_argument("path", nargs="?", default=".", help="Agent file or directory path")
    parser.add_argument("--tier", type=int, default=1, choices=[1, 2, 3], help="Validation tier")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--summary-only", action="store_true", help="Only show summary")

    args = parser.parse_args()

    path = Path(args.path)

    # Default to agents directory if current dir
    if path == Path("."):
        maia_root = Path(__file__).parent.parent.parent
        path = maia_root / "agents"

    if path.is_file():
        results = [validate_agent(path, args.tier)]
    elif path.is_dir():
        results = validate_directory(path, args.tier)
    else:
        print(f"Error: Path not found: {path}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = {
            "summary": generate_summary(results),
            "results": [asdict(r) for r in results],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(results, args.verbose)

    # Exit with error if any failures
    if not all(r.overall_pass for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
