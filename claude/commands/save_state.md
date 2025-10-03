# Save State Command - Complete System Documentation & Git Integration

## Overview
Comprehensive system state preservation with mandatory documentation updates and git integration.

## Execution Sequence

### Phase 1: Documentation Updates (MANDATORY)
1. **SYSTEM_STATE.md** - Update session context, phase, and recent changes
2. **README.md** - Update core capabilities and system overview
3. **claude/context/core/agents.md** - Update agent capabilities and enhancements
4. **claude/context/tools/available.md** - Update tool inventory and new capabilities
5. **claude/context/core/systematic_tool_checking.md** - Update tool discovery patterns if needed

### Phase 2: Verification
1. **Documentation Consistency Check** - Ensure all changes are reflected across files
2. **System Status Validation** - Verify all documented capabilities match actual system state
3. **Context Window Compatibility** - Ensure new context windows can operate correctly

### Phase 2.5: Anti-Sprawl Validation ⭐ **NEW - PHASE 81**
1. **Experimental Directory Check** - Flag files in experimental/ that should be graduated or archived
2. **Production Sprawl Detection** - Identify duplicate/versioned files in production directories
3. **Naming Convention Audit** - Check for prohibited patterns (_v1, _new, timestamps, etc.)
4. **Graduation Review** - Verify new production files have documentation updates
5. **User Confirmation** - If violations found, ask user to resolve before commit

**Validation Script**:
```bash
# Check for sprawl before committing
echo "🔍 Running anti-sprawl validation..."

# Check experimental directory age
find claude/extensions/experimental -type f -mtime +7 | while read file; do
    echo "⚠️  Old experimental file: $file (>7 days - graduate or archive?)"
done

# Check for version indicators in production
find claude/tools claude/agents claude/commands -type f \
    -name "*_v[0-9]*" -o -name "*_new*" -o -name "*_old*" | while read file; do
    echo "❌ Naming violation: $file (version indicators in production)"
done

# Check for multiple similar files (potential duplicates)
# (pattern matching for similar names)

echo "✅ Anti-sprawl validation complete"
```

### Phase 3: Git Integration (MANDATORY)
1. **Git Status Check** - Review all modified and new files
2. **Git Add** - Stage all documentation updates and system changes
3. **Git Commit** - Create descriptive commit with phase information
4. **Git Push** - Push changes to remote repository

### Phase 4: Implementation Tracking Integration ⭐ **NEW**
1. **Active Implementations Check** - Preserve ongoing implementation contexts
2. **Implementation Checkpoints** - Save current state of all active implementations
3. **Universal Tracker Update** - Ensure implementation continuity across context resets

### Phase 5: Completion Verification
1. **Documentation Audit** - Confirm all system changes are documented
2. **Git Status Verification** - Ensure clean working directory
3. **Implementation Continuity** - Verify all implementations can be resumed
4. **Anti-Sprawl Confirmation** - No violations committed
5. **System State Summary** - Provide completion confirmation

## Implementation Template

```bash
# Phase 1: Documentation Updates (handled by Maia)
echo "📚 Updating system documentation..."

# Phase 2: Verification (handled by Maia) 
echo "🔍 Verifying documentation consistency..."

# Phase 3: Git Integration
echo "📝 Committing changes to git..."
git add -A
git commit -m "📚 SAVE STATE: [Phase/Session Description] - [Key Changes]

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main

# Phase 4: Implementation Tracking Integration
echo "🔄 Preserving implementation contexts..."
python3 claude/tools/📊_data/universal_implementation_tracker.py list
# Save checkpoints for all active implementations if needed

# Phase 5: Completion
echo "✅ Save state complete - All implementations preserved"
```

## Mandatory Documentation Files

### Critical System Files (ALWAYS UPDATE)
- `SYSTEM_STATE.md` - Current phase and session overview
- `README.md` - Core capabilities and system summary
- `claude/context/core/agents.md` - Agent capabilities
- `claude/context/tools/available.md` - Tool inventory

### Context Files (UPDATE IF MODIFIED)
- `claude/context/core/identity.md` - System identity changes
- `claude/context/core/model_selection_strategy.md` - LLM routing changes
- `claude/context/core/systematic_tool_checking.md` - Tool discovery updates
- `claude/context/core/command_orchestration.md` - Orchestration changes

### Project-Specific Files (UPDATE IF RELEVANT)
- Session summary files in `claude/data/`
- Agent-specific documentation if enhanced
- Command documentation if workflows changed

## Quality Gates

### Documentation Requirements
- [ ] All system changes documented
- [ ] Phase progression clearly marked
- [ ] New capabilities accurately described
- [ ] Production status clearly indicated
- [ ] Integration points documented

### Anti-Sprawl Requirements ⭐ **NEW**
- [ ] No experimental files >7 days old without decision
- [ ] No naming violations in production directories
- [ ] New production files have SYSTEM_STATE.md updates
- [ ] No duplicate/versioned files uncommitted
- [ ] Graduation path clear for any experimental work

### Git Requirements
- [ ] All files staged with `git add -A`
- [ ] Descriptive commit message with phase information
- [ ] Claude Code attribution included
- [ ] Push successful to remote repository
- [ ] Working directory clean after completion

## Error Handling

### Documentation Failures
- **Missing Updates**: Identify and update all relevant files
- **Inconsistencies**: Reconcile conflicting information across files
- **Context Gaps**: Ensure new context windows have complete guidance

### Git Failures
- **Staging Issues**: Resolve file conflicts or permissions
- **Commit Failures**: Check git configuration and repository status
- **Push Failures**: Verify remote connectivity and authentication

## Success Criteria

✅ **Complete Success**: All documentation updated, git commit/push successful, system state preserved
⚠️ **Partial Success**: Documentation updated but git issues need resolution  
❌ **Failure**: Missing documentation updates or unable to preserve state

This command ensures systematic preservation of all system evolution and maintains continuity across context windows.