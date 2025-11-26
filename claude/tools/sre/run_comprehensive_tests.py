#!/usr/bin/env python3
"""
Maia Comprehensive Integration Test Runner
Automated execution of all integration tests with reporting

Usage:
    python3 run_comprehensive_tests.py                    # Run all tests
    python3 run_comprehensive_tests.py --category core    # Run specific category
    python3 run_comprehensive_tests.py --quick            # Run smoke tests only
    python3 run_comprehensive_tests.py --report report.json  # Custom report path
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Maia root directory (4 levels up from claude/tools/sre/run_comprehensive_tests.py)
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.absolute()

class TestRunner:
    """Orchestrates comprehensive integration test execution"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "work_projects" / "maia_test_results" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "test_log.txt"
        self.results = {
            "start_time": datetime.now().isoformat(),
            "categories": {},
            "summary": {"passed": 0, "failed": 0, "skipped": 0}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def run_command(self, command: str, description: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute shell command and capture output"""
        self.log(f"Running: {description}", "TEST")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=MAIA_ROOT
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr

            if success:
                self.log(f"✅ PASS: {description}", "PASS")
            else:
                self.log(f"❌ FAIL: {description}", "FAIL")
                self.log(f"Output: {output[:500]}", "ERROR")

            return success, output
        except subprocess.TimeoutExpired:
            self.log(f"⏱️ TIMEOUT: {description}", "TIMEOUT")
            return False, "Command timed out"
        except Exception as e:
            self.log(f"💥 ERROR: {description} - {str(e)}", "ERROR")
            return False, str(e)

    def run_category_1_core_infrastructure(self) -> Dict:
        """Category 1: Core Infrastructure Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 1: CORE INFRASTRUCTURE", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Core Infrastructure", "tests": []}

        # T1.1.1 - UFC System Loading
        success, output = self.run_command(
            f"""python3 -c "
from claude.tools.sre.smart_context_loader import SmartContextLoader
loader = SmartContextLoader()
result = loader.load_guaranteed_minimum()
assert 'capability_counts' in result
assert 'recent_phases' in result
print('✅ T1.1.1: UFC guaranteed minimum loads')
" """,
            "T1.1.1 - UFC System Loading"
        )
        results["tests"].append({"id": "T1.1.1", "name": "UFC System Loading", "passed": success})

        # T1.1.2 - Smart Context Loader
        success, output = self.run_command(
            'python3 claude/tools/sre/smart_context_loader.py "system overview" --stats',
            "T1.1.2 - Smart Context Loader"
        )
        results["tests"].append({"id": "T1.1.2", "name": "Smart Context Loader", "passed": success})

        # T1.1.3 - Capability Loading
        success, output = self.run_command(
            f"""python3 -c "
from claude.tools.sre.smart_context_loader import SmartContextLoader
loader = SmartContextLoader()
summary = loader.load_capability_context()
assert summary is not None
print(f'✅ T1.1.3: Capability summary loaded')
" """,
            "T1.1.3 - Capability Loading"
        )
        results["tests"].append({"id": "T1.1.3", "name": "Capability Loading", "passed": success})

        # T1.2.1 - SYSTEM_STATE Database
        success, output = self.run_command(
            'python3 claude/tools/sre/system_state_queries.py recent --count 10',
            "T1.2.1 - SYSTEM_STATE Database Query"
        )
        results["tests"].append({"id": "T1.2.1", "name": "SYSTEM_STATE Database", "passed": success})

        # T1.2.4 - Capabilities Database
        success, output = self.run_command(
            'python3 claude/tools/sre/capabilities_registry.py summary',
            "T1.2.4 - Capabilities Database"
        )
        results["tests"].append({"id": "T1.2.4", "name": "Capabilities Database", "passed": success})

        # T1.2.5 - Database Integrity
        success, output = self.run_command(
            'find claude/data/databases -name "*.db" -exec sqlite3 {} "PRAGMA integrity_check;" \\; | grep -c "ok"',
            "T1.2.5 - Database Integrity Checks"
        )
        results["tests"].append({"id": "T1.2.5", "name": "Database Integrity", "passed": success})

        # T1.3.1 - Root Directory Compliance
        success, output = self.run_command(
            'test $(ls -1 | wc -l) -le 15 && echo "✅ Root directory compliant"',
            "T1.3.1 - Root Directory Compliance"
        )
        results["tests"].append({"id": "T1.3.1", "name": "Root Directory Compliance", "passed": success})

        # T1.3.2 - UFC Structure
        success, output = self.run_command(
            'test -d claude/agents && test -d claude/tools && test -d claude/commands && echo "✅ UFC structure valid"',
            "T1.3.2 - UFC Structure Validation"
        )
        results["tests"].append({"id": "T1.3.2", "name": "UFC Structure", "passed": success})

        # T1.4.1 - TDD Protocol Structure
        success, output = self.run_command(
            'grep -c "^## Phase" claude/context/core/tdd_development_protocol.md',
            "T1.4.1 - TDD Protocol Structure"
        )
        results["tests"].append({"id": "T1.4.1", "name": "TDD Protocol Structure", "passed": success})

        # T1.4.2 - Quality Gates Count
        success, output = self.run_command(
            'grep -c "^### Gate" claude/context/core/tdd_development_protocol.md',
            "T1.4.2 - Quality Gates Count"
        )
        results["tests"].append({"id": "T1.4.2", "name": "Quality Gates Count", "passed": success})

        return results

    def run_category_2_agent_system(self) -> Dict:
        """Category 2: Agent System Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 2: AGENT SYSTEM", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Agent System", "tests": []}

        # T2.1.1 - Agent File Discovery
        success, output = self.run_command(
            'ls claude/agents/*.md | wc -l',
            "T2.1.1 - Agent File Discovery"
        )
        results["tests"].append({"id": "T2.1.1", "name": "Agent File Discovery", "passed": success})

        # T2.1.5 - Context ID Stability
        success, output = self.run_command(
            'python3 claude/hooks/swarm_auto_loader.py get_context_id',
            "T2.1.5 - Context ID Stability"
        )
        results["tests"].append({"id": "T2.1.5", "name": "Context ID Stability", "passed": success})

        # T2.2.1 - SRE Principal Engineer Agent
        success, output = self.run_command(
            'test -f claude/agents/sre_principal_engineer_agent.md && grep -q "v2.3" claude/agents/sre_principal_engineer_agent.md && echo "✅ SRE agent v2.3"',
            "T2.2.1 - SRE Agent Validation"
        )
        results["tests"].append({"id": "T2.2.1", "name": "SRE Agent", "passed": success})

        # T2.3.1 - Adaptive Routing Database
        success, output = self.run_command(
            'test -f claude/data/databases/intelligence/adaptive_routing.db && echo "✅ Adaptive routing DB exists"',
            "T2.3.1 - Adaptive Routing Database"
        )
        results["tests"].append({"id": "T2.3.1", "name": "Adaptive Routing DB", "passed": success})

        return results

    def run_category_3_tool_ecosystem(self) -> Dict:
        """Category 3: Tool Ecosystem Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 3: TOOL ECOSYSTEM", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Tool Ecosystem", "tests": []}

        # T3.1.1 - Full Test Suite
        success, output = self.run_command(
            'python3 claude/tools/sre/maia_comprehensive_test_suite.py --quiet',
            "T3.1.1 - Full Comprehensive Test Suite",
            timeout=60
        )
        results["tests"].append({"id": "T3.1.1", "name": "Full Test Suite", "passed": success})

        # T3.2.1 - PMP OAuth Manager
        success, output = self.run_command(
            f"""python3 -c "
from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
manager = PMPOAuthManager()
assert hasattr(manager, 'get_valid_token')
print('✅ T3.2.1: PMP OAuth manager imports')
" """,
            "T3.2.1 - PMP OAuth Manager"
        )
        results["tests"].append({"id": "T3.2.1", "name": "PMP OAuth Manager", "passed": success})

        # T3.2.3 - PMP Resilient Extractor
        success, output = self.run_command(
            'test -f claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py && python3 -m py_compile claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py && echo "✅ Compiles"',
            "T3.2.3 - PMP Resilient Extractor Compilation"
        )
        results["tests"].append({"id": "T3.2.3", "name": "PMP Resilient Extractor", "passed": success})

        # T3.2.4 - PMP DCAPI Extractor
        success, output = self.run_command(
            'test -f claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && python3 -m py_compile claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && echo "✅ Compiles"',
            "T3.2.4 - PMP DCAPI Extractor Compilation"
        )
        results["tests"].append({"id": "T3.2.4", "name": "PMP DCAPI Extractor", "passed": success})

        return results

    def run_category_4_data_intelligence(self) -> Dict:
        """Category 4: Data & Intelligence Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 4: DATA & INTELLIGENCE", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Data & Intelligence", "tests": []}

        # T4.1.1 - PMP Database Existence
        success, output = self.run_command(
            'test -f ~/.maia/databases/intelligence/pmp_config.db && echo "✅ PMP DB exists"',
            "T4.1.1 - PMP Database Existence"
        )
        results["tests"].append({"id": "T4.1.1", "name": "PMP Database", "passed": success})

        # T4.1.2 - PMP Database Schema
        success, output = self.run_command(
            'sqlite3 ~/.maia/databases/intelligence/pmp_config.db ".schema" | grep -c "CREATE TABLE"',
            "T4.1.2 - PMP Database Schema"
        )
        results["tests"].append({"id": "T4.1.2", "name": "PMP Schema", "passed": success})

        # T4.2.1 - Meeting Intelligence Database
        success, output = self.run_command(
            'test -f claude/data/databases/intelligence/meetings.db && echo "✅ Meeting DB exists"',
            "T4.2.1 - Meeting Intelligence Database"
        )
        results["tests"].append({"id": "T4.2.1", "name": "Meeting DB", "passed": success})

        # T4.3.1 - Email RAG Database
        success, output = self.run_command(
            'test -d claude/data/rag_databases/email_rag_ollama && echo "✅ Email RAG DB exists"',
            "T4.3.1 - Email RAG Database"
        )
        results["tests"].append({"id": "T4.3.1", "name": "Email RAG", "passed": success})

        return results

    def run_category_5_development_infra(self) -> Dict:
        """Category 5: Development Infrastructure Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 5: DEVELOPMENT INFRASTRUCTURE", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Development Infrastructure", "tests": []}

        # T5.1.3 - Phase 194 TDD Files
        success, output = self.run_command(
            'test -f claude/tools/pmp/pmp_dcapi_patch_extractor/requirements.md && test -f claude/tools/pmp/pmp_dcapi_patch_extractor/test_pmp_dcapi_patch_extractor.py && test -f claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && echo "✅ TDD files complete"',
            "T5.1.3 - Phase 194 TDD Files"
        )
        results["tests"].append({"id": "T5.1.3", "name": "Phase 194 TDD Files", "passed": success})

        # T5.1.5 - TDD Protocol Documentation
        success, output = self.run_command(
            'grep -c "Quality Gate" claude/context/core/tdd_development_protocol.md',
            "T5.1.5 - TDD Protocol Documentation"
        )
        results["tests"].append({"id": "T5.1.5", "name": "TDD Protocol", "passed": success})

        # T5.2.4 - Path Sync Validation
        success, output = self.run_command(
            'python3 claude/tools/sre/path_sync.py validate',
            "T5.2.4 - Path Sync Validation"
        )
        results["tests"].append({"id": "T5.2.4", "name": "Path Sync", "passed": success})

        # T5.3.1 - Phantom Tool Audit
        success, output = self.run_command(
            'python3 claude/tools/sre/phantom_tool_auditor.py --summary',
            "T5.3.1 - Phantom Tool Audit (Quality Check)",
            timeout=60
        )
        results["tests"].append({"id": "T5.3.1", "name": "Phantom Tool Audit", "passed": success})

        return results

    def run_category_6_integration_points(self) -> Dict:
        """Category 6: Integration Points Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 6: INTEGRATION POINTS", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Integration Points", "tests": []}

        # T6.1.1 - Cross-Database Query
        success, output = self.run_command(
            f"""python3 -c "
