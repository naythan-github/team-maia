# SPRINT-003: Swarm + Task Tool Orchestration

**Sprint ID**: SPRINT-003-SWARM-TASK-ORCHESTRATION
**Created**: 2026-01-15
**Status**: PLANNED
**Estimated Effort**: 16-20 hours across 6 phases

---

## Executive Summary

Adapt the existing SwarmOrchestrator infrastructure to work with Claude Code's Task tool for real multi-agent execution on Max plan (no API tokens required).

**Architecture**: SwarmOrchestrator = Planner/Analyzer, Task tool = Executor

**Key Deliverables**:
1. `build_subagent_prompt()` - Generates Task prompts with agent.md injection
2. `should_spawn_subagent()` - Decision logic for when to delegate
3. Session tracking for subagent executions
4. Handoff detection on Task results
5. CLAUDE.md guidance for orchestrated workflows
6. Sprint mode integration

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TARGET ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Query                                                                  │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Claude Code (Parent Session)                                         │    │
│  │   - Reads session state via swarm_auto_loader                        │    │
│  │   - Current agent context loaded                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SwarmOrchestrator (PLANNER - Python)                                 │    │
│  │   - should_spawn_subagent(query, context) → Decision + reasoning    │    │
│  │   - get_recommended_agent(query) → Best agent for task              │    │
│  │   - build_subagent_prompt(agent, task) → Full prompt with agent.md  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Task Tool (EXECUTOR - Claude Code built-in)                          │    │
│  │   Task(                                                              │    │
│  │     subagent_type="general-purpose",                                │    │
│  │     prompt=orchestrator_built_prompt,                               │    │
│  │     model="sonnet" | "opus" | "haiku"                               │    │
│  │   )                                                                  │    │
│  │   → Spawns REAL Claude subagent with injected agent context         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SwarmOrchestrator (ANALYZER - Python)                                │    │
│  │   - detect_handoff(result) → Check for transfer_to_X patterns       │    │
│  │   - record_subagent_execution(session, result, agent)               │    │
│  │   - If handoff detected: return next agent recommendation           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                       │
│      ▼                                                                       │
│  Final Result / Next Handoff Recommendation                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Description | Hours | Model | Injected Agent |
|-------|-------------|-------|-------|----------------|
| P1 | Subagent Prompt Builder | 3-4 | Sonnet | sre_principal_engineer_agent |
| P2 | Spawn Decision Logic | 2-3 | Sonnet | sre_principal_engineer_agent |
| P3 | Session Tracking | 2-3 | Sonnet | sre_principal_engineer_agent |
| P4 | Handoff Detection | 2-3 | Opus | devops_principal_architect_agent |
| P5 | CLAUDE.md Integration | 2-3 | Sonnet | sre_principal_engineer_agent |
| P6 | Sprint Mode Integration | 3-4 | Opus | sre_principal_engineer_agent |

**Each phase includes:**
- Implementation work
- Unit tests (TDD)
- Integration tests
- Python code review via `python_code_reviewer_agent`

---

## Phase 1: Subagent Prompt Builder

**Goal**: Create `build_subagent_prompt()` function that generates Task prompts with agent.md content injected.

