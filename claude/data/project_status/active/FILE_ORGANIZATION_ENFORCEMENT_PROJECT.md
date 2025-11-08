# File Organization Enforcement Project

**Last Updated**: 2025-11-07
**Status**: Planning Complete - Ready for Implementation
**Active Agents**: SRE Principal Engineer Agent
**Estimated Duration**: 90 minutes
**Priority**: High (prevents 180 MB repository pollution)

---

## Project Overview

### Problem Statement
Maia repository contains 180+ MB of operational work data (ServiceDesk analysis, Infrastructure team tickets, recruitment tests) mixed with Maia system files, violating UFC principle: "Don't pollute project repos with context files."

**Current State**:
- Repository size: 212 MB (194 MB in `claude/data/` alone - 92%)
- 25+ operational work files in `claude/data/`
- 61 phase documentation files scattered in `claude/data/` root
- 44 databases in `claude/data/` root (not in subdirectories)
- 14 markdown files in repository root (only 4 should exist)

**Target State**:
- Repository size: <30 MB (85% reduction)
- Operational data separated to `~/work_projects/`
- Phase docs archived in `claude/data/project_status/archive/`
- Databases organized in `claude/data/databases/{category}/`
- Root directory: 4 core files only

### Solution Approach
**Layered Enforcement** (defense-in-depth):
1. **Preventive**: Add `file_organization_policy.md` to mandatory core context loading
2. **Runtime**: Create `validate_file_location.py` tool (optional agent use)
3. **Enforcement**: Pre-commit hook prevents policy violations
4. **Documentation**: Add condensed reference to `identity.md`

---

## Phase 1: Create File Organization Policy

**AGENT**: Load SRE Principal Engineer Agent
**Command**: "load sre_principal_engineer_agent"
**Duration**: 30 minutes

### Steps

1. **Create `claude/context/core/file_organization_policy.md`**
   - Decision tree: "Where should I save this file?"
   - Location map table (file type → directory)
   - Size limits (>10 MB → work_projects)
   - Forbidden locations list
   - TDD project file organization
   - Project plan vs. requirements guidance

2. **Add to Mandatory Core Loading**
   - Update `CLAUDE.md` context loading protocol
   - Add to `smart_context_loading.md` always-load core
   - Target: ~150 lines, 2,500 tokens

3. **Test Context Loading**
   - Verify file loads in new context window
   - Check token count impact (+28% acceptable)
   - Measure load time (<100ms acceptable)

**Deliverables**:
- ✅ `claude/context/core/file_organization_policy.md` (150 lines)
- ✅ Updated `CLAUDE.md` (mandatory loading sequence)
- ✅ Updated `smart_context_loading.md` (core context list)

**Save Progress**: Update FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md with Phase 1 completion

---

## Phase 2: Create Validation Tool

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 45 minutes

### Steps

1. **Create `claude/tools/validate_file_location.py`**
   - Function: `validate_file_location(filepath: str, file_purpose: str) -> dict`
   - Checks:
     - Is this work output? → Recommend `~/work_projects/`
     - File size >10 MB? → Reject with policy violation
     - Matches UFC structure? → Suggest compliant path
     - Database not in databases/? → Recommend category
   - Returns: `{valid: bool, recommended_path: str, reason: str, policy_violated: str}`

2. **Add Helper Functions**
   - `is_work_output(file_purpose: str) -> bool`
   - `get_file_size(filepath: str) -> int`
   - `matches_ufc_structure(filepath: str) -> bool`
   - `get_ufc_compliant_path(filepath: str) -> str`
   - `infer_project(filepath: str) -> str`

3. **Create Test Suite**
   - Test work output detection
   - Test size limit enforcement
   - Test UFC structure validation
   - Test recommended path suggestions

4. **Update Documentation**
   - Add to `capability_index.md`
   - Document in `file_organization_policy.md`
   - Usage examples

**Deliverables**:
- ✅ `claude/tools/validate_file_location.py` (~200 lines)
- ✅ `tests/test_validate_file_location.py` (~150 lines)
- ✅ Updated `capability_index.md`

**Save Progress**: Update FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md with Phase 2 completion

---

## Phase 3: Create Pre-Commit Hook

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 30 minutes

### Steps

1. **Create `claude/hooks/pre_commit_file_organization.py`**
   - Check 1: Work outputs in Maia repo (ServiceDesk*, Infrastructure*, Lance*)
   - Check 2: Files >10 MB (except rag_databases/)
   - Check 3: Root directory pollution (only 4 allowed)
   - Check 4: Databases not in databases/ subdirectory
   - Check 5: Phase docs not archived (>30 days old)

