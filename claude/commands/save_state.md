# Save State Command - Tiered Approach

## Overview
Production-ready save state protocol with three tiers optimizing for different use cases:
- **Tier 1**: Quick checkpoint (2-3 min) - Incremental progress
- **Tier 2**: Standard save state (10-15 min) - End of session
- **Tier 3**: Comprehensive save state (30-45 min) - Major phases, releases

## Implementation Status
- **Current State**: ✅ Production Ready with Tiered Options
- **Last Updated**: 2025-10-15 (Phase 119 - Capability Amnesia Fix)
- **Entry Point**: Choose tier based on context (see Quick Tier Selection below)
- **Dependencies**: git, save_state_preflight_checker.py, save_state_security_checker.py
- **Previous Versions**: save_state.md (Oct 9), comprehensive_save_state.md (Oct 1 - archived)

---

## ⚡ Quick Tier Selection

### Tier 1: Quick Checkpoint (2-3 min) - `ss-quick`
**When**: Making incremental progress, multiple checkpoints per session, still in flow state
**Files**: SYSTEM_STATE.md (bullet point), capability_index.md (if new capability)
**Command**: See [save_state_tier1_quick.md](save_state_tier1_quick.md)
**Skips**: Pre-flight, security checks, README, available.md, agents.md
**Use Case**: "Just made progress, want to checkpoint before continuing"

### Tier 2: Standard Save State (10-15 min) - `ss-std`
**When**: End of work session, completing logical unit of work
**Files**: SYSTEM_STATE.md (full entry), capability_index.md, README (if needed), security check
**Command**: See [save_state_tier2_standard.md](save_state_tier2_standard.md)
**Skips**: Pre-flight, available.md/agents.md (unless major changes), session summaries
**Use Case**: "Done for now, want to document what I accomplished"

### Tier 3: Comprehensive Save State (30-45 min) - `ss-full`
**When**: End of major phase, weekly review, architecture changes, pre-release validation
**Files**: All documentation + validation + comprehensive testing
**Command**: This file (full protocol below)
**Skips**: Nothing - full validation and documentation
**Use Case**: "Major milestone complete, need comprehensive documentation and validation"

---

## Quick Decision Tree

```
Are you done with this session?
├─ No → Still working
│   └─ Made progress you want to checkpoint?
│       └─ Yes → **Tier 1** (2-3 min)
│
└─ Yes → Done for now
    └─ Is this a major milestone or phase completion?
        ├─ No → Normal end of session
        │   └─ **Tier 2** (10-15 min)
        │
        └─ Yes → Major phase/release
            └─ **Tier 3** (30-45 min, this file)
```

---

## Tier 3: Comprehensive Save State (Full Protocol)

---

## Pre-Flight Validation (MANDATORY)

**Before ANY save state operation, run**:
```bash
python3 claude/tools/sre/save_state_preflight_checker.py --check
```

**What it checks** (143 automated validations):
- Tool existence (detects phantom dependencies)
- Git status and configuration
- Write permissions for critical files
- Disk space (minimum 1GB)
- System readiness

**If pre-flight fails**: Fix issues before proceeding. **Do not bypass.**

---

## Execution Sequence

### Phase 0: Project Recovery Setup (For Multi-Phase Projects)

**When to use**: Starting a new multi-phase project (3+ phases, >2 hours duration)

**Purpose**: Generate comprehensive recovery files to prevent context compaction drift

**Time**: <5 minutes (one-time per project)

#### 0.1 Generate Recovery Files
```bash
# Interactive mode (recommended for first time)
python3 claude/templates/project_recovery/generate_recovery_files.py --interactive

# Or use config file (faster for repeat use)
python3 claude/templates/project_recovery/generate_recovery_files.py --example-config
nano project_config_example.json
python3 claude/templates/project_recovery/generate_recovery_files.py --config project_config_example.json
```

**What it generates**:
- `PROJECT_ID.md` - Comprehensive project plan (100-500 lines)
- `PROJECT_ID_RECOVERY.json` - Quick recovery state
- `implementation_checkpoints/PROJECT_ID_START_HERE.md` - Recovery entry point