**Duration**: 3-4 hours
**Model**: Sonnet
**Implementation Agent**: `sre_principal_engineer_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 1.1 Deliverables

**File**: `claude/tools/orchestration/subagent_prompt_builder.py`

```python
"""
Subagent Prompt Builder

Generates Task tool prompts with agent context injection.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SubagentPrompt:
    """Container for built subagent prompt."""
    prompt: str
    agent_name: str
    agent_tokens: int  # Approximate token count of agent content
    task_tokens: int   # Approximate token count of task
    total_tokens: int  # Combined estimate
    model_recommendation: str  # "haiku" | "sonnet" | "opus"

class SubagentPromptBuilder:
    """
    Builds Task tool prompts with agent context injection.

    Usage:
        builder = SubagentPromptBuilder()
        result = builder.build("sre_principal_engineer_agent", "analyze auth system")

        # Then in Claude:
        Task(
            subagent_type="general-purpose",
            prompt=result.prompt,
            model=result.model_recommendation
        )
    """

    def __init__(self, agents_dir: Optional[Path] = None):
        """Initialize with agents directory."""

    def build(
        self,
        agent_name: str,
        task: str,
        additional_context: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> SubagentPrompt:
        """
        Build a complete prompt for Task tool subagent.

        Args:
            agent_name: Name of agent (with or without _agent suffix)
            task: The task description for the subagent
            additional_context: Extra context to include (e.g., file contents)
            output_format: Expected output format (e.g., "JSON", "markdown summary")

        Returns:
            SubagentPrompt with full prompt and metadata
        """

    def _load_agent(self, agent_name: str) -> str:
        """Load agent markdown content."""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: chars / 4)."""

    def _recommend_model(self, total_tokens: int, task_complexity: str) -> str:
        """Recommend model based on token count and complexity."""
```

### 1.2 TDD Test Requirements

**File**: `tests/test_subagent_prompt_builder.py`

```python
"""Tests for SubagentPromptBuilder - TDD first."""

import pytest
from pathlib import Path

class TestSubagentPromptBuilder:
    """Unit tests for prompt builder."""

    def test_build_basic_prompt(self):
        """Test basic prompt building with agent injection."""
        # Given: agent name and task
        # When: build() called
        # Then: prompt contains agent content + task

    def test_build_with_additional_context(self):
        """Test prompt with extra context included."""

    def test_build_with_output_format(self):
        """Test prompt with specified output format."""

    def test_agent_not_found_error(self):
        """Test graceful error when agent doesn't exist."""

    def test_agent_name_normalization(self):
        """Test that 'sre' becomes 'sre_principal_engineer_agent'."""

    def test_token_estimation(self):
        """Test token count estimation is reasonable."""

    def test_model_recommendation_small_task(self):
        """Test haiku recommended for small tasks."""

    def test_model_recommendation_large_task(self):
        """Test sonnet/opus for large tasks."""

    def test_prompt_structure(self):
        """Test prompt has correct sections: Agent Context, Task, Output Format."""

class TestSubagentPromptBuilderIntegration:
    """Integration tests with real agent files."""

    def test_build_with_real_sre_agent(self):
        """Test building prompt with actual SRE agent file."""

    def test_build_with_real_security_agent(self):
        """Test building prompt with actual security agent file."""

    def test_all_agents_loadable(self):
        """Test that all agents in directory can be loaded."""
```

### 1.3 Integration Test

```python
def test_integration_task_prompt_works():
    """
    Integration test: Built prompt works with Task tool.

    NOTE: This test validates the prompt structure.
    Actual Task execution happens in Claude, not pytest.
    """
    builder = SubagentPromptBuilder()
    result = builder.build(
        agent_name="sre_principal_engineer_agent",
        task="List the top 3 Python files by size in claude/tools/",
        output_format="JSON array of {file, size_bytes}"
    )

    # Validate structure
    assert "SRE Principal Engineer" in result.prompt
    assert "List the top 3 Python files" in result.prompt
    assert "JSON array" in result.prompt
    assert result.model_recommendation in ["haiku", "sonnet", "opus"]
    assert result.total_tokens > 0
```

### 1.4 Code Review Gate

After implementation, spawn code review subagent:

```
Task(
    subagent_type="general-purpose",
    description="P1 Code Review",
    model="sonnet",
    prompt="""
    {python_code_reviewer_agent.md content}

    ## Code Review Task

    Review the following files from SPRINT-003 Phase 1:
    - claude/tools/orchestration/subagent_prompt_builder.py
    - tests/test_subagent_prompt_builder.py

    Evaluate:
    1. Code quality and Pythonic patterns
    2. Error handling completeness
    3. Test coverage adequacy
    4. Documentation quality
    5. Edge cases handled

    Return:
    - PASS: No blocking issues
    - FAIL: List of MUST-FIX items
    """
)
```

### 1.5 Phase 1 Success Criteria

- [ ] `SubagentPromptBuilder` class implemented
- [ ] All unit tests passing
- [ ] Integration test validates prompt structure
- [ ] Code review returns PASS
- [ ] Registered in capabilities.db

---

## Phase 2: Spawn Decision Logic

**Goal**: Create `should_spawn_subagent()` function that determines when to delegate to a subagent.

**Duration**: 2-3 hours
**Model**: Sonnet
**Implementation Agent**: `sre_principal_engineer_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 2.1 Deliverables

