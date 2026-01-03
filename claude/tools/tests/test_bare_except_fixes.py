#!/usr/bin/env python3
"""
TDD Tests for Bare Except Clause Fixes

Tests that verify Python files don't contain bare `except:` clauses,
which is a MUST-FIX code quality issue.

Run: python3 -m pytest claude/tools/tests/test_bare_except_fixes.py -v
"""

import ast
import pytest
from pathlib import Path


def find_bare_excepts(filepath: Path) -> list[tuple[int, str]]:
    """
    Parse Python file and find all bare except clauses.
    Returns list of (line_number, context) tuples.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [(-1, "SyntaxError - cannot parse")]

    bare_excepts = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:  # Bare except: with no exception type
                # Get context - find parent function if possible
                context = f"bare except at line {node.lineno}"
                bare_excepts.append((node.lineno, context))

    return bare_excepts


class TestDNSCompleteAudit:
    """Tests for dns_complete_audit.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "dns_complete_audit.py"

    def test_file_exists(self):
        """Verify test target exists"""
        assert self.FILEPATH.exists(), f"File not found: {self.FILEPATH}"

    def test_no_bare_excepts(self):
        """MUST-FIX: No bare except clauses allowed"""
        bare_excepts = find_bare_excepts(self.FILEPATH)

        assert len(bare_excepts) == 0, (
            f"Found {len(bare_excepts)} bare except clause(s) in {self.FILEPATH.name}:\n"
            + "\n".join(f"  Line {line}: {ctx}" for line, ctx in bare_excepts)
        )

    def test_uses_specific_dns_exceptions(self):
        """Verify DNS-specific exceptions are used"""
        with open(self.FILEPATH, 'r') as f:
            content = f.read()

        # Should contain specific DNS exception handling
        assert "dns.resolver.NoAnswer" in content or "dns.exception" in content, (
            "Expected specific DNS exception handling"
        )


class TestAutomatedHealthMonitor:
    """Tests for automated_health_monitor.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "sre" / "automated_health_monitor.py"

    def test_file_exists(self):
        """Verify test target exists"""
        assert self.FILEPATH.exists(), f"File not found: {self.FILEPATH}"

    def test_no_bare_excepts(self):
        """MUST-FIX: No bare except clauses allowed"""
        bare_excepts = find_bare_excepts(self.FILEPATH)

        assert len(bare_excepts) == 0, (
            f"Found {len(bare_excepts)} bare except clause(s) in {self.FILEPATH.name}:\n"
            + "\n".join(f"  Line {line}: {ctx}" for line, ctx in bare_excepts)
        )

    def test_uses_specific_parsing_exceptions(self):
        """Verify parsing uses specific exceptions (ValueError, IndexError)"""
        with open(self.FILEPATH, 'r') as f:
            content = f.read()

        # After fix, should contain specific exception types for parsing
        # This test validates the fix approach
        has_value_error = "ValueError" in content
        has_index_error = "IndexError" in content

        assert has_value_error or has_index_error, (
            "Expected specific parsing exception handling (ValueError/IndexError)"
        )


class TestDNSAdvancedAudit:
    """Tests for dns_advanced_audit.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "dns_advanced_audit.py"

    def test_file_exists(self):
        """Verify test target exists"""
        assert self.FILEPATH.exists(), f"File not found: {self.FILEPATH}"

    def test_no_bare_excepts(self):
        """MUST-FIX: No bare except clauses allowed"""
        bare_excepts = find_bare_excepts(self.FILEPATH)

        assert len(bare_excepts) == 0, (
            f"Found {len(bare_excepts)} bare except clause(s) in {self.FILEPATH.name}:\n"
            + "\n".join(f"  Line {line}: {ctx}" for line, ctx in bare_excepts)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
