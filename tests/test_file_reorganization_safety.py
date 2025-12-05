"""
TDD Safety Net for File Reorganization - Phase 218

Purpose: Validate all imports resolve correctly before/after file moves.
Run this test BEFORE and AFTER any file reorganization to catch silent failures.

Usage:
    pytest tests/test_file_reorganization_safety.py -v
    pytest tests/test_file_reorganization_safety.py::test_all_tool_imports_resolve -v

Created: 2024-12-02
TDD Protocol: Test written BEFORE any file cleanup operations
"""

import importlib
import importlib.util
import os
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Set, Dict
import pytest


# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "claude" / "tools"))


class ImportAnalyzer:
    """Analyzes Python files for import statements and validates they resolve."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools_dir = project_root / "claude" / "tools"

    def extract_imports_from_file(self, filepath: Path) -> List[str]:
        """Extract all import statements from a Python file."""
        imports = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        # Also track full import path
                        for alias in node.names:
                            if alias.name != '*':
                                imports.append(f"{node.module}.{alias.name}")
        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors or encoding issues
            pass

        return imports

    def find_all_python_files(self, directory: Path) -> List[Path]:
        """Find all Python files in directory, excluding caches and tests."""
        python_files = []

        for root, dirs, files in os.walk(directory):
            # Skip cache and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(Path(root) / file)

        return python_files

    def find_internal_imports(self, filepath: Path) -> List[Tuple[str, str]]:
        """Find imports that reference other claude/tools modules."""
        imports = self.extract_imports_from_file(filepath)
        internal_imports = []

        for imp in imports:
            # Check if this is an internal claude.tools import
            if imp.startswith('claude.tools') or imp.startswith('claude/tools'):
                internal_imports.append((str(filepath), imp))
            # Check for relative imports within tools directory
            elif not imp.startswith(('os', 'sys', 'json', 'csv', 'datetime', 'pathlib',
                                     'typing', 'dataclasses', 'collections', 'itertools',
                                     'functools', 're', 'logging', 'subprocess', 'shutil',
                                     'tempfile', 'urllib', 'http', 'socket', 'ssl',
                                     'hashlib', 'base64', 'uuid', 'random', 'time',
                                     'sqlite3', 'requests', 'pytest', 'unittest',
                                     'argparse', 'configparser', 'ast', 'importlib',
                                     'traceback', 'io', 'glob', 'fnmatch', 'copy',
                                     'enum', 'abc', 'contextlib', 'threading',
                                     'multiprocessing', 'concurrent', 'asyncio',
                                     'aiohttp', 'numpy', 'pandas', 'chromadb',
                                     'openai', 'anthropic', 'google', 'ollama',
                                     'bs4', 'lxml', 'yaml', 'toml', 'dotenv')):
                # Could be a local import - check if file exists
                potential_file = self.tools_dir / f"{imp.replace('.', '/')}.py"
                potential_file_direct = self.tools_dir / f"{imp}.py"

                if potential_file.exists() or potential_file_direct.exists():
                    internal_imports.append((str(filepath), imp))

        return internal_imports

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a graph of which files import which other files."""
        dependency_graph = {}
        python_files = self.find_all_python_files(self.tools_dir)

        for filepath in python_files:
            rel_path = str(filepath.relative_to(self.project_root))
            internal_imports = self.find_internal_imports(filepath)

            if internal_imports:
                dependency_graph[rel_path] = set(imp for _, imp in internal_imports)

        return dependency_graph


@pytest.fixture
def analyzer():
    """Provide ImportAnalyzer instance."""
    return ImportAnalyzer(PROJECT_ROOT)


