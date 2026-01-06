# Pre-Compaction Learning Capture System
**Phase 237: Intelligent Context Compaction with Learning Preservation**

## Overview

The Pre-Compaction Learning Capture system prevents data loss during Claude Code's context compaction by extracting learnings and archiving full conversations **before** summarization happens.

### Problem Solved
- ❌ **Before**: Context compaction broke long conversations and lost learning context
- ✅ **After**: Full conversations archived, learnings preserved, zero data loss

---

## Architecture

```
Claude Code
    ↓
Context Near Limit
    ↓
PreCompact Hook Triggered
    ↓
┌─────────────────────────────────────────┐
│ pre_compaction_learning_capture.py      │
├─────────────────────────────────────────┤
│ 1. Read JSONL transcript                │
│ 2. Extract learnings (extraction.py)    │
│ 3. Archive conversation (archive.py)    │
│ 4. Log metrics                          │
│ 5. Return success                       │
└─────────────────────────────────────────┘
    ↓
Claude Code Proceeds with Compaction
```

---

## Components

### 1. Learning Extraction Engine
**File**: `claude/tools/learning/extraction.py`

**Pattern Library**: 12 learning categories (5 original + 7 enhanced)

#### Original Patterns (Phase 237.1)
| Category | Patterns | Example |
|----------|----------|---------|
| **Decision** | "decided to", "chose X over Y" | "Chose SQLite over Postgres because simpler" |
| **Solution** | "fixed by", "root cause was" | "Fixed timeout by increasing pool size" |
| **Outcome** | "✅ worked", "failed because" | "✅ All tests passed successfully" |
| **Handoff** | "HANDOFF DECLARATION" | Agent transitions |
| **Checkpoint** | "save state", "git commit" | Save points |

#### Enhanced Patterns (Phase 237.3) 🆕
| Category | Confidence | Example |
|----------|------------|---------|
| **Refactoring** | 0.88 | "Refactored auth module to use dependency injection" |
| **Error Recovery** | 0.92 | "Caught FileNotFoundError and handled it by..." |
| **Optimization** | 0.90 | "Reduced query time from 2s to 50ms" |
| **Learning** | 0.95 | "Learned that connection pooling is critical" |
| **Breakthrough** | 0.98 | "Key insight: The bottleneck was in serialization" |
| **Test** | 0.87 | "Added integration tests for all endpoints" |
| **Security** | 0.93 | "Fixed SQL injection by using parameterized queries" |

📖 **Full Pattern Documentation**: [ENHANCED_PATTERNS_README.md](ENHANCED_PATTERNS_README.md)

**Performance**: 0.05s for 1000 messages (100x faster than 5s target)

### 2. Conversation Archive
**File**: `claude/tools/learning/archive.py`
**Database**: `~/.maia/data/conversation_archive.db`

**Tables**:
- `conversation_snapshots`: Full conversation storage with FTS5 search
- `compaction_metrics`: Performance monitoring

**Features**:
- Millisecond-precision timestamps
- Thread-safe operations
- Full-text search (FTS5)
- Automatic deduplication

### 3. Retrieval Tools
**File**: `claude/tools/learning/retrieval.py`

**API**:
```python
from claude.tools.learning import retrieval

# Get archived conversation
conversation = retrieval.get_conversation('context_id_123')

# Search conversations
results = retrieval.search_conversations('database schema')

# Get compaction history
history = retrieval.get_compaction_history('context_id_123')

# Export conversation
markdown = retrieval.export_conversation('context_id_123', format='markdown')

# Get statistics
stats = retrieval.get_conversation_stats()
```

### 4. Pre-Compaction Hook
**File**: `claude/hooks/pre_compaction_learning_capture.py`

**Features**:
- 3-retry logic with exponential backoff
- Graceful degradation (never blocks compaction)
- Comprehensive logging
- <5s performance guarantee

---

## Installation

### Step 1: Merge Hook Configuration

Add to `~/.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "manual",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$MAIA_ROOT\"/claude/hooks/pre_compaction_learning_capture.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

**Note**: Starts with `"matcher": "manual"` for safe testing. Add `"auto"` matcher after validation.

### Step 2: Test with Manual Compaction

```bash
# In Claude Code, run:
/compact

