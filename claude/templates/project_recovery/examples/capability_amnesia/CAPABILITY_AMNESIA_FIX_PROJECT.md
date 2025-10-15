# Capability Amnesia Fix - Complete Project Plan

**Project ID**: CAPABILITY_AMNESIA_FIX_001
**Created**: 2025-10-15
**Status**: Planning Complete, Ready for Implementation
**Estimated Time**: 3-4 hours total
**Priority**: CRITICAL - Solves root cause of duplicate work and context loss

---

## 🎯 EXECUTIVE SUMMARY

### Problem Statement
Maia frequently builds duplicate tools/agents because new context windows don't consistently load documentation of existing capabilities. Current save state process documents everything correctly, but smart context loading skips available.md/agents.md in many scenarios, causing capability amnesia.

### Root Cause
**Gap**: Documentation exists but isn't loaded consistently
- Smart SYSTEM_STATE loader: Only loads recent phases (misses older work)
- Domain-based loading: Skips available.md in minimal/simple/personal modes
- No always-loaded capability registry
- Phase 0 capability check: Manual, often forgotten

### Solution Architecture
**Two-Pronged Fix**:
1. **Architectural Solution**: Create always-loaded capability index (fixes root cause)
2. **Process Optimization**: Simplify save state while maintaining memory (reduces overhead)

### Success Metrics
- ✅ Zero capability amnesia (new contexts know what exists)
- ✅ 70% reduction in save state overhead
- ✅ 2-4K token cost per session (down from 16-39K)
- ✅ <2 min to update capability index per commit
- ✅ Phase 0 capability check automated

---

## 📋 PROJECT PHASES

### **PHASE 1: Capability Index Creation** ⭐ FOUNDATION
**Duration**: 1 hour
**Deliverable**: capability_index.md (always-loaded capability registry)

#### Phase 1.1: Extract Existing Capabilities (30 min)
**Input Sources**:
- `claude/context/tools/available.md` - 200+ tools
- `claude/context/core/agents.md` - 49 agents
- `SYSTEM_STATE.md` - Recent phases (118, 117, 116, 115, 113)

**Extraction Pattern**:
```markdown
## [Category Name]
- tool_name.py - Phase NNN - One-line description
- agent_name - Phase NNN - One-line description
```

**Categories to Extract**:
1. Security Tools (15+ tools)
2. SRE/Reliability Tools (20+ tools)
3. Data/Analytics Tools (30+ tools)
4. Information Management Tools (10+ tools)
5. Orchestration Infrastructure (10+ files)
6. Agents by Specialization (49 agents)

**Quality Criteria**:
- ✅ Each entry: Name + Phase + 1-line description (max 100 chars)
- ✅ Organized by category for quick scanning
- ✅ Recent tools (last 30 days) at top
- ✅ Total length: 250-350 lines (target 3K tokens)

#### Phase 1.2: Create Searchable Keyword Index (15 min)
**Purpose**: Enable quick searches like "do we have security scanner?"

**Format**:
```markdown
## Quick Search Keywords
Security scanning → save_state_security_checker.py, osv_scanner.py
Context loading → smart_context_loader.py, dynamic_context_loader.py
Agent orchestration → agent_swarm.py, agent_loader.py
Data analysis → servicedesk_multi_rag_indexer.py
```

**Keyword Categories**:
- Problem domains (security, analytics, orchestration)
- Technologies (rag, llm, azure, database)
- Operations (scan, check, monitor, analyze)

#### Phase 1.3: Add Usage Examples (15 min)
**Purpose**: Show how to use capability index in practice

**Content**:
```markdown
## How to Use This Index

**Before building anything new**:
1. Search this file for keywords (Cmd/Ctrl+F)
2. Check if capability exists
3. If found: Use existing tool/agent
4. If not found: Proceed with Phase 0 capability check

**Examples**:
- Need: "Check code for security issues"
  → Search: "security" → Found: save_state_security_checker.py

- Need: "Analyze service desk data"
  → Search: "service desk" → Found: servicedesk_multi_rag_indexer.py
```

**Output**: `/Users/naythandawe/git/maia/claude/context/core/capability_index.md`

---

### **PHASE 2: Smart Context Loader Integration** ⭐ ALWAYS LOAD
**Duration**: 30 minutes
**Deliverable**: capability_index.md loaded in ALL context scenarios

#### Phase 2.1: Update Loading Strategies (15 min)
**File**: `claude/hooks/dynamic_context_loader.py`

