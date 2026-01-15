# Dashboard Remediation Project - Systematic SRE Approach

**Date Started**: 2025-10-17
**Status**: STARTING - Phase A
**Agent**: SRE Principal Engineer Agent (REQUIRED - DO NOT PROCEED WITHOUT LOADING)
**Assessment**: [DASHBOARD_SRE_ASSESSMENT.md](DASHBOARD_SRE_ASSESSMENT.md)

---

## 🚨 CRITICAL: Agent Loading Protocol

### **MANDATORY BEFORE ANY WORK**

```bash
# ALWAYS load SRE agent first - NO EXCEPTIONS
load the sre agent
```

**File Location**: `/Users/YOUR_USERNAME/git/maia/claude/agents/sre_principal_engineer_agent.md`

**Why This Matters**: SRE systematic approach ensures production-grade reliability

---

## 📋 Project Overview

**Objective**: Fix 9/11 broken dashboards using systematic SRE methodology

**Current State**: 18% operational (2/11 dashboards working)
**Target State**: 100% operational (11/11 dashboards working)

**Timeline**: 8-11 hours total across 3 phases

---

## 🎯 Three-Phase Approach

### **Phase A: Safety Net** (1-2 hours) 🔴 **CURRENT PHASE**
**Priority**: CRITICAL - Build before touching production dashboards

**Deliverable**: Automated dashboard test suite
- File existence checks
- Startup health tests (< 5 second timeout)
- Port availability validation
- Dependency checks
- Health endpoint verification

**Outcome**: Data-driven baseline, regression prevention

**Status**: ⏳ STARTING NOW

---

### **Phase B: Observability** (2-3 hours)
**Priority**: HIGH - Make problems visible

**Deliverable**: Standardized health endpoints
- Add `/health` to 9 dashboards (using hook_performance_dashboard.py as template)
- Add `/ready` for readiness checks
- Implement dependency validation
- Update registry with health paths

**Outcome**: Real-time dashboard monitoring, immediate failure visibility

**Status**: ⏳ PENDING (after Phase A)

---

### **Phase C: Remediation** (4-6 hours)
**Priority**: MEDIUM - Fix broken dashboards

**Deliverable**: All 11 dashboards operational

**Priority Order**:
1. ServiceDesk Operations (Port 8065) - High business value
2. Security Intelligence (Port 8061) - Security critical
3. DORA Metrics (Port 8057) - Engineering metrics
4. Others by usage

**Outcome**: 100% operational dashboard ecosystem

**Status**: ⏳ PENDING (after Phase B)

---

## 📊 Current Dashboard Status

### ✅ Working (2/11 - 18%)
- Hook Performance Dashboard (8067) - SRE-grade with `/api/health`
- Agent Performance Dashboard (8066) - Operational

### ⚠️ Broken (9/11 - 82%)

| Dashboard | Port | Issue | Priority |
|-----------|------|-------|----------|
| ServiceDesk Operations | 8065 | Startup timeout | 🔴 P0 |
| Security Intelligence | 8061 | Startup timeout | 🔴 P0 |
| EIA Executive | 8052 | Missing DB: eia_orchestrator.db | 🟠 P1 |
| Security Operations | 8058 | Not tested | 🟠 P1 |
| DORA Metrics | 8057 | Not tested | 🟠 P1 |
| Team Intelligence | 8050 | Not tested | 🟡 P2 |
| AI Business Intel | 8054 | Not tested | 🟡 P2 |
| Insights Generator | 8055 | Not tested | 🟡 P2 |
| Executive Redesigned | 8059 | Not tested | 🟡 P2 |

---

## 🔧 Phase A: Safety Net - Implementation Plan

### Task 1: Create Automated Test Suite (45 min)

**File**: `claude/tests/test_all_dashboards.sh`

**Test Categories**:

1. **File Existence Check** (5 min)
   ```bash
   for dashboard in $(sqlite3 dashboard_registry.db "SELECT file_path FROM dashboards"); do
     test -f "$dashboard" || echo "MISSING: $dashboard"
   done
   ```

2. **Startup Health Test** (15 min)
   ```bash
   # Test each dashboard starts within 5 seconds
   timeout 5 python3 $dashboard &
   sleep 2
   curl -s http://127.0.0.1:$port/health
   ```

3. **Port Availability Check** (10 min)
   ```bash
   # Verify no port conflicts
   lsof -i :$port
   ```

4. **Dependency Validation** (10 min)
   ```bash
   # Check for required databases
   grep -o "[a-z_]*\.db" $dashboard | while read db; do
     test -f "$db" || echo "Missing: $db"
   done
   ```

