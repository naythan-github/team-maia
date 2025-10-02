# Documentation Workflow - Systematic Documentation Practices

## 🔄 MANDATORY DOCUMENTATION TRIGGERS

### When ANY of these happen, documentation MUST be updated:

1. **System Architecture Changes**
   - Path structure modifications
   - New core components added/removed
   - Migration or major refactoring
   - Import system changes

2. **File Structure Changes**
   - New directories created
   - Files moved or renamed
   - Core tools added/modified
   - Database schema changes

3. **User-Facing Changes**
   - New commands or tools
   - Changed usage patterns
   - Modified configuration requirements
   - Updated workflows

4. **Task Completion**
   - Major phases completed (like migrations)
   - Critical bug fixes
   - New integrations working
   - System validation results

## 📝 DOCUMENTATION CHECKLIST

### ALWAYS UPDATE THESE FILES:
- [ ] **SYSTEM_STATE.md** - Current system status and recent changes
- [ ] **CLAUDE.md** - User instructions and examples (if usage changed)
- [ ] **claude/context/tools/available.md** - Tool inventory and capabilities
- [ ] **Relevant command/agent documentation** - If workflow changed

### UPDATE IF APPLICABLE:
- [ ] **README.md** - If fundamental setup changed
- [ ] **claude/context/core/identity.md** - If capabilities expanded
- [ ] **Project structure documentation** - If directories changed
- [ ] **Integration guides** - If new systems added

## 🎯 DOCUMENTATION STANDARDS

### Required Elements:
1. **What Changed** - Clear description of modifications
2. **Why Changed** - Business/technical justification
3. **Impact** - What this means for users/system
4. **Status** - Current operational state
5. **Next Steps** - What remains to be done

### Format Requirements:
- Use clear headers and bullet points
- Include timestamps for major changes
- Maintain chronological order in status docs
- Use emoji indicators for status (✅❌⚠️🔄)

## 🔒 ENFORCEMENT RULES

### Non-Negotiable:
1. **No task is "complete" until documentation is updated**
2. **Documentation updates happen BEFORE moving to next major task**
3. **System state must always reflect current reality**
4. **Examples in user docs must be tested and working**

### Quality Gates:
- Documentation must be readable by someone unfamiliar with recent changes
- All file paths and examples must be current and working
- Status indicators must reflect actual system state
- Changes must be explained in context of overall system

## 📊 DOCUMENTATION WORKFLOW

### Step 1: Identify Changes
- List all files/systems modified
- Note any new capabilities or changed workflows
- Identify user-impacting changes

### Step 2: Update Core Status
- Update SYSTEM_STATE.md with current reality
- Update completion status of major initiatives
- Note any new issues or blockers discovered

### Step 3: Update User Guidance
- Verify examples in CLAUDE.md still work
- Update tool descriptions in available.md
- Modify command documentation if workflows changed

### Step 4: Validate Documentation
- Test any code examples provided
- Ensure file paths are accurate
- Verify status claims match reality

### Step 5: Mark Complete
- Only mark task as complete after documentation updated
- Include doc updates in completion summary
- Note what docs were modified

## 🚨 CRITICAL REMINDER

**Documentation debt compounds exponentially. A system with outdated docs becomes unmaintainable. Always pay the documentation tax immediately.**

This workflow is mandatory for all significant system changes going forward.
