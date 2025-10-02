# 🔄 SESSION RECOVERY PROTOCOL

## Purpose
This document defines how Maia (and new sessions) can rapidly reconstruct context after context window compression or session interruption.

## Recovery Time Target
**< 2 minutes** from new session start to full operational context

## 🚨 MANDATORY FIRST ACTIONS

When starting any new session, **ALWAYS** run these commands in order:

### 1. System Status Check
```bash
python3 claude/tools/maia_status.py
```
**Purpose:** Get comprehensive system status in 30 seconds
**Output:** Database stats, high-priority jobs, recent activity, progress

### 2. Current State Review
```bash
cat claude/context/session/current_state.md
```
**Purpose:** Understand current project focus and decisions made
**Output:** Progress, completed phases, next actions, blockers

### 3. High-Priority Jobs
```bash
python3 claude/tools/job_query_cli.py high-priority
```
**Purpose:** See active opportunities requiring attention
**Output:** Scored job opportunities with analysis

### 4. Recent Analysis
```bash
ls -la claude/analytics/*.md | tail -3
```
**Purpose:** Check latest analysis and decisions
**Output:** Most recent analysis files with timestamps

## 🧠 CONTEXT RECONSTRUCTION PATTERN

### Load Order (Critical)
1. **System Identity** (`claude/context/core/identity.md`)
2. **Current State** (`claude/context/session/current_state.md`)
3. **Database Status** (via `maia_status.py`)
4. **Active Tasks** (latest analysis files)

### Context Hints
- **If high-priority jobs exist:** Focus on job search automation
- **If database has >50 jobs:** System is mature, focus on optimization
- **If recent analysis files:** Continue interrupted work
- **If no current_state.md:** Start with fresh context loading

## 🔧 TOOLS FOR RAPID CONTEXT

### Status Commands
- `maia_status.py` - Complete system overview
- `job_query_cli.py stats` - Database statistics
- `job_query_cli.py high-priority` - Current opportunities
- `job_query_cli.py recent` - Recent job activity

### Quick Context Files
- `current_state.md` - Session state and progress
- `identity.md` - System purpose and capabilities
- `job_preferences.md` - User profile and requirements

## 📝 SESSION HANDOFF PROTOCOL

### When Context Window Fills:
1. **Update current_state.md** with latest progress
2. **Note critical decisions** that can't be lost
3. **Mark specific next actions**
4. **Save any interim results** to appropriate files

### Template for Handoffs:
```markdown
## URGENT: Next Session Must
- [ ] [Specific immediate action]
- [ ] [Any critical context that can't be recreated]
- [ ] [Current blockers or dependencies]

## Current State
- Progress: [X% complete on Y project]
- Last completed: [specific achievement]
- Database status: [jobs/analysis counts]
```

## 🎯 SUCCESS METRICS

A successful context recovery should achieve:
- **Full understanding** of current project status
- **Immediate access** to relevant data (jobs, analysis)
- **Clear next actions** without re-research
- **No lost decisions** or duplicated work

## 🔄 CONTINUOUS IMPROVEMENT

Each session should update:
1. **current_state.md** - Keep progress current
2. **This file** - If recovery process improves
3. **Tools** - Add status commands as needed

**The goal: Make context window compression transparent to productivity.**
