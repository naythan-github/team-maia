# TDD Development Protocol - Maia Standard Workflow

## 🚨 **MANDATORY ENFORCEMENT** 🚨
**STATUS**: REQUIRED for ALL development work (tools, agents, features, bug fixes, schema changes)
**EXEMPTIONS**: Documentation-only changes, configuration-only changes (no code logic)
**AGENT PAIRING**: Domain Specialist + SRE Principal Engineer Agent (ALWAYS)

## Overview
MANDATORY protocol for ALL Test-Driven Development to prevent requirements drift and ensure production-ready, SRE-hardened implementations before deployment.

## Key Problems Addressed
- Requirements drift during implementation
- Premature test creation before complete requirements gathering
- Lost decisions and requirements through conversation
- Better outcomes consistently observed with TDD approach
- Production reliability issues from missing SRE review
- Domain expertise gaps without specialist agent involvement

## Standard TDD Workflow

### Phase 0: Pre-Discovery Architecture Review ⭐ **PHASE 135**
**CRITICAL**: Check architecture BEFORE starting requirements

1. **Architecture Documentation Check**
   - Does `PROJECT/ARCHITECTURE.md` exist for this system?
   - If YES: Read it to understand deployment model, integration points, operational commands
   - If NO + infrastructure work: Plan to create ARCHITECTURE.md after implementation

2. **Review Relevant ADRs**
   - Check `PROJECT/ADRs/` directory for related decisions
   - Understand: Why current architecture? What alternatives were rejected?
   - Identify architectural constraints (e.g., "MUST use docker exec, NOT direct connection")

3. **Verify Active Deployments**
   - Check `claude/context/core/active_deployments.md`
   - Understand: What systems are running? How to access them?
   - Avoid: Duplicate deployments, conflicting ports, incompatible versions

**Gate**: Understand current architecture before proceeding to requirements

---

### Phase 1: Requirements Discovery (NO CODING/TESTS)
**CRITICAL**: No tests or code until requirements are complete and confirmed

1. **Core Purpose Discovery**
   - What problem are we solving?
   - Who will use this?
   - What's the success criteria?

2. **Functional Requirements Gathering**
   - Input: What goes in?
   - Processing: What transformations?
   - Output: What comes out?
   - Error cases: What could go wrong?

3. **Example-Driven Clarification**
   - "Walk me through a typical use case"
   - "What happens if [edge case]?"
   - "Show me example input/output"
   - Request at least 3 concrete usage examples

4. **Non-Functional Requirements**
   - Performance requirements?
   - Security constraints?
   - Integration points?
   - Future extensibility needs?

5. **Explicit Confirmation Checkpoint**
   - Summarize all requirements discovered
   - Ask "What am I missing?"
   - Wait for explicit "requirements complete" confirmation
   - **HARD GATE**: Do not proceed without confirmation

### Phase 2: Requirements Documentation
1. Create `requirements.md` with all discovered requirements
2. Include acceptance criteria for each requirement
3. Document example scenarios and edge cases
4. Get explicit approval of documented requirements

### Phase 3: Test Design (ONLY after requirements confirmed)
1. Set up appropriate test framework
2. Create `test_requirements.py` (or language-appropriate test file)
3. Write failing tests for EACH requirement
4. Confirm test coverage matches requirements
5. No implementation until all requirement tests exist

### Phase 3.5: Integration Test Design ⭐ **NEW - MANDATORY**
**CRITICAL**: Design integration tests BEFORE implementation

Integration tests verify cross-component interactions, not just isolated unit behavior. These tests catch the gaps that unit tests miss (N+1 queries, circuit breaker failures, missing observability).

**Required Test Categories**:

1. **Cross-Component Integration Tests** (MANDATORY)
   - Test interactions between modules/services
   - Verify data flow across boundaries
   - Validate error propagation
   - Example: `test_end_to_end_workflow()`, `test_database_to_api_integration()`

2. **External Integration Tests** (if applicable)
   - Test interactions with external services (APIs, databases, queues)
   - Use test doubles/mocks for external dependencies
   - Validate contract adherence
   - Example: `test_api_client_handles_rate_limits()`, `test_database_connection_pooling()`

3. **State Management Tests** (if applicable)
   - Test data persistence across operations
   - Validate transaction boundaries
   - Test rollback scenarios
   - Example: `test_transaction_rollback_on_error()`, `test_session_state_persistence()`

**SRE Collaboration** (Phase 3.5):
- SRE Agent reviews integration test design
- Validates failure mode coverage
- Ensures observability test coverage
- Approves integration test plan

**Gate**: No implementation until integration test plan approved

### Phase 4: Implementation
1. Standard TDD red-green-refactor cycle
2. Make tests pass one at a time
3. Regular verification against requirements.md
4. Update documentation if requirements evolve

