# Close Session - Pre-Shutdown Workflow

Comprehensive pre-shutdown checklist ensuring clean state before closing Claude Code window.

## Purpose

When preparing to close your Claude Code window, use this command to verify everything is saved, nothing is missed, and session context is properly cleaned up. This prevents data loss and ensures clean shutdown.

## Usage

```bash
/close-session
```

Or in conversation:
- "close session"
- "preparing to close window"
- "shutdown prep"

## What It Does - Comprehensive Checklist

**Phase 213 Enhancement**: Full pre-shutdown verification
**Phase 214 Enhancement**: Development file cleanup detection
**Phase PAI-v2**: Learning system integration

1. **Git Status Check**
   - Detects uncommitted changes
   - Shows modified files (first 10)
   - Offers to run `/save_state` interactively

2. **Documentation Currency Check**
   - Compares recent code changes vs SYSTEM_STATE.md timestamp
   - Warns if documentation may be outdated
   - Prompts to update docs before closing

3. **Active Background Processes Check**
   - Detects running background bash shells
   - Warns about processes that will be interrupted
   - Helps prevent data loss from incomplete tasks

4. **Checkpoint Currency Check**
   - Checks age of last checkpoint
   - Warns if >2 hours old with uncommitted changes
   - Suggests creating checkpoint before closing

5. **Development File Cleanup Check** ⭐ **Phase 214**
   - Detects versioned files (e.g., `tool_v2.py`, `script_v3.py`)
   - Finds misplaced test files (test_*.py outside tests/ directories)
   - Identifies build artifacts (.DS_Store, __pycache__, *.pyc)
   - Shows first 3 of each category with counts
   - Prevents development file accumulation

6. **PAI v2 Learning Analysis** ⭐ **NEW - Personal PAI v2**
   - Runs VERIFY phase to measure session success
   - Runs LEARN phase to extract patterns (if successful)
   - Saves session summary to Maia Memory for future context
   - Displays confidence score and extracted patterns
   - Enables cross-session learning and preference tracking

7. **Session File Cleanup**
   - Deletes `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json`
   - Displays closed agent and domain
   - Confirms clean shutdown

8. **Final Confirmation**
   - "Safe to close Claude Code window" message
   - Summary of any skipped items
   - Peace of mind before closing

## Interactive Flow

### Clean State (No Issues)
```
/close-session

🔍 Pre-shutdown check...

✅ All checks passed - clean state

📊 Running learning analysis...
   ✅ Session successful (confidence: 85%)
   📚 Extracted 2 pattern(s)
   💾 Summary saved to Maia Memory

✅ Agent session closed

============================================================
✅ Pre-shutdown complete
   Safe to close Claude Code window
============================================================
```

### Issues Detected (Offers save_state)
```
/close-session

🔍 Pre-shutdown check...

⚠️  Uncommitted changes detected:
    M claude/hooks/swarm_auto_loader.py
    M .claude/commands/close-session.md

⚠️  Recent code changes detected without SYSTEM_STATE.md update
   Last SYSTEM_STATE.md update: 2025-11-29 14:30

============================================================

📝 Run /save_state to commit changes and update docs? (y/n): y

🔄 Running save_state workflow...

⚠️  Please run 'save state' in the main Claude conversation
   Then run /close-session again
```

## When to Use

✅ **Use before:**
- Closing Claude Code window
- Taking a break from current work
- Switching to different project/context
- End of work session

✅ **Benefits:**
- Prevents uncommitted work loss
- Ensures documentation is current
- Catches background processes that would be interrupted
- Gives peace of mind before shutdown

## Example Workflow

```
Day 1-3: Working on PMP integration
         (PMP API Specialist agent persists across days)

Day 3: Code complete, testing done

Day 3: "/close-session"
       🔍 Pre-shutdown check...
       ⚠️  Uncommitted changes: 5 files
       ⚠️  SYSTEM_STATE.md not updated

       📝 Run /save_state? (y/n): y
       → Returns to run 'save state' in conversation

Day 3: "save state"
       → Documentation updated, committed, pushed

Day 3: "/close-session"
       ✅ All checks passed - clean state
       ✅ Agent session closed: pmp_api_specialist_agent
       ✅ Pre-shutdown complete - Safe to close window

Day 4: [Opens new Claude Code window]
       → Loads default agent (from user preferences)
       → Fresh start with clean state
```

## Technical Details

- **Command**: `python3 claude/hooks/swarm_auto_loader.py close_session`
- **Session File**: `/tmp/maia_active_swarm_session_{CONTEXT_ID}.json`
- **Context ID**: Stable Claude Code window PID (Phase 134.4)
- **Safety**: All checks use graceful degradation (never blocks)
- **Performance**: ~1-3 seconds (depends on git repo size)
- **Interactive**: Prompts for save_state if issues detected

## Checks Performed

| Check | Detection | Action |
|-------|-----------|--------|
| Git Status | Uncommitted changes | Show files, offer save_state |
| Documentation | SYSTEM_STATE.md older than code | Warn about stale docs |
| Background Processes | Running bash shells | Warn about interruption |
| Checkpoints | >2hr old with git changes | Suggest creating checkpoint |
| Development Cleanup | Versioned files, misplaced tests, build artifacts | Show counts and examples, remind to clean |
| **PAI v2 Learning** ⭐ | Active learning session | Run VERIFY + LEARN, save to Maia Memory |
| Session File | Active agent session | Delete and confirm |

## Related

- **save_state**: Full documentation + git commit workflow
- **Working Principle #15**: Automatic Agent Persistence system
- **Phase 134.7**: User-controlled session lifecycle management
- **Phase 213**: Enhanced pre-shutdown checklist
- **Phase PAI-v2**: Personal learning system integration
- **/memory**: Search past sessions in Maia Memory
