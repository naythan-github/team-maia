# Smart Context Loader Enablement Tasks
**Created**: 2025-10-13
**Status**: ✅ COMPLETE (All HIGH + MEDIUM priority tasks finished)
**Completed**: 2025-10-13
**Priority**: HIGH (System built but not wired into context loading)

---

## Executive Summary

**Problem**: Smart context loader built and tested (85% token reduction achieved) but NOT integrated into actual context loading workflow. Tool exists but isn't invoked by the system.

**Current State**:
- ✅ `smart_context_loader.py` created (450 lines, production-ready)
- ✅ End-to-end testing complete (4/4 test cases passed)
- ✅ Documentation complete (SYSTEM_STATE.md, available.md, CLAUDE.md)
- ❌ **NOT wired into context loading hooks**
- ❌ **smart_context_loading.md still uses static Read**
- ❌ **No automatic invocation in workflows**

**Solution**: Execute 7 enablement tasks to integrate smart loader into context loading system

**Estimated Time**: HIGH priority (10 min) + MEDIUM priority (75 min) = 85 min total

---

## HIGH PRIORITY TASKS (10 min) 🚨 DO IMMEDIATELY

### Task 1: Update smart_context_loading.md (5 min)

**File**: `/Users/naythandawe/git/maia/claude/context/core/smart_context_loading.md`
**Line**: 21
**Issue**: Currently references static `${MAIA_ROOT}/SYSTEM_STATE.md` Read

**Current Content** (Line 21):
```markdown
5. `${MAIA_ROOT}/SYSTEM_STATE.md` - **🚨 CURRENT SESSION STATE - CRITICAL FOR CLEANUP/MODIFICATION DECISIONS**
```

**Required Change**:
```markdown
5. **Smart SYSTEM_STATE Loading** ⭐ **INTELLIGENT LOADING - 85% TOKEN REDUCTION**
   - **Primary**: Use `smart_context_loader.py` for intent-aware phase selection
   - **Performance**: 85% token reduction (42K → 5-20K adaptive)
   - **Query-Adaptive**:
     - Agent enhancement queries → Phases 2, 107-111 (4.4K tokens)
     - SRE/reliability queries → Phases 103-105 (8.0K tokens)
     - Strategic planning → Recent 20 phases (13K tokens)
     - Simple queries → Recent 10 phases (3.4K tokens)
   - **Tool**: `python3 claude/tools/sre/smart_context_loader.py "user_query_context"`
   - **Fallback**: If smart loader unavailable → `Read SYSTEM_STATE.md offset=2000 limit=1059` (recent phases only)
   - **Manual Usage**:
     ```bash
     # Get context for current query
     python3 claude/tools/sre/smart_context_loader.py "Continue agent enhancement work"

     # Load specific phases
     python3 claude/tools/sre/smart_context_loader.py --phases 2 107 108

     # Load recent N phases
     python3 claude/tools/sre/smart_context_loader.py --recent 15
     ```
```

**Verification**:
```bash
# After editing, verify line 21 changed
grep -n "Smart SYSTEM_STATE Loading" /Users/naythandawe/git/maia/claude/context/core/smart_context_loading.md
```

---

### Task 2: Test Smart Loader with Current Session Query (2 min)

**Purpose**: Validate smart loader works with actual context loading workflow

**Test Commands**:
```bash
# Test 1: Agent enhancement query (should load Phases 2, 107-111)
python3 claude/tools/sre/smart_context_loader.py "Continue agent enhancement work" --stats

# Test 2: SRE query (should load Phases 103-105)
python3 claude/tools/sre/smart_context_loader.py "Check system health" --stats

# Test 3: Strategic query (should load recent 15-20 phases)
python3 claude/tools/sre/smart_context_loader.py "What should we prioritize?" --stats

# Test 4: Verify actual content loading (not just stats)
python3 claude/tools/sre/smart_context_loader.py "agent status" | head -100
```

**Expected Results**:
- ✅ Agent query: 3-5K tokens, strategy=agent_enhancement
- ✅ SRE query: 6-9K tokens, strategy=sre_reliability
- ✅ Strategic query: 10-15K tokens, strategy=moderate_complexity/strategic_planning
- ✅ Content preview shows header + selected phases

---

### Task 3: Document Manual Usage in CLAUDE.md (3 min)

**File**: `/Users/naythandawe/git/maia/CLAUDE.md`
**Section**: Critical File Locations (already has smart loader mention at line 70)

