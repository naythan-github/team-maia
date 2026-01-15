# Git Repository Governance Project
## Production-Grade Multi-User Repository Protection

**Project ID**: REPO-GOV-001
**Created**: 2025-10-27
**Status**: Planning → Implementation Ready
**Owner**: Naythan Dawe
**Agents**: DevOps Principal Architect + SRE Principal Engineer

---

## Executive Summary

**Problem**: Maia repository built for personal use needs multi-user collaboration with protection against accidental core degradation.

**Solution**: Enhanced Monorepo with automated protection layers (CODEOWNERS + CI + Performance Baselines + Emergency Recovery).

**Impact**:
- 🔒 99.9%+ core protection success rate (no unauthorized changes)
- 🚀 Team productivity maintained (standard PR workflow)
- ⚡ <5 min emergency recovery MTTR
- 📊 Automated quality gates (zero manual enforcement)

**Timeline**: 2-3 weeks (phased implementation with team training)

**Investment**: ~20-30 hours implementation + 4 hours/quarter maintenance

---

## Problem Statement

### Current State
- **Repository**: 200+ tools, 49 agents, personal use case
- **Challenge**: File system cluttered, needs team collaboration
- **Risk**: Breaking changes to core components may go unnoticed
- **Constraint**: Want Git-based sharing with protection

### Stakeholders
1. **You (Owner)**: Personal use cases, core system integrity, avoid bottlenecks
2. **Team Members**: Collaborative tooling, safe contribution environment
3. **Future Contributors**: Clear boundaries, efficient onboarding

### Success Criteria
- ✅ Core Maia protected from breaking changes (automated enforcement)
- ✅ Team can contribute safely (clear guidelines + automated validation)
- ✅ Changes reviewed before merge (PR workflow + CODEOWNERS)
- ✅ Degradation detected automatically (performance baselines + CI tests)
- ✅ Fast recovery if core breaks (<5 min emergency rollback)

---

## Architecture Decision

### **Selected Solution: Enhanced Monorepo (Option A)**

**Rationale**:
- Industry-proven (Google, Meta, Microsoft use this pattern)
- Automated enforcement (minimal manual overhead)
- Balanced protection (core protected, team empowered)
- GitHub-native (no custom tooling required)
- Scalable (2-20 people)

**Rejected Alternatives**:
- ❌ **Multi-Repo + Submodules**: 30% team toil on Git complexity
- ❌ **Pre-Commit Hooks Only**: Bypassable, weak enforcement
- ❌ **Fork Model**: You become bottleneck for ALL changes (not just core)

---

## Technical Architecture

### Repository Structure

```
maia/
├── claude/
│   ├── context/core/          # 🔒 PROTECTED (owner approval required)
│   │   ├── identity.md
│   │   ├── systematic_thinking_protocol.md
│   │   ├── model_selection_strategy.md
│   │   └── capability_index.md
│   │
│   ├── agents/                # 🔒 PROTECTED (owner approval required)
│   │   ├── sre_principal_engineer_agent.md
│   │   ├── devops_principal_architect_agent.md
│   │   └── ... (49 agents)
│   │
│   ├── tools/                 # 🔓 TEAM WRITABLE (automated review)
│   │   ├── sre/
│   │   ├── productivity/
│   │   └── servicedesk/
│   │
│   ├── extensions/            # 🔓 TEAM WRITABLE (no review needed)
│   │   ├── experimental/
│   │   └── plugins/
│   │
│   └── projects/              # 🔓 USER-OWNED (namespace isolation)
│       ├── user1/
│       └── user2/
│
├── CODEOWNERS                 # Protection rules
├── .github/
│   └── workflows/
│       ├── core-protection.yml         # Layer 2: CI quality gates
│       ├── performance-baseline.yml    # Layer 3: Regression detection
│       ├── ci-health-monitor.yml       # Monitoring layer
│       ├── core-change-alert.yml       # Alerting layer
│       └── emergency-rollback.yml      # Recovery layer
│
├── claude/tools/sre/
│   ├── validate_core_schema.py         # Schema validation
│   ├── performance_baseline.py         # Performance regression detector
│   └── emergency_rollback_runbook.md   # Recovery procedures
│
└── docs/
    ├── CONTRIBUTING.md                 # Team contribution guide
    ├── CORE_PROTECTION_GUIDE.md        # Protection system overview
    └── EMERGENCY_PROCEDURES.md         # Incident response runbook
```

---

## Protection Layers (Defense in Depth)

### **Layer 1: CODEOWNERS (GitHub-Native Enforcement)**

**Purpose**: Automatic reviewer assignment + merge blocking

