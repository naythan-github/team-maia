# Automatic Agent Persistence - TDD Requirements Document

**Project**: Implement Working Principle #15 (Automatic Agent Routing) with Full Swarm Integration
**Status**: Phase 0 - Requirements Discovery Complete
**Created**: 2025-10-20
**Agent Pairing**: AI Specialists Agent + SRE Principal Engineer Agent

---

## 🎯 **PROJECT GOALS**

**Primary Goal**: Complete Phase 121's original vision - transform routing suggestions into automatic agent execution with session persistence and swarm orchestration.

**Success Criteria**:
1. ✅ Agent auto-loads when coordinator suggests (confidence >70%, complexity >3)
2. ✅ Full swarm orchestrator invoked (not single-agent shortcuts)
3. ✅ Agent context switches automatically when domain changes
4. ✅ Context sharing between agents via handoff pattern
5. ✅ Quality improvement: +25-40% (validated via existing quality scoring)
6. ✅ Token reduction: 60-70% for specialist conversations
7. ✅ User experience: Zero manual "load X agent" commands

---

## 📋 **FUNCTIONAL REQUIREMENTS**

### **Requirement 1: Automatic Swarm Invocation**

**Given**: User submits query
**When**: Hook Stage 0.8 routing confidence >70% AND complexity >3
**Then**: Hook invokes SwarmOrchestrator with suggested agent(s)
**And**: Swarm executes with full context sharing and handoff support

**Details**:
- Use existing `SwarmOrchestrator` class (`agent_swarm.py`)
- Use existing `SwarmConversationBridge` for Claude Code integration
- Initial agent determined by coordinator's primary domain
- Allow dynamic handoffs if agent determines additional specialists needed

**Acceptance Criteria**:
```bash
# Test: Technical query triggers swarm
User: "Review my Python code for security issues"
→ Coordinator: Security domain, confidence 85%
→ Hook invokes: SwarmOrchestrator(initial_agent="security_specialist")
→ Result: Security agent active, can handoff if needed
```

---

### **Requirement 2: Domain Change Detection & Agent Switching**

**Given**: Agent currently active (e.g., FinOps Agent)
**When**: User query domain changes (e.g., financial → security)
**Then**: Re-classify intent, detect domain change
**And**: Current agent hands off to new domain specialist with context
**And**: New agent continues with enriched context from previous agent

**Details**:
- Re-classify every message (5-10ms overhead acceptable)
- Switch threshold: New domain confidence >70% AND >20% higher than current
- Context preservation: Use SwarmOrchestrator's context enrichment
- Handoff chain tracking: Log all transitions (Phase 125 integration)

**Acceptance Criteria**:
```bash
# Test: Domain switch mid-conversation
Message 1: "Optimize Azure costs" → FinOps Agent
Message 2: "Make it secure" → Security Agent (receives cost optimization context)
Message 3: "Document it" → Technical Writer Agent (receives cost + security context)

# Handoff chain logged:
FinOps → Security (reason: security requirements added)
Security → Technical Writer (reason: documentation needed)
```

---

### **Requirement 3: Context Persistence & Session Management**

**Given**: Agent loaded via swarm orchestrator
**When**: User continues conversation in same domain
**Then**: Agent context persists (no re-loading overhead)
**And**: Conversation state maintained across messages

**Implementation Approach**: Modified System Message (Option C)

**Mechanism**:
```bash
# Hook creates agent context file
/tmp/maia_active_swarm_session.json:
{
  "current_agent": "security_specialist",
  "session_start": "2025-10-20T14:30:00",
  "handoff_chain": ["finops_agent", "security_specialist"],
  "context": { "previous_work": "...", "key_findings": "..." },
  "domain": "security",
  "last_classification_confidence": 0.87
}

# Maia reads on startup (via CLAUDE.md instruction)
LOAD: ${MAIA_ROOT}/claude/agents/${current_agent}.md
CONTEXT: Enriched with session context from previous agents
```

