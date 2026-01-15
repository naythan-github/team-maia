# Maia Project Registry System
## Production-Grade Project Backlog Management

**Project ID**: PROJ-REG-001
**Created**: 2025-10-27
**Status**: Planning → Ready for Implementation
**Owner**: Naythan Dawe
**Agent**: SRE Principal Engineer (primary)
**Session Persistence**: Enabled (SRE agent auto-loads for this project)

---

## Executive Summary

**Problem**: 22+ project plan files scattered across `claude/data/` with no centralized tracking, causing operational inefficiency and project discovery overhead.

**Solution**: Production-grade SQLite project registry with CLI tooling, automatic markdown export, and reliability guarantees.

**Impact**:
- 🎯 100% project visibility (single source of truth)
- ⚡ <100ms query performance (fast project discovery)
- 🔒 ACID guarantees (zero data loss)
- 📊 Auto-generated backlog reports (always current)
- 💾 Disaster recovery ready (daily backups)

**Timeline**: 3-4 hours implementation
**Maintenance**: <15 min/week (automated backups + exports)

---

## Problem Statement

### Current State
- **22+ project plan files** in `claude/data/` (scattered, no index)
- **"UP NEXT" section** in `capability_index.md` (manual, only 2 projects)
- **No dependency tracking** (risk of starting blocked projects)
- **No priority visibility** (suboptimal resource allocation)
- **No completion metrics** (unknown velocity/ROI)

### Operational Cost
- **Project discovery**: 5-10 min per lookup (grep/find across files)
- **Status checks**: 30 min/week (manual file reviews)
- **Backlog planning**: 1-2 hours/month (manual consolidation)
- **Total annual waste**: ~40 hours/year

### Risks
- ⚠️ **Medium Risk**: Inefficiency and toil (not production-critical)
- ⚠️ **Missed opportunities**: High-value projects buried in backlog
- ⚠️ **Duplicate work**: No visibility into existing research
- ⚠️ **Blocked starts**: Dependencies not tracked

---

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                 Maia Project Registry System                    │
│                     (Local-First, ACID-Safe)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Data Layer (SQLite 3.x)                                     │
│  ├─ project_registry.db (Single Source of Truth)               │
│  │  ├─ WAL mode enabled (crash recovery)                       │
│  │  ├─ ACID transactions (data integrity)                      │
│  │  └─ Foreign key constraints (referential integrity)         │
│  │                                                              │
│  ├─ Tables:                                                     │
│  │  ├─ projects (main registry)                                │
│  │  ├─ project_updates (audit log)                             │
│  │  ├─ deliverables (outputs tracking)                         │
│  │  └─ dependencies (project relationships)                    │
│  │                                                              │
│  └─ Backup Strategy:                                            │
│     ├─ Daily: OneDrive sync (disaster recovery)                │
│     └─ On-demand: Manual export to JSON                        │
│                                                                 │
│  🔧 Access Layer (CLI Tool)                                     │
│  ├─ project_registry.py (Python 3.x)                           │
│  │  ├─ CRUD operations (create, read, update, delete)          │
│  │  ├─ Atomic writes (transaction safety)                      │
│  │  ├─ Input validation (prevent corrupt data)                 │
│  │  └─ Error handling (graceful degradation)                   │
│  │                                                              │
│  ├─ Commands:                                                   │
│  │  ├─ add (create new project)                                │
│  │  ├─ list (filter by status/priority/category)               │
│  │  ├─ update (change status/priority)                         │
│  │  ├─ start (begin project, set started_date)                 │
│  │  ├─ complete (finish project, calculate metrics)            │
│  │  ├─ backlog (prioritized view)                              │
│  │  ├─ stats (summary metrics)                                 │
│  │  └─ export (generate markdown/JSON)                         │
│  │                                                              │
│  └─ Performance:                                                │
│     ├─ Query latency: <100ms P95 (SLO)                         │
│     └─ Write latency: <50ms P95                                │
│                                                                 │
│  📄 Export Layer (Human-Readable Views)                         │
│  ├─ MAIA_PROJECT_BACKLOG.md (auto-generated)                   │
│  │  ├─ Regenerated on every update (always fresh)              │
│  │  ├─ Git-tracked (version history)                           │
│  │  └─ Organized by priority (critical → low)                  │
│  │                                                              │
│  └─ project_registry_export.json (machine-readable)            │
│     └─ Full database dump for external tools                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `projects` (Primary Registry)

