# SPRINT-004: Orchestration Enforcement - Hybrid Solution

**Sprint ID**: SPRINT-004-ORCHESTRATION-ENFORCEMENT
**Created**: 2026-01-16
**Status**: PLANNED
**Estimated Effort**: 8-10 hours across 5 phases
**Predecessor**: SPRINT-003-SWARM-TASK-ORCHESTRATION

---

## Executive Summary

Implement the hybrid solution to enforce subagent orchestration (agent context injection) when Claude Code spawns Task subagents. Since no PreToolUse hook exists, we use a multi-layered passive guidance approach.

**Problem**: Orchestration tools exist but aren't used - Task subagents run without agent context.

**Solution**: Defense-in-depth via session state + mandate injection + smart context + monitoring.

**Target**: 70-85% compliance rate (Claude follows orchestration guidance).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID ENFORCEMENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Prompt                                                                 │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 1: Session State (P1)                                         │    │
│  │   session.orchestration = {                                         │    │
│  │     spawn_patterns: [...],                                          │    │
│  │     no_spawn_patterns: [...],                                       │    │
│  │     workflow_hint: "decision → builder → Task"                      │    │
│  │   }                                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 2: Agent Mandate Injection (P2)                               │    │
│  │   Mandate template includes:                                        │    │
│  │   "## Subagent Orchestration Protocol"                              │    │
│  │   - When to spawn (patterns)                                        │    │
│  │   - How to spawn (import paths)                                     │    │
│  │   - Required steps (decision → build → track)                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 3: Smart Context Loading (P3)                                 │    │
│  │   For exploration queries (how/find/analyze):                       │    │
│  │   → Inject orchestration tools into context                         │    │
│  │   → Prioritize spawn_decision.py, subagent_prompt_builder.py        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 4: Compliance Monitoring (P4)                                 │    │
│  │   PostToolUse hook monitors Task calls:                             │    │
│  │   - Check for "## Agent Context" in prompt                          │    │
│  │   - Log compliance rate to session                                  │    │
│  │   - Feed learning system for improvement                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Layer 5: Documentation + Integration (P5)                           │    │
│  │   - CLAUDE.md Principle #26 enhanced with examples                  │    │
│  │   - Capability registration                                         │    │
│  │   - E2E integration test                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Description | Hours | Subagent | Model | TDD Tests |
|-------|-------------|-------|----------|-------|-----------|
| P1 | Session State Orchestration | 2 | sre_principal_engineer_agent | sonnet | 6 |
| P2 | Mandate Template Enhancement | 1.5 | sre_principal_engineer_agent | sonnet | 4 |
| P3 | Smart Context Priority | 1.5 | sre_principal_engineer_agent | sonnet | 5 |
| P4 | Compliance Monitoring | 2 | devops_principal_architect_agent | sonnet | 5 |
| P5 | Documentation + Integration | 1.5 | sre_principal_engineer_agent | haiku | 3 |

**Each phase includes:**
- TDD: Write tests first
- Implementation
- Code review via `python_code_reviewer_agent`
- Gate criteria verification

---

## Phase 1: Session State Orchestration

**Goal**: Inject orchestration configuration into session files at creation time.

**Duration**: 2 hours
**Subagent**: `sre_principal_engineer_agent`
**Model**: `sonnet`

### 1.1 Deliverables

**File**: `claude/hooks/swarm_auto_loader.py` (Enhancement)

```python
# Add to session creation logic
ORCHESTRATION_CONFIG = {
    'enabled': True,
    'version': '1.0',
    'spawn_patterns': [
        r'\bhow\s+(does|do|is|are)\b',
        r'\bwhere\s+(is|are)\b',
        r'\bfind\s+all\b',
        r'\banalyze\b',
        r'\bexplore\b',
        r'\barchitecture\b',
        r'\bwhat\s+is\s+the\b',
        r'\breview\s+the\b',
    ],
    'no_spawn_patterns': [
        r'\bedit\b',
        r'\bread\s+(file|the)\b',
        r'\brun\b',
        r'\bexecute\b',
        r'\bcommit\b',
        r'\bpush\b',
    ],
    'imports': {
        'decision': 'from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine',
        'builder': 'from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder',
        'tracker': 'from claude.tools.orchestration.subagent_tracker import SubagentTracker',
    },
    'workflow': 'SpawnDecisionEngine.analyze() → SubagentPromptBuilder.build() → Task(prompt=result.prompt)',
}


def create_session(context_id: str, agent: str, query: str) -> Dict[str, Any]:
    """Create session with orchestration config."""
    return {
        'current_agent': agent,
        'session_start': datetime.utcnow().isoformat() + 'Z',
        'handoff_chain': [agent],
        'context': {},
        'domain': _extract_domain(agent),
        'last_classification_confidence': 1.0,
        'query': query,
        'working_directory': str(MAIA_ROOT),
        'git_remote_url': _get_git_remote(),
        'git_branch': _get_git_branch(),
        # NEW: Orchestration config
        'orchestration': ORCHESTRATION_CONFIG,
    }
```

