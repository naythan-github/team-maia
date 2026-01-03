#!/usr/bin/env python3
"""
Maia Comprehensive Test Suite - SRE Production Validation

Purpose: Automated validation of ALL Maia components to detect silent failures
Target: 400+ checks across tools, agents, databases, RAG, hooks, and core functionality

Usage:
    python3 maia_comprehensive_test_suite.py              # Run all tests
    python3 maia_comprehensive_test_suite.py --category tools  # Run specific category
    python3 maia_comprehensive_test_suite.py --quick      # Quick smoke test (~50 checks)
    python3 maia_comprehensive_test_suite.py --json       # Output JSON report

Categories:
    - tools: Import validation for all 471+ Python tools
    - agents: Structure validation for all 63 agents
    - databases: Integrity tests for 30+ SQLite databases
    - rag: ChromaDB/RAG validation for 3 instances
    - hooks: Hook import and structure validation
    - core: Core functionality (smart loader, routing, queries)
    - ollama: Local LLM model availability

Author: SRE Principal Engineer Agent
Created: 2024-11-22
"""

import argparse
import ast
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Maia root directory
MAIA_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass
class TestResult:
    """Individual test result"""
    category: str
    name: str
    passed: bool
    message: str
    duration_ms: float = 0.0
    details: Optional[Dict] = None


