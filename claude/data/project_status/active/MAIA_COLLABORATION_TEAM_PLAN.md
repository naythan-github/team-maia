# Maia Multi-User Collaboration: Team Implementation Plan

**Document Version**: 1.0
**Date**: 2026-01-03
**Status**: Ready for Team Review
**Authors**: DevOps Principal Architect, SRE Principal Engineer, Cloud Security Principal (Agent Swarm)

---

## Executive Summary

### The Problem
Maia is a personal AI infrastructure (556 tools, 91 agents) currently designed for single-user operation. We need to enable 30 Azure/M365 engineers to collaborate while:
1. **Preventing personal data leakage** into the shared repository
2. **Protecting core system integrity** from breaking changes
3. **Enabling team contribution** with minimal friction

### The Solution
**Two-Location Architecture with Defense-in-Depth Protection**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MAIA COLLABORATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────┐         ┌─────────────────────────┐        │
│  │   SHARED REPOSITORY     │         │   LOCAL USER DATA       │        │
│  │   (GitHub - maia/)      │         │   (~/.maia/)            │        │
│  │                         │         │                         │        │
│  │  ┌───────────────────┐  │         │  ┌───────────────────┐  │        │
│  │  │ PROTECTED         │  │         │  │ User Databases    │  │        │
│  │  │ Agents, Hooks,    │  │         │  │ User Preferences  │  │        │
│  │  │ Core Context      │  │         │  │ Personal Profile  │  │        │
│  │  └───────────────────┘  │         │  │ Session State     │  │        │
│  │                         │         │  └───────────────────┘  │        │
│  │  ┌───────────────────┐  │         │                         │        │
│  │  │ TEAM WRITABLE     │  │         │  Never in Git           │        │
│  │  │ Domain Tools      │  │         │  Per-user isolation     │        │
│  │  │ Commands          │  │         │                         │        │
│  │  └───────────────────┘  │         └─────────────────────────┘        │
│  │                         │                                            │
│  │  ┌───────────────────┐  │                                            │
│  │  │ OPEN              │  │                                            │
│  │  │ Extensions        │  │                                            │
│  │  │ Experiments       │  │                                            │
│  │  └───────────────────┘  │                                            │
│  └─────────────────────────┘                                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     PROTECTION LAYERS                             │   │
│  │  Layer 1: CODEOWNERS (reviewer assignment)                       │   │
│  │  Layer 2: CI Quality Gates (personal data, secrets, tests)       │   │
│  │  Layer 3: Branch Protection (PR required, squash merge)          │   │
│  │  Layer 4: Local Hooks (pre-commit, pre-push)                     │   │
│  │  Layer 5: Emergency Recovery (<5 min rollback)                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Outcomes

| Outcome | Target | How |
|---------|--------|-----|
| Zero personal data leakage | 100% blocked | Multi-layer detection (pre-commit + CI) |
| Core system protection | 99.9% | CODEOWNERS + branch protection |
| Team onboarding time | <30 minutes | Automated setup script |
| Emergency recovery | <5 minutes | One-click rollback workflow |
| CI execution time | <5 min P95 | Parallel jobs + caching |
| Contribution friction | Minimal | Auto-merge for open areas |

### Investment Summary

| Phase | Focus | Duration | Effort |
|-------|-------|----------|--------|
| Phase 1 | CI + Protection | Days 1-2 | 8 hours |
| Phase 2 | Path Isolation | Days 3-4 | 10 hours |
| Phase 3 | Local Hooks | Days 5-6 | 8 hours |
| Phase 4 | Emergency Recovery | Day 7 | 4 hours |
| Phase 5 | Validation | Days 8-9 | 8 hours |
| **Total** | | **~2 weeks** | **38 hours** |

**Annual Maintenance**: ~35 hours/year
**Net Productivity Gain**: +95 hours/year (team of 30)

---

## Architecture Decision Records (ADRs)

### ADR-001: Clean Repository Start

**Decision**: Start with a fresh repository instead of scrubbing git history.

**Context**: Personal data exists in the current repository (profile, user databases, hardcoded paths).

