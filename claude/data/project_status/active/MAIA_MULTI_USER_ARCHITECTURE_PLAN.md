# Maia Multi-User Architecture Project Plan

**Document Version**: 1.0
**Created**: 2024-12-14
**Author**: Naythan Dawe + Maia (SRE Principal Engineer + Git Specialist Agents)
**Status**: Planning Complete - Ready for Implementation
**Classification**: Team Shared

---

## Executive Summary

This document defines the architecture and implementation plan for enabling **multi-user collaboration** on the Maia AI infrastructure. The goal is to allow team members to work with Maia locally on their own laptops while sharing core improvements (tools, agents, commands) through a controlled contribution workflow.

### Key Principles
1. **Local-first operation** - No VPN, no shared database, full offline capability
2. **Personal data isolation** - User learning, preferences, and profiles never shared
3. **Controlled core sharing** - Improvements to tools/agents/commands shared via PR workflow
4. **Maia-powered approval** - Automated quality gates with Maia reviewing contributions
5. **Easy adoption** - Minimal setup, familiar Git workflow

### Current State Assessment
- **Multi-User Readiness**: ~30%
- **Architecture Quality**: Excellent modularity, single-user optimized
- **Primary Gaps**: User identity layer, data isolation, collaboration infrastructure

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Architecture Decision](#2-architecture-decision)
3. [Repository Structure](#3-repository-structure)
4. [What Gets Shared vs Local](#4-what-gets-shared-vs-local)
5. [Database Strategy](#5-database-strategy)
6. [Git Workflow](#6-git-workflow)
7. [Branch Strategy](#7-branch-strategy)
8. [Quality Gates](#8-quality-gates)
9. [Implementation Phases](#9-implementation-phases)
10. [File Changes Required](#10-file-changes-required)
11. [Team Onboarding](#11-team-onboarding)
12. [Risk Assessment](#12-risk-assessment)
13. [Success Metrics](#13-success-metrics)
14. [Appendix: Configuration Files](#appendix-configuration-files)

---

## 1. Problem Statement

### Current Situation
Maia is a personal AI infrastructure with 92 agents, 278+ tools, and 117 commands. It currently operates as a single-user system with:
- Personal data embedded in the repository
- User-specific database naming (`*_naythan.db`)
- Session state tied to local machine
- No contribution workflow for team improvements

### Requirements
| Requirement | Priority | Notes |
|-------------|----------|-------|
| Team works on own laptops | Must Have | No VPN, no shared DB |
| Share core improvements | Must Have | Tools, agents, commands |
| Personal data stays private | Must Have | Learning, preferences, profile |
| Approval workflow for changes | Must Have | Prevent core corruption |
| Maia can review contributions | Should Have | Automated quality gates |
| Easy setup for team | Should Have | < 30 min onboarding |
| Offline operation | Must Have | Full local functionality |

### Constraints
- No internet-accessible shared database
- Team members on different networks
- Must preserve existing Maia functionality
- Cannot require significant training

---

## 2. Architecture Decision

### Selected Approach: Two-Location Model

After evaluating three options, **Option A: Shared Core + Per-User Data** was selected.

#### Options Evaluated

| Option | Description | Pros | Cons | Selected |
|--------|-------------|------|------|----------|
| **A: Two-Location** | Shared Git repo + `~/.maia/` local | Clean separation, minimal changes | Two locations to understand | **Yes** |
| B: Monorepo + .gitignore | Single repo, ignore personal | Simple structure | Risk of accidental commits | No |
| C: Fork-based | Each user forks | Full isolation | Sync overhead, merge complexity | No |

#### Decision Rationale
1. **Clear mental model**: "Shared stuff in repo, personal stuff in ~/.maia/"
2. **Zero risk of personal data leakage**: Personal files never in Git working directory
3. **Standard Git workflow**: PRs, reviews, merges - familiar to developers
4. **Minimal migration**: Move ~10 files, update ~5 path references
5. **Future-proof**: Can evolve to database-backed if scale demands

---

## 3. Repository Structure

### Shared Repository (Git)
```
maia/                              # Shared Git repository
├── CLAUDE.md                      # System instructions
├── SYSTEM_STATE.md                # Phase history and capabilities
├── README.md                      # Project overview
├── requirements.txt               # Python dependencies
├── .gitignore                     # Excludes personal/generated data
├── .github/
│   ├── CODEOWNERS                 # Domain ownership rules
│   ├── PULL_REQUEST_TEMPLATE.md   # PR checklist
│   ├── CONTRIBUTING.md            # Contribution guide
│   └── workflows/
│       └── maia-ci.yml            # CI/CD pipeline
├── scripts/
│   └── setup-team-member.sh       # Team onboarding script
├── tests/                         # Test suite
│   └── [domain]/test_*.py
└── claude/
    ├── agents/                    # 92 specialized agents (shared)
    │   └── *_agent.md
    ├── tools/                     # 278+ tools (shared)
    │   ├── core/                  # System utilities
    │   ├── sre/                   # SRE/reliability tools
    │   ├── security/              # Security tools
    │   ├── experimental/          # Work-in-progress (shared)
    │   └── [domain]/              # Domain-specific tools
    ├── commands/                  # 117 slash commands (shared)
    │   └── *.md
    ├── hooks/                     # System hooks (shared)
    │   ├── user-prompt-submit
    │   ├── swarm_auto_loader.py
    │   ├── pre_commit_tdd_gate.py
    │   └── contribution_reviewer.py  # NEW: Maia review system
    ├── context/
    │   ├── core/                  # System protocols (shared)
    │   ├── tools/                 # Tool documentation (shared)
    │   ├── knowledge/             # Domain knowledge (shared)
    │   └── projects/              # Project contexts (shared)
    └── data/
        ├── databases/
        │   ├── system/            # Generated DBs (gitignored)
        │   └── intelligence/      # Shared intelligence (optional)
        ├── project_status/        # Phase documentation
        │   ├── active/
        │   └── archive/
        └── immutable_paths.json   # File protection rules (shared)
```

### Local User Data (~/.maia/)
```
~/.maia/                           # Per-user, never in Git
├── data/
│   ├── databases/
│   │   └── user/                  # User-specific databases
│   │       ├── background_learning.db
│   │       ├── calendar_optimizer.db
│   │       ├── contextual_memory.db
│   │       └── [other personal DBs]
│   ├── user_preferences.json      # Default agent, settings
│   └── checkpoints/               # Session recovery data
├── context/
│   └── personal/
│       └── profile.md             # Personal identity/preferences
└── projects/                      # Personal work outputs
```

### Temporary Session Data
```
/tmp/maia_{USERNAME}_{CONTEXT_ID}.json   # Per-user session files
```

---

## 4. What Gets Shared vs Local

### Definitive Classification

| Category | Location | In Git | Shared | Notes |
|----------|----------|--------|--------|-------|
| **Agents** | `claude/agents/` | Yes | Yes | All 92 agents |
| **Tools** | `claude/tools/` | Yes | Yes | All 278+ tools |
| **Commands** | `claude/commands/` | Yes | Yes | All 117 commands |
| **Hooks** | `claude/hooks/` | Yes | Yes | Enforcement system |
| **Core Context** | `claude/context/core/` | Yes | Yes | Protocols, identity |
| **Knowledge** | `claude/context/knowledge/` | Yes | Yes | Domain expertise |
| **Tests** | `tests/` | Yes | Yes | Quality assurance |
| **System DBs** | `claude/data/databases/system/` | No | Generated | Regenerate locally |
| **Intelligence DBs** | `claude/data/databases/intelligence/` | Optional | Optional | Team decides |
| **User DBs** | `~/.maia/data/databases/user/` | No | No | Personal learning |
| **User Preferences** | `~/.maia/data/user_preferences.json` | No | No | Personal settings |
| **Personal Profile** | `~/.maia/context/personal/profile.md` | No | No | Personal identity |
| **Checkpoints** | `~/.maia/data/checkpoints/` | No | No | Session recovery |
| **Session State** | `/tmp/maia_{user}_{ctx}.json` | No | No | Ephemeral |

### Personal Data That Must Be Externalized

The following files currently contain personal data and must move to `~/.maia/`:

| Current Location | New Location | Contains |
|------------------|--------------|----------|
| `claude/context/personal/profile.md` | `~/.maia/context/personal/profile.md` | Name, email, role, paths |
| `claude/data/user_preferences.json` | `~/.maia/data/user_preferences.json` | Default agent |
| `claude/data/databases/user/*_naythan.db` | `~/.maia/data/databases/user/*.db` | Personal learning |

---

## 5. Database Strategy

### Core Principle: Source Files are Truth, Databases are Cache

```
Source of Truth (Git)              Derived Cache (Local)
─────────────────────              ────────────────────
claude/tools/*.py      ──scan──►   capabilities.db
claude/agents/*.md     ──────►     (regenerated locally)
SYSTEM_STATE.md        ──parse──►  system_state.db
```

### Database Classification

| Database | Type | Strategy | Regeneration Command |
|----------|------|----------|---------------------|
| `capabilities.db` | Derived | Don't share, regenerate | `capabilities_registry.py scan` |
| `system_state.db` | Derived | Don't share, regenerate | `system_state_etl.py --recent all` |
| `tool_discovery.db` | Derived | Don't share, regenerate | Auto on capability scan |
| `deduplication.db` | Derived | Don't share, regenerate | Auto rebuild |
| `routing_decisions.db` | Accumulated | Don't share | Local analytics |
| `conversations.db` | Accumulated | Don't share | Local history |
| `performance_metrics.db` | Accumulated | Don't share | Local metrics |
| `*_naythan.db` (user/) | Personal | Move to ~/.maia/ | N/A |

### .gitignore Additions for Databases

```gitignore
# Derived databases - regenerate locally after pull
claude/data/databases/system/capabilities.db*
claude/data/databases/system/system_state.db*
claude/data/databases/system/tool_discovery.db*
claude/data/databases/system/deduplication.db*

# Accumulated local data
claude/data/databases/system/routing_decisions.db*
claude/data/databases/system/conversations.db*
claude/data/databases/system/performance_metrics.db*
claude/data/databases/system/verification_hook.db*
claude/data/databases/system/self_improvement.db*
claude/data/databases/system/system_health.db*
claude/data/databases/system/research_cache.db*

# Business-specific (if any)
claude/data/databases/system/orro_*.db*

# User databases (should be in ~/.maia/ but exclude if present)
claude/data/databases/user/

# SQLite temp files
*.db-shm
*.db-wal
*.db-journal
```

### Post-Pull Database Regeneration

Databases automatically regenerate via Git post-merge hook:

```bash
# .git/hooks/post-merge
#!/bin/bash
echo "🔄 Refreshing local databases from shared files..."
python3 claude/tools/sre/capabilities_registry.py scan --quiet
python3 claude/tools/sre/system_state_etl.py --recent all --quiet 2>/dev/null || true
echo "✅ Local databases updated"
```

---

## 6. Git Workflow

### Contribution Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTRIBUTION WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: SYNC                                                   │
│  ──────────────                                                 │
│  $ git checkout main                                            │
│  $ git pull origin main                                         │
│  # Post-merge hook regenerates capabilities.db automatically    │
│                                                                  │
│  STEP 2: BRANCH                                                 │
│  ─────────────                                                  │
│  $ git checkout -b feature/descriptive-name                     │
│  # Naming: feature/, fix/, enhance/, docs/                      │
│                                                                  │
│  STEP 3: DEVELOP                                                │
│  ───────────────                                                │
│  # New tools → claude/tools/experimental/ first                 │
│  # Write tests → tests/test_*.py                                │
│  # Test locally → python -m pytest tests/test_*.py              │
│                                                                  │
│  STEP 4: GRADUATE (if new tool/agent)                           │
│  ─────────────────────────────────────                          │
│  # Move from experimental/ to production directory              │
│  $ mv claude/tools/experimental/my_tool.py \                    │
│       claude/tools/sre/my_tool.py                               │
│                                                                  │
│  STEP 5: COMMIT                                                 │
│  ─────────────                                                  │
│  $ git add .                                                    │
│  $ git commit -m "feat(tools): add descriptive message"         │
│  # Follow conventional commit format                            │
│                                                                  │
│  STEP 6: LOCAL REVIEW                                           │
│  ────────────────────                                           │
│  $ /review-contribution                                         │
│  # Maia validates: security, architecture, TDD, docs            │
│  # Must pass before push                                        │
│                                                                  │
│  STEP 7: PUSH & PR                                              │
│  ────────────────                                               │
│  $ git push -u origin feature/descriptive-name                  │
│  $ gh pr create --fill                                          │
│  # Or create PR via GitHub UI                                   │
│                                                                  │
│  STEP 8: REVIEW & MERGE                                         │
│  ──────────────────────                                         │
│  # CI runs automated checks                                     │
│  # Code owner reviews (Naythan or delegate)                     │
│  # Squash merge to main                                         │
│                                                                  │
│  STEP 9: CLEANUP                                                │
│  ─────────────                                                  │
│  $ git checkout main                                            │
│  $ git pull origin main                                         │
│  $ git branch -d feature/descriptive-name                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
| Type | Use For | Example |
|------|---------|---------|
| `feat` | New capability | `feat(agents): add Kubernetes specialist agent` |
| `fix` | Bug fix | `fix(hooks): prevent session collision` |
| `enhance` | Improvement | `enhance(tools): add retry logic to API client` |
| `docs` | Documentation | `docs(readme): update installation steps` |
| `test` | Tests | `test(sre): add system_state_queries tests` |
| `refactor` | Restructure | `refactor(tools): consolidate path utilities` |

**Scopes:** `tools`, `agents`, `commands`, `hooks`, `context`, `tests`, `ci`

---

## 7. Branch Strategy

### Selected: GitHub Flow

**Why GitHub Flow** (not GitFlow):
- Simple: main + feature branches
- Right-sized for small team
- Continuous integration friendly
- Low learning curve

### Branch Structure

```
main (protected)
  │
  ├── feature/user-a/azure-cost-analyzer
  ├── feature/user-b/fix-agent-routing
  ├── fix/session-collision-bug
  ├── enhance/tdd-hook-performance
  └── docs/contribution-guide
```

### Branch Naming Convention

| Prefix | Use For | Example |
|--------|---------|---------|
| `feature/` | New capabilities | `feature/kubernetes-agent` |
| `fix/` | Bug fixes | `fix/database-lock-timeout` |
| `enhance/` | Improvements | `enhance/context-loader-speed` |
| `docs/` | Documentation | `docs/api-reference` |
| `refactor/` | Code restructure | `refactor/tool-organization` |

### Branch Protection Rules (main)

```yaml
Protection Rules for 'main':
├── Require pull request before merging: Yes
│   ├── Required approving reviews: 1
│   ├── Dismiss stale reviews: Yes
│   └── Require review from code owners: Yes
├── Require status checks to pass: Yes
│   ├── Require branches to be up to date: Yes
│   └── Required checks: [test, maia-review]
├── Require linear history: Yes (squash merge)
├── Allow force pushes: No
└── Allow deletions: No
```

---

## 8. Quality Gates

### Gate 1: Pre-Commit (Local)

Runs automatically on `git commit`:

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "🔍 Running pre-commit checks..."

# Check 1: No personal data in staged files
if git diff --cached --name-only | xargs grep -l "naythandawe\|/Users/naythan" 2>/dev/null; then
    echo "❌ BLOCKED: Personal data detected in staged files"
    echo "   Remove personal paths/usernames before committing"
    exit 1
fi

# Check 2: TDD gate (tests exist for new tools)
python3 claude/hooks/pre_commit_tdd_gate.py

# Check 3: File organization (correct directories)
python3 claude/hooks/pre_commit_file_organization.py

echo "✅ Pre-commit passed"
```

### Gate 2: Pre-Push (Before Sharing)

Runs automatically on `git push`:

```bash
#!/bin/bash
# .git/hooks/pre-push

set -e

# Block direct push to main
protected_branch='main'
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

if [ "$current_branch" = "$protected_branch" ]; then
    echo "❌ BLOCKED: Direct push to main not allowed"
    echo "   Create a feature branch and submit a PR"
    exit 1
fi

# Run Maia contribution review
echo "🤖 Running Maia contribution review..."
python3 claude/tools/contribution_reviewer.py

if [ $? -ne 0 ]; then
    echo "❌ BLOCKED: Maia review failed"
    echo "   Fix the issues listed above and try again"
    exit 1
fi

echo "✅ Ready to push"
```

### Gate 3: Maia Review System (New Tool)

The `/review-contribution` command runs comprehensive validation:

```python
# claude/tools/contribution_reviewer.py
"""
Maia-powered contribution review system.
Validates changes meet quality standards before PR.
"""

class ContributionReviewer:
    """
    Checks performed:
    1. Security - No secrets, no injection risks, no personal data
    2. Architecture - Correct paths, naming conventions, no sprawl
    3. TDD - Tests exist and pass for new code
    4. Documentation - Relevant docs updated
    5. Quality - Code patterns, error handling, no breaking changes
    """

    def review(self) -> ReviewResult:
        results = []

        # Security scan
        results.append(self.check_no_secrets())
        results.append(self.check_no_personal_data())
        results.append(self.check_no_injection_risks())

        # Architecture compliance
        results.append(self.check_file_locations())
        results.append(self.check_naming_conventions())
        results.append(self.check_no_sprawl())

        # TDD compliance
        results.append(self.check_tests_exist())
        results.append(self.check_tests_pass())

        # Documentation
        results.append(self.check_docs_updated())

        # Quality
        results.append(self.check_code_patterns())
        results.append(self.check_no_breaking_changes())

        if all(r.passed for r in results):
            return ReviewResult.APPROVED
        else:
            return ReviewResult.NEEDS_WORK(results)
```

### Gate 4: CI Pipeline (GitHub Actions)

Runs automatically on PR:

```yaml
# .github/workflows/maia-ci.yml
name: Maia CI

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt pytest
      - name: Run tests
        run: python -m pytest tests/ -v

  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for personal data
        run: |
          if grep -rE "naythandawe|/Users/naythan" claude/ --include="*.py" --include="*.md"; then
            echo "❌ Personal data found"
            exit 1
          fi

  maia-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Maia architecture check
        run: python3 claude/tools/contribution_reviewer.py --ci
```

### Gate 5: Human Review (Code Owner)

Required before merge:
- At least 1 approval from CODEOWNERS
- All CI checks passing
- No unresolved comments

---

## 9. Implementation Phases

### Phase 0: Preparation (2 hours)

| Task | Description | Owner |
|------|-------------|-------|
| 0.1 | Create GitHub repository | Naythan |
| 0.2 | Set up branch protection rules | Naythan |
| 0.3 | Create team access (collaborators) | Naythan |
| 0.4 | Document current state baseline | Maia |

### Phase 1: Repository Structure (4 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 1.1 | Create `.github/` directory | New directory |
| 1.2 | Add CODEOWNERS file | `.github/CODEOWNERS` |
| 1.3 | Add PR template | `.github/PULL_REQUEST_TEMPLATE.md` |
| 1.4 | Add contributing guide | `.github/CONTRIBUTING.md` |
| 1.5 | Create CI workflow | `.github/workflows/maia-ci.yml` |
| 1.6 | Update .gitignore | `.gitignore` |

### Phase 2: Path System Updates (4 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 2.1 | Add user data path resolution | `claude/tools/core/paths.py` |
| 2.2 | Update session file paths | `claude/hooks/swarm_auto_loader.py` |
| 2.3 | Update preference loading | `claude/hooks/swarm_auto_loader.py` |
| 2.4 | Fix 8 hardcoded path tools | See list below |

**Tools with hardcoded paths to fix:**
1. `claude/tools/document_conversion/create_clean_orro_template.py`
2. `claude/tools/intelligent_product_grouper.py`
3. `claude/tools/morning_email_intelligence_local.py`
4. `claude/tools/macos_contacts_bridge.py`
5. `claude/tools/personal_knowledge_graph.py`
6. `claude/tools/sre/restore_maia_enterprise.py`
7. `claude/tools/services/background_learning_service.py`
8. `claude/tools/services/continuous_monitoring_service.py`

### Phase 3: Quality Gates (8 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 3.1 | Create contribution reviewer | `claude/tools/contribution_reviewer.py` |
| 3.2 | Create review command | `claude/commands/review-contribution.md` |
| 3.3 | Update pre-commit hook | `claude/hooks/pre_commit_*.py` |
| 3.4 | Create pre-push hook | `.git/hooks/pre-push` |
| 3.5 | Create post-merge hook | `.git/hooks/post-merge` |

### Phase 4: Local Data Migration (2 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 4.1 | Create setup script | `scripts/setup-team-member.sh` |
| 4.2 | Document ~/.maia/ structure | `CONTRIBUTING.md` |
| 4.3 | Create profile template | Template in setup script |
| 4.4 | Create preferences template | Template in setup script |

### Phase 5: Database Refresh System (4 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 5.1 | Create refresh script | `claude/tools/refresh_local_databases.py` |
| 5.2 | Create refresh command | `claude/commands/refresh-capabilities.md` |
| 5.3 | Integrate with post-merge hook | `.git/hooks/post-merge` |
| 5.4 | Test regeneration flow | Manual testing |

### Phase 6: Documentation (4 hours)

| Task | Description | Files Changed |
|------|-------------|---------------|
| 6.1 | Update README for team use | `README.md` |
| 6.2 | Create contribution guide | `.github/CONTRIBUTING.md` |
| 6.3 | Document architecture decision | This document |
| 6.4 | Create team onboarding guide | `docs/TEAM_ONBOARDING.md` |

### Phase 7: Testing & Validation (4 hours)

| Task | Description | Owner |
|------|-------------|-------|
| 7.1 | Test fresh clone workflow | Team member |
| 7.2 | Test contribution workflow | Team member |
| 7.3 | Test PR and merge flow | Naythan |
| 7.4 | Validate database regeneration | Maia |
| 7.5 | Security audit (no personal data leaks) | Maia |

### Total Estimated Effort: 32 hours

---

## 10. File Changes Required

### New Files to Create

| File | Purpose | Priority |
|------|---------|----------|
| `.github/CODEOWNERS` | Domain ownership | P0 |
| `.github/CONTRIBUTING.md` | Contribution guide | P0 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist | P0 |
| `.github/workflows/maia-ci.yml` | CI pipeline | P1 |
| `scripts/setup-team-member.sh` | Team onboarding | P0 |
| `claude/tools/contribution_reviewer.py` | Maia review system | P1 |
| `claude/commands/review-contribution.md` | Review command | P1 |
| `claude/tools/refresh_local_databases.py` | DB regeneration | P1 |
| `claude/commands/refresh-capabilities.md` | Refresh command | P2 |

### Existing Files to Modify

| File | Change | Priority |
|------|--------|----------|
| `.gitignore` | Add database exclusions | P0 |
| `claude/tools/core/paths.py` | Add user data paths | P0 |
| `claude/hooks/swarm_auto_loader.py` | Update session paths | P0 |
| 8 tools with hardcoded paths | Replace with dynamic | P1 |
| `README.md` | Add team usage section | P2 |

### Files to Move (Migration)

| Current | New | Notes |
|---------|-----|-------|
| `claude/context/personal/profile.md` | `~/.maia/context/personal/profile.md` | Per-user |
| `claude/data/user_preferences.json` | `~/.maia/data/user_preferences.json` | Per-user |
| `claude/data/databases/user/*_naythan.db` | `~/.maia/data/databases/user/*.db` | Per-user |

---

## 11. Team Onboarding

### Prerequisites
- Git installed
- Python 3.11+
- GitHub account with repository access

### Setup Steps (< 30 minutes)

```bash
# 1. Clone repository
git clone https://github.com/[org]/maia.git ~/maia
cd ~/maia

# 2. Run setup script
./scripts/setup-team-member.sh

# 3. Edit personal profile
vim ~/.maia/context/personal/profile.md
# Add your name, role, preferences

# 4. Verify setup
python3 claude/tools/sre/capabilities_registry.py summary
# Should show 92 agents, 278+ tools

# 5. Test Maia
# Open Claude Code in ~/maia
# Run: load
# Verify context loads correctly
```

### First Contribution Checklist

- [ ] Successfully cloned repository
- [ ] Setup script completed without errors
- [ ] Personal profile created in ~/.maia/
- [ ] Can run Maia commands locally
- [ ] Understand branch naming conventions
- [ ] Know how to run /review-contribution
- [ ] Know who to ask for PR reviews

---

## 12. Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Personal data accidentally committed | Medium | High | Pre-commit hook blocks, .gitignore |
| Database merge conflicts | Low | Medium | DBs not in Git, regenerate locally |
| Breaking change merged | Low | High | CI tests, Maia review, code owner approval |
| Team member unfamiliar with Git | Medium | Low | Onboarding guide, simple workflow |
| Path resolution fails | Low | Medium | Fallback to in-repo paths |
| CI pipeline flaky | Low | Low | Retry logic, manual override |

### Rollback Plan

If multi-user setup causes issues:

1. **Immediate**: Team members can continue with their local copy
2. **Short-term**: Disable branch protection, allow direct commits
3. **Full rollback**: Return to single-user model with personal data in repo

---

## 13. Success Metrics

### Adoption Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Team members onboarded | 100% | Count of successful setups |
| Time to first contribution | < 1 week | PR timestamp |
| Setup time | < 30 min | Onboarding feedback |

### Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Personal data leaks | 0 | Security audit |
| Failed CI runs | < 10% | GitHub Actions stats |
| PR review turnaround | < 24h | PR metrics |
| Breaking changes merged | 0 | Incident count |

### Collaboration Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| PRs per month | > 5 | GitHub stats |
| Contributors | > 3 | Unique PR authors |
| Shared improvements | > 10 | Merged PRs count |

---

## Appendix: Configuration Files

### A.1 CODEOWNERS

```gitignore
# .github/CODEOWNERS

# Default owner for everything
* @naythandawe

# Core system - require owner approval
/CLAUDE.md @naythandawe
/SYSTEM_STATE.md @naythandawe
/claude/context/core/ @naythandawe
/claude/hooks/ @naythandawe
/claude/tools/core/ @naythandawe

# Domain areas - can expand ownership later
# /claude/tools/security/ @security-lead
# /claude/tools/sre/ @sre-lead
# /claude/agents/*security* @security-lead

# Tests - broader approval
/tests/ @naythandawe
```

### A.2 PR Template

```markdown
# .github/PULL_REQUEST_TEMPLATE.md

## Summary
<!-- What does this PR do? 1-2 sentences -->

## Type of Change
- [ ] New tool (`claude/tools/`)
- [ ] New agent (`claude/agents/`)
- [ ] New command (`claude/commands/`)
- [ ] Enhancement to existing capability
- [ ] Bug fix
- [ ] Documentation only

## Checklist

### Required for All PRs
- [ ] I have run `/review-contribution` locally and it passed
- [ ] No personal data is included in this PR
- [ ] No hardcoded paths are introduced

### Required for New Capabilities
- [ ] Followed experimental → production workflow
- [ ] Tests added in `tests/`
- [ ] Tests pass locally (`python -m pytest tests/test_*.py`)
- [ ] Documentation updated (capability_index.md if applicable)

### Required for Bug Fixes
- [ ] Root cause identified and documented
- [ ] Test added to prevent regression

## Maia Review Output
<!-- Paste the output from /review-contribution -->
```
[Paste here]
```

## Testing Done
<!-- How did you verify this works? -->

## Additional Notes
<!-- Any context reviewers should know -->
```

### A.3 Contributing Guide

```markdown
# .github/CONTRIBUTING.md

# Contributing to Maia

Welcome! This guide explains how to contribute improvements to the shared Maia infrastructure.

## Quick Start

1. Clone: `git clone https://github.com/[org]/maia.git ~/maia`
2. Setup: `./scripts/setup-team-member.sh`
3. Branch: `git checkout -b feature/your-feature`
4. Develop: Make your changes, write tests
5. Review: `/review-contribution`
6. Push: `git push -u origin feature/your-feature`
7. PR: Create pull request on GitHub

## What Can I Contribute?

### Encouraged
- New tools that benefit the team
- New specialized agents
- Bug fixes
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Requires Discussion First
- Changes to core context files
- Changes to hook behavior
- Architectural changes
- Breaking changes to existing tools

## Development Workflow

### New Tools
1. Start in `claude/tools/experimental/`
2. Write tests in `tests/`
3. Test thoroughly
4. Graduate to appropriate domain directory
5. Update documentation

### Commit Messages
Follow conventional commits:
- `feat(tools): add new capability`
- `fix(hooks): resolve issue`
- `docs(readme): update section`

### Pull Requests
- One logical change per PR
- Descriptive title and summary
- Pass all CI checks
- Respond to review feedback promptly

## Code Standards

- Follow existing patterns in the codebase
- Include error handling
- No hardcoded paths (use `MAIA_ROOT` or `~/.maia/`)
- No personal data in code

## Getting Help

- Check existing documentation first
- Ask in team chat
- Tag @naythandawe for architectural questions

## Code of Conduct

Be respectful, constructive, and collaborative.
```

### A.4 CI Workflow

```yaml
# .github/workflows/maia-ci.yml
name: Maia CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          python -m pytest tests/ -v --cov=claude/tools --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for personal data
        run: |
          echo "Scanning for personal data..."
          if grep -rE "(naythandawe|/Users/naythan)" claude/ --include="*.py" --include="*.md" 2>/dev/null | grep -v ".gitignore"; then
            echo "❌ Personal data found in code"
            exit 1
          fi
          echo "✅ No personal data detected"

      - name: Check for secrets
        run: |
          echo "Scanning for potential secrets..."
          if grep -rE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]" claude/ --include="*.py" 2>/dev/null; then
            echo "⚠️ Potential secrets found - review required"
          fi
          echo "✅ Secret scan complete"

  architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Check file organization
        run: |
          python3 claude/hooks/pre_commit_file_organization.py --check || true

      - name: Verify no version indicators
        run: |
          echo "Checking for naming violations..."
          violations=$(find claude/tools -name "*_v[0-9]*" -o -name "*_new.*" -o -name "*_old.*" 2>/dev/null | grep -v experimental || true)
          if [ -n "$violations" ]; then
            echo "❌ Naming violations found:"
            echo "$violations"
            exit 1
          fi
          echo "✅ No naming violations"
```

### A.5 Setup Script

```bash
#!/bin/bash
# scripts/setup-team-member.sh

set -e

echo "🚀 Setting up Maia for team development..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Create local data directory structure
echo "📁 Creating local data directory (~/.maia/)..."
mkdir -p ~/.maia/{data/databases/user,context/personal,checkpoints,projects}
echo -e "${GREEN}   ✓ Directory structure created${NC}"

# 2. Initialize personal profile
if [ ! -f ~/.maia/context/personal/profile.md ]; then
    echo "👤 Creating personal profile template..."
    cat > ~/.maia/context/personal/profile.md << 'EOF'
# Personal Profile

## Identity
- **Name**: [Your Full Name]
- **Role**: [Your Role/Title]
- **Team**: [Your Team]

## Preferences
- **Default Agent**: maia_core_agent
- **Working Style**: [e.g., "Prefer detailed explanations", "Brief responses"]
- **Focus Areas**: [e.g., "Security", "SRE", "Data Analysis"]

## Local Paths
- **Work Projects**: ~/work_projects/
- **Notes**: [Any personal notes directory]

## Contact
- **Email**: [Your work email]
- **Slack**: [Your Slack handle]
EOF
    echo -e "${YELLOW}   → Edit ~/.maia/context/personal/profile.md with your details${NC}"
else
    echo -e "${GREEN}   ✓ Personal profile already exists${NC}"
fi

# 3. Initialize user preferences
if [ ! -f ~/.maia/data/user_preferences.json ]; then
    echo "⚙️  Creating user preferences..."
    cat > ~/.maia/data/user_preferences.json << 'EOF'
{
  "default_agent": "maia_core_agent",
  "fallback_agent": "maia_core_agent",
  "version": "1.0",
  "description": "User-specific Maia preferences",
  "created": "TIMESTAMP_PLACEHOLDER"
}
EOF
    # Replace timestamp
    sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date -u +"%Y-%m-%dT%H:%M:%SZ")/" ~/.maia/data/user_preferences.json
    rm -f ~/.maia/data/user_preferences.json.bak
    echo -e "${GREEN}   ✓ User preferences created${NC}"
else
    echo -e "${GREEN}   ✓ User preferences already exists${NC}"
fi

# 4. Install git hooks
echo "🪝 Installing git hooks..."
HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"

# Pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/bash
set -e

echo "🔍 Running pre-commit checks..."

# Check for personal data
if git diff --cached --name-only | xargs grep -l "naythandawe\|/Users/naythan" 2>/dev/null; then
    echo "❌ Personal data detected in staged files"
    exit 1
fi

# Run TDD gate if it exists
if [ -f "claude/hooks/pre_commit_tdd_gate.py" ]; then
    python3 claude/hooks/pre_commit_tdd_gate.py
fi

# Run file organization check if it exists
if [ -f "claude/hooks/pre_commit_file_organization.py" ]; then
    python3 claude/hooks/pre_commit_file_organization.py
fi

echo "✅ Pre-commit passed"
HOOK
chmod +x "$HOOKS_DIR/pre-commit"

# Post-merge hook
cat > "$HOOKS_DIR/post-merge" << 'HOOK'
#!/bin/bash
echo "🔄 Refreshing local databases..."
python3 claude/tools/sre/capabilities_registry.py scan --quiet 2>/dev/null || true
echo "✅ Local databases updated"
HOOK
chmod +x "$HOOKS_DIR/post-merge"

echo -e "${GREEN}   ✓ Git hooks installed${NC}"

# 5. Generate local databases
echo "🗄️  Generating local databases..."
if python3 claude/tools/sre/capabilities_registry.py scan --quiet 2>/dev/null; then
    echo -e "${GREEN}   ✓ Capabilities database generated${NC}"
else
    echo -e "${YELLOW}   → Database will generate on first Maia use${NC}"
fi

# 6. Summary
echo ""
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Edit your profile:    vim ~/.maia/context/personal/profile.md"
echo "  2. Pull latest changes:  git pull origin main"
echo "  3. Start Maia:           Open Claude Code in this directory"
echo "  4. Load context:         Type 'load' in Claude Code"
echo ""
echo "To contribute:"
echo "  1. Create branch:        git checkout -b feature/your-feature"
echo "  2. Make changes and test"
echo "  3. Run review:           /review-contribution"
echo "  4. Push and create PR:   git push -u origin feature/your-feature"
echo ""
echo "Questions? Check .github/CONTRIBUTING.md or ask the team."
echo ""
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-14 | Naythan + Maia | Initial plan |

---

**End of Document**
