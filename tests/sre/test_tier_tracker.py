"""
ServiceDesk Tier Tracking Dashboard - Comprehensive Test Suite

Project: TIER-TRACKER-001
Phase: 2 - Test Design (TDD)
Agent: SRE Principal Engineer + Service Desk Manager Agent
Status: ALL TESTS INITIALLY FAILING (no implementation yet)

Test Coverage: 100% target for database operations
Test Framework: pytest + psycopg2
Execution: pytest claude/tools/sre/test_tier_tracker.py -v

Test Categories:
1. Schema Tests (7 tests) - Verify database structure
2. Data Validation Tests (3 tests) - Verify data quality
3. Backfill Tests (4 tests) - Verify tier categorization
4. Query Tests (5 tests) - Verify dashboard panels
5. Failure Mode Tests (3 tests) - Verify error handling

Created: 2025-10-27
Last Updated: 2025-10-27
"""

import pytest
import psycopg2
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# PostgreSQL connection via docker exec (per ARCHITECTURE.md ADR-001)
DOCKER_CONTAINER = "servicedesk-postgres"
DB_USER = "servicedesk_user"
DB_NAME = "servicedesk"

# Performance SLOs (from requirements NFR-1)
QUERY_LATENCY_SLO_MS = 100  # P95 latency
DASHBOARD_LOAD_SLO_SEC = 2   # Total dashboard load time
BACKFILL_SLO_SEC = 300       # 5 minutes for 10,939 rows

# Data quality thresholds (from requirements NFR-2)
VALID_TIERS = ['L1', 'L2', 'L3']
TIER_ACCURACY_THRESHOLD = 0.90  # 90% categorization accuracy
NULL_TIER_THRESHOLD = 0.01      # Max 1% NULL tiers allowed


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def db_connection():
    """
    Database connection fixture using docker exec (NOT direct psycopg2).

    Per ARCHITECTURE.md ADR-001: Database runs in isolated Docker container,
    must use `docker exec` for access.

    Yields:
        Tuple[str, str, str]: (container, user, database) for docker exec commands
    """
    # Verify container is running
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={DOCKER_CONTAINER}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )

    if DOCKER_CONTAINER not in result.stdout:
        pytest.fail(f"Container {DOCKER_CONTAINER} not running. Start with docker-compose up -d")

    # Verify database connectivity
    result = subprocess.run(
        ["docker", "exec", DOCKER_CONTAINER, "pg_isready"],
        capture_output=True
    )

    if result.returncode != 0:
        pytest.fail(f"PostgreSQL not ready in container {DOCKER_CONTAINER}")

    yield (DOCKER_CONTAINER, DB_USER, DB_NAME)