**Options Considered**:
1. **Git filter-branch/BFG** - Remove personal data from history
2. **Fresh repository** - Start clean, migrate code manually

**Decision**: Option 2 - Fresh repository

**Rationale**:
- Eliminates risk of missed personal data in history
- Simpler mental model for team
- No complex git operations
- Clean commit history from day one

**Consequences**:
- Lose git history (acceptable - history is in current repo as archive)
- One-time migration effort

---

### ADR-002: Two-Location Data Architecture

**Decision**: Separate shared code (Git) from personal data (~/.maia/).

**Context**: Need to prevent personal data leakage while enabling collaboration.

**Options Considered**:
1. **Everything in Git** with .gitignore - Risk of accidental commit
2. **Separate repos** (shared + personal) - Complexity, sync issues
3. **Two locations** - Shared repo + ~/.maia/ local directory

**Decision**: Option 3 - Two locations

**Rationale**:
- Personal data physically cannot be in Git path
- Simple mental model: "~/.maia/ is mine, maia/ is shared"
- No sync required - local data stays local
- Matches Unix conventions (config in home directory)

**Consequences**:
- Setup script must create ~/.maia/ structure
- Tools must use dynamic path resolution

---

### ADR-003: Three-Tier Protection Model

**Decision**: Use three protection tiers (Protected, Team, Open).

**Context**: Need to balance protection with team productivity for 30 engineers.

**Tiers**:

| Tier | Paths | Approval | Rationale |
|------|-------|----------|-----------|
| **Protected** | Agents, hooks, core context, CLAUDE.md | Owner only | System-critical, breaking changes affect everyone |
| **Team** | Domain tools, commands, tests | Owner visibility | Quality matters, but team can contribute |
| **Open** | Extensions, experiments, user namespaces | CI only | Low risk, encourage innovation |

**Consequences**:
- Owner is bottleneck for Protected tier (mitigated by backup owners)
- Team tier may need domain leads as CODEOWNERS scales

---

### ADR-004: Squash Merge Only

**Decision**: Enforce squash merge to main branch.

**Context**: 30 engineers will create many PRs; need clean history.

**Rationale**:
- Linear history is easier to bisect
- One commit per PR makes reverts simpler
- Encourages right-sized PRs
- Cleaner git log

**Consequences**:
- Individual commits within PR are lost (acceptable)
- PR title becomes commit message (team must write good titles)

---

### ADR-005: No Git Submodules

**Decision**: Keep single repository, no submodules.

**Context**: Considered separating personal tools into submodule.

**Rationale**:
- Submodules add complexity (detached heads, sync issues)
- Single repo is simpler to clone and manage
- CODEOWNERS provides sufficient protection
- Two-location architecture handles personal data

**Consequences**:
- All 556 tools in one repo (acceptable with domain directories)
- Larger clone size (acceptable)

---

### ADR-006: GitHub Actions for CI (No Self-Hosted Runners)

**Decision**: Use GitHub-hosted runners for all CI.

**Context**: Need <5 minute CI, considering self-hosted for speed.

**Rationale**:
- GitHub-hosted runners have no maintenance burden
- Pip caching reduces cold start impact
- Parallel jobs achieve <5 minute target
- Self-hosted adds infrastructure complexity

**Consequences**:
- Subject to GitHub Actions availability
- Queue delays possible at peak times (mitigated by parallelization)

---

## Implementation Checklist

### Phase 1: Immediate Protection (Days 1-2)

**Goal**: Block personal data leakage, establish baseline protection

#### Day 1 (4 hours)

- [ ] **1.1** Create `.github/CODEOWNERS`
  - [ ] Add three-tier protection rules
  - [ ] Add backup owner(s) for availability

- [ ] **1.2** Create `.github/workflows/ci.yml`
  - [ ] Personal data detection job
  - [ ] Hardcoded path detection job
  - [ ] Secret scanning (Trufflehog)
  - [ ] Test job with coverage
  - [ ] Lint job (ruff)