**File**: `CODEOWNERS`
```
# Core Maia - Owner approval required
/claude/context/core/          @YOUR_USERNAME
/claude/agents/                @YOUR_USERNAME
/CLAUDE.md                     @YOUR_USERNAME
/SYSTEM_STATE.md               @YOUR_USERNAME

# Tools - Automated review OR owner discretion
/claude/tools/                 @maia-bot @YOUR_USERNAME

# Extensions - Anyone can contribute
/claude/extensions/            # No review required

# User Projects - No review needed
/claude/projects/*/            # User-owned namespaces
```

**Enforcement**: GitHub branch protection rules (1-2 approvals required)

---

### **Layer 2: CI Quality Gates (Automated Testing)**

**Purpose**: Block merges if core validation fails

**File**: `.github/workflows/core-protection.yml`
```yaml
name: Core Protection

on:
  pull_request:
    paths:
      - 'claude/context/core/**'
      - 'claude/agents/**'
      - 'CLAUDE.md'
      - 'SYSTEM_STATE.md'

jobs:
  core-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # 1. Schema Validation
      - name: Validate Core Schema
        run: python3 claude/tools/sre/validate_core_schema.py

      # 2. Integration Tests
      - name: Core Integration Tests
        run: python3 -m pytest claude/tests/core/ -v

      # 3. Performance Regression Check
      - name: Performance Baseline Check
        run: python3 claude/tools/sre/performance_baseline.py --check

      # 4. Security Scan
      - name: Security Validation
        run: python3 claude/tools/save_state_security_checker.py

      # 5. CODEOWNERS Integrity Check
      - name: Validate CODEOWNERS Unchanged
        run: |
          if git diff origin/main..HEAD -- CODEOWNERS | grep -q .; then
            echo "❌ CODEOWNERS modification detected - requires manual security review"
            exit 1
          fi

      # 6. Quality Gate
      - name: Block if Failures
        run: |
          if [ -f .ci_failures ]; then
            echo "❌ Core protection checks failed - see logs above"
            cat .ci_failures
            exit 1
          fi
```

**SLO**: CI execution time <5 minutes (fast feedback)

---

### **Layer 3: Performance Baselines (Degradation Detection)**

**Purpose**: Detect gradual performance regression

**File**: `claude/tools/sre/performance_baseline.py`
```python
"""
Performance Regression Detector for Core Maia Components

Baseline Metrics (established 2024-10):
- Context loading: P95 <500ms
- Agent routing: P95 <200ms
- Smart context loader: P95 <1000ms
- UFC system load: P95 <300ms

SLO: All metrics must stay within 20% of baseline
"""

import time
import statistics
import sys

# Baseline thresholds (milliseconds)
BASELINES = {
    "context_loading": 500,
    "agent_routing": 200,
    "smart_context": 1000,
    "ufc_load": 300
}

TOLERANCE = 0.20  # 20% tolerance

def benchmark_context_loading():
    """Benchmark core context loading performance."""
    times = []

    for _ in range(10):
        start = time.time()

        # Simulate context loading
        load_ufc_system()
        load_identity()
        load_capability_index()
        load_systematic_thinking()

        elapsed_ms = (time.time() - start) * 1000
        times.append(elapsed_ms)

    p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
    baseline = BASELINES["context_loading"]
    threshold = baseline * (1 + TOLERANCE)

    result = {
        "metric": "context_loading",
        "p95_ms": round(p95, 2),
        "baseline_ms": baseline,
        "threshold_ms": threshold,
        "status": "pass" if p95 <= threshold else "fail"
    }

    if result["status"] == "fail":
        print(f"❌ Performance regression detected:")
        print(f"   Context Loading P95: {p95:.2f}ms (baseline: {baseline}ms, threshold: {threshold}ms)")
        print(f"   Regression: {((p95 - baseline) / baseline * 100):.1f}%")

    return result

def benchmark_agent_routing():
    """Benchmark agent routing performance."""
    # Similar implementation for agent routing
    pass

def run_all_benchmarks():
    """Run all performance benchmarks."""
    results = []

    results.append(benchmark_context_loading())
    results.append(benchmark_agent_routing())
    results.append(benchmark_smart_context())
    results.append(benchmark_ufc_load())

    # Check for failures
    failures = [r for r in results if r["status"] == "fail"]

    if failures:
        print("\n❌ Performance regression detected - PR BLOCKED")
        print(f"   Failed benchmarks: {len(failures)}/{len(results)}")
        sys.exit(1)
    else:
        print("\n✅ All performance benchmarks passed")
        sys.exit(0)

if __name__ == "__main__":
    run_all_benchmarks()
```

**Integration**: Runs on every PR touching core files

---

### **Monitoring Layer: CI Health + Alerts**

**Purpose**: Detect enforcement system failures