2. **Define Allowed Patterns**
   ```python
   ALLOWED_ROOT_FILES = [
       'CLAUDE.md',
       'README.md',
       'SYSTEM_STATE.md',
       'SYSTEM_STATE_ARCHIVE.md'
   ]

   WORK_OUTPUT_PATTERNS = [
       '*ServiceDesk*',
       '*Infrastructure*',
       '*Lance_Letran*',
       '*L2_*'
   ]

   MAX_FILE_SIZE_MB = 10
   ```

3. **Implement Violation Reporting**
   - Print clear error messages
   - Reference `file_organization_policy.md`
   - Suggest correct locations
   - Exit with code 1 to block commit

4. **Configure Git Hook**
   - Add to `.git/hooks/pre-commit` (or document manual setup)
   - Test with sample violations
   - Verify can skip with `--no-verify` if urgent

**Deliverables**:
- ✅ `claude/hooks/pre_commit_file_organization.py` (~150 lines)
- ✅ Hook configuration instructions
- ✅ Test validation suite

**Save Progress**: Update FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md with Phase 3 completion

---

## Phase 4: Execute Cleanup (Optional - User Decision)

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 15 minutes

**NOTE**: This phase moves existing files. Requires user approval before execution.

### Steps

1. **Create Directory Structure**
   ```bash
   mkdir -p ~/work_projects/servicedesk_analysis
   mkdir -p ~/work_projects/infrastructure_team
   mkdir -p ~/work_projects/recruitment
   mkdir -p claude/data/project_status/archive/2025-Q4
   mkdir -p claude/data/databases/{intelligence,system,user,archive}
   ```

2. **Move Operational Data** (if user approves)
   ```bash
   # ServiceDesk analysis (180 MB)
   mv claude/data/servicedesk_tickets.db ~/work_projects/servicedesk_analysis/
   mv claude/data/ServiceDesk_*.xlsx ~/work_projects/servicedesk_analysis/

   # Infrastructure team data
   mv claude/data/Infrastructure_* ~/work_projects/infrastructure_team/
   mv claude/data/Lance_Letran_* ~/work_projects/infrastructure_team/

   # Recruitment tests
   mv claude/data/L2_* ~/work_projects/recruitment/
   ```

3. **Archive Phase Docs** (if user approves)
   ```bash
   # Move phase docs >30 days old
   mv claude/data/PHASE_*.md claude/data/project_status/archive/2025-Q4/
   mv claude/data/*_COMPLETE.md claude/data/project_status/archive/2025-Q4/
   mv claude/data/SESSION_SUMMARY_*.md claude/data/project_status/archive/2025-Q4/
   ```

4. **Organize Databases** (if user approves)
   ```bash
   # Intelligence databases
   mv claude/data/security_intelligence.db claude/data/databases/intelligence/
   mv claude/data/rss_intelligence.db claude/data/databases/intelligence/

   # System databases
   mv claude/data/routing_decisions.db claude/data/databases/system/
   mv claude/data/tool_usage.db claude/data/databases/system/

   # User databases
   mv claude/data/*_naythan.db claude/data/databases/user/
   ```

5. **Clean Root Directory** (if user approves)
   ```bash
   # Move feature status docs
   mv DASHBOARDS_QUICK_START.md claude/data/feature_status/
   mv NGINX_SETUP_COMPLETE.md claude/data/feature_status/

   # Move phase summaries
   mv PHASE_84_85_SUMMARY.md claude/data/project_status/archive/2025-Q3/
   ```

**Deliverables**:
- ✅ Directory structure created
- ✅ Files moved to appropriate locations
- ✅ Repository size reduced by 180 MB (85%)

**Save Progress**: Update FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md with Phase 4 completion

---

## Phase 5: Update Documentation

**AGENT RELOAD**: "load sre_principal_engineer_agent"
**Duration**: 10 minutes

### Steps

1. **Update `.gitignore`**
   ```
   # Operational work outputs (should be in ~/work_projects/)
   claude/data/*ServiceDesk*.xlsx
   claude/data/*Infrastructure*.xlsx
   claude/data/*.csv
   claude/data/servicedesk_tickets.db

   # Temporary analysis files
   claude/data/*_Analysis_*.xlsx
   claude/data/*_Summary_*.md
   ```

