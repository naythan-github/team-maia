# File Organization Policy
**Purpose**: Clear rules for file placement to maintain UFC structure
**Enforcement**: Core context + pre-commit hook + validation tool

---

## DECISION TREE

### STEP 1: Maia System File or Work Output?

**Maia system** (helps Maia operate): Tools, agents, commands, operational DBs, system docs
→ Continue to **STEP 2**

**Work output** (produced BY Maia): ServiceDesk analysis, infrastructure data, client deliverables, recruitment tests, one-off analysis
→ Save to `~/work_projects/{project_name}/`

**Rule**: "Does this help Maia operate (KEEP) or is it output FROM Maia (MOVE)?"

---

### STEP 2: File Type Location

| Type | Location | Examples |
|------|----------|----------|
| Agent | `claude/agents/` | `*_agent.md` |
| Tool | `claude/tools/` | `*.py` scripts |
| Command | `claude/commands/` | `*.md` slash commands |
| System Context | `claude/context/core/` | Policies, protocols |
| Domain Knowledge | `claude/context/knowledge/{domain}/` | Reference materials |
| Operational DB | `claude/data/databases/{category}/` | `*.db` (see categories) |
| RAG DB | `claude/data/rag_databases/` | Vector stores, ChromaDB |
| Phase Docs (active) | `claude/data/project_status/active/` | <30 days old |
| Phase Docs (archive) | `claude/data/project_status/archive/{YYYY-QQ}/` | >30 days old |
| Project Plans | `claude/data/project_status/active/` | `{PROJECT}_PLAN.md` |
| Tests | `tests/` | `test_*.py` |

---

## FORBIDDEN LOCATIONS

**Repository Root** (only 4 core files + 3 operational dirs):
- ✅ `CLAUDE.md`, `README.md`, `SYSTEM_STATE.md`, `SYSTEM_STATE_ARCHIVE.md`
- ✅ `${MAIA_ROOT}/`, `backup/`, `scripts/`
- ❌ All other files

**claude/data/ root**: Use subdirectories (databases/, project_status/, rag_databases/)

**Maia repo for work outputs**: ❌ NEVER - All work → `~/work_projects/`

---

## SIZE LIMITS

**Rule**: Files >10 MB → `~/work_projects/` (NOT Maia repo)
**Exception**: RAG databases in `claude/data/rag_databases/`

---

## DATABASE ORGANIZATION

**Location**: All `*.db` → `claude/data/databases/{category}/`

| Category | Purpose | Examples |
|----------|---------|----------|
| intelligence/ | Intelligence gathering | `security_intelligence.db`, `rss_intelligence.db` |
| system/ | Maia system operations | `routing_decisions.db`, `tool_usage.db` |
| user/ | User-specific | `*_naythan.db` (autonomous_alerts, etc.) |
| archive/ | Deprecated/experimental | Old databases |

**Exception**: `claude/data/rag_databases/` for vector databases

---

## TDD PROJECT ORGANIZATION

### Maia System Development
```
claude/tools/{tool_name}/
├── requirements.md
├── implementation.py
└── README.md

tests/
└── test_{tool_name}.py
```

### Work Projects
```
~/work_projects/{project}/
├── requirements.md
├── implementation.py (if applicable)
├── test_requirements.py
├── data/
└── README.md
```

---

## PROJECT DOCUMENTATION

| Type | When | Location | Purpose |
|------|------|----------|---------|
| requirements.md | ALWAYS for TDD | With implementation | Technical specs |
| {PROJECT}_PLAN.md | Multi-phase (>3 phases) | `project_status/active/` | High-level plan |
| {PROJECT}_progress.md | Multi-phase | `project_status/active/` | Progress tracking |
| README.md | All tools/projects | With implementation | Usage guide |

---

## IMPLEMENTATION PLANS

Multi-phase projects → `claude/data/project_status/active/{PROJECT}_PLAN.md`

**Template**:
```markdown
## Phase 1: [Name]
**AGENT**: Load [agents]
**Command**: "load agent_name"
[Phase steps...]
**Save Progress**: Update progress.md
```

---

## PHASE DOCUMENTATION ARCHIVAL

**Active** (`project_status/active/`): Last 5 phases OR last 30 days
**Archive** (`project_status/archive/{YYYY-QQ}/`): >30 days old
**Cleanup**: Delete >1 year old (history in SYSTEM_STATE.md)

---

## VALIDATION WORKFLOW

### Before Saving:
1. Maia system file or work output?
2. What type? (agent, tool, database, etc.)
3. Size >10 MB?
4. Optional: `python3 claude/tools/validate_file_location.py "path" "purpose"`

---

## ENFORCEMENT LAYERS

**Layer 1**: This policy (mandatory core context)
**Layer 2**: `validate_file_location.py` tool (optional)
**Layer 3**: Pre-commit hook (`pre_commit_file_organization.py`)
**Layer 4**: `identity.md` Working Principle #19

---

## COMMON SCENARIOS

| Scenario | File | Decision | Location |
|----------|------|----------|----------|
| ServiceDesk Analysis | ServiceDesk_Tier_Analysis.xlsx | Work output | `~/work_projects/servicedesk_analysis/` |
| New Agent | data_analyst_agent.md | Maia system | `claude/agents/` |
| Analysis DB | project_metrics.db | Maia system | `claude/data/databases/system/` |
| Phase Doc | PHASE_151_COMPLETE.md | Recent phase | `project_status/active/` (then archive) |
| Large Dataset | servicedesk_tickets.db (154MB) | >10MB work output | `~/work_projects/.../data/` |

---

## POST-REORGANIZATION SYNC ⭐ PHASE 169

**After moving/reorganizing files:**
```bash
# Re-scan capabilities + fix system_state.db paths
python3 claude/tools/sre/path_sync.py sync

# Or separately:
python3 claude/tools/sre/capabilities_registry.py scan
python3 claude/tools/sre/path_sync.py auto-fix

# Dry-run first:
python3 claude/tools/sre/path_sync.py auto-fix --dry-run
```

**When to run**: After file reorganization, archiving, moving tools, renaming agents

---

## PRE-COMMIT HOOK

**Install**:
```bash
ln -s ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass** (if urgent): `git commit --no-verify`

---

## SUCCESS METRICS

**Compliant**:
- Root: 4 core files + 3 operational dirs only
- claude/data/ root: <20 files
- No files >10MB (except rag_databases/)
- No work outputs in Maia repo
- All DBs in databases/{category}/

**Non-Compliant**:
- Root: 10+ files
- claude/data/ root: 200+ files
- Multiple files >10MB
- Work outputs mixed with system files

---

**Version**: 1.0 | **Updated**: 2025-11-07 | **Status**: Active - Mandatory Core Context