### 1.2 TDD Tests

**File**: `tests/test_session_orchestration.py`

```python
"""Tests for session orchestration config - TDD first."""

import pytest
import json
from pathlib import Path


class TestSessionOrchestrationConfig:
    """Unit tests for orchestration in session files."""

    def test_new_session_has_orchestration_field(self):
        """Test newly created sessions include orchestration config."""
        # Given: Session creation function
        # When: create_session() called
        # Then: Result has 'orchestration' key
        pass

    def test_orchestration_has_spawn_patterns(self):
        """Test orchestration config includes spawn patterns."""
        # Given: Session with orchestration
        # When: Access orchestration.spawn_patterns
        # Then: List of regex patterns returned
        pass

    def test_orchestration_has_no_spawn_patterns(self):
        """Test orchestration config includes no-spawn patterns."""
        pass

    def test_orchestration_has_imports(self):
        """Test orchestration config includes import strings."""
        # Given: Session orchestration config
        # When: Access orchestration.imports
        # Then: Contains decision, builder, tracker import strings
        pass

    def test_orchestration_has_workflow_hint(self):
        """Test orchestration config includes workflow description."""
        pass

    def test_orchestration_version_tracking(self):
        """Test orchestration config has version for compatibility."""
        pass


class TestSessionOrchestrationIntegration:
    """Integration tests with real session files."""

    def test_init_creates_session_with_orchestration(self, tmp_path):
        """Test /init command creates session with orchestration."""
        # Given: Temp session directory
        # When: Session created via init workflow
        # Then: Session file contains orchestration config
        pass
```

### 1.3 Gate Criteria

- [ ] `create_session()` returns dict with `orchestration` key
- [ ] Orchestration contains: `spawn_patterns`, `no_spawn_patterns`, `imports`, `workflow`
- [ ] All 6 tests passing
- [ ] Backward compatible (existing sessions without orchestration still work)
- [ ] Code review PASS

---

## Phase 2: Mandate Template Enhancement

**Goal**: Add orchestration protocol section to agent mandate injection.

**Duration**: 1.5 hours
**Subagent**: `sre_principal_engineer_agent`
**Model**: `sonnet`

### 2.1 Deliverables

**File**: `claude/hooks/agent_mandate_injector.py` (Enhancement)

```python
# New constant for orchestration section
ORCHESTRATION_PROTOCOL = """
## Subagent Orchestration Protocol ⭐ MANDATORY

When delegating heavy exploration to Task subagents, use orchestration tools:

### Decision Check
```python
from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

engine = SpawnDecisionEngine()
decision = engine.analyze(query, session_context={'sprint_mode': False}, files_mentioned=[])

if decision.should_spawn:
    # Use builder to inject agent context
```

### Prompt Building (REQUIRED for Task subagents)
```python
from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder

builder = SubagentPromptBuilder()
result = builder.build(
    agent_name=decision.recommended_agent,  # or current agent
    task="the task description"
)

# Then call Task with enriched prompt:
# Task(subagent_type="general-purpose", prompt=result.prompt, model=result.model_recommendation)
```

### Spawn Patterns (triggers orchestration)
- "How does X work?" → SPAWN with agent context
- "Find all X" → SPAWN
- "Analyze X" → SPAWN
- "Explore X" → SPAWN

### No-Spawn Patterns (direct execution)
- "Edit file X" → DIRECT (no Task needed)
- "Run command X" → DIRECT
- "Read file X" → DIRECT
"""


def generate_mandate(agent_name: str, agent_file: Path) -> Optional[str]:
    """Generate agent mandate with orchestration protocol."""
    # ... existing code ...

    # Add orchestration protocol after agent sections
    mandate_parts.append("")
    mandate_parts.append(ORCHESTRATION_PROTOCOL)

    # ... rest of existing code ...
```

