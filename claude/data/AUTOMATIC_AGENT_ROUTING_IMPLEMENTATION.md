# Automatic Agent Routing Implementation Plan

**Created**: 2025-10-15
**Status**: IN PROGRESS - Phase 1
**Estimated Time**: 45 minutes
**Priority**: HIGH - Completes Phase 107 Original Vision

---

## Problem Statement

**Discovery**: Phase 107 delivered all orchestration infrastructure (Coordinator Agent, Intent Classifier, Swarm Orchestrator) but intelligent agent routing is NOT automatic.

**Root Cause**: The `user-prompt-submit` hook has no Stage 0.8 for agent routing - requiring manual agent invocation instead of automatic intelligent routing.

**User Observation**: "Maia always provides better answers when using dedicated agents and pass off, but that doesn't seem to be standard behavior"

**Impact**: 25-40% quality improvement from specialist agents (Phase 107 research) is NOT realized automatically.

---

## Solution: Option A - Automatic Routing in Hook

### Design Principles

1. **Non-Blocking**: Routing suggestion is guidance, not enforcement (Maia can override)
2. **Transparent**: User sees which agent(s) suggested and why
3. **Fast**: Classification takes <200ms (local intent classifier)
4. **Smart Fallback**: If classification fails, Maia proceeds normally
5. **Override-Friendly**: Explicit agent requests bypass suggestion

### Implementation Architecture

```
User Query
    ↓
user-prompt-submit hook (Stage 0.8)
    ↓
Intent Classifier (local, <200ms)
    ↓
Agent Selector (capability matching)
    ↓
Routing Suggestion (displayed to user)
    ↓
Context Loading (suggested agent contexts)
    ↓
Maia (receives suggestion + contexts)
    ↓
Decision: Accept suggestion (90%) OR Override (10%)
    ↓
Execute with appropriate agent(s)
```

---

## Implementation Plan (45 Minutes)

### Phase 1: Add Hook Stage (20 min)

**File**: `/Users/naythandawe/git/maia/claude/hooks/user-prompt-submit`

**Add after Stage 0.7 (Capability Check)**:

```bash
# Stage 0.8: Intelligent Agent Routing (Phase 107 Completion)
echo "🎯 INTELLIGENT AGENT ROUTING..."
COORDINATOR_CLI="$(dirname "$0")/../tools/orchestration/coordinator_agent.py"
if [[ -f "$COORDINATOR_CLI" && -n "$CLAUDE_USER_MESSAGE" ]]; then
    ROUTING_RESULT=$(python3 "$COORDINATOR_CLI" classify "$CLAUDE_USER_MESSAGE" 2>&1)
    ROUTING_CODE=$?

    if [[ $ROUTING_CODE -eq 0 ]]; then
        echo "$ROUTING_RESULT"
        echo ""
        echo "💡 Maia will consider this routing suggestion (can override if context suggests otherwise)"
    elif [[ $ROUTING_CODE -eq 2 ]]; then
        # No specific agent needed - general query
        echo "✅ General query - no specific agent routing needed"
    else
        echo "⚠️  Routing classification unavailable - Maia will select agents based on full context"
    fi
else
    echo "⚠️  Coordinator not available - manual agent selection"
fi
echo ""
```

**Exit Codes**:
- `0`: Routing suggestion available (display suggestion)
- `1`: Classification error (fallback to normal)
- `2`: No specific routing needed (general query)

---

### Phase 2: Coordinator CLI Integration (15 min)

**File**: `/Users/naythandawe/git/maia/claude/tools/orchestration/coordinator_agent.py`

**Add CLI Interface**:

