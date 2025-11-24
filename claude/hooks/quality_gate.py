#!/usr/bin/env python3
"""
Quality Gate - Unified Quality Check Hook

Phase 2 Agentic AI Enhancement: Combines all quality checks into one gate.

Integrates:
- Output Critic (Phase 1) - content quality
- Output Validator (Phase 2) - code/config validation
- Continuous Eval (Phase 2) - learning from outcomes

Usage:
    from quality_gate import check_quality, QualityResult

    result = check_quality(response_text, query)
    if not result.passed:
        print(result.summary)
        # Consider refinement

Author: Maia System
Created: 2025-11-24 (Phase 2 Agentic AI Enhancement)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Ensure tools are importable
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "orchestration"))


@dataclass
class QualityResult:
    """Combined quality check result"""
    passed: bool
    overall_score: float
    content_score: float  # From OutputCritic
    validation_passed: bool  # From OutputValidator
    security_safe: bool
    issues: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    refinement_needed: bool = False
    refinement_prompt: Optional[str] = None

    @property
    def summary(self) -> str:
        """Human-readable summary"""
        status = "" if self.passed else ""
        lines = [f"{status} Quality: {self.overall_score:.0%}"]

        if not self.validation_passed:
            lines.append("  Code/config validation failed")
        if not self.security_safe:
            lines.append("  Security issues detected")
        if self.issues:
            lines.append(f"  Issues: {len(self.issues)}")

        return "\n".join(lines)


def check_quality(
    output: str,
    query: Optional[str] = None,
    threshold: float = 0.7,
    validate_code: bool = True,
    check_security: bool = True
) -> QualityResult:
    """
    Comprehensive quality check combining all systems.

    Args:
        output: Response text to check
        query: Original user query (for context)
        threshold: Quality threshold (default: 0.7)
        validate_code: Whether to validate code blocks
        check_security: Whether to run security checks

    Returns:
        QualityResult with combined assessment
    """
    issues = []
    warnings = []
    content_score = 1.0
    validation_passed = True
    security_safe = True

    # Phase 1: Content quality via OutputCritic
    try:
        from output_critic import OutputCritic

        critic = OutputCritic(threshold=threshold, use_llm=False)
        context = {'query': query} if query else {}
        critique_result = critic.critique(output, context)

        content_score = critique_result.overall_score

        for issue in critique_result.issues:
            issues.append({
                'source': 'critic',
                'category': issue.category.value,
                'severity': issue.severity,
                'description': issue.description
            })

    except ImportError:
        # Graceful degradation
        warnings.append("OutputCritic unavailable")

    # Phase 2: Code/Config validation via OutputValidator
    if validate_code:
        try:
            from output_validator import OutputValidator

            validator = OutputValidator()
            validation_result = validator.validate_output(output)

            validation_passed = validation_result['all_valid']

            for v in validation_result.get('validations', []):
                if not v.get('valid', True):
                    for error in v.get('errors', []):
                        issues.append({
                            'source': 'validator',
                            'category': 'code_validation',
                            'severity': 'high',
                            'description': f"{v['language']}: {error.get('message', str(error))}"
                        })

                for warning in v.get('warnings', []):
                    warnings.append(f"Code warning: {warning}")

        except ImportError:
            warnings.append("OutputValidator unavailable")

    # Phase 2: Security check
    if check_security:
        try:
            from output_validator import OutputValidator

            validator = OutputValidator()
            security_result = validator.security_check(output)

            security_safe = security_result['safe']

            for issue in security_result.get('issues', []):
                issues.append({
                    'source': 'security',
                    'category': 'security',
                    'severity': 'high',
                    'description': f"Potential {issue['type']} detected"
                })

        except ImportError:
            pass  # Already warned above

    # Calculate overall score
    overall_score = content_score
    if not validation_passed:
        overall_score *= 0.7
    if not security_safe:
        overall_score *= 0.5

    passed = overall_score >= threshold and validation_passed and security_safe

    # Generate refinement prompt if needed
    refinement_prompt = None
    if not passed and issues:
        issue_descriptions = [i['description'] for i in issues[:3]]
        refinement_prompt = f"""Please address these issues in your response:
{chr(10).join(f'- {d}' for d in issue_descriptions)}"""

    return QualityResult(
        passed=passed,
        overall_score=overall_score,
        content_score=content_score,
        validation_passed=validation_passed,
        security_safe=security_safe,
        issues=issues,
        warnings=warnings,
        refinement_needed=not passed,
        refinement_prompt=refinement_prompt
    )


def quick_check(output: str, query: Optional[str] = None) -> bool:
    """
    Quick pass/fail quality check.

    Args:
        output: Response text
        query: Original query

    Returns:
        True if quality is acceptable
    """
    result = check_quality(output, query, validate_code=False, check_security=False)
    return result.passed


def validate_before_send(output: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate output before sending to user.

    Returns dict compatible with hook systems.
    """
    result = check_quality(output, query)

    return {
        'allow': result.passed,
        'score': result.overall_score,
        'issues_count': len(result.issues),
        'refinement_prompt': result.refinement_prompt if not result.passed else None,
        'summary': result.summary
    }


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Quality Gate")
    parser.add_argument('--text', '-t', help='Text to check')
    parser.add_argument('--file', '-f', help='File to check')
    parser.add_argument('--query', '-q', help='Original query context')
    parser.add_argument('--threshold', type=float, default=0.7)
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Provide --text or --file")
        return 1

    result = check_quality(text, args.query, args.threshold)

    if args.json:
        import json
        print(json.dumps({
            'passed': result.passed,
            'overall_score': result.overall_score,
            'content_score': result.content_score,
            'validation_passed': result.validation_passed,
            'security_safe': result.security_safe,
            'issues': result.issues,
            'warnings': result.warnings
        }, indent=2))
    else:
        print(result.summary)

        if result.issues:
            print("\nIssues:")
            for issue in result.issues[:5]:
                print(f"  [{issue['severity'].upper()}] {issue['description']}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings[:3]:
                print(f"  - {warning}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
