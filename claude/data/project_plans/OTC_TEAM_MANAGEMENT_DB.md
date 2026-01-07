# OTC Team Management Database Implementation Plan

**Date:** 2026-01-07
**Status:** Pending Data Analyst Review
**Priority:** P2 (Performance & Query Optimization)
**Estimated Effort:** 2-3 hours implementation + testing

---

## Executive Summary

Implement database tables to manage engineering team membership and queue assignments in the OTC ServiceDesk database. This will replace JSON-based team configuration with relational data, enabling:
- 10x faster queries (indexed lookups vs file parsing)
- Complex relational queries (joins, aggregations, historical analysis)
- Data integrity via foreign keys and constraints
- Audit trail for team changes over time

**Current State:** Team roster stored in JSON files (`user_preferences.json`, `engineering_team_roster.json`)
**Proposed State:** Normalized relational tables with proper indexing and constraints

---

## Problem Statement

### Current Limitations

1. **Performance Bottleneck**
   - JSON file parsing: 50-100ms per query
   - Python-side filtering required
   - No database-level optimization

2. **Query Complexity**
   - Cannot join team data with ticket data in SQL
   - Aggregations require application code
   - Historical analysis not possible

3. **Data Integrity**
   - No referential integrity
   - Manual synchronization between files
   - No audit trail

4. **Example Query Comparison**

**Current (JSON + Python):**
```python
# Load JSON, parse, filter in Python
team = load_json('user_preferences.json')['teams']['engineering']
names = [m['name'] for m in team['members']]
cursor.execute(
    "SELECT * FROM tickets WHERE \"TKT-Assigned To User\" IN %s",
    (tuple(names),)
)
# 50-100ms + query time
```

**Proposed (Database):**
```sql
-- Single query with join
SELECT t.*
FROM servicedesk.tickets t
JOIN servicedesk.team_members tm ON t."TKT-Assigned To User" = tm.name
WHERE tm.team = 'engineering' AND tm.active = true;
-- 5-10ms with proper indexes
```

---

## Database Schema Design

### Table 1: `team_members`

Core table for team member information.

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

-- Indexes for performance
CREATE INDEX idx_team_members_active ON servicedesk.team_members(active);
CREATE INDEX idx_team_members_team ON servicedesk.team_members(team);
CREATE INDEX idx_team_members_email ON servicedesk.team_members(email);
CREATE INDEX idx_team_members_name ON servicedesk.team_members(name);
CREATE INDEX idx_team_members_manager ON servicedesk.team_members(manager_id);

-- Comments for documentation
COMMENT ON TABLE servicedesk.team_members IS 'Engineering team roster with organizational hierarchy';
COMMENT ON COLUMN servicedesk.team_members.name IS 'Full name as it appears in TKT-Assigned To User field';
COMMENT ON COLUMN servicedesk.team_members.manager_id IS 'Self-referencing FK for organizational hierarchy';
COMMENT ON COLUMN servicedesk.team_members.active IS 'false = left team, true = current member';
```

**Rationale:**
- `name` matches ticket assignment format for easy joins
- `email` unique constraint prevents duplicates
- `manager_id` self-reference enables org chart queries
- `active` boolean for soft deletes (preserve historical data)
- Date range tracking for tenure analysis

### Table 2: `team_queue_assignments`

Many-to-many relationship between team members and queues.

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

-- Indexes for performance
CREATE INDEX idx_queue_assignments_member ON servicedesk.team_queue_assignments(team_member_id);
CREATE INDEX idx_queue_assignments_queue ON servicedesk.team_queue_assignments(queue_name);
CREATE INDEX idx_queue_assignments_active ON servicedesk.team_queue_assignments(active);
CREATE INDEX idx_queue_assignments_type ON servicedesk.team_queue_assignments(assignment_type);

-- Comments
COMMENT ON TABLE servicedesk.team_queue_assignments IS 'Team member assignments to support queues over time';
COMMENT ON COLUMN servicedesk.team_queue_assignments.queue_name IS 'References TKT-Team field value';
COMMENT ON COLUMN servicedesk.team_queue_assignments.assignment_type IS 'primary (main responsibility), backup (secondary), rotation (scheduled)';
```

