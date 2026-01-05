# Phase 237 Restart Guide
**Pre-Compaction Learning Capture - Hook Testing Continuation**

## Current Status

✅ **ALL Phase 1 Deliverables Complete**:
- Archive system (16 tests passing)
- Learning extraction (20 tests passing)
- Retrieval API (21 tests passing)
- Pre-compaction hook (13 tests passing)
- Documentation (PRECOMPACT_README.md)
- Production config (precompact_hook_config.json)

✅ **Hook Configuration Installed**:
- Location: `~/.claude/settings.local.json`
- Matcher: `"manual"` (triggers on `/compact` command)
- Timeout: 5000ms

⚠️ **Waiting on**: Hook configuration reload (requires Claude Code restart)

---

## What Happened Before Restart

1. **Built complete pre-compaction learning capture system** (Phase 237)
2. **Installed hook configuration** in `~/.claude/settings.local.json`
3. **Ran `/compact` to test** - compaction succeeded but hook didn't fire
4. **Diagnosed**: Claude Code needs restart to load new hook configuration
5. **Verified hook works**: Manual test succeeded perfectly (1ms execution time)

**Root cause**: Hooks are loaded at Claude Code startup. Adding PreCompact hook mid-session requires restart.

---

## Immediate Next Steps After Restart

### Step 1: Verify Hook is Loaded
```bash
# Check hook configuration
cat ~/.claude/settings.local.json | grep -A 15 "PreCompact"
```

Expected output:
```json
"PreCompact": [
  {
    "matcher": "manual",
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/pre_compaction_learning_capture.py",
        "timeout": 5000
      }
    ]
  }
]
```

### Step 2: Trigger Manual Compaction
```bash
# In Claude Code, run:
/compact
```

### Step 3: Verify Hook Executed
```bash
# Check debug log for new entries
tail -10 ~/.maia/logs/pre_compaction_debug.log

# Expected output (timestamps will be current):
# 2026-01-06T[TIME] [DEBUG] Processing hook for context [CONTEXT_ID], trigger: manual
# 2026-01-06T[TIME] [DEBUG] Success: snapshot_id=[ID], learnings=[N], time=[X]ms
```

### Step 4: Verify Conversation Archived
```python
python3 -c "
from claude.tools.learning.archive import get_archive

# Get current context ID first
import subprocess
context_id = subprocess.check_output(
    ['python3', 'claude/hooks/swarm_auto_loader.py', 'get_context_id'],
    text=True
).strip()

print(f'Context ID: {context_id}')

# Check if archived
archive = get_archive()
conversation = archive.get_conversation(context_id)

if conversation:
    print(f'✅ CONVERSATION ARCHIVED!')
    print(f'Snapshot ID: {conversation[\"snapshot_id\"]}')
    print(f'Messages: {conversation[\"message_count\"]}')
    print(f'Learnings: {conversation[\"learning_count\"]}')
    print(f'Tools used: {conversation[\"tool_usage_stats\"]}')
else:
    print(f'❌ No archive found for context {context_id}')
"
```

### Step 5: Check Metrics
```bash
sqlite3 ~/.maia/data/conversation_archive.db "
SELECT
    context_id,
    trigger_type,
    execution_time_ms,
    messages_processed,
    learnings_extracted,
    success,
    datetime(compaction_timestamp/1000, 'unixepoch') as timestamp
FROM compaction_metrics
ORDER BY compaction_timestamp DESC
LIMIT 5
"
```

---

## Success Criteria

Phase 237 Day 1 is **COMPLETE** when:

- [x] Archive system implemented with 16 tests passing
- [x] Learning extraction implemented with 20 tests passing
- [x] Retrieval API implemented with 21 tests passing
- [x] Pre-compaction hook implemented with 13 tests passing
- [x] Hook configuration installed in settings.local.json
- [ ] **Hook successfully captures conversation during `/compact`** ← ONLY REMAINING TASK
- [ ] **Logs show successful execution with <5s performance**
- [ ] **Database contains archived conversation with learnings**

---

## If Hook Still Doesn't Fire

### Troubleshooting Steps:

1. **Verify environment variable**:
   ```bash
   echo $CLAUDE_PROJECT_DIR
   # Should output: /Users/naythandawe/maia
   ```

2. **Test hook manually** (confirm it still works):
   ```bash
   echo '{
     "session_id": "test_after_restart",
     "transcript_path": "/tmp/test.jsonl",
     "trigger": "manual"
   }' > /tmp/hook_input.json

   echo '{"type": "user_message", "content": "test"}' > /tmp/test.jsonl

   cat /tmp/hook_input.json | python3 "$MAIA_ROOT/claude/hooks/pre_compaction_learning_capture.py"
   ```

3. **Check for hook errors**:
   ```bash
   tail -20 ~/.maia/logs/pre_compaction_errors.log
   ```

4. **Alternative: Add auto matcher**:
   If manual matcher doesn't work, try adding auto-compaction:
   ```json
   "PreCompact": [
     {
       "matcher": "manual",
       "hooks": [...]
     },
     {
       "matcher": "auto",
       "hooks": [...]
     }
   ]
   ```

---

## Phase 2 Planning (After Hook Validation)

Once hook is verified working:

1. **Enable auto-compaction** (add "auto" matcher)
2. **PAI v2 integration** (learning ID tracking)
3. **Enhanced pattern library** (more learning types)
4. **Conversation analytics dashboard**
5. **Performance optimization** for 50K+ message conversations

---

## Files to Reference

| File | Purpose |
|------|---------|
| [PRECOMPACT_README.md](../../../tools/learning/PRECOMPACT_README.md) | Comprehensive system documentation |
| [precompact_hook_config.json](../../../config/precompact_hook_config.json) | Production hook configuration |
| [PRECOMPACT_LEARNING_CAPTURE.md](PRECOMPACT_LEARNING_CAPTURE.md) | Implementation plan and progress |
| [pre_compaction_learning_capture.py](../../../hooks/pre_compaction_learning_capture.py) | Hook implementation |
| [archive.py](../../../tools/learning/archive.py) | Conversation archival system |
| [extraction.py](../../../tools/learning/extraction.py) | Learning extraction engine |
| [retrieval.py](../../../tools/learning/retrieval.py) | Retrieval API |

---

## Test Commands

```bash
# Run all Phase 237 tests
pytest tests/learning/test_archive.py -v
pytest tests/learning/test_extraction.py -v
pytest tests/learning/test_retrieval.py -v
pytest tests/learning/test_pre_compaction_hook.py -v

# Quick smoke test (should see 70 tests pass)
pytest tests/learning/ -v --tb=short

# Performance test
pytest tests/learning/test_pre_compaction_hook.py::test_hook_performance -v
```

---

## Quick Resume Command

After restart, to quickly get back to testing:

```bash
# Load context + verify everything
/init

# Then immediately test compaction
/compact

# Then verify capture
python3 -c "from claude.tools.learning.retrieval import get_conversation_stats; print(get_conversation_stats())"
```

---

## Context for Next Session

**User's last request**: "option 1" (restart Claude Code to load hook configuration)

**What I was doing**: Preparing restart by creating this guide and committing all work.

**What to do next**:
1. Run `/compact` command
2. Verify hook captured the conversation
3. Celebrate Phase 237 Day 1 complete! 🎉
4. (Optional) Plan Phase 2 implementation

---

**Created**: 2026-01-06
**Session**: Context ID 27009
**Phase**: 237 - Pre-Compaction Learning Capture
**Status**: Day 1 COMPLETE (pending final hook validation)
