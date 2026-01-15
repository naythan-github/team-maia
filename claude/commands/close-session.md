# Close Session - Pre-Shutdown Workflow

**Purpose**: Clean shutdown verification before closing Claude Code window
**Command**: `/close-session` | "close session" | "shutdown prep"
**Status**: ✅ Production | **Phase 233.2**: Direct save_state.py integration

---

## Execution

```bash
python3 claude/hooks/swarm_auto_loader.py close_session
```

## How Learning Works (Phase 236)

Learning sessions start **automatically** on every user prompt (Stage 0.05 in user-prompt-submit hook).
No manual action needed - just use `/close-session` at end to capture insights.

## Checks Performed

| Check | Detection | Action |
|-------|-----------|--------|
| Git Status | Uncommitted changes | Show files, offer save_state |
| Documentation | SYSTEM_STATE.md older than code | Warn stale docs |
| Background Processes | Running bash shells | Warn interruption |
| Checkpoints | >2hr old with changes | Suggest checkpoint |
| Dev Cleanup | Versioned files, misplaced tests, artifacts | Show counts |
| **/finish Completion** | No completion record for session | **Warn to run /finish first** |
| PAI v2 Learning | Active session | Run VERIFY + LEARN, save to Memory |
| Session File | Active agent | Delete, confirm |

## Outcomes

**Clean**: All pass → "Safe to close Claude Code window"
**Issues**: Shows warnings → User says "yes" → Runs `save_state.py` directly → Continues cleanup

## Technical

- **Session**: `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json`
- **Context ID**: Stable window PID (Phase 134.4/230)
- **Safety**: Graceful degradation (never blocks)
- **Performance**: 1-3 seconds

## When to Use

Before closing window | End of session | Switching projects | Taking break

## Related

- `/finish`: Completion verification (run before close-session)
- `save_state`: Documentation + git commit
- `/memory`: Search past sessions
- Phase 134.7/213/214/PAI-v2: Session lifecycle enhancements
