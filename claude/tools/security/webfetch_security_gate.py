#!/usr/bin/env python3
"""
WebFetch Security Gate - PreToolUse Hook
Layer 1: Validates URLs BEFORE fetch is executed.

This hook runs before WebFetch/WebSearch tool execution to:
- Validate URL schemes (http/https only)
- Block SSRF attempts (localhost, private IPs, cloud metadata)
- Check against domain blocklists

Install in ~/.claude/settings.local.json:
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [{"type": "command", "command": "python3 $CLAUDE_PROJECT_DIR/claude/tools/security/webfetch_security_gate.py", "timeout": 2000}]
      },
      {
        "matcher": "WebSearch",
        "hooks": [{"type": "command", "command": "python3 $CLAUDE_PROJECT_DIR/claude/tools/security/webfetch_security_gate.py", "timeout": 2000}]
      }
    ]
  }
}
"""

import json
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from claude.tools.security.ssrf_protection import SSRFProtection


# Allowed URL schemes
ALLOWED_SCHEMES = {'http', 'https'}

# Blocked schemes (dangerous)
BLOCKED_SCHEMES = {'javascript', 'data', 'file', 'ftp', 'gopher', 'vbscript'}


class WebFetchSecurityGate:
    """
    PreToolUse gate for WebFetch/WebSearch.

    Validates:
    - URL scheme (http/https only)
    - SSRF protection (no localhost, private IPs)
    - Domain blocklist

    Usage:
        gate = WebFetchSecurityGate()
        result = gate.validate_request({'url': 'http://localhost/admin', 'prompt': 'test'})
        if result['decision'] == 'block':
            reject_request(result['reason'])
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize security gate.

        Args:
            config_path: Optional path to blocklist config file
        """
        self.ssrf = SSRFProtection()
        self.config_path = config_path
        self.blocklist = self._load_blocklist()
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'allowed_requests': 0,
            'by_reason': {},
            'start_time': datetime.now().isoformat()
        }

    def _load_blocklist(self) -> List[str]:
        """Load domain blocklist from config file."""
        if not self.config_path:
            return []

        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                    return config.get('blocked_domains', [])
        except Exception:
            pass

        return []

    def validate_request(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate WebFetch/WebSearch request.

        Args:
            tool_input: The tool_input from PreToolUse hook
                       Expected: {'url': str, 'prompt': str} for WebFetch
                       Expected: {'query': str, ...} for WebSearch

        Returns:
            {
                'decision': 'allow' | 'block',
                'reason': str,
                'checks_performed': List[str],
                'threat_type': Optional[str],
                'confidence': float  # 0.0-1.0
            }
        """
        self.stats['total_requests'] += 1
        checks_performed = []

        # WebSearch with query only - no URL to validate
        if 'query' in tool_input and 'url' not in tool_input:
            self.stats['allowed_requests'] += 1
            return {
                'decision': 'allow',
                'reason': 'WebSearch query - no URL validation needed',
                'checks_performed': ['query_only_check'],
                'threat_type': None,
                'confidence': 1.0
            }

        # Get URL from input
        url = tool_input.get('url')
        if not url:
            return self._blocked_result(
                'No URL provided in request',
                'missing_url',
                checks_performed,
                confidence=1.0
            )

        # Check 1: Scheme validation
        checks_performed.append('scheme_validation')
        scheme_result = self.check_scheme(url)
        if not scheme_result['is_safe']:
            return self._blocked_result(
                f"Blocked scheme: {scheme_result['reason']}",
                'scheme',
                checks_performed,
                confidence=1.0
            )

        # Check 2: SSRF protection
        checks_performed.append('ssrf_protection')
        ssrf_result = self.check_ssrf(url)
        if not ssrf_result['is_safe']:
            return self._blocked_result(
                f"SSRF blocked: {ssrf_result['reason']}",
                'ssrf',
                checks_performed,
                confidence=0.95
            )

        # Check 3: Blocklist
        checks_performed.append('blocklist_check')
        blocklist_result = self.check_blocklist(url)
        if not blocklist_result['is_safe']:
            return self._blocked_result(
                f"Blocked domain: {blocklist_result['reason']}",
                'blocklist',
                checks_performed,
                confidence=0.9
            )

        # All checks passed
        self.stats['allowed_requests'] += 1
        return {
            'decision': 'allow',
            'reason': 'All security checks passed',
            'checks_performed': checks_performed,
            'threat_type': None,
            'confidence': 1.0
        }

    def check_scheme(self, url: str) -> Dict[str, Any]:
        """
        Validate URL scheme is http or https.

        Args:
            url: URL to check

        Returns:
            {'is_safe': bool, 'reason': str}
        """
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()

            if scheme in BLOCKED_SCHEMES:
                return {
                    'is_safe': False,
                    'reason': f"Dangerous scheme '{scheme}' is blocked"
                }

            if scheme not in ALLOWED_SCHEMES:
                return {
                    'is_safe': False,
                    'reason': f"Scheme '{scheme}' is not allowed (only http/https)"
                }

            return {
                'is_safe': True,
                'reason': f"Scheme '{scheme}' is allowed"
            }

        except Exception as e:
            return {
                'is_safe': False,
                'reason': f"Failed to parse URL: {e}"
            }

    def check_ssrf(self, url: str) -> Dict[str, Any]:
        """
        Check for SSRF vulnerabilities using SSRFProtection.

        Args:
            url: URL to check

        Returns:
            {'is_safe': bool, 'reason': str, 'threat_type': Optional[str]}
        """
        result = self.ssrf.check_url(url, resolve_dns=True)
        return {
            'is_safe': result['is_safe'],
            'reason': result['reason'],
            'threat_type': result.get('threat_type')
        }

    def check_blocklist(self, url: str) -> Dict[str, Any]:
        """
        Check URL against domain blocklist.

        Args:
            url: URL to check

        Returns:
            {'is_safe': bool, 'reason': str}
        """
        if not self.blocklist:
            return {'is_safe': True, 'reason': 'No blocklist configured'}

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''
            hostname_lower = hostname.lower()

            for blocked in self.blocklist:
                blocked_lower = blocked.lower()
                if hostname_lower == blocked_lower or hostname_lower.endswith('.' + blocked_lower):
                    return {
                        'is_safe': False,
                        'reason': f"Domain '{hostname}' is blocklisted"
                    }

            return {'is_safe': True, 'reason': 'Domain not in blocklist'}

        except Exception as e:
            return {'is_safe': False, 'reason': f"Failed to check blocklist: {e}"}

    def _blocked_result(
        self,
        reason: str,
        threat_type: str,
        checks_performed: List[str],
        confidence: float = 0.9
    ) -> Dict[str, Any]:
        """Create a blocked result and update stats."""
        self.stats['blocked_requests'] += 1
        self.stats['by_reason'][threat_type] = \
            self.stats['by_reason'].get(threat_type, 0) + 1

        return {
            'decision': 'block',
            'reason': reason,
            'checks_performed': checks_performed,
            'threat_type': threat_type,
            'confidence': confidence
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get gate statistics."""
        return {
            'total_requests': self.stats['total_requests'],
            'blocked_requests': self.stats['blocked_requests'],
            'allowed_requests': self.stats['allowed_requests'],
            'by_reason': self.stats['by_reason'],
            'start_time': self.stats['start_time']
        }


def process_pretool_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for PreToolUse hook.

    Args:
        input_data: JSON from stdin with tool_name, tool_input, session_id

    Returns:
        {'decision': 'allow'|'block', 'reason': str, ...}
    """
    gate = WebFetchSecurityGate()

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Handle WebFetch and WebSearch
    if tool_name in ['WebFetch', 'WebSearch']:
        return gate.validate_request(tool_input)

    # Unknown tool - allow by default
    return {
        'decision': 'allow',
        'reason': f'Tool {tool_name} not subject to WebFetch security',
        'checks_performed': [],
        'threat_type': None,
        'confidence': 1.0
    }


def main():
    """Hook entry point - reads JSON from stdin, outputs decision."""
    try:
        # Read input from stdin
        input_text = sys.stdin.read()
        if not input_text.strip():
            # No input - allow (shouldn't happen in normal operation)
            result = {
                'decision': 'allow',
                'reason': 'No input provided',
                'checks_performed': []
            }
        else:
            input_data = json.loads(input_text)
            result = process_pretool_input(input_data)

        # Output result as JSON
        print(json.dumps(result))
        sys.exit(0 if result['decision'] == 'allow' else 1)

    except json.JSONDecodeError as e:
        error_result = {
            'decision': 'block',
            'reason': f'Invalid JSON input: {e}',
            'checks_performed': []
        }
        print(json.dumps(error_result))
        sys.exit(1)

    except Exception as e:
        error_result = {
            'decision': 'block',
            'reason': f'Security gate error: {e}',
            'checks_performed': []
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == '__main__':
    main()