### 2.2 TDD Tests

**File**: `tests/test_mandate_orchestration.py`

```python
"""Tests for mandate orchestration protocol - TDD first."""

import pytest


class TestMandateOrchestration:
    """Unit tests for orchestration in mandate injection."""

    def test_mandate_includes_orchestration_section(self):
        """Test generated mandate includes orchestration protocol."""
        # Given: Agent name
        # When: generate_mandate() called
        # Then: Output contains "## Subagent Orchestration Protocol"
        pass

    def test_mandate_has_spawn_decision_import(self):
        """Test mandate includes SpawnDecisionEngine import."""
        pass

    def test_mandate_has_builder_import(self):
        """Test mandate includes SubagentPromptBuilder import."""
        pass

    def test_mandate_has_spawn_patterns(self):
        """Test mandate lists spawn patterns."""
        pass
```

### 2.3 Gate Criteria

- [ ] `generate_mandate()` output contains orchestration protocol
- [ ] Protocol includes imports, patterns, examples
- [ ] All 4 tests passing
- [ ] Mandate size within token budget (<6000 chars)
- [ ] Code review PASS

---

## Phase 3: Smart Context Priority

**Goal**: Inject orchestration tools into context when exploration queries detected.

**Duration**: 1.5 hours
**Subagent**: `sre_principal_engineer_agent`
**Model**: `sonnet`

### 3.1 Deliverables

**File**: `claude/tools/sre/smart_context_loader.py` (Enhancement)

```python
# New function for orchestration context
ORCHESTRATION_CONTEXT_TEMPLATE = """
## Orchestration Tools Available

For exploration queries, use these tools to spawn Task subagents with agent context:

**Decision Engine**: `claude.tools.orchestration.spawn_decision.SpawnDecisionEngine`
- `engine.analyze(query, session_context, files_mentioned)` → SpawnDecision
- Returns: should_spawn, recommended_agent, confidence

**Prompt Builder**: `claude.tools.orchestration.subagent_prompt_builder.SubagentPromptBuilder`
- `builder.build(agent_name, task)` → SubagentPrompt
- Returns: prompt (with agent.md injected), model_recommendation

**Tracker**: `claude.tools.orchestration.subagent_tracker.SubagentTracker`
- `tracker.start_execution(agent, task)` → execution_id
- `tracker.complete_execution(exec_id, result_summary)`

**Workflow**: `decision.analyze() → builder.build() → Task(prompt=result.prompt)`
"""


def get_orchestration_context(query: str) -> Optional[str]:
    """
    Return orchestration context for exploration queries.

    Args:
        query: User query to analyze

    Returns:
        Orchestration guidance if exploration detected, None otherwise
    """
    # Exploration patterns that should trigger orchestration
    exploration_patterns = [
        r'\bhow\s+(does|do|is|are)\b',
        r'\bwhere\s+(is|are)\b',
        r'\bfind\s+all\b',
        r'\banalyze\b',
        r'\bexplore\b',
        r'\barchitecture\b',
        r'\bwhat\s+is\s+the\b',
        r'\breview\s+the\b',
    ]

    query_lower = query.lower()

    for pattern in exploration_patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return ORCHESTRATION_CONTEXT_TEMPLATE

    return None


def load_smart_context(query: str) -> str:
    """
    Load context optimized for query intent.

    Enhanced to include orchestration tools for exploration queries.
    """
    context_parts = []

    # ... existing smart loading logic ...

    # NEW: Add orchestration context for exploration queries
    orchestration_ctx = get_orchestration_context(query)
    if orchestration_ctx:
        context_parts.append(orchestration_ctx)

    return '\n\n'.join(context_parts)
```

### 3.2 TDD Tests

**File**: `tests/test_smart_context_orchestration.py`