**File**: `claude/tools/orchestration/spawn_decision.py`

```python
"""
Spawn Decision Logic

Determines when Claude should spawn a Task subagent vs work directly.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class SpawnReason(Enum):
    """Reasons to spawn a subagent."""
    MULTI_FILE_EXPLORATION = "multi_file_exploration"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    HEAVY_RESEARCH = "heavy_research"
    SPRINT_MODE_ACTIVE = "sprint_mode_active"
    EXPLICIT_REQUEST = "explicit_request"
    CONTEXT_PRESERVATION = "context_preservation"

class NoSpawnReason(Enum):
    """Reasons NOT to spawn a subagent."""
    SIMPLE_TASK = "simple_task"
    SPECIFIC_FILE_KNOWN = "specific_file_known"
    DIRECT_EDIT = "direct_edit"
    SINGLE_COMMAND = "single_command"

@dataclass
class SpawnDecision:
    """Result of spawn decision analysis."""
    should_spawn: bool
    reason: SpawnReason | NoSpawnReason
    confidence: float  # 0.0 - 1.0
    recommended_agent: Optional[str]
    explanation: str

class SpawnDecisionEngine:
    """
    Determines when to spawn subagents.

    Usage:
        engine = SpawnDecisionEngine()
        decision = engine.analyze(
            query="How does our authentication work?",
            session_context={"sprint_mode": True}
        )

        if decision.should_spawn:
            # Use SubagentPromptBuilder to create prompt
            # Then call Task tool
    """

    def __init__(self):
        """Initialize decision engine."""
        self.spawn_patterns = self._load_spawn_patterns()
        self.no_spawn_patterns = self._load_no_spawn_patterns()

    def analyze(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None,
        files_mentioned: Optional[List[str]] = None
    ) -> SpawnDecision:
        """
        Analyze whether to spawn a subagent.

        Args:
            query: User's query/task
            session_context: Current session state (sprint_mode, current_agent, etc.)
            files_mentioned: Files referenced in query (if known)

        Returns:
            SpawnDecision with recommendation and reasoning
        """

    def _check_sprint_mode(self, session_context: Dict[str, Any]) -> Optional[SpawnDecision]:
        """If sprint mode active, bias toward spawning."""

    def _check_exploration_patterns(self, query: str) -> Optional[SpawnDecision]:
        """Check for exploration keywords (how, where, find, analyze)."""

    def _check_direct_patterns(self, query: str, files: List[str]) -> Optional[SpawnDecision]:
        """Check for direct work patterns (edit X, read Y, run Z)."""

    def _get_recommended_agent(self, query: str, reason: SpawnReason) -> str:
        """Recommend best agent for the task."""
```

### 2.2 TDD Test Requirements

**File**: `tests/test_spawn_decision.py`

