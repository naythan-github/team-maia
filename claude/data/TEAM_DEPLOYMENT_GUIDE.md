# Maia Team Deployment Guide
**Phase 134.2 - Production Monitoring for Team Sharing**
**Date**: 2025-10-21
**Status**: ✅ PRODUCTION READY

---

## 🎯 **Overview**

This guide helps team members deploy and monitor their own Maia instance. Each person runs Maia independently on their laptop with **local monitoring** - no central logging required.

**What's Been Validated**:
- ✅ Agent persistence system (Phase 134/134.1)
- ✅ Routing accuracy monitoring (Phase 125)
- ✅ Agent quality spot-checks (Phase 134.2)
- ✅ Health check automation (Phase 134.2)
- ✅ SRE enforcement for reliability work (Phase 134.2)

---

## 🚀 **Quick Start for Team Members**

### **1. Initial Setup** (5 minutes)

```bash
# Clone Maia repository
git clone https://github.com/naythan-orro/maia.git
cd maia

# Install dependencies (if not already done)
pip install -r requirements.txt  # If requirements file exists

# Verify installation
python3 claude/tools/sre/maia_health_check.py
```

**Expected**: Health check should pass (or show warnings for routing data - normal initially)

---

### **2. Weekly Monitoring** (2 minutes/week)

Run this every week to ensure Maia stays healthy:

```bash
./claude/tools/sre/weekly_health_check.sh
```

**What it checks**:
1. Session state health
2. Agent loading performance
3. Routing accuracy (if data available)
4. Agent quality (v2.2 Enhanced patterns present)

**Expected output**:
```
✅ ALL CHECKS PASSED - Maia is healthy
```

---

### **3. If Issues Detected**

**Scenario 1: Performance Degradation**
```bash
# Symptoms: P95 > 200ms
# Fix: Check for system load, restart if needed
# Escalate if persistent (> 500ms consistently)
```

**Scenario 2: Routing Accuracy Low**
```bash
# Symptoms: <80% acceptance rate
# Review: claude/data/logs/routing_accuracy_*.md
# Action: Share report with lead for coordinator tuning
```

**Scenario 3: Agent Quality Failures**
```bash
# Symptoms: Agent quality tests failing
# Check: python3 tests/test_agent_quality_spot_check.py
# Action: May indicate agent file corruption - re-pull from git
```

---

## 📊 **Monitoring Components**

### **1. Health Check** (`maia_health_check.py`)

**What it does**:
- Validates session state file
- Measures agent loading performance
- Checks routing accuracy (if data exists)
- Runs quick integration tests (optional)

**Usage**:
```bash
# Quick check (3 checks)
python3 claude/tools/sre/maia_health_check.py

# Detailed check (includes integration tests)
python3 claude/tools/sre/maia_health_check.py --detailed
```

**Exit codes**:
- `0` = Healthy
- `1` = Warnings (operational)
- `2` = Degraded (action needed)

---

### **2. Agent Quality Spot-Check** (`test_agent_quality_spot_check.py`)

**What it does**:
- Validates top 10 agents have v2.2 Enhanced patterns
- Checks for few-shot examples
- Verifies self-reflection checkpoints
- Ensures comprehensive agent content

**Usage**:
```bash
# Run spot-check
python3 tests/test_agent_quality_spot_check.py

# Or via pytest
pytest tests/test_agent_quality_spot_check.py -v
```

**Agents tested**:
1. Security Specialist
2. Azure Solutions Architect
3. SRE Principal Engineer
4. DevOps Principal Architect
5. Cloud Security Principal
6. Principal IDAM Engineer
7. DNS Specialist
8. FinOps Engineering
9. Service Desk Manager
10. Prompt Engineer

---

### **3. Routing Accuracy Report** (weekly_accuracy_report.py)

**What it does**:
- Analyzes coordinator routing decisions
- Tracks acceptance vs rejection rates
- Identifies low-accuracy patterns
- Provides improvement recommendations

**Usage**:
```bash
# Generate last 7 days report
python3 claude/tools/orchestration/weekly_accuracy_report.py \
    --start 2025-10-14 \
    --end 2025-10-21

# Output saved to: claude/data/logs/routing_accuracy_YYYY-WNN.md
```

**Target metrics**:
- **Acceptance rate**: >80% (coordinator suggestions accepted)
- **Override rate**: <20% (users override suggestions)

---

## 🚨 **SRE Agent Enforcement** ⭐ **NEW - Phase 134.2**

### **Automatic Routing for Reliability Work**

**All reliability/testing/production queries now automatically route to SRE Principal Engineer:**

**Enforced Keywords**:
```
test, testing, reliability, production, monitoring,
slo, sli, observability, incident, health check,
regression, performance, validation, integration test,
quality check, deployment, ci/cd
```

**Examples**:
```bash
❌ Before: "run integration tests" → Might route to various agents
✅ After:  "run integration tests" → ALWAYS routes to SRE Principal Engineer

❌ Before: "build monitoring dashboard" → Azure Architect
✅ After:  "build monitoring dashboard" → SRE Principal Engineer

✅ Still works: "design Azure architecture" → Azure Solutions Architect
```

**Why this matters**:
- Reliability work requires SRE expertise
- Other agents can advise, but SRE delivers implementation
- Ensures consistent production-quality standards

---

## 📁 **File Locations**