```python
"""Tests for smart context orchestration loading - TDD first."""

import pytest


class TestSmartContextOrchestration:
    """Unit tests for orchestration in smart context."""

    def test_exploration_query_returns_orchestration(self):
        """Test 'how does X work' returns orchestration context."""
        # Given: Exploration query
        # When: get_orchestration_context() called
        # Then: Returns orchestration template
        pass

    def test_find_query_returns_orchestration(self):
        """Test 'find all X' returns orchestration context."""
        pass

    def test_analyze_query_returns_orchestration(self):
        """Test 'analyze X' returns orchestration context."""
        pass

    def test_edit_query_returns_none(self):
        """Test 'edit file X' returns None (no orchestration needed)."""
        pass

    def test_orchestration_context_has_imports(self):
        """Test orchestration context includes tool import paths."""
        pass
```

### 3.3 Gate Criteria

- [ ] `get_orchestration_context()` returns template for exploration queries
- [ ] Returns None for direct action queries
- [ ] All 5 tests passing
- [ ] Integrated into `load_smart_context()`
- [ ] Code review PASS

---

## Phase 4: Compliance Monitoring

**Goal**: Monitor Task tool usage to measure orchestration compliance.

**Duration**: 2 hours
**Subagent**: `devops_principal_architect_agent`
**Model**: `sonnet`

### 4.1 Deliverables

**File**: `claude/hooks/orchestration_compliance_monitor.py` (New)

```python
#!/usr/bin/env python3
"""
Orchestration Compliance Monitor

PostToolUse hook that monitors Task tool calls for orchestration compliance.
Logs whether agent context was injected via SubagentPromptBuilder.

Part of SPRINT-004-ORCHESTRATION-ENFORCEMENT.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Session directory
SESSIONS_DIR = Path.home() / '.maia' / 'sessions'


def get_context_id() -> Optional[str]:
    """Get current context ID from environment or derive from PID."""
    import os
    # Try environment variable first
    context_id = os.environ.get('CLAUDE_CONTEXT_ID')
    if context_id:
        return context_id
    # Fall back to PID-based derivation
    return str(os.getppid() % 100000)


def check_orchestration_compliance(prompt: str) -> Dict[str, Any]:
    """
    Check if Task prompt used orchestration (agent context injection).

    Args:
        prompt: The prompt passed to Task tool

    Returns:
        Compliance analysis dict
    """
    # Markers indicating proper orchestration was used
    orchestration_markers = [
        '## Agent Context',
        'You are operating with the following agent specialization',
        '# SRE Principal Engineer Agent',
        '# Cloud Security Principal Agent',
        '_agent.md',
    ]

    has_agent_context = any(marker in prompt for marker in orchestration_markers)

    # Check for builder output structure
    has_builder_structure = (
        '## Agent Context' in prompt and
        '## Task' in prompt
    )

    return {
        'compliant': has_agent_context,
        'has_builder_structure': has_builder_structure,
        'markers_found': [m for m in orchestration_markers if m in prompt],
        'prompt_length': len(prompt),
    }


def log_compliance(
    context_id: str,
    compliance_data: Dict[str, Any],
    tool_params: Dict[str, Any]
) -> None:
    """
    Log compliance data to session file.

    Args:
        context_id: Session context ID
        compliance_data: Results from check_orchestration_compliance()
        tool_params: Original Task tool parameters
    """
    session_file = SESSIONS_DIR / f'swarm_session_{context_id}.json'

    if not session_file.exists():
        return

    try:
        session_data = json.loads(session_file.read_text())
    except (json.JSONDecodeError, IOError):
        return

    # Initialize compliance tracking if not present
    if 'orchestration_compliance' not in session_data:
        session_data['orchestration_compliance'] = {
            'total_task_calls': 0,
            'compliant_calls': 0,
            'non_compliant_calls': 0,
            'compliance_rate': 0.0,
            'history': [],
        }

    compliance = session_data['orchestration_compliance']

    # Update counters
    compliance['total_task_calls'] += 1
    if compliance_data['compliant']:
        compliance['compliant_calls'] += 1
    else:
        compliance['non_compliant_calls'] += 1

    # Calculate rate
    compliance['compliance_rate'] = (
        compliance['compliant_calls'] / compliance['total_task_calls'] * 100
    )

    # Add to history (keep last 20)
    compliance['history'].append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'compliant': compliance_data['compliant'],
        'has_builder_structure': compliance_data['has_builder_structure'],
        'subagent_type': tool_params.get('subagent_type', 'unknown'),
        'model': tool_params.get('model', 'unknown'),
    })
    compliance['history'] = compliance['history'][-20:]

    # Write back
    session_file.write_text(json.dumps(session_data, indent=2))


def monitor_task_call(tool_output: Dict[str, Any]) -> None:
    """
    Main hook function: Monitor Task tool calls.

    Args:
        tool_output: PostToolUse hook data
    """
    tool_name = tool_output.get('tool_name', '')

    # Only monitor Task tool
    if tool_name != 'Task':
        return

    tool_params = tool_output.get('tool_params', {})
    prompt = tool_params.get('prompt', '')

    # Skip non-general-purpose subagents (they have built-in context)
    subagent_type = tool_params.get('subagent_type', '')
    if subagent_type != 'general-purpose':
        return

    # Check compliance
    compliance_data = check_orchestration_compliance(prompt)

    # Log to session
    context_id = get_context_id()
    if context_id:
        log_compliance(context_id, compliance_data, tool_params)


def main():
    """CLI entry point for PostToolUse hook."""
    # Read tool output from stdin (hook protocol)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Silent exit on bad input

    monitor_task_call(input_data)
    sys.exit(0)


if __name__ == '__main__':
    main()
```

