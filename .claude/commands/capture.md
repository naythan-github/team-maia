# Capture Learning

Manually trigger conversation learning capture to archive database.

**Execution**:
Run `bash claude/hooks/capture_skill.sh`

**What It Captures**:
- Conversation transcript and context
- Learning patterns (decisions, solutions, breakthroughs)
- Tool usage patterns
- Agent interactions

**When to Use**:
- Before context compaction
- End of work session to preserve progress
- After significant breakthroughs or decisions
- Before long breaks

**Related**:
- `/close-session` - Includes learning capture automatically
- Phase 237: Pre-Compaction Learning Capture System
