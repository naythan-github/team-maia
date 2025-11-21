# File Organization Policy

**Purpose**: Define clear rules for where files should be saved to maintain UFC structure and prevent repository pollution.

**Enforcement**: Mandatory core context loading + pre-commit hook + validation tool

---

## 🚨 DECISION TREE: Where Should I Save This File?

### STEP 1: Is this a Maia system file or work output?

**Maia system file** (helps Maia operate):
- Tools, agents, commands that make Maia work
- Maia operational databases (routing, tool usage, etc.)
- System documentation and protocols
→ Continue to **STEP 2**

**Work output** (produced BY Maia for operational work):
- ServiceDesk analysis reports
- Infrastructure team data
- Client deliverables
- Recruitment tests
- One-off analysis files
→ Save to `~/work_projects/{project_name}/`

**Decision Criteria**: "Does this file help Maia operate, or is it output FROM Maia?"

---

### STEP 2: What type of Maia file is it?

| File Type | Location | Examples |
|-----------|----------|----------|
| **Agent Definition** | `claude/agents/` | `*_agent.md` |
| **Tool Implementation** | `claude/tools/` | `*.py` scripts |
| **Command** | `claude/commands/` | `*.md` slash commands |
| **System Context** | `claude/context/core/` | System-wide policies, protocols |
| **Domain Knowledge** | `claude/context/knowledge/{domain}/` | Reference materials |
| **Operational Database** | `claude/data/databases/{category}/` | `*.db` files (see categories below) |
| **RAG Database** | `claude/data/rag_databases/` | Vector stores, ChromaDB |
| **Phase Documentation** | `claude/data/project_status/active/` | Phase docs <30 days old |
| **Archived Phase Docs** | `claude/data/project_status/archive/{YYYY-QQ}/` | Phase docs >30 days old |
| **Project Plans** | `claude/data/project_status/active/` | `{PROJECT}_PLAN.md`, `{PROJECT}_progress.md` |
| **Test Files** | `tests/` | `test_*.py` |

---

## FORBIDDEN LOCATIONS

❌ **Repository Root** (only 6 core files + 2 path manager directories allowed):
- ✅ ALLOWED FILES: `CLAUDE.md`, `README.md`, `SYSTEM_STATE.md`, `SYSTEM_STATE_ARCHIVE.md`
- ✅ ALLOWED DIRECTORIES: `${MAIA_ROOT}/` (path manager template), `get_path_manager().get_path('backup') /` (backup system)
- ❌ FORBIDDEN: All other files

❌ **claude/data/ root** (use subdirectories):
- Use `databases/`, `project_status/`, `rag_databases/`, etc.
- NOT directly in `claude/data/`

❌ **Maia repo for work outputs**:
- ServiceDesk analysis → `~/work_projects/servicedesk_analysis/`
- Infrastructure team data → `~/work_projects/infrastructure_team/`
- Recruitment tests → `~/work_projects/recruitment/`

---

## SIZE LIMITS

**Rule**: Files >10 MB MUST be in `~/work_projects/` (NOT Maia repository)

**Exception**: RAG databases in `claude/data/rag_databases/` (can exceed 10 MB)

**Rationale**: Large operational datasets bloat repository and slow git operations.

---

## DATABASE ORGANIZATION

**Location**: All `*.db` files → `claude/data/databases/{category}/`

**Categories**:

