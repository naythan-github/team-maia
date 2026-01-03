#!/usr/bin/env python3
"""
Python Function Scanner - AST-Based Accurate Analysis
Phase 230 Lesson: Always use AST for function length measurement.

Scans Python files and reports function lengths using Python's AST module,
which provides accurate end_lineno for each function definition.

Usage:
    # Scan single file
    python3 python_function_scanner.py claude/tools/sre/some_file.py

    # Scan directory for functions >100 lines
    python3 python_function_scanner.py claude/tools/ --min-lines 100

    # Output JSON for processing
    python3 python_function_scanner.py claude/tools/ --json --min-lines 100
"""

import ast
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class FunctionInfo:
    """Information about a Python function."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    line_count: int
    function_type: str  # 'function', 'method', 'async_function', 'async_method'
    class_name: Optional[str]  # Parent class if method
    is_dunder: bool  # __init__, __str__, etc.
    has_docstring: bool


class PythonFunctionScanner:
    """Scans Python files for function definitions using AST."""

    def __init__(self, min_lines: int = 1):
        self.min_lines = min_lines
        self.functions: List[FunctionInfo] = []

    def scan_file(self, file_path: Path) -> List[FunctionInfo]:
        """Scan a single Python file for functions."""
        try:
            source = file_path.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            print(f"  ⚠️  Syntax error in {file_path}: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"  ⚠️  Error parsing {file_path}: {e}", file=sys.stderr)
            return []

        functions = []
        self._extract_functions(tree, file_path, functions, class_name=None)
        return functions

    def _extract_functions(
        self,
        node: ast.AST,
        file_path: Path,
        functions: List[FunctionInfo],
        class_name: Optional[str]
    ) -> None:
        """Recursively extract function definitions from AST."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                # Recurse into class to find methods
                self._extract_functions(child, file_path, functions, class_name=child.name)

            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate accurate line count using end_lineno
                if hasattr(child, 'end_lineno') and child.end_lineno:
                    line_count = child.end_lineno - child.lineno + 1
                else:
                    # Fallback for older Python (shouldn't happen with 3.8+)
                    line_count = self._estimate_function_length(child)

                # Skip if below minimum
                if line_count < self.min_lines:
                    continue

                # Determine function type
                is_async = isinstance(child, ast.AsyncFunctionDef)
                if class_name:
                    func_type = 'async_method' if is_async else 'method'
                else:
                    func_type = 'async_function' if is_async else 'function'

                # Check for docstring
                has_docstring = (
                    len(child.body) > 0 and
                    isinstance(child.body[0], ast.Expr) and
                    isinstance(child.body[0].value, ast.Constant) and
                    isinstance(child.body[0].value.value, str)
                )

                func_info = FunctionInfo(
                    name=child.name,
                    file_path=str(file_path),
                    start_line=child.lineno,
                    end_line=child.end_lineno or child.lineno,
                    line_count=line_count,
                    function_type=func_type,
                    class_name=class_name,
                    is_dunder=child.name.startswith('__') and child.name.endswith('__'),
                    has_docstring=has_docstring
                )
                functions.append(func_info)

                # Also check nested functions
                self._extract_functions(child, file_path, functions, class_name=class_name)

    def _estimate_function_length(self, node: ast.FunctionDef) -> int:
        """Fallback estimation if end_lineno not available."""
        # This is a rough estimate - shouldn't be needed with Python 3.8+
        max_line = node.lineno
        for child in ast.walk(node):
            if hasattr(child, 'lineno') and child.lineno:
                max_line = max(max_line, child.lineno)
        return max_line - node.lineno + 1

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[FunctionInfo]:
        """Scan all Python files in a directory."""
        pattern = '**/*.py' if recursive else '*.py'
        all_functions = []

        for py_file in directory.glob(pattern):
            # Skip __pycache__ and hidden directories
            if '__pycache__' in str(py_file) or '/.' in str(py_file):
                continue

            functions = self.scan_file(py_file)
            all_functions.extend(functions)

        # Sort by line count descending
        all_functions.sort(key=lambda f: f.line_count, reverse=True)
        return all_functions


def format_output(functions: List[FunctionInfo], output_format: str = 'table') -> str:
    """Format function list for output."""
    if not functions:
        return "No functions found matching criteria."

    if output_format == 'json':
        return json.dumps([asdict(f) for f in functions], indent=2)

    # Table format
    lines = []
    lines.append(f"\n{'='*100}")
    lines.append(f"Python Function Length Analysis (AST-Based)")
    lines.append(f"{'='*100}")
    lines.append(f"Found {len(functions)} functions\n")

    # Group by severity
    critical = [f for f in functions if f.line_count >= 200]
    high = [f for f in functions if 150 <= f.line_count < 200]
    medium = [f for f in functions if 100 <= f.line_count < 150]
    low = [f for f in functions if f.line_count < 100]

    if critical:
        lines.append(f"🔴 CRITICAL (≥200 lines): {len(critical)} functions")
    if high:
        lines.append(f"🟠 HIGH (150-199 lines): {len(high)} functions")
    if medium:
        lines.append(f"🟡 MEDIUM (100-149 lines): {len(medium)} functions")
    if low:
        lines.append(f"🟢 LOW (<100 lines): {len(low)} functions")

    lines.append(f"\n{'='*100}")
    lines.append(f"| {'#':>3} | {'Lines':>5} | {'Type':>12} | {'Function Name':<40} | {'File:Line':<50} |")
    lines.append(f"|{'-'*5}|{'-'*7}|{'-'*14}|{'-'*42}|{'-'*52}|")

    for i, func in enumerate(functions, 1):
        # Format function name with class prefix if method
        if func.class_name:
            full_name = f"{func.class_name}.{func.name}"
        else:
            full_name = func.name

        # Truncate if too long
        full_name = full_name[:38] + '..' if len(full_name) > 40 else full_name

        # Format file path (relative, truncated)
        file_loc = f"{Path(func.file_path).name}:{func.start_line}"
        file_loc = file_loc[:48] + '..' if len(file_loc) > 50 else file_loc

        # Severity indicator
        if func.line_count >= 200:
            severity = "🔴"
        elif func.line_count >= 150:
            severity = "🟠"
        elif func.line_count >= 100:
            severity = "🟡"
        else:
            severity = "🟢"

        lines.append(
            f"| {i:>3} | {severity}{func.line_count:>4} | {func.function_type:>12} | "
            f"{full_name:<40} | {file_loc:<50} |"
        )

    lines.append(f"{'='*100}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Scan Python files for function lengths using AST analysis'
    )
    parser.add_argument('path', help='File or directory to scan')
    parser.add_argument('--min-lines', type=int, default=100,
                        help='Minimum lines to report (default: 100)')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--no-recursive', action='store_true',
                        help='Do not recurse into subdirectories')
    parser.add_argument('--include-dunders', action='store_true',
                        help='Include __init__, __str__, etc.')

    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    scanner = PythonFunctionScanner(min_lines=args.min_lines)

    if path.is_file():
        functions = scanner.scan_file(path)
    else:
        functions = scanner.scan_directory(path, recursive=not args.no_recursive)

    # Filter out dunders unless requested
    if not args.include_dunders:
        functions = [f for f in functions if not f.is_dunder]

    output_format = 'json' if args.json else 'table'
    print(format_output(functions, output_format))

    # Exit with code based on critical functions found
    critical_count = len([f for f in functions if f.line_count >= 200])
    if critical_count > 0:
        print(f"\n⚠️  {critical_count} critical functions (≥200 lines) require refactoring")


if __name__ == '__main__':
    main()
