#!/usr/bin/env python3
"""
Output Critic - Self-Critique Before Completion

Implements the Review and Critique (Generator + Critic) pattern:
  CURRENT: Agent generates -> Done
  AGENTIC: Agent generates -> Critic evaluates -> Agent refines -> Done

Key Features:
- Lightweight critic function (rules-based + local LLM)
- Checks: completeness, accuracy claims, missing edge cases
- Force refinement pass if score < threshold
- Detailed feedback for improvement

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 1)
"""

import re
import json
import requests
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum


class CritiqueCategory(Enum):
    """Categories for critique checks"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    EDGE_CASES = "edge_cases"
    ACTIONABILITY = "actionability"
    CLARITY = "clarity"
    SAFETY = "safety"


@dataclass
class CritiqueIssue:
    """A single issue found by the critic"""
    category: CritiqueCategory
    severity: str  # low, medium, high
    description: str
    suggestion: str
    location: Optional[str] = None  # Where in the output the issue was found


@dataclass
class CritiqueResult:
    """Complete critique result"""
    output_hash: str
    overall_score: float  # 0.0-1.0
    passed: bool
    issues: List[CritiqueIssue]
    strengths: List[str]
    refinement_needed: bool
    refinement_prompt: Optional[str]
    category_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_hash": self.output_hash,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "issues": [
                {
                    "category": i.category.value,
                    "severity": i.severity,
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "location": i.location
                }
                for i in self.issues
            ],
            "strengths": self.strengths,
            "refinement_needed": self.refinement_needed,
            "refinement_prompt": self.refinement_prompt,
            "category_scores": self.category_scores
        }


class OutputCritic:
    """
    Self-Critique System for Agent Outputs.

    Combines rules-based checks with optional LLM evaluation
    to ensure output quality before delivery.
    """

    # Severity weights for scoring
    SEVERITY_WEIGHTS = {
        "low": 0.1,
        "medium": 0.25,
        "high": 0.5
    }

    # Quality threshold for passing
    DEFAULT_THRESHOLD = 0.7

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        use_llm: bool = True,
        llm_model: str = "llama3.2:3b"
    ):
        """
        Initialize Output Critic.

        Args:
            threshold: Minimum score to pass (default: 0.7)
            use_llm: Use local LLM for semantic evaluation (default: True)
            llm_model: Ollama model for LLM evaluation (default: llama3.2:3b)
        """
        self.threshold = threshold
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"

    def _compute_hash(self, text: str) -> str:
        """Compute hash for output tracking"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:8]

    def _llm_call(self, prompt: str) -> Optional[str]:
        """Make a call to local LLM"""
        if not self.use_llm:
            return None

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception:
            return None

    # ========== RULES-BASED CHECKS ==========

    def _check_completeness(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check if output is complete"""
        issues = []

        # Check for TODO/FIXME markers
        if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', output, re.IGNORECASE):
            issues.append(CritiqueIssue(
                category=CritiqueCategory.COMPLETENESS,
                severity="high",
                description="Output contains TODO/FIXME markers indicating incomplete work",
                suggestion="Complete the marked sections before delivery"
            ))

        # Check for placeholder text
        placeholder_patterns = [
            r'\[.*?\]',  # [placeholder]
            r'<.*?>',     # <placeholder>
            r'\.{3,}',    # ...
            r'\bTBD\b',
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, output) and pattern not in [r'\.{3,}']:
                matches = re.findall(pattern, output)
                # Filter out legitimate markdown links and HTML
                real_placeholders = [m for m in matches if not re.match(r'\[.*?\]\(', m) and m not in ['<', '>']]
                if real_placeholders:
                    issues.append(CritiqueIssue(
                        category=CritiqueCategory.COMPLETENESS,
                        severity="medium",
                        description=f"Output contains placeholder text: {real_placeholders[:3]}",
                        suggestion="Replace placeholders with actual content"
                    ))
                    break

        # Check for trailing sentences
        if output.strip().endswith((',', ':', '-')):
            issues.append(CritiqueIssue(
                category=CritiqueCategory.COMPLETENESS,
                severity="medium",
                description="Output ends with incomplete sentence",
                suggestion="Complete the final sentence"
            ))

        # Check for empty sections (markdown headers without content)
        header_pattern = r'^(#{1,6}\s+.+)$'
        lines = output.split('\n')
        for i, line in enumerate(lines[:-1]):
            if re.match(header_pattern, line.strip()):
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not next_line or re.match(header_pattern, next_line):
                    issues.append(CritiqueIssue(
                        category=CritiqueCategory.COMPLETENESS,
                        severity="low",
                        description=f"Empty section found: {line.strip()[:50]}",
                        suggestion="Add content or remove empty section",
                        location=line.strip()
                    ))

        return issues

    def _check_accuracy(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check for accuracy concerns"""
        issues = []

        # Check for overconfident claims
        overconfident_patterns = [
            (r'\b(guarantee|ensures?|always|never|impossible)\b', "high"),
            (r'\b(definitely|absolutely|certainly|undoubtedly)\b', "medium"),
            (r'\b100%\b', "high"),
        ]

        for pattern, severity in overconfident_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.ACCURACY,
                    severity=severity,
                    description=f"Output contains overconfident claim (matched: {pattern})",
                    suggestion="Add qualifiers or confidence bounds to claims"
                ))
                break  # Only report once

        # Check for unsubstantiated statistics
        stat_pattern = r'\b\d+(\.\d+)?%'
        stats = re.findall(stat_pattern, output)
        if len(stats) > 2:
            # Multiple statistics - check if they have sources
            if not re.search(r'(source|according to|based on|per |research)', output, re.IGNORECASE):
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.ACCURACY,
                    severity="medium",
                    description="Multiple statistics without cited sources",
                    suggestion="Add sources for statistical claims or note they are estimates"
                ))

        return issues

    def _check_edge_cases(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check for missing edge case handling"""
        issues = []

        # If output contains code, check for error handling
        if '```' in output:
            code_blocks = re.findall(r'```[\w]*\n(.*?)```', output, re.DOTALL)
            for code in code_blocks:
                # Check for missing error handling in Python
                if 'def ' in code and 'except' not in code and 'raise' not in code:
                    if 'open(' in code or 'request' in code or 'connect' in code:
                        issues.append(CritiqueIssue(
                            category=CritiqueCategory.EDGE_CASES,
                            severity="medium",
                            description="Code with I/O operations lacks error handling",
                            suggestion="Add try/except blocks for I/O operations"
                        ))

                # Check for missing input validation
                if 'def ' in code and 'if ' not in code:
                    issues.append(CritiqueIssue(
                        category=CritiqueCategory.EDGE_CASES,
                        severity="low",
                        description="Function may lack input validation",
                        suggestion="Consider adding input validation or type hints"
                    ))

        # Check for "happy path only" indicators
        if re.search(r'\b(should work|will work|works fine)\b', output, re.IGNORECASE):
            if not re.search(r'\b(however|but|note|warning|caveat)\b', output, re.IGNORECASE):
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.EDGE_CASES,
                    severity="low",
                    description="Output focuses on happy path without mentioning limitations",
                    suggestion="Add notes about potential edge cases or limitations"
                ))

        return issues

    def _check_actionability(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check if output is actionable"""
        issues = []
        query = context.get('query', '').lower()

        # If query asks for action, output should contain actionable items
        action_keywords = ['how to', 'how do i', 'steps to', 'help me', 'can you']
        is_action_query = any(kw in query for kw in action_keywords)

        if is_action_query:
            # Check for numbered steps or bullet points
            has_steps = bool(re.search(r'^\s*(\d+\.|[-*•])\s', output, re.MULTILINE))
            has_code = '```' in output

            if not has_steps and not has_code:
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.ACTIONABILITY,
                    severity="medium",
                    description="Action query received explanation without clear steps",
                    suggestion="Add numbered steps or concrete actions"
                ))

        # Check for vague recommendations
        vague_patterns = [
            r'\b(you should consider|you might want to|perhaps|maybe)\b.*\.',
        ]
        vague_count = 0
        for pattern in vague_patterns:
            vague_count += len(re.findall(pattern, output, re.IGNORECASE))

        if vague_count >= 3:
            issues.append(CritiqueIssue(
                category=CritiqueCategory.ACTIONABILITY,
                severity="low",
                description="Output contains many vague recommendations",
                suggestion="Make recommendations more specific and concrete"
            ))

        return issues

    def _check_clarity(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check output clarity"""
        issues = []

        # Check for overly long paragraphs
        paragraphs = output.split('\n\n')
        for para in paragraphs:
            if len(para) > 1000 and '\n' not in para:
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.CLARITY,
                    severity="low",
                    description="Very long paragraph may be hard to read",
                    suggestion="Break into smaller paragraphs or use bullet points",
                    location=para[:50] + "..."
                ))
                break

        # Check for unexplained acronyms
        acronyms = re.findall(r'\b[A-Z]{2,5}\b', output)
        common_acronyms = {'API', 'URL', 'HTTP', 'JSON', 'SQL', 'CSS', 'HTML', 'CLI', 'GUI', 'IDE', 'SRE', 'TDD'}
        uncommon = [a for a in set(acronyms) if a not in common_acronyms]

        if len(uncommon) > 3:
            issues.append(CritiqueIssue(
                category=CritiqueCategory.CLARITY,
                severity="low",
                description=f"Multiple uncommon acronyms used: {uncommon[:5]}",
                suggestion="Define acronyms on first use"
            ))

        return issues

    def _check_safety(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Check for safety concerns"""
        issues = []

        # Check for hardcoded credentials/secrets
        secret_patterns = [
            (r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'(api_key|apikey|api-key)\s*[=:]\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'(secret|token)\s*[=:]\s*["\'][a-zA-Z0-9+/=]{20,}["\']', "Hardcoded secret/token"),
        ]

        for pattern, description in secret_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                issues.append(CritiqueIssue(
                    category=CritiqueCategory.SAFETY,
                    severity="high",
                    description=f"Potential security issue: {description}",
                    suggestion="Use environment variables or secret management"
                ))

        # Check for dangerous operations without warnings
        dangerous_patterns = [
            (r'rm\s+-rf\s+/', "Recursive delete from root"),
            (r'DROP\s+(TABLE|DATABASE)', "SQL DROP statement"),
            (r'sudo\s+chmod\s+777', "World-writable permissions"),
            (r'eval\s*\(', "Use of eval()"),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                # Check if there's a warning nearby
                if not re.search(r'(warning|caution|careful|danger|note:)', output, re.IGNORECASE):
                    issues.append(CritiqueIssue(
                        category=CritiqueCategory.SAFETY,
                        severity="high",
                        description=f"Dangerous operation without warning: {description}",
                        suggestion="Add appropriate safety warnings"
                    ))

        return issues

    # ========== LLM-BASED CRITIQUE ==========

    def _llm_critique(self, output: str, context: Dict[str, Any]) -> List[CritiqueIssue]:
        """Use LLM for semantic critique"""
        if not self.use_llm:
            return []

        query = context.get('query', 'Unknown query')

        prompt = f"""Critique this AI assistant output for quality issues.

ORIGINAL QUERY: {query}

OUTPUT TO CRITIQUE:
{output[:2000]}

Find issues in these categories:
1. COMPLETENESS - Is anything missing that should be included?
2. ACCURACY - Are there claims that seem wrong or overconfident?
3. EDGE_CASES - Are failure modes or limitations discussed?
4. ACTIONABILITY - For action requests, are steps clear?
5. CLARITY - Is it easy to understand?

Reply with JSON only:
{{"issues": [{{"category": "...", "severity": "low/medium/high", "description": "...", "suggestion": "..."}}], "strengths": ["..."]}}

If output is good, return empty issues array."""

        response = self._llm_call(prompt)

        if not response:
            return []

        try:
            # Parse JSON response
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            data = json.loads(response.strip())
            issues = []

            for issue_data in data.get("issues", []):
                try:
                    category = CritiqueCategory(issue_data.get("category", "completeness").lower())
                except ValueError:
                    category = CritiqueCategory.COMPLETENESS

                issues.append(CritiqueIssue(
                    category=category,
                    severity=issue_data.get("severity", "medium"),
                    description=issue_data.get("description", "LLM identified issue"),
                    suggestion=issue_data.get("suggestion", "Review and improve")
                ))

            return issues

        except (json.JSONDecodeError, KeyError):
            return []

    # ========== MAIN CRITIQUE ==========

    def critique(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> CritiqueResult:
        """
        Critique an agent output.

        Args:
            output: The output text to critique
            context: Optional context (query, task type, etc.)
            verbose: Print progress

        Returns:
            CritiqueResult with score and issues
        """
        context = context or {}
        output_hash = self._compute_hash(output)

        if verbose:
            print(f"\n🔍 Critiquing output ({len(output)} chars)...")

        # Collect all issues
        all_issues: List[CritiqueIssue] = []

        # Run rules-based checks
        checks = [
            ("completeness", self._check_completeness),
            ("accuracy", self._check_accuracy),
            ("edge_cases", self._check_edge_cases),
            ("actionability", self._check_actionability),
            ("clarity", self._check_clarity),
            ("safety", self._check_safety),
        ]

        category_scores = {}

        for category_name, check_func in checks:
            issues = check_func(output, context)
            all_issues.extend(issues)

            # Calculate category score
            penalty = sum(self.SEVERITY_WEIGHTS[i.severity] for i in issues)
            category_scores[category_name] = max(0, 1.0 - penalty)

            if verbose and issues:
                print(f"   {category_name}: {len(issues)} issues found")

        # Run LLM critique
        if self.use_llm:
            if verbose:
                print("   Running LLM semantic critique...")
            llm_issues = self._llm_critique(output, context)
            all_issues.extend(llm_issues)
            if verbose and llm_issues:
                print(f"   LLM found: {len(llm_issues)} additional issues")

        # Calculate overall score
        if all_issues:
            total_penalty = sum(self.SEVERITY_WEIGHTS[i.severity] for i in all_issues)
            # Cap penalty at 1.0 (score can't go negative)
            overall_score = max(0, 1.0 - min(1.0, total_penalty))
        else:
            overall_score = 1.0

        passed = overall_score >= self.threshold

        # Identify strengths
        strengths = []
        if category_scores.get('completeness', 0) >= 0.9:
            strengths.append("Complete and thorough response")
        if category_scores.get('actionability', 0) >= 0.9:
            strengths.append("Clear and actionable guidance")
        if category_scores.get('safety', 0) >= 1.0:
            strengths.append("No safety concerns")
        if not all_issues:
            strengths.append("No issues detected - high quality output")

        # Generate refinement prompt if needed
        refinement_prompt = None
        if not passed and all_issues:
            high_priority = [i for i in all_issues if i.severity in ['high', 'medium']]
            if high_priority:
                issues_text = "\n".join([f"- {i.description}" for i in high_priority[:3]])
                refinement_prompt = f"""Please revise the output to address these issues:

{issues_text}

Specific improvements needed:
{chr(10).join([f"- {i.suggestion}" for i in high_priority[:3]])}"""

        result = CritiqueResult(
            output_hash=output_hash,
            overall_score=overall_score,
            passed=passed,
            issues=all_issues,
            strengths=strengths,
            refinement_needed=not passed,
            refinement_prompt=refinement_prompt,
            category_scores=category_scores
        )

        if verbose:
            status = "✅ PASSED" if passed else "❌ NEEDS REFINEMENT"
            print(f"\n📊 Critique Result: {status}")
            print(f"   Overall Score: {overall_score:.0%}")
            print(f"   Issues Found: {len(all_issues)}")
            if strengths:
                print(f"   Strengths: {', '.join(strengths[:2])}")

        return result

    def critique_and_refine(
        self,
        output: str,
        refine_func,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 2,
        verbose: bool = True
    ) -> Tuple[str, List[CritiqueResult]]:
        """
        Critique and iteratively refine output.

        Args:
            output: Initial output to critique
            refine_func: Function(output, refinement_prompt) -> refined_output
            context: Optional context
            max_iterations: Max refinement attempts (default: 2)
            verbose: Print progress

        Returns:
            Tuple of (final_output, list of critique results)
        """
        current_output = output
        results = []

        for iteration in range(max_iterations + 1):
            if verbose:
                print(f"\n{'='*50}")
                print(f"Iteration {iteration + 1}/{max_iterations + 1}")

            result = self.critique(current_output, context, verbose=verbose)
            results.append(result)

            if result.passed:
                if verbose:
                    print(f"\n✅ Output passed critique on iteration {iteration + 1}")
                break

            if iteration < max_iterations and result.refinement_prompt:
                if verbose:
                    print(f"\n🔄 Refining output...")
                current_output = refine_func(current_output, result.refinement_prompt)
            else:
                if verbose:
                    print(f"\n⚠️  Max iterations reached, returning best effort")

        return current_output, results


def main():
    """CLI for output critic"""
    import argparse

    parser = argparse.ArgumentParser(description="Output Critic - Self-Critique System")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Critique command
    critique_parser = subparsers.add_parser('critique', help='Critique text input')
    critique_parser.add_argument('--file', '-f', help='File to critique')
    critique_parser.add_argument('--text', '-t', help='Text to critique')
    critique_parser.add_argument('--query', '-q', help='Original query context')
    critique_parser.add_argument('--threshold', type=float, default=0.7, help='Pass threshold')
    critique_parser.add_argument('--no-llm', action='store_true', help='Skip LLM evaluation')
    critique_parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.command == 'critique':
        # Get text to critique
        if args.file:
            with open(args.file, 'r') as f:
                text = f.read()
        elif args.text:
            text = args.text
        else:
            print("Error: Provide --file or --text", file=sys.stderr)
            return 1

        # Build context
        context = {}
        if args.query:
            context['query'] = args.query

        # Run critique
        critic = OutputCritic(
            threshold=args.threshold,
            use_llm=not args.no_llm
        )

        result = critic.critique(text, context, verbose=not args.json)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("\n" + "=" * 50)
            print("📋 CRITIQUE SUMMARY")
            print("=" * 50)
            status = "✅ PASSED" if result.passed else "❌ NEEDS WORK"
            print(f"Status: {status}")
            print(f"Score: {result.overall_score:.0%}")

            if result.issues:
                print(f"\n❗ Issues ({len(result.issues)}):")
                for issue in result.issues[:5]:
                    print(f"   [{issue.severity.upper()}] {issue.category.value}: {issue.description}")
                    print(f"      → {issue.suggestion}")

            if result.strengths:
                print(f"\n✨ Strengths:")
                for s in result.strengths:
                    print(f"   • {s}")

        return 0 if result.passed else 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