**Current Content** (Lines 70-73):
```markdown
  - **Smart Loader**: `${MAIA_ROOT}/claude/tools/sre/smart_context_loader.py` ⭐ **NEW - PHASE 2 SYSTEM_STATE PROJECT**
    - Intent-aware loading (5-20K tokens vs 42K full file, 75-90% reduction)
    - Query routing: agent enhancement → Phases 2, 107-111 | SRE → Phases 103-105 | etc.
    - Usage: `SmartContextLoader().load_for_intent(user_query)` → optimized context
```

**Add After Line 73**:
```markdown
    - **Manual CLI Usage** (for context loading validation):
      ```bash
      # Load context for query
      python3 claude/tools/sre/smart_context_loader.py "your query here"

      # Show statistics only
      python3 claude/tools/sre/smart_context_loader.py "your query" --stats

      # Load specific phases
      python3 claude/tools/sre/smart_context_loader.py --phases 2 103 107

      # Load recent N phases
      python3 claude/tools/sre/smart_context_loader.py --recent 20
      ```
```

**Verification**:
```bash
# After editing, verify addition
grep -A 10 "Manual CLI Usage" /Users/naythandawe/git/maia/CLAUDE.md
```

---

## MEDIUM PRIORITY TASKS (75 min) 🔧 DO SOON

### Task 4: Create Smart Loader Bash Wrapper (15 min)

**File**: `/Users/naythandawe/git/maia/claude/hooks/load_system_state_smart.sh` (NEW)
**Purpose**: Simple wrapper for context loading hooks to invoke smart loader

**Content**:
```bash
#!/bin/bash
# Smart SYSTEM_STATE.md Loader - Intent-Aware Context Loading
# Part of: Phase 2 SYSTEM_STATE Intelligent Loading Project
# Usage: ./load_system_state_smart.sh "user query context"

set -e

# Detect MAIA_ROOT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIA_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Get user query context (default if not provided)
QUERY="${1:-What is the current system status?}"

# Invoke smart context loader
LOADER_PATH="$MAIA_ROOT/claude/tools/sre/smart_context_loader.py"

if [[ ! -f "$LOADER_PATH" ]]; then
    echo "⚠️  Smart loader not found: $LOADER_PATH" >&2
    echo "   Falling back to static Read of recent SYSTEM_STATE phases..." >&2

    # Fallback: Read recent 1000 lines (Phases 97-111 approximately)
    SYSTEM_STATE="$MAIA_ROOT/SYSTEM_STATE.md"
    if [[ -f "$SYSTEM_STATE" ]]; then
        tail -n 1000 "$SYSTEM_STATE"
        exit 0
    else
        echo "❌ SYSTEM_STATE.md not found: $SYSTEM_STATE" >&2
        exit 1
    fi
fi

# Execute smart loader
python3 "$LOADER_PATH" "$QUERY"
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "⚠️  Smart loader failed with exit code $EXIT_CODE" >&2
    echo "   Falling back to static Read..." >&2
    tail -n 1000 "$MAIA_ROOT/SYSTEM_STATE.md"
    exit 0
fi

exit 0
```

**Make Executable**:
```bash
chmod +x /Users/naythandawe/git/maia/claude/hooks/load_system_state_smart.sh
```

**Testing**:
```bash
# Test wrapper works
/Users/naythandawe/git/maia/claude/hooks/load_system_state_smart.sh "agent enhancement status" | head -50

# Test fallback (temporarily rename smart_context_loader.py)
mv /Users/naythandawe/git/maia/claude/tools/sre/smart_context_loader.py /tmp/test_smart_loader.py
/Users/naythandawe/git/maia/claude/hooks/load_system_state_smart.sh "test" | head -20
mv /tmp/test_smart_loader.py /Users/naythandawe/git/maia/claude/tools/sre/smart_context_loader.py
```

**Expected Results**:
- ✅ Primary path: Smart loader output (header + selected phases)
- ✅ Fallback path: Last 1000 lines of SYSTEM_STATE.md
- ✅ Error handling: Clear messages, no crashes

---

### Task 5: Update dynamic_context_loader.py (30 min)

**File**: `/Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py`
**Current State**: No SYSTEM_STATE loading logic (only loads other context files)
**Required**: Add smart loader invocation for SYSTEM_STATE

**Step 5.1**: Read current file structure (5 min)
```bash
# Examine current structure
head -100 /Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py
grep -n "def.*load\|class.*Loader" /Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py
```

**Step 5.2**: Identify where SYSTEM_STATE should be loaded (5 min)
```bash
# Find where context files are loaded
grep -n "CORE.*FILES\|mandatory.*files\|always.*load" /Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py
```

**Step 5.3**: Add SYSTEM_STATE smart loading function (15 min)