5. **Health Endpoint Test** (5 min)
   ```bash
   # Validate health endpoint returns JSON
   curl -s http://127.0.0.1:$port/health | jq .
   ```

**Expected Results**:
- 2 dashboards: PASS all tests
- 9 dashboards: FAIL startup or health endpoint tests
- Clear data on what's broken

---

### Task 2: Run Baseline Tests (15 min)

**Execute**:
```bash
bash claude/tests/test_all_dashboards.sh > dashboard_test_baseline.txt
```

**Capture**:
- Startup times (P50/P95/P99)
- Failure modes
- Missing dependencies
- Port conflicts

---

### Task 3: Create Test Database (15 min)

**File**: `claude/data/dashboard_test_results.db`

**Schema**:
```sql
CREATE TABLE test_runs (
  id INTEGER PRIMARY KEY,
  timestamp TEXT,
  dashboard_name TEXT,
  test_type TEXT,
  result TEXT,
  latency_ms INTEGER,
  error_message TEXT
);
```

**Purpose**: Track improvement over time, detect regressions

---

### Task 4: Git Commit Test Suite (15 min)

**Commit**:
```bash
git add claude/tests/test_all_dashboards.sh
git add claude/data/dashboard_test_results.db
git commit -m "Dashboard Remediation Phase A: Automated Test Suite"
```

---

## 📈 Success Metrics

### Phase A Targets
- ✅ Test suite operational
- ✅ Baseline data captured for 11 dashboards
- ✅ Regression prevention active
- ✅ < 2 minute test execution time

### Phase B Targets
- ✅ 9 dashboards with `/health` endpoints
- ✅ 100% health check coverage
- ✅ Unified hub can monitor all dashboards

### Phase C Targets
- ✅ 100% dashboards operational (11/11)
- ✅ P95 startup time < 3 seconds
- ✅ 99.5% uptime SLO defined
- ✅ Zero critical issues remaining

---

## 🔗 Related Documentation

- **SRE Assessment**: `claude/data/DASHBOARD_SRE_ASSESSMENT.md` (comprehensive 400+ line analysis)
- **Phase 127 Project**: `claude/data/PHASE_127_ARCHITECTURE_REVIEW_PROJECT.md` (methodology reference)
- **SRE Agent**: `claude/agents/sre_principal_engineer_agent.md` (MUST load before work)
- **Hook Performance Dashboard**: `claude/tools/sre/hook_performance_dashboard.py` (template for health endpoints)

---

## 🔄 Workflow Instructions

### Starting Work (Fresh Session)

1. **Load SRE Agent** (MANDATORY)
   ```
   load the sre agent
   ```

2. **Review Project State**
   ```
   read /Users/YOUR_USERNAME/git/maia/claude/data/DASHBOARD_REMEDIATION_PROJECT.md
   ```

3. **Check Current Phase**
   - Look at "Current Phase" section
   - Identify next pending task
   - Review expected outcomes

4. **Execute Task**
   - Follow SRE systematic approach
   - Measure before/after metrics
   - Document results in this file

### Resuming After Compaction

1. **FIRST**: Load SRE agent
   ```
   load the sre agent
   ```

2. **SECOND**: Reload project context
   ```
   resume dashboard remediation project
   ```

3. **THIRD**: Verify current phase
   - Check "Current Phase" in this file
   - Ask user: "Should I continue with [next task]?"

---

## 📝 Progress Tracking

### ✅ Completed Work

**Phase A: Safety Net** - ⏳ IN PROGRESS
- [ ] Task 1: Create automated test suite
- [ ] Task 2: Run baseline tests
- [ ] Task 3: Create test database
- [ ] Task 4: Git commit test suite

**Phase B: Observability** - ⏳ PENDING

**Phase C: Remediation** - ⏳ PENDING

---

## 🎓 Lessons Learned (To Be Updated)

### From Phase 127
1. **Safety nets first**: Tests prevent breaking working systems
2. **Systematic > ad-hoc**: Methodical approach catches edge cases
3. **Measure everything**: Data-driven decisions prevent guesswork
4. **Document thoroughly**: Future you will thank present you

### From Dashboard Remediation (TBD)
- To be added as we learn

---

**Last Updated**: 2025-10-17
**Current Phase**: Phase A - Safety Net (Task 1 starting)
**Next Action**: Create `test_all_dashboards.sh` automated test suite
**Expected Completion**: Phase A (1-2 hours), Full project (8-11 hours)
**Status**: PROJECT STARTED - Phase A in progress