**File**: `.github/workflows/ci-health-monitor.yml`
```yaml
name: CI Health Monitor

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes

jobs:
  check-ci-health:
    runs-on: ubuntu-latest
    steps:
      - name: Query CI Status
        run: |
          # Check GitHub Actions API for recent workflow runs
          # Alert if failure rate >10% in last hour
          # Alert if CI runtime >10 minutes (performance regression)

          curl -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
            "https://api.github.com/repos/${{ github.repository }}/actions/runs?status=completed&per_page=20" \
            | jq '.workflow_runs[] | select(.conclusion == "failure")'

      - name: Alert if Degraded
        if: failure()
        run: |
          # Send Slack/Teams notification
          # Create incident ticket
          echo "⚠️ CI health degraded - alerting team"
```

**File**: `.github/workflows/core-change-alert.yml`
```yaml
name: Core Change Alert

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'claude/context/core/**'
      - 'claude/agents/**'
      - 'CLAUDE.md'

jobs:
  alert-core-change:
    runs-on: ubuntu-latest
    steps:
      - name: Send Alert
        run: |
          # Slack notification to #maia-core-changes
          # Include: Author, files changed, PR link, diff summary
          # Tag: @YOUR_USERNAME for awareness

          echo "🚨 Core change detected in PR #${{ github.event.pull_request.number }}"
          echo "Author: ${{ github.event.pull_request.user.login }}"
          echo "Files: $(git diff --name-only origin/main..HEAD | grep -E 'core/|agents/')"
```

**SLO**: CI uptime >99.5% (monitored every 15 minutes)

---

### **Recovery Layer: Emergency Rollback**

**Purpose**: Fast recovery if core breaks in production

**File**: `.github/workflows/emergency-rollback.yml`
```yaml
name: Emergency Core Rollback

on:
  workflow_dispatch:
    inputs:
      target_commit:
        description: 'Commit SHA to revert to (leave empty to revert last commit)'
        required: false
      reason:
        description: 'Emergency reason (required for audit trail)'
        required: true
      alert_team:
        description: 'Send team alert?'
        type: boolean
        default: true

jobs:
  emergency-revert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for revert

      - name: Create Revert Commit
        run: |
          git config user.name "Maia Emergency Bot"
          git config user.email "bot@maia.local"

          if [ -z "${{ inputs.target_commit }}" ]; then
            # Revert last commit
            git revert --no-edit HEAD
          else
            # Revert to specific commit
            git revert --no-edit HEAD..${{ inputs.target_commit }}
          fi

          # Add emergency marker
          git commit --amend -m "EMERGENCY ROLLBACK: ${{ inputs.reason }}"
          git push origin main

      - name: Alert Team
        if: inputs.alert_team
        run: |
          # Post to Slack/Teams
          # Create incident post-mortem ticket
          echo "🚨 EMERGENCY ROLLBACK EXECUTED"
          echo "Reason: ${{ inputs.reason }}"
          echo "Reverted to: ${{ inputs.target_commit || 'HEAD~1' }}"

      - name: Create Post-Mortem Issue
        uses: actions/github-script@v6
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Post-Mortem: Emergency Rollback - ${{ inputs.reason }}`,
              body: `
              ## Incident Summary
              - **Timestamp**: ${new Date().toISOString()}
              - **Reason**: ${{ inputs.reason }}
              - **Reverted to**: ${{ inputs.target_commit || 'HEAD~1' }}
              - **Triggered by**: @${{ github.actor }}

              ## Post-Mortem Template
              - [ ] Root cause analysis
              - [ ] Timeline of events
              - [ ] Prevention measures
              - [ ] Update runbooks
              `,
              labels: ['incident', 'post-mortem', 'critical']
            });
```

**MTTR**: <5 minutes (manual trigger + automated execution)

**File**: `claude/tools/sre/emergency_rollback_runbook.md`
```markdown
# Emergency Core Rollback Runbook

## When to Use
- Core system breaking production (context loading failures, agent routing errors)
- Performance degradation >50% from baseline
- Security vulnerability in core components

## Procedure

### Step 1: Trigger Rollback (T+0 to T+2 min)
1. Navigate to: `https://github.com/YOUR_ORG/maia/actions/workflows/emergency-rollback.yml`
2. Click "Run workflow"
3. Fill in:
   - **Target Commit**: Leave empty to revert last commit, OR paste specific SHA
   - **Reason**: Brief description (e.g., "Context loading failing - P95 >5000ms")
   - **Alert Team**: ✅ Checked
4. Click "Run workflow"

### Step 2: Monitor Execution (T+2 to T+5 min)
- Watch workflow run in GitHub Actions
- Verify revert commit created
- Check Slack for team alert