| Category | Purpose | Examples |
|----------|---------|----------|
| **intelligence/** | Intelligence gathering databases | `security_intelligence.db`, `rss_intelligence.db`, `servicedesk_operations_intelligence.db` |
| **system/** | Maia system operational databases | `routing_decisions.db`, `tool_usage.db`, `documentation_enforcement.db`, `project_registry.db` |
| **user/** | User-specific databases | `*_naythan.db` (autonomous_alerts, background_learning, etc.) |
| **archive/** | Deprecated/experimental databases | Old databases no longer in use |

**Exception**: `claude/data/rag_databases/` for vector databases (ChromaDB, etc.)

---

## TDD PROJECT FILE ORGANIZATION

### Maia System Development (improving Maia itself)

**Structure**:
```
claude/tools/{tool_name}/
├── requirements.md          # TDD requirements document
├── implementation.py        # Tool implementation
└── README.md               # Tool documentation

tests/
└── test_{tool_name}.py     # Test suite
```

**Example**: Developing new analysis tool
- `claude/tools/analysis_pattern_library/requirements.md`
- `claude/tools/analysis_pattern_library/implementation.py`
- `tests/test_analysis_pattern_library.py`

---

### Work Projects (using Maia for operational work)

**Structure**:
```
~/work_projects/{project}/
├── requirements.md          # Project requirements
├── implementation.py        # Implementation (if applicable)
├── test_requirements.py     # Tests
├── data/                    # Project data files
└── README.md               # Project documentation
```

**Example**: ServiceDesk analysis project
- `~/work_projects/servicedesk_analysis/requirements.md`
- `~/work_projects/servicedesk_analysis/data/servicedesk_tickets.db`
- `~/work_projects/servicedesk_analysis/analysis_results/`

---

## PROJECT DOCUMENTATION TYPES

### When to create what:

| File Type | When to Create | Location | Purpose |
|-----------|---------------|----------|---------|
| **requirements.md** | ALWAYS for TDD development | With implementation | Technical specs, acceptance criteria |
| **{PROJECT}_PLAN.md** | Multi-phase projects (>3 phases) | `claude/data/project_status/active/` | High-level project plan, phases, timeline |
| **{PROJECT}_progress.md** | Multi-phase projects | `claude/data/project_status/active/` | Incremental progress tracking |
| **README.md** | All tools/projects | With implementation | Usage guide, documentation |

### File Relationships:
- **PROJECT_PLAN.md**: "What phases?" (strategic)
- **requirements.md**: "What functionality?" (tactical)
- **progress.md**: "What's done?" (tracking)

---

## IMPLEMENTATION PLAN ORGANIZATION

**When creating implementation plans**:
- Multi-phase projects → `claude/data/project_status/active/{PROJECT}_PLAN.md`
- Include agent reload commands (per Phase 150 protocol)
- Include progress saving checkpoints
- Reference requirements.md for technical details

**Template**:
```markdown
## Phase 1: [Name]
**AGENT**: Load SRE Principal Engineer Agent + [Domain Specialist]
**Command**: "load sre_principal_engineer_agent"

[Phase steps...]

**Save Progress**: Update {PROJECT}_progress.md with Phase 1 completion
```

---

## PHASE DOCUMENTATION ARCHIVAL

**Active** (`claude/data/project_status/active/`):
- Last 5 phases OR last 30 days (whichever is more)
- Current project plans and progress trackers

**Archive** (`claude/data/project_status/archive/{YYYY-QQ}/`):
- Phase docs >30 days old
- Completed project plans
- Organized by quarter (2025-Q4, 2025-Q3, etc.)

**Cleanup**: Delete phase docs >1 year old (history preserved in SYSTEM_STATE.md)

---

## VALIDATION WORKFLOW

### Before Saving Any File:

1. **Ask**: Is this Maia system file or work output?
2. **Check**: What type of file is it? (agent, tool, database, etc.)
3. **Verify**: Does size exceed 10 MB?
4. **Validate**: Use `validate_file_location.py` tool (optional):
   ```bash
   python3 claude/tools/validate_file_location.py "path/to/file" "file purpose"
   ```

### Tool Output:
```
✅ Valid: Compliant with file organization policy
   OR
❌ Invalid: Work outputs should not be in Maia repository
   Recommended: ~/work_projects/servicedesk_analysis/
   Policy violated: Operational Data Separation Policy
```

---

## ENFORCEMENT MECHANISMS

### Layer 1: Preventive (This Policy)
- Loaded in mandatory core context (every session)
- Provides clear guidance before files created

### Layer 2: Runtime Validation (Optional)
- `validate_file_location.py` tool
- Agents can call to check before saving

### Layer 3: Git-Time Enforcement (Pre-Commit Hook)
- `claude/hooks/pre_commit_file_organization.py`
- Blocks commits violating policy
- Can bypass with `--no-verify` if urgent

### Layer 4: Documentation Reference
- `identity.md` Working Principle #19
- Quick reference for file storage rules

---

## COMMON SCENARIOS

### Scenario 1: Creating ServiceDesk Analysis
**File**: `ServiceDesk_Tier_Analysis.xlsx`
**Purpose**: "Analysis of L1/L2/L3 ticket distribution"
**Decision**: Work output → `~/work_projects/servicedesk_analysis/`
**NOT**: `claude/data/ServiceDesk_Tier_Analysis.xlsx` ❌

### Scenario 2: Creating New Agent
**File**: `data_analyst_agent.md`
**Purpose**: "Maia agent for data analysis"
**Decision**: Maia system file → `claude/agents/data_analyst_agent.md` ✅

### Scenario 3: Creating Analysis Database
**File**: `project_metrics.db`
**Purpose**: "Database tracking project completion metrics"
**Decision**: Maia system database → `claude/data/databases/system/project_metrics.db` ✅

### Scenario 4: Creating Phase Documentation
**File**: `PHASE_151_COMPLETE.md`
**Purpose**: "Documentation of Phase 151 completion"
**Decision**: Recent phase doc → `claude/data/project_status/active/PHASE_151_COMPLETE.md` ✅
**After 30 days**: Move to `claude/data/project_status/archive/2025-Q4/`

### Scenario 5: Creating Large Dataset
**File**: `servicedesk_tickets.db` (154 MB)
**Purpose**: "ServiceDesk ticket database for analysis"
**Decision**: >10 MB work output → `~/work_projects/servicedesk_analysis/data/servicedesk_tickets.db` ✅
**NOT**: `claude/data/servicedesk_tickets.db` ❌ (violates size limit)

---

## MIGRATION GUIDANCE

### If Files Currently Misplaced:

**DO NOT move files immediately** - requires dependency analysis first.

**Proper cleanup workflow**:
1. Analyze dependencies (`grep -r "filename" claude/tools/ claude/hooks/`)
2. Check SYSTEM_STATE.md for production system status
3. Test incremental movement (1 file at a time)
4. Consider symlink strategy (safer than direct movement)
5. Validate all dependent systems after each move

**See**: Anti-Breakage Protocol (`claude/context/core/anti_breakage_protocol.md`)

---

## EXCEPTIONS

### When size limit doesn't apply:
- ✅ RAG databases in `claude/data/rag_databases/` (can exceed 10 MB)
- ✅ Test fixtures in `tests/fixtures/` (if needed for testing)

### When work output can stay in Maia repo:
- ❌ **NEVER** - All work outputs → `~/work_projects/`

### When root directory files allowed:
- ✅ Only 4 core files: `CLAUDE.md`, `README.md`, `SYSTEM_STATE.md`, `SYSTEM_STATE_ARCHIVE.md`

---

## PRE-COMMIT HOOK INSTALLATION

**Automatic** (recommended):
```bash
ln -s ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Manual** (copy file):
```bash
cp claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass** (if urgent):
```bash
git commit --no-verify
```

---

## SUCCESS METRICS

**Compliant Repository**:
- Root directory: 4 core files + 2 path manager directories only
- claude/data/ root: <20 files (rest in subdirectories)
- No files >10 MB (except rag_databases/)
- No work outputs in Maia repo
- All databases in databases/{category}/

**Non-Compliant Repository**:
- Root directory: 10+ files (excluding allowed path manager directories)
- claude/data/ root: 200+ files
- Multiple files >10 MB
- Work outputs mixed with system files
- Databases scattered throughout

---

**Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: Active - Mandatory Core Context Loading
