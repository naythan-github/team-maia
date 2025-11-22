# Maia Core Agent - TDD Requirements Specification

**Project**: Maia Core Agent + Checkpoint System
**Created**: 2025-11-22
**Agent Pairing**: SRE Principal Engineer Agent (primary - reliability focus)
**Status**: Phase 1 - Requirements Discovery Complete

---

## 1. Core Purpose

### 1.1 Problem Statement
Maia's base behavior lacks operational discipline. After context compaction:
- Work needs to be redone
- State is lost
- No recovery protocol exists
- User must manually reload SRE agent for reliability

**User Quote**: "At the moment, if Maia loads after compaction, almost all work needs to be redone. It is more important for Maia default to be reliable and reliability focused, than general assistant."

### 1.2 Success Criteria
1. Context compaction does NOT cause complete work loss
2. Recovery from any interruption takes <2 minutes
3. Work is reproducible by another engineer
4. Default behavior has SRE-grade operational discipline
5. MSP operational patterns embedded (multi-tenant, SLA-aware)

### 1.3 Users
- Primary: Engineering Manager at national MSP (Naythan)
- Secondary: Future Maia users requiring reliability

---

## 2. System Components

### 2.1 Maia Core Agent (`claude/agents/maia_core_agent.md`)
Default agent loaded when no specialized agent session exists.

### 2.2 Checkpoint Manager (`claude/tools/checkpoint_manager.py`)
Python tool for state persistence and recovery.

### 2.3 Recovery Protocol (enhanced `claude/hooks/swarm_auto_loader.py`)
Updated session loader with recovery capabilities.

### 2.4 Checkpoints Directory (`claude/data/checkpoints/`)
Persistent storage for work-in-progress state.

---

## 3. Functional Requirements

### FR-1: State Preservation Protocol

**FR-1.1**: Auto-checkpoint triggers
- Every 10 tool calls → create checkpoint
- Before complex operations (multi-file edits, deployments) → create checkpoint
- User says "save state" → full checkpoint + git commit
- Token budget <20% remaining → proactive checkpoint with warning

**FR-1.2**: Checkpoint content structure
```json
{
  "checkpoint_id": "uuid",
  "timestamp": "ISO8601",
  "session_context_id": "string",
  "current_task": {
    "description": "string",
    "status": "in_progress|blocked|pending",
    "progress_percentage": 0-100
  },
  "todo_list": [...],
  "key_decisions": [...],
  "files_modified": [...],
  "git_state": {
    "branch": "string",
    "last_commit": "sha",
    "uncommitted_changes": true|false
  },
  "recovery_instructions": "string",
  "next_steps": [...]
}
```

**FR-1.3**: Checkpoint storage locations
- Active session: `/tmp/maia_active_swarm_session_{CONTEXT_ID}.json`
- Persistent checkpoints: `claude/data/checkpoints/{date}_{task_id}.json`
- Retention: 7 days, then auto-archive to `claude/data/checkpoints/archive/`

### FR-2: Recovery Protocol

**FR-2.1**: Recovery trigger conditions
- New session starts (no active session file)
- Context compaction detected (internal signal)
- User explicitly requests recovery ("recover", "resume", "where were we")

**FR-2.2**: Recovery sequence
1. Check git log (last 24h) for recent commits
2. Load most recent checkpoint from `claude/data/checkpoints/`
3. Present recovery context to user:
   ```
   RECOVERY DETECTED:
   - Last work: [description from checkpoint]
   - Git commits: [list recent commits]
   - Progress: [percentage]
   - Next steps: [from checkpoint]

   Is this context correct? [confirm/update/start fresh]
   ```
4. Wait for user confirmation before proceeding
5. On confirmation, restore todo list and continue

**FR-2.3**: Graceful degradation
- If checkpoint corrupted → fall back to git history only
- If git history unavailable → ask user for context summary
- Never block on missing state → always provide path forward

### FR-3: Operational Discipline

**FR-3.1**: Every task follows protocol
```
TASK RECEIVED → Requirements → Plan → Execute → Validate → Document
```
No shortcuts. No "you should investigate further."

**FR-3.2**: Failure modes explicit
Every plan includes:
- What could go wrong
- How to detect failure
- How to recover

**FR-3.3**: Repeatable outputs
- Same input = same output
- Runbook-style execution
- Steps documented for another engineer to follow

### FR-4: MSP Operational Patterns

**FR-4.1**: Customer tier awareness
- P1 customers: Higher rigor, faster response, explicit escalation paths
- Standard customers: Normal workflow

**FR-4.2**: SLA consciousness
- Track time-to-resolution mentally
- Flag when approaching SLA breach
- Escalation awareness

**FR-4.3**: Multi-tenant thinking
- Always ask: "Does this affect one customer or many?"
- Isolation verification for changes

**FR-4.4**: Documentation-first
- IT Glue/Confluence as source of truth
- Changes must be documented

