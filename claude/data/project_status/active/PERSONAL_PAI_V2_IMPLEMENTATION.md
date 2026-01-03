# Personal PAI v2 Implementation Plan

**Project ID**: PAI-V2-001
**Created**: 2026-01-04
**Status**: READY FOR EXECUTION
**Priority**: High - Core capability enhancement
**Executor**: SRE Principal Engineer Agent
**Estimated Effort**: 10 days

---

## Executive Summary

Implement Daniel Miessler's PAI v2 learning system for Maia in **personal-only mode**. Each user gets their own learning system stored in `~/.maia/` - no team sharing, no PR workflow complexity.

### What We're Building

| Component | Purpose | Storage |
|-----------|---------|---------|
| **UOCS** | Capture all tool outputs | `~/.maia/outputs/` |
| **Kai History** | Searchable session summaries | `~/.maia/kai_history/` |
| **VERIFY** | Measure session success | `~/.maia/learning/` |
| **LEARN** | Extract patterns & preferences | `~/.maia/learning/` |
| **Self-modification** | Update personal preferences | `~/.maia/learning/preferences.db` |

### What We're NOT Building

- Team sharing / cross-user learning
- PR-based system modifications
- Anonymization pipelines
- CODEOWNERS integration for learning

---

## Architecture

### Storage Layout

```
~/.maia/                              # Per-user (NOT in git)
├── sessions/                         # EXISTING: Agent persistence
│   └── swarm_session_{ctx}.json
├── checkpoints/                      # EXISTING: State recovery
│   └── checkpoint_{id}.json
├── outputs/                          # NEW: UOCS captures
│   └── {session_id}/
│       ├── 001_bash_output.txt
│       ├── 002_read_output.txt
│       ├── manifest.json
│       └── summary.json
├── kai_history/                      # NEW: Session summaries
│   ├── kai.db                        # SQLite with FTS
│   └── summaries/
│       └── {date}/
│           └── {session_id}.md
└── learning/                         # NEW: Patterns & preferences
    ├── learning.db                   # Patterns, preferences, metrics
    └── config.json                   # User learning preferences
```

### Hook Integration Points

```
Session Lifecycle:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SESSION START (user-prompt-submit hook)                       │
│  ├── Load existing swarm session (existing)                    │
│  ├── Load relevant Kai summaries (NEW)                         │
│  ├── Load user preferences/patterns (NEW)                      │
│  └── Initialize UOCS capture (NEW)                             │
│                                                                 │
│  TOOL EXECUTION (tool-output hook - if available)              │
│  └── UOCS captures output (NEW)                                │
│                                                                 │
│  SESSION END (/close-session command)                          │
│  ├── VERIFY: Measure success (NEW)                             │
│  ├── LEARN: Extract patterns (NEW)                             │
│  ├── Generate Kai summary (NEW)                                │
│  └── Update preferences (NEW)                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (1 day)

### 1.1 Create Directory Structure

**File**: `claude/tools/learning/__init__.py`

```python
#!/usr/bin/env python3
"""
Maia Personal Learning System (PAI v2 Implementation)

Personal-only learning with no team sharing:
- UOCS: Universal Output Capture System
- Kai: Session history and summaries
- VERIFY: Success measurement
- LEARN: Pattern extraction
"""

from pathlib import Path

