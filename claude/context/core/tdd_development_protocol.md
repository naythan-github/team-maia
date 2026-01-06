# TDD Protocol v2.4

## Enforcement
**STATUS**: MANDATORY | **HOOK**: Pre-commit blocks violations (Phase 217)
**AGENT PAIRING**: Domain Specialist + SRE Principal Engineer (ALWAYS)
**BYPASS**: `git commit --no-verify` → log in `claude/data/TDD_EXEMPTIONS.md`

---

## Workflow State Machine

```
P0:Architecture → P1:Requirements → P2:Documentation → P3:Tests → P3.5:Integration → P4:Implementation → P5:Execution → P6:Validation → P6.5:Completeness
     ↓ GATE           ↓ GATE            ↓ GATE          ↓ GATE       ↓ GATE            ↓ GATE           ↓ GATE         ↓ GATE            ↓ GATE
  Read ARCH.md    "requirements     Approval of      All tests    Integration      All tests        DBs synced     SRE sign-off      All docs
  + ADRs          complete"         requirements.md   written      plan approved    passing          + registered                     updated
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

### P3: Test Design - Real Failure Data Priority ⭐ NEW v2.4

**PRIORITY ORDER**:
1. **Production Failure Data First** - Check for existing bug reports, production incidents, PIRs
2. **Exact Failure Reproduction** - Test 1 uses EXACT data from real failure (not hypothetical)
3. **Edge Cases Second** - Hypothetical scenarios = Test 2+

**RATIONALE** (Phase 230 Learning):
- Real failures > hypothetical edge cases
- Example: PIR-OCULUS-2025-01 ben@oculus.info error → Test 1 with exact data → 8/8 tests passing
- **Key Insight**: Testing against actual production errors prevents assumption-based bugs

**ACTIONS**:
- Framework setup
- Check incident database/PIRs for real failure data
- `test_requirements.py` with Test 1 = real failure (if available)
- Failing tests for EACH requirement

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

### P6.5: Completeness Review ⭐ NEW v2.4

**PURPOSE**: Pause after technical validation to ensure holistic completeness before declaring "done"

**CHECKLIST** (ALL required):
1. **Documentation Updated**:
   - ✅ `CLAUDE.md` reflects new capabilities
   - ✅ `capability_index.md` includes new entries
   - ✅ `SYSTEM_STATE.md` phase documented (if significant work)
   - ✅ `requirements.md` reflects final implementation
   - ✅ Domain-specific docs updated (IR_PLAYBOOK.md, etc.)

2. **Integration Tests Complete**:
   - ✅ P3.5 integration tests ran successfully
   - ✅ Cross-component interactions validated
   - ✅ External dependencies tested (DBs, APIs, file I/O)

3. **Holistic Review**:
   - ✅ Does the solution solve the original problem?
   - ✅ Any missed edge cases or failure modes?
   - ✅ Clean design with no over-engineering?
   - ✅ Code follows established patterns?

4. **Capabilities DB Synced**:
   - ✅ `capabilities_registry.py scan` completed
   - ✅ `system_state_etl.py` ran if phase work
   - ✅ New tools/agents discoverable via find_capability.py

**GATE**: All 4 checklist items complete → Task can be declared "done"

---

## Post-Incident TDD Workflow ⭐ NEW v2.4

**USE WHEN**: Fixing production bugs, addressing PIR findings, or resolving user-reported issues

**WORKFLOW**:
```
Incident Report → P0: Get EXACT failure data → P1: Reproduce failure → P2: Write test with exact data → P3: Verify test FAILS → P4: Implement fix → P5: Verify test PASSES → P6: Validate + Document
```

**EXAMPLE** (Phase 230 - Account Validator):
1. **Incident**: PIR-OCULUS-2025-01 - ben@oculus.info incorrectly flagged as compromised
2. **Exact Data**: Password policy failure on 2025-12-19, sign-in from US (not AU)
3. **Test 1**:
```python
def test_password_policy_failure_not_compromise():
    # EXACT data from PIR-OCULUS-2025-01
    account = {"email": "ben@oculus.info", "password_status": "PASSWORD_POLICY_FAILURE", ...}
    result = validate_account(account)
    assert result.status == "NOT_COMPROMISED"
```
4. **Outcome**: Test fails → Fix validator → Test passes → 8/8 tests passing

**KEY PRINCIPLE**: Real failure data beats hypothetical scenarios - always use exact production data for Test 1

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
- P6.5: Completeness review, documentation verification

---

## Quality Gates (13 Total) ⭐ +1 NEW v2.4

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
| 13 | Completeness Gate | "Done" until docs/integration/holistic review complete |

---

## Feature Tracker CLI - Structural Enforcement ⭐ EXPANDED v2.4

**WHY STRUCTURAL ENFORCEMENT?**
- **Problem**: Documentation-based TDD easily ignored, state lost during context compaction
- **Solution**: JSON feature lists persist through compaction, provide objective progress tracking
- **Benefit**: Can't be ignored (pre-commit blocks), survives context loss, prevents infinite retry loops

**COMMANDS**:
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

**INTEGRATION**:
- `swarm_auto_loader.py` injects TDD context into session state
- `tdd_precommit_hook.py` blocks commits when features failing
- JSON persists in `claude/data/project_status/active/{PROJECT}_features.json`

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

## v2.4 Changelog (2026-01-06)

**ADDED**:
- P3: Real Failure Data Priority (Phase 230 learning - production failures > hypothetical)
- Post-Incident TDD Workflow (exact failure reproduction pattern)
- P6.5: Completeness Review phase (pause before "done" declaration)
- Gate 13: Completeness Gate (docs/integration/holistic review)
- Feature Tracker: Expanded rationale with structural enforcement explanation

**ENHANCED**:
- Workflow state machine updated with P6.5 and Gate 13
- SRE Lifecycle includes P6.5 completeness review
- Feature Tracker section explains WHY structural > documentation

**METRICS**:
- Gates: 12 → 13 (+1)
- Phases: 7 → 8 (+P6.5)
- Lines: ~200 → ~260 (+30% for critical learnings, acceptable decompression)

---

*v2.4 | ~260 lines | 13 gates | Real failure data + Completeness review integrated*