```python
"""Tests for SpawnDecisionEngine - TDD first."""

import pytest

class TestSpawnDecisionEngine:
    """Unit tests for spawn decision logic."""

    def test_exploration_query_spawns(self):
        """Test 'how does X work' triggers spawn."""

    def test_find_query_spawns(self):
        """Test 'find all X' triggers spawn."""

    def test_analyze_query_spawns(self):
        """Test 'analyze X' triggers spawn."""

    def test_simple_edit_no_spawn(self):
        """Test 'edit file X' does NOT spawn."""

    def test_read_specific_file_no_spawn(self):
        """Test 'read file X' does NOT spawn."""

    def test_single_command_no_spawn(self):
        """Test 'run pytest' does NOT spawn."""

    def test_sprint_mode_biases_spawn(self):
        """Test sprint_mode=True increases spawn likelihood."""

    def test_multiple_files_triggers_spawn(self):
        """Test >3 files mentioned triggers spawn."""

    def test_agent_recommendation_sre_for_infra(self):
        """Test infrastructure queries recommend SRE agent."""

    def test_agent_recommendation_security_for_auth(self):
        """Test auth/security queries recommend security agent."""

    def test_confidence_high_for_clear_patterns(self):
        """Test clear patterns have high confidence."""

    def test_confidence_medium_for_ambiguous(self):
        """Test ambiguous queries have medium confidence."""

class TestSpawnDecisionIntegration:
    """Integration tests with session context."""

    def test_with_real_session_file(self):
        """Test decision with actual session state."""

    def test_sprint_mode_from_session(self):
        """Test sprint mode detection from session."""
```

### 2.3 Code Review Gate

Same pattern as Phase 1 - spawn `python_code_reviewer_agent` subagent.

### 2.4 Phase 2 Success Criteria

- [ ] `SpawnDecisionEngine` class implemented
- [ ] Pattern matching for spawn/no-spawn cases
- [ ] Agent recommendation logic working
- [ ] All unit tests passing
- [ ] Integration test with session context
- [ ] Code review returns PASS

---

## Phase 3: Session Tracking

**Goal**: Update session files to track subagent executions and their results.

**Duration**: 2-3 hours
**Model**: Sonnet
**Implementation Agent**: `sre_principal_engineer_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 3.1 Deliverables

**File**: `claude/tools/orchestration/subagent_tracker.py`

```python
"""
Subagent Execution Tracker

Records subagent executions in session files for audit trail.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

@dataclass
class SubagentExecution:
    """Record of a single subagent execution."""
    execution_id: str
    timestamp: str
    agent_injected: str
    task_summary: str
    model_used: str
    result_summary: str
    handoff_detected: bool
    handoff_target: Optional[str]
    tokens_estimated: int
    duration_seconds: Optional[float]

@dataclass
class SubagentChain:
    """Chain of subagent executions in a session."""
    session_id: str
    started_at: str
    executions: List[SubagentExecution] = field(default_factory=list)
    total_executions: int = 0
    handoffs_performed: int = 0

class SubagentTracker:
    """
    Tracks subagent executions in session state.

    Usage:
        tracker = SubagentTracker(context_id="12345")

        # Before spawning
        exec_id = tracker.start_execution(
            agent="sre_principal_engineer_agent",
            task="analyze auth"
        )

        # After Task returns
        tracker.complete_execution(
            exec_id=exec_id,
            result_summary="Found 5 auth files...",
            handoff_target=None
        )
    """

    def __init__(self, context_id: str, session_dir: Optional[Path] = None):
        """Initialize tracker for session."""

    def start_execution(
        self,
        agent: str,
        task: str,
        model: str = "sonnet"
    ) -> str:
        """Record start of subagent execution. Returns execution_id."""

    def complete_execution(
        self,
        exec_id: str,
        result_summary: str,
        handoff_target: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ) -> None:
        """Record completion of subagent execution."""

    def get_chain(self) -> SubagentChain:
        """Get current execution chain."""

    def get_last_execution(self) -> Optional[SubagentExecution]:
        """Get most recent execution."""

    def _update_session_file(self) -> None:
        """Update session JSON with execution data."""
```

### 3.2 Session File Schema Update

Add to `swarm_session_{context_id}.json`:

```json
{
  "current_agent": "sre_principal_engineer_agent",
  "session_start": "2026-01-15T00:00:00Z",
  "handoff_chain": ["sre_principal_engineer_agent"],
  "subagent_executions": {
    "chain_id": "exec_chain_001",
    "started_at": "2026-01-15T22:00:00Z",
    "executions": [
      {
        "execution_id": "exec_001",
        "timestamp": "2026-01-15T22:05:00Z",
        "agent_injected": "sre_principal_engineer_agent",
        "task_summary": "Analyze authentication system",
        "model_used": "sonnet",
        "result_summary": "Found 5 auth-related files, identified JWT pattern",
        "handoff_detected": true,
        "handoff_target": "cloud_security_principal_agent",
        "tokens_estimated": 8500,
        "duration_seconds": 45.2
      }
    ],
    "total_executions": 1,
    "handoffs_performed": 1
  }
}
```

### 3.3 TDD Test Requirements

**File**: `tests/test_subagent_tracker.py`

```python
"""Tests for SubagentTracker - TDD first."""

import pytest
import json
from pathlib import Path

class TestSubagentTracker:
    """Unit tests for execution tracking."""

    def test_start_execution_creates_record(self):
        """Test start_execution creates new record."""

    def test_complete_execution_updates_record(self):
        """Test complete_execution updates existing record."""

    def test_execution_id_unique(self):
        """Test each execution gets unique ID."""

    def test_get_chain_returns_all_executions(self):
        """Test get_chain returns full history."""

    def test_get_last_execution(self):
        """Test get_last_execution returns most recent."""

    def test_session_file_updated(self):
        """Test session JSON file is updated."""

    def test_backward_compatible_session(self):
        """Test works with sessions without subagent_executions field."""

class TestSubagentTrackerIntegration:
    """Integration tests with real session files."""

    def test_integration_with_existing_session(self):
        """Test tracking works with real session file."""

    def test_multiple_executions_chain(self):
        """Test multiple executions build chain correctly."""
```

### 3.4 Code Review Gate

Same pattern - spawn `python_code_reviewer_agent` subagent.

### 3.5 Phase 3 Success Criteria

- [ ] `SubagentTracker` class implemented
- [ ] Session schema updated with subagent_executions
- [ ] Backward compatible with existing sessions
- [ ] All unit tests passing
- [ ] Integration test with real session
- [ ] Code review returns PASS

---

## Phase 4: Handoff Detection

**Goal**: Analyze subagent results for handoff patterns and recommend next agent.

**Duration**: 2-3 hours
**Model**: Opus (architectural decisions)
**Implementation Agent**: `devops_principal_architect_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 4.1 Deliverables

**File**: `claude/tools/orchestration/subagent_handoff.py`

```python
"""
Subagent Handoff Detection