- [ ] **1.3** Configure branch protection
  - [ ] Require PR before merging
  - [ ] Require 1 approval
  - [ ] Require CODEOWNERS review
  - [ ] Require status checks (ci.yml)
  - [ ] Enable squash merge only

#### Day 2 (4 hours)

- [ ] **1.4** Create `.github/CONTRIBUTING.md`
  - [ ] Contribution workflow
  - [ ] Branch naming conventions
  - [ ] PR checklist

- [ ] **1.5** Create `.github/PULL_REQUEST_TEMPLATE.md`
  - [ ] Summary section
  - [ ] Type of change checkboxes
  - [ ] Testing checklist
  - [ ] Security checklist

- [ ] **1.6** Create `requirements-dev.txt`
  - [ ] pytest, pytest-cov
  - [ ] ruff, mypy

- [ ] **1.7** Update `.gitignore`
  - [ ] All database patterns
  - [ ] Personal data paths
  - [ ] Credential patterns

- [ ] **1.8** Configure Teams integration
  - [ ] Subscribe channel to repository
  - [ ] Configure notification filters

- [ ] **1.9** Create auto-labeler
  - [ ] `.github/labeler.yml`
  - [ ] `.github/workflows/labeler.yml`

**Exit Criteria**:
- [ ] PR to main requires approval
- [ ] CI runs on all PRs
- [ ] Personal data patterns blocked
- [ ] Teams notifications working

---

### Phase 2: Path Isolation (Days 3-4)

**Goal**: Enable multi-user with proper data separation

#### Day 3 (5 hours)

- [ ] **2.1** Create `claude/tools/core/paths.py`
  ```python
  class PathManager:
      get_maia_root() -> Path
      get_user_data_path() -> Path  # ~/.maia/
      get_user_db_path(name) -> Path
      get_shared_db_path(name) -> Path
  ```

- [ ] **2.2** Fix hardcoded path tools (8 identified)
  - [ ] `dns_audit_route53.py`
  - [ ] `create_clean_orro_template.py`
  - [ ] `dns_complete_audit.py`
  - [ ] `intelligent_product_grouper.py`
  - [ ] `test_cv_parser.py`
  - [ ] `health_check.py`
  - [ ] `morning_email_intelligence_local.py`
  - [ ] `personal_knowledge_graph.py`

#### Day 4 (5 hours)

- [ ] **2.3** Create `scripts/setup-team-member.sh`
  - [ ] Create `~/.maia/` directory structure
  - [ ] Create profile template
  - [ ] Create user_preferences.json
  - [ ] Install git hooks
  - [ ] Regenerate local databases

- [ ] **2.4** Create `.github/workflows/core-protection.yml`
  - [ ] Trigger on protected paths only
  - [ ] Validate CODEOWNERS unchanged
  - [ ] Run core integration tests
  - [ ] Notify owner of core changes

- [ ] **2.5** Create profile template
  - [ ] `~/.maia/context/personal/profile.md` template
  - [ ] Document required fields

**Exit Criteria**:
- [ ] All tools use PathManager
- [ ] Setup script creates complete ~/.maia/
- [ ] Core changes trigger extra validation

---

### Phase 3: Local Quality Gates (Days 5-6)

**Goal**: Shift-left quality enforcement

#### Day 5 (4 hours)

- [ ] **3.1** Create `claude/hooks/contribution_reviewer.py`
  - [ ] Check 1: No secrets
  - [ ] Check 2: No personal data
  - [ ] Check 3: No hardcoded paths
  - [ ] Check 4: File locations correct
  - [ ] Check 5: Naming conventions
  - [ ] Check 6: Tests exist for new tools
  - [ ] Check 7: Docstrings present

- [ ] **3.2** Add hooks to setup script
  - [ ] pre-commit: Personal data + secrets
  - [ ] pre-push: Block main, run reviewer
  - [ ] post-merge: Regenerate databases

#### Day 6 (4 hours)

- [ ] **3.3** Create core integration tests
  - [ ] `tests/core/test_context_loading.py`
  - [ ] `tests/core/test_agent_routing.py`
  - [ ] `tests/core/test_path_resolution.py`

