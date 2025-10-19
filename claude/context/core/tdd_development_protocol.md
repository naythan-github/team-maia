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

### Phase 4: Implementation
1. Standard TDD red-green-refactor cycle
2. Make tests pass one at a time
3. Regular verification against requirements.md
4. Update documentation if requirements evolve

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

**Maia's Automatic Workflow**:
1. Detect development task (code changes, new tools, bug fixes, schema changes)
2. **Agent Pairing**: Select domain specialist + SRE (announce selection)
3. **Phase 1**: Initiate requirements discovery questions
4. **Phase 2-4**: Execute TDD workflow with both agents

### During Development
- Start each session: "Let me read the requirements file"
- After design decisions: "Updating requirements with our decisions..."
- Before implementing: "Let me verify against our test suite"
- Regular checkpoint: "Are we still aligned with requirements?"

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
```

## Success Metrics
- Zero requirement misses after implementation
- All initial tests remain valid (no deletion due to misunderstanding)
- Requirements document stays current with implementation
- No "oh, I forgot to mention" moments after test creation

## Quality Gates
1. **Requirements Gate**: No tests until "requirements complete" confirmation
2. **Test Gate**: No implementation until all tests written
3. **Implementation Gate**: No feature complete until all tests pass
4. **Documentation Gate**: Requirements.md updated with any changes

## Risk Mitigation
- Active probing during discovery phase
- Multiple concrete examples required
- Explicit confirmation checkpoints
- Regular requirements verification
- Test-first discipline enforcement

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
*Last Updated: 2025-10-19*
*Status: MANDATORY Protocol - Enforced for ALL Development*
*Agent Pairing: Domain Specialist + SRE Principal Engineer Agent (ALWAYS)*