**File**: `.claude/settings.local.json` (Update hooks section)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/orchestration_compliance_monitor.py",
            "timeout": 2000
          }
        ]
      }
    ]
  }
}
```

### 4.2 TDD Tests

**File**: `tests/test_orchestration_compliance.py`

```python
"""Tests for orchestration compliance monitoring - TDD first."""

import pytest
import json
from pathlib import Path


class TestComplianceChecker:
    """Unit tests for compliance checking."""

    def test_prompt_with_agent_context_is_compliant(self):
        """Test prompt containing '## Agent Context' is marked compliant."""
        # Given: Prompt with agent context
        # When: check_orchestration_compliance() called
        # Then: Returns compliant=True
        pass

    def test_prompt_without_agent_context_is_non_compliant(self):
        """Test prompt without agent context is marked non-compliant."""
        pass

    def test_builder_structure_detected(self):
        """Test prompts with builder structure are detected."""
        # Given: Prompt with '## Agent Context' and '## Task'
        # When: check_orchestration_compliance() called
        # Then: has_builder_structure=True
        pass


class TestComplianceLogging:
    """Unit tests for compliance logging."""

    def test_compliance_logged_to_session(self, tmp_path):
        """Test compliance data written to session file."""
        # Given: Session file exists
        # When: log_compliance() called
        # Then: Session contains orchestration_compliance field
        pass

    def test_compliance_rate_calculated(self, tmp_path):
        """Test compliance rate calculated correctly."""
        # Given: Multiple compliance logs
        # When: compliance_rate accessed
        # Then: Correct percentage returned
        pass
```

### 4.3 Gate Criteria

- [ ] `check_orchestration_compliance()` correctly identifies compliant prompts
- [ ] `log_compliance()` writes to session file
- [ ] Compliance rate calculated correctly
- [ ] All 5 tests passing
- [ ] Hook registered in settings.local.json
- [ ] Code review PASS

---

## Phase 5: Documentation + Integration

**Goal**: Update CLAUDE.md, register capabilities, create E2E test.

**Duration**: 1.5 hours
**Subagent**: `sre_principal_engineer_agent`
**Model**: `haiku` (documentation tasks)

### 5.1 Deliverables

**File**: `CLAUDE.md` (Update Principle #26)

```markdown
## Subagent Orchestration (Principle #26 Detail)

**SPRINT-004-ORCHESTRATION-ENFORCEMENT**: Multi-layered enforcement for Task subagent context injection.

### When to Spawn Subagents

| Pattern | Action | Example |
|---------|--------|---------|
| "How does X work?" | SPAWN | Exploration query |
| "Find all X" | SPAWN | Multi-file search |
| "Analyze X" | SPAWN | Deep analysis |
| Sprint mode active | SPAWN | Offload heavy work |
| "Edit file X" | DIRECT | Known specific file |
| "Run command X" | DIRECT | Single command |

### Usage (MANDATORY for general-purpose Task subagents)

