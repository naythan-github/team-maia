# Close Session

Clean shutdown verification before closing Claude Code window.

**Execution**:
Run `python3 claude/hooks/swarm_auto_loader.py close_session`

**Checks Performed**:
- Git status (uncommitted changes)
- Background processes (running shells)
- PAI v2 Learning (VERIFY + LEARN phases)
- Session file cleanup

**When to Use**:
Before closing window, end of session, switching projects.
