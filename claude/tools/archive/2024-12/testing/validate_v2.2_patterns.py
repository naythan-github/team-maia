#!/usr/bin/env python3
"""
Validate v2.2 Patterns in Agents
================================

Purpose: Check that agents have all 5 advanced patterns from v2.2 template
"""

import sys
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PatternCheck:
    pattern_name: str
    check_string: str
    found: bool
    location: str


def validate_agent_patterns(agent_file: Path) -> dict:
    """Check if agent has all 5 v2.2 advanced patterns"""

    with open(agent_file, 'r') as f:
        content = f.read()

    patterns = {
        "self_reflection": PatternCheck(
            "Self-Reflection & Review",
            "Self-Reflection & Review",
            "Self-Reflection & Review" in content or "Self-Reflection Checkpoint" in content,
            "Core Behavior Principles"
        ),
        "review_pattern": PatternCheck(
            "Review in Example",
            "SELF-REVIEW",
            "SELF-REVIEW" in content or "Self-Review" in content,
            "Few-Shot Examples"
        ),
        "prompt_chaining": PatternCheck(
            "Prompt Chaining",
            "When to Use Prompt Chaining" in content or "Prompt Chaining" in content or "prompt chaining" in content,
            "When to Use Prompt Chaining" in content or "prompt chaining" in content,
            "Problem-Solving Approach"
        ),
        "explicit_handoff": PatternCheck(
            "Explicit Handoff",
            "HANDOFF DECLARATION" in content or "Handoff Declaration" in content,
            "HANDOFF DECLARATION" in content or "Handoff Declaration Pattern" in content,
            "Integration Points"
        ),
        "test_frequently": PatternCheck(
            "Test Frequently",
            "Test frequently" in content or "Testing" in content,
            "Test frequently" in content or "Self-Reflection Checkpoint" in content,
            "Problem-Solving Approach"
        )
    }

    patterns_found = sum(1 for p in patterns.values() if p.found)
    all_patterns = patterns_found == 5

    lines = content.split('\n')
    size = len(lines)

    return {
        "agent_file": agent_file.name,
        "size": size,
        "patterns": patterns,
        "patterns_found": patterns_found,
        "all_patterns": all_patterns
    }


def test_agents():
    """Test all 5 agents for v2.2 patterns"""

    agents_dir = Path("claude/agents")

    agents_to_test = [
        "dns_specialist_agent_v2.md",
        "sre_principal_engineer_agent_v2.md",
        "azure_solutions_architect_agent_v2.md",
        "service_desk_manager_agent_v2.md",
        "ai_specialists_agent_v2.md"
    ]

    print("="*80)
    print("V2.2 PATTERN VALIDATION TEST")
    print("="*80)
    print("\nChecking 5 agents for advanced patterns\n")

    results = []

    for agent_file in agents_to_test:
        file_path = agents_dir / agent_file
        if file_path.exists():
            result = validate_agent_patterns(file_path)
            results.append(result)

            status = "✅" if result['all_patterns'] else "⚠️"
            print(f"{status} {agent_file}")
            print(f"   Size: {result['size']} lines")
            print(f"   Patterns: {result['patterns_found']}/5")

            for pattern_key, pattern in result['patterns'].items():
                status = "✅" if pattern.found else "❌"
                print(f"     {status} {pattern.pattern_name}")
        else:
            print(f"❌ {agent_file} - NOT FOUND")
        print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)

    agents_with_all = sum(1 for r in results if r['all_patterns'])
    avg_patterns = sum(r['patterns_found'] for r in results) / len(results) if results else 0
    avg_size = sum(r['size'] for r in results) / len(results) if results else 0

    print(f"\nAgents tested: {len(results)}/5")
    print(f"Agents with all patterns: {agents_with_all}/5")
    print(f"Average patterns per agent: {avg_patterns:.1f}/5")
    print(f"Average size: {avg_size:.0f} lines")

    print(f"\n{'='*80}")
    print("PATTERN BREAKDOWN")
    print("="*80)

    pattern_names = [
        "self_reflection",
        "review_pattern",
        "prompt_chaining",
        "explicit_handoff",
        "test_frequently"
    ]

    for pattern_key in pattern_names:
        count = sum(1 for r in results if r['patterns'][pattern_key].found)
        pattern_name = results[0]['patterns'][pattern_key].pattern_name if results else pattern_key
        status = "✅" if count == 5 else "⚠️"
        print(f"{status} {pattern_name}: {count}/5 agents")

    print(f"\n{'='*80}")
    if agents_with_all == 5:
        print("✅ **ALL AGENTS UPDATED TO V2.2**")
        print("\nAll 5 agents have advanced patterns")
        print("Ready for final testing")
    elif agents_with_all > 0:
        print("⚠️ **PARTIAL UPDATE**")
        print(f"\n{agents_with_all}/5 agents updated")
        print(f"{5 - agents_with_all} agents still need patterns")
    else:
        print("❌ **NO AGENTS UPDATED**")
        print("\nAll agents need v2.2 patterns added")
        print("See: v2_to_v2.2_update_guide.md")

    print("="*80 + "\n")

    return {
        "agents_tested": len(results),
        "agents_complete": agents_with_all,
        "success": agents_with_all == 5
    }


if __name__ == "__main__":
    result = test_agents()
    sys.exit(0 if result['success'] else 1)