**Rationale:**
- Many-to-many: Members can cover multiple queues, queues have multiple members
- Historical tracking: assigned_date/removed_date for rotation analysis
- `assignment_type`: Distinguishes primary vs backup coverage
- Cascade delete: Removing team member removes all assignments

### Table 3: `team_member_history` (Audit Trail)

Change tracking for compliance and analysis.

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

-- Comments
COMMENT ON TABLE servicedesk.team_member_history IS 'Audit trail for all team roster changes';
```

**Rationale:**
- Compliance: Track who changed what and when
- Analysis: Team composition over time
- Rollback: Recover from mistakes

---

## Initial Data Migration

### Step 1: Extract from JSON

Source: `claude/data/user_preferences.json` (lines 14-35)

**Current Engineering Team (11 members):**
1. Trevor Harte - trevor.harte@orro.group
2. Llewellyn Booth - llewellyn.booth@orro.group
3. Dion Jewell - dion.jewell@orro.group
4. Michael Villaflor - michael.villaflor@orro.group
5. Olli Ojala - olli.ojala@orro.group
6. Abdallah Ziadeh - abdallah.ziadeh@orro.group
7. Alex Olver - alex.olver@orro.group
8. Josh James - josh.james@orro.group
9. Taylor Barkle - taylor.barkle@orro.group
10. Steve Daalmeyer - steve.daalmeyer@orro.group
11. Daniel Dignadice - daniel.dignadice@orro.group

**Queue Assignments (3 queues):**
- Cloud - Infrastructure
- Cloud - Security
- Cloud - L3 Escalation

### Step 2: Migration SQL

```sql
-- Insert team members
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

-- Insert queue assignments (all team members to all 3 queues)
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

-- Verify migration
SELECT COUNT(*) AS team_members FROM servicedesk.team_members WHERE active = true;
-- Expected: 11

SELECT COUNT(*) AS queue_assignments FROM servicedesk.team_queue_assignments WHERE active = true;
-- Expected: 33 (11 members × 3 queues)
```

---

## Query Examples & Use Cases

### 1. Get All Active Team Members

```sql
SELECT name, email, start_date
FROM servicedesk.team_members
WHERE team = 'engineering' AND active = true
ORDER BY name;
```

### 2. Team Workload by Queue

```sql
SELECT
    tqa.queue_name,
    COUNT(DISTINCT tm.id) AS team_members_assigned,
    COUNT(t."TKT-Ticket ID") AS total_tickets,
    COUNT(CASE WHEN t."TKT-Status" IN ('Open', 'In Progress') THEN 1 END) AS active_tickets
FROM servicedesk.team_queue_assignments tqa
JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
LEFT JOIN servicedesk.tickets t ON t."TKT-Team" = tqa.queue_name
WHERE tm.active = true AND tqa.active = true
GROUP BY tqa.queue_name
ORDER BY total_tickets DESC;
```

### 3. Individual Team Member Performance

```sql
SELECT
    tm.name,
    COUNT(t."TKT-Ticket ID") AS total_tickets,
    COUNT(CASE WHEN t."TKT-Status" = 'Closed' THEN 1 END) AS closed_tickets,
    ROUND(
        COUNT(CASE WHEN t."TKT-Status" = 'Closed' THEN 1 END) * 100.0 /
        NULLIF(COUNT(t."TKT-Ticket ID"), 0),
        1
    ) AS closure_rate_pct