**Current Minimal Strategy**:
```python
"minimal": {
    "files": [
        "claude/context/ufc_system.md",
        "claude/context/core/identity.md",
        "claude/context/core/systematic_thinking_protocol.md",
        "claude/context/core/model_selection_strategy.md"
    ]
}
```

**Enhanced Minimal Strategy**:
```python
"minimal": {
    "files": [
        "claude/context/ufc_system.md",
        "claude/context/core/identity.md",
        "claude/context/core/systematic_thinking_protocol.md",
        "claude/context/core/model_selection_strategy.md",
        "claude/context/core/capability_index.md"  # ← ADD TO ALL STRATEGIES
    ]
}
```

**Changes Required**:
- Update ALL 7 loading strategies (minimal, research, security, personal, technical, cloud, design, full)
- Add capability_index.md to each strategy's file list
- Verify total token increase: ~2-3K per load (acceptable)

#### Phase 2.2: Update Documentation (10 min)
**Files to Update**:
1. `claude/context/core/smart_context_loading.md`
   - Document that capability_index.md is ALWAYS loaded
   - Add to mandatory core files list

2. `claude/hooks/dynamic_context_loader.py` docstring
   - Update examples to show capability_index in output

#### Phase 2.3: Test Context Loading (5 min)
**Test Cases**:
```bash
# Test 1: Minimal loading
python3 claude/hooks/dynamic_context_loader.py analyze "what is 2+2"
→ Verify capability_index.md in output

# Test 2: Research loading
python3 claude/hooks/dynamic_context_loader.py analyze "research AI trends"
→ Verify capability_index.md in output

# Test 3: Security loading
python3 claude/hooks/dynamic_context_loader.py analyze "check for vulnerabilities"
→ Verify capability_index.md in output
```

**Success Criteria**:
- ✅ capability_index.md appears in ALL test outputs
- ✅ Token cost increase: 2-3K (within acceptable range)
- ✅ No loading errors

---

### **PHASE 3: Automated Phase 0 Enforcement** ⭐ PREVENT DUPLICATES
**Duration**: 1.5 hours
**Deliverable**: capability_check_enforcer.py + hook integration

#### Phase 3.1: Create Capability Check Enforcer (1 hour)
**File**: `claude/hooks/capability_check_enforcer.py`

**Core Functionality**:
```python
def detect_build_request(user_input: str) -> bool:
    """Detect if user is requesting to build/create something new"""
    build_patterns = [
        r"\b(build|create|make|implement|develop|add|write)\b.*\b(tool|agent|script|function|class)",
        r"\blet'?s build\b",
        r"\bcan you (create|make|build|write)",
        r"\bneed a (new|tool|agent|script)",
        r"\bimplement.*for"
    ]
    return any(re.search(pattern, user_input.lower()) for pattern in build_patterns)

def enforce_capability_check(user_input: str) -> dict:
    """
    Run automated capability check before build requests
    Returns: {
        "should_block": bool,
        "existing_capability": str or None,
        "confidence": float,
        "message": str
    }
    """
    if not detect_build_request(user_input):
        return {"should_block": False}

    # Auto-run capability checker
    result = subprocess.run(
        ["python3", "claude/tools/capability_checker.py", user_input],
        capture_output=True, text=True
    )

    # Parse results
    if "RECOMMENDATION: USE EXISTING" in result.stdout:
        confidence = extract_confidence(result.stdout)
        capability = extract_capability_name(result.stdout)

        if confidence >= 70:
            return {
                "should_block": True,
                "existing_capability": capability,
                "confidence": confidence,
                "message": f"⚠️ STOP: We already have {capability} (confidence: {confidence}%)"
            }

    return {"should_block": False}
```

**Output Format**:
```
🔍 PHASE 0: AUTOMATED CAPABILITY CHECK

⚠️ BUILD REQUEST DETECTED: "create a tool to scan for vulnerabilities"

Searching existing capabilities...
  ✅ FOUND: save_state_security_checker.py (Phase 113)
  📊 Confidence: 85%
  📍 Location: claude/tools/sre/save_state_security_checker.py

🎯 RECOMMENDATION: USE EXISTING

Options:
  1. Use existing tool (recommended)
  2. Enhance existing tool if insufficient
  3. Build new tool anyway (justify why)

Please confirm choice before proceeding.
```

#### Phase 3.2: Integrate with User-Prompt-Submit Hook (20 min)
**File**: `claude/hooks/user-prompt-submit`