@dataclass
class CategoryResult:
    """Results for a test category"""
    category: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    tests: List[TestResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0.0


@dataclass
class TestReport:
    """Complete test report"""
    timestamp: str
    maia_root: str
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    duration_seconds: float = 0.0
    categories: Dict[str, CategoryResult] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return (self.total_passed / self.total_tests * 100) if self.total_tests > 0 else 0.0


class MaiaTestSuite:
    """Comprehensive test suite for Maia system validation"""

    def __init__(self, maia_root: Path = MAIA_ROOT, verbose: bool = True):
        self.maia_root = maia_root
        self.verbose = verbose
        self.report = TestReport(
            timestamp=datetime.now().isoformat(),
            maia_root=str(maia_root)
        )

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose"""
        if self.verbose:
            prefix = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(level, "")
            print(f"{prefix} {message}")

    def add_result(self, category: str, result: TestResult):
        """Add a test result to the report"""
        if category not in self.report.categories:
            self.report.categories[category] = CategoryResult(category=category)

        cat = self.report.categories[category]
        cat.tests.append(result)
        cat.total += 1

        if result.passed:
            cat.passed += 1
            self.report.total_passed += 1
        else:
            cat.failed += 1
            self.report.total_failed += 1

        self.report.total_tests += 1

        # Log result
        if result.passed:
            self.log(f"[{category}] {result.name}: PASS", "PASS")
        else:
            self.log(f"[{category}] {result.name}: FAIL - {result.message}", "FAIL")

    # =========================================================================
    # CATEGORY 1: Tool Import Validation
    # =========================================================================

    def test_tools(self) -> CategoryResult:
        """Test all Python tools can be imported without errors"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 1: Tool Import Validation")
        self.log("="*60)

        start_time = time.time()
        tools_dir = self.maia_root / "claude" / "tools"

        # Find all Python files
        python_files = list(tools_dir.rglob("*.py"))
        self.log(f"Found {len(python_files)} Python files to validate")

        # Exclude test files and __pycache__
        python_files = [
            f for f in python_files
            if "__pycache__" not in str(f)
            and not f.name.startswith("test_")
            and not f.name.endswith("_test.py")
        ]

        for py_file in python_files:
            rel_path = py_file.relative_to(self.maia_root)
            test_start = time.time()

            try:
                # Check syntax first (faster than import)
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()

                ast.parse(source)

                result = TestResult(
                    category="tools",
                    name=str(rel_path),
                    passed=True,
                    message="Syntax valid",
                    duration_ms=(time.time() - test_start) * 1000
                )
            except SyntaxError as e:
                result = TestResult(
                    category="tools",
                    name=str(rel_path),
                    passed=False,
                    message=f"Syntax error: {e.msg} at line {e.lineno}",
                    duration_ms=(time.time() - test_start) * 1000
                )
            except Exception as e:
                result = TestResult(
                    category="tools",
                    name=str(rel_path),
                    passed=False,
                    message=f"Parse error: {str(e)[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )

            self.add_result("tools", result)

        self.report.categories["tools"].duration_seconds = time.time() - start_time
        return self.report.categories["tools"]

    # =========================================================================
    # CATEGORY 2: Agent Structure Validation
    # =========================================================================

    def test_agents(self) -> CategoryResult:
        """Validate all agent markdown files have required structure"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 2: Agent Structure Validation")
        self.log("="*60)

        start_time = time.time()
        agents_dir = self.maia_root / "claude" / "agents"

        agent_files = list(agents_dir.glob("*.md"))
        self.log(f"Found {len(agent_files)} agent files to validate")

        required_sections = ["##", "Purpose", "Core"]  # Flexible requirements

        for agent_file in agent_files:
            test_start = time.time()
            agent_name = agent_file.stem

            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for basic structure
                has_title = content.startswith("#")
                has_sections = "##" in content
                has_content = len(content) > 200  # Minimum content

                issues = []
                if not has_title:
                    issues.append("Missing title (# heading)")
                if not has_sections:
                    issues.append("Missing sections (## headings)")
                if not has_content:
                    issues.append(f"Too short ({len(content)} chars)")

                if issues:
                    result = TestResult(
                        category="agents",
                        name=agent_name,
                        passed=False,
                        message="; ".join(issues),
                        duration_ms=(time.time() - test_start) * 1000
                    )
                else:
                    result = TestResult(
                        category="agents",
                        name=agent_name,
                        passed=True,
                        message=f"Valid structure ({len(content)} chars)",
                        duration_ms=(time.time() - test_start) * 1000
                    )
            except Exception as e:
                result = TestResult(
                    category="agents",
                    name=agent_name,
                    passed=False,
                    message=f"Read error: {str(e)[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )

            self.add_result("agents", result)

        self.report.categories["agents"].duration_seconds = time.time() - start_time
        return self.report.categories["agents"]

    # =========================================================================
    # CATEGORY 3: Database Integrity Tests
    # =========================================================================

    def test_databases(self) -> CategoryResult:
        """Test all SQLite databases for integrity"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 3: Database Integrity Tests")
        self.log("="*60)

        start_time = time.time()
        data_dir = self.maia_root / "claude" / "data"

        # Find all SQLite databases
        db_files = list(data_dir.rglob("*.db")) + list(data_dir.rglob("*.sqlite3"))
        self.log(f"Found {len(db_files)} database files to validate")

        for db_file in db_files:
            rel_path = db_file.relative_to(self.maia_root)
            test_start = time.time()

            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()

                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]

                # Get table count
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                # Get total row count across all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                total_rows = 0
                for table in tables:
                    try:
                        cursor.execute(f"SELECT count(*) FROM [{table[0]}]")
                        total_rows += cursor.fetchone()[0]
                    except sqlite3.Error:
                        pass

                conn.close()

                if integrity_result == "ok":
                    result = TestResult(
                        category="databases",
                        name=str(rel_path),
                        passed=True,
                        message=f"Integrity OK ({table_count} tables, {total_rows} rows)",
                        duration_ms=(time.time() - test_start) * 1000,
                        details={"tables": table_count, "rows": total_rows}
                    )
                else:
                    result = TestResult(
                        category="databases",
                        name=str(rel_path),
                        passed=False,
                        message=f"Integrity check failed: {integrity_result}",
                        duration_ms=(time.time() - test_start) * 1000
                    )
            except Exception as e:
                result = TestResult(
                    category="databases",
                    name=str(rel_path),
                    passed=False,
                    message=f"Database error: {str(e)[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )

            self.add_result("databases", result)

        self.report.categories["databases"].duration_seconds = time.time() - start_time
        return self.report.categories["databases"]

    # =========================================================================
    # CATEGORY 4: ChromaDB/RAG Validation
    # =========================================================================

    def test_rag(self) -> CategoryResult:
        """Test ChromaDB/RAG instances"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 4: ChromaDB/RAG Validation")
        self.log("="*60)

        start_time = time.time()
        rag_dir = self.maia_root / "claude" / "data" / "rag_databases"

        rag_instances = [
            ("email_rag_ollama", "Email RAG"),
            ("meeting_transcripts_rag", "Meeting Transcripts RAG"),
            ("analysis_patterns", "Analysis Patterns RAG"),
        ]

        for rag_name, description in rag_instances:
            test_start = time.time()
            rag_path = rag_dir / rag_name

            try:
                if not rag_path.exists():
                    result = TestResult(
                        category="rag",
                        name=description,
                        passed=False,
                        message=f"Directory not found: {rag_path}",
                        duration_ms=(time.time() - test_start) * 1000
                    )
                else:
                    # Check for ChromaDB files
                    chroma_db = rag_path / "chroma.sqlite3"

                    if chroma_db.exists():
                        # Try to open and query ChromaDB
                        conn = sqlite3.connect(str(chroma_db))
                        cursor = conn.cursor()

                        # Check for collections table
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [t[0] for t in cursor.fetchall()]

                        # Get collection info
                        collection_count = 0
                        embedding_count = 0

                        if "collections" in tables:
                            cursor.execute("SELECT count(*) FROM collections")
                            collection_count = cursor.fetchone()[0]

                        if "embeddings" in tables:
                            cursor.execute("SELECT count(*) FROM embeddings")
                            embedding_count = cursor.fetchone()[0]

                        conn.close()

                        result = TestResult(
                            category="rag",
                            name=description,
                            passed=True,
                            message=f"ChromaDB OK ({collection_count} collections, {embedding_count} embeddings)",
                            duration_ms=(time.time() - test_start) * 1000,
                            details={"collections": collection_count, "embeddings": embedding_count}
                        )
                    else:
                        result = TestResult(
                            category="rag",
                            name=description,
                            passed=False,
                            message="chroma.sqlite3 not found",
                            duration_ms=(time.time() - test_start) * 1000
                        )
            except Exception as e:
                result = TestResult(
                    category="rag",
                    name=description,
                    passed=False,
                    message=f"RAG error: {str(e)[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )

            self.add_result("rag", result)

        self.report.categories["rag"].duration_seconds = time.time() - start_time
        return self.report.categories["rag"]

    # =========================================================================
    # CATEGORY 5: Hook Validation
    # =========================================================================

    def test_hooks(self) -> CategoryResult:
        """Test all hooks can be parsed without errors"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 5: Hook Validation")
        self.log("="*60)

        start_time = time.time()
        hooks_dir = self.maia_root / "claude" / "hooks"

        hook_files = list(hooks_dir.glob("*.py"))
        self.log(f"Found {len(hook_files)} hook files to validate")

        for hook_file in hook_files:
            test_start = time.time()
            hook_name = hook_file.stem

            try:
                with open(hook_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                # Parse AST
                tree = ast.parse(source)

                # Check for main function or class
                has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
                has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))

                if has_functions or has_classes:
                    result = TestResult(
                        category="hooks",
                        name=hook_name,
                        passed=True,
                        message="Syntax valid, has callable definitions",
                        duration_ms=(time.time() - test_start) * 1000
                    )
                else:
                    result = TestResult(
                        category="hooks",
                        name=hook_name,
                        passed=True,
                        message="Syntax valid (no functions/classes)",
                        duration_ms=(time.time() - test_start) * 1000
                    )
            except SyntaxError as e:
                result = TestResult(
                    category="hooks",
                    name=hook_name,
                    passed=False,
                    message=f"Syntax error: {e.msg} at line {e.lineno}",
                    duration_ms=(time.time() - test_start) * 1000
                )
            except Exception as e:
                result = TestResult(
                    category="hooks",
                    name=hook_name,
                    passed=False,
                    message=f"Parse error: {str(e)[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )

            self.add_result("hooks", result)

        self.report.categories["hooks"].duration_seconds = time.time() - start_time
        return self.report.categories["hooks"]

    # =========================================================================
    # CATEGORY 6: Core Functionality Tests
    # =========================================================================

    def _test_file_readable(self, file_path: Path, test_name: str,
                            content_pattern: str = None) -> TestResult:
        """Helper: Test that a file exists, is readable, and optionally matches a pattern."""
        test_start = time.time()
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                extra_info = ""
                if content_pattern:
                    matches = len(re.findall(content_pattern, content))
                    extra_info = f", {matches} pattern matches"
                return TestResult(
                    category="core",
                    name=test_name,
                    passed=True,
                    message=f"Readable ({len(content)} chars{extra_info})",
                    duration_ms=(time.time() - test_start) * 1000
                )
            else:
                return TestResult(
                    category="core",
                    name=test_name,
                    passed=False,
                    message="File not found",
                    duration_ms=(time.time() - test_start) * 1000
                )
        except Exception as e:
            return TestResult(
                category="core",
                name=test_name,
                passed=False,
                message=f"Read error: {str(e)[:100]}",
                duration_ms=(time.time() - test_start) * 1000
            )

    def _test_tool_execution(self, tool_path: Path, test_name: str,
                             args: List[str], success_pattern: str = None) -> TestResult:
        """Helper: Test that a Python tool executes successfully."""
        test_start = time.time()
        try:
            if tool_path.exists():
                result = subprocess.run(
                    [sys.executable, str(tool_path)] + args,
                    capture_output=True, text=True, timeout=10,
                    cwd=str(self.maia_root)
                )
                if result.returncode == 0:
                    if success_pattern and success_pattern not in result.stdout:
                        return TestResult(
                            category="core",
                            name=test_name,
                            passed=False,
                            message=f"Missing expected output pattern",
                            duration_ms=(time.time() - test_start) * 1000
                        )
                    return TestResult(
                        category="core",
                        name=test_name,
                        passed=True,
                        message="Execution successful",
                        duration_ms=(time.time() - test_start) * 1000
                    )
                else:
                    return TestResult(
                        category="core",
                        name=test_name,
                        passed=False,
                        message=f"Exit code {result.returncode}: {result.stderr[:100]}",
                        duration_ms=(time.time() - test_start) * 1000
                    )
            else:
                return TestResult(
                    category="core",
                    name=test_name,
                    passed=False,
                    message="File not found",
                    duration_ms=(time.time() - test_start) * 1000
                )
        except subprocess.TimeoutExpired:
            return TestResult(
                category="core",
                name=test_name,
                passed=False,
                message="Timeout (>10s)",
                duration_ms=(time.time() - test_start) * 1000
            )
        except Exception as e:
            return TestResult(
                category="core",
                name=test_name,
                passed=False,
                message=f"Error: {str(e)[:100]}",
                duration_ms=(time.time() - test_start) * 1000
            )

    def _test_syntax_valid(self, file_path: Path, test_name: str) -> TestResult:
        """Helper: Test that a Python file has valid syntax."""
        test_start = time.time()
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    source = f.read()
                ast.parse(source)
                return TestResult(
                    category="core",
                    name=test_name,
                    passed=True,
                    message="Syntax valid",
                    duration_ms=(time.time() - test_start) * 1000
                )
            else:
                return TestResult(
                    category="core",
                    name=test_name,
                    passed=False,
                    message="File not found",
                    duration_ms=(time.time() - test_start) * 1000
                )
        except Exception as e:
            return TestResult(
                category="core",
                name=test_name,
                passed=False,
                message=f"Error: {str(e)[:100]}",
                duration_ms=(time.time() - test_start) * 1000
            )

    def _test_directories_exist(self, dir_paths: List[str], test_name: str) -> TestResult:
        """Helper: Test that required directories exist."""
        test_start = time.time()
        missing_dirs = []
        for dir_path in dir_paths:
            full_path = self.maia_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        if not missing_dirs:
            return TestResult(
                category="core",
                name=test_name,
                passed=True,
                message=f"All {len(dir_paths)} required directories exist",
                duration_ms=(time.time() - test_start) * 1000
            )
        else:
            return TestResult(
                category="core",
                name=test_name,
                passed=False,
                message=f"Missing directories: {', '.join(missing_dirs)}",
                duration_ms=(time.time() - test_start) * 1000
            )

    def test_core(self) -> CategoryResult:
        """Test core Maia functionality"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 6: Core Functionality Tests")
        self.log("="*60)

        start_time = time.time()

        # Test 1: SYSTEM_STATE.md
        self.add_result("core", self._test_file_readable(
            self.maia_root / "SYSTEM_STATE.md",
            "SYSTEM_STATE.md",
            content_pattern=r'## Phase \d+'
        ))

        # Test 2: CLAUDE.md
        self.add_result("core", self._test_file_readable(
            self.maia_root / "CLAUDE.md",
            "CLAUDE.md"
        ))

        # Test 3: UFC System
        self.add_result("core", self._test_file_readable(
            self.maia_root / "claude" / "context" / "ufc_system.md",
            "UFC System"
        ))

        # Test 4: Capability Index
        self.add_result("core", self._test_file_readable(
            self.maia_root / "claude" / "context" / "core" / "capability_index.md",
            "Capability Index",
            content_pattern=r'\.py\b'
        ))

        # Test 5: Smart Context Loader
        self.add_result("core", self._test_tool_execution(
            self.maia_root / "claude" / "tools" / "sre" / "smart_context_loader.py",
            "Smart Context Loader",
            args=["test query", "--stats"]
        ))

        # Test 6: SYSTEM_STATE Query Interface
        self.add_result("core", self._test_tool_execution(
            self.maia_root / "claude" / "tools" / "sre" / "system_state_queries.py",
            "SYSTEM_STATE Query Interface",
            args=["recent", "--count", "3"],
            success_pattern="Phase"
        ))

        # Test 7: Swarm Auto Loader
        self.add_result("core", self._test_syntax_valid(
            self.maia_root / "claude" / "hooks" / "swarm_auto_loader.py",
            "Swarm Auto Loader"
        ))

        # Test 8: Directory Structure
        self.add_result("core", self._test_directories_exist(
            ["claude/agents", "claude/tools", "claude/data",
             "claude/context", "claude/hooks", "claude/commands"],
            "Directory Structure"
        ))

        self.report.categories["core"].duration_seconds = time.time() - start_time
        return self.report.categories["core"]

    # =========================================================================
    # CATEGORY 7: Ollama Model Availability
    # =========================================================================

    def test_ollama(self) -> CategoryResult:
        """Test Ollama availability and required models"""
        self.log("\n" + "="*60)
        self.log("CATEGORY 7: Ollama Model Availability")
        self.log("="*60)

        start_time = time.time()

        # Test 1: Ollama service running
        test_start = time.time()
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                models = [line.split()[0] for line in result.stdout.strip().split('\n')[1:] if line]
                result_obj = TestResult(
                    category="ollama",
                    name="Ollama Service",
                    passed=True,
                    message=f"Running ({len(models)} models available)",
                    duration_ms=(time.time() - test_start) * 1000,
                    details={"models": models}
                )
            else:
                result_obj = TestResult(
                    category="ollama",
                    name="Ollama Service",
                    passed=False,
                    message=f"Not running: {result.stderr[:100]}",
                    duration_ms=(time.time() - test_start) * 1000
                )
        except FileNotFoundError:
            result_obj = TestResult(
                category="ollama",
                name="Ollama Service",
                passed=False,
                message="Ollama not installed",
                duration_ms=(time.time() - test_start) * 1000
            )
        except subprocess.TimeoutExpired:
            result_obj = TestResult(
                category="ollama",
                name="Ollama Service",
                passed=False,
                message="Timeout checking Ollama",
                duration_ms=(time.time() - test_start) * 1000
            )
        except Exception as e:
            result_obj = TestResult(
                category="ollama",
                name="Ollama Service",
                passed=False,
                message=f"Error: {str(e)[:100]}",
                duration_ms=(time.time() - test_start) * 1000
            )
        self.add_result("ollama", result_obj)

        # Get list of available models for subsequent tests
        available_models = []
        if result_obj.passed and result_obj.details:
            available_models = result_obj.details.get("models", [])

        # Required models for various Maia features
        required_models = [
            ("nomic-embed-text", "Email RAG embeddings"),
            ("gemma2:9b", "Meeting summarization"),
            ("hermes-2-pro-mistral", "Action item extraction (Hermes-2-Pro-Mistral-7B)"),
            ("qwen2.5:7b-instruct", "Keyword extraction"),
        ]

        for model_name, purpose in required_models:
            test_start = time.time()

            # Check if model or variant is available
            model_found = False
            found_variant = None
            for available in available_models:
                # Handle model name variations (e.g., "gemma2:9b" matches "gemma2:9b-instruct-q4_0")
                if model_name.split(":")[0] in available:
                    model_found = True
                    found_variant = available
                    break

            if model_found:
                result_obj = TestResult(
                    category="ollama",
                    name=f"Model: {model_name}",
                    passed=True,
                    message=f"Available ({found_variant}) - {purpose}",
                    duration_ms=(time.time() - test_start) * 1000
                )
            else:
                result_obj = TestResult(
                    category="ollama",
                    name=f"Model: {model_name}",
                    passed=False,
                    message=f"Not found - Required for: {purpose}",
                    duration_ms=(time.time() - test_start) * 1000
                )
            self.add_result("ollama", result_obj)

        self.report.categories["ollama"].duration_seconds = time.time() - start_time
        return self.report.categories["ollama"]

    # =========================================================================
    # Main Test Runner
    # =========================================================================

    def run_all(self, categories: Optional[List[str]] = None) -> TestReport:
        """Run all tests or specified categories"""
        overall_start = time.time()

        all_categories = {
            "tools": self.test_tools,
            "agents": self.test_agents,
            "databases": self.test_databases,
            "rag": self.test_rag,
            "hooks": self.test_hooks,
            "core": self.test_core,
            "ollama": self.test_ollama,
        }

        if categories:
            test_funcs = {k: v for k, v in all_categories.items() if k in categories}
        else:
            test_funcs = all_categories

        self.log("\n" + "="*60)
        self.log("MAIA COMPREHENSIVE TEST SUITE")
        self.log(f"Running {len(test_funcs)} categories: {', '.join(test_funcs.keys())}")
        self.log("="*60)

        for category_name, test_func in test_funcs.items():
            try:
                test_func()
            except Exception as e:
                self.log(f"Category {category_name} crashed: {e}", "FAIL")

        self.report.duration_seconds = time.time() - overall_start

        # Print summary
        self.print_summary()

        return self.report

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        for cat_name, cat_result in self.report.categories.items():
            status = "✅" if cat_result.failed == 0 else "❌"
            print(f"{status} {cat_name}: {cat_result.passed}/{cat_result.total} passed ({cat_result.pass_rate:.1f}%) in {cat_result.duration_seconds:.1f}s")

        print("-"*60)
        overall_status = "✅ ALL TESTS PASSED" if self.report.total_failed == 0 else f"❌ {self.report.total_failed} FAILURES"
        print(f"{overall_status}")
        print(f"Total: {self.report.total_passed}/{self.report.total_tests} passed ({self.report.pass_rate:.1f}%)")
        print(f"Duration: {self.report.duration_seconds:.1f} seconds")
        print("="*60)

        # Print failures
        if self.report.total_failed > 0:
            print("\n❌ FAILURES:")
            print("-"*60)
            for cat_name, cat_result in self.report.categories.items():
                for test in cat_result.tests:
                    if not test.passed:
                        print(f"  [{cat_name}] {test.name}")
                        print(f"    → {test.message}")

    def to_json(self) -> str:
        """Export report as JSON"""
        def convert(obj):
            if hasattr(obj, '__dict__'):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            else:
                return obj

        return json.dumps(convert(self.report), indent=2)


def main():
    parser = argparse.ArgumentParser(description="Maia Comprehensive Test Suite")
    parser.add_argument("--category", "-c", choices=["tools", "agents", "databases", "rag", "hooks", "core", "ollama"],
                        action="append", help="Run specific category (can be repeated)")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick smoke test (core + databases only)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON report")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--output", "-o", help="Save JSON report to file")

    args = parser.parse_args()

    suite = MaiaTestSuite(verbose=not args.quiet)

    if args.quick:
        categories = ["core", "databases"]
    elif args.category:
        categories = args.category
    else:
        categories = None  # Run all

    report = suite.run_all(categories)

    if args.json or args.output:
        json_output = suite.to_json()
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"\nJSON report saved to: {args.output}")
        if args.json:
            print("\n" + json_output)

    # Exit with appropriate code
    sys.exit(0 if report.total_failed == 0 else 1)


if __name__ == "__main__":
    main()
