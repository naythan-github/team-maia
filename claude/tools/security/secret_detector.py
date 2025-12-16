#!/usr/bin/env python3
"""
Secret Detection System
Detects secrets, credentials, and sensitive data in text and files.

Features:
- Pattern-based detection of API keys, passwords, tokens
- File scanning with line-level findings
- Severity classification
- Placeholder detection to reduce false positives
- Statistics tracking
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SecretPattern:
    """Defines a secret detection pattern"""
    name: str
    pattern: str
    secret_type: str
    severity: str  # critical, high, medium, low
    description: str


class SecretDetector:
    """
    Detects secrets and credentials in text and files.

    Usage:
        detector = SecretDetector()
        result = detector.scan_text("API_KEY=sk-abc123...")
        file_result = detector.scan_file("/path/to/file.py")
    """

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.placeholder_patterns = self._initialize_placeholder_patterns()
        self.stats = {
            'total_scans': 0,
            'secrets_found': 0,
            'files_scanned': 0,
            'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'by_type': {},
            'start_time': datetime.now().isoformat()
        }

    def _initialize_patterns(self) -> List[SecretPattern]:
        """Initialize detection patterns for various secret types"""
        return [
            # AWS Credentials
            SecretPattern(
                name="aws_access_key",
                pattern=r"(?:^|[^A-Z0-9])([A-Z0-9]{20})(?:[^A-Z0-9]|$)",
                secret_type="aws_access_key",
                severity="critical",
                description="AWS Access Key ID"
            ),
            SecretPattern(
                name="aws_secret_key",
                pattern=r"(?i)(?:aws_secret|secret_access_key|aws_secret_access_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
                secret_type="aws_secret_key",
                severity="critical",
                description="AWS Secret Access Key"
            ),

            # OpenAI/Anthropic API Keys
            SecretPattern(
                name="openai_api_key",
                pattern=r"sk-(?:proj-)?[A-Za-z0-9]{20,}",
                secret_type="api_key",
                severity="critical",
                description="OpenAI API Key"
            ),
            SecretPattern(
                name="anthropic_api_key",
                pattern=r"sk-ant-[A-Za-z0-9-]{20,}",
                secret_type="api_key",
                severity="critical",
                description="Anthropic API Key"
            ),

            # GitHub Tokens
            SecretPattern(
                name="github_pat",
                pattern=r"ghp_[A-Za-z0-9]{36}",
                secret_type="github_token",
                severity="critical",
                description="GitHub Personal Access Token"
            ),
            SecretPattern(
                name="github_oauth",
                pattern=r"gho_[A-Za-z0-9]{36}",
                secret_type="github_token",
                severity="critical",
                description="GitHub OAuth Token"
            ),

            # Slack Tokens
            SecretPattern(
                name="slack_token",
                pattern=r"xox[baprs]-[A-Za-z0-9-]{10,}",
                secret_type="slack_token",
                severity="high",
                description="Slack Token"
            ),

            # Private Keys
            SecretPattern(
                name="rsa_private_key",
                pattern=r"-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----",
                secret_type="private_key",
                severity="critical",
                description="RSA Private Key"
            ),
            SecretPattern(
                name="generic_private_key",
                pattern=r"-----BEGIN\s+(?:EC\s+)?PRIVATE\s+KEY-----",
                secret_type="private_key",
                severity="critical",
                description="Private Key"
            ),
            SecretPattern(
                name="openssh_private_key",
                pattern=r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
                secret_type="private_key",
                severity="critical",
                description="OpenSSH Private Key"
            ),

            # Passwords in code
            SecretPattern(
                name="password_assignment",
                pattern=r"(?i)(?:password|passwd|pwd|pass)\s*[=:]\s*['\"]?([^'\"\s]{4,})['\"]?",
                secret_type="password",
                severity="high",
                description="Hardcoded password"
            ),
            SecretPattern(
                name="db_password",
                pattern=r"(?i)(?:db_password|database_password|mysql_password|postgres_password)\s*[=:]\s*['\"]([^'\"]{4,})['\"]",
                secret_type="password",
                severity="high",
                description="Database password"
            ),

            # Connection Strings
            SecretPattern(
                name="mongodb_conn",
                pattern=r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^\s]+",
                secret_type="connection_string",
                severity="high",
                description="MongoDB connection string with credentials"
            ),
            SecretPattern(
                name="postgresql_conn",
                pattern=r"postgres(?:ql)?://[^:]+:[^@]+@[^\s]+",
                secret_type="connection_string",
                severity="high",
                description="PostgreSQL connection string with credentials"
            ),
            SecretPattern(
                name="mysql_conn",
                pattern=r"mysql://[^:]+:[^@]+@[^\s]+",
                secret_type="connection_string",
                severity="high",
                description="MySQL connection string with credentials"
            ),

            # JWT Tokens
            SecretPattern(
                name="jwt_token",
                pattern=r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
                secret_type="jwt",
                severity="high",
                description="JWT Token"
            ),

            # Azure
            SecretPattern(
                name="azure_storage",
                pattern=r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]+",
                secret_type="azure_credential",
                severity="critical",
                description="Azure Storage Account Key"
            ),

            # GCP
            SecretPattern(
                name="gcp_service_account",
                pattern=r'"type"\s*:\s*"service_account"',
                secret_type="gcp_credential",
                severity="high",
                description="GCP Service Account JSON"
            ),

            # Generic API Keys
            SecretPattern(
                name="generic_api_key",
                pattern=r"(?i)(?:api[_-]?key|apikey)\s*[=:]\s*['\"]?([A-Za-z0-9_-]{20,})['\"]?",
                secret_type="api_key",
                severity="medium",
                description="Generic API Key"
            ),

            # Stripe
            SecretPattern(
                name="stripe_secret",
                pattern=r"sk_live_[A-Za-z0-9]{8,}",
                secret_type="stripe_key",
                severity="critical",
                description="Stripe Live Secret Key"
            ),

            # SendGrid
            SecretPattern(
                name="sendgrid_key",
                pattern=r"SG\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
                secret_type="sendgrid_key",
                severity="high",
                description="SendGrid API Key"
            ),
        ]

    def _initialize_placeholder_patterns(self) -> List[str]:
        """Patterns that indicate placeholder/example values"""
        return [
            r"(?i)your[_-]?(api[_-]?)?key[_-]?here",
            r"(?i)<[^>]*>",  # <INSERT_HERE>
            r"(?i)replace[_-]?me",
            r"(?i)xxx+",
            r"(?i)\$\{[^}]+\}",  # ${ENV_VAR}
            r"(?i)example",
            r"(?i)placeholder",
            r"(?i)changeme",
            r"(?i)todo",
            r"(?i)insert[_-]",
        ]

    def _is_placeholder(self, value: str) -> bool:
        """Check if a value appears to be a placeholder"""
        for pattern in self.placeholder_patterns:
            if re.search(pattern, value):
                return True
        return False

    def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Scan text for secrets.

        Args:
            text: Content to scan

        Returns:
            Dict with keys: findings, total_found, has_secrets
        """
        self.stats['total_scans'] += 1
        findings = []

        if not text:
            return {'findings': [], 'total_found': 0, 'has_secrets': False}

        for pattern in self.patterns:
            matches = re.finditer(pattern.pattern, text)
            for match in matches:
                # Get the matched value
                value = match.group(1) if match.lastindex else match.group(0)

                # Calculate confidence (reduced for placeholders)
                confidence = 0.9
                if self._is_placeholder(value) or self._is_placeholder(text[max(0, match.start()-20):match.end()+20]):
                    confidence = 0.3

                findings.append({
                    'type': pattern.secret_type,
                    'pattern_name': pattern.name,
                    'severity': pattern.severity,
                    'confidence': confidence,
                    'description': pattern.description,
                    'match': value[:20] + '...' if len(value) > 20 else value,
                    'position': match.start()
                })

        # Update stats
        high_confidence_findings = [f for f in findings if f['confidence'] >= 0.5]
        self.stats['secrets_found'] += len(high_confidence_findings)

        for finding in high_confidence_findings:
            self.stats['by_severity'][finding['severity']] = \
                self.stats['by_severity'].get(finding['severity'], 0) + 1
            self.stats['by_type'][finding['type']] = \
                self.stats['by_type'].get(finding['type'], 0) + 1

        return {
            'findings': findings,
            'total_found': len(findings),
            'has_secrets': len(high_confidence_findings) > 0
        }

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a file for secrets.

        Args:
            file_path: Path to file to scan

        Returns:
            Dict with keys: file_path, findings, total_found, has_secrets
        """
        self.stats['files_scanned'] += 1
        path = Path(file_path)

        if not path.exists():
            return {
                'file_path': file_path,
                'findings': [],
                'total_found': 0,
                'has_secrets': False,
                'error': 'File not found'
            }

        try:
            content = path.read_text(errors='ignore')
        except Exception as e:
            return {
                'file_path': file_path,
                'findings': [],
                'total_found': 0,
                'has_secrets': False,
                'error': str(e)
            }

        # Scan the content
        result = self.scan_text(content)

        # Add line numbers to findings
        lines = content.split('\n')
        for finding in result['findings']:
            pos = finding['position']
            line_num = content[:pos].count('\n') + 1
            finding['line'] = line_num
            # Get context
            if 0 < line_num <= len(lines):
                finding['line_content'] = lines[line_num - 1][:100]

        return {
            'file_path': file_path,
            'findings': result['findings'],
            'total_found': result['total_found'],
            'has_secrets': result['has_secrets']
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            'total_scans': self.stats['total_scans'],
            'files_scanned': self.stats['files_scanned'],
            'secrets_found': self.stats['secrets_found'],
            'by_severity': self.stats['by_severity'],
            'by_type': self.stats['by_type'],
            'patterns_loaded': len(self.patterns),
            'start_time': self.stats['start_time']
        }


def main():
    """CLI interface for secret detection"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Scan for secrets in text or files')
    parser.add_argument('--file', '-f', help='File to scan')
    parser.add_argument('--text', '-t', help='Text to scan')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()
    detector = SecretDetector()

    if args.file:
        result = detector.scan_file(args.file)
        print(f"\nScanning: {args.file}")
        print(f"Secrets found: {result['total_found']}")

        for finding in result['findings']:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
            print(f"\n{severity_emoji.get(finding['severity'], '⚪')} [{finding['severity'].upper()}] {finding['description']}")
            print(f"   Line {finding.get('line', 'N/A')}: {finding.get('line_content', finding['match'])}")

    elif args.text:
        result = detector.scan_text(args.text)
        print(f"Secrets found: {result['total_found']}")
        for finding in result['findings']:
            print(f"  [{finding['severity']}] {finding['description']}: {finding['match']}")

    else:
        print("Usage: python3 secret_detector.py --file <path> OR --text <content>")


if __name__ == '__main__':
    main()