### Phase 5: Integration Test Execution & Registration ⭐ **ENHANCED - MANDATORY**
**CRITICAL**: Execute integration tests and register new capabilities

1. **Unit Test Verification** (existing)
   - All Phase 3 requirement tests passing
   - Code coverage >80%

2. **Integration Test Execution** ⭐ **NEW**
   - Run Phase 3.5 integration tests
   - Verify cross-component interactions
   - Validate state management
   - **Gate**: All integration tests must pass

3. **Capabilities Scan** (if new tools/agents created)
   ```bash
   python3 claude/tools/sre/capabilities_registry.py scan
   ```
   - Registers new tools/agents in capabilities.db
   - Makes them discoverable by smart context loader

4. **SYSTEM_STATE Update** (if significant feature)
   - Add phase entry documenting the new capability
   - Run ETL to sync:
   ```bash
   python3 claude/tools/sre/system_state_etl.py --recent 10
   ```

5. **Save State Handoff**
   - If TDD project complete, execute save_state workflow
   - Ensures all databases synchronized
   - Commits with proper phase documentation

**Gate**: New capabilities NOT production-ready until:
- ✅ Unit tests passing
- ✅ Integration tests passing ⭐ **NEW**
- ✅ Databases synchronized

### Phase 6: Post-Implementation Validation ⭐ **NEW - MANDATORY**
**CRITICAL**: Production readiness validation before declaring complete

This phase catches production issues that unit/integration tests miss (performance degradation, circuit breaker failures, missing observability).

**Required Validation Categories**:

1. **Performance Testing** (MANDATORY)
   - Load test at 10x expected traffic
   - Validate P95/P99 latency meets SLOs
   - Resource utilization acceptable (<70% CPU/memory)
   - Query count assertions (prevent N+1)
   - Example: `test_api_latency_under_10x_load()`, `test_max_query_count()`

2. **Resilience Testing** (MANDATORY)
   - Circuit breaker validation (dependency failures)
   - Fallback behavior verification
   - Graceful degradation tests
   - Retry logic with exponential backoff
   - Example: `test_circuit_breaker_opens_on_errors()`, `test_fallback_to_cache()`

3. **Observability Validation** (MANDATORY)
   - Structured logs emitted for key operations
   - Metrics exported (RED: Rate, Errors, Duration)
   - Trace context propagated
   - Dashboard smoke test
   - Example: `test_logs_contain_request_id()`, `test_metrics_exported()`

4. **Smoke Testing** (MANDATORY)
   - End-to-end happy path in production-like environment
   - Health check endpoints responding
   - Critical user journeys functional
   - Example: `test_smoke_create_user_e2e()`, `test_health_check_returns_200()`

5. **Contract Testing** (if public API)
   - API response schemas validated
   - Backward compatibility verified
   - OpenAPI spec generation/validation
   - Example: `test_api_matches_published_schema()`, `test_backward_compatibility()`

**SRE Production Readiness Review** (Phase 6):
- SRE Agent validates all 5 validation categories
- Reviews performance test results against SLOs
- Approves resilience and observability implementation
- Signs off on production deployment

**Gate**: Production deployment NOT approved until all validation passing

## 🤖 **AGENT PAIRING PROTOCOL** 🤖

### Automatic Agent Selection
**TRIGGER**: ANY development task (tool, agent, feature, bug fix, schema change)

**AGENT PAIRING FORMULA**:
1. **Domain Specialist Agent** - Primary domain expertise
2. **SRE Principal Engineer Agent** - Production reliability, observability, error handling

### Agent Selection Process (Self-Consultation)
**Maia's Internal Process**:
1. Detect development task type (ServiceDesk, Security, Cloud, Data, etc.)
2. Ask internally: "Which domain specialist would Naythan want for this?"
3. Analyze options using systematic framework:
   - Domain expertise match (90% weight)
   - Past success with similar tasks (10% weight)
4. Present recommendation with reasoning
5. Proceed with selected pairing (no approval wait)

**Example Output**:
> "This ServiceDesk ETL work needs the **Service Desk Manager Agent** (domain expertise in ticket analysis patterns) + **SRE Principal Engineer Agent** (pipeline reliability, circuit breakers, observability). Proceeding with this pairing."

### SRE Agent Lifecycle Integration
**Phase 1 (Requirements)**: SRE defines reliability requirements
- Observability needs (logging, metrics, tracing)
- Error handling requirements (circuit breakers, retries, fallbacks)
- Performance SLOs (latency, throughput, resource limits)
- Data quality gates (validation, cleaning, profiling)
- Operational requirements (health checks, graceful degradation)

**Phase 2-3 (Test Design & Implementation)**: SRE collaborates during development
- Review test coverage for failure modes
- Validate error handling paths
- Ensure observability instrumentation
- Co-design reliability patterns