```sql
CREATE TABLE projects (
    -- Identity
    id TEXT PRIMARY KEY,                    -- e.g., "REPO-GOV-001"
    name TEXT NOT NULL,                     -- "Git Repository Governance"

    -- Status & Priority
    status TEXT NOT NULL                    -- planned/active/blocked/completed/archived
        CHECK(status IN ('planned', 'active', 'blocked', 'completed', 'archived')),
    priority TEXT NOT NULL DEFAULT 'medium' -- critical/high/medium/low
        CHECK(priority IN ('critical', 'high', 'medium', 'low')),

    -- Effort & Impact
    effort_hours INTEGER,                   -- estimated hours (null if unknown)
    actual_hours INTEGER,                   -- tracked hours (null until completed)
    impact TEXT                             -- high/medium/low
        CHECK(impact IN ('high', 'medium', 'low')),

    -- Categorization
    category TEXT,                          -- SRE/DevOps/Security/ServiceDesk/Agent/etc.
    tags TEXT,                              -- JSON array: ["performance", "monitoring"]

    -- Timeline
    created_date TEXT NOT NULL,             -- ISO 8601: "2025-10-27T10:30:00Z"
    started_date TEXT,                      -- when status → active
    completed_date TEXT,                    -- when status → completed

    -- References
    project_plan_path TEXT,                 -- path to detailed plan (md file)
    confluence_url TEXT,                    -- optional Confluence page
    github_issue_url TEXT,                  -- optional GitHub issue

    -- Notes
    description TEXT,                       -- brief summary
    notes TEXT,                             -- detailed notes, constraints, context

    -- Metadata
    created_by TEXT DEFAULT 'maia',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_priority ON projects(priority);
CREATE INDEX idx_projects_category ON projects(category);
CREATE INDEX idx_projects_created ON projects(created_date);
```

### Table: `project_updates` (Audit Log)

```sql
CREATE TABLE project_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Change tracking
    field_changed TEXT,                     -- "status", "priority", etc.
    old_value TEXT,
    new_value TEXT,

    -- Context
    change_reason TEXT,                     -- why was this changed?
    updated_by TEXT DEFAULT 'maia',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Index for audit queries
CREATE INDEX idx_updates_project ON project_updates(project_id, timestamp DESC);
```

### Table: `deliverables` (Project Outputs)

```sql
CREATE TABLE deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,

    -- Deliverable info
    name TEXT NOT NULL,                     -- "validate_core_schema.py"
    type TEXT NOT NULL                      -- tool/agent/documentation/infrastructure
        CHECK(type IN ('tool', 'agent', 'documentation', 'infrastructure', 'database', 'workflow')),
    status TEXT NOT NULL DEFAULT 'planned'  -- planned/in_progress/completed
        CHECK(status IN ('planned', 'in_progress', 'completed')),

    -- References
    file_path TEXT,                         -- actual location if created
    description TEXT,                       -- brief description

    -- Timeline
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_date TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Index for deliverable queries
CREATE INDEX idx_deliverables_project ON deliverables(project_id);
CREATE INDEX idx_deliverables_status ON deliverables(status);
```

### Table: `dependencies` (Project Relationships)