```python
from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder
from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

# 1. Check if should spawn
engine = SpawnDecisionEngine()
decision = engine.analyze(query, session_context, files_mentioned=[])

if decision.should_spawn:
    # 2. Build prompt with agent injection
    builder = SubagentPromptBuilder()
    prompt = builder.build(decision.recommended_agent, task)

    # 3. Use Task tool with enriched prompt
    # Task(subagent_type="general-purpose", prompt=prompt.prompt, model=prompt.model_recommendation)
```

### Execution Tracking

All subagent executions recorded in session state via `SubagentTracker`.
Compliance rate tracked in `session.orchestration_compliance`.

### Compliance Monitoring

Session files track orchestration compliance:
- `orchestration_compliance.total_task_calls`: Total Task spawns
- `orchestration_compliance.compliant_calls`: Spawns with agent context
- `orchestration_compliance.compliance_rate`: Percentage compliant

Target: **70-85% compliance rate**
```

**File**: Capability Registration

```bash
python3 claude/tools/core/find_capability.py --register \
  --name orchestration_compliance_monitor.py \
  --type tool \
  --category orchestration \
  --path claude/hooks/orchestration_compliance_monitor.py \
  --keywords "compliance,monitoring,task,subagent,orchestration"
```

### 5.2 TDD Tests

**File**: `tests/integration/test_orchestration_e2e.py`

```python
"""E2E tests for orchestration enforcement - TDD first."""

import pytest
import json
from pathlib import Path


class TestOrchestrationE2E:
    """End-to-end integration tests."""

    def test_session_creation_includes_orchestration(self, tmp_path):
        """Test full /init flow creates session with orchestration."""
        pass

    def test_mandate_injection_includes_orchestration(self):
        """Test agent mandate includes orchestration protocol."""
        pass

    def test_compliance_tracking_works_e2e(self, tmp_path):
        """Test compliance monitoring records Task calls."""
        pass
```

### 5.3 Gate Criteria

- [ ] CLAUDE.md Principle #26 updated with enforcement details
- [ ] Capability registered in capabilities.db
- [ ] All 3 E2E tests passing
- [ ] Documentation review PASS

---

## Success Metrics

### Immediate (After Implementation)
- ✅ Session files contain `orchestration` config
- ✅ Agent mandates include orchestration protocol
- ✅ Smart context returns orchestration tools for exploration
- ✅ Compliance monitoring active

### Week 1
- 🎯 **50%+ compliance rate** (baseline measurement)
- 🎯 **Zero breaking changes** to existing workflows
- 🎯 **All tests green**

### Week 2-4
- 🎯 **70%+ compliance rate** (as Claude learns patterns)
- 🎯 **Positive user feedback** (seamless experience)

### Month 2+
- 🎯 **85%+ compliance rate** (mature pattern)
- 🎯 **Subagent quality improvement** measurable via PAI learning

---

## Rollback Plan

If compliance <50% after 2 weeks:

1. **Escalate**: Add orchestration to ALL agent.md files (90+ files)
2. **Explicit command**: Implement `/spawn` slash command
3. **Document limitation**: Update CLAUDE.md with manual workflow
4. **Feature request**: Advocate for Claude Code PreToolUse hook

---

## Test Summary

| Phase | Test File | Tests | Focus |
|-------|-----------|-------|-------|
| P1 | `tests/test_session_orchestration.py` | 6 | Session config |
| P2 | `tests/test_mandate_orchestration.py` | 4 | Mandate injection |
| P3 | `tests/test_smart_context_orchestration.py` | 5 | Context loading |
| P4 | `tests/test_orchestration_compliance.py` | 5 | Compliance monitoring |
| P5 | `tests/integration/test_orchestration_e2e.py` | 3 | E2E integration |

**Total: 23 tests**

---

## Code Review Gates

Each phase requires code review before proceeding:

```
HANDOFF DECLARATION:
To: python_code_reviewer_agent
Reason: Phase N complete - TDD green, code review required
Context: [files_modified] passed TDD
Key data: {"phase": N, "files": [...], "tests_passed": X}
```

---

## Sprint Contact

**Implementation**: SRE Principal Engineer Agent (P1-P3, P5)
**Monitoring/Hooks**: DevOps Principal Architect Agent (P4)
**Code Review**: Python Code Reviewer Agent (all phases)

---

**Document Version**: 1.0
**Created**: 2026-01-16
**Sprint**: SPRINT-004-ORCHESTRATION-ENFORCEMENT