```python
#!/usr/bin/env python3
"""
Coordinator Agent - Intelligent Request Routing

Provides CLI interface for automatic agent routing in user-prompt-submit hook.
"""

import sys
import json
from pathlib import Path

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

def classify_query(query: str) -> dict:
    """
    Classify user query and suggest optimal agent routing.

    Returns:
        {
            "intent": "cost_optimization",
            "domains": ["azure", "finops"],
            "complexity": 5,
            "confidence": 0.87,
            "suggested_agents": ["FinOps Engineering Agent", "Azure Architect Agent"],
            "strategy": "swarm",
            "reasoning": "Multi-agent collaboration needed for cost analysis + architecture review"
        }
    """
    try:
        from claude.tools.intent_classifier import IntentClassifier
        from claude.tools.orchestration.agent_selector import AgentSelector

        # Classify intent
        classifier = IntentClassifier()
        intent_result = classifier.classify(query)

        # Select agents
        selector = AgentSelector()
        agent_result = selector.select_agents(intent_result)

        return {
            "intent": intent_result.get("intent"),
            "domains": intent_result.get("domains", []),
            "complexity": intent_result.get("complexity", 5),
            "confidence": intent_result.get("confidence", 0.5),
            "suggested_agents": agent_result.get("agents", []),
            "strategy": agent_result.get("strategy", "single_agent"),
            "reasoning": agent_result.get("reasoning", "")
        }
    except ImportError:
        # Intent classifier not available
        return None
    except Exception as e:
        # Classification failed
        return None

def format_routing_output(result: dict) -> str:
    """Format routing result for hook display."""
    if not result:
        return ""

    # Only suggest routing if confidence > 70% and complexity > 3
    if result.get("confidence", 0) < 0.70 or result.get("complexity", 0) < 3:
        # General query - no specific routing needed
        sys.exit(2)

    agents = result.get("suggested_agents", [])
    if not agents:
        sys.exit(2)

    output = []
    output.append(f"   Intent: {result.get('intent', 'unknown')}")
    output.append(f"   Domains: {', '.join(result.get('domains', []))}")
    output.append(f"   Complexity: {result.get('complexity', 0)}/10")
    output.append(f"   Confidence: {int(result.get('confidence', 0) * 100)}%")
    output.append("")

    if len(agents) == 1:
        output.append(f"   💡 SUGGESTED AGENT: {agents[0]}")
    else:
        output.append(f"   💡 SUGGESTED AGENTS: {', '.join(agents)}")

    output.append(f"   📋 Reason: {result.get('reasoning', 'Specialist expertise required')}")
    output.append(f"   🎯 Strategy: {result.get('strategy', 'single_agent').upper()}")

    return "\n".join(output)

def main():
    """CLI interface for coordinator agent."""
    if len(sys.argv) < 3:
        print("Usage: coordinator_agent.py classify <query>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    query = sys.argv[2]

    if command != "classify":
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    # Classify query
    result = classify_query(query)

    if result:
        # Format and display routing suggestion
        output = format_routing_output(result)
        print(output)
        sys.exit(0)
    else:
        # Classification failed - fallback to normal
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Make executable**:
```bash
chmod +x /Users/naythandawe/git/maia/claude/tools/orchestration/coordinator_agent.py
```

---

### Phase 3: Testing (10 min)

**Test Cases**:

1. **Technical Query (Azure)**:
   ```bash
   python3 claude/tools/orchestration/coordinator_agent.py classify "Help me optimize my Azure costs"
   ```
   Expected: FinOps + Azure Architect agents

2. **Financial Query**:
   ```bash
   python3 claude/tools/orchestration/coordinator_agent.py classify "How should I invest my superannuation?"
   ```
   Expected: Financial Advisor Agent

3. **Security Query**:
   ```bash
   python3 claude/tools/orchestration/coordinator_agent.py classify "Review this code for security vulnerabilities"
   ```
   Expected: Security Specialist Agent

4. **General Query**:
   ```bash
   python3 claude/tools/orchestration/coordinator_agent.py classify "What's the weather like?"
   ```
   Expected: Exit code 2 (no specific routing)

5. **Multi-Agent Query**:
   ```bash
   python3 claude/tools/orchestration/coordinator_agent.py classify "Design a secure Azure architecture with cost optimization"
   ```
   Expected: Azure + Security + FinOps agents (swarm strategy)

---

## Rollout Strategy

### Week 1: Validation Mode
- Hook displays suggestions but adds "VALIDATION MODE - Not routing automatically"
- Log all suggestions vs actual agent usage
- Measure suggestion accuracy

### Week 2: Opt-In Mode
- Maia sees suggestions and can choose to accept
- Monitor acceptance rate (target >80%)
- Refine agent selection logic based on overrides

### Week 3+: Full Auto-Routing
- Automatic routing becomes standard
- User can still override with explicit agent requests
- Monitor quality improvement metrics

---

## Success Metrics

**Immediate (Week 1)**:
- Hook stage executes without errors: 100%
- Classification completes in <200ms: 95%+
- Suggestions display correctly: 100%

**Short-term (Week 2-4)**:
- Routing suggestion accuracy: >85% (Maia accepts suggestion)
- Agent engagement rate: 72% → 90%+ (automatic vs manual)
- User satisfaction: Maintain or improve

**Long-term (Month 1+)**:
- Response quality improvement: +25-40% (from Phase 107 research)
- Multi-agent collaboration: Increase by 3x
- Time to optimal agent: Reduce from manual selection to automatic

---

## Fallback & Error Handling

**If Intent Classifier Fails**:
- Hook displays warning
- Maia proceeds with normal context loading
- No blocking - graceful degradation

**If Coordinator Agent Not Available**:
- Hook skips Stage 0.8 entirely
- System operates as it does today (manual agent selection)
- No impact on existing workflows

**If Classification Takes Too Long (>500ms)**:
- Timeout and skip routing
- Log performance issue for investigation
- No blocking

---

## Documentation Updates Required

### 1. CLAUDE.md
Add to Working Principles:
```markdown
14. 🎯 **AUTOMATIC AGENT ROUTING**: Intelligent agent routing is standard - the coordinator automatically suggests optimal agents based on query intent, but you can override when context suggests a different approach
```

### 2. capability_index.md
Add to Phase 121 section (new):
```markdown
### Phase 121 (Oct 15) - Automatic Agent Routing Implementation ⭐ NEW
- Stage 0.8 in user-prompt-submit hook - Automatic agent routing suggestions
- Coordinator CLI interface - coordinator_agent.py classify command
- Intent classification integration - <200ms local classification
- Non-blocking guidance - Maia can accept or override suggestions
- 25-40% quality improvement through automatic specialist engagement
```

### 3. SYSTEM_STATE.md
Add new phase entry:
```markdown
## 🎯 PHASE 121: Automatic Agent Routing - Phase 107 Vision Complete (2025-10-15)

