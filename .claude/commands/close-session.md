# Close Agent Session

Close the active agent session and restore natural agent routing.

## Purpose

When you finish working on a project or task, use this command to clear the persistent agent session. This ensures the next conversation will route naturally based on query content rather than continuing with the current agent.

## Usage

```bash
/close-session
```

Or in conversation:
- "close session"
- "clear agent session"
- "end agent session"

## What It Does

1. Checks for active agent session file (`/tmp/maia_active_swarm_session_{CONTEXT_ID}.json`)
2. Displays current agent and domain
3. Deletes the session file
4. Confirms natural routing is restored

## When to Use

✅ **Use after:**
- Completing a multi-day project
- Running `save state` to document work
- Finishing a specific task/domain
- Before starting work on unrelated topic

❌ **Don't use during:**
- Active work on same project (breaks continuity)
- Multi-turn troubleshooting session
- When you want agent to persist

## Example Workflow

```
Day 1-3: Working on Essential Eight ML3 implementation
         (Airlock agent persists across days)

Day 3: "save state"
       → Documentation updated, committed, pushed

Day 3: "/close-session"
       → ✅ Agent session closed
       → Agent: airlock_digital_specialist_agent
       → Domain: security
       → Next conversation will route naturally

Day 4: "Help with SRE incident response"
       → Routes naturally to SRE agent (not Airlock)
```

## Technical Details

- **Command**: `python3 claude/hooks/swarm_auto_loader.py close_session`
- **Session File**: `/tmp/maia_active_swarm_session_{CONTEXT_ID}.json`
- **Context ID**: Stable Claude Code window PID (Phase 134.4)
- **Safety**: Gracefully handles missing or corrupted sessions

## Related

- **save_state**: Document project progress before closing session
- **Working Principle #15**: Automatic Agent Persistence system
- **Phase 134.7**: User-controlled session lifecycle management