2. **Update `identity.md` Working Principles**
   - Add condensed file storage rule (#19)
   - Reference full policy document

3. **Update `SYSTEM_STATE.md`**
   - Add Phase 151 entry
   - Document cleanup results
   - Link to file_organization_policy.md

4. **Update `capability_index.md`**
   - Add validate_file_location tool
   - Add file_organization_policy.md to core context

**Deliverables**:
- ✅ Updated `.gitignore`
- ✅ Updated `identity.md`
- ✅ Updated `SYSTEM_STATE.md` (Phase 151)
- ✅ Updated `capability_index.md`

**Save Progress**: Update FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md with Phase 5 completion

---

## Implementation Sequence

### DISCOVERY MODE (Current State)
Present this plan to user for approval before execution.

**User Decision Points**:
1. **Approve layered approach?** (Phases 1-3 + 5)
2. **Execute cleanup now?** (Phase 4 - optional)
3. **Which cleanup steps?** (operational data, phase docs, databases, root cleanup)

### EXECUTION MODE (After Approval)
Execute approved phases autonomously with progress tracking.

**Workflow**:
1. User says "yes" / "do it" / "proceed with Phase 1-3"
2. Load SRE Principal Engineer Agent
3. Execute Phase 1 → Save progress
4. Execute Phase 2 → Save progress
5. Execute Phase 3 → Save progress
6. Execute Phase 5 → Save progress
7. Commit all changes to git

---

## Success Metrics

### Before Implementation
- Repository size: 212 MB
- `claude/data/` files: 207+ in root directory
- Operational data: Mixed with Maia system data
- Databases: 44 scattered files
- Root directory: 14 markdown files

### After Implementation (Target)
- Repository size: **<30 MB** (85% reduction)
- `claude/data/` files: **<50 in root** (organized subdirectories)
- Operational data: **Separated to ~/work_projects/**
- Databases: **44 files in categorized subdirectories**
- Root directory: **4 core files only**

### Performance Impact
- Context loading: +2,500 tokens (+28%, acceptable)
- Session start: +50ms (one-time)
- Commit time: +100-200ms (pre-commit hook)
- Response latency: 0ms (no runtime overhead)

---

## Risk Mitigation

### Risk 1: Policy File Too Large
**Mitigation**: Keep <150 lines using tables and decision trees (information dense)

### Risk 2: Agents Ignore Policy
**Mitigation**: Mandatory core loading + pre-commit hook enforcement

### Risk 3: Performance Degradation
**Mitigation**: Optional validation tool (not mandatory hook), git-time enforcement only

### Risk 4: Breaking Tool Code
**Mitigation**: Phase 4 cleanup is optional, can be done incrementally

### Risk 5: User Workflow Disruption
**Mitigation**: Phase 4 requires explicit approval, can skip if not ready

---

## Rollback Plan

If implementation causes issues:

1. **Remove from mandatory loading**:
   - Comment out in `CLAUDE.md`
   - Remove from `smart_context_loading.md`

2. **Disable pre-commit hook**:
   - Remove `.git/hooks/pre-commit`
   - Or use `git commit --no-verify`

3. **Restore files** (if Phase 4 executed):
   - Copy back from `~/work_projects/`
   - Git revert cleanup commits

**Recovery Time**: <5 minutes

---

## Session Resumption

**If interrupted, resume with**:

1. Read this file: `claude/data/project_status/active/FILE_ORGANIZATION_ENFORCEMENT_PROJECT_progress.md`
2. Load agent: "load sre_principal_engineer_agent"
3. Check completed phases
4. Continue from next incomplete phase

**Context**: Implementing file organization policy with layered enforcement (preventive + runtime + git-time) to prevent 180 MB repository pollution and maintain UFC structure compliance.

---

## Files to Create/Modify

### Create (3 files)
- `claude/context/core/file_organization_policy.md` (~150 lines)
- `claude/tools/validate_file_location.py` (~200 lines)
- `claude/hooks/pre_commit_file_organization.py` (~150 lines)

### Modify (5 files)
- `CLAUDE.md` (add to mandatory loading)
- `claude/context/core/smart_context_loading.md` (add to core)
- `claude/context/core/identity.md` (add working principle)
- `SYSTEM_STATE.md` (Phase 151 entry)
- `claude/context/core/capability_index.md` (add tool)

### Optional Cleanup (Phase 4)
- Move ~25 operational files
- Archive ~61 phase docs
- Organize ~44 databases
- Clean ~10 root files

**Total New Code**: ~500 lines
**Total Documentation**: ~200 lines

---

## Next Steps

**Awaiting User Decision**:
1. Approve Phases 1-3 + 5? (create policy, tool, hook, documentation)
2. Execute Phase 4 cleanup? (move files to organize repository)
3. Any modifications to approach?

**Ready to Execute**: All phases designed and documented, awaiting approval to proceed.