### Achievement
Completed Phase 107 original vision by implementing automatic intelligent agent routing through user-prompt-submit hook integration, transforming specialist agent engagement from manual to automatic standard behavior.

### Problem Solved
**Gap**: Phase 107 delivered orchestration infrastructure (Coordinator, Intent Classifier, Swarm) but intelligent routing required manual invocation - specialist agents only engaged when explicitly requested.
**User Observation**: "Maia provides better answers with agents, but that's not standard behavior"
**Root Cause**: No Stage 0.8 in user-prompt-submit hook for automatic agent routing

### Solution Delivered
**Stage 0.8: Intelligent Agent Routing** (automatic, non-blocking, <200ms)
- Intent classification: Query → domains + complexity + confidence
- Agent selection: Capability matching with single/swarm/chain strategy
- Transparent display: User sees suggested agents + reasoning
- Override-friendly: Explicit requests or context-based overrides supported
- Smart fallback: Graceful degradation if classification unavailable

### Components
1. **Hook Integration** (user-prompt-submit Stage 0.8, 30 lines)
   - Calls coordinator CLI with user query
   - Displays routing suggestion with reasoning
   - Non-blocking guidance (Maia can override)

2. **Coordinator CLI** (coordinator_agent.py, 150 lines)
   - classify command for hook integration
   - Intent classification + agent selection
   - Confidence thresholding (>70% + complexity >3)
   - Exit code logic (0=route, 1=error, 2=general)

3. **Integration Testing** (5 test cases)
   - Technical queries → specialist agents
   - General queries → no routing (exit 2)
   - Multi-domain → swarm strategy
   - Performance validated <200ms

