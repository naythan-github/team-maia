# File Organization Policy - Requirements

**Created**: 2025-11-07 (Retroactive - TDD compliance)
**Component**: Core context policy document
**Purpose**: Define clear rules for where files should be saved in Maia repository

---

## Core Purpose

**Problem**: Agents have no clear guidance on where to save files, resulting in 180+ MB of operational work data mixed with Maia system files.

**Solution**: Comprehensive file organization policy loaded in mandatory core context, providing decision tree and location map for all file types.

---

## Functional Requirements

### FR1: Decision Tree (2-Step Process)
**Requirement**: Provide clear 2-step decision process for file placement.

**Step 1**: Is this Maia system file or work output?
- Maia system file → Continue to Step 2
- Work output → `~/work_projects/{project}/`

**Step 2**: What type of Maia file?
- Map file type to specific directory

**Acceptance Criteria**:
- ✅ Decision tree answers "where to save?" in ≤2 steps
- ✅ Every file type has clear destination
- ✅ No ambiguous cases

**Example**:
- Input: "ServiceDesk analysis Excel file"
- Output: Work output → `~/work_projects/servicedesk_analysis/`

---

### FR2: Location Map (File Type → Directory)
**Requirement**: Table mapping all file types to correct directories.

**File Types Covered**:
1. Agent definitions (`*_agent.md`)
2. Tool implementations (`*.py`)
3. Commands (`*.md`)
4. System context policies
5. Domain knowledge
6. Operational databases
7. RAG databases
8. Phase documentation (active/archive)
9. Project plans
10. Test files

**Acceptance Criteria**:
- ✅ All 10+ file types documented
- ✅ Table format (scannable, information-dense)
- ✅ Clear examples for each type

---

### FR3: Size Limits
**Requirement**: Enforce file size limits to prevent repository bloat.

**Rules**:
- Files >10 MB → MUST be in `~/work_projects/`
- Exception: RAG databases in `claude/data/rag_databases/`

**Acceptance Criteria**:
- ✅ Clear MB threshold (10 MB)
- ✅ Exception documented
- ✅ Rationale explained (git performance)

**Example**:
- `servicedesk_tickets.db` (154 MB) → `~/work_projects/` (violates limit)

---

### FR4: Database Organization
**Requirement**: Categorize databases for organization.