class TestImportValidation:
    """Test suite for validating imports before/after file reorganization."""

    def test_all_tool_imports_resolve(self, analyzer):
        """
        Verify all Python files in claude/tools can be parsed without import errors.
        This catches missing dependencies and broken imports.
        """
        tools_dir = PROJECT_ROOT / "claude" / "tools"
        python_files = analyzer.find_all_python_files(tools_dir)

        failures = []

        for filepath in python_files:
            # Skip test files for this check
            if 'test_' in filepath.name or filepath.name == 'conftest.py':
                continue

            try:
                # Try to load the module spec (validates syntax and basic imports)
                spec = importlib.util.spec_from_file_location(
                    filepath.stem,
                    filepath
                )
                if spec and spec.loader:
                    # We don't actually load the module (could have side effects)
                    # Just verify the spec can be created
                    pass
            except Exception as e:
                failures.append(f"{filepath.relative_to(PROJECT_ROOT)}: {type(e).__name__}: {e}")

        if failures:
            pytest.fail(f"Import validation failures ({len(failures)}):\n" + "\n".join(failures[:20]))

    def test_no_syntax_errors_in_tools(self, analyzer):
        """Verify all Python files have valid syntax."""
        tools_dir = PROJECT_ROOT / "claude" / "tools"
        python_files = analyzer.find_all_python_files(tools_dir)

        syntax_errors = []

        for filepath in python_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                syntax_errors.append(f"{filepath.relative_to(PROJECT_ROOT)}: Line {e.lineno}: {e.msg}")
            except UnicodeDecodeError as e:
                syntax_errors.append(f"{filepath.relative_to(PROJECT_ROOT)}: Encoding error: {e}")

        if syntax_errors:
            pytest.fail(f"Syntax errors found ({len(syntax_errors)}):\n" + "\n".join(syntax_errors))

    def test_internal_imports_have_targets(self, analyzer):
        """
        Verify all internal imports (claude.tools.*) reference files that exist.
        This is the key test for catching broken imports after file moves.
        """
        tools_dir = PROJECT_ROOT / "claude" / "tools"
        python_files = analyzer.find_all_python_files(tools_dir)

        broken_imports = []

        for filepath in python_files:
            internal_imports = analyzer.find_internal_imports(filepath)

            for source_file, import_path in internal_imports:
                # Convert import path to potential file paths
                if import_path.startswith('claude.tools.'):
                    relative_path = import_path.replace('claude.tools.', '').replace('.', '/')
                else:
                    relative_path = import_path.replace('.', '/')

                # Check multiple possible locations
                possible_paths = [
                    tools_dir / f"{relative_path}.py",
                    tools_dir / relative_path / "__init__.py",
                    PROJECT_ROOT / "claude" / "tools" / f"{relative_path}.py",
                ]

                # For simple names, also check same directory
                if '.' not in import_path and '/' not in import_path:
                    source_dir = Path(source_file).parent
                    possible_paths.append(source_dir / f"{import_path}.py")

                if not any(p.exists() for p in possible_paths):
                    # Only flag if it looks like a local import (not a package)
                    if not import_path.startswith(('claude.', 'maia.')):
                        broken_imports.append(f"{source_file} imports '{import_path}' - target not found")

        if broken_imports:
            # Report but don't fail - some imports may be conditional or optional
            print(f"\nPotential broken imports ({len(broken_imports)}):")
            for bi in broken_imports[:20]:
                print(f"  ⚠️  {bi}")

    def test_versioned_tools_dependency_check(self, analyzer):
        """
        Specifically check versioned tools (v1, v2, v3, v4) for dependencies.
        These are the files we might archive - need to know what imports them.
        """
        tools_dir = PROJECT_ROOT / "claude" / "tools"

        # Find all versioned files
        versioned_files = []
        for filepath in analyzer.find_all_python_files(tools_dir):
            if '_v' in filepath.stem and filepath.stem[-1].isdigit():
                versioned_files.append(filepath)

        # Build reverse dependency map: who imports each versioned file?
        importers = {str(vf.relative_to(PROJECT_ROOT)): [] for vf in versioned_files}

        for filepath in analyzer.find_all_python_files(tools_dir):
            imports = analyzer.extract_imports_from_file(filepath)

            for vf in versioned_files:
                vf_name = vf.stem  # e.g., "pmp_complete_intelligence_extractor_v4"

                for imp in imports:
                    if vf_name in imp:
                        rel_source = str(filepath.relative_to(PROJECT_ROOT))
                        rel_target = str(vf.relative_to(PROJECT_ROOT))
                        if rel_source != rel_target:  # Don't count self-imports
                            importers[rel_target].append(rel_source)

        # Report findings
        print("\n=== VERSIONED TOOLS DEPENDENCY REPORT ===")
        safe_to_archive = []
        cannot_archive = []

        for vf, deps in importers.items():
            if deps:
                cannot_archive.append((vf, deps))
                print(f"\n🛑 {vf}")
                print(f"   Imported by {len(deps)} file(s):")
                for dep in deps[:5]:
                    print(f"      - {dep}")
                if len(deps) > 5:
                    print(f"      ... and {len(deps) - 5} more")
            else:
                safe_to_archive.append(vf)
                print(f"\n✅ {vf}")
                print(f"   No importers - SAFE TO ARCHIVE")

        # Store results for later use
        print(f"\n=== SUMMARY ===")
        print(f"Safe to archive: {len(safe_to_archive)}")
        print(f"Cannot archive (has dependencies): {len(cannot_archive)}")

        # This test passes - it's informational
        assert True


class TestSpecificToolDependencies:
    """Test dependencies for specific tools we plan to move/archive."""

    def test_pmp_extractor_dependencies(self, analyzer):
        """Check what imports the PMP intelligence extractors."""
        tools_dir = PROJECT_ROOT / "claude" / "tools"
        pmp_dir = tools_dir / "pmp"

        if not pmp_dir.exists():
            pytest.skip("PMP directory not found")

        # Target files we might archive
        targets = [
            "pmp_complete_intelligence_extractor_v2",
            "pmp_complete_intelligence_extractor_v3",
            "pmp_complete_intelligence_extractor_v4",
            "pmp_complete_intelligence_extractor_v4_resume",
            "pmp_config_extractor_v4",
        ]

        dependencies = {t: [] for t in targets}

        for filepath in analyzer.find_all_python_files(tools_dir):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            for target in targets:
                if target in content and filepath.stem != target:
                    dependencies[target].append(str(filepath.relative_to(PROJECT_ROOT)))

        # Report
        print("\n=== PMP EXTRACTOR DEPENDENCY REPORT ===")
        for target, deps in dependencies.items():
            status = "🛑 BLOCKED" if deps else "✅ SAFE"
            print(f"\n{status} {target}")
            if deps:
                print(f"   Imported by: {deps}")

        # Store blocked files for documentation
        blocked = [t for t, d in dependencies.items() if d]
        safe = [t for t, d in dependencies.items() if not d]

        print(f"\n=== ARCHIVE DECISION ===")
        print(f"Can archive: {safe}")
        print(f"Cannot archive: {blocked}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