```sql
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relationship
    project_id TEXT NOT NULL,               -- dependent project
    depends_on_project_id TEXT NOT NULL,    -- dependency (must complete first)

    -- Metadata
    dependency_type TEXT DEFAULT 'blocks'   -- blocks/optional/enhances
        CHECK(dependency_type IN ('blocks', 'optional', 'enhances')),
    notes TEXT,                             -- why is this a dependency?

    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- Prevent circular dependencies (enforced at application level)
    UNIQUE(project_id, depends_on_project_id)
);

-- Indexes for dependency graph queries
CREATE INDEX idx_deps_project ON dependencies(project_id);
CREATE INDEX idx_deps_depends_on ON dependencies(depends_on_project_id);
```

---

## CLI Tool Specification

### File: `claude/tools/project_management/project_registry.py`

**Commands**:

#### 1. `add` - Create New Project

```bash
python3 claude/tools/project_management/project_registry.py add \
    --id REPO-GOV-001 \
    --name "Git Repository Governance" \
    --status planned \
    --priority high \
    --effort 40 \
    --impact high \
    --category "DevOps/SRE" \
    --plan claude/data/GIT_REPOSITORY_GOVERNANCE_PROJECT.md \
    --description "Production-grade multi-user repository protection"
```

**Validation**:
- ✅ ID format: `[A-Z0-9-]+` (uppercase, numbers, hyphens only)
- ✅ ID uniqueness (prevent duplicates)
- ✅ Plan path exists (if provided)
- ✅ Status/priority/impact valid enum values

---

#### 2. `list` - Query Projects

```bash
# List all planned projects
python3 claude/tools/project_management/project_registry.py list --status planned

# List high-priority projects
python3 claude/tools/project_management/project_registry.py list --priority high

# List by category
python3 claude/tools/project_management/project_registry.py list --category SRE

# List active projects
python3 claude/tools/project_management/project_registry.py list --status active

# Filter by multiple criteria
python3 claude/tools/project_management/project_registry.py list \
    --status planned \
    --priority high \
    --category DevOps
```

**Output Format**:
```
ID              Name                                Status    Priority  Effort  Impact
─────────────────────────────────────────────────────────────────────────────────────
REPO-GOV-001    Git Repository Governance           planned   high      40h     high
PHASE-126       Quality Improvement Measurement     planned   high      12h     medium
SEC-AUT-002     Security Automation Enhancement     planned   critical  20h     high
```

---

#### 3. `show` - Project Details

```bash
python3 claude/tools/project_management/project_registry.py show REPO-GOV-001
```

**Output**:
```
Project: REPO-GOV-001
Name: Git Repository Governance
Status: planned
Priority: high
Effort: 40 hours (estimated)
Impact: high
Category: DevOps/SRE

Description:
  Production-grade multi-user repository protection with automated
  enforcement layers and emergency recovery procedures.

Project Plan:
  claude/data/GIT_REPOSITORY_GOVERNANCE_PROJECT.md

Timeline:
  Created: 2025-10-27
  Started: (not started)
  Completed: (not completed)

Dependencies:
  None

Deliverables (8):
  - CODEOWNERS file (planned)
  - core-protection.yml (planned)
  - validate_core_schema.py (planned)
  - performance_baseline.py (planned)
  - CONTRIBUTING.md (planned)
  - CORE_PROTECTION_GUIDE.md (planned)
  - EMERGENCY_PROCEDURES.md (planned)
  - emergency-rollback.yml (planned)
```

---

#### 4. `start` - Begin Project

```bash
python3 claude/tools/project_management/project_registry.py start REPO-GOV-001
```

**Actions**:
- Set `status = 'active'`
- Set `started_date = CURRENT_TIMESTAMP`
- Log to `project_updates` table
- Regenerate markdown backlog

---

#### 5. `complete` - Finish Project

```bash
python3 claude/tools/project_management/project_registry.py complete REPO-GOV-001 \
    --actual-hours 38 \
    --notes "Completed 2 hours under estimate"
```

**Actions**:
- Set `status = 'completed'`
- Set `completed_date = CURRENT_TIMESTAMP`
- Set `actual_hours` (if provided)
- Calculate variance: `actual_hours - effort_hours`
- Log to `project_updates`
- Archive project plan to `claude/data/archive/completed/`