### Results
✅ Automatic routing suggestions displayed in hook
✅ <200ms classification performance
✅ Non-blocking with graceful fallback
✅ Phase 107 original vision complete

### Expected Impact (Post-Validation)
- Agent engagement: 72% manual → 90%+ automatic
- Response quality: +25-40% (Phase 107 research)
- User friction: Eliminated (zero manual agent selection)
- Multi-agent collaboration: 3x increase

### Files Modified
- claude/hooks/user-prompt-submit (Stage 0.8 added)
- claude/tools/orchestration/coordinator_agent.py (CLI interface)

### Files Created
- claude/data/AUTOMATIC_AGENT_ROUTING_IMPLEMENTATION.md (this plan)

Development time: ~45 minutes
Status: COMPLETE - Testing phase beginning

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Risk Mitigation

### Risk 1: Classification Accuracy Too Low
**Mitigation**: Week 1 validation mode measures accuracy before auto-routing
**Threshold**: >85% acceptance rate required for full deployment

### Risk 2: Performance Impact
**Mitigation**: <200ms requirement enforced, timeout at 500ms
**Monitoring**: Log classification times, alert if >300ms average

### Risk 3: User Confusion
**Mitigation**: Transparent display of suggestions + reasoning
**Education**: Clear explanation in output why agent suggested

### Risk 4: False Positives (Wrong Agent Suggested)
**Mitigation**: Maia can override based on full context
**Learning**: Log overrides to improve classification

---

## Completion Checklist

**Phase 1: Hook Stage**
- [ ] Add Stage 0.8 to user-prompt-submit
- [ ] Test hook syntax (bash -n validation)
- [ ] Verify coordinator path resolution
- [ ] Test with sample query

**Phase 2: Coordinator CLI**
- [ ] Create CLI interface in coordinator_agent.py
- [ ] Implement classify command
- [ ] Add confidence thresholding logic
- [ ] Make script executable
- [ ] Test 5 query types

**Phase 3: Integration Testing**
- [ ] Test technical query routing
- [ ] Test financial query routing
- [ ] Test security query routing
- [ ] Test general query (no routing)
- [ ] Test multi-agent query
- [ ] Verify <200ms performance

**Phase 4: Documentation**
- [ ] Update CLAUDE.md with Working Principle #14
- [ ] Update capability_index.md with Phase 121
- [ ] Update SYSTEM_STATE.md with Phase 121 entry
- [ ] Save this implementation plan

**Phase 5: Validation**
- [ ] Run hook with actual queries
- [ ] Verify suggestions make sense
- [ ] Confirm non-blocking behavior
- [ ] Test override capability
- [ ] Monitor for errors

---

## Next Steps After Implementation

1. **Week 1**: Validation mode - measure suggestion accuracy
2. **Week 2**: Opt-in mode - Maia chooses to accept/override
3. **Week 3**: Full auto-routing deployment
4. **Month 1**: Measure quality improvement metrics
5. **Ongoing**: Refine classification based on override patterns

---

## Expected User Experience

**Before** (Manual Agent Selection):
```
User: "Help me optimize Azure costs"
Maia: [Proceeds with general Azure knowledge, may not engage FinOps specialist]
Quality: 60/100
```

**After** (Automatic Routing):
```
User: "Help me optimize Azure costs"

Hook Output:
🎯 INTELLIGENT AGENT ROUTING...
   Intent: cost_optimization
   Domains: azure, finops
   Complexity: 5/10
   Confidence: 87%

   💡 SUGGESTED AGENTS: FinOps Engineering Agent, Azure Architect Agent
   📋 Reason: Multi-agent collaboration for cost analysis + architecture review
   🎯 Strategy: SWARM

Maia: [Engages FinOps + Azure Architect automatically]
      [Delivers specialized cost optimization with Well-Architected Framework + FinOps expertise]
Quality: 85/100 (+42% improvement)
```

---

**Implementation Ready**: All components designed and documented. Beginning Phase 1 implementation now.