#### 0.2 Review Generated Files
```bash
# Open and review the project plan
open claude/data/YOUR_PROJECT_ID/YOUR_PROJECT_ID.md

# Verify recovery JSON is valid
python3 -m json.tool claude/data/YOUR_PROJECT_ID/YOUR_PROJECT_ID_RECOVERY.json

# Read START_HERE guide
cat claude/data/YOUR_PROJECT_ID/implementation_checkpoints/YOUR_PROJECT_ID_START_HERE.md
```

#### 0.3 Fill in TBD Sections
Edit the generated project plan to complete:
- Architecture description
- Success metrics details
- Test scenarios
- Validation criteria

#### 0.4 Commit Recovery Files
```bash
git add claude/data/YOUR_PROJECT_ID/
git commit -m "📋 Phase 0: Project recovery files for [PROJECT_NAME]

Generated comprehensive recovery protection:
- Project plan with phase-by-phase guide
- Quick recovery JSON for 30-second status checks
- START_HERE guide with recovery sequence

Prevents context compaction drift and project amnesia.
Estimated recovery time: <5 min (vs 15-30 min without protection)"
```

**Skip Phase 0 when**:
- Single-phase project (<1 hour)
- Simple bug fix or small enhancement
- Work will complete in one session

**See**: `claude/templates/project_recovery/README.md` for complete documentation

---

### Phase 1: Session Analysis & Documentation Updates

#### 1.1 Session Context Analysis (Manual)
Review and document:
- What was accomplished this session?
- What problems were solved?
- What design decisions were made? (capture in JSON if significant)
- What changed in the system?

#### 1.2 Critical Documentation Updates (MANDATORY)
Update these files with session changes:

1. **SYSTEM_STATE.md**
   - Update **Current Phase** number
   - Add new phase section with: Achievement, Problem Context, Implementation Details, Metrics
   - Update **Last Updated** date
   - Document new files created, tools built, capabilities added

