# 🚀 Automatic Agent Persistence System - START HERE

**If you see this file, you're resuming the Automatic Agent Persistence System project.**

---

## ⚡ QUICK RECOVERY (30 seconds)

**Problem**: Phase 121 routing suggestions displayed but agents not auto-loaded, causing 60-70% token waste and 25-40% quality loss
**Solution**: Implement Working Principle #15 with full SwarmOrchestrator integration for automatic agent loading, session persistence, and context-aware domain switching
**Status**: Check JSON file below for current phase

---

## 📋 RECOVERY SEQUENCE

### Step 1: Read Project Status (5 min)
```bash
# Quick status check
cat claude/data/AGENT_PERSISTENCE_134_RECOVERY.json | grep -A 5 "current_phase"

# See what's been completed
cat claude/data/AGENT_PERSISTENCE_134_RECOVERY.json | grep -A 20 "phase_progress"
```

### Step 2: Read Full Project Plan (10 min)
```bash
# Complete project details
open claude/data/AGENT_PERSISTENCE_134.md

# Or read in terminal
cat claude/data/AGENT_PERSISTENCE_134.md
```

### Step 3: Verify Completed Deliverables (2 min)
```bash
# Check if files from completed phases exist
ls -la claude/data/AGENT_PERSISTENCE_TDD_REQUIREMENTS.md 2>/dev/null || echo "Phase 0: Not started"
ls -la claude/tools/orchestration/test_automatic_agent_persistence.py 2>/dev/null || echo "Phase 1: Not started"
ls -la claude/hooks/user-prompt-submit (Stage 0.8 enhanced) 2>/dev/null || echo "Phase 2: Not started"
ls -la claude/tools/orchestration/agent_swarm.py (_execute_agent implemented) 2>/dev/null || echo "Phase 3: Not started"
ls -la CLAUDE.md instruction update + session state reader 2>/dev/null || echo "Phase 4: Not started"
ls -la Domain change detection + context handoff logic 2>/dev/null || echo "Phase 5: Not started"
ls -la End-to-end test results + performance profile 2>/dev/null || echo "Phase 6: Not started"
ls -la Working Principle #15 status updated, user guide, SYSTEM_STATE.md Phase 134 entry 2>/dev/null || echo "Phase 7: Not started"
```

### Step 4: Resume from Current Phase
See claude/data/AGENT_PERSISTENCE_134.md for detailed phase instructions.

---

## 📊 PROJECT AT A GLANCE

**Total Phases**: 7
**Estimated Time**: 2 hours, 4 hours, 3 hours, 4 hours, 2 hours, 3 hours, 3 hours, 2 hours total
**Current Phase**: See JSON file

**Phases**:
1. ⏳ Requirements Discovery (TDD Phase 0) (2 hours)
2. ⏳ Test Design (TDD Phase 1) (4 hours)
3. ⏳ Hook Enhancement (Stage 0.8 Modification) (3 hours)
4. ⏳ SwarmOrchestrator Integration (4 hours)
5. ⏳ Maia Agent Check Logic (2 hours)
6. ⏳ Session Persistence & Domain Switching (3 hours)
7. ⏳ Integration Testing (3 hours)
8. ⏳ Documentation & Deployment (2 hours)

---

## 🎯 WHY THIS MATTERS

**User Feedback/Request**: "Maia only loads a dedicated agent when I ask and then regularly switches back to maia. Quality of work performed is always lower quality and high token consumption from base Maia. It seems like Maia only loads a dedicated agent when I ask and then regularly switches back to maia."

**Root Cause**: Phase 121 routing suggestions displayed but agents not auto-loaded, causing 60-70% token waste and 25-40% quality loss

**The Fix**:
Implement Working Principle #15 with full SwarmOrchestrator integration for automatic agent loading, session persistence, and context-aware domain switching

**Result**: TBD

---

## 📁 KEY FILES

**Project Plan** (READ THIS): `claude/data/AGENT_PERSISTENCE_134.md`
**Recovery State**: `claude/data/AGENT_PERSISTENCE_134_RECOVERY.json`
**This File**: `claude/data/implementation_checkpoints/AGENT_PERSISTENCE_134_START_HERE.md`

---

## 🔥 ANTI-DRIFT PROTECTION

**If context compaction happens**:
1. You see this file → You know project is in progress
2. Read claude/data/AGENT_PERSISTENCE_134_RECOVERY.json → See current phase
3. Read claude/data/AGENT_PERSISTENCE_134.md → Get full context
4. Check deliverables exist → Verify progress
5. Resume from current phase → Continue work

**No confusion, no starting over, no project drift.**

---

**Ready to continue? Start with Step 1 above.**