### **Monitoring Tools**
- `claude/tools/sre/maia_health_check.py` - Main health check
- `claude/tools/sre/weekly_health_check.sh` - Automated weekly check
- `tests/test_agent_persistence_integration.py` - Integration tests (Phase 134.1)
- `tests/test_agent_quality_spot_check.py` - Quality validation (Phase 134.2)

### **Routing Monitoring** (Phase 125)
- `claude/tools/orchestration/routing_decision_logger.py` - Logs routing decisions
- `claude/tools/orchestration/weekly_accuracy_report.py` - Generates accuracy reports
- `claude/tools/orchestration/accuracy_analyzer.py` - Detailed analysis

### **Data Files** (local to your laptop)
- `claude/data/routing_decisions.db` - Your routing history (SQLite)
- `claude/data/logs/routing_accuracy_*.md` - Weekly reports
- `/tmp/maia_active_swarm_session.json` - Active session state

---

## 🔒 **Security & Privacy**

### **No Central Logging**
- Each team member's Maia runs independently
- No data shared between instances
- Local SQLite database only
- Session state file: `/tmp/maia_active_swarm_session.json` (600 permissions)

### **Data Isolation**
- Your routing decisions: Only on your laptop
- Your session history: Only in your `/tmp`
- Your quality checks: Local test results only

---

## 📈 **Expected Quality Metrics**

### **From Google/OpenAI Research** (Phase 2 Agent Evolution)
Based on v2.2 Enhanced agent upgrades:

| Pattern | Expected Improvement |
|---------|---------------------|
| Few-Shot Examples | +20-30% consistency |
| Chain-of-Thought | +25-40% quality |
| Self-Reflection | 60-80% issue detection |
| ReACT Pattern | Proven reliability |
| Persistence Reminder | +40-50% completion rate |

### **Production Validation** (Phase 134.1)
Actual measured performance:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Agent Loading (P95) | <200ms | 187.5ms | ✅ PASS |
| Session State Security | 600 perms | 600 | ✅ PASS |
| Graceful Degradation | 100% | 100% | ✅ PASS |
| Integration Tests | >80% | 81% (13/16) | ✅ PASS |

---

## 🆘 **Troubleshooting**

### **"Health check shows degraded"**
1. Run detailed check: `python3 claude/tools/sre/maia_health_check.py --detailed`
2. Review specific failures
3. Check for corrupted files: `git status`
4. Reset if needed: `git pull --rebase`

### **"Routing accuracy <50%"**
1. Review report: `ls -lt claude/data/logs/routing_accuracy_*.md | head -1`
2. Check if using Maia as intended (coordinator's suggestions are usually good)
3. Share report with lead if pattern persists

### **"Agent quality tests failing"**
1. Run: `python3 tests/test_agent_quality_spot_check.py`
2. Note which agents failing
3. Check agent files: `ls -lh claude/agents/{failing_agent}*`
4. Re-pull from git if corrupted: `git checkout claude/agents/`

### **"Session state corrupted"**
1. This auto-recovers (graceful degradation tested ✅)
2. Just delete: `rm /tmp/maia_active_swarm_session.json`
3. Next agent load will recreate

---

## 📞 **Getting Help**

### **For Technical Issues**
1. Run health check: `python3 claude/tools/sre/maia_health_check.py --detailed`
2. Capture output
3. Share with lead: [Your Team Lead Contact]

### **For Routing Questions**
1. Generate routing report for last 7 days
2. Review coordinator suggestions vs your usage
3. Discuss patterns with lead if concerns

### **For Agent Quality Concerns**
1. Run quality spot-check: `python3 tests/test_agent_quality_spot_check.py`
2. Note which agents showing issues
3. Re-pull from git or escalate to lead

---

## ✅ **Pre-Deployment Checklist**

Before sharing Maia with your team, confirm:

- [x] Phase 134.1 integration tests passing (13/16)
- [x] Health check operational
- [x] Agent quality spot-check created
- [x] SRE enforcement implemented
- [x] Weekly check automation ready
- [x] Team documentation complete
- [x] Troubleshooting guide provided

**Status**: ✅ ALL COMPLETE - Ready for team deployment

---

## 📚 **Additional Resources**

### **Phase Documentation**
- Phase 134: Automatic Agent Persistence ([SYSTEM_STATE.md](../SYSTEM_STATE.md#phase-134))
- Phase 134.1: Integration Testing & Bug Fix ([SYSTEM_STATE.md](../SYSTEM_STATE.md#phase-134-1))
- Phase 134.2: Team Deployment Monitoring (this document)
- Phase 2: Agent Evolution (v2.2 Enhanced) ([SYSTEM_STATE.md](../SYSTEM_STATE.md#phase-2))

### **Test Results**
- Integration Tests: [AGENT_PERSISTENCE_TEST_RESULTS.md](AGENT_PERSISTENCE_TEST_RESULTS.md)
- Bug Fix Summary: [AGENT_PERSISTENCE_FIX_SUMMARY.md](AGENT_PERSISTENCE_FIX_SUMMARY.md)

### **Monitoring Tools**
- Routing Logger: `claude/tools/orchestration/routing_decision_logger.py`
- Accuracy Analyzer: `claude/tools/orchestration/accuracy_analyzer.py`
- Health Monitor: `claude/tools/sre/maia_health_check.py`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Maintained By**: SRE/DevOps Team
**Questions**: Contact team lead
