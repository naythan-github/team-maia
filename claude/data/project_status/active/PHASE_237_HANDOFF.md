# Phase 237 Project Handoff Document
**Phase 237.4: Proactive Context Monitor (70% Trigger)**

**Date**: 2026-01-07
**Status**: ✅ COMPLETE (Fixed in Phase 240)
**Previous Phases**: ✅ COMPLETE (Phases 1, 2.2, 2.3)
**Phase 240**: Fixed archive schema to allow `proactive_monitor` trigger type - system now operational

---

## Executive Summary

**What's Been Built** (Phases 1-2.3):
- ✅ Pre-compaction learning capture system (12 pattern types)
- ✅ PAI v2 integration with learning ID tracking
- ✅ Enhanced pattern library (5 original + 7 new patterns)
- ✅ Full end-to-end integration verified
- ✅ 316 tests (315 passing = 99.7%)

**Current Issue**:
- PreCompact hook only fires at ~95% context (and has bugs #13572, #13668)
- No way to trigger capture proactively at 70% context

**Next Phase Goal**:
Build a background monitor that checks context usage every 5 minutes and triggers learning capture at 70% threshold (proactive, before auto-compaction).

---

## Current State: Phase 237.3 COMPLETE ✅

### What Works
| Component | Status | Evidence |
|-----------|--------|----------|
| **Learning extraction** | ✅ Working | 12 pattern types, 0.05s for 1000 messages |
| **Conversation archive** | ✅ Working | SQLite + FTS5, millisecond timestamps |
| **PAI v2 integration** | ✅ Working | Learning IDs cross-referenced |
| **PreCompact hook** | ⚠️ Partial | Works on manual `/compact`, auto-trigger has bug |
| **Integration tests** | ✅ Passing | 3/3 end-to-end tests, 14 learnings extracted |
| **Documentation** | ✅ Complete | PRECOMPACT_README.md, capability index updated |

### Test Coverage
```bash
pytest tests/learning/ -v
# 316 total tests
# 315 passing (99.7%)
# 1 pre-existing failure (unrelated)

# Breakdown by component:
# - Archive: 16 tests
# - Extraction: 20 tests (original) + 18 tests (enhanced patterns)
# - Retrieval: 21 tests
# - PreCompact hook: 13 tests
# - PAI v2 bridge: 20 tests
# - Integration: 3 tests
```

### Key Files Created
```
claude/tools/learning/
├── extraction.py              # 12 pattern types (418 lines)
├── archive.py                 # Conversation archive (350 lines)
├── retrieval.py               # Retrieval API (280 lines)
├── pai_v2_bridge.py           # PAI v2 integration (270 lines)
├── PRECOMPACT_README.md       # Main documentation (472 lines)
└── ENHANCED_PATTERNS_README.md # Pattern reference (450 lines)

claude/hooks/
└── pre_compaction_learning_capture.py  # Hook implementation (250 lines)

tests/learning/
├── test_extraction.py         # 20 tests (original patterns)
├── test_extraction_enhanced.py # 18 tests (enhanced patterns)
├── test_archive.py            # 16 tests
├── test_retrieval.py          # 21 tests
├── test_pre_compaction_hook.py # 13 tests
├── test_pai_v2_bridge.py      # 20 tests
└── test_integration_enhanced.py # 3 integration tests
```

### Git Commits (Phase 237)
```bash
# Phase 1: Core Capture
b838780 - Implementation plan
06053ef - Archive system
ed3ed26 - Extraction engine
4a8e252 - Retrieval tools
628fe0a - Pre-compaction hook
1c1ded8 - Documentation & config

# Phase 2.2: PAI v2 Integration
13ebbf9 - PAI v2 bridge implementation

# Phase 2.3: Enhanced Patterns
2091d5d - Enhanced patterns (TDD)
30fca91 - Integration tests + docs
```

---

## Phase 237.4: Background Context Monitor

### Problem Statement
**Current**: PreCompact hook only fires at ~95% context when auto-compaction happens (and has bugs).
**Desired**: Proactive capture at 70% context to preserve learnings before compaction is necessary.
**Solution**: Background daemon that monitors context usage and triggers capture at configurable threshold.

### Technical Approach

#### Architecture
```
┌─────────────────────────────────────────┐
│ Background Monitor Daemon               │
│ (claude/hooks/context_monitor.py)      │
├─────────────────────────────────────────┤
│ Every 5 minutes:                        │
│ 1. Scan ~/.claude/projects/*/          │
│ 2. Count messages in transcript.jsonl  │
│ 3. Estimate tokens (msg_count * 800)   │
│ 4. If > 70% threshold:                  │
│    → Trigger pre_compaction hook        │
│    → Log capture event                  │
│    → Reset check timer                  │
└─────────────────────────────────────────┘
```

#### Implementation Spec

**File**: `claude/hooks/context_monitor.py`

**Features**:
- Configurable threshold (default: 70%)
- Configurable check interval (default: 300s)
- Multiple context window support (Opus 200K, Sonnet 200K, Haiku 200K)
- Graceful error handling (never crash, log errors)
- PID file for single-instance enforcement
- Signal handling (SIGTERM, SIGINT for clean shutdown)

**Configuration** (via environment variables or config file):
```bash
MAIA_CONTEXT_THRESHOLD=0.70      # Trigger at 70%
MAIA_CHECK_INTERVAL=300          # Check every 5 minutes
MAIA_CONTEXT_WINDOW=200000       # Opus 4.5 context window
MAIA_TOKENS_PER_MESSAGE=800      # Estimation factor
```

**Logging**:
- Log file: `~/.maia/logs/context_monitor.log`
- Log format: `[timestamp] [level] [context_id] message`
- Rotation: Keep last 7 days

---

## TDD Implementation Plan

### Phase 237.4.1: Core Monitor (Day 1)

#### Step 1: Write Tests First (RED)
**File**: `tests/learning/test_context_monitor.py`

```python
def test_context_estimation():
    """Test token estimation from message count"""
    # Given: Transcript with 100 messages
    # When: Estimate tokens
    # Then: Should estimate ~80,000 tokens (100 * 800)

def test_threshold_detection():
    """Test 70% threshold detection"""
    # Given: Context at 150K tokens (75% of 200K)
    # When: Check threshold
    # Then: Should return True (over 70%)

def test_single_instance_enforcement():
    """Test PID file prevents multiple instances"""
    # Given: Monitor already running
    # When: Start second instance
    # Then: Should exit with error

def test_graceful_shutdown():
    """Test SIGTERM handler"""
    # Given: Monitor running
    # When: Send SIGTERM
    # Then: Should clean up and exit gracefully

def test_trigger_capture_on_threshold():
    """Test capture triggered when threshold exceeded"""
    # Given: Context at 145K tokens (72.5%)
    # When: Monitor checks
    # Then: Should trigger pre_compaction_learning_capture.py

def test_skip_capture_below_threshold():
    """Test no capture when below threshold"""
    # Given: Context at 100K tokens (50%)
    # When: Monitor checks
    # Then: Should not trigger capture

def test_error_handling_missing_transcript():
    """Test graceful handling of missing transcript"""
    # Given: Project directory without transcript.jsonl
    # When: Monitor scans
    # Then: Should log warning and continue

def test_multiple_projects_scanning():
    """Test scanning multiple Claude Code projects"""
    # Given: 3 active projects
    # When: Monitor scans
    # Then: Should check all 3 projects independently
```

**Expected**: All tests FAIL (RED phase)

#### Step 2: Implement Core Monitor (GREEN)
**File**: `claude/hooks/context_monitor.py`

```python
#!/usr/bin/env python3
"""
Background Context Monitor for Proactive Learning Capture
Phase 237.4: Monitors Claude Code context usage and triggers capture at 70%

Author: Maia (Phase 237.4)
Created: 2026-01-06
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

# Configuration
CONTEXT_THRESHOLD = float(os.getenv('MAIA_CONTEXT_THRESHOLD', '0.70'))
CHECK_INTERVAL = int(os.getenv('MAIA_CHECK_INTERVAL', '300'))
CONTEXT_WINDOW = int(os.getenv('MAIA_CONTEXT_WINDOW', '200000'))
TOKENS_PER_MESSAGE = int(os.getenv('MAIA_TOKENS_PER_MESSAGE', '800'))

# Paths
MAIA_ROOT = Path(__file__).parent.parent
LOG_DIR = Path.home() / '.maia' / 'logs'
PID_FILE = Path.home() / '.maia' / 'context_monitor.pid'

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / 'context_monitor.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContextStatus:
    """Context usage status"""
    context_id: str
    message_count: int
    estimated_tokens: int
    usage_percentage: float
    transcript_path: Path


class ContextMonitor:
    """
    Background monitor for Claude Code context usage.

    Scans active Claude Code projects, estimates context usage,
    and triggers learning capture at configurable threshold.
    """

    def __init__(
        self,
        threshold: float = CONTEXT_THRESHOLD,
        check_interval: int = CHECK_INTERVAL,
        context_window: int = CONTEXT_WINDOW,
        tokens_per_message: int = TOKENS_PER_MESSAGE
    ):
        self.threshold = threshold
        self.check_interval = check_interval
        self.context_window = context_window
        self.tokens_per_message = tokens_per_message
        self.running = False

        # Track contexts already captured (don't spam)
        self.captured_contexts = set()

    def estimate_context_usage(self, transcript_path: Path) -> Optional[ContextStatus]:
        """
        Estimate context usage from transcript file.

        Args:
            transcript_path: Path to transcript.jsonl

        Returns:
            ContextStatus or None if file doesn't exist
        """
        if not transcript_path.exists():
            return None

        try:
            message_count = sum(1 for _ in open(transcript_path))
            estimated_tokens = message_count * self.tokens_per_message
            usage_percentage = (estimated_tokens / self.context_window) * 100

            context_id = transcript_path.parent.name

            return ContextStatus(
                context_id=context_id,
                message_count=message_count,
                estimated_tokens=estimated_tokens,
                usage_percentage=usage_percentage,
                transcript_path=transcript_path
            )
        except Exception as e:
            logger.error(f"Error estimating context for {transcript_path}: {e}")
            return None

    def should_trigger_capture(self, status: ContextStatus) -> bool:
        """
        Check if capture should be triggered.

        Args:
            status: ContextStatus

        Returns:
            True if over threshold and not already captured
        """
        if status.context_id in self.captured_contexts:
            return False  # Already captured this context

        return (status.usage_percentage / 100) > self.threshold

    def trigger_capture(self, status: ContextStatus) -> bool:
        """
        Trigger pre-compaction learning capture.

        Args:
            status: ContextStatus

        Returns:
            True if capture succeeded
        """
        try:
            import subprocess
            import json

            # Build hook input
            hook_input = {
                'session_id': status.context_id,
                'transcript_path': str(status.transcript_path),
                'trigger': 'proactive_monitor',
                'hook_event_name': 'PreCompact'
            }

            # Call hook
            hook_path = MAIA_ROOT / 'hooks' / 'pre_compaction_learning_capture.py'
            result = subprocess.run(
                ['python3', str(hook_path)],
                input=json.dumps(hook_input).encode(),
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(
                    f"✅ Capture triggered for {status.context_id} "
                    f"({status.usage_percentage:.1f}% context)"
                )
                self.captured_contexts.add(status.context_id)
                return True
            else:
                logger.error(
                    f"❌ Capture failed for {status.context_id}: "
                    f"{result.stderr.decode()}"
                )
                return False

        except Exception as e:
            logger.error(f"Error triggering capture for {status.context_id}: {e}")
            return False

    def scan_projects(self) -> List[ContextStatus]:
        """
        Scan all Claude Code projects for context usage.

        Returns:
            List of ContextStatus for all active projects
        """
        projects_dir = Path.home() / '.claude' / 'projects'

        if not projects_dir.exists():
            logger.warning(f"Projects directory not found: {projects_dir}")
            return []

        statuses = []

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            for transcript in project_dir.glob('*.jsonl'):
                status = self.estimate_context_usage(transcript)
                if status:
                    statuses.append(status)

        return statuses

    def check_and_trigger(self):
        """Check all contexts and trigger captures if needed."""
        logger.info("Scanning projects for context usage...")

        statuses = self.scan_projects()

        if not statuses:
            logger.info("No active projects found")
            return

        for status in statuses:
            logger.debug(
                f"Context {status.context_id}: {status.usage_percentage:.1f}% "
                f"({status.message_count} messages, ~{status.estimated_tokens:,} tokens)"
            )

            if self.should_trigger_capture(status):
                logger.warning(
                    f"⚠️ Context {status.context_id} at {status.usage_percentage:.1f}% "
                    f"(threshold: {self.threshold*100:.0f}%) - triggering capture"
                )
                self.trigger_capture(status)

    def enforce_single_instance(self):
        """Ensure only one monitor instance is running."""
        if PID_FILE.exists():
            try:
                with open(PID_FILE) as f:
                    old_pid = int(f.read().strip())

                # Check if process is actually running
                os.kill(old_pid, 0)  # Raises OSError if not running

                logger.error(f"Monitor already running (PID {old_pid})")
                sys.exit(1)

            except (OSError, ValueError):
                # Old PID file, process not running
                logger.info("Removing stale PID file")
                PID_FILE.unlink()

        # Write current PID
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

    def cleanup(self):
        """Clean up resources."""
        logger.info("Shutting down context monitor...")

        if PID_FILE.exists():
            PID_FILE.unlink()

        self.running = False

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Run monitor daemon."""
        logger.info(
            f"Starting context monitor "
            f"(threshold: {self.threshold*100:.0f}%, interval: {self.check_interval}s)"
        )

        # Enforce single instance
        self.enforce_single_instance()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.running = True

        try:
            while self.running:
                self.check_and_trigger()
                time.sleep(self.check_interval)

        except Exception as e:
            logger.error(f"Monitor crashed: {e}")
            raise

        finally:
            self.cleanup()


def main():
    """Entry point."""
    monitor = ContextMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
```

**Expected**: All tests PASS (GREEN phase)

#### Step 3: Refactor & Optimize (REFACTOR)
- Add command-line arguments (`--threshold`, `--interval`, `--dry-run`)
- Add status command (`context_monitor.py status`)
- Optimize file scanning (cache project directories)
- Add metrics (captures triggered, errors, average context usage)

---

### Phase 237.4.2: LaunchAgent Integration (Day 2)

#### Step 1: Write Tests First (RED)
**File**: `tests/learning/test_context_monitor_launchd.py`

```python
def test_generate_launchd_plist():
    """Test LaunchAgent plist generation"""
    # Given: Monitor script path
    # When: Generate plist
    # Then: Should create valid plist with correct paths

def test_launchd_plist_validation():
    """Test plist XML validation"""
    # Given: Generated plist
    # When: Validate XML
    # Then: Should pass plutil validation

def test_install_launchagent():
    """Test LaunchAgent installation"""
    # Given: Generated plist
    # When: Install to ~/Library/LaunchAgents/
    # Then: Should copy file and set permissions

def test_uninstall_launchagent():
    """Test LaunchAgent uninstallation"""
    # Given: Installed LaunchAgent
    # When: Uninstall
    # Then: Should remove plist and unload service
```

**Expected**: All tests FAIL (RED phase)

#### Step 2: Implement LaunchAgent Manager (GREEN)
**File**: `claude/tools/learning/context_monitor_installer.py`

```python
#!/usr/bin/env python3
"""
Context Monitor LaunchAgent Installer
Manages macOS LaunchAgent for automatic context monitoring
"""

from pathlib import Path
import subprocess

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maia.context-monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{monitor_script}</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>MAIA_CONTEXT_THRESHOLD</key>
        <string>0.70</string>
        <key>MAIA_CHECK_INTERVAL</key>
        <string>300</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{log_dir}/context_monitor_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/context_monitor_stderr.log</string>
</dict>
</plist>
"""

def install():
    """Install LaunchAgent"""
    # Generate plist
    # Copy to ~/Library/LaunchAgents/
    # Load with launchctl
    pass

def uninstall():
    """Uninstall LaunchAgent"""
    # Unload with launchctl
    # Remove plist
    pass

def status():
    """Check LaunchAgent status"""
    # Query launchctl
    pass
```

**Expected**: All tests PASS (GREEN phase)

---

### Phase 237.4.3: Integration Testing (Day 3)

#### Integration Tests
**File**: `tests/learning/test_context_monitor_integration.py`

```python
def test_full_monitor_flow():
    """
    Test complete flow:
    1. Create synthetic transcript (150 messages = 120K tokens = 60%)
    2. Add messages to push over 70% (175 messages = 140K tokens = 70%)
    3. Run monitor (should trigger capture)
    4. Verify learning capture succeeded
    5. Verify archive created
    6. Verify PAI v2 patterns saved
    """

def test_monitor_does_not_spam():
    """
    Test monitor doesn't trigger multiple captures for same context:
    1. Context at 75%
    2. Monitor runs (triggers capture)
    3. Monitor runs again 5 min later (should NOT trigger)
    4. Verify only 1 capture event
    """

def test_monitor_handles_multiple_contexts():
    """
    Test monitor handles multiple active contexts:
    1. Context A at 50% (below threshold)
    2. Context B at 75% (above threshold)
    3. Context C at 90% (above threshold)
    4. Run monitor
    5. Verify only B and C captured
    """

def test_monitor_recovery_after_capture_failure():
    """
    Test monitor continues after capture failure:
    1. Context at 75%
    2. Simulate capture failure (corrupt transcript)
    3. Run monitor (logs error, continues)
    4. Fix transcript
    5. Run monitor again (retries capture successfully)
    """
```

---

## Success Criteria

### Phase 237.4 is COMPLETE when:

#### Functionality
- [ ] Monitor runs continuously without crashes
- [ ] Triggers capture at 70% context threshold
- [ ] Does not spam (captures once per context)
- [ ] Handles multiple concurrent Claude Code projects
- [ ] Gracefully handles errors (missing files, corrupt transcripts)
- [ ] Clean shutdown on SIGTERM/SIGINT

#### Testing
- [ ] Unit tests >90% coverage for monitor core logic
- [ ] Integration tests pass (full flow verified)
- [ ] LaunchAgent tests pass (install/uninstall/status)
- [ ] Performance test: <100ms per project scan
- [ ] Stress test: Handles 10+ concurrent projects

#### Documentation
- [ ] README.md updated with monitor setup instructions
- [ ] LaunchAgent installation guide
- [ ] Troubleshooting section (common issues)
- [ ] Configuration reference (env vars)

#### Production
- [ ] LaunchAgent plist generated
- [ ] Installation script tested
- [ ] Uninstallation script tested
- [ ] Logs rotating correctly (7-day retention)
- [ ] PID file cleanup on crash

#### Code Quality
- [ ] Pre-commit TDD hook passes
- [ ] No hardcoded paths (use MAIA_ROOT)
- [ ] Type hints on all public functions
- [ ] Error messages actionable
- [ ] Logging comprehensive (INFO/WARNING/ERROR levels)

---

## Commands for SRE Agent

### Setup
```bash
# Initialize development
cd /Users/naythandawe/maia

# Verify current state
pytest tests/learning/ -v
# Should see 316 tests (315 passing)

# Read existing implementation
cat claude/hooks/pre_compaction_learning_capture.py
cat claude/tools/learning/extraction.py
cat claude/tools/learning/archive.py
```

### TDD Workflow
```bash
# 1. Write tests first (RED)
# Create tests/learning/test_context_monitor.py
# Run: pytest tests/learning/test_context_monitor.py -v
# Expected: All FAIL

# 2. Implement (GREEN)
# Create claude/hooks/context_monitor.py
# Run: pytest tests/learning/test_context_monitor.py -v
# Expected: All PASS

# 3. Refactor
# Optimize, add features
# Run: pytest tests/learning/test_context_monitor.py -v
# Expected: All PASS (maintained)

# 4. Integration tests
# Create tests/learning/test_context_monitor_integration.py
# Run: pytest tests/learning/test_context_monitor_integration.py -v
# Expected: All PASS

# 5. Full test suite
pytest tests/learning/ -v
# Expected: All monitor tests + existing 316 tests = 325+ tests
```

### Progress Tracking
```bash
# Update progress log
# File: claude/data/project_status/active/PRECOMPACT_LEARNING_CAPTURE.md
# Add section: "2026-01-06 16:00 - PHASE 2.4 IN PROGRESS"

# Use TodoWrite tool to track:
# - Write core monitor tests
# - Implement monitor daemon
# - Write LaunchAgent tests
# - Implement installer
# - Integration testing
# - Documentation
# - Commit
```

### Git Workflow
```bash
# After each component complete
git add tests/learning/test_context_monitor.py claude/hooks/context_monitor.py
git commit -m "feat(learning): Add background context monitor (Phase 237.4.1)

TDD implementation:
- 8 unit tests (all passing)
- Context estimation from message count
- 70% threshold detection
- Single instance enforcement (PID file)
- Signal handling (SIGTERM, SIGINT)
- Graceful error handling

Performance: <100ms per project scan
Next: LaunchAgent integration (Phase 237.4.2)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Integration Points

### With Existing Phase 237 System
```python
# Monitor uses existing pre-compaction hook
from claude.hooks.pre_compaction_learning_capture import PreCompactionHook

# Calls existing learning extraction
from claude.tools.learning.extraction import get_extractor

# Archives to existing database
from claude.tools.learning.archive import get_archive

# Saves to existing PAI v2
from claude.tools.learning.pai_v2_bridge import get_pai_v2_bridge
```

### Configuration Alignment
```bash
# Monitor threshold should align with hook trigger
MAIA_CONTEXT_THRESHOLD=0.70  # Trigger at 70% (proactive)
# vs.
# PreCompact hook triggers at ~0.95 (auto-compaction, reactive)

# Strategy: Monitor captures at 70%, hook is backup at 95%
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Monitor crashes and stops | Medium | High | LaunchAgent KeepAlive=true, crash reporting |
| Token estimation inaccurate | High | Medium | Document as estimate, add calibration factor |
| Multiple monitors running | Low | Medium | PID file enforcement, single instance check |
| Spam captures (same context) | Medium | Medium | Track captured contexts, cooldown period |
| High CPU usage | Low | Low | Sleep between scans, optimize file I/O |
| LaunchAgent permission issues | Low | Medium | Installation script checks permissions |

---

## Next Session Checklist for SRE Agent

### Before Starting
- [ ] Read this entire handoff document
- [ ] Review existing Phase 237 implementation:
  - `claude/hooks/pre_compaction_learning_capture.py`
  - `claude/tools/learning/extraction.py`
  - `claude/tools/learning/archive.py`
- [ ] Run existing tests to verify baseline:
  ```bash
  pytest tests/learning/ -v
  # Should see 316 tests (315 passing)
  ```
- [ ] Verify git state:
  ```bash
  git log --oneline -10
  # Should see commit 30fca91 (integration tests)
  ```

### Start Here
1. **Create test file**: `tests/learning/test_context_monitor.py`
2. **Write 8 core tests** (see TDD Implementation Plan above)
3. **Run tests** → Should FAIL (RED phase)
4. **Create implementation**: `claude/hooks/context_monitor.py`
5. **Run tests** → Should PASS (GREEN phase)
6. **Use TodoWrite** to track progress through all 4 phases

### Questions to Ask User
- [ ] "Should monitor scan all Claude Code projects or just current one?"
- [ ] "Preferred check interval? (300s = 5min, 600s = 10min)"
- [ ] "Should monitor auto-start on login via LaunchAgent?"

---

## References

### Documentation
- **Main docs**: `claude/tools/learning/PRECOMPACT_README.md`
- **Enhanced patterns**: `claude/tools/learning/ENHANCED_PATTERNS_README.md`
- **Project status**: `claude/data/project_status/active/PRECOMPACT_LEARNING_CAPTURE.md`
- **Capability index**: `claude/context/core/capability_index.md` (lines 549-575)

### Key Concepts
- **Context window**: 200K tokens (Opus 4.5)
- **Estimation factor**: ~800 tokens per message
- **Threshold**: 70% = 140K tokens = ~175 messages
- **Check interval**: 300s (5 minutes)
- **Trigger types**: `manual`, `auto`, `skill`, `proactive_monitor` (new)

### External References
- Claude Code hooks: https://code.claude.com/docs/en/hooks.md
- Claude Code bugs: #13572 (PreCompact not firing), #13668 (empty transcript_path)

---

## Final Notes

**This is a well-scoped, production-ready task**:
- Clear requirements
- Existing working system to integrate with
- TDD approach defined
- Success criteria explicit
- Risk mitigations identified

**Estimated effort**: 2-3 days (with TDD + integration testing + docs)

**Expected outcome**: Proactive learning capture at 70% context, eliminating dependency on buggy auto-compaction triggers.

---

**Handoff prepared by**: Maia (Claude Sonnet 4.5)
**Date**: 2026-01-06
**Session**: Context 63140
**Ready for**: SRE Principal Engineer Agent