2. **claude/context/core/capability_index.md** ⭐ **CRITICAL - MAIA AWARENESS**
   - Add entry to "Recent Capabilities" for NEW tools/agents (if created this session)
   - Include: name, location, purpose, core capabilities, usage, status
   - **Purpose**: Maia ALWAYS loads this file - if not updated, Maia won't know tool exists
   - **Format**: Follow existing Phase entries (comprehensive single-bullet format)
   - **Impact**: Without this, users will ask "how do I X?" and Maia says "I don't know"
   - **Skip**: Only if NO new capabilities added (modifications to existing tools don't need new entry)

3. **README.md**
   - Add new features to relevant sections
   - Update capability descriptions if changed
   - Keep concise (reference SYSTEM_STATE.md for details)

4. **claude/context/tools/available.md**
   - Document new tools with: purpose, capabilities, usage, status
   - Update existing tool documentation if modified
   - Mark deprecated tools clearly

5. **claude/context/core/agents.md**
   - Document new agents or agent enhancements
   - Update agent capabilities if modified
   - Maintain agent catalog consistency

#### 1.3 Project Recovery JSON Update (If Using Phase 0)
**If this session is part of a multi-phase project with recovery files**:

Update the recovery JSON with current progress:
```bash
# Example: Update current_phase and phase_progress
nano claude/data/YOUR_PROJECT_ID/YOUR_PROJECT_ID_RECOVERY.json
```

Update fields:
- `current_phase`: Current phase number
- `phase_progress.phase_N.started`: Start date (if just started)
- `phase_progress.phase_N.completed`: Completion date (if just finished)
- `phase_progress.phase_N.deliverable_exists`: true/false
- `phase_progress.phase_N.notes`: Key notes about completion

**Example**:
```json
{
  "current_phase": 3,
  "phase_progress": {
    "phase_2": {
      "started": "2025-10-15",
      "completed": "2025-10-15",
      "deliverable_exists": true,
      "notes": "Dashboard operational on port 8063"
    }
  }
}
```

**Why important**: Enables <5 min recovery after context compaction (vs 15-30 min without)

#### 1.4 Session-Specific Documentation (If Applicable)
- Create session summary in `claude/context/session/` for complex work
- Document design decisions in `claude/context/session/decisions/` (JSON format)
- Update command documentation if workflows changed

**Design Decision Template** (if needed):
```json
{
  "decision_id": "phase_NNN_decision_N",
  "date": "2025-MM-DD",
  "title": "Decision Title",
  "context": "Why was this decision needed?",
  "alternatives_considered": ["Option A", "Option B", "Option C"],
  "chosen_solution": "Option B",
  "rationale": "Why Option B was chosen",
  "trade_offs": "What we gave up choosing Option B",
  "validation": "How we know this was the right choice"
}
```

---

### Phase 2: Anti-Sprawl & System Validation

#### 2.1 Anti-Sprawl Validation
Check for common sprawl patterns:

```bash
# Check experimental directory for old files (>7 days)
find claude/extensions/experimental -type f -mtime +7 2>/dev/null | head -5

# Check for naming violations in production
find claude/tools claude/agents claude/commands -type f \
  \( -name "*_v[0-9]*" -o -name "*_new*" -o -name "*_old*" \) 2>/dev/null | head -5
```

**Action if violations found**: Clean up before commit (graduate to production or archive)

#### 2.2 Comprehensive System Health Check ⭐ **PHASE 103 WEEK 3 - AUTOMATED**
```bash
python3 claude/tools/sre/automated_health_monitor.py
```

**What it checks** (4 comprehensive validations):
1. **Dependency Health**: Phantom tool detection, dependency graph integrity
2. **RAG System Health**: Data freshness, availability, document counts
3. **Service Health**: LaunchAgent availability, failed services
4. **UFC Compliance**: Directory nesting, file naming, structure validation

**Exit codes**:
- 0 = HEALTHY (all checks pass)
- 1 = WARNING/DEGRADED (warnings but no critical issues)
- 2 = CRITICAL (critical issues found, review required)

**Action if CRITICAL**: Review critical issues and fix before proceeding with commit

#### 2.2.1 File Organization Compliance Check ⭐ **PHASE 151.1 - NEW**
```bash
python3 claude/tools/sre/file_organization_checker.py --check
```

**What it checks** (5 comprehensive validations):
1. **Root Directory**: Only 4 core files allowed (CLAUDE.md, README.md, SYSTEM_STATE.md, SYSTEM_STATE_ARCHIVE.md)
2. **Work Output Separation**: No work outputs in Maia repository (must be in ~/work_projects/)
3. **File Size Limits**: Files >10 MB must be in ~/work_projects/ (except RAG databases)
4. **Database Categorization**: All .db files in claude/data/databases/{category}/ subdirectories
5. **Phase Documentation**: Identifies phase docs >30 days old for archival

**Exit codes**:
- 0 = PASSED (compliant)
- 1 = WARNINGS (non-blocking, but should address)
- 2 = CRITICAL (violations block save state until fixed)

**Action if CRITICAL**: Review violations and fix before proceeding with commit
- Root violations: Move files to appropriate subdirectories
- Work outputs: Move to ~/work_projects/
- Large files: Move to ~/work_projects/ or delete
- Databases: Move to claude/data/databases/{category}/

**Alternative: Individual checks** (if automated monitor unavailable):
```bash
# UFC Compliance only
python3 claude/tools/security/ufc_compliance_checker.py --check

# Dependency Health only
python3 claude/tools/sre/dependency_graph_validator.py --analyze --critical-only

# RAG Health only
python3 claude/tools/sre/rag_system_health_monitor.py --dashboard

# Service Health only
python3 claude/tools/sre/launchagent_health_monitor.py --dashboard

# File Organization only
python3 claude/tools/sre/file_organization_checker.py --check
```

#### 2.4 Documentation Consistency Verification
- Verify all new tools mentioned in SYSTEM_STATE.md are also in available.md
- Verify all new agents mentioned in SYSTEM_STATE.md are also in agents.md
- Check that phase numbers are consistent across files
- **If using project recovery files**: Verify recovery JSON is updated with current phase progress

---

### Phase 3: Implementation Tracking Integration

#### 3.1 Active Implementations Check (If Applicable)
If using universal implementation tracker:
```bash
python3 claude/tools/📊_data/universal_implementation_tracker.py list 2>/dev/null || echo "No active implementations"
```

#### 3.2 Implementation Checkpoints
- Save current state of any active implementations
- Document next steps in session recovery file
- Ensure implementation can be resumed in next session

---

### Phase 4: Git Integration (MANDATORY)

#### 4.1 Review Changes
```bash
git status
git diff --stat
```

**Review**:
- Are all intended changes staged?
- Are there unexpected changes?
- Should any files be excluded?

#### 4.2 Stage Changes
```bash
git add -A
```

**Or selective staging**:
```bash
git add SYSTEM_STATE.md
git add README.md
git add claude/context/tools/available.md
git add claude/context/core/agents.md
git add [other specific files]
```

#### 4.3 Context Compaction (Optional - Long Sessions) ⭐ **PHASE 126 - CONVERSATION LENGTH PROTECTION**

**When to use**: Sessions with 50+ messages OR received "Prompt is too long" / "Conversation too long" errors

**Why safe now** (Phase 120 protection):
- Project recovery files preserve complete project state
- SYSTEM_STATE.md documents full session context
- Anti-breakage protocol prevents accidental cleanup
- capability_index.md preserves tool/agent knowledge

**Execute**:
```
/compact
```

**Validation immediately after compaction**:
1. Test recall: "What phase are we on? What did we just accomplish?"
2. Check recovery: Can you load project from recovery files if they exist?
3. Verify context: SYSTEM_STATE.md + capability_index.md provide complete picture?

**Expected result**: Conversation compacted, but you can resume work seamlessly from documentation

**If compaction fails with "Conversation too long"**:
- Execute save state WITHOUT compaction
- Start new conversation
- Load from recovery files: `claude/data/PROJECT_ID/PROJECT_ID_START_HERE.md`
- Resume from checkpoint with fresh context

**Skip if**: Session <50 messages AND no length warnings

---

#### 4.4 Security Validation (MANDATORY) ⭐ **PHASE 113 - AUTOMATED THREAT PREVENTION**
**Run security checks before commit to prevent accidentally creating threats**:
```bash
python3 claude/tools/sre/save_state_security_checker.py --verbose
```

**What it checks** (4 automated security validations):
1. **Secret Detection**: API keys, passwords, tokens, private keys (8 patterns)
2. **Critical Vulnerabilities**: Recent scans for critical CVEs
3. **Code Security**: Bandit high-severity issues in Python files
4. **Compliance**: UFC system validation

**Exit codes**:
- 0 = ✅ PASSED (clean, commit allowed)
- 1 = ❌ BLOCKED (critical issues found, fix before commit)

**Action if BLOCKED**:
- Review security findings displayed
- Fix critical issues (remove secrets, fix vulnerabilities)
- Re-run security check
- **Do NOT bypass security gate**

**Security notes added to commit**: Warnings automatically added to commit message

#### 4.4.1 Database Sync ⭐ **PHASE 192 - AUTOMATED**
**Status**: ✅ **Automatic via Git Hook** (Phase 192)

**How it works**:
- Git post-commit hook automatically triggers ETL sync
- Runs asynchronously in background (<100ms overhead)
- Daily backup at 2 AM via LaunchAgent (safety net)

**What happens automatically**:
- Parses SYSTEM_STATE.md for recent 10 phases
- Extracts problems, solutions, metrics, files
- Upserts to system_state.db
- Logs to `~/.maia/logs/etl_sync_*.log`

**Manual trigger** (if needed):
```bash
python3 claude/tools/sre/system_state_etl.py --recent 10
```

**No action required** - Git commit handles everything

#### 4.4.2 Capabilities Discovery ⭐ **PHASE 192 - ENHANCED**
**Status**: ✅ **100% Coverage** (Phase 192)

**Improvements**:
- Recursive scanning finds ALL tools (478/478 = 100%)
- Discovery hint always visible in guaranteed minimum context
- Confluence tools: 18/18 found (was 3/18)
- Database optimized with WAL mode

**Manual rescan** (optional):
```bash
python3 claude/tools/sre/capabilities_registry.py scan
```

**When to rescan**:
- After adding new tools/agents (optional - discovery is dynamic)
- After major refactoring (to update categories/metadata)

**No regular action required** - capabilities auto-discovered

#### 4.5 Create Comprehensive Commit
```bash
git commit -m "$(cat <<'EOF'
[EMOJI] PHASE NNN: [Title] - [Subtitle]

## Achievement
[One-line summary of what was accomplished]

## Problem Solved
[What problem did this solve? Why was it needed?]

## Implementation Details
[Key technical details, files created, metrics]

## Files Created/Modified
- file1.py (purpose)
- file2.md (purpose)
- file3.json (purpose)

## Metrics/Results
[Quantitative results, performance metrics, validation]

## Status
✅ [Status] - [Next steps if applicable]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Commit Message Guidelines**:
- Use emoji that represents the work (🛡️ SRE, 🧠 AI, 📊 data, 🔧 fix, ✨ feature)
- Be specific about phase number and achievement
- Include quantitative metrics when available
- Reference problem context (why this was needed)

#### 4.6 Push to Remote
```bash
git push
```

**If push fails**: Resolve conflicts, rebase if needed, try again

---

### Phase 5: Completion Verification

#### 5.1 Verify Clean Working Directory
```bash
git status
```

**Expected**: "working tree clean" or only untracked files remaining

#### 5.2 Documentation Audit Checklist
- [ ] SYSTEM_STATE.md updated with current phase
- [ ] **capability_index.md updated if NEW tools/agents created** ⭐ **CRITICAL**
- [ ] README.md updated if capabilities changed
- [ ] available.md updated if tools added/modified
- [ ] agents.md updated if agents added/modified
- [ ] Session summary created if complex work
- [ ] Design decisions documented if architectural changes
- [ ] **Security validation passed (Phase 113)**
- [ ] ~~**Database sync completed**~~ ⭐ **AUTOMATED** (Phase 192 - git hook)
- [ ] ~~**Capabilities scan completed**~~ ⭐ **AUTOMATED** (Phase 192 - 100% coverage)
- [ ] Git commit created with comprehensive message
- [ ] Git push successful
- [ ] Anti-sprawl validation passed
- [ ] No phantom dependencies introduced

#### 5.3 Success Confirmation
**Confirm these statements are true**:
- ✅ All system changes are documented
- ✅ Phase progression is clearly marked
- ✅ New capabilities are accurately described
- ✅ Git history captures complete change context
- ✅ Next session can resume without context loss
- ✅ Pre-flight checks would pass for next save state

---

## Quick Reference

### Minimal Save State (Simple Changes)
```bash
# 1. Pre-flight check
python3 claude/tools/sre/save_state_preflight_checker.py --check

# 2. Update SYSTEM_STATE.md (add phase entry)
# 3. Update README.md if needed
# 4. Security validation (Phase 113)
python3 claude/tools/sre/save_state_security_checker.py --verbose

# 5. Database sync (Phase 179 - if phase updates)
python3 claude/tools/sre/system_state_etl.py --recent 10

# 6. Capabilities scan (Phase 179 - if tool/agent changes)
python3 claude/tools/sre/capabilities_registry.py scan

# 7. Git commit & push
git add -A
git commit -m "[EMOJI] PHASE NNN: [Title]"
git push
```

### Comprehensive Save State (Complex Changes)
```bash
# 1. Pre-flight check
python3 claude/tools/sre/save_state_preflight_checker.py --check

# 2. Update all documentation (SYSTEM_STATE, README, available.md, agents.md)
# 3. Create session summary in claude/context/session/
# 4. Document design decisions if applicable
# 5. Run anti-sprawl validation
# 6. Check dependency health
# 7. Security validation (Phase 113 - MANDATORY)
python3 claude/tools/sre/save_state_security_checker.py --verbose

# 8. Database sync (Phase 179 - if phase updates)
python3 claude/tools/sre/system_state_etl.py --recent 10

# 9. Capabilities scan (Phase 179 - if tool/agent changes)
python3 claude/tools/sre/capabilities_registry.py scan

# 10. Git commit with full details & push
```

---

## Error Handling

### Pre-Flight Check Fails
**Symptom**: save_state_preflight_checker.py returns exit code 1
**Action**: Review failed checks, fix issues, run pre-flight again
**Do NOT**: Proceed with save state if critical checks fail

### Phantom Dependency Introduced
**Symptom**: Dependency validator shows new phantom tools
**Action**: Either build the missing tool or remove the reference
**Prevention**: Run `python3 claude/tools/sre/save_state_preflight_checker.py --check` before commit

### Git Push Fails
**Symptom**: `git push` returns error (conflicts, authentication, network)
**Action**:
- **Conflicts**: `git pull --rebase`, resolve conflicts, `git push`
- **Authentication**: Check GitHub credentials, update if needed
- **Network**: Retry when connection restored

### Security Check Blocked Commit ⭐ **NEW - PHASE 113**
**Symptom**: save_state_security_checker.py returns exit code 1 (blocked)
**Action**:
- **Secrets Detected**: Remove API keys, passwords, tokens from staged files
- **Critical CVEs**: Fix vulnerabilities or defer commit until resolved
- **Code Security**: Fix high-severity Bandit issues in Python code
- **Compliance**: Address critical UFC violations
**Prevention**: Run security scans regularly during development, not just at commit time

### Documentation Inconsistency
**Symptom**: New tool mentioned in SYSTEM_STATE.md but not in available.md
**Action**: Add tool documentation to available.md
**Prevention**: Use Phase 5.2 checklist before committing

---

## Differences from Previous Versions

### vs save_state.md (Oct 3)
**Added**:
- ✅ Session analysis and design decision capture
- ✅ Mandatory pre-flight validation
- ✅ Session-specific documentation guidance
- ✅ Dependency health checking

**Kept**:
- ✅ Anti-sprawl validation (working feature)
- ✅ Implementation tracking integration
- ✅ Practical execution steps

### vs comprehensive_save_state.md (Oct 1 - ARCHIVED)
**Removed**:
- ❌ Dependency on design_decision_capture.py (doesn't exist)
- ❌ Dependency on documentation_validator.py (doesn't exist)
- ❌ Automated Stage 2 compliance audit (tool missing)

**Replaced with**:
- ✅ Manual design decision capture (JSON template)
- ✅ Pre-flight checker validation (actual tool)
- ✅ Dependency graph validator (actual tool)

**Result**: Comprehensive scope + executable steps = no phantom dependencies

---

## Integration Points

### With SRE Tools (Phase 103)
- **Pre-Flight Checker**: Mandatory before all save state operations
- **Dependency Validator**: Optional but recommended for dependency health
- **LaunchAgent Monitor**: Use to document service status if applicable

### With UFC System
- **Context Files**: Updates maintain UFC system structure
- **Session Files**: Follow UFC organization in `claude/context/session/`
- **Compliance**: Anti-sprawl validation enforces UFC principles

### With Implementation Tracking
- **Universal Tracker**: Preserve active implementation contexts
- **Session Recovery**: Create recovery files for complex work
- **Checkpoint System**: Enable seamless continuation in next session

---

## Success Criteria

### Complete Success ✅
- All documentation updated
- Pre-flight checks passed
- Git commit created with comprehensive message
- Git push successful
- Working directory clean
- No phantom dependencies introduced
- System state fully preserved

### Partial Success ⚠️
- Documentation updated
- Git commit created
- But: push failed (network) or minor issues remaining
- **Action**: Resolve issues and complete push

### Failure ❌
- Pre-flight checks failed and not resolved
- Critical documentation missing
- Phantom dependencies introduced
- Git operations failed completely
- **Action**: Do not proceed, fix issues first

---

## Meta

**This protocol is**:
- ✅ Comprehensive (session analysis, design decisions)
- ✅ Executable (no phantom dependencies, all tools validated)
- ✅ Validated (pre-flight checks prevent failures)
- ✅ Practical (works for both simple and complex changes)
- ✅ Maintainable (clear steps, error handling, success criteria)

**Based on lessons learned**:
- User feedback: *"save state should always be comprehensive, otherwise you forget/don't find some of your tools"*
- SRE principle: Fail fast with clear errors vs silent failures
- Architecture audit: 42% phantom dependency rate requires validation
- Phase 103: Observability and reliability gates are mandatory

**Status**: ✅ Production Ready - Use this protocol for all future save state operations