def get_learning_root() -> Path:
    """Get ~/.maia/ learning root, create if needed."""
    root = Path.home() / ".maia"

    # Create directory structure
    dirs = [
        root / "outputs",
        root / "kai_history" / "summaries",
        root / "learning",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return root

# Initialize on import
LEARNING_ROOT = get_learning_root()
```

### 1.2 Create Database Schema

**File**: `claude/tools/learning/schema.py`

```python
#!/usr/bin/env python3
"""Database schemas for Personal PAI v2."""

import sqlite3
from pathlib import Path

KAI_SCHEMA = """
-- Kai History: Session summaries
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    initial_query TEXT,
    agent_used TEXT,
    domain TEXT,
    status TEXT CHECK(status IN ('active', 'completed', 'abandoned', 'error')),

    -- Summary (populated on session end)
    summary_text TEXT,
    key_decisions TEXT,          -- JSON array
    tools_used TEXT,             -- JSON: {tool: count}
    files_touched TEXT,          -- JSON array

    -- VERIFY results
    verify_success BOOLEAN,
    verify_confidence REAL,
    verify_metrics TEXT,         -- JSON

    -- LEARN results
    learn_insights TEXT,         -- JSON array
    patterns_extracted INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_domain ON sessions(domain);

-- Full-text search for summaries
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    id, initial_query, summary_text, key_decisions,
    content=sessions, content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, id, initial_query, summary_text, key_decisions)
    VALUES (new.rowid, new.id, new.initial_query, new.summary_text, new.key_decisions);
END;

CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, id, initial_query, summary_text, key_decisions)
    VALUES ('delete', old.rowid, old.id, old.initial_query, old.summary_text, old.key_decisions);
    INSERT INTO sessions_fts(rowid, id, initial_query, summary_text, key_decisions)
    VALUES (new.rowid, new.id, new.initial_query, new.summary_text, new.key_decisions);
END;
"""

LEARNING_SCHEMA = """
-- Patterns: Extracted from sessions
CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT CHECK(pattern_type IN ('workflow', 'tool_sequence', 'preference', 'correction')),
    domain TEXT,
    description TEXT NOT NULL,
    pattern_data TEXT,           -- JSON: specific pattern details
    confidence REAL DEFAULT 0.5,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TEXT,
    last_seen TEXT,
    decayed_confidence REAL      -- Computed: confidence * decay_factor
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_domain ON patterns(domain);

-- Preferences: Inferred from corrections
CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,      -- 'coding_style', 'tool_choice', 'communication', etc.
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source_sessions TEXT,        -- JSON: [session_ids that contributed]
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(category, key)
);

CREATE INDEX IF NOT EXISTS idx_preferences_category ON preferences(category);

-- Metrics: Session success tracking
CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,   -- 'tool_success', 'task_completion', 'user_correction'
    value REAL NOT NULL,
    metadata TEXT,               -- JSON
    recorded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type, recorded_at);
"""

def init_kai_db(db_path: Path) -> sqlite3.Connection:
    """Initialize Kai history database."""
    conn = sqlite3.connect(db_path)
    conn.executescript(KAI_SCHEMA)
    conn.commit()
    return conn

def init_learning_db(db_path: Path) -> sqlite3.Connection:
    """Initialize learning database."""
    conn = sqlite3.connect(db_path)
    conn.executescript(LEARNING_SCHEMA)
    conn.commit()
    return conn
```

### 1.3 Update setup-team-member.sh

Add to existing script:

```bash
# Create learning directories (add after existing ~/.maia/ creation)
echo "Creating learning system directories..."
mkdir -p ~/.maia/outputs
mkdir -p ~/.maia/kai_history/summaries
mkdir -p ~/.maia/learning

# Initialize databases
echo "Initializing learning databases..."
python3 -c "
from claude.tools.learning.schema import init_kai_db, init_learning_db
from pathlib import Path
init_kai_db(Path.home() / '.maia' / 'kai_history' / 'kai.db')
init_learning_db(Path.home() / '.maia' / 'learning' / 'learning.db')
print('  Databases initialized')
"
```

**Validation**:
- [ ] `~/.maia/outputs/` exists
- [ ] `~/.maia/kai_history/kai.db` exists with tables
- [ ] `~/.maia/learning/learning.db` exists with tables

---

## Phase 2: UOCS - Universal Output Capture (1.5 days)

### 2.1 Create UOCS Module

**File**: `claude/tools/learning/uocs.py`

```python
#!/usr/bin/env python3
"""
Universal Output Capture System (UOCS)

Captures all tool outputs during a session for:
- Session replay and debugging
- VERIFY phase success measurement
- LEARN phase pattern extraction
- Kai summary generation input

Performance: <10ms overhead (async writes)
Storage: ~/.maia/outputs/{session_id}/
Retention: 7 days default (configurable)
"""

import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class CapturedOutput:
    """A single captured tool output."""
    capture_id: str
    tool_name: str
    timestamp: str
    input_hash: str
    output_path: Optional[str]
    output_size: int
    success: bool
    latency_ms: int
    capture_mode: str

class UOCS:
    """Universal Output Capture System."""

    # Capture modes by tool type
    CAPTURE_MODES = {
        'bash': 'output',        # Capture stdout/stderr
        'read': 'metadata',      # Just file path + size
        'write': 'metadata',     # Just file path
        'edit': 'diff',          # Capture the diff
        'grep': 'output',        # Capture matches
        'glob': 'output',        # Capture file list
        'task': 'metadata',      # Agent task summary
        'webfetch': 'summary',   # First 1000 chars
        'websearch': 'output',   # Search results
    }

    MAX_OUTPUT_SIZE = 100_000  # 100KB per capture

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.outputs_dir = Path.home() / ".maia" / "outputs" / session_id
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        self.captures: List[CapturedOutput] = []
        self.tool_counter = 0
        self._lock = threading.Lock()

    def capture(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ) -> str:
        """
        Capture a tool invocation (async, non-blocking).

        Returns capture_id.
        """
        self.tool_counter += 1
        capture_id = f"{self.tool_counter:04d}_{tool_name}"

        # Async capture to avoid blocking
        thread = threading.Thread(
            target=self._do_capture,
            args=(capture_id, tool_name, tool_input, tool_output, success, latency_ms),
            daemon=True
        )
        thread.start()

        return capture_id

    def _do_capture(
        self,
        capture_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ):
        """Actual capture logic (runs in thread)."""
        try:
            # Compute input hash for deduplication
            input_str = json.dumps(tool_input, sort_keys=True, default=str)
            input_hash = hashlib.sha256(input_str.encode()).hexdigest()[:16]

            # Determine capture mode
            capture_mode = self.CAPTURE_MODES.get(tool_name.lower(), 'metadata')

            # Capture based on mode
            output_path = None
            output_size = 0

            if capture_mode == 'output':
                content = self._truncate(str(tool_output))
                output_path = self.outputs_dir / f"{capture_id}.txt"
                output_path.write_text(content)
                output_size = len(content)

            elif capture_mode == 'diff':
                content = self._extract_diff(tool_input, tool_output)
                if content:
                    output_path = self.outputs_dir / f"{capture_id}.diff"
                    output_path.write_text(content)
                    output_size = len(content)

            elif capture_mode == 'summary':
                content = self._truncate(str(tool_output), 1000)
                output_path = self.outputs_dir / f"{capture_id}.txt"
                output_path.write_text(content)
                output_size = len(content)

            # metadata mode: no content saved

            # Record capture
            captured = CapturedOutput(
                capture_id=capture_id,
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
                input_hash=input_hash,
                output_path=str(output_path) if output_path else None,
                output_size=output_size,
                success=success,
                latency_ms=latency_ms,
                capture_mode=capture_mode
            )

            with self._lock:
                self.captures.append(captured)
                self._write_manifest()

        except Exception as e:
            # Never fail - graceful degradation
            pass

    def _truncate(self, content: str, max_size: int = None) -> str:
        """Truncate content to max size."""
        max_size = max_size or self.MAX_OUTPUT_SIZE
        if len(content) > max_size:
            return content[:max_size] + f"\n... [TRUNCATED at {max_size} bytes]"
        return content

    def _extract_diff(self, tool_input: Dict, tool_output: Any) -> Optional[str]:
        """Extract diff from edit operations."""
        if 'old_string' in tool_input and 'new_string' in tool_input:
            return f"--- old\n+++ new\n-{tool_input['old_string']}\n+{tool_input['new_string']}"
        return None

    def _write_manifest(self):
        """Write manifest to disk."""
        manifest = {
            'session_id': self.session_id,
            'capture_count': len(self.captures),
            'captures': [asdict(c) for c in self.captures]
        }
        manifest_path = self.outputs_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

    def get_summary(self) -> Dict[str, Any]:
        """Get session capture summary for Kai."""
        tools_used = {}
        total_latency = 0
        success_count = 0

        for c in self.captures:
            tools_used[c.tool_name] = tools_used.get(c.tool_name, 0) + 1
            total_latency += c.latency_ms
            if c.success:
                success_count += 1

        return {
            'session_id': self.session_id,
            'total_captures': len(self.captures),
            'tools_used': tools_used,
            'success_rate': success_count / max(len(self.captures), 1),
            'total_latency_ms': total_latency,
            'total_size_bytes': sum(c.output_size for c in self.captures)
        }

    def finalize(self):
        """Finalize session - write summary."""
        summary = self.get_summary()
        summary_path = self.outputs_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2))
        return summary