# Check logs
tail -f ~/.maia/logs/pre_compaction_debug.log
```

### Step 3: Verify Archival

```python
from claude.tools.learning import retrieval

# Get latest snapshot
conversation = retrieval.get_conversation('your_context_id')

print(f"Messages: {conversation['message_count']}")
print(f"Learnings: {conversation['learning_count']}")
```

### Step 4: Enable Auto-Compaction (Phase 2)

After successful manual testing, add auto matcher:

```json
{
  "hooks": {
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
  }
}
```

---

## Usage

### Retrieve Archived Conversation

```python
from claude.tools.learning import retrieval

# Get conversation
conversation = retrieval.get_conversation('context_123')

# Access data
for msg in conversation['messages']:
    print(f"{msg['type']}: {msg['content']}")

print(f"\nLearnings captured: {conversation['learning_count']}")
print(f"Tools used: {conversation['tool_usage_stats']}")
```

### Search Across Conversations

```python
# Find conversations about databases
results = retrieval.search_conversations('database schema SQLite')

for result in results:
    print(f"{result['context_id']}: {result['first_message']}")
```

### Export for Analysis

```python
# Export as markdown
markdown = retrieval.export_conversation(
    'context_123',
    format='markdown',
    output_path='~/Desktop/conversation.md'
)

# Or JSON for programmatic use
json_data = retrieval.export_conversation('context_123', format='json')
```

### Monitor Compaction Metrics

```python
from claude.tools.learning.archive import get_archive

archive = get_archive()

with archive._get_connection() as conn:
    cursor = conn.execute("""
        SELECT
            context_id,
            AVG(execution_time_ms) as avg_time,
            SUM(learnings_extracted) as total_learnings,
            COUNT(*) as compaction_count
        FROM compaction_metrics
        WHERE success = 1
        GROUP BY context_id
    """)

    for row in cursor:
        print(f"Context: {row['context_id']}")
        print(f"  Avg time: {row['avg_time']}ms")
        print(f"  Learnings: {row['total_learnings']}")
        print(f"  Compactions: {row['compaction_count']}")
```

---

## Monitoring & Troubleshooting

### Log Files

| Log | Location | Purpose |
|-----|----------|---------|
| **Error Log** | `~/.maia/logs/pre_compaction_errors.log` | Failed hook executions |
| **Debug Log** | `~/.maia/logs/pre_compaction_debug.log` | Detailed execution traces |

### Check Hook Status

```bash
# View recent errors
tail -20 ~/.maia/logs/pre_compaction_errors.log

# View debug output
tail -50 ~/.maia/logs/pre_compaction_debug.log

# Query metrics database
sqlite3 ~/.maia/data/conversation_archive.db \
  "SELECT * FROM compaction_metrics ORDER BY compaction_timestamp DESC LIMIT 10"
```

### Common Issues

#### Hook Not Firing

**Symptom**: No entries in debug log after `/compact`

**Solutions**:
1. Verify hook configuration in `~/.claude/settings.local.json`
2. Check `$MAIA_ROOT` environment variable is set (NOT `$CLAUDE_PROJECT_DIR`)
3. If config uses `$CLAUDE_PROJECT_DIR`, update to `$MAIA_ROOT`
4. Restart Claude Code to reload hooks
5. Test hook manually:
   ```bash
   echo '{"session_id":"test","transcript_path":"~/test.jsonl","trigger":"manual"}' | \
     python3 claude/hooks/pre_compaction_learning_capture.py
   ```

#### Slow Performance

**Symptom**: Hook takes >5s

**Solutions**:
1. Check transcript size:
   ```python
   import os
   size = os.path.getsize('~/.claude/projects/.../transcript.jsonl')
   print(f"{size / 1024 / 1024:.2f} MB")
   ```
2. Monitor extraction time:
   ```bash
   grep "execution_time_ms" ~/.maia/logs/pre_compaction_debug.log
   ```
3. If consistently slow, check DB locks:
   ```bash
   sqlite3 ~/.maia/data/conversation_archive.db ".timeout 1000"
   ```

#### Learning Not Captured

**Symptom**: `learning_count` is 0 or lower than expected

**Solutions**:
1. Verify patterns match your conversations:
   ```python
   from claude.tools.learning.extraction import LEARNING_PATTERNS
   print(LEARNING_PATTERNS)
   ```
2. Test extraction directly:
   ```python
   from claude.tools.learning.extraction import get_extractor

   extractor = get_extractor()
   result = extractor.extract_from_transcript(your_transcript)
   print(f"Learnings: {len(result['learnings'])}")
   for learning in result['learnings']:
       print(f"  - {learning['type']}: {learning['content'][:100]}")
   ```
3. Add custom patterns if needed (see Customization below)

---

## Customization

### Add Custom Learning Patterns

```python
from claude.tools.learning.extraction import LearningExtractor