---

#### 6. `update` - Modify Project

```bash
# Change priority
python3 claude/tools/project_management/project_registry.py update REPO-GOV-001 \
    --priority critical

# Block project
python3 claude/tools/project_management/project_registry.py update REPO-GOV-001 \
    --status blocked \
    --notes "Waiting for GitHub Enterprise approval"

# Update effort estimate
python3 claude/tools/project_management/project_registry.py update REPO-GOV-001 \
    --effort 45
```

---

#### 7. `backlog` - Prioritized View

```bash
python3 claude/tools/project_management/project_registry.py backlog
```

**Output** (sorted by priority, then effort):
```
════════════════════════════════════════════════════════════════
MAIA PROJECT BACKLOG
Total: 28 projects (22 planned, 3 active, 1 blocked, 2 completed)
════════════════════════════════════════════════════════════════

🔥 CRITICAL PRIORITY (1 project, 20 hours)

  SEC-AUT-002: Security Automation Enhancement
  Status: planned | Effort: 20h | Impact: high | Category: Security
  Plan: claude/data/SECURITY_AUTOMATION_PROJECT.md

⚡ HIGH PRIORITY (5 projects, 132 hours)

  REPO-GOV-001: Git Repository Governance
  Status: planned | Effort: 40h | Impact: high | Category: DevOps/SRE
  Plan: claude/data/GIT_REPOSITORY_GOVERNANCE_PROJECT.md

  PHASE-126: Quality Improvement Measurement
  Status: planned | Effort: 12h | Impact: medium | Category: SRE
  Dependencies: Phase-121, Phase-125

  [... 3 more high-priority projects ...]

📊 MEDIUM PRIORITY (10 projects, 180 hours)
  [...]

📌 LOW PRIORITY (6 projects, 85 hours)
  [...]

🚧 ACTIVE (3 projects)
  [...]

⛔ BLOCKED (1 project)
  [...]
```

---

#### 8. `stats` - Summary Metrics

```bash
python3 claude/tools/project_management/project_registry.py stats
```

**Output**:
```
MAIA PROJECT REGISTRY STATISTICS
═════════════════════════════════════════════════════════════

Project Count:
  Total Projects: 28
  Planned: 22 (78.6%)
  Active: 3 (10.7%)
  Blocked: 1 (3.6%)
  Completed: 2 (7.1%)

Effort Estimates:
  Total Planned Effort: 417 hours
  Average Project Size: 19 hours
  Largest Project: 60 hours (SERVICEDESK-TIER-001)
  Smallest Project: 3 hours (DOC-UPDATE-005)

By Priority:
  Critical: 1 project (20h)
  High: 5 projects (132h)
  Medium: 10 projects (180h)
  Low: 6 projects (85h)

By Category:
  SRE: 8 projects (156h)
  DevOps: 4 projects (92h)
  ServiceDesk: 6 projects (98h)
  Security: 3 projects (45h)
  Agent: 2 projects (16h)
  Documentation: 5 projects (10h)

Velocity (last 30 days):
  Completed: 2 projects
  Average completion time: 12 days
  Effort variance: -8% (beating estimates)
```

---

#### 9. `export` - Generate Reports

```bash
# Export to markdown (auto-generated backlog)
python3 claude/tools/project_management/project_registry.py export --format markdown

# Export to JSON (machine-readable)
python3 claude/tools/project_management/project_registry.py export --format json

# Export completed projects only
python3 claude/tools/project_management/project_registry.py export \
    --format markdown \
    --status completed
```

**Markdown Output** → `MAIA_PROJECT_BACKLOG.md` (auto-committed to Git)

---

#### 10. `depend` - Manage Dependencies

```bash
# Add dependency
python3 claude/tools/project_management/project_registry.py depend add \
    --project PHASE-126 \
    --depends-on PHASE-121 \
    --type blocks

# List dependencies for project
python3 claude/tools/project_management/project_registry.py depend list PHASE-126

# Show dependency graph
python3 claude/tools/project_management/project_registry.py depend graph
```

