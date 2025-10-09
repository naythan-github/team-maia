# System Architecture Review - Prompt for New Context Window

## Your Mission

Review Maia's system architecture for **inconsistencies, broken references, and documentation gaps**. Look for patterns of tools/processes that are documented but don't actually exist, or exist but aren't documented properly.

---

## Background Context

**Current Phase**: 102 (Conversation Persistence System just completed)
**System Status**: Operational but documentation/reality mismatches discovered during comprehensive save state process

**What Happened**: During Phase 101/102 implementation, user requested "save state" and expected comprehensive documentation updates following `comprehensive_save_state.md` protocol. When attempting to follow that protocol, discovered:

1. **Missing Tools**: `design_decision_capture.py` and `documentation_validator.py` referenced in multiple places but don't exist
2. **Unused Tools**: `ufc_compliance_checker.py` exists but wasn't integrated into save state process
3. **Dual Protocols**: Two save state commands (`save_state.md` vs `comprehensive_save_state.md`) with unclear relationship

**User's Key Insight**: *"save state should always be comprehensive, otherwise you forget/don't find some of your tools"*

This review should find similar issues across the entire system.

---

## Specific Issues Discovered (Use as Examples)

### Issue 1: Phantom Tools (Documented but Missing)

**Files to Check**:
- `claude/context/tools/available.md` (1,522 lines - tool inventory)
- `claude/commands/*.md` (command documentation)

**Pattern Found**:
```
available.md says:
  "design_decision_capture - Structured framework for capturing design decisions"

Reality:
  $ find . -name "design_decision_capture.py"
  (no results)

Referenced in: comprehensive_save_state.md, design_decision_audit.md, available.md
```

**What to Look For**:
- Tools listed in `available.md` that don't exist in `claude/tools/`
- Commands in `claude/commands/` that reference non-existent scripts
- Agents in `claude/context/core/agents.md` that have no corresponding file

**Search Commands**:
```bash
# Extract tool names from available.md
grep -E "^\*\*[a-z_]+\.py\*\*" claude/context/tools/available.md

# Check if they exist
find claude/tools -name "tool_name.py"

# Find all .py references in commands
grep -r "\.py" claude/commands/ | grep -v "^Binary"
```

---

### Issue 2: Dual/Conflicting Documentation

**Pattern Found**:
- `claude/commands/save_state.md` - Simpler protocol (5 phases)
- `claude/commands/comprehensive_save_state.md` - Advanced protocol (5 stages, requires missing tools)

**Questions**:
- Which one is the "real" save state process?
- Why are there two?
- Should they be merged or clearly differentiated?

**What to Look For**:
- Multiple commands/docs doing the same thing
- Outdated vs current versions not clearly marked
- Conflicting instructions (e.g., "do X" in one place, "do Y" in another)

**Search Commands**:
```bash
# Find duplicate command names
ls claude/commands/*.md | xargs basename -s .md | sort | uniq -d

# Find files with similar names
ls claude/tools/*.py | grep -E "_v[0-9]|_new|_old|_backup"
```

---

### Issue 3: Broken Integration Points

**Pattern Found**:
- `comprehensive_save_state.md` Stage 2 says: "Execute `design_decision_capture.py audit`"
- Tool doesn't exist → Stage 2 can't be executed
- Process documented but not operational

**What to Look For**:
- Workflows that depend on missing tools
- Agent orchestrations referencing non-existent agents
- Hooks calling scripts that don't exist
- Commands with broken dependency chains

**Search Commands**:
```bash
# Find Python script calls in markdown
grep -r "python3.*\.py" claude/commands/ claude/context/

# Check if referenced scripts exist
# (manual verification needed)
```

---

### Issue 4: Undocumented but Critical Tools

**Pattern Found**:
- `ufc_compliance_checker.py` exists at `claude/tools/security/ufc_compliance_checker.py`
- Has JSON output from 2025-01-07 in `claude/context/session/`
- BUT wasn't mentioned in save state execution
- Found violations (6-level nesting in MCP directories) that weren't addressed

**What to Look For**:
- Tools in `claude/tools/` not listed in `available.md`
- Agents in `claude/agents/` not in `agents.md`
- Commands in `claude/commands/` without documentation
- Background services/LaunchAgents without user-facing docs