**Phase 4 (Review)**: SRE reviews implementation
- Production readiness assessment
- Performance validation
- Security review
- Operational runbook validation

### Domain Specialist Examples
- **ServiceDesk work** → Service Desk Manager Agent
- **Security analysis** → Security Specialist Agent
- **Cloud infrastructure** → Azure Solutions Architect Agent
- **Data pipelines** → Data Analyst Agent
- **Recruitment tools** → Technical Recruitment Agent
- **Information management** → Information Management Orchestrator Agent

## Conversation Management

### Starting a TDD Project (AUTOMATIC TRIGGER)
**OLD BEHAVIOR** (deprecated): User says "Let's do TDD"
**NEW BEHAVIOR** (mandatory): Maia auto-detects development work and initiates TDD

**🚨 AUTO-DETECTION TRIGGERS - TDD IS MANDATORY FOR** 🚨

**ALWAYS Trigger TDD Workflow When Creating**:
- ✅ Tools: `*.py` files in `claude/tools/`
- ✅ Agents: `*.md` files in `claude/agents/`
- ✅ Hooks: `*.py` files in `claude/hooks/`
- ✅ Core Policies: `*.md` files in `claude/context/core/` (if executable/enforced)
- ✅ Commands: `*.md` files in `claude/commands/` (if they contain logic)
- ✅ ANY code that will be executed (Python, bash, etc.)
- ✅ Database schema changes
- ✅ API modifications
- ✅ Integration work

**🚨 CRITICAL: User Saying "Proceed" Does NOT Override TDD** 🚨
- Even if user says "go ahead", "do it", "execute", "proceed"
- TDD is MANDATORY for development work (not optional)
- Must complete requirements discovery FIRST
- Must get "requirements complete" confirmation
- Must write tests BEFORE implementation

**Exception - User Can Skip TDD By**:
- Explicitly saying "skip TDD for this" (rare, emergency only)
- Documentation-only changes (no executable code)
- Configuration-only changes (no logic)

**Maia's Automatic Workflow**:
1. **Detect development task** (code changes, new tools, bug fixes, schema changes)
2. **Halt execution** if no requirements.md exists yet
3. **Agent Pairing**: Select domain specialist + SRE (announce selection)
4. **Phase 1**: Initiate requirements discovery questions
5. **Phase 2-4**: Execute TDD workflow with both agents

### During Development
- Start each session: "Let me read the requirements file"
- After design decisions: "Updating requirements with our decisions..."
- Before implementing: "Let me verify against our test suite"
- Regular checkpoint: "Are we still aligned with requirements?"

### 🚨 Agent Continuity & Progress Preservation 🚨

**CRITICAL**: Multi-phase projects risk losing agent context after:
- Context compression (long sessions)
- Session breaks
- Phase transitions
- Base Maia taking over without agent reload

**MANDATORY PRACTICES**:

1. **Agent Reload Instructions in ALL Implementation Plans**:
   ```markdown
   ## Phase 1: Requirements Discovery
   **AGENT**: Load SRE Principal Engineer Agent + [Domain Specialist]
   **Command**: "load sre_principal_engineer_agent"

   [Phase 1 steps...]

   **Save Progress**: Update {PROJECT}_progress.md with Phase 1 completion

   ## Phase 2: Test Design
   **AGENT RELOAD**: "load sre_principal_engineer_agent" (don't assume persistence)

   [Phase 2 steps...]
   ```

2. **Incremental Progress Saving**:
   - **Location**: `claude/data/project_status/active/{PROJECT}_progress.md`
   - **Frequency**: After EACH phase completion (not just at end)
   - **Trigger**: Every 30-60 minutes of work OR natural breakpoints
   - **Content**:
     ```markdown
     # {PROJECT} - Progress Tracker

     **Last Updated**: [timestamp]
     **Active Agents**: SRE Principal Engineer Agent + [Domain Specialist]

     ## Completed Phases
     - [x] Phase 1: Requirements Discovery (2025-11-07 14:30)
       - Created requirements.md
       - Confirmed with user
       - Decision: [key decisions made]

     ## Current Phase
     - [ ] Phase 2: Test Design (IN PROGRESS)
       - Status: 60% complete
       - Next: Write remaining edge case tests

     ## Session Resumption
     **Command**: "load sre_principal_engineer_agent"
     **Context**: Working on {PROJECT}, Phase 2 test design
     **Next Step**: Complete edge case tests, then proceed to implementation
     ```

3. **Session Start Protocol**:
   - Read `{PROJECT}_progress.md` FIRST
   - Reload agent context: "load sre_principal_engineer_agent"
   - Confirm identity: "I'm the SRE Principal Engineer Agent, resuming..."
   - Continue from documented next step

4. **Base Maia Takeover Detection**:
   - **Warning sign**: Response doesn't start with agent identity
   - **Recovery**: User says "reload SRE agent" or "load sre_principal_engineer_agent"
   - **Prevention**: Explicit reload commands at phase transitions