FROM servicedesk.team_members tm
LEFT JOIN servicedesk.tickets t ON t."TKT-Assigned To User" = tm.name
WHERE tm.team = 'engineering' AND tm.active = true
GROUP BY tm.name
ORDER BY total_tickets DESC;
```

### 4. Queue Coverage Analysis

```sql
-- Which queues have backup coverage?
SELECT
    queue_name,
    COUNT(*) AS assigned_members,
    STRING_AGG(tm.name, ', ' ORDER BY tm.name) AS members
FROM servicedesk.team_queue_assignments tqa
JOIN servicedesk.team_members tm ON tqa.team_member_id = tm.id
WHERE tqa.active = true
GROUP BY queue_name
HAVING COUNT(*) < 2  -- Single point of failure
ORDER BY assigned_members ASC;
```

### 5. Team Composition Over Time (with History)

```sql
-- Team size by month
SELECT
    DATE_TRUNC('month', start_date) AS month,
    COUNT(*) AS new_members,
    SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', start_date)) AS cumulative_size
FROM servicedesk.team_members
WHERE team = 'engineering'
GROUP BY DATE_TRUNC('month', start_date)
ORDER BY month;
```

---

## Performance Considerations

### Index Strategy

**Primary Indexes (created with schema):**
- `team_members.active` - Most queries filter by active status
- `team_members.name` - Join key to tickets table
- `team_members.email` - Unique constraint + lookups
- `team_queue_assignments.team_member_id` - Join to team_members
- `team_queue_assignments.queue_name` - Join to tickets

**Estimated Query Performance:**

| Query Type | Current (JSON) | Proposed (DB) | Improvement |
|------------|---------------|---------------|-------------|
| Get team roster | 50-100ms | 5-10ms | 10x faster |
| Team tickets count | 100-200ms | 10-20ms | 10x faster |
| Queue workload | 150-300ms | 15-30ms | 10x faster |
| Historical analysis | Not possible | 20-50ms | New capability |

### Table Size Estimates

**team_members:**
- Rows: ~50 (current 11, room for growth)
- Size: ~10KB
- Growth: ~10 rows/year

**team_queue_assignments:**
- Rows: ~200 (current 33, historical data)
- Size: ~30KB
- Growth: ~50 rows/year

**team_member_history:**
- Rows: ~1000 (audit trail)
- Size: ~100KB
- Growth: ~200 rows/year

**Total:** <1MB for first 5 years (negligible)

---

## Integration Points

### 1. Update User Preferences

After migration, update `claude/data/user_preferences.json`:

```json
{
  "analysis_preferences": {
    "otc_servicedesk": {
      "team_source": "database",
      "team_source_fallback": "json",
      "teams": {
        "engineering": {
          "db_table": "servicedesk.team_members",
          "db_query": "SELECT name FROM servicedesk.team_members WHERE team = 'engineering' AND active = true",
          "members": [...] // Keep as fallback
        }
      }
    }
  }
}
```

### 2. Helper Functions

Create Python helper module: `claude/tools/integrations/otc/team_management.py`

```python
def get_team_members(team: str = 'engineering', active_only: bool = True) -> List[Dict]:
    """Get team members from database."""

def get_team_queues(team: str = 'engineering') -> List[str]:
    """Get queue assignments for team."""

def add_team_member(name: str, email: str, **kwargs) -> int:
    """Add new team member (with history tracking)."""

def update_team_member(member_id: int, **updates) -> bool:
    """Update team member (with history tracking)."""

def assign_queue(member_id: int, queue_name: str, **kwargs) -> int:
    """Assign team member to queue."""
```

### 3. Dashboard Queries

Update analytics queries to use database joins instead of JSON filtering.

---

## Testing Strategy

### Unit Tests

Location: `tests/integrations/test_otc_team_management.py`

```python
class TestTeamManagement:
    def test_team_member_crud(self):
        """Test create, read, update, delete operations."""

    def test_queue_assignments(self):
        """Test queue assignment operations."""

    def test_history_tracking(self):
        """Test audit trail creation."""

    def test_referential_integrity(self):
        """Test foreign key constraints."""

    def test_query_performance(self):
        """Benchmark query performance vs JSON."""