### Step 3: Validate Recovery (T+5 to T+10 min)
- Run smoke tests: `python3 claude/tools/sre/smoke_tests.py`
- Check performance: `python3 claude/tools/sre/performance_baseline.py --check`
- Monitor error logs for 15 minutes

### Step 4: Post-Mortem (T+1 hour to T+24 hours)
- Fill in auto-created GitHub issue
- Identify root cause
- Implement prevention measures
- Update this runbook if needed

## Emergency Contacts
- Primary: @YOUR_USERNAME
- Backup: @senior-team-member
- Slack Channel: #maia-incidents
```

---

## GitHub Branch Protection Configuration

**Repository Settings** → **Branches** → **Branch protection rules** for `main`:

```
✅ Require a pull request before merging
   ✅ Require approvals: 1 (for non-core), 2 (for core paths)
   ✅ Dismiss stale pull request approvals when new commits are pushed
   ✅ Require review from Code Owners

✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   Status checks:
   - core-validation (core-protection.yml)
   - performance-baseline (performance-baseline.yml)
   - security-scan (core-protection.yml)

✅ Require conversation resolution before merging

✅ Require linear history (no merge commits, rebase only)

❌ Allow force pushes (DISABLED - use emergency-rollback.yml instead)
❌ Allow deletions (DISABLED)

✅ Restrict who can push to matching branches
   - @YOUR_USERNAME (owner)
   - @maia-bot (CI/CD automation)