from claude.tools.sre.system_state_queries import SystemStateQueries
from claude.tools.sre.capabilities_registry import CapabilitiesRegistry
ssq = SystemStateQueries()
cap = CapabilitiesRegistry()
phases = ssq.get_recent_phases(5)
caps = cap.get_summary()
assert len(phases) == 5
assert 'total' in caps
print('✅ T6.1.1: Cross-DB query successful')
" """,
            "T6.1.1 - Cross-Database Query"
        )
        results["tests"].append({"id": "T6.1.1", "name": "Cross-DB Query", "passed": success})

        # T6.2.1 - OAuth Manager Import
        success, output = self.run_command(
            f"""python3 -c "
from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
manager = PMPOAuthManager()
assert hasattr(manager, 'authorize')
assert hasattr(manager, 'get_valid_token')
print('✅ T6.2.1: OAuth manager functional')
" """,
            "T6.2.1 - OAuth Manager Import"
        )
        results["tests"].append({"id": "T6.2.1", "name": "OAuth Manager", "passed": success})

        return results

    def run_category_7_performance_resilience(self) -> Dict:
        """Category 7: Performance & Resilience Tests"""
        self.log("=" * 60, "INFO")
        self.log("CATEGORY 7: PERFORMANCE & RESILIENCE", "INFO")
        self.log("=" * 60, "INFO")

        results = {"name": "Performance & Resilience", "tests": []}

        # T7.1.4 - Test Suite Performance
        start_time = time.time()
        success, output = self.run_command(
            'python3 claude/tools/sre/maia_comprehensive_test_suite.py --quiet',
            "T7.1.4 - Test Suite Performance",
            timeout=10
        )
        elapsed = time.time() - start_time
        self.log(f"Test suite completed in {elapsed:.2f}s", "PERF")
        results["tests"].append({"id": "T7.1.4", "name": "Test Suite Performance", "passed": success and elapsed < 2.0})

        # T7.2.2 - Error Handling Patterns
        success, output = self.run_command(
            'grep -c "try:" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py',
            "T7.2.2 - Error Handling Patterns"
        )
        results["tests"].append({"id": "T7.2.2", "name": "Error Handling", "passed": success})

        # T7.3.1 - Structured Logging
        success, output = self.run_command(
            'grep -c "json" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py',
            "T7.3.1 - Structured Logging"
        )
        results["tests"].append({"id": "T7.3.1", "name": "Structured Logging", "passed": success})

        return results

    def run_all_categories(self):
        """Run all test categories"""
        self.log("=" * 80, "INFO")
        self.log("MAIA COMPREHENSIVE INTEGRATION TEST SUITE", "INFO")
        self.log(f"Started: {self.results['start_time']}", "INFO")
        self.log(f"Output Directory: {self.output_dir}", "INFO")
        self.log("=" * 80, "INFO")

        categories = [
            ("core_infrastructure", self.run_category_1_core_infrastructure),
            ("agent_system", self.run_category_2_agent_system),
            ("tool_ecosystem", self.run_category_3_tool_ecosystem),
            ("data_intelligence", self.run_category_4_data_intelligence),
            ("development_infra", self.run_category_5_development_infra),
            ("integration_points", self.run_category_6_integration_points),
            ("performance_resilience", self.run_category_7_performance_resilience),
        ]

        for category_id, category_func in categories:
            try:
                category_results = category_func()
                self.results["categories"][category_id] = category_results

                # Update summary
                for test in category_results["tests"]:
                    if test["passed"]:
                        self.results["summary"]["passed"] += 1
                    else:
                        self.results["summary"]["failed"] += 1
            except Exception as e:
                self.log(f"Category {category_id} failed with error: {str(e)}", "ERROR")
                self.results["categories"][category_id] = {
                    "name": category_id,
                    "error": str(e),
                    "tests": []
                }

        self.results["end_time"] = datetime.now().isoformat()
        self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        self.log("=" * 80, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 80, "INFO")

        total = self.results["summary"]["passed"] + self.results["summary"]["failed"]
        pass_rate = (self.results["summary"]["passed"] / total * 100) if total > 0 else 0

        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {self.results['summary']['passed']}", "INFO")
        self.log(f"Failed: {self.results['summary']['failed']}", "INFO")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "INFO")

        # Category breakdown
        self.log("", "INFO")
        self.log("Category Breakdown:", "INFO")
        for category_id, category_data in self.results["categories"].items():
            if "error" in category_data:
                self.log(f"  {category_data.get('name', category_id)}: ERROR", "ERROR")
            else:
                passed = sum(1 for t in category_data["tests"] if t["passed"])
                total_cat = len(category_data["tests"])
                rate = (passed / total_cat * 100) if total_cat > 0 else 0
                self.log(f"  {category_data['name']}: {passed}/{total_cat} ({rate:.1f}%)", "INFO")

        # Save JSON report
        report_file = self.output_dir / "test_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        self.log(f"", "INFO")
        self.log(f"JSON report saved: {report_file}", "INFO")
        self.log(f"Log file saved: {self.log_file}", "INFO")

        # Success/failure determination
        if pass_rate >= 95:
            self.log("", "INFO")
            self.log("✅ TEST SUITE PASSED (≥95% pass rate)", "SUCCESS")
            return 0
        else:
            self.log("", "INFO")
            self.log("❌ TEST SUITE FAILED (<95% pass rate)", "FAIL")
            return 1