Analyzes subagent results to detect handoff recommendations.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re

@dataclass
class HandoffRecommendation:
    """Handoff recommendation from subagent result analysis."""
    should_handoff: bool
    target_agent: Optional[str]
    reason: str
    context_to_pass: Optional[str]
    confidence: float
    detected_patterns: List[str]

class SubagentHandoffDetector:
    """
    Detects handoff recommendations in subagent results.

    Patterns detected:
    - Explicit: "transfer_to_X", "handoff to X", "recommend X agent"
    - Implicit: Domain keywords suggesting different expertise needed

    Usage:
        detector = SubagentHandoffDetector()
        result = detector.analyze(subagent_output)

        if result.should_handoff:
            # Spawn next subagent with result.target_agent
            # Pass result.context_to_pass as additional context
    """

    def __init__(self):
        """Initialize with handoff patterns."""
        self.explicit_patterns = self._load_explicit_patterns()
        self.domain_keywords = self._load_domain_keywords()

    def analyze(
        self,
        subagent_result: str,
        current_agent: str
    ) -> HandoffRecommendation:
        """
        Analyze subagent result for handoff signals.

        Args:
            subagent_result: Text output from Task subagent
            current_agent: Agent that was injected into subagent

        Returns:
            HandoffRecommendation with analysis
        """

    def _check_explicit_handoff(self, text: str) -> Optional[str]:
        """Check for explicit handoff patterns like 'transfer_to_X'."""

    def _check_domain_mismatch(self, text: str, current_agent: str) -> Optional[str]:
        """Check if result suggests different domain expertise needed."""

    def _extract_context_for_handoff(self, text: str) -> str:
        """Extract key context to pass to next agent."""
