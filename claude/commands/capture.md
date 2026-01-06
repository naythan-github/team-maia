# Capture Learning Command

## Purpose
Manually trigger conversation learning capture to archive database. Use this before compaction to preserve conversation learnings, decisions, and tool usage patterns.

## When to Use
- Before running `/compact` (until PreCompact hooks are fixed)
- End of work session to archive progress
- After significant breakthroughs or decisions
- Before context-heavy operations

## Implementation

Execute the pre-compaction learning capture script directly:

```bash
python3 claude/hooks/pre_compaction_learning_capture.py <<EOF
{
  "session_id": "$(python3 claude/hooks/swarm_auto_loader.py get_context_id)",
  "transcript_path": "",
  "trigger": "skill",
  "hook_event_name": "Capture"
}
EOF
```

Then verify capture:
```bash
tail -3 ~/.maia/logs/pre_compaction_debug.log
```

## Output
- Logs capture details to `~/.maia/logs/pre_compaction_debug.log`
- Stores conversation in `~/.maia/data/conversation_archive.db`
- Returns confirmation with snapshot ID and learning count

## Related
- `/compact` - Compact conversation context (run AFTER /capture)
- `/close-session` - End session with learning verification
- Phase 237: Pre-Compaction Learning Capture System

## Known Issues
- **Bug Workaround**: Created due to Claude Code Issues [#13572](https://github.com/anthropics/claude-code/issues/13572) and [#13668](https://github.com/anthropics/claude-code/issues/13668)
- PreCompact hooks don't fire on manual `/compact` (will be deprecated when fixed)