**Why This Approach**:
- ✅ Natural extension of smart context loading pattern
- ✅ AgentLoader infrastructure already exists
- ✅ File-based state survives across Claude Code messages
- ✅ JSON allows structured context sharing
- ✅ Compatible with swarm handoff pattern

**Acceptance Criteria**:
```bash
# Test: Session persistence
Message 1: "Review code" → Security Agent loads
Message 2: "Check line 42" → Security Agent persists (no reload)
Message 3: "What about performance?" → Security Agent persists OR handoffs to SRE if complexity increases
```

---

### **Requirement 4: Swarm Orchestrator Integration**

**Given**: Hook determines swarm invocation needed
**When**: SwarmOrchestrator.execute_with_handoffs() called
**Then**: Use SwarmConversationBridge for Claude Code integration
**And**: Present agent prompts within conversation context
**And**: Parse responses for handoff declarations
**And**: Maintain handoff chain audit trail

**Details**:
- **Bridge Mode**: "conversation" (not "simulated")
- **Agent Loading**: Via AgentLoader (existing infrastructure)
- **Context Injection**: SwarmOrchestrator enriches context at each handoff
- **Handoff Parsing**: HandoffParser extracts HANDOFF DECLARATION from responses
- **Max Handoffs**: 5 (configurable, prevents infinite loops)

**Integration Points**:
```python
# Hook → SwarmOrchestrator → AgentLoader → Context Injection → Conversation

# 1. Hook invokes orchestrator
swarm = SwarmOrchestrator(agent_dir=Path("claude/agents"))
result = swarm.execute_with_handoffs(
    initial_agent="security_specialist",
    task={"query": user_query, "domain": "security"},
    max_handoffs=5
)

# 2. Orchestrator uses AgentLoader
loader = AgentLoader()
agent_prompt = loader.load_agent("security_specialist")
full_prompt = loader.inject_context(agent_prompt, enriched_context)

# 3. Present in conversation
# (Agent responds within Claude Code conversation)

# 4. Parse for handoffs
handoff = HandoffParser.extract_handoff(agent_response)
if handoff:
    # Continue to next agent with enriched context
```

**Acceptance Criteria**:
```bash
# Test: Multi-agent handoff
User: "Setup Azure Exchange with custom domain"
→ DNS Specialist: Configures DNS records
→ HANDOFF to Azure Architect: "DNS complete, need Exchange setup"
→ Azure Architect: Configures Exchange Online
→ Result: Complete solution with context sharing
```

---

### **Requirement 5: Graceful Degradation & Error Handling**

**Given**: Automatic routing active
**When**: Agent file missing/corrupted OR swarm execution fails
**Then**: Fall back to base Maia context
**And**: Log error for investigation
**And**: Continue conversation (non-blocking failure)

**Error Scenarios**:
1. **Agent file not found**: Fallback to base Maia, log warning
2. **Agent prompt parse error**: Fallback to base Maia, log error
3. **Swarm orchestrator timeout**: Cancel handoff chain, use current agent output
4. **Circular handoff detected**: Break loop, use last valid output
5. **Classification service down**: Skip Stage 0.8, proceed normally

**Acceptance Criteria**:
```bash
# Test: Agent file missing
User: "Optimize Azure costs"
→ Routing suggests: finops_agent
→ File missing: claude/agents/finops_agent.md not found
→ Fallback: Base Maia responds with general Azure knowledge
→ Log: "WARNING: finops_agent file not found, fallback to base context"
```

---

### **Requirement 6: Low Confidence Handling**

**Given**: User submits general query
**When**: Routing confidence <70% OR complexity ≤3
**Then**: No agent loaded, base Maia handles query
**And**: No swarm invocation overhead

**Acceptance Criteria**:
```bash
# Test: General query
User: "What's the weather?"
→ Routing: general domain, confidence 20%, complexity 1
→ Action: Skip Stage 0.8, no agent loading
→ Result: Base Maia responds normally
```

---

### **Requirement 7: Explicit Override Capability**