**Search Commands**:
```bash
# Count tools in directory
find claude/tools -name "*.py" -type f | wc -l

# Count tools documented
grep -c "\.py" claude/context/tools/available.md

# Find undocumented tools
# (requires cross-reference script)
```

---

## Your Review Checklist

### 1. Tool Inventory Audit (High Priority)

**Check**: `claude/context/tools/available.md` against actual `claude/tools/` directory

**Questions**:
- [ ] How many tools are documented in available.md?
- [ ] How many .py files exist in claude/tools/ (recursively)?
- [ ] Which tools are documented but missing?
- [ ] Which tools exist but aren't documented?
- [ ] Are tool descriptions accurate? (check a sample of 10)

**Deliverable**: List of phantom tools and undocumented tools

---

### 2. Agent Inventory Audit (High Priority)

**Check**: `claude/context/core/agents.md` against `claude/agents/` directory

**Questions**:
- [ ] How many agents are documented?
- [ ] How many agent files exist?
- [ ] Which agents are documented but have no file?
- [ ] Which agent files exist but aren't documented?
- [ ] Check "Status" field accuracy (sample 5 agents)

**Deliverable**: List of phantom agents and undocumented agents

---

### 3. Command Inventory Audit (Medium Priority)

**Check**: Commands in `claude/commands/` for completeness

**Questions**:
- [ ] Are there duplicate/similar commands? (list them)
- [ ] Which commands reference non-existent scripts?
- [ ] Which commands have "Status: Deployed" but dependencies missing?
- [ ] Are there _old, _new, _v1 files that should be cleaned up?

**Deliverable**: List of broken commands and duplicates

---

### 4. Save State Process Reconciliation (High Priority)

**Check**: `save_state.md` vs `comprehensive_save_state.md`

**Questions**:
- [ ] What are the differences between the two?
- [ ] Which dependencies exist vs missing for comprehensive version?
- [ ] What was actually followed for Phase 101/102?
- [ ] Should these be merged or clearly differentiated?
- [ ] Which one should be the "official" process?

**Deliverable**: Recommendation on save state process (merge, choose one, or clarify both)

---

### 5. Hook System Audit (Medium Priority)

**Check**: `claude/hooks/` directory for completeness

**Questions**:
- [ ] Which hooks reference non-existent scripts?
- [ ] Are all hooks documented in context/core docs?
- [ ] Check `user-prompt-submit` - are all stages documented?
- [ ] Are hook dependencies available?

**Deliverable**: List of broken hook integrations

---

### 6. RAG Systems Audit (Medium Priority)

**Check**: Multiple RAG systems (email, meeting, system_state, conversation, multi_collection)

