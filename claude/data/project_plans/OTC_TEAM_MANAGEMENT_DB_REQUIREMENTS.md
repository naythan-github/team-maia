# OTC Team Management Database - Implementation Requirements

**Date:** 2026-01-07
**Status:** ✅ Data Analyst Approved - Ready for Implementation
**Assigned To:** SRE Principal Engineer Agent
**Priority:** P2 (Performance & Query Optimization)
**Estimated Effort:** 3 hours (including TDD)
**Methodology:** TDD (Test-Driven Development)

---

## Executive Summary

Implement database tables to manage engineering team membership and queue assignments in the OTC ServiceDesk database. This replaces JSON-based team configuration with relational data.

**Approved Benefits:**
- ✅ 10x faster queries (5-10ms vs 50-100ms) - Data Analyst verified
- ✅ Complex relational queries (joins, aggregations, historical analysis)
- ✅ Data integrity via foreign keys and constraints
- ✅ Audit trail for team changes over time

**Data Analyst Review Status:** ✅ **APPROVED with 4 Required Enhancements**

---

## Current State

### Existing Data Sources

**Primary:** `claude/data/user_preferences.json` (lines 14-35)
```json
{
  "analysis_preferences": {
    "otc_servicedesk": {
      "teams": {
        "engineering": {
          "members": [
            {"name": "Trevor Harte", "email": "trevor.harte@orro.group"},
            {"name": "Llewellyn Booth", "email": "llewellyn.booth@orro.group"},
            {"name": "Dion Jewell", "email": "dion.jewell@orro.group"},
            {"name": "Michael Villaflor", "email": "michael.villaflor@orro.group"},
            {"name": "Olli Ojala", "email": "olli.ojala@orro.group"},
            {"name": "Abdallah Ziadeh", "email": "abdallah.ziadeh@orro.group"},
            {"name": "Alex Olver", "email": "alex.olver@orro.group"},
            {"name": "Josh James", "email": "josh.james@orro.group"},
            {"name": "Taylor Barkle", "email": "taylor.barkle@orro.group"},
            {"name": "Steve Daalmeyer", "email": "steve.daalmeyer@orro.group"},
            {"name": "Daniel Dignadice", "email": "daniel.dignadice@orro.group"}
          ],
          "team_assignments": [
            "Cloud - Infrastructure",
            "Cloud - Security",
            "Cloud - L3 Escalation"
          ]
        }
      }
    }
  }
}
```

**Backup:** `claude/data/engineering_team_roster.json`

### Performance Baseline

| Operation | Current (JSON) | Target (Database) | Improvement |
|-----------|---------------|-------------------|-------------|
| Get team roster | 50-100ms | 5-10ms | 10x faster |
| Team tickets count | 100-200ms | 10-20ms | 10x faster |
| Queue workload | 150-300ms | 15-30ms | 10x faster |
| Historical analysis | Not possible | 20-50ms | New capability |

---

## Required Deliverables

### 1. Database Schema (Enhanced per Data Analyst Review)

#### Table 1: `servicedesk.team_members`

```sql
CREATE TABLE servicedesk.team_members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    organization VARCHAR(100) DEFAULT 'Orro',
    team VARCHAR(100) DEFAULT 'engineering',
    manager_id INTEGER REFERENCES servicedesk.team_members(id),
    active BOOLEAN DEFAULT true,
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT active_requires_no_end_date CHECK (active = false OR end_date IS NULL)
);

-- Primary Indexes
CREATE INDEX idx_team_members_active ON servicedesk.team_members(active);
CREATE INDEX idx_team_members_team ON servicedesk.team_members(team);
CREATE INDEX idx_team_members_email ON servicedesk.team_members(email);
CREATE INDEX idx_team_members_name ON servicedesk.team_members(name);
CREATE INDEX idx_team_members_manager ON servicedesk.team_members(manager_id);

-- ⭐ REQUIRED ENHANCEMENT 1: Composite index for common filter pattern
CREATE INDEX idx_team_members_team_active ON servicedesk.team_members(team, active);

-- Documentation
COMMENT ON TABLE servicedesk.team_members IS 'Engineering team roster with organizational hierarchy';
COMMENT ON COLUMN servicedesk.team_members.name IS 'Full name as it appears in TKT-Assigned To User field';
COMMENT ON COLUMN servicedesk.team_members.manager_id IS 'Self-referencing FK for organizational hierarchy';
COMMENT ON COLUMN servicedesk.team_members.active IS 'false = left team, true = current member';
```