**Given**: Automatic routing active
**When**: User explicitly requests different agent ("load X agent")
**Then**: Override automatic routing, use requested agent
**And**: Log override (for accuracy tracking - Phase 125)

**OR**

**When**: Maia determines context requires override (full conversation context differs from classification)
**Then**: Maia can override automatic routing
**And**: Log reasoning for override learning

**Acceptance Criteria**:
```bash
# Test: User override
User: "Review this code" (automatic: Security Agent)
User: "Actually, load SRE agent instead"
→ Override: Load SRE agent, log user override
→ Routing logger: Record suggestion vs. actual (Phase 125)
```

---

## 🔧 **NON-FUNCTIONAL REQUIREMENTS (SRE Review)**

### **Performance Requirements**

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Hook Stage 0.8 latency | <50ms | <200ms | >500ms |
| Agent loading time | <1s | <3s | >5s |
| Swarm orchestrator overhead | <100ms/handoff | <300ms/handoff | >1s/handoff |
| Domain classification | <10ms | <50ms | >100ms |
| Session state file I/O | <5ms | <20ms | >50ms |

**SLA**: 95% of agent loads complete within acceptable timeframe

---

### **Reliability Requirements**

**Failure Mode Handling**:
1. **Agent file missing**: Fallback to base Maia (MUST NOT block conversation)
2. **Swarm orchestrator crash**: Return partial results from completed agents
3. **Circular handoff detected**: Break after 5 handoffs (MaxHandoffsExceeded)
4. **Classification service timeout**: Skip Stage 0.8, proceed with base context
5. **Context file corruption**: Recover with empty context, log error

**Data Integrity**:
- Session state file: Atomic writes (tmp file + rename for consistency)
- Handoff chain: Complete audit trail persisted to database (Phase 125)
- Context preservation: Validate JSON schema before reading

**Circuit Breaker Pattern** (SRE Requirement):
```python
# If agent loading fails 3 times in 5 minutes
# → Disable automatic routing for 10 minutes
# → Log critical alert for investigation
# → Auto-recovery after cooldown period
```

---

### **Observability Requirements**

**Logging** (Structured JSON logs):
```json
{
  "timestamp": "2025-10-20T14:30:00Z",
  "event": "agent_loaded",
  "agent": "security_specialist",
  "routing_confidence": 0.87,
  "domain": "security",
  "loading_time_ms": 245,
  "session_id": "conv_abc123"
}
```

**Metrics** (Prometheus-compatible):
```
maia_agent_loads_total{agent="security_specialist"} 42
maia_agent_load_duration_seconds{agent="security_specialist",quantile="0.95"} 0.8
maia_domain_switches_total{from="finops",to="security"} 12
maia_swarm_handoffs_total 156
maia_agent_load_errors_total{reason="file_not_found"} 3
```

**Dashboard Integration**:
- Extend Phase 125 routing accuracy dashboard with:
  - Agent load success rate
  - Average handoffs per query
  - Domain switch frequency
  - Agent load latency P50/P95/P99

**Tracing**:
- Handoff chain visualization (user query → agent 1 → agent 2 → result)
- Context enrichment size tracking (detect context bloat)
- Performance bottleneck identification (which agent/handoff is slow)

---

### **Security Requirements**

**Agent Context Isolation**:
- ❌ Agent A cannot access Agent B's private context
- ✅ Only shared context via handoff declarations
- ✅ Validate handoff context doesn't contain secrets

**File Access Control**:
- Agent files: Read-only for security (no runtime modification)
- Session state: User-scoped (no cross-user context leakage)
- Temporary files: Secure permissions (600), cleaned on conversation end

**Input Validation**:
- Agent names: Whitelist pattern `^[a-z_]+$` (prevent path traversal)
- Context JSON: Schema validation before deserialization
- Handoff declarations: Size limits (prevent DoS via massive context)

---

## 🔄 **INTEGRATION POINTS**

### **Existing Systems to Modify**

**1. Hook Stage 0.8** (`claude/hooks/user-prompt-submit`):
- Current: Displays routing suggestion only
- New: Invokes SwarmOrchestrator, creates session state file
- Impact: +150ms latency (classification + orchestrator initialization)