- [ ] **3.4** Validate hook installation
  - [ ] Test pre-commit blocks personal data
  - [ ] Test pre-push blocks main
  - [ ] Test post-merge regenerates DBs

**Exit Criteria**:
- [ ] Local hooks catch issues before push
- [ ] Core has test coverage >80%
- [ ] contribution_reviewer.py passes all checks

---

### Phase 4: Emergency Recovery (Day 7)

**Goal**: Enable rapid rollback

- [ ] **4.1** Create `.github/workflows/emergency-rollback.yml`
  - [ ] Manual trigger (workflow_dispatch)
  - [ ] Target commit input
  - [ ] Reason input (required)
  - [ ] Create revert commit
  - [ ] Push directly to main
  - [ ] Create post-mortem issue

- [ ] **4.2** Create emergency runbook
  - [ ] `docs/runbooks/emergency-rollback.md`
  - [ ] Detection steps
  - [ ] Execution steps
  - [ ] Verification steps
  - [ ] Escalation contacts

- [ ] **4.3** Configure ADMIN_PAT secret
  - [ ] Create GitHub PAT with admin access
  - [ ] Add to repository secrets
  - [ ] Document rotation schedule

- [ ] **4.4** Test rollback procedure
  - [ ] Create test breaking change
  - [ ] Execute rollback workflow
  - [ ] Verify <5 min recovery
  - [ ] Verify post-mortem issue created

**Exit Criteria**:
- [ ] Rollback workflow tested
- [ ] Recovery time <5 minutes
- [ ] Runbook documented

---

### Phase 5: Validation & Onboarding (Days 8-9)

**Goal**: Prove system works end-to-end

#### Day 8 (4 hours)

- [ ] **5.1** Fresh clone test
  - [ ] Clone repository on clean machine
  - [ ] Run setup script
  - [ ] Verify Maia loads
  - [ ] Time: <30 minutes total

- [ ] **5.2** Full PR workflow test
  - [ ] Create feature branch
  - [ ] Make change to team-writable path
  - [ ] Push and create PR
  - [ ] Verify CI passes
  - [ ] Get approval and merge

#### Day 9 (4 hours)

- [ ] **5.3** Core rejection test
  - [ ] Create PR modifying `claude/agents/`
  - [ ] Verify CODEOWNERS requires owner
  - [ ] Verify cannot merge without approval

- [ ] **5.4** Personal data rejection test
  - [ ] Attempt commit with hardcoded path
  - [ ] Verify pre-commit hook blocks
  - [ ] Verify CI would catch if bypassed

- [ ] **5.5** Emergency rollback test
  - [ ] Trigger rollback workflow
  - [ ] Verify execution <5 min
  - [ ] Verify post-mortem issue created

- [ ] **5.6** Document lessons learned
  - [ ] Update runbooks with findings
  - [ ] Note any edge cases discovered
  - [ ] Update this checklist if needed

**Exit Criteria**:
- [ ] 2 team members onboarded successfully
- [ ] All test scenarios pass
- [ ] Documentation complete

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Status |
|----|------|-------------|--------|------------|--------|
| R1 | CODEOWNERS bottleneck (owner unavailable) | HIGH | MEDIUM | Add 2 backup CODEOWNERS with different time zones | **ACTION REQUIRED** |
| R2 | CI saturation with 30 concurrent PRs | MEDIUM | MEDIUM | Pip caching, parallel jobs, queue monitoring | Mitigated in design |
| R3 | Breaking change bypasses protection | LOW | HIGH | Branch protection + emergency rollback | Mitigated in design |
| R4 | Personal data leaks to repository | MEDIUM | HIGH | Multi-layer detection (hooks + CI) | Mitigated in design |
| R5 | Hardcoded paths break for other users | HIGH | MEDIUM | Path audit + fix before sharing | **PHASE 2** |
| R6 | Session file collision (shared machine) | LOW | LOW | Add $USER prefix to session filename | Minor fix needed |
| R7 | CI pipeline down (GitHub outage) | LOW | HIGH | Manual merge fallback documented | Accept risk |
| R8 | Team doesn't follow contribution guide | MEDIUM | LOW | PR template enforces checklist | Mitigated in design |