**Questions**:
- [ ] How many RAG systems exist? List them with locations
- [ ] Are they all documented in available.md?
- [ ] Are storage locations documented? (~/.maia/*)
- [ ] Check for duplicate/overlapping functionality
- [ ] Are they all operational? (check for missing dependencies)

**Deliverable**: RAG system inventory with status

---

### 7. LaunchAgent/Background Services Audit (Low Priority)

**Check**: macOS LaunchAgents and background services

**Questions**:
- [ ] Which LaunchAgents are configured? (check ~/Library/LaunchAgents/)
- [ ] Are they documented in available.md or README.md?
- [ ] Are they actually running? (launchctl list | grep maia)
- [ ] Do the scripts they call exist?

**Deliverable**: List of LaunchAgents with documentation status

---

### 8. Documentation Cross-Reference Check (Low Priority)

**Check**: Major documentation files for consistency

**Files to Compare**:
- `README.md` (user-facing capabilities)
- `SYSTEM_STATE.md` (current phase, recent work)
- `claude/context/tools/available.md` (tool inventory)
- `claude/context/core/agents.md` (agent inventory)

**Questions**:
- [ ] Does README.md mention all major capabilities?
- [ ] Is SYSTEM_STATE.md up to date (should be Phase 102)?
- [ ] Are Phase 101/102 documented in all three places?
- [ ] Spot check 5 recent phases - are they consistent across docs?

**Deliverable**: Documentation inconsistencies found

---

## Output Format

Please provide your findings in this structure:

```markdown
# Maia System Architecture Review - Findings

**Review Date**: [DATE]
**Reviewer**: [New Context Window]
**Scope**: Complete system architecture audit

---

## Executive Summary

- **Total Issues Found**: [NUMBER]
- **Critical Issues**: [NUMBER] (missing core tools, broken integrations)
- **Medium Issues**: [NUMBER] (documentation gaps, duplicates)
- **Low Issues**: [NUMBER] (minor inconsistencies)

**Key Finding**: [1-2 sentence summary of biggest problem]

---

## Critical Issues (Fix Immediately)

### Issue 1: [Title]
**Type**: [Phantom Tool | Broken Integration | etc.]
**Impact**: [What breaks because of this]
**Evidence**:
- File: [path]
- Expected: [what should exist]
- Reality: [what actually exists]
**Recommendation**: [Specific fix needed]

[Repeat for each critical issue]

---

## Medium Priority Issues

[Same format as critical]

---

## Low Priority Issues

[Same format as critical]

---

## Statistics

### Tool Inventory:
- Documented in available.md: [NUMBER]
- Actually exist in claude/tools/: [NUMBER]
- Phantom tools (documented but missing): [NUMBER]
- Undocumented tools (exist but not documented): [NUMBER]

### Agent Inventory:
- Documented in agents.md: [NUMBER]
- Actually exist in claude/agents/: [NUMBER]
- Phantom agents: [NUMBER]
- Undocumented agents: [NUMBER]

### Command Inventory:
- Total commands in claude/commands/: [NUMBER]
- Broken commands (missing dependencies): [NUMBER]
- Duplicate commands: [NUMBER]

### RAG Systems:
- Total RAG systems: [NUMBER]
- Documented: [NUMBER]
- Operational: [NUMBER]
- Broken: [NUMBER]

---

## Recommendations

### Immediate Actions (Critical):
1. [Fix X]
2. [Fix Y]

### Short-term Actions (Medium):
1. [Update X]
2. [Consolidate Y]

### Long-term Actions (Low):
1. [Improve X]
2. [Enhance Y]

### Process Improvements:
1. [How to prevent this in future]
2. [What checks to add to save state]

---

## Save State Process Recommendation

[Based on your analysis of save_state.md vs comprehensive_save_state.md]

**Recommended Approach**: [Merge | Keep Both | Choose One]
**Rationale**: [Why]
**Implementation**: [Specific steps]

```

---

## Important Constraints

**DO NOT**:
- ❌ Make any changes yourself
- ❌ Create missing files
- ❌ Update documentation
- ❌ Fix broken references
- ❌ Delete anything

**DO**:
- ✅ Document what you find
- ✅ Provide specific evidence
- ✅ Make clear recommendations
- ✅ Prioritize issues by impact
- ✅ Suggest process improvements

---

## Starting Point

Begin with:
1. Read this prompt completely
2. Load `claude/context/tools/available.md` and count documented tools
3. Run: `find claude/tools -name "*.py" -type f | wc -l`
4. Compare the numbers - this will give you a baseline
5. Proceed through the checklist systematically

---

## Context Files to Load

**Required**:
- `claude/context/tools/available.md` (tool inventory)
- `claude/context/core/agents.md` (agent inventory)
- `claude/commands/save_state.md` (simple protocol)
- `claude/commands/comprehensive_save_state.md` (advanced protocol)
- `SYSTEM_STATE.md` (current state - should be Phase 102)
- `README.md` (user-facing capabilities)

**For Reference**:
- `claude/context/session/phase_101_102_session_summary.md` (what just happened)
- `claude/context/session/decisions/phase_101_102_design_decisions.json` (recent decisions)

---

## Success Criteria

Your review is successful if:
1. ✅ Clear inventory of phantom vs real tools/agents/commands
2. ✅ Specific evidence for each issue found
3. ✅ Prioritized recommendations (critical/medium/low)
4. ✅ Actionable fixes (not vague suggestions)
5. ✅ Process improvement suggestions to prevent recurrence
6. ✅ Save state process recommendation with rationale

---

**Good luck! The system needs this audit - be thorough.**