```

### 4.2 Handoff Patterns

```python
EXPLICIT_PATTERNS = [
    r"transfer_to_(\w+)",
    r"handoff to (\w+)",
    r"recommend (\w+) agent",
    r"this requires (\w+) expertise",
    r"escalate to (\w+)",
]

DOMAIN_AGENT_MAP = {
    "security": "cloud_security_principal_agent",
    "authentication": "cloud_security_principal_agent",
    "infrastructure": "azure_infrastructure_architect_agent",
    "terraform": "azure_infrastructure_architect_agent",
    "ci/cd": "devops_principal_architect_agent",
    "pipeline": "devops_principal_architect_agent",
    "performance": "sre_principal_engineer_agent",
    "reliability": "sre_principal_engineer_agent",
}
```

### 4.3 TDD Test Requirements

**File**: `tests/test_subagent_handoff.py`

```python
"""Tests for SubagentHandoffDetector - TDD first."""

import pytest

class TestSubagentHandoffDetector:
    """Unit tests for handoff detection."""

    def test_explicit_transfer_to_pattern(self):
        """Test 'transfer_to_security_agent' detected."""

    def test_explicit_handoff_to_pattern(self):
        """Test 'handoff to devops' detected."""

    def test_explicit_recommend_pattern(self):
        """Test 'recommend security agent' detected."""

    def test_domain_keyword_security(self):
        """Test security keywords trigger security agent."""

    def test_domain_keyword_infrastructure(self):
        """Test terraform keywords trigger infra agent."""

    def test_no_handoff_when_appropriate(self):
        """Test no handoff when task completed by current agent."""

    def test_context_extraction(self):
        """Test key context extracted for handoff."""

    def test_confidence_high_explicit(self):
        """Test explicit patterns have high confidence."""

    def test_confidence_medium_implicit(self):
        """Test implicit patterns have medium confidence."""

class TestSubagentHandoffIntegration:
    """Integration tests with real agent outputs."""

    def test_sre_to_security_handoff(self):
        """Test SRE result triggers security handoff."""

    def test_multi_domain_result(self):
        """Test result with multiple domains picks best match."""
```

### 4.4 Code Review Gate

Same pattern - spawn `python_code_reviewer_agent` subagent.

### 4.5 Phase 4 Success Criteria

- [ ] `SubagentHandoffDetector` class implemented
- [ ] Explicit pattern detection working
- [ ] Domain keyword detection working
- [ ] Context extraction working
- [ ] All unit tests passing
- [ ] Integration test with sample outputs
- [ ] Code review returns PASS

---

## Phase 5: CLAUDE.md Integration

**Goal**: Update CLAUDE.md with orchestrated workflow guidance and integrate with existing protocols.

**Duration**: 2-3 hours
**Model**: Sonnet
**Implementation Agent**: `sre_principal_engineer_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 5.1 Deliverables

**CLAUDE.md additions**:

```markdown
## Subagent Orchestration (Principle #26)

**When to delegate to subagents**: Use Task tool with agent injection for heavy exploration work to keep parent context clean.

### Decision Logic

```python
from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

engine = SpawnDecisionEngine()
decision = engine.analyze(query, session_context)

if decision.should_spawn:
    # Build prompt with agent injection
    from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder
    builder = SubagentPromptBuilder()
    prompt = builder.build(decision.recommended_agent, task)

    # Then call Task tool with built prompt
```

### When to Spawn Subagents

| Pattern | Action | Example |
|---------|--------|---------|
| "How does X work?" | SPAWN | Exploration query |
| "Find all X" | SPAWN | Multi-file search |
| "Analyze X" | SPAWN | Deep analysis |
| Sprint mode active | SPAWN | Offload heavy work |
| "Edit file X" | DIRECT | Known specific file |
| "Run command X" | DIRECT | Single command |
| "Read file X" | DIRECT | Specific file read |

### Execution Tracking

All subagent executions are recorded in session state:
- Agent injected
- Task summary
- Result summary
- Handoff detection
- Duration and token estimates

### Handoff Detection

After subagent completes, check for handoff:

```python
from claude.tools.orchestration.subagent_handoff import SubagentHandoffDetector