### Critical Actions Before Launch

1. **Add backup CODEOWNERS** - At least 2 people who can approve protected paths
2. **Fix 8 hardcoded path tools** - Cannot share until complete
3. **Create fresh repository** - Personal data must never be in shared history
4. **Test with 2-3 team members** - Validate before full 30-person rollout

---

## Validation Test Plan

### Pre-Launch Tests (Must Pass)

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Fresh clone works | `git clone`, `./scripts/setup-team-member.sh`, type `load` | Maia loads in <30 min | [ ] |
| Personal data blocked locally | Add `YOUR_USERNAME` to file, `git commit` | Pre-commit hook blocks | [ ] |
| Personal data blocked in CI | Force-push PR with personal data | CI fails, merge blocked | [ ] |
| Hardcoded paths blocked | Add `/Users/test/` to .py file | CI fails | [ ] |
| Secrets blocked | Add fake API key to file | Trufflehog catches | [ ] |
| Protected path requires owner | PR to `claude/agents/` | CODEOWNERS shows owner | [ ] |
| Direct push to main blocked | `git push origin main` | Pre-push hook blocks | [ ] |
| CI completes <5 min | Measure 10 PR runs | P95 < 5 minutes | [ ] |
| Emergency rollback works | Trigger workflow | Revert in <5 min | [ ] |
| Post-merge regenerates DBs | Merge PR, check databases | Databases updated | [ ] |

### Post-Launch Monitoring (First 2 Weeks)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| CI false positive rate | <2% | Track manual overrides |
| Onboarding time | <30 min | Survey new team members |
| PR review latency (team tier) | <4 hours | GitHub insights |
| PR review latency (protected) | <24 hours | GitHub insights |
| Emergency rollbacks triggered | 0 | Incident tracking |
| Personal data near-misses | 0 | CI block count |

---

## Team Communication Template

### Announcement Email

```
Subject: Maia Multi-User Collaboration - Ready for Team Use

Team,

We've enabled multi-user collaboration on Maia. Here's what you need to know:

GETTING STARTED (30 minutes)
1. Clone: git clone git@github.com:[org]/maia.git
2. Setup: ./scripts/setup-team-member.sh
3. Verify: Open Claude Code, type "load"

KEY RULES
- Your personal data lives in ~/.maia/ (never committed)
- Core files (agents, hooks) require owner approval
- Domain tools (sre/, security/) - open for contribution
- Extensions and experiments - auto-merge with CI pass

CONTRIBUTION WORKFLOW
1. Create branch: git checkout -b feature/your-feature
2. Make changes, commit, push
3. Create PR on GitHub
4. CI runs automatically
5. Get approval (if needed), merge

HELP
- Guide: .github/CONTRIBUTING.md
- Questions: #maia-support channel
- Issues: Create GitHub issue

Let's build!
```

---

## Appendix: Files to Create

### Priority 1 (Phase 1)
1. `.github/CODEOWNERS`
2. `.github/workflows/ci.yml`
3. `.github/CONTRIBUTING.md`
4. `.github/PULL_REQUEST_TEMPLATE.md`
5. `.github/labeler.yml`
6. `.github/workflows/labeler.yml`
7. `requirements-dev.txt`

### Priority 2 (Phase 2)
8. `claude/tools/core/paths.py`
9. `scripts/setup-team-member.sh`
10. `.github/workflows/core-protection.yml`

### Priority 3 (Phase 3)
11. `claude/hooks/contribution_reviewer.py`
12. `tests/core/test_context_loading.py`
13. `tests/core/test_agent_routing.py`

### Priority 4 (Phase 4)
14. `.github/workflows/emergency-rollback.yml`
15. `docs/runbooks/emergency-rollback.md`

---

**Document Status**: Ready for team review and approval
**Next Step**: Phase 1 implementation (Day 1)
**Owner**: @YOUR_USERNAME