#### Table 2: `servicedesk.team_queue_assignments`

```sql
CREATE TABLE servicedesk.team_queue_assignments (
    id SERIAL PRIMARY KEY,
    team_member_id INTEGER NOT NULL REFERENCES servicedesk.team_members(id) ON DELETE CASCADE,
    queue_name VARCHAR(255) NOT NULL,
    assigned_date DATE DEFAULT CURRENT_DATE,
    removed_date DATE,
    active BOOLEAN DEFAULT true,
    assignment_type VARCHAR(50) DEFAULT 'primary', -- 'primary', 'backup', 'rotation'
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_active_assignment UNIQUE(team_member_id, queue_name, assigned_date),
    CONSTRAINT valid_assignment_dates CHECK (removed_date IS NULL OR removed_date >= assigned_date),
    CONSTRAINT active_requires_no_removal CHECK (active = false OR removed_date IS NULL)
);

-- Primary Indexes
CREATE INDEX idx_queue_assignments_member ON servicedesk.team_queue_assignments(team_member_id);
CREATE INDEX idx_queue_assignments_queue ON servicedesk.team_queue_assignments(queue_name);
CREATE INDEX idx_queue_assignments_active ON servicedesk.team_queue_assignments(active);
CREATE INDEX idx_queue_assignments_type ON servicedesk.team_queue_assignments(assignment_type);

-- ⭐ REQUIRED ENHANCEMENT 2: Composite index for queue lookups
CREATE INDEX idx_queue_assignments_queue_active ON servicedesk.team_queue_assignments(queue_name, active);

-- Documentation
COMMENT ON TABLE servicedesk.team_queue_assignments IS 'Team member assignments to support queues over time';
COMMENT ON COLUMN servicedesk.team_queue_assignments.queue_name IS 'References TKT-Team field value';
COMMENT ON COLUMN servicedesk.team_queue_assignments.assignment_type IS 'primary (main responsibility), backup (secondary), rotation (scheduled)';
```

#### Table 3: `servicedesk.team_member_history`

```sql
CREATE TABLE servicedesk.team_member_history (
    id SERIAL PRIMARY KEY,
    team_member_id INTEGER NOT NULL REFERENCES servicedesk.team_members(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL, -- 'created', 'updated', 'deactivated', 'reactivated'
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW(),
    change_reason TEXT
);

-- Indexes
CREATE INDEX idx_history_member ON servicedesk.team_member_history(team_member_id);
CREATE INDEX idx_history_change_type ON servicedesk.team_member_history(change_type);
CREATE INDEX idx_history_changed_at ON servicedesk.team_member_history(changed_at);

-- ⭐ REQUIRED ENHANCEMENT 3: Retention policy documentation
COMMENT ON TABLE servicedesk.team_member_history IS 'Audit trail for all team roster changes - retain 7 years per compliance policy';
```

### 2. Data Migration SQL

