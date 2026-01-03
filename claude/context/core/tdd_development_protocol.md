# TDD Protocol v2.3 (Compressed Template)

## Enforcement
**STATUS**: MANDATORY | **HOOK**: Pre-commit blocks violations (Phase 217)
**AGENT PAIRING**: Domain Specialist + SRE Principal Engineer (ALWAYS)
**BYPASS**: `git commit --no-verify` → log in `claude/data/TDD_EXEMPTIONS.md`

---

## Workflow State Machine

```
P0:Architecture → P1:Requirements → P2:Documentation → P3:Tests → P3.5:Integration → P4:Implementation → P5:Execution → P6:Validation
     ↓ GATE           ↓ GATE            ↓ GATE          ↓ GATE       ↓ GATE            ↓ GATE           ↓ GATE         ↓ GATE
  Read ARCH.md    "requirements     Approval of      All tests    Integration      All tests        DBs synced     SRE sign-off
  + ADRs          complete"         requirements.md   written      plan approved    passing          + registered
```

---

## Phase Details

### P0: Architecture Review
**CHECK**: `PROJECT/ARCHITECTURE.md` exists? → Read it | `PROJECT/ADRs/` → Review decisions | `active_deployments.md` → Avoid conflicts
**GATE**: Understand current architecture before requirements

### P1: Requirements Discovery (NO CODE/TESTS)
**ACTIONS**: Core purpose | Functional reqs (I/O/Transform/Errors) | 3+ examples | Non-functional | Explicit confirmation
**KEY PHRASE**: "requirements complete" = proceed signal
**GATE**: No tests until explicit confirmation

### P2: Requirements Documentation
**OUTPUT**: `requirements.md` with acceptance criteria + examples
**GATE**: Approval before test design

### P3: Test Design
**ACTIONS**: Framework setup | `test_requirements.py` | Failing tests for EACH requirement
**GATE**: No implementation until all tests written

### P3.5: Integration Test Design
**CATEGORIES**: Cross-component | External dependencies | State management
**SRE REVIEW**: Failure modes, observability coverage
**GATE**: No implementation until integration plan approved

### P4: Implementation
**CYCLE**: Red → Green → Refactor | Regular verification against requirements.md

### P5: Execution & Registration
**UNIT**: All P3 tests passing, >80% coverage
**INTEGRATION**: All P3.5 tests passing
**REGISTER** (if new tools/agents):
```bash
python3 claude/tools/sre/capabilities_registry.py scan
python3 claude/tools/sre/system_state_etl.py --recent 10
```
**GATE**: Unit + Integration tests passing, DBs synced

### P6: Post-Implementation Validation
**PERFORMANCE**: 10x load, P95/P99 meets SLOs, <70% CPU/mem, no N+1
**RESILIENCE**: Circuit breakers, fallbacks, graceful degradation, retries
**OBSERVABILITY**: Structured logs, RED metrics, traces, dashboard
**SMOKE**: E2E happy path, health checks, critical journeys
**CONTRACT** (if API): Schema validation, backward compat
**GATE**: All categories passing → SRE production sign-off

---

## Refactoring Workflow (Phase 230)

**R1: TDD Foundation**
Write tests → Red → Fix → Green → `python3 -m py_compile <file>`

**R2: Smoke Tests (MANDATORY)**
| Test | Command |
|------|---------|
| Import | `from module import X` |
| Instantiation | `obj = Class()` |
| Method existence | `hasattr(obj, 'method')` |
| Behavior | `result = obj.method(input)` |

**R3: Tool Execution**
```bash
python3 claude/tools/sre/tool.py --help  # or --dashboard
```

**GATE**: Syntax + Import + Instantiation + Methods + Behavior all pass

---

## Auto-Triggers (TDD Required)

**ALWAYS**: Tools (`claude/tools/*.py`) | Agents (`claude/agents/*.md`) | Hooks | Schema changes | API mods | Bug fixes | Integration work

**EXEMPT**: Documentation-only | Config-only (no logic) | README | Comments

**USER OVERRIDE**: "skip TDD" (rare, emergency only)

---

## Agent Pairing Protocol

**FORMULA**: Detect task type → Select Domain Specialist → Pair with SRE

| Domain | Specialist Agent |
|--------|------------------|
| ServiceDesk | Service Desk Manager |
| Security | Security Specialist |
| Cloud | Azure Solutions Architect |
| Data | Data Analyst |
| Recruitment | Technical Recruitment |

**SRE LIFECYCLE**:
- P1: Define reliability reqs (logging, circuit breakers, SLOs)
- P2-4: Review failure modes, validate error handling
- P5-6: Production readiness, performance, security

---

## Quality Gates (12 Total)

| # | Gate | Blocks |
|---|------|--------|
| 1 | Requirements Gate | Tests until "requirements complete" |
| 2 | Test Gate | Implementation until tests written |
| 3 | Implementation Gate | Complete until tests pass |
| 4 | Documentation Gate | Complete until requirements.md current |
| 5 | Progress Gate | Complete until progress saved |
| 6 | Agent Continuity Gate | Next phase until identity confirmed |
| 7 | Registration Gate | Production until capabilities.db updated |
| 8 | Sync Gate | Production until DBs synced |
| 9 | Integration Test Design Gate | Implementation until P3.5 approved |
| 10 | Integration Execution Gate | Production until integration tests pass |
| 11 | Production Readiness Gate | Deploy until P6 validation pass |
| 12 | Refactoring Smoke Test Gate | Complete until smoke tests pass |

---

## Feature Tracker CLI

```bash
# Structural TDD enforcement (Phase 221)
python3 claude/tools/sre/feature_tracker.py init <project>
python3 claude/tools/sre/feature_tracker.py add <project> "Feature" --priority 1 --verification "Test 1" "Test 2"
python3 claude/tools/sre/feature_tracker.py next <project>
python3 claude/tools/sre/feature_tracker.py update <project> F001 --passes|--fails
python3 claude/tools/sre/feature_tracker.py status <project>
python3 claude/tools/sre/feature_tracker.py reset <project> F001  # After fixing blocked feature
```

**CIRCUIT BREAKER**: 5 failed attempts → feature blocked → requires `reset` after fix

---

## File Structure

```
project/
├── requirements.md           # Living requirements
├── test_requirements.py      # Tests for all requirements
└── implementation.py         # Code

claude/data/project_status/active/
└── {PROJECT}_progress.md     # Incremental tracking
└── {PROJECT}_features.json   # Feature tracker state
```

---

## Key Phrases

| Phrase | Action |
|--------|--------|
| "requirements complete" | Proceed to P3 (tests) |
| "check requirements" | Re-read requirements.md |
| "update requirements" | Capture new decisions |
| "show me the tests" | Validate coverage |

---

## Session Continuity

**AGENT RELOAD**: Include in all plans: `load sre_principal_engineer_agent`
**PROGRESS SAVE**: After EACH phase → `{PROJECT}_progress.md`
**RECOVERY**: Read progress.md → Reload agent → Continue from documented step

---

*v2.3 | 595→~200 lines (~66% reduction) | All 12 gates preserved*
