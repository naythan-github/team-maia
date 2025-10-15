# 🚀 CAPABILITY AMNESIA FIX - START HERE

**If you see this file, you're resuming the Capability Amnesia Fix project.**

---

## ⚡ QUICK RECOVERY (30 seconds)

**Problem**: Maia forgets existing tools in new contexts, builds duplicates
**Solution**: Always-load capability index + automate Phase 0 checks
**Status**: Check JSON file below for current phase

---

## 📋 RECOVERY SEQUENCE

### Step 1: Read Project Status (5 min)
```bash
# Quick status check
cat claude/data/CAPABILITY_AMNESIA_RECOVERY.json | grep -A 5 "current_phase"

# See what's been completed
cat claude/data/CAPABILITY_AMNESIA_RECOVERY.json | grep -A 20 "phase_progress"
```

### Step 2: Read Full Project Plan (10 min)
```bash
# Complete project details
open claude/data/CAPABILITY_AMNESIA_FIX_PROJECT.md

# Or read in terminal
cat claude/data/CAPABILITY_AMNESIA_FIX_PROJECT.md
```

### Step 3: Verify Completed Deliverables (2 min)
```bash
# Check if files from completed phases exist
ls -la claude/context/core/capability_index.md 2>/dev/null || echo "Phase 1: Not started"
grep "capability_index" claude/hooks/dynamic_context_loader.py 2>/dev/null || echo "Phase 2: Not started"
ls -la claude/hooks/capability_check_enforcer.py 2>/dev/null || echo "Phase 3: Not started"
ls -la claude/commands/save_state_tier1_quick.md 2>/dev/null || echo "Phase 4: Not started"
```

### Step 4: Resume from Current Phase
See CAPABILITY_AMNESIA_FIX_PROJECT.md for detailed phase instructions.

---

## 📊 PROJECT AT A GLANCE

**Total Phases**: 5
**Estimated Time**: 3-4 hours total
**Current Phase**: See JSON file

**Phases**:
1. ⏳ Create capability_index.md (1 hour)
2. ⏳ Integrate with context loader (30 min)
3. ⏳ Automate Phase 0 enforcement (1.5 hours)
4. ⏳ Create tiered save state (45 min)
5. ⏳ Test & validate (30 min)

---

## 🎯 WHY THIS MATTERS

**Your Feedback**: "Maia often works on something, completes something, but then doesn't update all the guidance required to remember what had just been created."

**Root Cause**: Smart context loading skips available.md and agents.md in many scenarios (minimal, simple, personal modes). New contexts have capability amnesia.

**The Fix**:
- Always-loaded capability_index.md (2-3K tokens, all 200+ tools/49 agents)
- Automated Phase 0 check (prevents duplicate builds)
- Simplified save state (70% time savings)

**Result**: Zero capability amnesia, 70% less overhead, Maia always remembers what exists.

---

## 📁 KEY FILES

**Project Plan** (READ THIS): `claude/data/CAPABILITY_AMNESIA_FIX_PROJECT.md`
**Recovery State**: `claude/data/CAPABILITY_AMNESIA_RECOVERY.json`
**This File**: `claude/data/implementation_checkpoints/CAPABILITY_AMNESIA_START_HERE.md`

---

## 🔥 ANTI-DRIFT PROTECTION

**If context compaction happens**:
1. You see this file → You know project is in progress
2. Read CAPABILITY_AMNESIA_RECOVERY.json → See current phase
3. Read CAPABILITY_AMNESIA_FIX_PROJECT.md → Get full context
4. Check deliverables exist → Verify progress
5. Resume from current phase → Continue work

**No confusion, no starting over, no project drift.**

---

**Ready to continue? Start with Step 1 above.**