```sql
-- Backup check: Verify JSON data exists before migration
-- Expected: 11 members, 3 queues

-- Insert 11 team members from user_preferences.json
INSERT INTO servicedesk.team_members (name, email, organization, team, active, start_date) VALUES
('Trevor Harte', 'trevor.harte@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Llewellyn Booth', 'llewellyn.booth@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Dion Jewell', 'dion.jewell@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Michael Villaflor', 'michael.villaflor@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Olli Ojala', 'olli.ojala@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Abdallah Ziadeh', 'abdallah.ziadeh@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Alex Olver', 'alex.olver@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Josh James', 'josh.james@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Taylor Barkle', 'taylor.barkle@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Steve Daalmeyer', 'steve.daalmeyer@orro.group', 'Orro', 'engineering', true, '2025-01-01'),
('Daniel Dignadice', 'daniel.dignadice@orro.group', 'Orro', 'engineering', true, '2025-01-01');

-- Insert 33 queue assignments (11 members × 3 queues)
INSERT INTO servicedesk.team_queue_assignments (team_member_id, queue_name, assigned_date, active, assignment_type)
SELECT
    tm.id,
    queue,
    '2025-01-01',
    true,
    'primary'
FROM servicedesk.team_members tm
CROSS JOIN (
    VALUES
        ('Cloud - Infrastructure'),
        ('Cloud - Security'),
        ('Cloud - L3 Escalation')
) AS queues(queue)
WHERE tm.team = 'engineering';

-- Verification queries
SELECT COUNT(*) AS team_members FROM servicedesk.team_members WHERE active = true;
-- Expected: 11

SELECT COUNT(*) AS queue_assignments FROM servicedesk.team_queue_assignments WHERE active = true;
-- Expected: 33

SELECT queue_name, COUNT(*) AS members
FROM servicedesk.team_queue_assignments
WHERE active = true
GROUP BY queue_name;
-- Expected: 11 members per queue
```

### 3. Python Helper Module

**File:** `claude/tools/integrations/otc/team_management.py`

**Required Functions:**

```python
from typing import List, Dict, Optional
import psycopg2
from datetime import datetime

def get_team_members(
    team: str = 'engineering',
    active_only: bool = True,
    fallback_to_json: bool = True
) -> List[Dict]:
    """
    Get team members from database with JSON fallback.

    Args:
        team: Team name (default: 'engineering')
        active_only: Filter to active members only (default: True)
        fallback_to_json: Fall back to JSON if DB unavailable (default: True)

    Returns:
        List of team member dicts with keys: id, name, email, organization, team, active, start_date

    Raises:
        DatabaseError: If DB unavailable and fallback_to_json=False
    """
    pass

def get_team_queues(team: str = 'engineering', active_only: bool = True) -> List[str]:
    """
    Get queue assignments for team.

    Args:
        team: Team name (default: 'engineering')
        active_only: Filter to active assignments only (default: True)

    Returns:
        List of queue names (TKT-Team values)
    """
    pass

def get_member_by_email(email: str) -> Optional[Dict]:
    """
    Get team member by email address.

    Args:
        email: Email address

    Returns:
        Team member dict or None if not found
    """
    pass

def get_member_workload(member_id: int) -> Dict:
    """
    Get workload statistics for team member.

    Args:
        member_id: Team member ID

    Returns:
        Dict with keys: name, total_tickets, open_tickets, closed_tickets, closure_rate_pct
    """
    pass

def add_team_member(
    name: str,
    email: str,
    organization: str = 'Orro',
    team: str = 'engineering',
    start_date: Optional[datetime] = None,
    notes: Optional[str] = None,
    changed_by: str = 'system'
) -> int:
    """
    Add new team member with history tracking.

    Args:
        name: Full name (as appears in TKT-Assigned To User)
        email: Email address (must be unique)
        organization: Organization name (default: 'Orro')
        team: Team name (default: 'engineering')
        start_date: Start date (default: today)
        notes: Optional notes
        changed_by: Who is making the change (default: 'system')

    Returns:
        New team member ID

    Raises:
        IntegrityError: If email already exists
    """
    pass

def update_team_member(
    member_id: int,
    changed_by: str = 'system',
    **updates
) -> bool:
    """
    Update team member with history tracking.

    Args:
        member_id: Team member ID
        changed_by: Who is making the change (default: 'system')
        **updates: Fields to update (name, email, organization, team, active, end_date, notes)

    Returns:
        True if successful

    Raises:
        ValueError: If member_id not found
    """
    pass

def assign_queue(
    member_id: int,
    queue_name: str,
    assigned_date: Optional[datetime] = None,
    assignment_type: str = 'primary',
    notes: Optional[str] = None
) -> int:
    """
    Assign team member to queue.

    Args:
        member_id: Team member ID
        queue_name: Queue name (TKT-Team value)
        assigned_date: Assignment date (default: today)
        assignment_type: 'primary', 'backup', or 'rotation' (default: 'primary')
        notes: Optional notes

    Returns:
        Assignment ID
    """
    pass

def remove_queue_assignment(assignment_id: int, removed_date: Optional[datetime] = None) -> bool:
    """
    Remove queue assignment (soft delete).

    Args:
        assignment_id: Assignment ID
        removed_date: Removal date (default: today)

    Returns:
        True if successful
    """
    pass

def export_teams_to_json() -> None:
    """
    ⭐ REQUIRED ENHANCEMENT 4: Unidirectional sync (DB → JSON)

    Export database team data to JSON for fallback freshness.
    Updates user_preferences.json with current team roster from database.

    This should be run periodically (e.g., daily cron) to keep JSON fallback fresh.
    """
    pass
```

