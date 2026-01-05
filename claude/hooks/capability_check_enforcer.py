#!/usr/bin/env python3
"""
Capability Check Enforcer (Phase 127 - Cached Version, Phase 235 - DB-First)

Automated Phase 0 capability check to prevent building duplicate tools/agents.
Integrated with user-prompt-submit hook to run before every request.

Performance: <10ms per check (uses DB queries instead of 68KB markdown file)

Usage:
    python3 capability_check_enforcer.py "user message here"

Exit codes:
    0 = No duplicate detected (or low confidence)
    1 = Existing capability found with high confidence (should warn user)
    2 = Error running check

Author: Maia (Phase 119 - Capability Amnesia Fix, Phase 127 - Cached Optimization)
Created: 2025-10-15
Updated: 2025-10-17 (Phase 127 - Cache optimization)
Updated: 2026-01-05 (Phase 235 - DB-first to fix context bloat)
"""

import sys
import re
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, Optional, List


class CapabilityEnforcer:
    """Enforces Phase 0 capability check for build requests."""

    BUILD_KEYWORDS = [
        'build', 'create', 'make', 'develop', 'implement', 'write',
        'generate', 'add', 'construct', 'design', 'code',
        'new tool', 'new agent', 'new script', 'new capability'
    ]

    HIGH_CONFIDENCE_THRESHOLD = 70  # 70%+ confidence = warn user

    def __init__(self, maia_root: Optional[Path] = None):
        """Initialize enforcer with Maia root directory."""
        if maia_root is None:
            # Find maia root by looking for CLAUDE.md
            current = Path(__file__).parent
            while current != current.parent:
                if (current / 'CLAUDE.md').exists():
                    maia_root = current
                    break
                current = current.parent

        self.maia_root = maia_root or Path.cwd()
        # Use cached version for 99.99% performance improvement (0.1ms vs 920ms)
        self.capability_checker = self.maia_root / 'claude' / 'tools' / 'capability_checker_cached.py'
        # Phase 235: Use DB instead of 68KB markdown file
        self.capabilities_db = self.maia_root / 'claude' / 'data' / 'databases' / 'system' / 'capabilities.db'
        # Deprecated: Only used as fallback if DB unavailable
        self.capability_index = self.maia_root / 'claude' / 'context' / 'core' / 'capability_index.md'

    def detect_build_request(self, user_input: str) -> bool:
        """
        Detect if user input is requesting to build something new.

        Returns True if input contains build-related keywords.
        """
        input_lower = user_input.lower()

        for keyword in self.BUILD_KEYWORDS:
            if keyword in input_lower:
                return True

        return False

    def search_capability_db(self, user_input: str) -> Optional[Dict]:
        """
        Search capabilities.db for potential matches (Phase 235 - DB-First).

        Uses SQLite database instead of reading 68KB markdown file.
        Reduces context overhead from ~17K tokens to ~200 tokens.

        Args:
            user_input: User's message to search for keywords

        Returns:
            Dict with 'name', 'path', 'keyword_matches' if found, None otherwise
        """
        if not self.capabilities_db.exists():
            return None

        try:
            # Extract keywords from user input (4+ char words, excluding common build terms)
            words = re.findall(r'\b\w{4,}\b', user_input.lower())
            words = [w for w in words if w not in [
                'build', 'create', 'make', 'tool', 'agent', 'write',
                'implement', 'develop', 'generate', 'construct'
            ]]

            if not words:
                return None

            conn = sqlite3.connect(self.capabilities_db)
            conn.row_factory = sqlite3.Row

            # Search for each keyword (limit to first 3 for performance)
            for word in words[:3]:
                result = conn.execute(
                    """SELECT name, path, keywords FROM capabilities
                       WHERE LOWER(name) LIKE ? OR LOWER(keywords) LIKE ?
                       LIMIT 1""",
                    (f'%{word}%', f'%{word}%')
                ).fetchone()

                if result:
                    conn.close()
                    return {
                        'name': result['name'],
                        'path': result['path'],
                        'keyword_matches': 1
                    }

            conn.close()
            return None

        except Exception:
            return None

    def search_capability_index(self, user_input: str) -> Optional[Dict]:
        """
        DEPRECATED: Use search_capability_db() instead.

        This method reads the full 68KB capability_index.md file which causes
        context bloat (~17K tokens). Kept for backward compatibility only.

        Phase 235: Replaced by search_capability_db() for DB-first queries.
        """
        if not self.capability_index.exists():
            return None

        try:
            content = self.capability_index.read_text()

            # Extract keywords from user input
            words = re.findall(r'\b\w{4,}\b', user_input.lower())
            words = [w for w in words if w not in ['build', 'create', 'make', 'tool', 'agent']]

            if not words:
                return None

            # Search for matching capabilities
            matches = []
            for line in content.split('\n'):
                line_lower = line.lower()
                match_count = sum(1 for word in words if word in line_lower)

                if match_count >= 2:  # At least 2 keyword matches
                    # Extract capability name
                    match = re.match(r'^-\s+([^\s]+)\s*-', line)
                    if match:
                        matches.append({
                            'name': match.group(1),
                            'line': line.strip(),
                            'keyword_matches': match_count
                        })

            if matches:
                # Return best match (most keyword matches)
                best = max(matches, key=lambda m: m['keyword_matches'])
                return best

        except Exception:
            return None

        return None

    def run_capability_checker(self, user_input: str) -> Dict:
        """
        Run full capability_checker.py for deep search.

        Returns dict with:
            - found: bool
            - capability: str or None
            - confidence: float
            - location: str or None
        """
        if not self.capability_checker.exists():
            return {'found': False, 'error': 'capability_checker.py not found'}

        try:
            result = subprocess.run(
                ['python3', str(self.capability_checker), user_input],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse output
            stdout = result.stdout

            if 'RECOMMENDATION: USE EXISTING' in stdout:
                # Extract details
                confidence = self._extract_confidence(stdout)
                capability = self._extract_capability(stdout)
                location = self._extract_location(stdout)

                return {
                    'found': True,
                    'capability': capability,
                    'confidence': confidence,
                    'location': location
                }

            return {'found': False}

        except subprocess.TimeoutExpired:
            return {'found': False, 'error': 'capability_checker timeout'}
        except Exception as e:
            return {'found': False, 'error': str(e)}

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence percentage from capability_checker output."""
        match = re.search(r'Confidence:\s*(\d+)%', text)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_capability(self, text: str) -> Optional[str]:
        """Extract capability name from capability_checker output."""
        match = re.search(r'FOUND:\s+([^\s]+)', text)
        if match:
            return match.group(1)
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract file location from capability_checker output."""
        match = re.search(r'Location:\s+(.+)$', text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def enforce(self, user_input: str) -> Dict:
        """
        Main enforcement logic.

        Returns dict with:
            - should_warn: bool (True = found existing with high confidence)
            - existing_capability: str or None
            - confidence: float
            - message: str (formatted warning for user)
        """
        # Step 1: Detect if this is a build request
        if not self.detect_build_request(user_input):
            return {
                'should_warn': False,
                'message': '✅ Not a build request - no capability check needed'
            }

        # Step 2: Quick search in capabilities database (Phase 235 - DB-First)
        db_match = self.search_capability_db(user_input)
        if db_match:
            # Found potential match in DB
            return {
                'should_warn': True,
                'existing_capability': db_match['name'],
                'confidence': 75.0,  # Heuristic confidence for DB matches
                'location': db_match.get('path', 'capabilities.db'),
                'message': self._format_warning(
                    db_match['name'],
                    75.0,
                    db_match.get('path', 'capabilities.db'),
                    'DB capability search'
                )
            }

        # Step 3: Run full capability checker if available
        checker_result = self.run_capability_checker(user_input)

        if checker_result.get('found') and checker_result.get('confidence', 0) >= self.HIGH_CONFIDENCE_THRESHOLD:
            return {
                'should_warn': True,
                'existing_capability': checker_result['capability'],
                'confidence': checker_result['confidence'],
                'location': checker_result.get('location'),
                'message': self._format_warning(
                    checker_result['capability'],
                    checker_result['confidence'],
                    checker_result.get('location'),
                    'Deep capability search'
                )
            }

        # No duplicate found or low confidence
        return {
            'should_warn': False,
            'message': '✅ No duplicate capability detected (or low confidence match)'
        }

    def _format_warning(self, capability: str, confidence: float, location: str, method: str) -> str:
        """Format warning message for user."""
        return f"""
🔍 AUTOMATED CAPABILITY CHECK (Phase 0)

⚠️  BUILD REQUEST DETECTED in your message

Searching existing capabilities... ({method})
  ✅ FOUND: {capability}
  📊 Confidence: {confidence:.0f}%
  📍 Location: {location}

🎯 RECOMMENDATION: USE EXISTING CAPABILITY

Options:
  1. Use existing capability (recommended)
  2. Enhance existing capability if insufficient
  3. Build new capability anyway (justify why)

⏸️  Please confirm your choice before proceeding.
"""


def main():
    """Main entry point for hook integration."""
    if len(sys.argv) < 2:
        print("Usage: capability_check_enforcer.py 'user message'", file=sys.stderr)
        sys.exit(2)

    user_input = ' '.join(sys.argv[1:])

    try:
        enforcer = CapabilityEnforcer()
        result = enforcer.enforce(user_input)

        # Print message (always)
        print(result['message'])

        # Exit code determines action
        if result.get('should_warn'):
            sys.exit(1)  # Warning - found existing capability
        else:
            sys.exit(0)  # OK - no duplicate detected

    except Exception as e:
        print(f"❌ Error running capability check: {e}", file=sys.stderr)
        print("   Manual Phase 0 check recommended", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