**Dependency Graph Output**:
```
PHASE-121 (completed)
  └─→ PHASE-126 (planned) [blocks]
      └─→ PHASE-127 (planned) [blocks]

REPO-GOV-001 (planned)
  ├─→ PHASE-135 (completed) [optional]
  └─→ (no blocking dependencies)
```

---

## Migration Plan

### Automatic Migration from Existing Projects

**File**: `claude/tools/project_management/migrate_existing_projects.py`

**Process**:
1. Scan `claude/data/` for `*PROJECT*.md` and `*PLAN*.md` files
2. Parse each file:
   - Extract metadata from frontmatter (if exists)
   - Infer status from file name patterns (`PROJECT_PLAN`, `IMPLEMENTATION_PLAN`)
   - Extract effort estimates from text
   - Identify deliverables from sections
3. Insert into `project_registry.db`
4. Generate audit log entry
5. Validate migration completeness (100% coverage)

**Execution**:
```bash
python3 claude/tools/project_management/migrate_existing_projects.py \
    --source-dir claude/data \
    --dry-run

# Review output, then actually migrate
python3 claude/tools/project_management/migrate_existing_projects.py \
    --source-dir claude/data \
    --confirm
```

**Expected Results**:
```
Migration Report
═══════════════════════════════════════════════════════════
Scanned Files: 28
Successfully Migrated: 28 (100%)
Failed: 0
Warnings: 3 (missing effort estimates)

Migrated Projects by Status:
  planned: 22
  completed: 6

Migration completed in 2.3 seconds.
Database: claude/data/project_registry.db (184 KB)
```

---

## Operational Procedures

### Daily Operations (Automated)

**Backup**: Daily at 2 AM (via cron/launchd)
```bash
# Backup database to OneDrive
cp claude/data/project_registry.db \
   ~/Library/CloudStorage/OneDrive-YOUR_ORG/Maia-Backups/project_registry_$(date +%Y%m%d).db
```

**Export**: Auto-regenerate markdown on every update
```python
# In project_registry.py (after any write operation)
def _auto_export():
    """Auto-export markdown backlog after DB changes."""
    export_markdown(output_path="MAIA_PROJECT_BACKLOG.md")
    # Git commit if changes detected
    if git_has_changes("MAIA_PROJECT_BACKLOG.md"):
        git_commit("MAIA_PROJECT_BACKLOG.md", "Auto-update: Project backlog refreshed")
```

---

### Weekly Review (15 min)

**Monday Morning Checklist**:
1. Review backlog: `project_registry.py backlog`
2. Check blocked projects: `project_registry.py list --status blocked`
3. Review active projects: `project_registry.py list --status active`
4. Plan week's work (select 1-2 projects to start)

---

### Monthly Retrospective (30 min)

**First Monday of Month**:
1. Generate stats: `project_registry.py stats`
2. Review velocity trends (completed vs planned)
3. Update stale projects (>90 days planned → archive?)
4. Adjust priorities based on business needs
5. Document learnings in `project_updates` notes

---

## Service Level Objectives (SLOs)

### Performance SLOs

| Metric | SLO | Measurement | Alert Threshold |
|--------|-----|-------------|-----------------|
| Query Latency | P95 <100ms | CLI execution time | P95 >200ms |
| Write Latency | P95 <50ms | Transaction commit time | P95 >100ms |
| Export Generation | <5 seconds | Markdown export duration | >10 seconds |
| Database Size | <10 MB | File size (1,000 projects) | >50 MB |

### Reliability SLOs

| Metric | SLO | Measurement | Alert Threshold |
|--------|-----|-------------|-----------------|
| Data Integrity | 100% (ACID) | SQLite guarantees | Transaction failure |
| Backup Success Rate | >99% | Daily backup logs | Failed backup |
| Migration Coverage | 100% | Validation script | <100% |
| Query Success Rate | >99.9% | Error logs | >0.1% failures |

