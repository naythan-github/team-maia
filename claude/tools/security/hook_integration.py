#!/usr/bin/env python3
"""
Security Hook Integration Module
Provides integration functions for user-prompt-submit and pre-commit hooks.

This module bridges the security tools with the Maia hook system:
- check_prompt_injection(): For user-prompt-submit hook
- check_staged_files_for_secrets(): For pre-commit hook
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add maia root to path
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.security.prompt_injection_defense import PromptInjectionDefense
from claude.tools.security.secret_detector import SecretDetector


def check_prompt_injection(message: str, threshold: float = 0.8) -> Dict[str, Any]:
    """
    Check user message for prompt injection attempts.

    Called by user-prompt-submit hook to screen incoming messages.

    Args:
        message: User message to check
        threshold: Confidence threshold for blocking (default 0.8)

    Returns:
        Dict with keys:
            - is_blocked: bool - whether to block the message
            - reason: str - explanation if blocked
            - confidence: float - threat confidence score
            - threat_type: str - type of threat detected (if any)
    """
    if not message or not message.strip():
        return {
            'is_blocked': False,
            'reason': 'Empty message',
            'confidence': 0.0,
            'threat_type': None
        }

    defense = PromptInjectionDefense()
    result = defense.analyze(message)

    if result['is_threat'] and result['confidence'] >= threshold:
        return {
            'is_blocked': True,
            'reason': f"Potential prompt injection detected: {result['threat_type']} "
                      f"(confidence: {result['confidence']:.2f})",
            'confidence': result['confidence'],
            'threat_type': result['threat_type'],
            'matches': result['matches']
        }

    return {
        'is_blocked': False,
        'reason': 'No threats detected',
        'confidence': result.get('confidence', 0.0),
        'threat_type': None
    }


def check_staged_files_for_secrets(
    file_paths: List[str] = None,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Check staged files for secrets before commit.

    Called by pre-commit hook to prevent accidental secret commits.

    Args:
        file_paths: List of file paths to check. If None, uses git staged files.
        threshold: Confidence threshold for blocking (default 0.7)

    Returns:
        Dict with keys:
            - blocked: bool - whether to block the commit
            - files_with_secrets: list - files containing secrets
            - total_findings: int - total number of secrets found
            - details: list - detailed findings per file
    """
    # Get staged files if not provided
    if file_paths is None:
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                cwd=str(MAIA_ROOT)
            )
            file_paths = [f for f in result.stdout.strip().split('\n') if f]
        except Exception:
            file_paths = []

    if not file_paths:
        return {
            'blocked': False,
            'files_with_secrets': [],
            'total_findings': 0,
            'details': []
        }

    detector = SecretDetector()
    files_with_secrets = []
    all_details = []
    total_findings = 0

    for file_path in file_paths:
        # Convert to absolute path if needed
        if not Path(file_path).is_absolute():
            full_path = MAIA_ROOT / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            continue

        # Skip binary files and common non-code files
        skip_extensions = {'.pyc', '.db', '.sqlite', '.png', '.jpg', '.jpeg',
                          '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}
        if full_path.suffix.lower() in skip_extensions:
            continue

        result = detector.scan_file(str(full_path))

        # Filter to high-confidence findings
        high_confidence = [
            f for f in result.get('findings', [])
            if f.get('confidence', 0) >= threshold
        ]

        if high_confidence:
            files_with_secrets.append(file_path)
            total_findings += len(high_confidence)
            all_details.append({
                'file': file_path,
                'findings': high_confidence
            })

    return {
        'blocked': len(files_with_secrets) > 0,
        'files_with_secrets': files_with_secrets,
        'total_findings': total_findings,
        'details': all_details
    }


def main():
    """CLI interface for testing hook integration"""
    import argparse

    parser = argparse.ArgumentParser(description='Security Hook Integration')
    parser.add_argument('--check-message', '-m', help='Check message for prompt injection')
    parser.add_argument('--check-staged', '-s', action='store_true',
                        help='Check staged files for secrets')
    parser.add_argument('--check-file', '-f', help='Check specific file for secrets')

    args = parser.parse_args()

    if args.check_message:
        result = check_prompt_injection(args.check_message)
        if result['is_blocked']:
            print(f"BLOCKED: {result['reason']}")
            sys.exit(1)
        else:
            print("OK: Message passed security check")
            sys.exit(0)

    elif args.check_staged:
        result = check_staged_files_for_secrets()
        if result['blocked']:
            print(f"BLOCKED: Found secrets in {len(result['files_with_secrets'])} files")
            for detail in result['details']:
                print(f"\n  {detail['file']}:")
                for finding in detail['findings']:
                    print(f"    [{finding['severity']}] Line {finding.get('line', 'N/A')}: "
                          f"{finding['description']}")
            sys.exit(1)
        else:
            print("OK: No secrets found in staged files")
            sys.exit(0)

    elif args.check_file:
        result = check_staged_files_for_secrets([args.check_file])
        if result['blocked']:
            print(f"BLOCKED: Found {result['total_findings']} secrets")
            sys.exit(1)
        else:
            print("OK: No secrets found")
            sys.exit(0)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