### 4. Test Suite

**File:** `tests/integrations/test_otc_team_management.py`

**Required Test Classes (TDD - Write These First):**

```python
import pytest
import psycopg2
from datetime import datetime

class TestSchemaCreation:
    """Test Phase 1: Database schema creation."""

    def test_team_members_table_exists(self, db_connection):
        """Verify team_members table created with correct schema."""
        pass

    def test_team_queue_assignments_table_exists(self, db_connection):
        """Verify team_queue_assignments table created with correct schema."""
        pass

    def test_team_member_history_table_exists(self, db_connection):
        """Verify team_member_history table created with correct schema."""
        pass

    def test_composite_indexes_created(self, db_connection):
        """Verify composite indexes created per Data Analyst requirements."""
        # Check idx_team_members_team_active
        # Check idx_queue_assignments_queue_active
        pass

    def test_foreign_key_constraints(self, db_connection):
        """Verify foreign key constraints work correctly."""
        pass

    def test_check_constraints(self, db_connection):
        """Verify check constraints enforce business rules."""
        pass

class TestDataMigration:
    """Test Phase 2: Data migration from JSON."""

    def test_migration_inserts_11_members(self, db_connection):
        """Verify all 11 team members migrated."""
        pass

    def test_migration_inserts_33_assignments(self, db_connection):
        """Verify all 33 queue assignments migrated (11 × 3)."""
        pass

    def test_migrated_data_matches_json(self, db_connection):
        """Verify migrated data matches source JSON."""
        pass

    def test_no_duplicate_emails(self, db_connection):
        """Verify email uniqueness constraint enforced."""
        pass

class TestTeamManagementFunctions:
    """Test Phase 3: Python helper functions."""

    def test_get_team_members(self, db_connection):
        """Test get_team_members returns correct roster."""
        pass

    def test_get_team_members_active_filter(self, db_connection):
        """Test active_only parameter filters correctly."""
        pass

    def test_get_team_members_fallback_to_json(self, db_connection):
        """Test graceful fallback to JSON when DB unavailable."""
        pass

    def test_get_team_queues(self, db_connection):
        """Test get_team_queues returns correct queues."""
        pass

    def test_get_member_by_email(self, db_connection):
        """Test email lookup."""
        pass

    def test_get_member_workload(self, db_connection):
        """Test workload statistics calculation."""
        pass

    def test_add_team_member(self, db_connection):
        """Test adding new team member creates history entry."""
        pass

    def test_update_team_member_with_history(self, db_connection):
        """Test updating member creates history entry."""
        pass

    def test_assign_queue(self, db_connection):
        """Test queue assignment."""
        pass

    def test_remove_queue_assignment_soft_delete(self, db_connection):
        """Test soft delete of queue assignment."""
        pass

    def test_export_teams_to_json(self, db_connection):
        """Test DB → JSON export for fallback freshness."""
        pass

class TestQueryPerformance:
    """Test Phase 4: Performance benchmarks."""

    def test_team_roster_query_performance(self, db_connection):
        """Benchmark team roster query (target: <10ms)."""
        pass

    def test_team_tickets_join_performance(self, db_connection):
        """Benchmark team tickets join query (target: <20ms)."""
        pass

    def test_composite_index_usage(self, db_connection):
        """Verify composite indexes used in query plans."""
        pass

    def test_index_only_scan_possible(self, db_connection):
        """Verify index-only scans for common queries."""
        pass

class TestIntegration:
    """Test Phase 5: Integration with existing system."""

    def test_team_tickets_join(self, db_connection):
        """Test joining team data with tickets table."""
        pass

    def test_queue_workload_aggregation(self, db_connection):
        """Test queue workload aggregation query."""
        pass

    def test_individual_performance_query(self, db_connection):
        """Test individual team member performance query."""
        pass

    def test_historical_team_composition(self, db_connection):
        """Test historical team composition query."""
        pass

class TestHistoryTracking:
    """Test Phase 6: Audit trail functionality."""

    def test_add_member_creates_history(self, db_connection):
        """Verify adding member creates history entry."""
        pass

    def test_update_member_creates_history(self, db_connection):
        """Verify updating member creates history entry."""
        pass

    def test_deactivate_member_creates_history(self, db_connection):
        """Verify deactivating member creates history entry."""
        pass

    def test_history_retention_policy(self, db_connection):
        """Verify 7-year retention policy documented."""
        pass
```

