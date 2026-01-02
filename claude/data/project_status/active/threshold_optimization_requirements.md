# Threshold Optimization - TDD Requirements

## Project: Agent Routing Threshold Optimization
**Phase**: TDD Implementation
**Date**: 2025-01-02
**Status**: In Progress

---

## Problem Statement

Current 70% confidence threshold is too restrictive for a 90-agent system. UFC philosophy requires specialist-first routing, not generalist fallback.

---

## Functional Requirements

### FR-1: Lower Agent Loading Threshold to 60%
- **FR-1.1**: Agent loading triggers when confidence >= 0.60 (was >0.70)
- **FR-1.2**: Use inclusive comparison (>=) not exclusive (>)
- **FR-1.3**: Remove redundant `domain != "general"` check
- **FR-1.4**: Complexity threshold remains >= 3

### FR-2: Capability Gap Detection at 40%
- **FR-2.1**: Queries with confidence < 0.40 are logged as capability gaps
- **FR-2.2**: Gap log includes: query, attempted domains, timestamp, confidence
- **FR-2.3**: Gap log stored in `claude/data/capability_gaps.json`
- **FR-2.4**: Gaps do NOT trigger agent loading (graceful degradation)

### FR-3: New Agent Recommendation
- **FR-3.1**: When 3+ gaps occur in same domain within 7 days, flag for new agent
- **FR-3.2**: Recommendation includes: domain, query examples, frequency
- **FR-3.3**: Recommendations stored in `claude/data/agent_recommendations.json`

---

## Non-Functional Requirements

### NFR-1: Performance
- Threshold check: <5ms (current SLA maintained)
- Gap logging: <10ms (async/non-blocking preferred)

### NFR-2: Reliability
- Graceful degradation if gap logging fails
- Never block conversation for logging failures

### NFR-3: Backwards Compatibility
- Existing session files remain valid
- No breaking changes to coordinator_agent.py interface

---

## Test Cases

### TC-1: Agent Loading Threshold (60%)
```
TC-1.1: confidence=0.60, complexity=3 → SHOULD load agent
TC-1.2: confidence=0.59, complexity=3 → SHOULD NOT load agent
TC-1.3: confidence=0.70, complexity=3 → SHOULD load agent
TC-1.4: confidence=0.60, complexity=2 → SHOULD NOT load (complexity too low)
TC-1.5: confidence=0.80, domain="general" → SHOULD load (removed domain check)
```

### TC-2: Capability Gap Detection (40%)
```
TC-2.1: confidence=0.39 → SHOULD log capability gap
TC-2.2: confidence=0.40 → SHOULD NOT log gap (at threshold)
TC-2.3: confidence=0.35 → gap log contains query, domains, timestamp
TC-2.4: Gap logging failure → conversation continues (graceful)
```

### TC-3: New Agent Recommendation
```
TC-3.1: 2 gaps in "cooking" domain → NO recommendation
TC-3.2: 3 gaps in "cooking" domain within 7 days → recommendation generated
TC-3.3: 3 gaps in "cooking" domain over 14 days → NO recommendation (too spread)
TC-3.4: Recommendation contains domain, example queries, count
```

---

## Files to Modify

1. `claude/hooks/swarm_auto_loader.py` - Threshold logic
2. `claude/hooks/tests/test_swarm_auto_loader.py` - New/updated tests
3. `claude/data/capability_gaps.json` - New file (gap log)
4. `claude/data/agent_recommendations.json` - New file (recommendations)

---

## Acceptance Criteria

- [ ] All TC-1.x tests pass (60% threshold)
- [ ] All TC-2.x tests pass (gap detection)
- [ ] All TC-3.x tests pass (recommendations)
- [ ] No regression in existing swarm_auto_loader tests
- [ ] Performance SLA maintained (<200ms total)
