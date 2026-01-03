#!/usr/bin/env python3
"""
TDD Tests for Batch 2 Bare Except Clause Fixes

Tests that verify Python files don't contain bare `except:` clauses,
which is a MUST-FIX code quality issue.

Run: python3 -m pytest claude/tools/tests/test_batch2_bare_except_fixes.py -v
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
                context = f"bare except at line {node.lineno}"
                bare_excepts.append((node.lineno, context))

    return bare_excepts


class TestDocxTemplateCleaner:
    """Tests for docx_template_cleaner.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "document" / "docx_template_cleaner.py"

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


class TestLaunchagentHealthMonitor:
    """Tests for launchagent_health_monitor.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "sre" / "launchagent_health_monitor.py"

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


class TestServicedeskGpuRagIndexer:
    """Tests for servicedesk_gpu_rag_indexer.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "sre" / "servicedesk_gpu_rag_indexer.py"

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


class TestAnalysisPatternLibrary:
    """Tests for analysis_pattern_library.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "analysis_pattern_library.py"

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


class TestMorningEmailIntelligence:
    """Tests for morning_email_intelligence_local.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "morning_email_intelligence_local.py"

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


class TestMaiaComprehensiveTestSuite:
    """Tests for maia_comprehensive_test_suite.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "sre" / "maia_comprehensive_test_suite.py"

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


class TestXlsxPreValidator:
    """Tests for xlsx_pre_validator.py bare except fixes"""

    FILEPATH = Path(__file__).parent.parent / "sre" / "xlsx_pre_validator.py"

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