def main():
    parser = argparse.ArgumentParser(description="Run Maia comprehensive integration tests")
    parser.add_argument("--category", choices=["core", "agent", "tool", "data", "dev", "integration", "performance"],
                       help="Run specific category only")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    parser.add_argument("--output", help="Custom output directory")

    args = parser.parse_args()

    runner = TestRunner(output_dir=args.output)

    if args.quick:
        runner.log("Running QUICK SMOKE TESTS", "INFO")
        # Run subset of critical tests
        runner.run_category_1_core_infrastructure()
        runner.run_category_3_tool_ecosystem()
        runner.generate_report()
    elif args.category:
        runner.log(f"Running CATEGORY: {args.category}", "INFO")
        category_map = {
            "core": runner.run_category_1_core_infrastructure,
            "agent": runner.run_category_2_agent_system,
            "tool": runner.run_category_3_tool_ecosystem,
            "data": runner.run_category_4_data_intelligence,
            "dev": runner.run_category_5_development_infra,
            "integration": runner.run_category_6_integration_points,
            "performance": runner.run_category_7_performance_resilience,
        }
        if args.category in category_map:
            category_map[args.category]()
            runner.generate_report()
    else:
        runner.run_all_categories()

    # Exit with appropriate code
    sys.exit(0 if runner.results["summary"]["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
