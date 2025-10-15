# 🚀 {{PROJECT_NAME}} - START HERE

**If you see this file, you're resuming the {{PROJECT_NAME}} project.**

---

## ⚡ QUICK RECOVERY (30 seconds)

**Problem**: {{PROBLEM_ONE_LINE}}
**Solution**: {{SOLUTION_ONE_LINE}}
**Status**: Check JSON file below for current phase

---

## 📋 RECOVERY SEQUENCE

### Step 1: Read Project Status (5 min)
```bash
# Quick status check
cat {{RECOVERY_JSON_PATH}} | grep -A 5 "current_phase"

# See what's been completed
cat {{RECOVERY_JSON_PATH}} | grep -A 20 "phase_progress"
```

### Step 2: Read Full Project Plan (10 min)
```bash
# Complete project details
open {{PROJECT_FILE_PATH}}

# Or read in terminal
cat {{PROJECT_FILE_PATH}}
```

### Step 3: Verify Completed Deliverables (2 min)
```bash
# Check if files from completed phases exist
{{DELIVERABLE_CHECK_COMMANDS}}
```

### Step 4: Resume from Current Phase
See {{PROJECT_FILE_PATH}} for detailed phase instructions.

---

## 📊 PROJECT AT A GLANCE

**Total Phases**: {{TOTAL_PHASES}}
**Estimated Time**: {{TOTAL_DURATION}} total
**Current Phase**: See JSON file

**Phases**:
{{PHASE_SUMMARY_LIST}}

---

## 🎯 WHY THIS MATTERS

**User Feedback/Request**: "{{USER_FEEDBACK}}"

**Root Cause**: {{ROOT_CAUSE_ONE_LINE}}

**The Fix**:
{{SOLUTION_BULLET_POINTS}}

**Result**: {{EXPECTED_RESULT}}

---

## 📁 KEY FILES

**Project Plan** (READ THIS): `{{PROJECT_FILE_PATH}}`
**Recovery State**: `{{RECOVERY_JSON_PATH}}`
**This File**: `{{START_HERE_PATH}}`

---

## 🔥 ANTI-DRIFT PROTECTION

**If context compaction happens**:
1. You see this file → You know project is in progress
2. Read {{RECOVERY_JSON_PATH}} → See current phase
3. Read {{PROJECT_FILE_PATH}} → Get full context
4. Check deliverables exist → Verify progress
5. Resume from current phase → Continue work

**No confusion, no starting over, no project drift.**

---

**Ready to continue? Start with Step 1 above.**