### Operational SLOs

| Metric | Target | Measurement | Review Frequency |
|--------|--------|-------------|------------------|
| Discovery Time | <30 seconds | Find any project | Monthly |
| Update Time | <2 minutes | Change status/priority | Monthly |
| Backlog Freshness | <24 hours | Last export timestamp | Weekly |
| False Data Rate | <1% | Manual spot checks | Quarterly |

---

## Implementation Phases

### Phase 1: Database Setup (1 hour)

**Tasks**:
1. Create database schema
2. Enable WAL mode
3. Add indexes
4. Create test data
5. Validate schema

**Deliverable**: `claude/data/project_registry.db` (functional, empty)

---

### Phase 2: CLI Tool Development (1.5 hours)

**Tasks**:
1. Build core CRUD operations
2. Implement validation logic
3. Add error handling
4. Create help text
5. Test with sample data

**Deliverable**: `claude/tools/project_management/project_registry.py` (working CLI)

---

### Phase 3: Migration Script (1 hour)

**Tasks**:
1. Build file scanner
2. Implement metadata parser
3. Create import logic
4. Add validation checks
5. Dry-run test on 28 existing projects

**Deliverable**: `claude/tools/project_management/migrate_existing_projects.py`

---

### Phase 4: Export & Automation (0.5 hours)

**Tasks**:
1. Build markdown export
2. Add JSON export
3. Create auto-export hook
4. Set up daily backup cron
5. Test end-to-end workflow

**Deliverables**:
- `MAIA_PROJECT_BACKLOG.md` (auto-generated)
- Backup cron job (LaunchAgent)

---

### Phase 5: Validation & Documentation (0.5 hours)

**Tasks**:
1. Execute full migration (28 projects)
2. Verify 100% coverage
3. Run performance benchmarks
4. Document CLI usage
5. Create quick reference card

**Deliverables**:
- Populated database (28 projects)
- `docs/PROJECT_REGISTRY_GUIDE.md`
- CLI quick reference

---

## Success Metrics

### Implementation Success

| Metric | Target | Validation |
|--------|--------|------------|
| Migration Coverage | 100% (28/28 projects) | Validation script |
| Database Integrity | 0 errors | PRAGMA integrity_check |
| Query Performance | <100ms P95 | Benchmark test |
| Export Success | 100% | Markdown generation |

### Operational Success (30 days post-launch)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time Saved | >30 min/week | User survey |
| Discovery Speed | <30 sec/project | Time tracking |
| Data Accuracy | >99% | Manual audit |
| Tool Adoption | 100% (used weekly) | Query logs |

---

## Risk Assessment

### High-Risk Scenarios

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Database Corruption** | Low | High | WAL mode + daily backups + OneDrive sync |
| **Migration Data Loss** | Low | High | Dry-run validation + manual review before confirm |
| **Performance Degradation** | Low | Medium | Indexes + benchmarks + SLO monitoring |
| **Circular Dependencies** | Medium | Low | Validation logic in `depend add` command |

### Rollback Plan

**If system fails or causes issues**:

1. **Disable auto-export** (prevent markdown churn)
2. **Restore from backup** (OneDrive daily backup)
3. **Fall back to manual tracking** (capability_index.md "UP NEXT")
4. **Post-mortem** (identify root cause, fix, re-deploy)

**Rollback Time**: <15 minutes

---

## File Locations

**Database**:
- `claude/data/project_registry.db` (primary)
- `~/Library/CloudStorage/OneDrive-YOUR_ORG/Maia-Backups/project_registry_*.db` (backups)

**CLI Tools**:
- `claude/tools/project_management/project_registry.py` (main tool)
- `claude/tools/project_management/migrate_existing_projects.py` (migration)

**Exports**:
- `MAIA_PROJECT_BACKLOG.md` (auto-generated, Git-tracked)
- `claude/data/project_registry_export.json` (machine-readable)