### 5. User Preferences Update

**File:** `claude/data/user_preferences.json`

**Required Change:**

```json
{
  "analysis_preferences": {
    "otc_servicedesk": {
      "default_start_date": "2025-12-28",
      "team_source": "database",
      "team_source_fallback": "json",
      "teams": {
        "engineering": {
          "db_table": "servicedesk.team_members",
          "db_query": "SELECT name FROM servicedesk.team_members WHERE team = 'engineering' AND active = true",
          "members": [...],  // Keep existing as fallback
          "team_assignments": [...]  // Keep existing as fallback
        }
      }
    }
  }
}
```

---

## TDD Implementation Workflow

### Phase Sequence (MUST Follow TDD)

**Phase 1: Schema Tests (RED)**
1. Write tests for schema creation (TestSchemaCreation)
2. Run tests - expect failures (tables don't exist yet)
3. Create schema DDL
4. Run tests - expect passes ✅

**Phase 2: Migration Tests (RED → GREEN)**
1. Write tests for data migration (TestDataMigration)
2. Run tests - expect failures (no data yet)
3. Execute migration SQL
4. Run tests - expect passes ✅

**Phase 3: Function Tests (RED → GREEN → REFACTOR)**
1. Write tests for helper functions (TestTeamManagementFunctions)
2. Run tests - expect failures (functions not implemented)
3. Implement helper functions
4. Run tests - expect passes ✅
5. Refactor for code quality

**Phase 4: Performance Tests (GREEN → VERIFY)**
1. Write benchmark tests (TestQueryPerformance)
2. Run tests - measure actual performance
3. Verify <10ms target met ✅

**Phase 5: Integration Tests (GREEN → VERIFY)**
1. Write integration tests (TestIntegration)
2. Run tests - verify joins work
3. All tests passing ✅

**Phase 6: History Tests (GREEN → VERIFY)**
1. Write history tests (TestHistoryTracking)
2. Run tests - verify audit trail
3. All tests passing ✅

### Test Execution Command

```bash
# Run all team management tests
pytest tests/integrations/test_otc_team_management.py -v --tb=short

# Expected: All tests passing (target: 35+ tests)
```

---

## Acceptance Criteria

### Functional Requirements ✅

- [ ] All 3 tables created with correct schema
- [ ] All 6 composite indexes created (including 2 new ones from Data Analyst)
- [ ] All 11 team members migrated from JSON
- [ ] All 33 queue assignments migrated (11 × 3)
- [ ] All helper functions implemented and tested
- [ ] JSON fallback works when DB unavailable
- [ ] Export DB → JSON function implemented
- [ ] History tracking creates audit entries

### Performance Requirements ✅

- [ ] Team roster query: <10ms (10x improvement verified)
- [ ] Team tickets join: <20ms (10x improvement verified)
- [ ] Composite indexes used in query plans
- [ ] Index-only scans possible for common queries

### Test Requirements ✅

- [ ] All 35+ tests passing (100% pass rate)
- [ ] TDD methodology followed (tests first)
- [ ] No regressions in existing OTC tests
- [ ] Performance benchmarks documented

### Integration Requirements ✅

- [ ] user_preferences.json updated with team_source="database"
- [ ] JSON fallback preserved for reliability
- [ ] Existing analytics queries compatible
- [ ] Documentation updated

---

## Rollback Plan

### Rollback SQL

```sql
-- Execute in reverse order to handle dependencies
DROP TABLE IF EXISTS servicedesk.team_member_history CASCADE;
DROP TABLE IF EXISTS servicedesk.team_queue_assignments CASCADE;
DROP TABLE IF EXISTS servicedesk.team_members CASCADE;
```

### Rollback User Preferences

```json
{
  "team_source": "json"  // Revert to JSON-only
}
```

### Rollback Criteria

Trigger rollback if:
- Migration errors (data loss detected)
- Performance worse than JSON baseline
- >10% test failure rate
- Critical integration bugs

---

## Data Analyst Approval Summary

**Review Date:** 2026-01-07
**Reviewer:** Data Analyst Agent v2.3
**Verdict:** ✅ **APPROVED with 4 Required Enhancements**

### Required Enhancements (Integrated Above)

1. ✅ **Composite Index:** `idx_team_members_team_active` (2-3x faster roster queries)
2. ✅ **Composite Index:** `idx_queue_assignments_queue_active` (faster queue lookups)
3. ✅ **Retention Policy:** 7-year history retention documented in table comments
4. ✅ **Sync Strategy:** Unidirectional DB → JSON via `export_teams_to_json()` function

### Data Analyst Performance Validation

- ✅ 10x improvement realistic (verified via B-tree index analysis)
- ✅ Size estimates conservative (<1MB for 5 years)
- ✅ Schema design normalized (3NF compliant)
- ✅ Risk assessment: LOW (clear rollback, graceful fallback)

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `OTC_TEAM_MANAGEMENT_DB.md` | Original implementation plan |
| `user_preferences.json` | Current JSON team data (lines 14-35) |
| `engineering_team_roster.json` | Backup JSON team data |
| `tdd_development_protocol.md` | TDD methodology (opened by user) |
| `SESSION_CHECKPOINT_OTC_ETL_PHASE3.md` | Previous OTC ETL work reference |

---

## Implementation Checklist

### Pre-Implementation
- [ ] Read this requirements document completely
- [ ] Review TDD protocol (`tdd_development_protocol.md`)
- [ ] Backup JSON files (`user_preferences.json`, `engineering_team_roster.json`)
- [ ] Verify database connection to servicedesk schema

### Phase 1: Schema Creation (45 min)
- [ ] Write schema creation tests (TestSchemaCreation)
- [ ] Run tests - verify failures (RED)
- [ ] Create `team_members` table with all indexes
- [ ] Create `team_queue_assignments` table with all indexes
- [ ] Create `team_member_history` table with all indexes
- [ ] Add table/column comments
- [ ] Run tests - verify passes (GREEN) ✅

### Phase 2: Data Migration (30 min)
- [ ] Write migration tests (TestDataMigration)
- [ ] Run tests - verify failures (RED)
- [ ] Execute migration SQL
- [ ] Verify 11 members inserted
- [ ] Verify 33 assignments inserted (11 × 3)
- [ ] Run tests - verify passes (GREEN) ✅

### Phase 3: Helper Functions (60 min)
- [ ] Write function tests (TestTeamManagementFunctions)
- [ ] Run tests - verify failures (RED)
- [ ] Implement `get_team_members()` with JSON fallback
- [ ] Implement `get_team_queues()`
- [ ] Implement `get_member_by_email()`
- [ ] Implement `get_member_workload()`
- [ ] Implement `add_team_member()` with history
- [ ] Implement `update_team_member()` with history
- [ ] Implement `assign_queue()`
- [ ] Implement `remove_queue_assignment()`
- [ ] Implement `export_teams_to_json()` (DB → JSON sync)
- [ ] Run tests - verify passes (GREEN) ✅
- [ ] Refactor for code quality (REFACTOR)

### Phase 4: Performance Benchmarks (20 min)
- [ ] Write performance tests (TestQueryPerformance)
- [ ] Run benchmarks - measure actual times
- [ ] Verify <10ms roster queries ✅
- [ ] Verify <20ms join queries ✅
- [ ] Verify composite index usage
- [ ] Document benchmark results

### Phase 5: Integration (20 min)
- [ ] Write integration tests (TestIntegration)
- [ ] Test team + tickets joins
- [ ] Test queue workload queries
- [ ] Test individual performance queries
- [ ] Test historical composition queries
- [ ] Run tests - verify passes ✅

### Phase 6: History Tracking (15 min)
- [ ] Write history tests (TestHistoryTracking)
- [ ] Test add member history creation
- [ ] Test update member history creation
- [ ] Test deactivate member history creation
- [ ] Run tests - verify passes ✅

### Phase 7: Finalization (20 min)
- [ ] Update `user_preferences.json` (team_source="database")
- [ ] Run full test suite (35+ tests)
- [ ] Verify zero regressions in existing OTC tests
- [ ] Create session checkpoint document
- [ ] Git commit with detailed message

### Total: ~3.5 hours

---

## Success Criteria Summary

**MUST ACHIEVE:**
1. ✅ All 35+ tests passing (100% pass rate)
2. ✅ Performance: <10ms roster queries (10x improvement)
3. ✅ Performance: <20ms join queries (10x improvement)
4. ✅ All 11 members + 33 assignments migrated
5. ✅ JSON fallback functional
6. ✅ History tracking operational
7. ✅ Zero regressions in existing tests

**NICE TO HAVE:**
- Performance benchmarks exceed targets (>10x improvement)
- Query plans show index-only scans
- Code coverage >95%

---

## Handoff Instructions for SRE Agent

### Context to Load

1. **This Requirements Document** (you are reading it)
2. **TDD Protocol** (`claude/context/core/tdd_development_protocol.md`)
3. **Database Reference** (`claude/context/knowledge/servicedesk/otc_database_reference.md`)
4. **Previous OTC Work** (`SESSION_CHECKPOINT_OTC_ETL_PHASE3.md` - for context)

### Execution Approach

1. **Follow TDD Strictly**: Tests first, implementation second
2. **Autonomous Execution**: No permission requests for pip, edits, git, tests
3. **Fix Until Working**: No half-measures, complete implementation
4. **Document Checkpoints**: Create checkpoint after each phase completion
5. **Performance Validation**: Benchmark after implementation, verify 10x improvement

### Expected Session Output

1. **3 Database Tables** (team_members, team_queue_assignments, team_member_history)
2. **10 Indexes Total** (6 original + 4 enhancements including 2 composite)
3. **Python Module** (`claude/tools/integrations/otc/team_management.py`)
4. **Test Suite** (`tests/integrations/test_otc_team_management.py` - 35+ tests)
5. **Updated Preferences** (`user_preferences.json` with team_source="database")
6. **Checkpoint Document** (detailed session summary)
7. **Git Commit** (all changes committed)

---

**Requirements Status:** ✅ **COMPLETE - Ready for SRE Implementation**
**Data Analyst Approval:** ✅ **APPROVED**
**Next Action:** Hand off to SRE Principal Engineer Agent