**Categories**:
1. **intelligence/**: Security, RSS, ServiceDesk ops intelligence
2. **system/**: Routing decisions, tool usage, doc enforcement
3. **user/**: User-specific (`*_naythan.db`)
4. **archive/**: Deprecated databases

**Location**: `claude/data/databases/{category}/`

**Acceptance Criteria**:
- ✅ 4 categories defined
- ✅ Clear categorization criteria
- ✅ Examples for each category

---

### FR5: TDD Project Structure
**Requirement**: Define file organization for TDD projects.

**Maia System Development**:
```
claude/tools/{tool_name}/
├── requirements.md
├── implementation.py
└── README.md
tests/test_{tool_name}.py
```

**Work Projects**:
```
~/work_projects/{project}/
├── requirements.md
├── implementation.py
├── test_requirements.py
└── data/
```

**Acceptance Criteria**:
- ✅ Both structures documented
- ✅ Clear distinction (Maia system vs. work)
- ✅ Examples provided

---

### FR6: Project Documentation Types
**Requirement**: Clarify different documentation file purposes.

**Types**:
1. **requirements.md**: Technical specs, acceptance criteria (TDD)
2. **{PROJECT}_PLAN.md**: High-level project plan, phases, timeline
3. **{PROJECT}_progress.md**: Incremental progress tracking
4. **README.md**: Usage guide, documentation

**Acceptance Criteria**:
- ✅ All 4 types explained
- ✅ When to create each type
- ✅ Where to save each type

---

### FR7: Phase Documentation Archival
**Requirement**: Define retention policy for phase documentation.

**Rules**:
- **Active**: Last 5 phases OR last 30 days → `claude/data/project_status/active/`
- **Archive**: >30 days old → `claude/data/project_status/archive/{YYYY-QQ}/`
- **Cleanup**: Delete >1 year old (history in SYSTEM_STATE.md)

**Acceptance Criteria**:
- ✅ Clear time-based rules
- ✅ Archive organization (by quarter)
- ✅ Cleanup policy defined

---

### FR8: Validation Workflow
**Requirement**: Provide step-by-step validation workflow.

**Steps**:
1. Ask: Maia system file or work output?
2. Check: What type of file?
3. Verify: Size >10 MB?
4. Validate: Use `validate_file_location.py` tool (optional)

**Acceptance Criteria**:
- ✅ 4-step workflow documented
- ✅ Each step has clear action
- ✅ Tool integration mentioned

---

### FR9: Enforcement Layers
**Requirement**: Document 4-layer defense-in-depth enforcement.

**Layers**:
1. **Preventive**: Policy in mandatory core context
2. **Runtime**: `validate_file_location.py` tool (optional)
3. **Git-Time**: Pre-commit hook (blocks violations)
4. **Documentation**: `identity.md` working principle reference

**Acceptance Criteria**:
- ✅ All 4 layers documented
- ✅ Each layer's purpose explained
- ✅ Integration points clear

---

### FR10: Common Scenarios
**Requirement**: Provide real-world examples with correct/incorrect paths.

**Scenarios** (minimum 5):
1. ServiceDesk analysis file
2. New Maia agent
3. Analysis database
4. Phase documentation
5. Large dataset (>10 MB)

**Acceptance Criteria**:
- ✅ ≥5 scenarios documented
- ✅ Each shows decision process
- ✅ Correct and incorrect paths shown

---

## Non-Functional Requirements

### NFR1: Readability
- Policy must be scannable (tables, decision trees)
- Information-dense format (not verbose prose)
- Clear headings and structure

**Acceptance Criteria**:
- ✅ Can find answer to "where to save?" in <60 seconds
- ✅ Tables used for complex mappings
- ✅ Decision tree uses 2-step format

---

### NFR2: Token Efficiency
- Target: ~2,500 tokens (~150 lines)
- Use tables instead of prose (60-70% token reduction)
- Avoid verbose examples

**Acceptance Criteria**:
- ✅ Policy ≤3,000 tokens
- ✅ Tables used for file type mappings
- ✅ Examples concise

---

### NFR3: Mandatory Core Loading
- Must be loaded in EVERY new Claude session
- Added to CLAUDE.md and smart_context_loading.md
- Zero exceptions (no conditional loading)

**Acceptance Criteria**:
- ✅ Listed in CLAUDE.md core files
- ✅ Listed in smart_context_loading.md mandatory core
- ✅ Loaded before any agent-specific context

---

### NFR4: Maintenance
- Easy to update when new file types added
- Clear structure for adding categories
- Version tracked in SYSTEM_STATE.md

**Acceptance Criteria**:
- ✅ Table format allows easy row addition
- ✅ Categories clearly defined
- ✅ Version/last updated date included

---

## Performance Requirements

### PERF1: Context Loading Impact
- **Target**: ≤3,000 tokens added to core context
- **Actual**: ~2,500 tokens
- **Impact**: +28% core context (acceptable)

**Acceptance Criteria**:
- ✅ Tokens ≤3,000
- ✅ Load time <100ms
- ✅ No runtime overhead (loaded once per session)

---

### PERF2: Scan Time
- Agent should find answer in <60 seconds
- Decision tree ≤2 steps
- Tables are information-dense

**Acceptance Criteria**:
- ✅ Decision tree answers in 2 steps max
- ✅ Table lookup <30 seconds
- ✅ No need to read entire document

---

## Edge Cases

### EDGE1: File Fits Multiple Categories
**Scenario**: Database that's both operational AND intelligence

**Resolution**: Use primary purpose (intelligence gathering → intelligence/)

**Acceptance Criteria**:
- ✅ Tiebreaker rules documented
- ✅ Primary purpose determines category

---

### EDGE2: File Type Not in Map
**Scenario**: New file type not documented

**Resolution**: Default to `claude/data/` with note to update policy

**Acceptance Criteria**:
- ✅ Default location specified
- ✅ Process for updating policy documented

---

### EDGE3: Work Output That Helps Maia
**Scenario**: Analysis that becomes Maia intelligence database

**Resolution**: Transform workflow (work → Maia system)
1. Initial: `~/work_projects/analysis/report.md`
2. Transform: Extract insights → `claude/data/databases/intelligence/insights.db`

**Acceptance Criteria**:
- ✅ Transformation workflow documented
- ✅ Clear criteria for when to transform

---

## Success Metrics

### Measurable Outcomes:
1. **Agent compliance**: >90% of files saved to correct location
2. **Time to decision**: <60 seconds to find where to save
3. **Policy violations**: <5% of commits blocked by pre-commit hook
4. **Repository size**: No >10 MB files added (except RAG databases)

---

## Test Scenarios

### Test 1: Decision Tree - Work Output
- Input: "ServiceDesk analysis Excel file"
- Expected: `~/work_projects/servicedesk_analysis/`
- Reasoning: Work output (analysis keyword + ServiceDesk pattern)

### Test 2: Decision Tree - Maia Agent
- Input: "New specialist agent definition"
- Expected: `claude/agents/specialist_agent.md`
- Reasoning: Maia system file (agent type)

### Test 3: Size Limit Enforcement
- Input: 154 MB database file
- Expected: Rejected (>10 MB limit)
- Recommendation: `~/work_projects/`

### Test 4: Database Categorization
- Input: `security_intelligence.db`
- Expected: `claude/data/databases/intelligence/`
- Reasoning: Intelligence gathering database

### Test 5: Phase Documentation
- Input: `PHASE_151_COMPLETE.md` (created today)
- Expected: `claude/data/project_status/active/`
- After 30 days: `claude/data/project_status/archive/2025-Q4/`

---

**Status**: ✅ Requirements Complete (Retroactive)
**Next**: Validate implementation against these requirements