**Documentation**:
- `docs/PROJECT_REGISTRY_GUIDE.md` (usage guide)
- `docs/PROJECT_REGISTRY_QUICK_REF.md` (1-page cheat sheet)

---

## Session Persistence Configuration

**Agent Assignment**: SRE Principal Engineer Agent

**Auto-Load Trigger**: Any request mentioning:
- "project registry"
- "project backlog"
- "PROJ-REG-001"
- File paths: `project_registry.py`, `project_registry.db`

**Session State File**: `/tmp/maia_active_swarm_session_PROJ_REG_001.json`

**Contents**:
```json
{
  "version": "1.1",
  "context_id": "PROJ_REG_001",
  "current_agent": "sre_principal_engineer_agent",
  "routing_confidence": 0.95,
  "complexity_score": 8,
  "handoff_chain": ["sre_principal_engineer_agent"],
  "context": {
    "project_id": "PROJ-REG-001",
    "project_name": "Maia Project Registry System",
    "current_phase": "planning",
    "next_phase": "implementation",
    "session_notes": "Production-grade SQLite project backlog tracking system"
  },
  "timestamp": "2025-10-27T10:45:00Z"
}
```

**Benefits**:
- ✅ SRE agent auto-loads on session restart
- ✅ Project context preserved across restarts
- ✅ No manual "load sre agent" needed
- ✅ Consistent expertise throughout project lifecycle

---

## Next Steps

### Immediate Actions

**Decision Point**: Approve project plan for implementation

**Once Approved**:
1. Create session state file (persist SRE agent)
2. Start Phase 1: Database setup (1 hour)
3. Progress to Phase 2: CLI tool (1.5 hours)
4. Complete implementation (total: 3-4 hours)

**Ready to start?** Say:
- **"Start Phase 1"** → Begin database setup
- **"Implement the full system"** → Execute all 5 phases
- **"Show me Phase 1 code"** → Review database schema implementation

---

## Appendices

### Appendix A: Example Projects in Registry

**Sample Data** (after migration):

| ID | Name | Status | Priority | Effort | Category |
|----|------|--------|----------|--------|----------|
| REPO-GOV-001 | Git Repository Governance | planned | high | 40h | DevOps/SRE |
| PHASE-126 | Quality Improvement Measurement | planned | high | 12h | SRE |
| SEC-AUT-002 | Security Automation Enhancement | planned | critical | 20h | Security |
| SD-TIER-001 | ServiceDesk Tier Tracker | planned | medium | 30h | ServiceDesk |
| AGENT-EVO-001 | Agent Evolution Framework | completed | high | 18h | Agent |

---

### Appendix B: CLI Quick Reference

```bash
# Add new project
project_registry.py add --id ID --name "Name" --priority high

# List projects
project_registry.py list --status planned
project_registry.py list --priority high

# Show details
project_registry.py show ID

# Update project
project_registry.py update ID --status active
project_registry.py start ID

# Complete project
project_registry.py complete ID --actual-hours 38

# View backlog
project_registry.py backlog

# Statistics
project_registry.py stats

# Export
project_registry.py export --format markdown
```

---

### Appendix C: Database Maintenance

**Vacuum** (monthly, reclaim space):
```bash
sqlite3 claude/data/project_registry.db "VACUUM;"
```

**Integrity Check** (weekly):
```bash
sqlite3 claude/data/project_registry.db "PRAGMA integrity_check;"
```

**Backup Validation** (test restore):
```bash
cp ~/Library/CloudStorage/OneDrive-YOUR_ORG/Maia-Backups/project_registry_latest.db \
   /tmp/test_restore.db
sqlite3 /tmp/test_restore.db "SELECT COUNT(*) FROM projects;"
```

---

**Project Status**: ✅ PLANNING COMPLETE - READY FOR IMPLEMENTATION

**Last Updated**: 2025-10-27
**Version**: 1.0
**SRE Agent**: Loaded and persisted for project duration