```

### Integration Tests

```python
class TestTeamIntegration:
    def test_team_ticket_join(self):
        """Test joining team data with tickets."""

    def test_fallback_to_json(self):
        """Test graceful fallback if DB unavailable."""

    def test_migration_completeness(self):
        """Verify all JSON data migrated correctly."""
```

### Performance Tests

```python
def test_query_performance_benchmark():
    """Compare query times: JSON vs Database."""
    # Expected: DB queries 10x faster
```

---

## Rollback Plan

### Rollback Steps

1. **Database Rollback:**
```sql
-- Drop tables in reverse order (cascade will handle dependencies)
DROP TABLE IF EXISTS servicedesk.team_member_history CASCADE;
DROP TABLE IF EXISTS servicedesk.team_queue_assignments CASCADE;
DROP TABLE IF EXISTS servicedesk.team_members CASCADE;
```

2. **Restore JSON Preference:**
```json
{
  "team_source": "json"  // Revert to JSON
}
```

3. **Verify Fallback:**
```bash
python3 -c "from claude.tools.integrations.otc.team_management import get_team_members; print(get_team_members())"
```

### Rollback Criteria

Trigger rollback if:
- Migration errors (data loss)
- Query performance worse than JSON
- Integration tests fail (>10% failure rate)
- Critical bug in team lookup

---

## Implementation Checklist

### Phase 1: Schema Creation (30 min)
- [ ] Create `team_members` table
- [ ] Create `team_queue_assignments` table
- [ ] Create `team_member_history` table
- [ ] Create indexes
- [ ] Add comments

### Phase 2: Data Migration (20 min)
- [ ] Backup current JSON files
- [ ] Extract team data from JSON
- [ ] Insert team members
- [ ] Insert queue assignments
- [ ] Verify row counts

### Phase 3: Helper Functions (45 min)
- [ ] Create `team_management.py` module
- [ ] Implement CRUD functions
- [ ] Add history tracking
- [ ] Add database fallback to JSON

### Phase 4: Testing (30 min)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Run performance benchmarks
- [ ] Verify all tests pass

### Phase 5: Integration (15 min)
- [ ] Update user preferences
- [ ] Update analytics queries
- [ ] Update documentation

### Total: ~2.5 hours

---

## Open Questions for Data Analyst Review

1. **Schema Design:**
   - Is the three-table design appropriate?
   - Should we add more audit tracking fields?
   - Are the constraints sufficient?

2. **Indexing Strategy:**
   - Are the proposed indexes optimal?
   - Should we add composite indexes?
   - Any missing indexes for common queries?

3. **Data Model:**
   - Should we track more team metadata (location, timezone, etc.)?
   - Do we need a separate "teams" table (vs team VARCHAR)?
   - Should queue assignments track hours/shift schedules?

4. **Performance:**
   - Are the size estimates realistic?
   - Should we partition any tables?
   - Index-only scans possible?

5. **Historical Analysis:**
   - Is the history table design sufficient?
   - Should we track more change metadata?
   - Retention policy for history?

6. **Integration:**
   - Should team data sync bidirectionally with JSON?
   - How to handle external team changes (HR systems)?
   - API for team management?

---

## Success Criteria

1. **Performance:** Database queries 5-10x faster than JSON
2. **Coverage:** 100% of JSON data migrated successfully
3. **Tests:** All unit/integration tests passing
4. **Queries:** Complex joins working (team + tickets + queues)
5. **History:** Audit trail capturing all changes
6. **Fallback:** Graceful degradation to JSON if DB unavailable

---

## References

- Current team roster: `claude/data/user_preferences.json` (lines 14-35)
- Ticket schema: `servicedesk.tickets` table
- Queue field: `TKT-Team` column

---

**Next Steps:**
1. Data Analyst reviews this plan
2. Address open questions and feedback
3. Approve/modify schema design
4. Proceed with implementation