**Add New Function** (location: after other load functions):
```python
def load_system_state_smart(user_query: str = None) -> str:
    """
    Load SYSTEM_STATE.md intelligently using smart context loader.

    Args:
        user_query: User's query for intent-based loading

    Returns:
        SYSTEM_STATE content optimized for query (5-20K tokens)
    """
    import subprocess
    import sys
    from pathlib import Path

    maia_root = Path(__file__).parent.parent.parent
    loader_path = maia_root / "claude" / "tools" / "sre" / "smart_context_loader.py"

    # Default query if none provided
    if not user_query:
        user_query = "What is the current system status?"

    try:
        # Invoke smart loader
        result = subprocess.run(
            [sys.executable, str(loader_path), user_query],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return result.stdout
        else:
            # Fallback to recent phases
            print(f"⚠️  Smart loader failed, falling back to recent phases", file=sys.stderr)
            system_state = maia_root / "SYSTEM_STATE.md"
            if system_state.exists():
                lines = system_state.read_text().splitlines()
                # Load recent 1000 lines (approximately Phases 97-111)
                return '\n'.join(lines[-1000:])
            else:
                return "⚠️  SYSTEM_STATE.md not found"

    except Exception as e:
        # Fallback on any error
        print(f"⚠️  Smart loader exception: {e}, falling back", file=sys.stderr)
        system_state = maia_root / "SYSTEM_STATE.md"
        if system_state.exists():
            lines = system_state.read_text().splitlines()
            return '\n'.join(lines[-1000:])
        else:
            return "⚠️  SYSTEM_STATE.md not found"
```

**Step 5.4**: Update MANDATORY_CORE_FILES list (5 min)

**Find and Update**:
```python
# OLD (if exists)
MANDATORY_CORE_FILES = [
    "ufc_system.md",
    "identity.md",
    "systematic_thinking_protocol.md",
    "model_selection_strategy.md"
    # SYSTEM_STATE.md might be missing or static
]

# NEW
MANDATORY_CORE_FILES = [
    "ufc_system.md",
    "identity.md",
    "systematic_thinking_protocol.md",
    "model_selection_strategy.md"
    # Note: SYSTEM_STATE.md loaded via load_system_state_smart()
]
```

**Step 5.5**: Test integration (5 min)
```bash
# Test the updated dynamic_context_loader.py
python3 /Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py analyze "Continue agent enhancement"

# Verify SYSTEM_STATE smart loading works
python3 -c "
import sys
sys.path.insert(0, '/Users/naythandawe/git/maia/claude/hooks')
from dynamic_context_loader import load_system_state_smart
content = load_system_state_smart('agent status')
print(f'Loaded {len(content)} chars')
print(content[:500])
"
```

---

### Task 6: Update context_auto_loader.py (30 min)

**File**: `/Users/naythandawe/git/maia/claude/hooks/context_auto_loader.py`
**Purpose**: Auto-recovery system when context loading fails
**Required**: Add smart loader to auto-recovery sequence

**Step 6.1**: Read current structure (5 min)
```bash
# Examine current auto-loader
head -100 /Users/naythandawe/git/maia/claude/hooks/context_auto_loader.py
grep -n "SYSTEM_STATE\|system_state" /Users/naythandawe/git/maia/claude/hooks/context_auto_loader.py
```

**Step 6.2**: Add SYSTEM_STATE smart loading to recovery sequence (20 min)

**Find Recovery Function** (likely named `auto_recover` or `load_mandatory_context`):
```python
# Add to recovery sequence

def auto_recover_context():
    """Auto-recover context loading with smart SYSTEM_STATE loading."""

    recovery_steps = [
        ("UFC System", load_ufc_system),
        ("Identity", load_identity),
        ("Systematic Thinking", load_systematic_thinking),
        ("Model Selection", load_model_selection),
        ("SYSTEM_STATE (Smart)", load_system_state_smart_wrapper)  # NEW
    ]

    # ... rest of function

def load_system_state_smart_wrapper():
    """Wrapper for smart SYSTEM_STATE loading in auto-recovery."""
    import subprocess
    import sys
    from pathlib import Path

    maia_root = Path(__file__).parent.parent.parent
    loader_path = maia_root / "claude" / "tools" / "sre" / "smart_context_loader.py"

    try:
        result = subprocess.run(
            [sys.executable, str(loader_path), "--recent", "15"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return result.stdout
        else:
            # Fallback
            system_state = maia_root / "SYSTEM_STATE.md"
            lines = system_state.read_text().splitlines()
            return '\n'.join(lines[-1000:])

    except Exception:
        # Silent fallback
        system_state = maia_root / "SYSTEM_STATE.md"
        if system_state.exists():
            lines = system_state.read_text().splitlines()
            return '\n'.join(lines[-1000:])
        return ""
```