# Singleton per session
_active_uocs: Dict[str, UOCS] = {}

def get_uocs(session_id: str) -> UOCS:
    """Get or create UOCS for session."""
    if session_id not in _active_uocs:
        _active_uocs[session_id] = UOCS(session_id)
    return _active_uocs[session_id]

def close_uocs(session_id: str) -> Optional[Dict[str, Any]]:
    """Close and finalize UOCS for session."""
    if session_id in _active_uocs:
        summary = _active_uocs[session_id].finalize()
        del _active_uocs[session_id]
        return summary
    return None
```

### 2.2 Create UOCS Cleanup

**File**: `claude/tools/learning/uocs_cleanup.py`

```python
#!/usr/bin/env python3
"""UOCS cleanup - prune old captures."""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_outputs(days: int = 7):
    """Remove output directories older than N days."""
    outputs_root = Path.home() / ".maia" / "outputs"
    if not outputs_root.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    removed = 0

    for session_dir in outputs_root.iterdir():
        if not session_dir.is_dir():
            continue

        manifest = session_dir / "manifest.json"
        if manifest.exists():
            mtime = datetime.fromtimestamp(manifest.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(session_dir)
                removed += 1

    return removed

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    removed = cleanup_old_outputs(days)
    print(f"Removed {removed} output directories older than {days} days")
```

**Validation**:
- [ ] UOCS captures tool outputs to `~/.maia/outputs/{session}/`
- [ ] Manifest file created with capture index
- [ ] Async writes don't block tool execution
- [ ] Cleanup removes old directories

---

## Phase 3: Kai History System (2 days)

### 3.1 Create Kai History Module

**File**: `claude/tools/learning/kai.py`

```python
#!/usr/bin/env python3
"""
Kai History System

Auto-generates session summaries for cross-session learning:
- Summarizes key decisions and outcomes
- Enables full-text search across sessions
- Privacy-first (all data stays in ~/.maia/)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class KaiSummary:
    """A Kai session summary."""
    id: str
    session_id: str
    started_at: str
    ended_at: Optional[str]
    initial_query: str
    agent_used: Optional[str]
    domain: Optional[str]
    summary_text: str
    key_decisions: List[str]
    tools_used: Dict[str, int]
    verify_success: bool
    verify_confidence: float

class KaiHistory:
    """Manages Kai session summaries."""

    def __init__(self):
        self.db_path = Path.home() / ".maia" / "kai_history" / "kai.db"
        self.summaries_dir = Path.home() / ".maia" / "kai_history" / "summaries"
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Ensure database exists."""
        if not self.db_path.exists():
            from claude.tools.learning.schema import init_kai_db
            init_kai_db(self.db_path)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def start_session(
        self,
        session_id: str,
        context_id: str,
        initial_query: str,
        agent_used: Optional[str] = None,
        domain: Optional[str] = None
    ) -> str:
        """Record session start."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO sessions (id, context_id, started_at, initial_query, agent_used, domain, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (session_id, context_id, datetime.now().isoformat(), initial_query, agent_used, domain))
        conn.commit()
        conn.close()
        return session_id

    def end_session(
        self,
        session_id: str,
        summary_text: str,
        key_decisions: List[str],
        tools_used: Dict[str, int],
        files_touched: List[str],
        verify_success: bool,
        verify_confidence: float,
        verify_metrics: Dict[str, Any],
        learn_insights: List[Dict[str, Any]],
        status: str = 'completed'
    ):
        """Record session end with summary."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE sessions SET
                ended_at = ?,
                status = ?,
                summary_text = ?,
                key_decisions = ?,
                tools_used = ?,
                files_touched = ?,
                verify_success = ?,
                verify_confidence = ?,
                verify_metrics = ?,
                learn_insights = ?,
                patterns_extracted = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            status,
            summary_text,
            json.dumps(key_decisions),
            json.dumps(tools_used),
            json.dumps(files_touched),
            verify_success,
            verify_confidence,
            json.dumps(verify_metrics),
            json.dumps(learn_insights),
            len(learn_insights),
            session_id
        ))
        conn.commit()
        conn.close()

        # Write summary file
        self._write_summary_file(session_id, summary_text, key_decisions, tools_used)

    def _write_summary_file(
        self,
        session_id: str,
        summary_text: str,
        key_decisions: List[str],
        tools_used: Dict[str, int]
    ):
        """Write human-readable summary file."""
        date_dir = self.summaries_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)

        content = f"""# Session: {session_id}

## Summary
{summary_text}

## Key Decisions
{chr(10).join(f'- {d}' for d in key_decisions) if key_decisions else '- None recorded'}

## Tools Used
{chr(10).join(f'- {tool}: {count}x' for tool, count in tools_used.items()) if tools_used else '- None'}
"""
        (date_dir / f"{session_id}.md").write_text(content)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across sessions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT s.*, rank
            FROM sessions s
            JOIN sessions_fts f ON s.id = f.id
            WHERE sessions_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'started_at': row['started_at'],
                'initial_query': row['initial_query'],
                'summary_text': row['summary_text'],
                'agent_used': row['agent_used'],
                'domain': row['domain'],
                'verify_success': row['verify_success'],
                'relevance': -row['rank']  # FTS5 rank is negative
            })

        conn.close()
        return results

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM sessions
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_by_domain(self, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions by domain."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM sessions
            WHERE domain = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (domain, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_context_for_query(self, query: str, limit: int = 3) -> str:
        """Get relevant context to inject for a new query."""
        results = self.search(query, limit)

        if not results:
            return ""

        context_parts = ["## Relevant Prior Sessions\n"]
        for r in results:
            context_parts.append(f"""
### {r['started_at'][:10]} - {r['initial_query'][:100]}
{r['summary_text'][:500] if r['summary_text'] else 'No summary available'}
""")

        return "\n".join(context_parts)


# Singleton
_kai: Optional[KaiHistory] = None

def get_kai() -> KaiHistory:
    """Get Kai history singleton."""
    global _kai
    if _kai is None:
        _kai = KaiHistory()
    return _kai
```

### 3.2 Create Kai CLI Commands

**File**: `claude/commands/kai.md`

```markdown
# /kai - Session History Search

Search and browse your session history.

## Usage

```
/kai search <query>    - Search past sessions
/kai recent [n]        - Show N recent sessions (default 5)
/kai domain <name>     - Show sessions by domain
/kai context <query>   - Get relevant context for current task
```

## Examples

```
/kai search authentication
/kai recent 10
/kai domain sre
/kai context "fix memory leak"
```

## Implementation

When user invokes /kai, execute the appropriate KaiHistory method and display results.
```

**Validation**:
- [ ] Sessions are recorded on start
- [ ] Summaries are generated on end
- [ ] Full-text search works
- [ ] CLI commands work

---

## Phase 4: VERIFY Phase (1 day)

### 4.1 Create VERIFY Module

**File**: `claude/tools/learning/verify.py`

```python
#!/usr/bin/env python3
"""
VERIFY Phase - Success Measurement

Measures session success across multiple dimensions:
- Tool execution success rate
- Task completion indicators
- Error recovery effectiveness
- User correction frequency
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class VerifyResult:
    """Result of VERIFY phase analysis."""
    success: bool
    confidence: float
    metrics: Dict[str, float]
    insights: List[str]

class VerifyPhase:
    """Implements VERIFY phase logic."""

    # Thresholds
    SUCCESS_THRESHOLD = 0.7
    TOOL_SUCCESS_WEIGHT = 0.4
    COMPLETION_WEIGHT = 0.4
    RECOVERY_WEIGHT = 0.2

    def verify(
        self,
        uocs_summary: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> VerifyResult:
        """
        Verify session success.

        Args:
            uocs_summary: From UOCS.get_summary()
            session_data: Session metadata (agent, domain, etc.)

        Returns:
            VerifyResult with success assessment
        """
        metrics = {}
        insights = []

        # Metric 1: Tool success rate
        tool_success = uocs_summary.get('success_rate', 0)
        metrics['tool_success_rate'] = tool_success

        if tool_success < 0.8:
            insights.append(f"Tool success rate ({tool_success:.0%}) below target")

        # Metric 2: Task completion heuristic
        # High tool count + low errors = likely completion
        tool_count = uocs_summary.get('total_captures', 0)
        completion = min(1.0, tool_count / 10) * tool_success  # Normalize to ~10 tools
        metrics['task_completion'] = completion

        # Metric 3: Error recovery
        # If there were failures but overall success, good recovery
        if tool_success > 0 and tool_success < 1.0:
            recovery = tool_success  # Recovered from some failures
        else:
            recovery = 1.0 if tool_success == 1.0 else 0.0
        metrics['error_recovery'] = recovery

        # Metric 4: Session duration efficiency
        total_latency = uocs_summary.get('total_latency_ms', 0)
        if tool_count > 0:
            avg_latency = total_latency / tool_count
            # Penalize very slow sessions (>5s avg)
            efficiency = min(1.0, 5000 / max(avg_latency, 1))
            metrics['efficiency'] = efficiency
        else:
            metrics['efficiency'] = 0.5  # Neutral

        # Calculate overall score
        overall = (
            metrics['tool_success_rate'] * self.TOOL_SUCCESS_WEIGHT +
            metrics['task_completion'] * self.COMPLETION_WEIGHT +
            metrics['error_recovery'] * self.RECOVERY_WEIGHT
        )

        success = overall >= self.SUCCESS_THRESHOLD

        if success:
            insights.append(f"Session successful (confidence: {overall:.0%})")
        else:
            insights.append(f"Session had issues (confidence: {overall:.0%})")

        return VerifyResult(
            success=success,
            confidence=overall,
            metrics=metrics,
            insights=insights
        )

    def to_dict(self, result: VerifyResult) -> Dict[str, Any]:
        """Convert result to dict for storage."""
        return asdict(result)


# Singleton
_verify: Optional[VerifyPhase] = None

def get_verify() -> VerifyPhase:
    global _verify
    if _verify is None:
        _verify = VerifyPhase()
    return _verify
```

**Validation**:
- [ ] VERIFY produces success/confidence scores
- [ ] Metrics are meaningful
- [ ] Results stored in Kai session

---

## Phase 5: LEARN Phase (2 days)

### 5.1 Create LEARN Module

**File**: `claude/tools/learning/learn.py`

```python
#!/usr/bin/env python3
"""
LEARN Phase - Pattern Extraction

Extracts learnings from session for personal improvement:
- Pattern recognition (successful tool sequences)
- Preference inference (from corrections)
- Workflow detection (repeated approaches)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter

@dataclass
class LearningInsight:
    """A learning insight extracted from session."""
    insight_type: str  # 'workflow', 'tool_sequence', 'preference', 'correction'
    domain: Optional[str]
    description: str
    confidence: float
    data: Dict[str, Any]

class LearnPhase:
    """Implements LEARN phase logic."""

    MIN_CONFIDENCE = 0.5
    PATTERN_THRESHOLD = 3  # Minimum occurrences for pattern

    def __init__(self):
        self.db_path = Path.home() / ".maia" / "learning" / "learning.db"
        self._ensure_initialized()

    def _ensure_initialized(self):
        if not self.db_path.exists():
            from claude.tools.learning.schema import init_learning_db
            init_learning_db(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def learn(
        self,
        session_id: str,
        uocs_summary: Dict[str, Any],
        session_data: Dict[str, Any],
        verify_success: bool
    ) -> List[LearningInsight]:
        """
        Extract learning insights from session.

        Args:
            session_id: Session identifier
            uocs_summary: From UOCS.get_summary()
            session_data: Session metadata
            verify_success: From VERIFY phase

        Returns:
            List of extracted insights
        """
        insights = []

        # Only learn from successful sessions
        if not verify_success:
            return insights

        # Extract tool sequence pattern
        tool_sequence = self._extract_tool_sequence(uocs_summary)
        if tool_sequence:
            insights.append(tool_sequence)

        # Extract domain pattern
        domain_pattern = self._extract_domain_pattern(session_data, uocs_summary)
        if domain_pattern:
            insights.append(domain_pattern)

        # Store insights
        for insight in insights:
            self._store_pattern(session_id, insight)

        return insights

    def _extract_tool_sequence(self, uocs_summary: Dict[str, Any]) -> Optional[LearningInsight]:
        """Extract successful tool sequence pattern."""
        tools_used = uocs_summary.get('tools_used', {})

        if len(tools_used) < 2:
            return None

        # Top 5 tools by usage
        top_tools = sorted(tools_used.items(), key=lambda x: x[1], reverse=True)[:5]
        sequence = [t[0] for t in top_tools]

        return LearningInsight(
            insight_type='tool_sequence',
            domain=None,
            description=f"Successful pattern: {' -> '.join(sequence)}",
            confidence=uocs_summary.get('success_rate', 0.5),
            data={'sequence': sequence, 'counts': dict(top_tools)}
        )

    def _extract_domain_pattern(
        self,
        session_data: Dict[str, Any],
        uocs_summary: Dict[str, Any]
    ) -> Optional[LearningInsight]:
        """Extract domain-specific pattern."""
        domain = session_data.get('domain')
        agent = session_data.get('agent_used')

        if not domain and not agent:
            return None

        return LearningInsight(
            insight_type='workflow',
            domain=domain,
            description=f"Domain workflow: {domain or 'general'} with {agent or 'no agent'}",
            confidence=0.6,
            data={
                'domain': domain,
                'agent': agent,
                'tools': list(uocs_summary.get('tools_used', {}).keys())
            }
        )

    def _store_pattern(self, session_id: str, insight: LearningInsight):
        """Store pattern in database, updating confidence if exists."""
        conn = self._get_conn()

        # Check if similar pattern exists
        cursor = conn.execute("""
            SELECT id, occurrence_count, confidence
            FROM patterns
            WHERE pattern_type = ? AND domain IS ?
            LIMIT 1
        """, (insight.insight_type, insight.domain))

        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            new_count = existing['occurrence_count'] + 1
            # Increase confidence with more occurrences (max 0.95)
            new_confidence = min(0.95, existing['confidence'] + 0.05)

            conn.execute("""
                UPDATE patterns SET
                    occurrence_count = ?,
                    confidence = ?,
                    last_seen = ?,
                    pattern_data = ?
                WHERE id = ?
            """, (new_count, new_confidence, datetime.now().isoformat(),
                  json.dumps(insight.data), existing['id']))
        else:
            # Insert new pattern
            import uuid
            conn.execute("""
                INSERT INTO patterns (id, pattern_type, domain, description, pattern_data,
                                      confidence, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], insight.insight_type, insight.domain,
                  insight.description, json.dumps(insight.data), insight.confidence,
                  datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_patterns(self, domain: Optional[str] = None, min_confidence: float = 0.5) -> List[Dict]:
        """Get stored patterns."""
        conn = self._get_conn()

        if domain:
            cursor = conn.execute("""
                SELECT * FROM patterns
                WHERE domain = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (domain, min_confidence))
        else:
            cursor = conn.execute("""
                SELECT * FROM patterns
                WHERE confidence >= ?
                ORDER BY confidence DESC
            """, (min_confidence,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def record_preference(
        self,
        category: str,
        key: str,
        value: str,
        session_id: str,
        confidence: float = 0.6
    ):
        """Record a user preference (from correction or explicit setting)."""
        conn = self._get_conn()

        # Check if exists
        cursor = conn.execute("""
            SELECT id, source_sessions, confidence
            FROM preferences
            WHERE category = ? AND key = ?
        """, (category, key))

        existing = cursor.fetchone()

        if existing:
            # Update
            sources = json.loads(existing['source_sessions'] or '[]')
            sources.append(session_id)
            new_confidence = min(0.95, existing['confidence'] + 0.1)

            conn.execute("""
                UPDATE preferences SET
                    value = ?,
                    confidence = ?,
                    source_sessions = ?,
                    updated_at = ?
                WHERE category = ? AND key = ?
            """, (value, new_confidence, json.dumps(sources[-10:]),  # Keep last 10
                  datetime.now().isoformat(), category, key))
        else:
            # Insert
            import uuid
            conn.execute("""
                INSERT INTO preferences (id, category, key, value, confidence, source_sessions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], category, key, value, confidence,
                  json.dumps([session_id]), datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get stored preferences."""
        conn = self._get_conn()

        if category:
            cursor = conn.execute("""
                SELECT category, key, value, confidence
                FROM preferences
                WHERE category = ?
                ORDER BY confidence DESC
            """, (category,))
        else:
            cursor = conn.execute("""
                SELECT category, key, value, confidence
                FROM preferences
                ORDER BY category, confidence DESC
            """)

        prefs = {}
        for row in cursor.fetchall():
            cat = row['category']
            if cat not in prefs:
                prefs[cat] = {}
            prefs[cat][row['key']] = {
                'value': row['value'],
                'confidence': row['confidence']
            }

        conn.close()
        return prefs

    def to_dict(self, insights: List[LearningInsight]) -> List[Dict]:
        """Convert insights to dict for storage."""
        return [asdict(i) for i in insights]


# Singleton
_learn: Optional[LearnPhase] = None

def get_learn() -> LearnPhase:
    global _learn
    if _learn is None:
        _learn = LearnPhase()
    return _learn
```

**Validation**:
- [ ] Patterns extracted from successful sessions
- [ ] Patterns stored and updated in database
- [ ] Preferences can be recorded and retrieved
- [ ] Confidence increases with occurrences

---

## Phase 6: Integration (1.5 days)

### 6.1 Create Session Lifecycle Orchestrator

**File**: `claude/tools/learning/session.py`

```python
#!/usr/bin/env python3
"""
Session Lifecycle Orchestrator

Coordinates all PAI v2 components:
- Session start: Initialize UOCS, load context
- Session end: VERIFY, LEARN, generate Kai summary
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from claude.tools.learning.uocs import get_uocs, close_uocs
from claude.tools.learning.kai import get_kai
from claude.tools.learning.verify import get_verify
from claude.tools.learning.learn import get_learn

class SessionManager:
    """Manages the complete session lifecycle."""

    def __init__(self):
        self.kai = get_kai()
        self.verify = get_verify()
        self.learn = get_learn()
        self._active_session: Optional[str] = None
        self._session_data: Dict[str, Any] = {}

    def start_session(
        self,
        context_id: str,
        initial_query: str,
        agent_used: Optional[str] = None,
        domain: Optional[str] = None
    ) -> str:
        """
        Start a new learning session.

        Called from user-prompt-submit hook on first prompt.
        """
        session_id = f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Initialize UOCS
        get_uocs(session_id)

        # Record in Kai
        self.kai.start_session(
            session_id=session_id,
            context_id=context_id,
            initial_query=initial_query,
            agent_used=agent_used,
            domain=domain
        )

        # Store session data
        self._active_session = session_id
        self._session_data = {
            'session_id': session_id,
            'context_id': context_id,
            'initial_query': initial_query,
            'agent_used': agent_used,
            'domain': domain,
            'started_at': datetime.now().isoformat()
        }

        return session_id

    def capture_tool_output(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ):
        """
        Capture a tool output.

        Called from tool-output hook (if available) or manually.
        """
        if not self._active_session:
            return

        uocs = get_uocs(self._active_session)
        uocs.capture(tool_name, tool_input, tool_output, success, latency_ms)

    def end_session(self, status: str = 'completed') -> Dict[str, Any]:
        """
        End the session and run VERIFY + LEARN.

        Called from /close-session command.
        """
        if not self._active_session:
            return {'error': 'No active session'}

        session_id = self._active_session

        # Finalize UOCS
        uocs_summary = close_uocs(session_id)
        if not uocs_summary:
            uocs_summary = {'total_captures': 0, 'tools_used': {}, 'success_rate': 0}

        # Run VERIFY
        verify_result = self.verify.verify(uocs_summary, self._session_data)

        # Run LEARN (only from successful sessions)
        learn_insights = self.learn.learn(
            session_id=session_id,
            uocs_summary=uocs_summary,
            session_data=self._session_data,
            verify_success=verify_result.success
        )

        # Generate summary
        summary_text = self._generate_summary(uocs_summary, verify_result)
        key_decisions = self._extract_decisions()

        # Record in Kai
        self.kai.end_session(
            session_id=session_id,
            summary_text=summary_text,
            key_decisions=key_decisions,
            tools_used=uocs_summary.get('tools_used', {}),
            files_touched=[],  # TODO: extract from UOCS
            verify_success=verify_result.success,
            verify_confidence=verify_result.confidence,
            verify_metrics=verify_result.metrics,
            learn_insights=self.learn.to_dict(learn_insights),
            status=status
        )

        # Clear active session
        self._active_session = None
        result = {
            'session_id': session_id,
            'verify': self.verify.to_dict(verify_result),
            'learn': self.learn.to_dict(learn_insights),
            'summary': summary_text
        }
        self._session_data = {}

        return result

    def _generate_summary(self, uocs_summary: Dict, verify_result) -> str:
        """Generate human-readable summary."""
        tools = uocs_summary.get('tools_used', {})
        top_tools = sorted(tools.items(), key=lambda x: x[1], reverse=True)[:5]

        parts = [
            f"Session {'completed successfully' if verify_result.success else 'had issues'}.",
            f"Used {uocs_summary.get('total_captures', 0)} tool calls.",
        ]

        if top_tools:
            parts.append(f"Primary tools: {', '.join(t[0] for t in top_tools)}.")

        parts.append(f"Confidence: {verify_result.confidence:.0%}")

        return " ".join(parts)

    def _extract_decisions(self) -> List[str]:
        """Extract key decisions (placeholder - could use LLM)."""
        # For now, return empty - could be enhanced with LLM summarization
        return []

    def get_relevant_context(self, query: str) -> str:
        """Get relevant context from Kai for a new query."""
        return self.kai.get_context_for_query(query)

    @property
    def active_session_id(self) -> Optional[str]:
        return self._active_session


# Singleton
_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
```

### 6.2 Integrate with swarm_auto_loader.py

Add to existing `close_session()` function:

```python
# In claude/hooks/swarm_auto_loader.py, update close_session():

def close_session() -> Dict[str, Any]:
    """Close the current agent session."""
    context_id = get_context_id()
    session_file = get_session_file_path()

    result = {'context_id': context_id, 'closed': False}

    # Run PAI v2 session end
    try:
        from claude.tools.learning.session import get_session_manager
        manager = get_session_manager()
        if manager.active_session_id:
            learning_result = manager.end_session()
            result['learning'] = learning_result
    except ImportError:
        pass  # PAI v2 not installed yet

    # Existing session cleanup...
    if session_file.exists():
        # ... existing code ...
```

### 6.3 Create /close-session Command Update

**File**: `claude/commands/close_session.md` (update existing)

Add to existing close-session command:

```markdown
## PAI v2 Integration

When closing a session, the learning system:

1. **VERIFY** - Measures session success
   - Tool success rate
   - Task completion estimate
   - Error recovery effectiveness

2. **LEARN** - Extracts patterns (if successful)
   - Tool sequence patterns
   - Domain workflows
   - Updates preference database

3. **Kai Summary** - Generates searchable summary
   - Stored in ~/.maia/kai_history/
   - Searchable via /kai search
```

**Validation**:
- [ ] Session start initializes all components
- [ ] Session end runs VERIFY + LEARN + Kai
- [ ] Integration with existing swarm_auto_loader works
- [ ] /close-session produces learning output

---

## Phase 7: Testing (1.5 days)

### 7.1 Unit Tests

**File**: `tests/learning/test_uocs.py`

```python
#!/usr/bin/env python3
"""Tests for UOCS."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

class TestUOCS:
    def test_capture_creates_file(self):
        """Test that capture creates output file."""
        from claude.tools.learning.uocs import UOCS

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                uocs = UOCS("test_session")
                uocs.capture("bash", {"command": "ls"}, "file1\nfile2", True, 100)

                # Wait for async write
                import time
                time.sleep(0.1)

                assert len(uocs.captures) == 1
                assert uocs.captures[0].tool_name == "bash"

    def test_summary_calculates_correctly(self):
        """Test summary statistics."""
        from claude.tools.learning.uocs import UOCS

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                uocs = UOCS("test_session")
                uocs.capture("bash", {}, "out1", True, 100)
                uocs.capture("bash", {}, "out2", True, 50)
                uocs.capture("read", {}, "content", False, 25)

                import time
                time.sleep(0.1)

                summary = uocs.get_summary()
                assert summary['total_captures'] == 3
                assert summary['success_rate'] == pytest.approx(0.667, rel=0.01)
```

**File**: `tests/learning/test_kai.py`

```python
#!/usr/bin/env python3
"""Tests for Kai History."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

class TestKaiHistory:
    def test_session_lifecycle(self):
        """Test session start and end."""
        from claude.tools.learning.kai import KaiHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                kai = KaiHistory()

                # Start session
                sid = kai.start_session(
                    session_id="test_123",
                    context_id="ctx_1",
                    initial_query="Fix the bug",
                    agent_used="sre_agent",
                    domain="sre"
                )

                assert sid == "test_123"

                # End session
                kai.end_session(
                    session_id="test_123",
                    summary_text="Fixed the memory leak",
                    key_decisions=["Used profiler"],
                    tools_used={"bash": 5, "read": 3},
                    files_touched=["app.py"],
                    verify_success=True,
                    verify_confidence=0.85,
                    verify_metrics={"tool_success": 0.9},
                    learn_insights=[]
                )

                # Search
                results = kai.search("memory leak")
                assert len(results) >= 1
                assert results[0]['id'] == "test_123"
```

**File**: `tests/learning/test_verify.py`

```python
#!/usr/bin/env python3
"""Tests for VERIFY phase."""

import pytest

class TestVerifyPhase:
    def test_successful_session(self):
        """Test VERIFY on successful session."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is True
        assert result.confidence > 0.7

    def test_failed_session(self):
        """Test VERIFY on failed session."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 5,
            'success_rate': 0.2,
            'total_latency_ms': 10000,
            'tools_used': {'bash': 5}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is False
        assert result.confidence < 0.7
```

### 7.2 Integration Tests

**File**: `tests/learning/test_integration.py`

```python
#!/usr/bin/env python3
"""Integration tests for Personal PAI v2."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

class TestPAIv2Integration:
    def test_full_session_lifecycle(self):
        """Test complete session from start to end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                from claude.tools.learning.session import SessionManager

                manager = SessionManager()

                # Start session
                sid = manager.start_session(
                    context_id="test_ctx",
                    initial_query="Help me fix the auth bug",
                    agent_used="security_agent",
                    domain="security"
                )

                assert manager.active_session_id == sid

                # Capture some tool outputs
                manager.capture_tool_output("read", {"file": "auth.py"}, "code...", True, 50)
                manager.capture_tool_output("grep", {"pattern": "password"}, "matches", True, 100)
                manager.capture_tool_output("edit", {"file": "auth.py"}, "edited", True, 200)

                # End session
                result = manager.end_session()

                assert result['session_id'] == sid
                assert result['verify']['success'] is True
                assert 'summary' in result

                # Verify Kai recorded it
                from claude.tools.learning.kai import get_kai
                kai = get_kai()
                recent = kai.get_recent(1)
                assert len(recent) == 1
                assert recent[0]['id'] == sid
```

**Validation**:
- [ ] All unit tests pass
- [ ] Integration test passes
- [ ] Manual test of full workflow

---

## Validation Checklist

### Functional Tests

| Test | Command | Expected | Pass |
|------|---------|----------|------|
| UOCS captures | Run tools, check ~/.maia/outputs/ | Files created | [ ] |
| Kai records | /close-session, check kai.db | Session recorded | [ ] |
| Kai search | /kai search <term> | Results returned | [ ] |
| VERIFY runs | /close-session | Success/confidence shown | [ ] |
| LEARN extracts | Multiple sessions, check patterns | Patterns stored | [ ] |
| Preferences | Check preferences table | Preferences stored | [ ] |

### Performance Tests

| Test | Target | Actual | Pass |
|------|--------|--------|------|
| UOCS capture overhead | <10ms | | [ ] |
| Kai search latency | <100ms | | [ ] |
| Session end time | <500ms | | [ ] |

### Integration Tests

| Test | Pass |
|------|------|
| Works with existing swarm_auto_loader | [ ] |
| Works with /close-session | [ ] |
| Databases survive restarts | [ ] |
| Cleanup removes old data | [ ] |

---

## Files to Create

| File | Purpose |
|------|---------|
| `claude/tools/learning/__init__.py` | Package init, directory setup |
| `claude/tools/learning/schema.py` | Database schemas |
| `claude/tools/learning/uocs.py` | Universal Output Capture |
| `claude/tools/learning/uocs_cleanup.py` | UOCS maintenance |
| `claude/tools/learning/kai.py` | Kai History System |
| `claude/tools/learning/verify.py` | VERIFY phase |
| `claude/tools/learning/learn.py` | LEARN phase |
| `claude/tools/learning/session.py` | Session orchestrator |
| `claude/commands/kai.md` | Kai CLI command |
| `tests/learning/test_uocs.py` | UOCS tests |
| `tests/learning/test_kai.py` | Kai tests |
| `tests/learning/test_verify.py` | VERIFY tests |
| `tests/learning/test_integration.py` | Integration tests |

---

## Success Criteria

- [ ] All tests pass
- [ ] Session summaries generated and searchable
- [ ] Patterns extracted from successful sessions
- [ ] No performance regression (hooks <50ms)
- [ ] Cleanup works (old data removed)
- [ ] Documentation complete

---

**Document Status**: READY FOR EXECUTION
**Handoff To**: SRE Principal Engineer Agent
**Start Command**: Begin with Phase 1 - Foundation