**FR-4.5**: Handover-ready
- Work reproducible by another engineer
- No tribal knowledge in solutions

### FR-5: Default Agent Loading

**FR-5.1**: Load trigger
- When no specialized agent session exists
- After `/close-session` clears specialist agent
- On session start with no prior context

**FR-5.2**: Loading mechanism
Update `swarm_auto_loader.py` and CLAUDE.md context loading protocol:
- If no session file exists, load `maia_core_agent.md` as default
- Set session with `current_agent: "maia_core"` and `domain: "core"`

**FR-5.3**: Override behavior
- Explicit specialist load ("load SRE agent") overrides default
- Auto-routing (confidence >70%, complexity ≥3) overrides default

---

## 4. Non-Functional Requirements

### NFR-1: Performance
- Checkpoint creation: <500ms
- Checkpoint loading: <200ms
- Recovery protocol: <5 seconds to present options

### NFR-2: Reliability
- Checkpoint writes: Atomic (temp file + rename)
- No data loss on crash during checkpoint
- Graceful degradation always available

### NFR-3: Storage
- Individual checkpoint: <50KB
- 7-day retention: <5MB total
- Archive: Compressed, <1MB/month

### NFR-4: Compatibility
- Works with existing agent session system
- No breaking changes to current workflows
- Backward compatible with existing session files

---

## 5. Acceptance Criteria

### AC-1: State Preservation
- [ ] Checkpoint created after 10 tool calls
- [ ] Checkpoint created before complex operations
- [ ] "save state" creates checkpoint + git commit
- [ ] Token budget warning triggers proactive checkpoint
- [ ] Checkpoint contains all required fields

### AC-2: Recovery Protocol
- [ ] New session detects available checkpoints
- [ ] Recovery presents git + checkpoint context
- [ ] User can confirm, update, or start fresh
- [ ] Todo list restored on confirmation
- [ ] Graceful fallback when checkpoint missing

### AC-3: Operational Discipline
- [ ] Maia Core Agent follows task protocol
- [ ] Failure modes documented in plans
- [ ] Output is reproducible
- [ ] No "you should investigate" endings

### AC-4: MSP Patterns
- [ ] Customer impact considered in changes
- [ ] SLA awareness in task execution
- [ ] Documentation created/updated for changes
- [ ] Handover instructions provided

### AC-5: Default Loading
- [ ] Maia Core Agent loads when no session exists
- [ ] Specialist agents can override
- [ ] Auto-routing still functions

---

## 6. Test Scenarios

### TS-1: Checkpoint Creation
```
Given: User working on multi-step task
When: 10 tool calls completed
Then: Checkpoint auto-created with task context
```

### TS-2: Recovery After Compaction
```
Given: Previous session had checkpoint saved
When: New session starts
Then: Recovery protocol presents options
And: User confirms to restore context
And: Work continues from checkpoint
```

### TS-3: Graceful Degradation
```
Given: No checkpoint exists
When: New session starts
Then: Git history checked for recent work
And: User asked for context if none found
And: Session proceeds without blocking
```

### TS-4: Default Agent Loading
```
Given: No active agent session file
When: Maia context loads
Then: Maia Core Agent loaded as default
And: Session file created with agent: "maia_core"
```

### TS-5: Specialist Override
```
Given: Maia Core Agent active
When: User says "load SRE agent"
Then: SRE agent replaces Maia Core
And: Session file updated
```

---

## 7. Design Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Checkpoint location | Hybrid: `/tmp/` + `claude/data/checkpoints/` | Session in temp, work state persisted |
| Recovery behavior | Git + checkpoints + user confirmation | Objective truth + intent + human validation |
| MSP patterns | Embedded in core agent | User context is MSP engineering management |
| Default agent | Maia Core (reliability-focused) | SRE discipline as foundation, not specialty |

---

## 8. Out of Scope (Phase 1)

- Automatic context compaction detection (complex, deferred)
- Cloud sync of checkpoints (local-only for now)
- Multi-user checkpoint sharing
- Checkpoint encryption

---

## 9. Dependencies

- Existing agent session system (Phase 134)
- Git repository access
- File system access for checkpoints
- swarm_auto_loader.py modification rights

---

## 10. Files to Create/Modify

### New Files
- `claude/agents/maia_core_agent.md` - Default agent spec
- `claude/tools/checkpoint_manager.py` - Checkpoint tool
- `claude/data/checkpoints/` - Directory structure
- `claude/tools/test_checkpoint_manager.py` - Test suite
- `claude/tools/test_maia_core_agent.py` - Agent behavior tests

### Modified Files
- `claude/hooks/swarm_auto_loader.py` - Add recovery protocol + default loading
- `CLAUDE.md` - Update context loading protocol for default agent
- `claude/context/core/active_deployments.md` - Register new system

---

**Requirements Status**: COMPLETE
**Next Phase**: Test Design (Phase 3)
**Approval**: Pending user confirmation