**Step 6.3**: Test auto-recovery with smart loader (5 min)
```bash
# Test context auto-loader
python3 /Users/naythandawe/git/maia/claude/hooks/context_auto_loader.py

# Verify SYSTEM_STATE loaded via smart loader
```

---

## LOW PRIORITY TASKS (Future Enhancement) 🔮

### Task 7: Automatic Hook Integration (Phase 3)

**Scope**: Detect user query from Claude Code session, invoke smart loader automatically
**Complexity**: High (requires hook system understanding)
**Benefit**: Zero-touch context loading optimization
**Estimated Effort**: 2-3 hours

**Deferred Reason**: High priority tasks provide immediate value. This is optimization.

---

## Validation Checklist

After completing HIGH + MEDIUM priority tasks, verify:

### Context Loading Validation
- [ ] `smart_context_loading.md` Line 21 updated (references smart loader)
- [ ] CLAUDE.md has manual usage instructions
- [ ] Smart loader wrapper script created and executable
- [ ] `dynamic_context_loader.py` has `load_system_state_smart()` function
- [ ] `context_auto_loader.py` includes smart loader in recovery

### Functional Testing
- [ ] Smart loader CLI works: `python3 claude/tools/sre/smart_context_loader.py "test query"`
- [ ] Wrapper script works: `./claude/hooks/load_system_state_smart.sh "test"`
- [ ] Fallback works: Smart loader fails → static Read fallback succeeds
- [ ] Token reduction validated: Agent query loads ~4K tokens (not 42K)

### Documentation Validation
- [ ] CLAUDE.md mentions smart loader in Critical File Locations
- [ ] `smart_context_loading.md` references smart loader (not static Read)
- [ ] `available.md` has comprehensive smart loader documentation
- [ ] SYSTEM_STATE.md has Phase 2 completion entry
- [ ] This enablement task file saved for context recovery

---

## Success Criteria

**Definition of Done**:
1. ✅ Smart loader integrated into context loading workflow
2. ✅ Documentation updated (smart_context_loading.md, CLAUDE.md)
3. ✅ Wrapper scripts created for easy invocation
4. ✅ Fallback mechanisms working (graceful degradation)
5. ✅ Token reduction achieved in practice (not just in isolated tests)

**Validation Command**:
```bash
# Single command to validate full integration
python3 -c "
import subprocess
import sys

# Test 1: Smart loader CLI
result = subprocess.run([
    sys.executable,
    'claude/tools/sre/smart_context_loader.py',
    'agent enhancement status',
    '--stats'
], capture_output=True, text=True)

print('Test 1 - Smart Loader CLI:')
print('✅ PASS' if result.returncode == 0 else '❌ FAIL')
print()

# Test 2: Wrapper script
result = subprocess.run([
    'bash',
    'claude/hooks/load_system_state_smart.sh',
    'agent status'
], capture_output=True, text=True)

print('Test 2 - Wrapper Script:')
print('✅ PASS' if result.returncode == 0 else '❌ FAIL')
print()

# Test 3: Check documentation updated
import pathlib
smart_loading = pathlib.Path('claude/context/core/smart_context_loading.md').read_text()
has_smart_loader = 'smart_context_loader' in smart_loading

print('Test 3 - Documentation Updated:')
print('✅ PASS' if has_smart_loader else '❌ FAIL')
"
```

---

## Estimated Timeline

**HIGH Priority** (Do Immediately):
- Task 1: Update smart_context_loading.md → 5 min
- Task 2: Test smart loader → 2 min
- Task 3: Document manual usage → 3 min
- **Subtotal**: 10 minutes

**MEDIUM Priority** (Do This Session):
- Task 4: Create bash wrapper → 15 min
- Task 5: Update dynamic_context_loader.py → 30 min
- Task 6: Update context_auto_loader.py → 30 min
- **Subtotal**: 75 minutes

**Total Enablement Time**: 85 minutes (1 hour 25 minutes)

---

## Context Recovery Instructions

**If context is lost mid-enablement**, load this file and continue from last completed task:

```bash
# Load this enablement task file
Read /Users/naythandawe/git/maia/claude/data/SMART_LOADER_ENABLEMENT_TASKS.md

# Check what's already done
grep -n "Smart SYSTEM_STATE Loading" /Users/naythandawe/git/maia/claude/context/core/smart_context_loading.md
ls -la /Users/naythandawe/git/maia/claude/hooks/load_system_state_smart.sh
grep -n "load_system_state_smart" /Users/naythandawe/git/maia/claude/hooks/dynamic_context_loader.py

# Continue from first incomplete task
```

---

## Status: READY FOR EXECUTION

**Next Action**: Execute Task 1 (Update smart_context_loading.md) → 5 minutes

**Priority**: HIGH - System is built but not wired. Must complete enablement for smart loader to be used in practice.