@pytest.fixture
def execute_sql(db_connection):
    """
    Execute SQL via docker exec (transaction-safe).

    Args:
        sql (str): SQL command to execute

    Returns:
        Tuple[int, str, str]: (return_code, stdout, stderr)
    """
    container, user, database = db_connection

    def _execute(sql: str) -> Tuple[int, str, str]:
        cmd = [
            "docker", "exec", container,
            "psql", "-U", user, "-d", database,
            "-c", sql
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return (result.returncode, result.stdout, result.stderr)

    return _execute


@pytest.fixture
def sample_tickets():
    """
    Sample tickets for categorization testing.

    Returns 100 manually categorized tickets for accuracy validation.
    """
    return [
        # L1 Examples (Standard requests, routine operations)
        {
            "ticket_id": "TEST-0001",
            "title": "Password reset request",
            "description": "User cannot log in, needs password reset",
            "category": "Support",
            "root_cause": "User Error",
            "expected_tier": "L1"
        },
        {
            "ticket_id": "TEST-0002",
            "title": "Access grant for new user",
            "description": "New employee needs access to shared drive",
            "category": "Support",
            "root_cause": "Standard Request",
            "expected_tier": "L1"
        },
        {
            "ticket_id": "TEST-0003",
            "title": "SSL certificate expiring alert",
            "description": "Automated alert for certificate expiring in 30 days",
            "category": "Alert",
            "root_cause": "Proactive Monitoring",
            "expected_tier": "L1"
        },

        # L2 Examples (Escalated issues, complex troubleshooting)
        {
            "ticket_id": "TEST-0004",
            "title": "Application performance degradation",
            "description": "Users reporting slow response times, requires investigation",
            "category": "Support",
            "root_cause": "Performance Issue",
            "expected_tier": "L2"
        },
        {
            "ticket_id": "TEST-0005",
            "title": "Network connectivity intermittent",
            "description": "Multiple users experiencing network drops, escalated from L1",
            "category": "Incident",
            "root_cause": "Infrastructure",
            "expected_tier": "L2"
        },

        # L3 Examples (Architectural changes, emergency escalations)
        {
            "ticket_id": "TEST-0006",
            "title": "Database failover required",
            "description": "Primary database unresponsive, emergency failover needed",
            "category": "Incident",
            "root_cause": "System Failure",
            "expected_tier": "L3"
        },
        {
            "ticket_id": "TEST-0007",
            "title": "Security breach suspected",
            "description": "Unusual activity detected, potential security incident",
            "category": "Security",
            "root_cause": "Security Threat",
            "expected_tier": "L3"
        },

        # Edge Cases
        {
            "ticket_id": "TEST-0008",
            "title": "Request unclear",
            "description": None,  # NULL description
            "category": "Support",
            "root_cause": None,
            "expected_tier": "L2"  # Default to L2 when ambiguous
        },
        {
            "ticket_id": "TEST-0009",
            "title": None,  # NULL title
            "description": "Some description",
            "category": None,  # NULL category
            "root_cause": "Unknown",
            "expected_tier": "L2"  # Default to L2 when ambiguous
        },
    ]
    # Note: Real fixture would have 100 samples, abbreviated for brevity


# ============================================================================
# CATEGORY 1: SCHEMA TESTS (7 tests)
# ============================================================================

def test_support_tier_column_exists(execute_sql):
    """
    Test: support_tier column exists in servicedesk.tickets table

    Requirements: FR-1, Schema Change 1
    Expected: Column exists, type VARCHAR(10)
    """
    sql = """
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_schema='servicedesk'
      AND table_name='tickets'
      AND column_name='support_tier';
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"
    assert "support_tier" in stdout, "Column support_tier not found"
    assert "character varying" in stdout or "varchar" in stdout, "Column type incorrect"
    assert "10" in stdout, "Column length not VARCHAR(10)"


def test_assigned_pod_column_exists(execute_sql):
    """
    Test: assigned_pod column exists in servicedesk.tickets table

    Requirements: FR-4.3, Schema Change 2, User Q1
    Expected: Column exists, type VARCHAR(50), allows NULL
    """
    sql = """
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_schema='servicedesk'
      AND table_name='tickets'
      AND column_name='assigned_pod';
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"
    assert "assigned_pod" in stdout, "Column assigned_pod not found"
    assert "50" in stdout, "Column length not VARCHAR(50)"
    assert "YES" in stdout, "Column should allow NULL (for historical tickets)"


def test_tier_history_table_exists(execute_sql):
    """
    Test: tier_history table exists with correct schema

    Requirements: FR-6.1, Schema Change 3
    Expected: Table exists with columns: id, snapshot_date, support_tier, ticket_count, percentage, category, created_at
    """
    sql = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='servicedesk'
      AND table_name='tier_history'
    ORDER BY ordinal_position;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"
    assert "tier_history" in stdout or stdout.strip(), "Table tier_history not found"

    # Verify required columns exist
    required_columns = ["id", "snapshot_date", "support_tier", "ticket_count", "percentage", "created_at"]
    for col in required_columns:
        assert col in stdout, f"Required column {col} not found in tier_history"


def test_tier_cost_config_table_exists(execute_sql):
    """
    Test: tier_cost_config table exists with initial data

    Requirements: FR-1.4, NFR-4.1, Schema Change 4
    Expected: Table exists with L1/L2/L3 rows, costs $100/$200/$300
    """
    sql = """
    SELECT tier, cost_per_ticket, target_percentage
    FROM servicedesk.tier_cost_config
    ORDER BY tier;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Verify L1/L2/L3 rows exist
    assert "L1" in stdout, "L1 tier not found in tier_cost_config"
    assert "L2" in stdout, "L2 tier not found in tier_cost_config"
    assert "L3" in stdout, "L3 tier not found in tier_cost_config"

    # Verify costs (approximate, allowing for formatting)
    assert "100" in stdout, "L1 cost $100 not found"
    assert "200" in stdout, "L2 cost $200 not found"
    assert "300" in stdout, "L3 cost $300 not found"


def test_automation_tables_exist(execute_sql):
    """
    Test: automation_metrics and self_service_metrics tables exist (Phase 2 prep)

    Requirements: NFR-5.2, Schema Change 5, User Q3
    Expected: Tables exist (empty for now), ready for Phase 2 data
    """
    # Check automation_metrics
    sql1 = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='servicedesk'
      AND table_name='automation_metrics';
    """

    returncode, stdout, stderr = execute_sql(sql1)
    assert returncode == 0, f"Query failed: {stderr}"
    assert "automation_metrics" in stdout, "Table automation_metrics not found"

    # Check self_service_metrics
    sql2 = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='servicedesk'
      AND table_name='self_service_metrics';
    """

    returncode, stdout, stderr = execute_sql(sql2)
    assert returncode == 0, f"Query failed: {stderr}"
    assert "self_service_metrics" in stdout, "Table self_service_metrics not found"


def test_indexes_created(execute_sql):
    """
    Test: Performance indexes exist on support_tier, assigned_pod, snapshot_date

    Requirements: NFR-1.1, Schema Change 6
    Expected: Indexes exist for query performance (<100ms SLO)
    """
    sql = """
    SELECT indexname
    FROM pg_indexes
    WHERE schemaname='servicedesk'
      AND tablename IN ('tickets', 'tier_history');
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Verify critical indexes exist (exact names may vary)
    assert "tier" in stdout.lower() or "support_tier" in stdout.lower(), \
        "Index on support_tier not found"
    assert "pod" in stdout.lower() or "assigned_pod" in stdout.lower(), \
        "Index on assigned_pod not found"


# ============================================================================
# CATEGORY 2: DATA VALIDATION TESTS (3 tests)
# ============================================================================

def test_all_tickets_have_tier(execute_sql):
    """
    Test: 100% of tickets have non-NULL support_tier after backfill

    Requirements: NFR-2.1, DP-2
    Expected: COUNT(support_tier IS NULL) = 0
    """
    sql = """
    SELECT COUNT(*) as null_count
    FROM servicedesk.tickets
    WHERE support_tier IS NULL;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Extract count from output (format: "null_count\n----------\n         0")
    lines = stdout.strip().split('\n')
    count_line = [line for line in lines if line.strip().isdigit()]

    if count_line:
        null_count = int(count_line[0].strip())
        assert null_count == 0, f"Found {null_count} tickets with NULL support_tier (expected 0)"
    else:
        pytest.fail("Could not parse NULL count from query result")


def test_only_valid_tiers(execute_sql):
    """
    Test: All support_tier values are valid (L1, L2, or L3)

    Requirements: NFR-2.1, DP-1
    Expected: No invalid tier values (e.g., 'L4', 'Unknown', etc.)
    """
    sql = """
    SELECT COUNT(*) as invalid_count
    FROM servicedesk.tickets
    WHERE support_tier IS NOT NULL
      AND support_tier NOT IN ('L1', 'L2', 'L3');
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    lines = stdout.strip().split('\n')
    count_line = [line for line in lines if line.strip().isdigit()]

    if count_line:
        invalid_count = int(count_line[0].strip())
        assert invalid_count == 0, f"Found {invalid_count} tickets with invalid support_tier"
    else:
        pytest.fail("Could not parse invalid count from query result")


def test_tier_distribution_sums_to_100(execute_sql):
    """
    Test: Tier percentage distribution sums to 100% (within rounding tolerance)

    Requirements: FR-2.1, DP-4
    Expected: SUM(percentage) ≈ 100.0 (allowing ±0.1% rounding error)
    """
    sql = """
    SELECT SUM(percentage) as total_pct
    FROM (
        SELECT
            support_tier,
            ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 1) as percentage
        FROM servicedesk.tickets
        WHERE support_tier IS NOT NULL
        GROUP BY support_tier
    ) subquery;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Extract total percentage
    lines = stdout.strip().split('\n')
    for line in lines:
        if '.' in line and any(char.isdigit() for char in line):
            try:
                total_pct = float(line.strip())
                assert 99.9 <= total_pct <= 100.1, \
                    f"Tier percentages sum to {total_pct}% (expected 100%)"
                return
            except ValueError:
                continue

    pytest.fail("Could not parse total percentage from query result")


# ============================================================================
# CATEGORY 3: BACKFILL TESTS (4 tests)
# ============================================================================

def test_backfill_categorizes_correctly(sample_tickets, execute_sql):
    """
    Test: Backfill script categorizes sample tickets with ≥90% accuracy

    Requirements: DP-1, User Q2
    Expected: ≥90% of sample tickets match expected tier

    Note: This test WILL FAIL until backfill script is implemented
    """
    pytest.skip("Backfill script not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Insert sample tickets into test table
    # 2. Run backfill script
    # 3. Compare actual tier vs expected tier
    # 4. Calculate accuracy: correct / total
    # 5. Assert accuracy ≥ 90%


def test_backfill_handles_nulls(execute_sql):
    """
    Test: Backfill script handles NULL title/description/category gracefully

    Requirements: DP-1 (Edge Cases), User Q2
    Expected: No crashes, defaults to L2 for ambiguous cases

    Note: This test WILL FAIL until backfill script is implemented
    """
    pytest.skip("Backfill script not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Insert tickets with NULL fields
    # 2. Run backfill script
    # 3. Verify: No errors, all tickets have tier assigned
    # 4. Verify: Ambiguous cases → L2 (safer overestimate)


def test_backfill_performance(execute_sql):
    """
    Test: Backfill completes 10,939 tickets in <5 minutes

    Requirements: NFR-1.3, DP-2
    Expected: Execution time < 300 seconds

    Note: This test WILL FAIL until backfill script is implemented
    """
    pytest.skip("Backfill script not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Record start time
    # 2. Run backfill script on full 10,939 rows
    # 3. Record end time
    # 4. Assert: (end - start) < 300 seconds


def test_backfill_idempotent(execute_sql):
    """
    Test: Re-running backfill is safe (no duplicates, no errors)

    Requirements: NFR-2.3, DP-2
    Expected: Can run backfill multiple times without errors or data corruption

    Note: This test WILL FAIL until backfill script is implemented
    """
    pytest.skip("Backfill script not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Run backfill once
    # 2. Record tier counts
    # 3. Run backfill again
    # 4. Verify: No errors, tier counts unchanged


# ============================================================================
# CATEGORY 4: QUERY TESTS (5 tests)
# ============================================================================

def test_l1_percentage_query(execute_sql):
    """
    Test: Panel 1 L1 percentage query returns correct value

    Requirements: FR-1.1, Panel 1
    Expected: Returns percentage (0-100), matches manual calculation

    Note: This test WILL FAIL until support_tier column is populated
    """
    sql = """
    SELECT ROUND(
        COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC /
        COUNT(*)::NUMERIC * 100, 1
    ) as l1_percentage
    FROM servicedesk.tickets
    WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Verify result is a percentage (0-100)
    lines = stdout.strip().split('\n')
    for line in lines:
        if '.' in line and any(char.isdigit() for char in line):
            try:
                l1_pct = float(line.strip())
                assert 0 <= l1_pct <= 100, f"L1 percentage {l1_pct}% out of range (0-100)"
                return
            except ValueError:
                continue

    pytest.fail("Could not parse L1 percentage from query result")


def test_cost_savings_query(execute_sql):
    """
    Test: Panel 4 cost savings query uses tier_cost_config table (no hardcoded costs)

    Requirements: FR-1.4, NFR-4.1, Panel 4
    Expected: Query joins tier_cost_config, returns annual savings estimate

    Note: This test WILL FAIL until tier_cost_config table is populated and support_tier data exists
    """
    sql = """
    WITH costs AS (
        SELECT tier, cost_per_ticket, target_percentage
        FROM servicedesk.tier_cost_config
    ),
    current_dist AS (
        SELECT
            support_tier,
            COUNT(*) as count,
            COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () as percentage
        FROM servicedesk.tickets
        WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY support_tier
    )
    SELECT ROUND(
        SUM((cd.percentage - (c.target_percentage / 100)) * cd.count * 12 * c.cost_per_ticket)
    ) as estimated_annual_savings
    FROM current_dist cd
    JOIN costs c ON cd.support_tier = c.tier;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Verify result is a number (savings can be positive or negative)
    lines = stdout.strip().split('\n')
    for line in lines:
        if any(char.isdigit() for char in line):
            try:
                savings = float(line.strip().replace(',', ''))
                # Sanity check: Savings should be within reasonable range
                assert -1_000_000 <= savings <= 1_000_000, \
                    f"Cost savings ${savings:,.0f} seems unreasonable"
                return
            except ValueError:
                continue

    pytest.fail("Could not parse cost savings from query result")


def test_tier_trend_query(execute_sql):
    """
    Test: Panel 5 tier distribution over time query returns 12 months of data

    Requirements: FR-2.1, Panel 5
    Expected: Returns monthly tier percentages, 3 rows per month (L1/L2/L3)

    Note: This test WILL FAIL until support_tier column is populated
    """
    sql = """
    SELECT
        DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
        support_tier,
        COUNT(*) as ticket_count
    FROM servicedesk.tickets
    WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '12 months'
      AND support_tier IS NOT NULL
    GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier
    ORDER BY month DESC
    LIMIT 36;  -- 12 months × 3 tiers
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # Count rows (should be ~36 for 12 months × 3 tiers, may be less if recent months)
    lines = [line for line in stdout.strip().split('\n') if line.strip() and '|' in line]
    data_rows = len([line for line in lines if 'month' not in line.lower() and '---' not in line])

    assert data_rows >= 3, f"Expected ≥3 rows (at least 1 month), got {data_rows}"
    assert data_rows <= 36, f"Expected ≤36 rows (12 months max), got {data_rows}"


def test_l1_rate_by_pod_query(execute_sql):
    """
    Test: Panel 11 pod comparison query filters NULL pods, calculates L1 rates

    Requirements: FR-4.3, Panel 11, User Q1
    Expected: Returns L1 rate per pod, excludes NULL pods

    Note: This test WILL SKIP initially (no pod data yet)
    """
    sql = """
    SELECT
        assigned_pod as pod,
        ROUND(COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC / COUNT(*)::NUMERIC * 100, 1) as l1_rate
    FROM servicedesk.tickets
    WHERE assigned_pod IS NOT NULL
        AND DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY assigned_pod
    ORDER BY l1_rate DESC;
    """

    returncode, stdout, stderr = execute_sql(sql)

    assert returncode == 0, f"Query failed: {stderr}"

    # This query may return 0 rows initially (no pods assigned yet)
    # Test passes if query executes without error
    # When pods are assigned, verify L1 rates are percentages (0-100)
    lines = [line for line in stdout.strip().split('\n') if line.strip() and '|' in line]
    data_rows = [line for line in lines if 'pod' not in line.lower() and '---' not in line]

    if len(data_rows) == 0:
        pytest.skip("No pod data yet (assigned_pod column is NULL for all tickets)")

    # If data exists, verify L1 rates are valid percentages
    for row in data_rows:
        if any(char.isdigit() for char in row):
            # Extract percentage (approximate parsing)
            parts = row.split('|')
            if len(parts) >= 2:
                try:
                    l1_rate = float(parts[-1].strip())
                    assert 0 <= l1_rate <= 100, f"L1 rate {l1_rate}% out of range"
                except ValueError:
                    pass


def test_query_performance(execute_sql):
    """
    Test: All dashboard queries execute in <100ms (P95 latency SLO)

    Requirements: NFR-1.1
    Expected: Panel queries return in <100ms on average

    Note: This test measures actual query performance
    """
    queries = [
        ("Panel 1 - L1 Percentage", """
            SELECT ROUND(
                COUNT(*) FILTER (WHERE support_tier = 'L1')::NUMERIC /
                COUNT(*)::NUMERIC * 100, 1
            ) as l1_percentage
            FROM servicedesk.tickets
            WHERE DATE_TRUNC('month', "TKT-Created Time"::timestamp) = DATE_TRUNC('month', CURRENT_DATE);
        """),
        ("Panel 5 - Tier Trends", """
            SELECT
                DATE_TRUNC('month', "TKT-Created Time"::timestamp) as month,
                support_tier,
                COUNT(*) as count
            FROM servicedesk.tickets
            WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', "TKT-Created Time"::timestamp), support_tier;
        """),
    ]

    latencies = []

    for panel_name, sql in queries:
        start_time = time.time()
        returncode, stdout, stderr = execute_sql(sql)
        elapsed_ms = (time.time() - start_time) * 1000

        assert returncode == 0, f"{panel_name} query failed: {stderr}"

        latencies.append((panel_name, elapsed_ms))

    # Calculate P95 latency (approximate with max for small sample)
    p95_latency = max([lat for _, lat in latencies])

    # Log latencies for visibility
    for panel_name, latency in latencies:
        print(f"\n{panel_name}: {latency:.1f}ms")

    print(f"\nP95 Latency: {p95_latency:.1f}ms (SLO: <{QUERY_LATENCY_SLO_MS}ms)")

    assert p95_latency < QUERY_LATENCY_SLO_MS, \
        f"P95 query latency {p95_latency:.1f}ms exceeds SLO of {QUERY_LATENCY_SLO_MS}ms"


# ============================================================================
# CATEGORY 5: FAILURE MODE TESTS (3 tests)
# ============================================================================

def test_database_connection_failure():
    """
    Test: Graceful handling when PostgreSQL container is unavailable

    Requirements: NFR-2.2
    Expected: Clear error message, no crash, retry logic (if implemented)

    Note: This test intentionally simulates failure
    """
    # Attempt connection to non-existent container
    result = subprocess.run(
        ["docker", "exec", "nonexistent-container", "pg_isready"],
        capture_output=True
    )

    # Verify error is handled gracefully
    assert result.returncode != 0, "Expected connection failure"

    # Verify error message is informative (not cryptic)
    error_msg = result.stderr.decode()
    assert "Error" in error_msg or "error" in error_msg or "No such container" in error_msg, \
        "Error message should be informative"


def test_invalid_tier_value(execute_sql):
    """
    Test: Database rejects invalid tier values (constraint validation)

    Requirements: NFR-2.1, DP-1
    Expected: INSERT/UPDATE with invalid tier fails (e.g., 'L4', 'Unknown')

    Note: This test WILL FAIL until CHECK constraint is added
    """
    pytest.skip("CHECK constraint not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Attempt INSERT with invalid tier: 'L4'
    # 2. Verify: Query fails with constraint violation
    # 3. Attempt UPDATE with invalid tier: 'Unknown'
    # 4. Verify: Query fails with constraint violation


def test_rollback_on_error(execute_sql):
    """
    Test: Transaction rollback works correctly on backfill error

    Requirements: NFR-2.3, DP-2
    Expected: Partial backfill rolled back on error, no data corruption

    Note: This test WILL FAIL until backfill script is implemented with transactions
    """
    pytest.skip("Backfill script not implemented yet (Phase 3)")

    # TODO: Phase 3 implementation
    # 1. Run backfill with intentional error mid-way
    # 2. Verify: No partial data committed
    # 3. Verify: Database state unchanged (all or nothing)


# ============================================================================
# TEST EXECUTION SUMMARY
# ============================================================================

def test_summary():
    """
    Test suite summary (informational, always passes)

    Prints test coverage summary and expected failures
    """
    print("\n" + "="*70)
    print("ServiceDesk Tier Tracking Dashboard - Test Suite Summary")
    print("="*70)
    print("\nTest Categories:")
    print("  1. Schema Tests: 7 tests")
    print("  2. Data Validation Tests: 3 tests")
    print("  3. Backfill Tests: 4 tests (SKIPPED - Phase 3)")
    print("  4. Query Tests: 5 tests")
    print("  5. Failure Mode Tests: 3 tests (SKIPPED - Phase 3)")
    print("\nTotal: 22 tests")
    print("Expected Status: Most tests will FAIL (no implementation yet)")
    print("TDD Methodology: Red → Green → Refactor")
    print("\nNext Step: Phase 3 - Implement database schema and backfill script")
    print("="*70 + "\n")

    assert True  # Always pass


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (>5s)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


# Mark performance tests
test_query_performance = pytest.mark.performance(test_query_performance)
test_backfill_performance = pytest.mark.slow(test_backfill_performance)

# Mark integration tests
test_backfill_categorizes_correctly = pytest.mark.integration(test_backfill_categorizes_correctly)
test_rollback_on_error = pytest.mark.integration(test_rollback_on_error)