detector = SubagentHandoffDetector()
handoff = detector.analyze(result, current_agent)

if handoff.should_handoff:
    # Spawn next subagent with handoff.target_agent
    # Pass handoff.context_to_pass as additional context
```
```

### 5.2 Update Key Paths Table

Add to Key Paths section:

```markdown
| Subagent Builder | `claude/tools/orchestration/subagent_prompt_builder.py` |
| Spawn Decision | `claude/tools/orchestration/spawn_decision.py` |
| Subagent Tracker | `claude/tools/orchestration/subagent_tracker.py` |
| Handoff Detector | `claude/tools/orchestration/subagent_handoff.py` |
```

### 5.3 Update Working Principles Table

Add row 26:

```markdown
| 26 | **Subagent Orchestration** | Use Task + agent injection for heavy work, track in session | `subagent_prompt_builder.py` |
```

### 5.4 Phase 5 Success Criteria

- [ ] CLAUDE.md updated with subagent orchestration section
- [ ] Key Paths table updated
- [ ] Working Principles table updated
- [ ] Examples are accurate and tested
- [ ] Documentation review passes

---

## Phase 6: Sprint Mode Integration

**Goal**: Wire subagent orchestration into sprint mode for automated heavy work delegation.

**Duration**: 3-4 hours
**Model**: Opus (integration complexity)
**Implementation Agent**: `sre_principal_engineer_agent`
**Code Review Agent**: `python_code_reviewer_agent`

### 6.1 Deliverables

**File**: `claude/tools/orchestration/sprint_orchestrator.py`

```python
"""
Sprint Mode Orchestrator

Integrates subagent orchestration with sprint mode.
Part of SPRINT-003-SWARM-TASK-ORCHESTRATION.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

from .subagent_prompt_builder import SubagentPromptBuilder
from .spawn_decision import SpawnDecisionEngine
from .subagent_tracker import SubagentTracker
from .subagent_handoff import SubagentHandoffDetector

@dataclass
class SprintTask:
    """A task within a sprint."""
    task_id: str
    description: str
    status: str  # pending | in_progress | completed | blocked
    agent_recommended: str
    spawn_subagent: bool
    result_summary: Optional[str] = None

@dataclass
class SprintPlan:
    """A sprint plan with tasks."""
    sprint_id: str
    name: str
    tasks: List[SprintTask]
    current_task_index: int = 0
    status: str = "active"  # active | completed | paused

class SprintOrchestrator:
    """
    Orchestrates sprint execution with subagent delegation.

    Usage:
        orchestrator = SprintOrchestrator(context_id="12345")

        # Create sprint plan
        orchestrator.create_sprint("SPRINT-004-auth-refactor", [
            "Analyze current auth implementation",
            "Identify security gaps",
            "Design new auth flow",
            "Implement changes",
            "Write tests"
        ])

        # Get next task with orchestration recommendation
        task_info = orchestrator.get_current_task()
        # Returns: SprintTask with spawn_subagent=True, agent_recommended="sre"

        # After task complete
        orchestrator.complete_task(result_summary="Found 5 auth files...")
    """

    def __init__(self, context_id: str):
        """Initialize orchestrator."""
        self.context_id = context_id
        self.prompt_builder = SubagentPromptBuilder()
        self.decision_engine = SpawnDecisionEngine()
        self.tracker = SubagentTracker(context_id)
        self.handoff_detector = SubagentHandoffDetector()

    def create_sprint(self, sprint_id: str, tasks: List[str]) -> SprintPlan:
        """Create a new sprint plan with tasks."""

    def get_current_task(self) -> Optional[SprintTask]:
        """Get current task with orchestration recommendations."""

    def build_task_prompt(self, task: SprintTask) -> str:
        """Build Task tool prompt for current task."""

    def complete_task(self, result_summary: str) -> Optional[SprintTask]:
        """Complete current task, return next task if any."""

    def analyze_result_for_handoff(self, result: str) -> Dict[str, Any]:
        """Check if result suggests handoff needed."""

    def get_sprint_status(self) -> Dict[str, Any]:
        """Get current sprint status and progress."""
```