**Add Phase 0 Enforcement Stage**:
```bash
# Stage 0.7: Automated Capability Check (Phase 119 - Capability Amnesia Fix)
echo ""
echo "🔍 AUTOMATED CAPABILITY CHECK (Phase 0)..."
CAPABILITY_ENFORCER="$(dirname "$0")/capability_check_enforcer.py"
if [[ -f "$CAPABILITY_ENFORCER" && -n "$CLAUDE_USER_MESSAGE" ]]; then
    CAPABILITY_CHECK=$(python3 "$CAPABILITY_ENFORCER" "$CLAUDE_USER_MESSAGE" 2>&1)
    CAPABILITY_CODE=$?

    if [[ $CAPABILITY_CODE -eq 1 ]]; then
        # Existing capability found with high confidence
        echo "$CAPABILITY_CHECK"
        echo ""
        echo "⏸️  PAUSING: Review existing capability before building new"
        echo "   Continue anyway? Maia will ask for confirmation."
    elif [[ $CAPABILITY_CODE -eq 0 ]]; then
        echo "✅ No duplicate capability detected (or low confidence match)"
    fi
else
    echo "⚠️  Capability enforcer not available - manual Phase 0 check recommended"
fi
echo ""
```

**Integration Points**:
- Runs AFTER context loading enforcement
- Runs BEFORE model selection
- Non-blocking (shows warning, doesn't prevent response)
- Maia sees the warning in context and asks user to confirm

#### Phase 3.3: Test Enforcement (10 min)
**Test Cases**:
```bash
# Test 1: Should detect build request
echo "build a security scanner" | Test enforcement
→ Expect: Warning about save_state_security_checker.py

# Test 2: Should NOT trigger on non-build request
echo "analyze this data" | Test enforcement
→ Expect: No warning (not a build request)

# Test 3: Should handle no match gracefully
echo "build a quantum physics simulator" | Test enforcement
→ Expect: No warning (no existing capability)
```

---

### **PHASE 4: Simplified Save State Process** ⭐ REDUCE OVERHEAD
**Duration**: 45 minutes
**Deliverable**: Tiered save state templates + updated documentation

#### Phase 4.1: Create Tiered Templates (30 min)

**File 1**: `claude/commands/save_state_tier1_quick.md`
```markdown
# Tier 1: Quick Checkpoint (2-3 min)

Use for: Incremental progress, still in flow state

## Steps
1. Update SYSTEM_STATE.md (1 min)
   - Add bullet to current phase with brief change description

2. Update capability_index.md (1 min)
   - Add tool/agent name if new capability created
   - Format: `- name - Phase NNN - one-line description`

3. Git commit with short message (1 min)
   ```bash
   git add -A
   git commit -m "🔧 Phase NNN: [what changed in 5-10 words]"
   git push
   ```

## Skip
- ❌ Pre-flight checks
- ❌ Security validation (unless adding credentials)
- ❌ README updates
- ❌ available.md / agents.md updates

## Total Time: 2-3 minutes
## Token Cost: ~500 tokens
```

**File 2**: `claude/commands/save_state_tier2_standard.md`
```markdown
# Tier 2: Standard Save State (10-15 min)

Use for: End of work session, completing logical unit of work

## Steps
1. Update SYSTEM_STATE.md (5 min)
   - Add complete phase entry with Achievement, Problem, Details, Metrics

2. Update capability_index.md (1 min)
   - Add any new tools/agents

3. Update README.md IF major capabilities changed (2 min)
   - Skip if no user-facing changes

4. Run security check (1 min)
   ```bash
   python3 claude/tools/sre/save_state_security_checker.py --verbose
   ```

5. Git commit with structured message (3 min)
   ```bash
   git add -A
   git commit -m "$(cat <<'EOF'
   🎯 PHASE NNN: [Title]

   Achievement: [One-line summary]
   Result: [Key metrics/outcomes]
   Status: ✅ [Status]

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   git push
   ```

## Skip
- ❌ Pre-flight checks (rarely catch issues)
- ❌ available.md / agents.md (unless tools/agents actually changed)
- ❌ Session summaries

## Total Time: 10-15 minutes
## Token Cost: ~2,000 tokens
```

**File 3**: Keep existing `claude/commands/save_state.md` as Tier 3 (comprehensive)

#### Phase 4.2: Update Save State Command Documentation (15 min)
**File**: `claude/commands/save_state.md`

**Add Tier Selection Guide at Top**:
```markdown
# Save State Command - Tiered Approach

## Quick Tier Selection

### Tier 1: Quick Checkpoint (2-3 min)
**When**: Making incremental progress, multiple checkpoints per session
**Files**: SYSTEM_STATE.md (bullet), capability_index.md (if new capability)
**Use**: `claude/commands/save_state_tier1_quick.md`

### Tier 2: Standard Save State (10-15 min)
**When**: End of work session, completing logical unit
**Files**: SYSTEM_STATE.md (full entry), capability_index.md, README if needed
**Use**: `claude/commands/save_state_tier2_standard.md`

### Tier 3: Comprehensive Save State (30-45 min)
**When**: End of major phase, weekly review, architecture changes
**Files**: All documentation + validation + comprehensive commit
**Use**: This file (full protocol below)

---

## Tier 3: Comprehensive Save State (Full Protocol)
[Keep existing content...]
```

---

### **PHASE 5: Testing & Validation** ⭐ VERIFY IT WORKS
**Duration**: 30 minutes
**Deliverable**: Validated system with test results

#### Phase 5.1: End-to-End Test (20 min)

**Test Scenario 1: New Context Loads Capability Index**
```bash
# Simulate new context window
1. Open new Claude Code session
2. Send simple query: "what is 2+2"
3. Verify capability_index.md appears in loaded context
4. Check token cost

Expected: capability_index.md loaded, ~2K token increase
```

**Test Scenario 2: Automated Phase 0 Prevents Duplicate**
```bash
# Simulate build request for existing capability
1. User: "build a security scanner for checking secrets"
2. Hook detects build request
3. Capability checker runs automatically
4. Warning shown: "We already have save_state_security_checker.py"
5. User confirms or chooses alternative

Expected: Warning shown, user prompted for decision
```

**Test Scenario 3: Quick Checkpoint Workflow**
```bash
# Make small change
1. Modify a file
2. Update SYSTEM_STATE.md (add bullet)
3. Update capability_index.md (if applicable)
4. Git commit short message
5. Time the process

Expected: <3 minutes total
```

**Test Scenario 4: Standard Save State Workflow**
```bash
# Complete work session
1. Update SYSTEM_STATE.md (full entry)
2. Update capability_index.md
3. Run security check
4. Git commit structured message
5. Time the process

Expected: 10-15 minutes total
```

#### Phase 5.2: Validation Checklist (10 min)

**Architecture Validation**:
- [ ] capability_index.md exists in `claude/context/core/`
- [ ] capability_index.md loaded in minimal context mode
- [ ] capability_index.md loaded in all 7 domain modes
- [ ] Token cost increase: 2-3K (acceptable)

**Enforcement Validation**:
- [ ] capability_check_enforcer.py detects build requests
- [ ] Hook integration works (shows warnings)
- [ ] False positive rate acceptable (<10%)
- [ ] Can override warning if needed

**Process Validation**:
- [ ] Tier 1 template complete and tested
- [ ] Tier 2 template complete and tested
- [ ] Tier 3 (full protocol) still available
- [ ] Time savings: 70%+ vs current process

**Documentation Validation**:
- [ ] save_state.md updated with tier selection
- [ ] smart_context_loading.md updated
- [ ] capability_index.md documented as always-loaded

---

## 📊 SUCCESS CRITERIA

### Must-Have (P0)
- ✅ capability_index.md created with 200+ tools, 49 agents
- ✅ capability_index.md loaded in ALL context scenarios
- ✅ Automated Phase 0 capability check working
- ✅ Tier 1 and Tier 2 save state templates created
- ✅ Zero capability amnesia in test scenarios

### Should-Have (P1)
- ✅ Token cost per session: <6K (vs current 16-39K)
- ✅ Save state time: <15 min for standard, <3 min for quick
- ✅ Documentation consistent and updated
- ✅ All tests passing

### Nice-to-Have (P2)
- ✅ Keyword search index in capability_index.md
- ✅ Usage examples in capability_index.md
- ✅ Pre-commit hook for security (automatic)

---

## 🔄 RECOVERY & ROLLBACK

### If Context Compaction Happens Mid-Project

**Recovery File**: This file (CAPABILITY_AMNESIA_FIX_PROJECT.md)
**Location**: `claude/data/CAPABILITY_AMNESIA_FIX_PROJECT.md`

**Recovery Steps**:
1. Read this file in its entirety
2. Check "Current Phase" section below
3. Resume from last completed phase
4. Validate previous phase outputs exist

**Current Phase**: Phase 1 (Planning Complete)
**Last Updated**: 2025-10-15
**Completed Phases**: None (ready to start)

### Rollback Plan

**If Phase 1 fails**:
- Delete `claude/context/core/capability_index.md`
- No other changes made yet

**If Phase 2 fails**:
- Revert `claude/hooks/dynamic_context_loader.py`
- Keep capability_index.md (no harm)

**If Phase 3 fails**:
- Delete `claude/hooks/capability_check_enforcer.py`
- Revert hook integration changes
- Keep Phases 1-2 (independent value)

**If Phase 4 fails**:
- Delete tier templates
- Revert save_state.md changes
- Keep Phases 1-3 (core value)

---

## 📁 FILE MANIFEST

### Files to Create
1. `claude/context/core/capability_index.md` - Always-loaded capability registry
2. `claude/hooks/capability_check_enforcer.py` - Automated Phase 0 enforcement
3. `claude/commands/save_state_tier1_quick.md` - Quick checkpoint template
4. `claude/commands/save_state_tier2_standard.md` - Standard save state template

### Files to Modify
1. `claude/hooks/dynamic_context_loader.py` - Add capability_index to all strategies
2. `claude/hooks/user-prompt-submit` - Add Phase 0 enforcement stage
3. `claude/commands/save_state.md` - Add tier selection guide at top
4. `claude/context/core/smart_context_loading.md` - Document capability_index as mandatory

### Files to Reference (Read-Only)
1. `claude/context/tools/available.md` - Extract tools (200+)
2. `claude/context/core/agents.md` - Extract agents (49)
3. `SYSTEM_STATE.md` - Extract recent tools from phases 113-118

---

## 🎯 IMPLEMENTATION SEQUENCE

### Session 1 (1 hour) - Foundation
- Execute Phase 1: Create capability_index.md
- Extract from available.md, agents.md, SYSTEM_STATE.md
- Organize by category, add keywords
- **Checkpoint**: capability_index.md created (250-350 lines)

### Session 2 (30 min) - Integration
- Execute Phase 2: Update smart context loader
- Modify dynamic_context_loader.py
- Test loading in all modes
- **Checkpoint**: capability_index.md always loaded

### Session 3 (1.5 hours) - Automation
- Execute Phase 3: Create automated enforcement
- Build capability_check_enforcer.py
- Integrate with user-prompt-submit hook
- **Checkpoint**: Phase 0 automated

### Session 4 (45 min) - Process Optimization
- Execute Phase 4: Create tiered templates
- Write Tier 1, Tier 2 templates
- Update save_state.md with tier guide
- **Checkpoint**: Simplified process documented

### Session 5 (30 min) - Validation
- Execute Phase 5: End-to-end testing
- Run all test scenarios
- Validate success criteria
- **Checkpoint**: Project complete

**Total Estimated Time**: 3-4 hours across 5 sessions

---

## 💡 ANTI-DRIFT MEASURES

### How to Prevent Project Drift

**1. Always Start by Reading This File**
- If context compaction happens, read from top to bottom
- Check "Current Phase" section
- Resume from last checkpoint

**2. Update Current Phase After Each Session**
```markdown
**Current Phase**: Phase 2 (Integration)
**Last Completed**: Phase 1 - capability_index.md created (250 lines)
**Last Updated**: 2025-10-15 14:30
**Next Steps**: Update dynamic_context_loader.py to load capability_index
```

**3. Maintain File Manifest Checklist**
```markdown
### Files Created (Checkpoint)
- [x] capability_index.md (Phase 1 - COMPLETE)
- [ ] capability_check_enforcer.py (Phase 3 - PENDING)
- [ ] save_state_tier1_quick.md (Phase 4 - PENDING)
- [ ] save_state_tier2_standard.md (Phase 4 - PENDING)
```

**4. Record Decisions**
```markdown
### Design Decisions Made
1. **Capability Index Location**: Chose `claude/context/core/` (always loaded)
   - Alternative considered: `claude/context/tools/` (skipped sometimes)
   - Rationale: Core location ensures always-loaded status

2. **Token Budget**: Accepted 2-3K increase for capability_index.md
   - Alternative considered: Lighter index (1K tokens)
   - Rationale: Comprehensive index worth the cost to prevent duplicates
```

**5. Test Checkpoints**
After each phase, record test results:
```markdown
### Phase 1 Test Results
- capability_index.md created: ✅
- Line count: 287 lines (within 250-350 target)
- Token estimate: ~2.8K (acceptable)
- Completeness: 200+ tools, 49 agents documented
```

---

## 🔥 COMMON PITFALLS & SOLUTIONS

### Pitfall 1: Forgetting to Update Capability Index
**Problem**: Build new tool, forget to add to capability_index.md
**Solution**: Add to Tier 1 save state checklist (2 min step)
**Prevention**: Automated reminder in capability_check_enforcer.py

### Pitfall 2: Capability Index Gets Stale
**Problem**: Index has old tools, missing new ones
**Solution**: Weekly audit (compare to available.md)
**Prevention**: Add "last updated" date to index

### Pitfall 3: False Positives in Phase 0 Check
**Problem**: Enforcer flags legitimate new builds
**Solution**: User can override with justification
**Prevention**: Tune confidence threshold (70%+ = warning)

### Pitfall 4: Token Budget Creep
**Problem**: Capability index grows beyond 3K tokens
**Solution**: Archive old tools (>6 months) to separate file
**Prevention**: Keep "Recent Tools" section focused on last 30 days

---

## 📈 METRICS TO TRACK

### Before Implementation (Baseline)
- Save state time: 15-30 min per commit
- Token cost per session: 16-39K
- Capability amnesia incidents: ~2-3 per week (estimated)
- Duplicate tools built: Unknown (not tracked)

### After Implementation (Target)
- Save state time: 2-3 min (Tier 1), 10-15 min (Tier 2)
- Token cost per session: 4-6K (70-85% reduction)
- Capability amnesia incidents: 0 (capability_index always loaded)
- Duplicate tools prevented: Track via enforcer warnings

### Track These Weekly
- Capability index updates: How often?
- Phase 0 warnings triggered: How many?
- False positives: How often does user override?
- Time savings: Actual vs target

---

## ✅ COMPLETION CRITERIA

Project is COMPLETE when:
- [x] capability_index.md exists and is comprehensive
- [x] capability_index.md loaded in all context modes
- [x] Automated Phase 0 check working
- [x] Tiered save state templates created
- [x] All tests passing
- [x] Documentation updated
- [x] Zero capability amnesia in 5 test scenarios
- [x] 70%+ time savings measured
- [x] User satisfaction: Process feels better

---

## 🎯 POST-IMPLEMENTATION

### Week 1: Monitor & Tune
- Track Phase 0 warning frequency
- Adjust confidence threshold if needed
- Refine keyword index based on usage

### Week 2: Optimize
- Identify most-used tools (add to top of index)
- Archive old tools if index getting long
- Fine-tune save state tier templates

### Week 3: Document Learnings
- Update this project file with lessons learned
- Add to SYSTEM_STATE.md as Phase 119
- Share insights in commit message

### Ongoing Maintenance
- Update capability_index.md with each new tool/agent (2 min)
- Weekly audit: Verify index matches available.md
- Monthly review: Archive old tools, update keywords

---

## 📝 NOTES & CONTEXT

### Why This Project Matters
User reported: "Maia often works on something, completes something, but then doesn't update all the guidance required to remember what had just been created."

Root cause: Documentation exists but isn't consistently loaded. Smart context loading optimizes for minimal tokens, skipping available.md and agents.md in many scenarios.

Solution: Always-loaded capability index ensures EVERY context window knows what exists, regardless of domain or complexity.

### Design Philosophy
**80/20 Rule**: capability_index.md is 20% of the size of available.md + agents.md, but provides 80% of the value (knowing what exists).

**Fail-Safe Design**: Even if user forgets to update index, automated Phase 0 check catches duplicates via capability_checker.py searching SYSTEM_STATE.md + available.md.

**Progressive Enhancement**: Each phase adds value independently. Can stop after Phase 2 and still solve 80% of problem.

### Success Indicators
- User says: "I haven't built a duplicate tool in 2 weeks"
- Time saved: "Save state takes <5 min now vs 30 min before"
- Confidence: "New context windows always know what I've built"

---

## 🔗 RELATED DOCUMENTATION

- `claude/commands/save_state.md` - Current save state protocol (to be enhanced)
- `claude/context/core/smart_context_loading.md` - Context loading strategy
- `claude/hooks/dynamic_context_loader.py` - Domain-based context loading
- `claude/tools/capability_checker.py` - Existing capability search tool
- `SYSTEM_STATE.md` - Phase tracking and system state

---

**Project Status**: ✅ PLANNING COMPLETE - Ready for Phase 1 implementation
**Next Step**: Execute Phase 1.1 - Extract capabilities from available.md and agents.md
**Estimated Time to Complete**: 3-4 hours total
**Confidence**: 95% - Architecture is sound, phases are well-defined, rollback plans in place