```

---

## Service Level Objectives (SLOs)

### Protection System SLOs

| Metric | SLO | Measurement | Alerting |
|--------|-----|-------------|----------|
| Core Protection Success Rate | >99.9% | No unauthorized core changes per month | Alert if unauthorized change detected |
| CI Pipeline Uptime | >99.5% | CI executes successfully | Alert if failure rate >10% in 1 hour |
| CI Execution Time | <5 min P95 | Workflow duration | Alert if P95 >10 min |
| Emergency Rollback MTTR | <5 min | Manual trigger to recovery | Post-mortem if >5 min |
| False Positive Rate | <2% | Good PRs blocked by CI | Review thresholds if >2% |
| Performance Regression Detection | 100% | Catches >20% degradation | Alert on detection |

### Team Productivity SLOs

| Metric | SLO | Measurement | Impact |
|--------|-----|-------------|--------|
| PR Review Time (Core) | <24 hours | Time to first review | Prevents bottlenecks |
| PR Review Time (Non-Core) | <4 hours | Automated or human | Maintains velocity |
| Team Toil (Git Workflow) | <5 min/week | Surveys + time tracking | Standard PR workflow |
| Onboarding Time | <2 hours | New contributor to first PR | Training materials |

---

## Implementation Phases

### **Phase 1: Repository Cleanup** (Week 1, Days 1-2)
**Duration**: 1-2 days
**Effort**: 8-12 hours

**Tasks**:
1. **Audit Existing Structure**
   - Review `claude/` directory for clutter
   - Identify obsolete/experimental tools
   - Document current state

2. **Reorganize Repository**
   - Move experimental tools to `claude/extensions/experimental/`
   - Archive obsolete tools to `claude/extensions/archive/`
   - Create `claude/projects/` for user-specific code
   - Create template structure in `claude/projects/template/`

3. **Document Core vs Team-Writable**
   - Create `docs/REPOSITORY_STRUCTURE.md`
   - Define protection boundaries
   - Document contribution workflows

**Deliverables**:
- ✅ Clean repository structure
- ✅ `docs/REPOSITORY_STRUCTURE.md`
- ✅ `claude/projects/template/` created

---

### **Phase 2: Protection Setup** (Week 1-2, Days 3-7)
**Duration**: 5 days
**Effort**: 16-20 hours

**Tasks**:
1. **Create CODEOWNERS File** (2 hours)
   - Define ownership rules
   - Map paths to reviewers
   - Test with sample PR

2. **Configure Branch Protection** (1 hour)
   - Enable protection rules on `main`
   - Set approval requirements
   - Configure status checks

3. **Build CI Workflows** (8-10 hours)
   - `core-protection.yml` (4 hours)
   - `performance-baseline.yml` (2 hours)
   - `ci-health-monitor.yml` (2 hours)
   - `core-change-alert.yml` (1 hour)
   - `emergency-rollback.yml` (2 hours)

4. **Build Validation Tools** (5-6 hours)
   - `validate_core_schema.py` (3 hours)
   - `performance_baseline.py` (3 hours)

5. **Create Integration Tests** (4 hours)
   - Core context loading tests
   - Agent routing tests
   - Schema validation tests

**Deliverables**:
- ✅ `CODEOWNERS` configured
- ✅ Branch protection enabled
- ✅ 5 CI workflows operational
- ✅ 2 validation tools built
- ✅ Integration test suite (>80% coverage)

---

### **Phase 3: Documentation & Training** (Week 2, Days 8-10)
**Duration**: 3 days
**Effort**: 8-12 hours

**Tasks**:
1. **Create Team Documentation** (6 hours)
   - `docs/CONTRIBUTING.md` - Contribution guide
   - `docs/CORE_PROTECTION_GUIDE.md` - System overview
   - `docs/EMERGENCY_PROCEDURES.md` - Incident runbook
   - `docs/PR_WORKFLOW.md` - Step-by-step PR guide
   - `docs/FAQ.md` - Common questions

2. **Create Knowledge Base Articles** (4 hours)
   - KBA-001: How to Submit Your First PR
   - KBA-002: Understanding CODEOWNERS
   - KBA-003: What to Do When CI Fails
   - KBA-004: Emergency Rollback Procedure
   - KBA-005: Performance Baseline Troubleshooting

3. **Update TEAM_SETUP_README.md** (1 hour)
   - Add contribution workflow
   - Link to new documentation
   - Add examples

**Deliverables**:
- ✅ 5 documentation files
- ✅ 5 KBA articles
- ✅ Updated team setup guide

---

### **Phase 4: Team Onboarding** (Week 3, Days 11-15)
**Duration**: 5 days
**Effort**: 6-8 hours (your time) + team time

**Tasks**:
1. **Conduct Training Session** (2 hours)
   - Overview of protection system
   - Live demo: Create PR → Review → Merge
   - Live demo: Trigger emergency rollback
   - Q&A session

2. **Pilot with 2-3 Team Members** (3 days)
   - Select pilot team (2-3 people)
   - Guide through first PR submission
   - Monitor CI execution
   - Gather feedback

3. **Tune Thresholds** (2 hours)
   - Review false positive rate
   - Adjust performance baselines if needed
   - Update CI timeout values

4. **Full Team Rollout** (2 days)
   - Announce to full team
   - Share documentation links
   - Monitor for issues
   - Provide support channel (Slack #maia-support)

**Deliverables**:
- ✅ Training materials presented
- ✅ Pilot team onboarded (2-3 people)
- ✅ Thresholds tuned (false positive <2%)
- ✅ Full team enabled

---

### **Phase 5: Monitoring & Optimization** (Ongoing)
**Duration**: Continuous
**Effort**: ~4 hours/quarter

**Tasks**:
1. **Weekly Reviews** (Week 4+, 15 min/week)
   - Check CI health dashboard
   - Review core change alerts
   - Monitor false positive rate

2. **Monthly Retrospectives** (30 min/month)
   - Review protection system metrics
   - Team feedback on workflow
   - Identify improvement opportunities

3. **Quarterly Maintenance** (4 hours/quarter)
   - Update performance baselines
   - Review CI workflow efficiency
   - Update documentation
   - Dependency updates

**Deliverables**:
- ✅ Monthly metrics report
- ✅ Quarterly improvement plan
- ✅ Updated documentation

---

## Documentation Deliverables

### 1. **CONTRIBUTING.md** (Team Contribution Guide)

**Purpose**: Step-by-step guide for team members to contribute

**Sections**:
- Getting Started
- Repository Structure
- What Can I Modify? (protection boundaries)
- How to Submit a PR
- Code Review Process
- What Happens When CI Fails?
- Style Guide & Best Practices

**Length**: ~1,500 words, 10-15 min read

---

### 2. **CORE_PROTECTION_GUIDE.md** (System Overview)

**Purpose**: Explain how the protection system works

**Sections**:
- Architecture Overview (5 layers)
- CODEOWNERS Explanation
- CI Quality Gates
- Performance Baselines
- Emergency Rollback Process
- Monitoring & Alerting
- SLOs & Metrics

**Length**: ~2,000 words, 15-20 min read

---

### 3. **EMERGENCY_PROCEDURES.md** (Incident Runbook)

**Purpose**: Step-by-step emergency response

**Sections**:
- When to Trigger Emergency Rollback
- Emergency Rollback Procedure (with screenshots)
- Validation Steps
- Post-Mortem Template
- Emergency Contacts
- Common Incident Scenarios

**Length**: ~1,000 words, 5-10 min read

---

### 4. **PR_WORKFLOW.md** (Step-by-Step PR Guide)

**Purpose**: Visual guide for creating PRs

**Sections**:
- Create Feature Branch
- Make Changes
- Run Local Tests
- Submit PR (with screenshots)
- Address Review Feedback
- Merge Process
- Troubleshooting Common Issues

**Length**: ~800 words, 10-15 screenshots

---

### 5. **FAQ.md** (Common Questions)

**Purpose**: Quick answers to frequent questions

**Sections**:
- General Questions (10-15 Q&A)
- CODEOWNERS Questions (5-10 Q&A)
- CI/CD Questions (10-15 Q&A)
- Emergency Procedures (5-10 Q&A)
- Performance Baselines (5-10 Q&A)

**Length**: ~1,500 words, 40-50 Q&A pairs

---

## Knowledge Base Articles (KBAs)

### **KBA-001: How to Submit Your First PR**

**Audience**: New team members
**Format**: Step-by-step with screenshots
**Length**: 800 words

**Outline**:
1. Prerequisites (Git installed, repository cloned)
2. Create feature branch (`git checkout -b feature/my-tool`)
3. Make changes to allowed paths (`claude/tools/`, `claude/projects/`)
4. Run local tests (`pytest claude/tests/`)
5. Commit changes (with descriptive message)
6. Push branch (`git push origin feature/my-tool`)
7. Create PR in GitHub (screenshots)
8. Wait for CI (what to expect)
9. Address review feedback
10. Merge confirmation

---

### **KBA-002: Understanding CODEOWNERS**

**Audience**: All team members
**Format**: Conceptual explanation + examples
**Length**: 600 words

**Outline**:
1. What is CODEOWNERS?
2. How does it work in Maia?
3. Protected paths (core, agents)
4. Team-writable paths (tools, extensions)
5. User-owned paths (projects)
6. What happens when you modify protected files?
7. How to request core changes

---

### **KBA-003: What to Do When CI Fails**

**Audience**: All team members
**Format**: Troubleshooting guide
**Length**: 1,000 words

**Outline**:
1. Understanding CI failure messages
2. Common failure reasons:
   - Schema validation errors
   - Integration test failures
   - Performance regression
   - Security issues
   - CODEOWNERS modified
3. How to debug locally
4. How to fix and re-run CI
5. When to ask for help

---

### **KBA-004: Emergency Rollback Procedure**

**Audience**: Owner + senior team members
**Format**: Emergency runbook
**Length**: 800 words

**Outline**:
1. When to trigger emergency rollback
2. Step-by-step procedure (with screenshots)
3. Validation checklist
4. Team communication
5. Post-mortem requirements
6. Example scenarios (with timestamps)

---

### **KBA-005: Performance Baseline Troubleshooting**

**Audience**: Technical contributors
**Format**: Technical troubleshooting
**Length**: 900 words

**Outline**:
1. What are performance baselines?
2. Current baseline values (context: 500ms, routing: 200ms, etc.)
3. Why did my PR fail performance check?
4. How to run baselines locally
5. How to optimize if you caused regression
6. When baselines need updating (legitimate changes)
7. Request baseline adjustment process

---

## Training Materials

### **Training Session Agenda** (2-hour session)

**Part 1: Overview (30 min)**
- Welcome & Objectives
- Why do we need repository governance?
- Architecture overview (5 protection layers)
- Demo: Browse repository structure

**Part 2: Hands-On PR Workflow (60 min)**
- Live demo: Owner creates sample PR
- Hands-on: Each team member creates test PR
  - Modify `claude/projects/USERNAME/test_tool.py`
  - Submit PR
  - Watch CI run
  - Merge
- Hands-on: Attempt to modify core (see protection)
  - Modify `claude/context/core/identity.md`
  - Submit PR
  - See CODEOWNERS review requirement
  - See CI validation

**Part 3: Emergency Procedures (20 min)**
- Live demo: Emergency rollback simulation
- Discussion: When would you use this?
- Review emergency contacts

**Part 4: Q&A (10 min)**
- Open questions
- Feedback collection

---

### **Quick Reference Card** (1-page cheat sheet)

**Content**:
```
╔════════════════════════════════════════════════════════════╗
║           MAIA REPOSITORY QUICK REFERENCE                  ║
╠════════════════════════════════════════════════════════════╣
║ 🔒 PROTECTED (Need owner approval)                         ║
║    • claude/context/core/                                  ║
║    • claude/agents/                                        ║
║    • CLAUDE.md, SYSTEM_STATE.md                            ║
║                                                            ║
║ 🔓 TEAM-WRITABLE (Automated review)                        ║
║    • claude/tools/                                         ║
║    • claude/extensions/                                    ║
║                                                            ║
║ 👤 YOUR NAMESPACE (No review)                              ║
║    • claude/projects/YOUR_USERNAME/                        ║
╠════════════════════════════════════════════════════════════╣
║ STANDARD PR WORKFLOW                                       ║
║   1. git checkout -b feature/my-tool                       ║
║   2. Make changes (in allowed paths)                       ║
║   3. pytest claude/tests/                                  ║
║   4. git commit -m "Description"                           ║
║   5. git push origin feature/my-tool                       ║
║   6. Create PR in GitHub                                   ║
║   7. Wait for CI (green checkmark)                         ║
║   8. Merge!                                                ║
╠════════════════════════════════════════════════════════════╣
║ HELP & SUPPORT                                             ║
║   📚 Docs: /docs/CONTRIBUTING.md                           ║
║   💬 Slack: #maia-support                                  ║
║   🆘 Emergency: @YOUR_USERNAME                               ║
╚════════════════════════════════════════════════════════════╝
```

---

## Success Metrics & Monitoring

### Key Performance Indicators (KPIs)

| KPI | Target | Measurement Frequency | Alert Threshold |
|-----|--------|----------------------|-----------------|
| **Protection Metrics** |
| Core protection success rate | >99.9% | Daily | <99.9% |
| Unauthorized core changes | 0/month | Daily | >0 |
| CI uptime | >99.5% | Every 15 min | <99.5% |
| Emergency rollback MTTR | <5 min | Per incident | >5 min |
| **Team Productivity** |
| PR merge time (non-core) | <4 hours | Weekly | >24 hours |
| PR merge time (core) | <24 hours | Weekly | >72 hours |
| False positive rate | <2% | Weekly | >5% |
| Team toil (Git workflow) | <5 min/week | Monthly survey | >30 min/week |
| **Quality Metrics** |
| Performance regression incidents | 0/month | Daily | >1/month |
| Production incidents from core | 0/month | Daily | >0 |
| Post-merge hotfixes | <1/month | Monthly | >3/month |

---

### Monitoring Dashboards

**Dashboard 1: Protection System Health**
- CI pipeline uptime (15-min resolution)
- Core change frequency (daily)
- PR approval time distribution
- False positive rate trend
- Emergency rollback count

**Dashboard 2: Team Productivity**
- PR throughput (per day/week)
- Review time distribution
- Top contributors
- Contribution by path (core vs tools vs projects)
- Team toil survey results

**Dashboard 3: Quality Metrics**
- Performance baseline trends (P95 over time)
- Test coverage by path
- Incident count (core-related)
- Post-merge hotfix rate

---

## Risk Assessment & Mitigation

### High-Risk Scenarios

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **CI Pipeline Failure** (enforcement down) | Medium | High | CI health monitoring (15-min checks), backup validation script |
| **Owner Unavailable** (vacation/sick) | Medium | Medium | Delegate core approval to 1-2 senior team members |
| **Malicious CODEOWNERS Modification** | Low | Critical | CI validation (CODEOWNERS unchanged check) |
| **Performance Baseline False Positives** | Medium | Low | 20% tolerance, quarterly baseline review |
| **Emergency Rollback Needed** | Low | High | Tested runbook, <5 min MTTR, automated workflow |
| **Team Confusion** (complex workflow) | High | Medium | Comprehensive training, 5 KBAs, 1-page quick reference |
| **Alert Fatigue** | Medium | Medium | Tune thresholds (<2 alerts/week target) |

---

### Rollback Plan (If Project Fails)

**Scenario**: Protection system causing more problems than solving

**Indicators**:
- False positive rate >10%
- Team toil >30 min/week on Git workflow
- PR throughput drops >50%
- Team feedback overwhelmingly negative

**Rollback Procedure**:
1. Disable branch protection rules (Settings → Branches)
2. Remove CODEOWNERS file
3. Keep CI workflows (optional quality checks)
4. Document lessons learned
5. Plan lighter-weight alternative

**Rollback Time**: <30 minutes

---

## Operational Procedures

### Weekly Operational Tasks (15 min/week)

**Monday Morning** (10 min):
- Check CI health dashboard (any alerts?)
- Review core changes from last week
- Scan for long-pending PRs (>48 hours)

**Friday Afternoon** (5 min):
- Review week's metrics
- Update team on any issues
- Plan next week's improvements

---

### Monthly Review (30 min/month)

**First Monday of Month**:
1. Review protection system KPIs (vs targets)
2. Analyze false positive rate (any patterns?)
3. Review team productivity metrics
4. Collect team feedback (async survey)
5. Document improvement actions

---

### Quarterly Maintenance (4 hours/quarter)

**Tasks**:
1. Update performance baselines (re-benchmark)
2. Review CI workflow efficiency (any optimization opportunities?)
3. Update documentation (new learnings, FAQ additions)
4. Dependency updates (GitHub Actions versions)
5. Team retrospective (30-min meeting)
6. Plan next quarter improvements

---

## Cost Analysis

### Implementation Costs

| Phase | Duration | Effort (Hours) | Notes |
|-------|----------|----------------|-------|
| Phase 1: Cleanup | 1-2 days | 8-12 | One-time |
| Phase 2: Protection Setup | 5 days | 16-20 | One-time |
| Phase 3: Documentation | 3 days | 8-12 | One-time |
| Phase 4: Team Onboarding | 5 days | 6-8 | One-time per team |
| **Total Initial** | **2-3 weeks** | **38-52 hours** | |

### Ongoing Costs

| Activity | Frequency | Effort | Annual Total |
|----------|-----------|--------|--------------|
| Weekly monitoring | Weekly | 15 min | 13 hours |
| Monthly reviews | Monthly | 30 min | 6 hours |
| Quarterly maintenance | Quarterly | 4 hours | 16 hours |
| **Total Ongoing** | | | **35 hours/year** |

### Team Productivity Impact

**Time Saved** (vs manual code review):
- Automated CI validation: ~2 hours/week saved
- CODEOWNERS auto-assignment: ~30 min/week saved
- **Annual savings**: ~130 hours/year

**Net ROI**: 130 hours saved - 35 hours maintenance = **+95 hours/year net benefit**

---

## Next Steps

### Immediate Actions (This Week)

1. **Decision**: Approve project plan
2. **Schedule**: Book 2-hour training session (Week 3)
3. **Pilot Team**: Identify 2-3 team members for pilot
4. **Communication**: Announce project to team (timeline, expectations)

### Phase 1 Kickoff (Week 1)

1. **Day 1**: Repository audit + cleanup planning
2. **Day 2**: Execute cleanup, create new structure
3. **Day 3**: Begin Phase 2 (CODEOWNERS + CI setup)

---

## Appendices

### Appendix A: Tool Inventory

**New Tools Created**:
1. `claude/tools/sre/validate_core_schema.py` - Core structure validation
2. `claude/tools/sre/performance_baseline.py` - Performance regression detector
3. `claude/tools/sre/smoke_tests.py` - Post-rollback validation

**New Workflows Created**:
1. `.github/workflows/core-protection.yml` - CI quality gates
2. `.github/workflows/performance-baseline.yml` - Regression detection
3. `.github/workflows/ci-health-monitor.yml` - CI uptime monitoring
4. `.github/workflows/core-change-alert.yml` - Change notifications
5. `.github/workflows/emergency-rollback.yml` - Emergency recovery

---

### Appendix B: File Locations Reference

**Configuration Files**:
- `CODEOWNERS` - Ownership rules
- `.github/workflows/*.yml` - CI/CD workflows

**Tools**:
- `claude/tools/sre/validate_core_schema.py`
- `claude/tools/sre/performance_baseline.py`
- `claude/tools/sre/smoke_tests.py`

**Documentation**:
- `docs/CONTRIBUTING.md`
- `docs/CORE_PROTECTION_GUIDE.md`
- `docs/EMERGENCY_PROCEDURES.md`
- `docs/PR_WORKFLOW.md`
- `docs/FAQ.md`
- `docs/REPOSITORY_STRUCTURE.md`

**Knowledge Base**:
- `docs/kba/KBA-001-First-PR.md`
- `docs/kba/KBA-002-CODEOWNERS.md`
- `docs/kba/KBA-003-CI-Failures.md`
- `docs/kba/KBA-004-Emergency-Rollback.md`
- `docs/kba/KBA-005-Performance-Baselines.md`

**Runbooks**:
- `claude/tools/sre/emergency_rollback_runbook.md`

**Training**:
- `docs/training/Training-Session-Agenda.md`
- `docs/training/Quick-Reference-Card.pdf`

---

### Appendix C: Contact Information

**Project Owner**: Naythan Dawe (@YOUR_USERNAME)

**Emergency Contacts**:
- Primary: @YOUR_USERNAME
- Backup: [Senior Team Member TBD]

**Support Channels**:
- Slack: #maia-support (general questions)
- Slack: #maia-incidents (emergencies)
- GitHub Issues: Tag with `governance` label

---

### Appendix D: References & Related Projects

**Industry Examples**:
- [Google Monorepo (Piper)](https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)
- [Meta Monorepo](https://engineering.fb.com/2014/01/07/core-data/scaling-mercurial-at-facebook/)
- [Microsoft Azure DevOps CODEOWNERS](https://learn.microsoft.com/en-us/azure/devops/repos/git/require-branch-folders)

**Related Maia Projects**:
- Phase 134: Automatic Agent Persistence
- Phase 119: Capability Amnesia Fix
- Phase 129: Confluence Tooling Consolidation

---

**Project Status**: ✅ PLANNING COMPLETE - READY FOR IMPLEMENTATION

**Last Updated**: 2025-10-27
**Version**: 1.0
**Approved By**: [Pending]