### Key Phrases
- **"Requirements complete"** - User signal to proceed to test phase
- **"Check requirements"** - Prompts re-reading of requirements.md
- **"Update requirements"** - Captures new decisions
- **"Show me the tests"** - Validates test coverage

## File Structure for TDD Projects
```
project_name/
├── requirements.md          # Living requirements document
├── test_requirements.py     # Tests encoding all requirements
├── implementation.py        # Actual implementation
└── README.md               # Project overview

claude/data/project_status/active/
└── {PROJECT}_progress.md    # Incremental progress tracking (multi-phase projects)
```

## Success Metrics
- Zero requirement misses after implementation
- All initial tests remain valid (no deletion due to misunderstanding)
- Requirements document stays current with implementation
- No "oh, I forgot to mention" moments after test creation
- **Agent continuity maintained** (no base Maia takeovers mid-project)
- **Progress preserved** (can resume after any interruption)
- **Incremental saves completed** (progress.md updated after each phase)
- **Capabilities registered** (new tools/agents in capabilities.db) ⭐ **PHASE 179**
- **Databases synchronized** (system_state.db + capabilities.db current) ⭐ **PHASE 179**
- **Integration tests passing** (cross-component, external, state management) ⭐ **PHASE 193**
- **Performance validated** (P95/P99 latency meets SLOs, no N+1 queries) ⭐ **PHASE 193**
- **Resilience tested** (circuit breakers, fallbacks, graceful degradation) ⭐ **PHASE 193**
- **Observability confirmed** (logs/metrics/traces emitted, dashboard functional) ⭐ **PHASE 193**
- **Production readiness approved** (SRE sign-off on all validation categories) ⭐ **PHASE 193**

## Quality Gates
1. **Requirements Gate**: No tests until "requirements complete" confirmation
2. **Test Gate**: No implementation until all tests written
3. **Implementation Gate**: No feature complete until all tests pass
4. **Documentation Gate**: Requirements.md updated with any changes
5. **Progress Gate**: Progress saved after EACH phase (not just at end)
6. **Agent Continuity Gate**: Agent identity confirmed at phase transitions
7. **Registration Gate** ⭐ **PHASE 179**: New tools/agents registered in capabilities.db
8. **Sync Gate** ⭐ **PHASE 179**: Databases synced before declaring production-ready
9. **Integration Test Design Gate** ⭐ **PHASE 193**: Phase 3.5 integration tests designed and approved
10. **Integration Execution Gate** ⭐ **PHASE 193**: Phase 5 integration tests passing
11. **Production Readiness Gate** ⭐ **PHASE 193**: Phase 6 all validation passing (performance, resilience, observability, smoke, contracts)

## Risk Mitigation
- Active probing during discovery phase
- Multiple concrete examples required
- Explicit confirmation checkpoints
- Regular requirements verification
- Test-first discipline enforcement
- **Agent context loss prevention** (explicit reload commands in plans)
- **Progress loss prevention** (incremental saves after each phase)
- **Base Maia takeover prevention** (identity confirmation at transitions)

## Why This Works
1. **Persistent Documentation**: Requirements survive context resets
2. **Executable Verification**: Tests prove requirements are met
3. **Double Verification**: Both documentation and tests must align
4. **Systematic Discovery**: Comprehensive requirements before coding
5. **Clear Checkpoints**: Explicit gates prevent premature progress

## Integration with Maia Principles
- **Solve Once**: Capture requirements properly first time
- **System Design**: Systematic approach over ad-hoc development
- **Continuous Learning**: Update protocol based on project outcomes
- **Documentation-First**: Always update requirements when decisions change

## TDD Scope & Exemptions

### REQUIRES TDD (Mandatory)
✅ New tools, agents, features
✅ Bug fixes to existing code
✅ Database schema changes
✅ API modifications
✅ Data pipeline changes
✅ Integration work

### EXEMPT FROM TDD
❌ Documentation-only changes (no code logic)
❌ Configuration-only changes (no code logic)
❌ README/markdown updates
❌ Comment-only changes

### Grey Areas (Use Judgment)
⚠️ **Small typo fixes in code**: Generally exempt, but if touching critical logic → TDD
⚠️ **Config with logic**: If config changes affect behavior → TDD required

---
*Last Updated: 2025-11-26*
*Status: MANDATORY Protocol - Enforced for ALL Development*
*Agent Pairing: Domain Specialist + SRE Principal Engineer Agent (ALWAYS)*
*Agent Continuity: Explicit reload commands + incremental progress saving (ALWAYS)*
*Database Sync: Phase 5 registration + sync mandatory before production (PHASE 179)*
*Integration & Validation: Phase 3.5 integration tests + Phase 6 production validation (PHASE 193)*