**2. CLAUDE.md Instructions**:
- Current: Standard context loading sequence
- New: Add "Check for active swarm session" instruction
- Impact: +1-2 lines in CLAUDE.md, Maia reads session state on startup

**3. Phase 125 Routing Logger** (`routing_decision_logger.py`):
- Current: Logs routing suggestions and user acceptance
- New: Log handoff chains, domain switches, agent load times
- Impact: Additional database columns (handoff_chain, session_id)

**4. SwarmOrchestrator** (`agent_swarm.py`):
- Current: STUBBED `_execute_agent()` method
- New: Implement real agent loading via AgentLoader
- Impact: Replace stub with production integration

---

## 📊 **SUCCESS METRICS & VALIDATION**

### **Quality Metrics** (Post-Implementation)

**Baseline** (Current - Manual Agent Selection):
- Specialist engagement rate: 72% manual requests only
- Average response quality: 65/100 (base Maia for specialist queries)
- User satisfaction: 3.8/5.0

**Target** (After Automatic Routing):
- Specialist engagement rate: >90% (automatic routing)
- Average response quality: 85/100 (+25-40% improvement, Phase 107 research)
- User satisfaction: 4.5/5.0

**Measurement Method**:
- Quality scoring: Use existing quality_scorer.py (Phase 126)
- A/B comparison: 20 queries before/after implementation
- Statistical significance: T-test, p<0.05

---

### **Efficiency Metrics**

**Token Savings**:
- Current: Full Maia context every message (~8-12K tokens)
- Target: Specialist context only (~3-5K tokens)
- Expected savings: 60-70% for specialist queries

**Time Savings**:
- Current: User must manually identify and load specialist
- Target: Zero manual intervention (automatic)
- Expected reduction: 30-60 seconds per specialist query

---

### **Reliability Metrics**

**Agent Load Success Rate**: >95%
**Graceful degradation rate**: 100% (no blocking failures)
**Handoff chain completion rate**: >90% (not broken by errors)
**Domain switch accuracy**: >85% (correct agent for domain)

---

## 🧪 **TEST SCENARIOS** (Phase 1: Test Design)

### **Happy Path Tests**

**Test 1: Single Domain Specialist Query**
```
Input: "Review this Python code for security issues"
Expected:
- Classification: security domain, confidence 87%
- Agent loaded: security_specialist
- Session persisted: Yes
- Quality: Security-specific analysis (8/10)
```

**Test 2: Multi-Agent Handoff Chain**
```
Input: "Setup Azure Exchange with custom domain and security"
Expected:
- Agent 1: dns_specialist (DNS records)
- Handoff: dns → azure_solutions_architect (Exchange setup)
- Handoff: azure → security_specialist (security hardening)
- Handoff chain logged: 3 handoffs
- Context preserved: Each agent sees previous work
```

**Test 3: Domain Switch Mid-Conversation**
```
Input 1: "Optimize Azure costs" → finops_agent
Input 2: "Make it secure" → security_specialist (receives cost context)
Expected:
- Domain change detected: finops → security
- Context handoff: Cost optimization details passed
- Session updated: New agent persisted
```

---

### **Error Handling Tests**

**Test 4: Agent File Missing**
```
Setup: Delete security_specialist_agent.md
Input: "Review code for security"
Expected:
- Agent load fails gracefully
- Fallback to base Maia
- Warning logged
- Conversation continues (non-blocking)
```

**Test 5: Circular Handoff Detection**
```
Scenario: Agent A → Agent B → Agent A → Agent B (loop)
Expected:
- MaxHandoffsExceeded after 5 handoffs
- Error logged with handoff chain
- Last valid output returned
```

**Test 6: Low Confidence Query**
```
Input: "What's the weather?"
Expected:
- Classification: general, confidence 15%
- No agent loaded
- Base Maia handles query
- No swarm overhead
```

---

### **Performance Tests**

