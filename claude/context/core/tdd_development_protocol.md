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

## Quality Gates
1. **Requirements Gate**: No tests until "requirements complete" confirmation
2. **Test Gate**: No implementation until all tests written
3. **Implementation Gate**: No feature complete until all tests pass
4. **Documentation Gate**: Requirements.md updated with any changes
5. **Progress Gate**: Progress saved after EACH phase (not just at end)
6. **Agent Continuity Gate**: Agent identity confirmed at phase transitions

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
*Last Updated: 2025-11-07*
*Status: MANDATORY Protocol - Enforced for ALL Development*
*Agent Pairing: Domain Specialist + SRE Principal Engineer Agent (ALWAYS)*
*Agent Continuity: Explicit reload commands + incremental progress saving (ALWAYS)*