### 6.2 Sprint Mode Session Schema

Add to session file:

```json
{
  "sprint_mode": {
    "active": true,
    "sprint_id": "SPRINT-004-auth-refactor",
    "current_task_index": 1,
    "tasks": [
      {"task_id": "task_001", "description": "Analyze auth", "status": "completed"},
      {"task_id": "task_002", "description": "Identify gaps", "status": "in_progress"},
      {"task_id": "task_003", "description": "Design flow", "status": "pending"}
    ],
    "subagent_executions_count": 3
  }
}
```

### 6.3 TDD Test Requirements

**File**: `tests/test_sprint_orchestrator.py`

```python
"""Tests for SprintOrchestrator - TDD first."""

import pytest

class TestSprintOrchestrator:
    """Unit tests for sprint orchestration."""

    def test_create_sprint(self):
        """Test sprint creation with tasks."""

    def test_get_current_task(self):
        """Test getting current task."""

    def test_complete_task_advances(self):
        """Test completing task advances to next."""

    def test_build_task_prompt_injects_agent(self):
        """Test prompt building includes agent context."""

    def test_handoff_detection_integration(self):
        """Test handoff detection on task results."""

    def test_sprint_status(self):
        """Test status reporting."""

    def test_sprint_completion(self):
        """Test sprint marks complete when all tasks done."""

class TestSprintOrchestratorIntegration:
    """Integration tests with full workflow."""

    def test_full_sprint_workflow(self):
        """Test complete sprint from creation to completion."""

    def test_sprint_with_handoffs(self):
        """Test sprint where tasks trigger handoffs."""
```

### 6.4 Code Review Gate

Same pattern - spawn `python_code_reviewer_agent` subagent.

### 6.5 Phase 6 Success Criteria

- [ ] `SprintOrchestrator` class implemented
- [ ] Sprint plan creation working
- [ ] Task progression working
- [ ] Subagent prompt building integrated
- [ ] Handoff detection integrated
- [ ] Session tracking integrated
- [ ] All unit tests passing
- [ ] Full workflow integration test passing
- [ ] Code review returns PASS

---

## Final Integration Test

After all phases complete, run end-to-end integration test:

```python
def test_full_orchestration_workflow():
    """
    End-to-end test of subagent orchestration.

    Scenario:
    1. Create sprint with 3 tasks
    2. First task: exploration (should spawn subagent)
    3. Subagent result suggests handoff
    4. Second task: with new agent
    5. Third task: direct work (no spawn)
    6. Sprint completes

    Validates:
    - Sprint creation
    - Spawn decision logic
    - Prompt building with agent injection
    - Session tracking
    - Handoff detection
    - Sprint completion
    """
```

---

## Success Criteria Summary

| Phase | Key Deliverable | Test Coverage |
|-------|-----------------|---------------|
| P1 | `SubagentPromptBuilder` | Unit + Integration |
| P2 | `SpawnDecisionEngine` | Unit + Integration |
| P3 | `SubagentTracker` | Unit + Integration |
| P4 | `SubagentHandoffDetector` | Unit + Integration |
| P5 | CLAUDE.md updates | Documentation review |
| P6 | `SprintOrchestrator` | Unit + Integration + E2E |

---

## Rollback Plan

If issues arise in production:

1. **Disable sprint mode**: Set `sprint_mode.active = false` in session
2. **Bypass orchestration**: Use Task tool directly without orchestrator
3. **Revert CLAUDE.md**: Remove Principle #26 section
4. **Keep tools available**: Don't remove Python code, just don't use it

---

## Next Steps

1. Review this plan
2. Approve or request modifications
3. Begin Phase 1 with TDD approach
4. Gate each phase on code review pass

---

**Sprint Contact**: SRE Principal Engineer Agent
**Review Agent**: Python Code Reviewer Agent
**Documentation**: CLAUDE.md, capability_index.md