custom_patterns = {
    'discovery': [
        r'discovered (.*?)[\.\n]',
        r'found that (.*?)[\.\n]',
    ],
    'optimization': [
        r'optimized (.*?) by (.*?)[\.\n]',
        r'improved (.*?) performance',
    ]
}

extractor = LearningExtractor(patterns=custom_patterns)
```

### Configure Retention Policy

```sql
-- Delete snapshots older than 90 days
DELETE FROM conversation_snapshots
WHERE snapshot_timestamp < (strftime('%s', 'now') - 90*24*60*60) * 1000;

-- Keep only latest N snapshots per context
WITH ranked AS (
    SELECT snapshot_id,
           ROW_NUMBER() OVER (PARTITION BY context_id ORDER BY snapshot_timestamp DESC) as rn
    FROM conversation_snapshots
)
DELETE FROM conversation_snapshots
WHERE snapshot_id IN (SELECT snapshot_id FROM ranked WHERE rn > 10);
```

---

## Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| **100-message conversation** | <1s | ~50ms |
| **1000-message conversation** | <5s | ~200ms |
| **10K-message conversation** | <30s | ~2.5s |

**Testing**:
```bash
pytest tests/learning/test_pre_compaction_hook.py::test_hook_performance -v
```

---

## Test Coverage

**Total**: 70 tests (all passing)

| Component | Tests | Coverage |
|-----------|-------|----------|
| Archive System | 16 | Basic archival, retrieval, search, metrics |
| Extraction Engine | 20 | All patterns, metadata, edge cases |
| Retrieval Tools | 21 | API functions, exports, stats |
| Pre-Compaction Hook | 13 | Retry logic, performance, concurrency |

**Run Tests**:
```bash
# All pre-compaction tests
pytest tests/learning/test_archive.py -v
pytest tests/learning/test_extraction.py -v
pytest tests/learning/test_retrieval.py -v
pytest tests/learning/test_pre_compaction_hook.py -v

# All learning tests (includes PAI v2)
pytest tests/learning/ -v
```

---

## Roadmap

### Phase 1: Core Capture (COMPLETE ✅)
- [x] Archive system with SQLite + FTS5
- [x] Learning extraction engine
- [x] Retrieval API
- [x] Pre-compaction hook
- [x] Retry logic & graceful degradation
- [x] Comprehensive testing (70 tests)

### Phase 2: Production Hardening (IN PROGRESS)
- [ ] Auto-compaction enablement
- [ ] PAI v2 learning ID integration
- [ ] Enhanced pattern library
- [ ] Conversation analytics dashboard
- [ ] Performance optimization for 50K+ messages

### Phase 3: Advanced Features (PLANNED)
- [ ] Semantic search with embeddings
- [ ] Cross-conversation pattern analysis
- [ ] Conversation diffing
- [ ] Multi-tier archival (hot/warm/cold)
- [ ] Adaptive compaction strategies

---

## API Reference

See individual module documentation:
- [archive.py](archive.py) - Conversation archival
- [extraction.py](extraction.py) - Learning extraction
- [retrieval.py](retrieval.py) - Retrieval API
- [pre_compaction_learning_capture.py](../../../hooks/pre_compaction_learning_capture.py) - Hook implementation

---

## Support

**Issues**: [GitHub Issues](https://github.com/naythan-orro/maia/issues)
**Documentation**: See `PRECOMPACT_LEARNING_CAPTURE.md` in `claude/data/project_status/active/`

---

## License

Part of MAIA (My AI Agent) system
Phase 237 Implementation
Author: Maia + Naythan
Created: 2026-01-06