**Test 7: Hook Latency**
```
Measure: Stage 0.8 execution time
Target: <200ms for 95% of queries
Method: Run 100 queries, measure hook duration
```

**Test 8: Agent Loading Time**
```
Measure: Agent file read + context injection
Target: <3s for 95% of loads
Method: Load 10 different agents, measure duration
```

---

### **Integration Tests**

**Test 9: Phase 125 Logging Integration**
```
Input: Security query with automatic routing
Expected:
- Routing suggestion logged (routing_decisions.db)
- Agent load logged (session_id, agent_name, duration)
- Handoff chain logged (if multi-agent)
- Dashboard displays metrics
```

**Test 10: User Override**
```
Input 1: "Review code" (automatic: security_specialist)
Input 2: "load sre_principal_engineer instead"
Expected:
- Override detected
- SRE agent loaded instead
- Override logged with reasoning
- Routing accuracy tracker updated
```

---

## 📝 **IMPLEMENTATION PHASES**

### **Phase 0: Requirements Discovery** ✅ COMPLETE
- Define functional requirements
- SRE reliability requirements review
- Architecture decisions confirmed
- Test scenarios outlined

### **Phase 1: Test Design** (Next - Estimated 4 hours)
- Create `test_automatic_agent_persistence.py`
- Implement 10 test scenarios above
- Mock SwarmOrchestrator for isolated testing
- Validate test coverage against requirements

### **Phase 2: Hook Enhancement** (Estimated 3 hours)
- Enhance Stage 0.8 in user-prompt-submit
- Add SwarmOrchestrator invocation
- Create session state file mechanism
- Implement graceful degradation

### **Phase 3: SwarmOrchestrator Integration** (Estimated 4 hours)
- Replace `_execute_agent()` stub with AgentLoader
- Implement conversation-driven execution
- Add handoff chain tracking
- Performance optimization (<200ms target)

### **Phase 4: Maia Agent Check Logic** (Estimated 2 hours)
- Add CLAUDE.md instruction for session state check
- Implement context loading from session file
- Validate agent file exists and readable
- Error handling for corrupted state

### **Phase 5: Session Persistence** (Estimated 3 hours)
- Implement domain change detection
- Agent switching logic with context preservation
- Session state updates on handoffs
- Cleanup on conversation end

### **Phase 6: Integration Testing** (Estimated 3 hours)
- End-to-end test with real queries
- Phase 125 logging integration validation
- Performance profiling and optimization
- Error injection testing (resilience)

### **Phase 7: Documentation** (Estimated 2 hours)
- Update Working Principle #15 status
- Document architecture decisions
- User guide for override commands
- Troubleshooting guide

**Total Estimated Time**: 21 hours (vs. original 12 hours - swarm complexity adds ~9 hours)

---

## ✅ **REQUIREMENTS CONFIRMATION CHECKPOINT**

**Requirements Status**: COMPLETE - Ready for Phase 1 (Test Design)

**Key Decisions Made**:
1. ✅ Use SwarmOrchestrator (full multi-agent, not single-agent shortcuts)
2. ✅ Modified system message approach (session state file + CLAUDE.md instruction)
3. ✅ Domain change = automatic agent switch with context handoff
4. ✅ Re-classify every message for domain tracking
5. ✅ Graceful degradation for all error scenarios
6. ✅ Phase 125 integration for logging and accuracy tracking
7. ✅ SRE requirements: Performance SLAs, circuit breaker, observability

**Awaiting Confirmation**:
- [ ] User approves these requirements
- [ ] No additional constraints or concerns
- [ ] Ready to proceed to Phase 1 (Test Design)

**Once confirmed, proceeding to**: `test_automatic_agent_persistence.py` creation

---

## 🤖 **AGENT PAIRING NOTES**

**AI Specialists Agent**: Architectural decisions, swarm orchestration patterns
**SRE Principal Engineer Agent**: Reliability requirements, error handling, observability

**Collaboration Points**:
- Performance SLAs defined by SRE
- Circuit breaker pattern for resilience
- Structured logging for debugging
- Graceful degradation strategies
