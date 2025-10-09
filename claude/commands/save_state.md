# Save State Command - Comprehensive & Executable

## Overview
Production-ready save state protocol combining comprehensive session analysis with executable workflow. No phantom dependencies, all steps validated by pre-flight checks.

## Implementation Status
- **Current State**: ✅ Production Ready
- **Last Updated**: 2025-10-09 (Phase 103 - SRE Reliability Sprint)
- **Entry Point**: `save_state` command
- **Dependencies**: git, save_state_preflight_checker.py (all validated)
- **Previous Versions**: save_state.md (Oct 3), comprehensive_save_state.md (Oct 1 - archived)

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

2. **README.md**
   - Add new features to relevant sections
   - Update capability descriptions if changed
   - Keep concise (reference SYSTEM_STATE.md for details)

3. **claude/context/tools/available.md**
   - Document new tools with: purpose, capabilities, usage, status
   - Update existing tool documentation if modified
   - Mark deprecated tools clearly

4. **claude/context/core/agents.md**
   - Document new agents or agent enhancements
   - Update agent capabilities if modified
   - Maintain agent catalog consistency

#### 1.3 Session-Specific Documentation (If Applicable)
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

#### 2.2 Dependency Health Check (Optional but Recommended)
```bash
python3 claude/tools/sre/dependency_graph_validator.py --analyze --critical-only
```

**Action if critical phantoms found**: Fix phantom references or mark as known issue

#### 2.3 Documentation Consistency Verification
- Verify all new tools mentioned in SYSTEM_STATE.md are also in available.md
- Verify all new agents mentioned in SYSTEM_STATE.md are also in agents.md
- Check that phase numbers are consistent across files

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

#### 4.3 Create Comprehensive Commit
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

#### 4.4 Push to Remote
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
- [ ] README.md updated if capabilities changed
- [ ] available.md updated if tools added/modified
- [ ] agents.md updated if agents added/modified
- [ ] Session summary created if complex work
- [ ] Design decisions documented if architectural changes
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
# 4. Git commit & push
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
# 7. Git commit with full details & push
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
