# Maia Collaboration Infrastructure
## Consolidated Multi-User Architecture + Repository Governance

**Project ID**: COLLAB-INFRA-001
**Created**: 2026-01-03
**Status**: Implementation Ready
**Owner**: Naythan Dawe
**Agents**: DevOps Principal Architect + SRE Principal Engineer
**Supersedes**:
- `MAIA_MULTI_USER_ARCHITECTURE_PLAN.md`
- `GIT_REPOSITORY_GOVERNANCE_PROJECT.md`

---

## Executive Summary

**Problem**: Maia is a personal AI infrastructure (200+ tools, 49 agents) that needs multi-user collaboration with protection against personal data leakage and core system degradation.

**Solution**: Two-Location Architecture with Defense-in-Depth Protection
- **Data Isolation**: Shared repo (`maia/`) + Personal data (`~/.maia/`)
- **Protection Layers**: CODEOWNERS + CI Gates + Performance Baselines + Emergency Recovery

**Outcomes**:
- Zero personal data leakage (enforced separation)
- 99.9%+ core protection (automated enforcement)
- <30 min team onboarding
- <5 min emergency recovery MTTR
- +95 hours/year net productivity gain

**Investment**: ~42 hours implementation + 35 hours/year maintenance

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Structure](#2-repository-structure)
3. [Protection Tiers](#3-protection-tiers)
4. [Data Classification](#4-data-classification)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Quality Gates](#6-quality-gates)
7. [Emergency Recovery](#7-emergency-recovery)
8. [Implementation Phases](#8-implementation-phases)
9. [File Inventory](#9-file-inventory)
10. [Team Onboarding](#10-team-onboarding)
11. [Operational Procedures](#11-operational-procedures)
12. [Success Metrics](#12-success-metrics)
13. [Risk Assessment](#13-risk-assessment)

---

## 1. Architecture Overview

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Local-first** | Full offline capability, no VPN required |
| **Personal data isolation** | `~/.maia/` never touches Git |
| **Controlled sharing** | PR workflow with automated gates |
| **Defense in depth** | 5 protection layers |
| **Fast recovery** | <5 min emergency rollback |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MAIA COLLABORATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────┐         ┌─────────────────────────┐        │
│  │   SHARED REPOSITORY     │         │   LOCAL USER DATA       │        │
│  │   (Git - maia/)         │         │   (~/.maia/)            │        │
│  │                         │         │                         │        │
│  │  ┌───────────────────┐  │         │  ┌───────────────────┐  │        │
│  │  │ 🔒 PROTECTED      │  │         │  │ User Databases    │  │        │
│  │  │ claude/context/   │  │         │  │ User Preferences  │  │        │
│  │  │ claude/agents/    │  │         │  │ Personal Profile  │  │        │
│  │  │ CLAUDE.md         │  │         │  │ Checkpoints       │  │        │
│  │  └───────────────────┘  │         │  └───────────────────┘  │        │
│  │                         │         │                         │        │
│  │  ┌───────────────────┐  │         │  Never in Git           │        │
│  │  │ 🔓 TEAM WRITABLE  │  │         │  Per-user isolation     │        │
│  │  │ claude/tools/     │  │         │                         │        │
│  │  │ claude/commands/  │  │         └─────────────────────────┘        │
│  │  └───────────────────┘  │                                            │
│  │                         │         ┌─────────────────────────┐        │
│  │  ┌───────────────────┐  │         │   SESSION DATA          │        │
│  │  │ 🌐 OPEN           │  │         │   (/tmp/)               │        │
│  │  │ claude/extensions │  │         │                         │        │
│  │  │ claude/projects/  │  │         │  maia_{user}_{ctx}.json │        │
│  │  └───────────────────┘  │         │  Ephemeral              │        │
│  │                         │         │                         │        │
│  └─────────────────────────┘         └─────────────────────────┘        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     PROTECTION LAYERS                             │   │
│  │  Layer 1: CODEOWNERS (reviewer assignment)                       │   │
│  │  Layer 2: CI Quality Gates (schema, tests, security)             │   │
│  │  Layer 3: Performance Baselines (regression detection)           │   │
│  │  Layer 4: Monitoring & Alerting (CI health, change alerts)       │   │
│  │  Layer 5: Emergency Recovery (<5 min rollback)                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Structure

### Shared Repository (Git)

```
maia/                                    # Shared Git repository
├── CLAUDE.md                            # 🔒 System instructions
├── SYSTEM_STATE.md                      # 🔒 Phase history
├── README.md                            # Project overview
├── CODEOWNERS                           # Protection rules
├── requirements.txt                     # Python dependencies
├── .gitignore                           # Exclusions
│
├── .github/
│   ├── CODEOWNERS                       # Ownership rules
│   ├── CONTRIBUTING.md                  # Contribution guide
│   ├── PULL_REQUEST_TEMPLATE.md         # PR checklist
│   └── workflows/
│       ├── ci-main.yml                  # Primary CI pipeline
│       ├── ci-core-protection.yml       # Core validation (triggered)
│       ├── ci-performance.yml           # Performance baselines
│       ├── monitor-ci-health.yml        # CI health monitoring
│       ├── alert-core-change.yml        # Change notifications
│       └── emergency-rollback.yml       # Recovery workflow
│
├── scripts/
│   ├── setup-team-member.sh             # Team onboarding
│   └── refresh-databases.sh             # DB regeneration
│
├── tests/
│   ├── core/                            # Core system tests
│   ├── tools/                           # Tool tests
│   └── integration/                     # Integration tests
│
└── claude/
    ├── agents/                          # 🔒 49 specialized agents
    │   └── *_agent.md
    │
    ├── tools/                           # 🔓 200+ tools
    │   ├── core/                        # 🔒 System utilities (protected)
    │   ├── sre/                         # SRE/reliability tools
    │   ├── security/                    # Security tools
    │   ├── productivity/                # Productivity tools
    │   └── experimental/                # Work-in-progress
    │
    ├── commands/                        # 🔓 Slash commands
    │   └── *.md
    │
    ├── hooks/                           # 🔒 System hooks
    │   ├── user-prompt-submit/
    │   ├── swarm_auto_loader.py
    │   ├── pre_commit_tdd_gate.py
    │   └── contribution_reviewer.py     # NEW: Quality validation
    │
    ├── context/
    │   ├── core/                        # 🔒 System protocols
    │   ├── tools/                       # Tool documentation
    │   ├── knowledge/                   # Domain knowledge
    │   └── projects/                    # Project contexts
    │
    ├── extensions/                      # 🌐 Open contribution
    │   ├── experimental/                # Team experiments
    │   ├── plugins/                     # User plugins
    │   └── archive/                     # Deprecated items
    │
    ├── projects/                        # 🌐 User namespaces
    │   ├── template/                    # Project template
    │   └── {username}/                  # Per-user space
    │
    └── data/
        ├── databases/
        │   ├── system/                  # Generated (gitignored)
        │   ├── intelligence/            # Shared intelligence (optional)
        │   └── user/                    # MOVED to ~/.maia/
        ├── project_status/
        │   ├── active/
        │   └── archive/
        └── immutable_paths.json         # File protection rules
```

### Local User Data (~/.maia/)

```
~/.maia/                                 # Per-user, never in Git
├── data/
│   ├── databases/
│   │   └── user/                        # User-specific databases
│   │       ├── background_learning.db
│   │       ├── calendar_optimizer.db
│   │       ├── contextual_memory.db
│   │       └── preferences.db
│   ├── user_preferences.json            # Default agent, settings
│   └── checkpoints/                     # Session recovery
│
├── context/
│   └── personal/
│       └── profile.md                   # Personal identity
│
└── projects/                            # Personal work outputs
```

### Session Data (/tmp/)

```
/tmp/maia_{USERNAME}_{CONTEXT_ID}_{PID}.json   # Per-session state
```

---

## 3. Protection Tiers

### Tier Definitions

| Tier | Paths | Review Required | CI Validation |
|------|-------|-----------------|---------------|
| **PROTECTED** | `claude/context/core/`, `claude/agents/`, `claude/hooks/`, `claude/tools/core/`, `CLAUDE.md`, `SYSTEM_STATE.md` | Owner approval (1-2 reviewers) | Full suite |
| **TEAM-WRITABLE** | `claude/tools/{domain}/`, `claude/commands/` | Automated review OR owner | Standard suite |
| **OPEN** | `claude/extensions/`, `claude/projects/{user}/` | None | Basic lint |

### CODEOWNERS File

```gitignore
# .github/CODEOWNERS
# Format: path @owner

# ═══════════════════════════════════════════════════════════
# TIER 1: PROTECTED - Owner approval required
# ═══════════════════════════════════════════════════════════

# Core system files
/CLAUDE.md                              @naythandawe
/SYSTEM_STATE.md                        @naythandawe
/CODEOWNERS                             @naythandawe

# Core context (identity, protocols)
/claude/context/core/                   @naythandawe

# All agents
/claude/agents/                         @naythandawe

# System hooks
/claude/hooks/                          @naythandawe

# Core tools (path resolution, system utilities)
/claude/tools/core/                     @naythandawe

# ═══════════════════════════════════════════════════════════
# TIER 2: TEAM-WRITABLE - Automated or owner review
# ═══════════════════════════════════════════════════════════

# Domain tools - owner has visibility, automated gates primary
/claude/tools/sre/                      @naythandawe
/claude/tools/security/                 @naythandawe
/claude/tools/productivity/             @naythandawe
/claude/tools/servicedesk/              @naythandawe

# Commands
/claude/commands/                       @naythandawe

# Tests - broader approval OK
/tests/                                 @naythandawe

# ═══════════════════════════════════════════════════════════
# TIER 3: OPEN - No review required
# ═══════════════════════════════════════════════════════════

# Extensions (experimental, plugins)
/claude/extensions/

# User namespaces
/claude/projects/*/

# Documentation (non-core)
/docs/
```

---

## 4. Data Classification

### What Gets Shared vs Local

| Category | Location | In Git | Shared | Regeneration |
|----------|----------|--------|--------|--------------|
| **Agents** | `claude/agents/` | Yes | Yes | N/A |
| **Tools** | `claude/tools/` | Yes | Yes | N/A |
| **Commands** | `claude/commands/` | Yes | Yes | N/A |
| **Core Context** | `claude/context/core/` | Yes | Yes | N/A |
| **System DBs** | `claude/data/databases/system/` | No | No | Post-pull hook |
| **User DBs** | `~/.maia/data/databases/user/` | No | No | N/A |
| **User Prefs** | `~/.maia/data/user_preferences.json` | No | No | Setup script |
| **Profile** | `~/.maia/context/personal/profile.md` | No | No | Setup script |
| **Sessions** | `/tmp/maia_*` | No | No | Runtime |

### Database Strategy

**Principle**: Source files are truth, databases are cache.

```
Source of Truth (Git)              Derived Cache (Local)
─────────────────────              ────────────────────
claude/tools/*.py      ──scan──►   capabilities.db
claude/agents/*.md     ──────►     (regenerated locally)
SYSTEM_STATE.md        ──parse──►  system_state.db
```

| Database | Type | Git Status | Regeneration |
|----------|------|------------|--------------|
| `capabilities.db` | Derived | gitignored | `capabilities_registry.py scan` |
| `system_state.db` | Derived | gitignored | `system_state_etl.py` |
| `tool_discovery.db` | Derived | gitignored | Auto on scan |
| `routing_decisions.db` | Accumulated | gitignored | Local only |
| `*_user.db` | Personal | In ~/.maia/ | N/A |

### .gitignore Additions

```gitignore
# ═══════════════════════════════════════════════════════════
# DERIVED DATABASES - Regenerate locally after pull
# ═══════════════════════════════════════════════════════════
claude/data/databases/system/capabilities.db*
claude/data/databases/system/system_state.db*
claude/data/databases/system/tool_discovery.db*
claude/data/databases/system/deduplication.db*

# ═══════════════════════════════════════════════════════════
# ACCUMULATED LOCAL DATA
# ═══════════════════════════════════════════════════════════
claude/data/databases/system/routing_decisions.db*
claude/data/databases/system/conversations.db*
claude/data/databases/system/performance_metrics.db*
claude/data/databases/system/verification_hook.db*

# ═══════════════════════════════════════════════════════════
# USER DATA - Should be in ~/.maia/ but exclude if present
# ═══════════════════════════════════════════════════════════
claude/data/databases/user/

# ═══════════════════════════════════════════════════════════
# SQLITE TEMP FILES
# ═══════════════════════════════════════════════════════════
*.db-shm
*.db-wal
*.db-journal
```

---

## 5. CI/CD Pipeline

### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CI/CD WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PR OPENED                                                          │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ci-main.yml (Always runs)                                   │  │
│  │  ├─ Lint & format check                                      │  │
│  │  ├─ Unit tests                                               │  │
│  │  ├─ Security scan (no secrets, no personal data)             │  │
│  │  └─ Dependency check                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ci-core-protection.yml (If core paths changed)              │  │
│  │  ├─ Schema validation                                        │  │
│  │  ├─ Core integration tests                                   │  │
│  │  ├─ CODEOWNERS integrity check                               │  │
│  │  └─ Performance baseline check                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  alert-core-change.yml (If core paths changed)               │  │
│  │  └─ Notify owner of core change attempt                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│      │                                                              │
│      ▼                                                              │
│  REVIEW (CODEOWNERS-assigned reviewers)                            │
│      │                                                              │
│      ▼                                                              │
│  MERGE (Squash to main)                                            │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Post-merge: Team members pull → post-merge hook             │  │
│  │  └─ Regenerate local databases                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Primary CI Workflow

```yaml
# .github/workflows/ci-main.yml
name: Maia CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'

jobs:
  # ═══════════════════════════════════════════════════════════
  # JOB 1: Lint & Security
  # ═══════════════════════════════════════════════════════════
  lint-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for personal data
        run: |
          echo "🔍 Scanning for personal data..."
          if grep -rE "(naythandawe|/Users/naythan|/home/naythan)" \
             claude/ --include="*.py" --include="*.md" 2>/dev/null | \
             grep -v ".gitignore" | grep -v "CODEOWNERS"; then
            echo "❌ Personal data found in code"
            exit 1
          fi
          echo "✅ No personal data detected"

      - name: Check for hardcoded paths
        run: |
          echo "🔍 Scanning for hardcoded user paths..."
          if grep -rE "(/Users/|/home/)[a-zA-Z]+" \
             claude/tools --include="*.py" 2>/dev/null | \
             grep -v "# Example" | grep -v "test_"; then
            echo "❌ Hardcoded user paths found"
            exit 1
          fi
          echo "✅ No hardcoded paths detected"

      - name: Check for secrets
        run: |
          echo "🔍 Scanning for potential secrets..."
          patterns='(password|secret|api_key|token|credential)\s*=\s*["\x27][^"\x27]{8,}["\x27]'
          if grep -rEi "$patterns" claude/ --include="*.py" 2>/dev/null | \
             grep -v "# Example" | grep -v "test_" | grep -v "getenv"; then
            echo "⚠️ Potential secrets found - manual review required"
            exit 1
          fi
          echo "✅ Secret scan complete"

      - name: Check naming conventions
        run: |
          echo "🔍 Checking naming conventions..."
          violations=$(find claude/tools -name "*_v[0-9]*" \
                       -o -name "*_new.*" -o -name "*_old.*" \
                       -o -name "*_backup.*" 2>/dev/null | \
                       grep -v experimental || true)
          if [ -n "$violations" ]; then
            echo "❌ Naming violations found:"
            echo "$violations"
            exit 1
          fi
          echo "✅ No naming violations"

  # ═══════════════════════════════════════════════════════════
  # JOB 2: Tests
  # ═══════════════════════════════════════════════════════════
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          python -m pytest tests/ -v \
            --cov=claude/tools \
            --cov-report=xml \
            --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  # ═══════════════════════════════════════════════════════════
  # JOB 3: Architecture Check
  # ═══════════════════════════════════════════════════════════
  architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Run contribution reviewer
        run: |
          python3 claude/hooks/contribution_reviewer.py --ci
```

### Core Protection Workflow

```yaml
# .github/workflows/ci-core-protection.yml
name: Core Protection

on:
  pull_request:
    paths:
      - 'claude/context/core/**'
      - 'claude/agents/**'
      - 'claude/hooks/**'
      - 'claude/tools/core/**'
      - 'CLAUDE.md'
      - 'SYSTEM_STATE.md'
      - 'CODEOWNERS'

jobs:
  core-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for diff

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      # ─────────────────────────────────────────────────────
      # Check 1: CODEOWNERS integrity
      # ─────────────────────────────────────────────────────
      - name: Validate CODEOWNERS unchanged
        run: |
          if git diff origin/main..HEAD -- CODEOWNERS .github/CODEOWNERS | grep -q .; then
            echo "❌ CODEOWNERS modification detected"
            echo "   This requires manual security review by repository owner"
            exit 1
          fi
          echo "✅ CODEOWNERS unchanged"

      # ─────────────────────────────────────────────────────
      # Check 2: Schema validation
      # ─────────────────────────────────────────────────────
      - name: Validate core schema
        run: python3 claude/tools/sre/validate_core_schema.py

      # ─────────────────────────────────────────────────────
      # Check 3: Core integration tests
      # ─────────────────────────────────────────────────────
      - name: Core integration tests
        run: python3 -m pytest tests/core/ -v --tb=short

      # ─────────────────────────────────────────────────────
      # Check 4: Performance baseline
      # ─────────────────────────────────────────────────────
      - name: Performance baseline check
        run: python3 claude/tools/sre/performance_baseline.py --check

      # ─────────────────────────────────────────────────────
      # Summary
      # ─────────────────────────────────────────────────────
      - name: Core protection summary
        if: always()
        run: |
          echo "═══════════════════════════════════════════════"
          echo "CORE PROTECTION SUMMARY"
          echo "═══════════════════════════════════════════════"
          echo "Files changed in protected paths:"
          git diff --name-only origin/main..HEAD | grep -E "^(claude/context/core|claude/agents|claude/hooks|CLAUDE.md|SYSTEM_STATE.md)" || echo "  (none)"
          echo ""
          echo "Review required from: @naythandawe"
```

### Performance Baseline Workflow

```yaml
# .github/workflows/ci-performance.yml
name: Performance Baselines

on:
  pull_request:
    paths:
      - 'claude/context/core/**'
      - 'claude/tools/sre/smart_context_loader.py'
      - 'claude/hooks/swarm_auto_loader.py'
  schedule:
    - cron: '0 6 * * 1'  # Weekly baseline update (Monday 6 AM)

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run performance benchmarks
        run: |
          python3 claude/tools/sre/performance_baseline.py --check --verbose

      - name: Upload baseline results
        if: github.event_name == 'schedule'
        uses: actions/upload-artifact@v4
        with:
          name: performance-baseline-${{ github.run_number }}
          path: claude/data/performance_baselines.json
```

---

## 6. Quality Gates

### Gate 1: Pre-Commit (Local)

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "🔍 Running pre-commit checks..."

# ─────────────────────────────────────────────────────
# Check 1: No personal data in staged files
# ─────────────────────────────────────────────────────
echo "  Checking for personal data..."
if git diff --cached --name-only | xargs grep -l \
   "naythandawe\|/Users/naythan\|/home/naythan" 2>/dev/null; then
    echo "❌ BLOCKED: Personal data detected in staged files"
    echo "   Remove personal paths/usernames before committing"
    exit 1
fi

# ─────────────────────────────────────────────────────
# Check 2: No hardcoded absolute paths
# ─────────────────────────────────────────────────────
echo "  Checking for hardcoded paths..."
staged_py=$(git diff --cached --name-only | grep "\.py$" || true)
if [ -n "$staged_py" ]; then
    if echo "$staged_py" | xargs grep -l "/Users/\|/home/" 2>/dev/null | \
       grep -v "test_\|_test\.py"; then
        echo "❌ BLOCKED: Hardcoded user paths detected"
        echo "   Use MAIA_ROOT or ~/.maia/ instead"
        exit 1
    fi
fi

# ─────────────────────────────────────────────────────
# Check 3: TDD gate (tests exist for new tools)
# ─────────────────────────────────────────────────────
echo "  Checking TDD compliance..."
if [ -f "claude/hooks/pre_commit_tdd_gate.py" ]; then
    python3 claude/hooks/pre_commit_tdd_gate.py
fi

# ─────────────────────────────────────────────────────
# Check 4: File organization
# ─────────────────────────────────────────────────────
echo "  Checking file organization..."
if [ -f "claude/hooks/pre_commit_file_organization.py" ]; then
    python3 claude/hooks/pre_commit_file_organization.py
fi

echo "✅ Pre-commit passed"
```

### Gate 2: Pre-Push (Before Sharing)

```bash
#!/bin/bash
# .git/hooks/pre-push

set -e

# ─────────────────────────────────────────────────────
# Block direct push to main
# ─────────────────────────────────────────────────────
protected_branch='main'
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

if [ "$current_branch" = "$protected_branch" ]; then
    echo "❌ BLOCKED: Direct push to main not allowed"
    echo "   Create a feature branch and submit a PR:"
    echo "   git checkout -b feature/your-feature"
    echo "   git push -u origin feature/your-feature"
    exit 1
fi

# ─────────────────────────────────────────────────────
# Run contribution review
# ─────────────────────────────────────────────────────
echo "🤖 Running Maia contribution review..."
if [ -f "claude/hooks/contribution_reviewer.py" ]; then
    python3 claude/hooks/contribution_reviewer.py --local

    if [ $? -ne 0 ]; then
        echo "❌ BLOCKED: Contribution review failed"
        echo "   Fix the issues listed above and try again"
        exit 1
    fi
fi

echo "✅ Ready to push"
```

### Gate 3: Post-Merge (Database Refresh)

```bash
#!/bin/bash
# .git/hooks/post-merge

echo "🔄 Refreshing local databases from shared files..."

# Regenerate capabilities database
if python3 claude/tools/sre/capabilities_registry.py scan --quiet 2>/dev/null; then
    echo "  ✅ Capabilities database updated"
else
    echo "  ⚠️ Capabilities database refresh failed"
    echo "     Run manually: python3 claude/tools/sre/capabilities_registry.py scan"
fi

# Regenerate system state database
if python3 claude/tools/sre/system_state_etl.py --recent all --quiet 2>/dev/null; then
    echo "  ✅ System state database updated"
else
    echo "  ⚠️ System state database refresh failed (non-critical)"
fi

echo "✅ Post-merge complete"
```

### Gate 4: Contribution Reviewer

```python
#!/usr/bin/env python3
"""
claude/hooks/contribution_reviewer.py

Maia-powered contribution review system.
Validates changes meet quality standards before PR.

Usage:
    python3 contribution_reviewer.py --local   # Pre-push check
    python3 contribution_reviewer.py --ci      # CI check
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

MAIA_ROOT = Path(__file__).parent.parent.parent


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info


class ContributionReviewer:
    """
    Checks performed:
    1. Security - No secrets, no injection risks, no personal data
    2. Architecture - Correct paths, naming conventions
    3. TDD - Tests exist for new code
    4. Documentation - Docstrings present
    5. Dependencies - requirements.txt updated if needed
    """

    def __init__(self, ci_mode: bool = False):
        self.ci_mode = ci_mode
        self.results: List[CheckResult] = []

    def get_changed_files(self) -> List[Path]:
        """Get list of changed files vs main branch."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "origin/main..HEAD"],
                capture_output=True,
                text=True,
                cwd=MAIA_ROOT
            )
            files = [Path(f) for f in result.stdout.strip().split("\n") if f]
            return files
        except Exception:
            return []

    def get_staged_files(self) -> List[Path]:
        """Get list of staged files (for local mode)."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=MAIA_ROOT
            )
            files = [Path(f) for f in result.stdout.strip().split("\n") if f]
            return files
        except Exception:
            return []

    # ─────────────────────────────────────────────────────
    # Security Checks
    # ─────────────────────────────────────────────────────
    def check_no_secrets(self, files: List[Path]) -> CheckResult:
        """Check for hardcoded secrets."""
        import re

        secret_patterns = [
            r'(password|secret|api_key|token|credential)\s*=\s*["\'][^"\']{8,}["\']',
            r'(AWS_SECRET|AZURE_KEY|GCP_KEY)\s*=',
            r'-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----',
        ]

        violations = []
        for file in files:
            if not file.suffix == ".py":
                continue
            filepath = MAIA_ROOT / file
            if not filepath.exists():
                continue

            content = filepath.read_text()
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Exclude test files and examples
                    if "test_" not in file.name and "# Example" not in content:
                        violations.append(str(file))
                        break

        if violations:
            return CheckResult(
                name="No Secrets",
                passed=False,
                message=f"Potential secrets in: {', '.join(violations)}"
            )
        return CheckResult(name="No Secrets", passed=True, message="No secrets detected")

    def check_no_personal_data(self, files: List[Path]) -> CheckResult:
        """Check for personal data."""
        patterns = ["naythandawe", "/Users/naythan", "/home/naythan"]

        violations = []
        for file in files:
            filepath = MAIA_ROOT / file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()
                for pattern in patterns:
                    if pattern in content:
                        violations.append(str(file))
                        break
            except Exception:
                continue

        if violations:
            return CheckResult(
                name="No Personal Data",
                passed=False,
                message=f"Personal data in: {', '.join(violations)}"
            )
        return CheckResult(name="No Personal Data", passed=True, message="No personal data")

    def check_no_hardcoded_paths(self, files: List[Path]) -> CheckResult:
        """Check for hardcoded absolute paths."""
        import re

        path_pattern = r'["\']/(Users|home)/[a-zA-Z]+/'

        violations = []
        for file in files:
            if not file.suffix == ".py":
                continue
            filepath = MAIA_ROOT / file
            if not filepath.exists():
                continue

            content = filepath.read_text()
            if re.search(path_pattern, content):
                if "test_" not in file.name:
                    violations.append(str(file))

        if violations:
            return CheckResult(
                name="No Hardcoded Paths",
                passed=False,
                message=f"Hardcoded paths in: {', '.join(violations)}"
            )
        return CheckResult(name="No Hardcoded Paths", passed=True, message="No hardcoded paths")

    # ─────────────────────────────────────────────────────
    # Architecture Checks
    # ─────────────────────────────────────────────────────
    def check_file_locations(self, files: List[Path]) -> CheckResult:
        """Check files are in correct directories."""
        violations = []

        for file in files:
            # New tools should be in experimental first
            if (file.parent.name not in ["experimental", "core"] and
                str(file).startswith("claude/tools/") and
                file.suffix == ".py" and
                "_test" not in file.name):
                # Check if this is a new file
                result = subprocess.run(
                    ["git", "show", f"origin/main:{file}"],
                    capture_output=True,
                    cwd=MAIA_ROOT
                )
                if result.returncode != 0:  # File doesn't exist in main
                    violations.append(f"{file} (new tool should start in experimental/)")

        if violations:
            return CheckResult(
                name="File Locations",
                passed=False,
                message=f"Location issues: {'; '.join(violations)}",
                severity="warning"
            )
        return CheckResult(name="File Locations", passed=True, message="Files in correct locations")

    def check_naming_conventions(self, files: List[Path]) -> CheckResult:
        """Check naming conventions."""
        bad_patterns = ["_v1", "_v2", "_new", "_old", "_backup", "_copy"]

        violations = []
        for file in files:
            for pattern in bad_patterns:
                if pattern in file.stem:
                    violations.append(str(file))
                    break

        if violations:
            return CheckResult(
                name="Naming Conventions",
                passed=False,
                message=f"Bad names: {', '.join(violations)}"
            )
        return CheckResult(name="Naming Conventions", passed=True, message="Names OK")

    # ─────────────────────────────────────────────────────
    # TDD Checks
    # ─────────────────────────────────────────────────────
    def check_tests_exist(self, files: List[Path]) -> CheckResult:
        """Check that new tools have tests."""
        new_tools = []
        for file in files:
            if (str(file).startswith("claude/tools/") and
                file.suffix == ".py" and
                "_test" not in file.name and
                "__init__" not in file.name):
                new_tools.append(file)

        missing_tests = []
        for tool in new_tools:
            test_name = f"test_{tool.stem}.py"
            test_paths = [
                MAIA_ROOT / "tests" / tool.parent.name / test_name,
                MAIA_ROOT / "tests" / test_name,
            ]
            if not any(p.exists() for p in test_paths):
                missing_tests.append(str(tool))

        if missing_tests:
            return CheckResult(
                name="Tests Exist",
                passed=False,
                message=f"Missing tests for: {', '.join(missing_tests)}",
                severity="warning"
            )
        return CheckResult(name="Tests Exist", passed=True, message="Tests present")

    # ─────────────────────────────────────────────────────
    # Documentation Checks
    # ─────────────────────────────────────────────────────
    def check_docstrings(self, files: List[Path]) -> CheckResult:
        """Check that Python files have module docstrings."""
        import ast

        missing_docstrings = []
        for file in files:
            if not file.suffix == ".py":
                continue
            filepath = MAIA_ROOT / file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()
                tree = ast.parse(content)
                if not ast.get_docstring(tree):
                    missing_docstrings.append(str(file))
            except Exception:
                continue

        if missing_docstrings:
            return CheckResult(
                name="Docstrings",
                passed=True,  # Warning only
                message=f"Missing docstrings: {', '.join(missing_docstrings)}",
                severity="warning"
            )
        return CheckResult(name="Docstrings", passed=True, message="Docstrings present")

    # ─────────────────────────────────────────────────────
    # Main Review Method
    # ─────────────────────────────────────────────────────
    def review(self) -> bool:
        """Run all checks and return pass/fail."""
        if self.ci_mode:
            files = self.get_changed_files()
        else:
            files = self.get_staged_files()

        if not files:
            print("✅ No files to review")
            return True

        print(f"📋 Reviewing {len(files)} file(s)...")
        print()

        # Run all checks
        self.results = [
            self.check_no_secrets(files),
            self.check_no_personal_data(files),
            self.check_no_hardcoded_paths(files),
            self.check_file_locations(files),
            self.check_naming_conventions(files),
            self.check_tests_exist(files),
            self.check_docstrings(files),
        ]

        # Display results
        errors = []
        warnings = []

        for result in self.results:
            if result.passed:
                print(f"  ✅ {result.name}: {result.message}")
            elif result.severity == "warning":
                print(f"  ⚠️  {result.name}: {result.message}")
                warnings.append(result)
            else:
                print(f"  ❌ {result.name}: {result.message}")
                errors.append(result)

        print()

        if errors:
            print(f"❌ REVIEW FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
            return False
        elif warnings:
            print(f"⚠️  REVIEW PASSED WITH WARNINGS: {len(warnings)} warning(s)")
            return True
        else:
            print("✅ REVIEW PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(description="Maia Contribution Reviewer")
    parser.add_argument("--ci", action="store_true", help="CI mode (compare to main)")
    parser.add_argument("--local", action="store_true", help="Local mode (staged files)")
    args = parser.parse_args()

    reviewer = ContributionReviewer(ci_mode=args.ci)
    passed = reviewer.review()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
```

---

## 7. Emergency Recovery

### Emergency Rollback Workflow

```yaml
# .github/workflows/emergency-rollback.yml
name: Emergency Rollback

on:
  workflow_dispatch:
    inputs:
      target_commit:
        description: 'Commit SHA to revert to (leave empty to revert last commit)'
        required: false
      reason:
        description: 'Emergency reason (required for audit)'
        required: true
      notify_team:
        description: 'Send team notification?'
        type: boolean
        default: true

jobs:
  emergency-revert:
    runs-on: ubuntu-latest
    # Requires elevated permissions - use repository admin PAT
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.ADMIN_PAT }}  # PAT with admin access

      - name: Configure Git
        run: |
          git config user.name "Maia Emergency Bot"
          git config user.email "emergency@maia.local"

      - name: Create Revert Commit
        run: |
          echo "🚨 EMERGENCY ROLLBACK INITIATED"
          echo "Reason: ${{ inputs.reason }}"
          echo ""

          if [ -z "${{ inputs.target_commit }}" ]; then
            echo "Reverting last commit..."
            git revert --no-edit HEAD
          else
            echo "Reverting to commit ${{ inputs.target_commit }}..."
            git revert --no-edit HEAD..${{ inputs.target_commit }}
          fi

          # Amend with emergency marker
          git commit --amend -m "🚨 EMERGENCY ROLLBACK: ${{ inputs.reason }}

          Triggered by: @${{ github.actor }}
          Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
          Target: ${{ inputs.target_commit || 'HEAD~1' }}"

      - name: Push Revert
        run: git push origin main

      - name: Create Post-Mortem Issue
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `🚨 Post-Mortem: Emergency Rollback - ${{ inputs.reason }}`,
              body: `## Incident Summary

            | Field | Value |
            |-------|-------|
            | **Timestamp** | ${new Date().toISOString()} |
            | **Triggered By** | @${{ github.actor }} |
            | **Reason** | ${{ inputs.reason }} |
            | **Reverted To** | ${{ inputs.target_commit || 'HEAD~1' }} |

            ## Post-Mortem Checklist

            - [ ] Root cause identified
            - [ ] Timeline documented
            - [ ] Impact assessed
            - [ ] Prevention measures identified
            - [ ] Runbooks updated (if applicable)
            - [ ] Team notified

            ## Root Cause Analysis

            _To be completed within 24 hours_

            ## Timeline

            | Time | Event |
            |------|-------|
            | ${new Date().toISOString()} | Emergency rollback triggered |

            ## Prevention Measures

            _What changes will prevent this from recurring?_
            `,
              labels: ['incident', 'post-mortem', 'P1']
            });

      - name: Notify Team
        if: inputs.notify_team
        run: |
          echo "📢 Team notification would be sent here"
          echo "Implement: Slack webhook, email, or other notification"
          # curl -X POST ${{ secrets.SLACK_WEBHOOK }} -d '{"text": "..."}'
```

### Emergency Runbook

```markdown
# Emergency Core Rollback Runbook

## When to Use

Trigger emergency rollback when:
- ❌ Core context loading fails (users can't start Maia)
- ❌ Agent routing completely broken
- ❌ Performance degradation >50% (P95 latency doubled)
- ❌ Security vulnerability discovered in core

## Procedure (Target: <5 minutes)

### Step 1: Assess (T+0 to T+1 min)
1. Confirm the issue is core-related (not user-specific)
2. Check recent commits: `git log --oneline -5`
3. Identify the breaking commit

### Step 2: Trigger Rollback (T+1 to T+3 min)
1. Go to: `https://github.com/[org]/maia/actions/workflows/emergency-rollback.yml`
2. Click "Run workflow"
3. Fill in:
   - **Target Commit**: Leave empty (reverts last) OR paste specific SHA
   - **Reason**: Brief description (e.g., "Context loading fails after agent update")
   - **Notify Team**: ✅ Checked
4. Click "Run workflow"

### Step 3: Verify (T+3 to T+5 min)
1. Watch workflow complete (Actions tab)
2. Pull latest: `git pull origin main`
3. Test core functionality:
   ```bash
   python3 claude/tools/sre/smoke_tests.py
   ```
4. Confirm Maia loads correctly

### Step 4: Post-Mortem (T+1 hour to T+24 hours)
1. Fill in the auto-created GitHub issue
2. Document root cause
3. Identify prevention measures
4. Update this runbook if needed

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Primary | @naythandawe | Business hours |
| Backup | [TBD] | After hours |

## Manual Rollback (If Workflow Fails)

```bash
# If GitHub Actions is down, use local rollback:
git checkout main
git pull origin main
git revert HEAD  # Or: git revert <commit-sha>
git push origin main  # Requires admin access to bypass protection
```
```

---

## 8. Implementation Phases

### Overview

| Phase | Focus | Duration | Effort |
|-------|-------|----------|--------|
| **Phase 1** | Foundation | 2 days | 12 hours |
| **Phase 2** | Protection | 3 days | 16 hours |
| **Phase 3** | Quality Gates | 2 days | 8 hours |
| **Phase 4** | Documentation | 1 day | 4 hours |
| **Phase 5** | Validation | 1 day | 4 hours |
| **TOTAL** | | **~2 weeks** | **~44 hours** |

---

### Phase 1: Foundation (Days 1-2)

**Objective**: Set up local data structure and path resolution

| Task | Description | Files | Hours |
|------|-------------|-------|-------|
| 1.1 | Create `~/.maia/` directory structure | `scripts/setup-team-member.sh` | 1 |
| 1.2 | Implement dynamic path resolution | `claude/tools/core/paths.py` | 3 |
| 1.3 | Update session file paths (add PID) | `claude/hooks/swarm_auto_loader.py` | 2 |
| 1.4 | Fix 8 tools with hardcoded paths | See list below | 4 |
| 1.5 | Update `.gitignore` | `.gitignore` | 0.5 |
| 1.6 | Create user preference loader | `claude/tools/core/user_prefs.py` | 1.5 |

**Tools to Fix (Hardcoded Paths)**:
1. `claude/tools/document_conversion/create_clean_orro_template.py`
2. `claude/tools/intelligent_product_grouper.py`
3. `claude/tools/morning_email_intelligence_local.py`
4. `claude/tools/macos_contacts_bridge.py`
5. `claude/tools/personal_knowledge_graph.py`
6. `claude/tools/sre/restore_maia_enterprise.py`
7. `claude/tools/services/background_learning_service.py`
8. `claude/tools/services/continuous_monitoring_service.py`

**Deliverables**:
- ✅ `scripts/setup-team-member.sh` working
- ✅ `claude/tools/core/paths.py` with `get_user_data_path()`, `get_maia_root()`
- ✅ All 8 tools using dynamic paths
- ✅ `.gitignore` updated

---

### Phase 2: Protection (Days 3-5)

**Objective**: Set up CODEOWNERS, CI workflows, branch protection

| Task | Description | Files | Hours |
|------|-------------|-------|-------|
| 2.1 | Create CODEOWNERS | `.github/CODEOWNERS` | 1 |
| 2.2 | Create main CI workflow | `.github/workflows/ci-main.yml` | 3 |
| 2.3 | Create core protection workflow | `.github/workflows/ci-core-protection.yml` | 2 |
| 2.4 | Create performance baseline workflow | `.github/workflows/ci-performance.yml` | 1 |
| 2.5 | Implement `validate_core_schema.py` | `claude/tools/sre/validate_core_schema.py` | 3 |
| 2.6 | Implement `performance_baseline.py` (full) | `claude/tools/sre/performance_baseline.py` | 3 |
| 2.7 | Create emergency rollback workflow | `.github/workflows/emergency-rollback.yml` | 2 |
| 2.8 | Configure branch protection rules | GitHub Settings | 1 |

**Branch Protection Configuration**:
```
Repository Settings → Branches → Add rule for 'main':
✅ Require pull request (1 approval, dismiss stale)
✅ Require status checks (ci-main, ci-core-protection if applicable)
✅ Require conversation resolution
✅ Require linear history (squash merge)
❌ Allow force pushes
❌ Allow deletions
```

**Deliverables**:
- ✅ CODEOWNERS with 3-tier protection
- ✅ 4 CI workflows operational
- ✅ 2 validation tools implemented
- ✅ Branch protection enabled

---

### Phase 3: Quality Gates (Days 6-7)

**Objective**: Set up local hooks and contribution reviewer

| Task | Description | Files | Hours |
|------|-------------|-------|-------|
| 3.1 | Implement contribution reviewer | `claude/hooks/contribution_reviewer.py` | 3 |
| 3.2 | Create pre-commit hook | Template in setup script | 1 |
| 3.3 | Create pre-push hook | Template in setup script | 1 |
| 3.4 | Create post-merge hook | Template in setup script | 1 |
| 3.5 | Create core integration tests | `tests/core/test_context_loading.py` | 2 |

**Deliverables**:
- ✅ `contribution_reviewer.py` with 7 checks
- ✅ 3 Git hooks in setup script
- ✅ Core integration tests (>80% coverage)

---

### Phase 4: Documentation (Day 8)

**Objective**: Create team documentation

| Task | Description | Files | Hours |
|------|-------------|-------|-------|
| 4.1 | Create CONTRIBUTING.md | `.github/CONTRIBUTING.md` | 1.5 |
| 4.2 | Create PR template | `.github/PULL_REQUEST_TEMPLATE.md` | 0.5 |
| 4.3 | Create quick reference card | `docs/QUICK_REFERENCE.md` | 1 |
| 4.4 | Update README for team use | `README.md` | 1 |

**Deliverables**:
- ✅ CONTRIBUTING.md (contribution guide)
- ✅ PR template with checklist
- ✅ Quick reference card
- ✅ Updated README

---

### Phase 5: Validation (Day 9)

**Objective**: Test end-to-end workflows

| Task | Description | Owner | Hours |
|------|-------------|-------|-------|
| 5.1 | Test fresh clone workflow | Test user | 1 |
| 5.2 | Test contribution workflow (full PR) | Test user | 1 |
| 5.3 | Test core change rejection | Owner | 0.5 |
| 5.4 | Test emergency rollback | Owner | 0.5 |
| 5.5 | Security audit (no personal data leaks) | Owner | 1 |

**Validation Checklist**:
- [ ] Fresh clone + setup script works (<30 min)
- [ ] Team member can create PR to `claude/tools/`
- [ ] PR to `claude/agents/` requires owner approval
- [ ] CI blocks PRs with personal data
- [ ] CI blocks PRs with secrets
- [ ] Emergency rollback executes in <5 min
- [ ] Post-merge hook regenerates databases

---

## 9. File Inventory

### New Files to Create

| File | Purpose | Phase |
|------|---------|-------|
| `.github/CODEOWNERS` | Protection rules | 2 |
| `.github/CONTRIBUTING.md` | Contribution guide | 4 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist | 4 |
| `.github/workflows/ci-main.yml` | Primary CI | 2 |
| `.github/workflows/ci-core-protection.yml` | Core validation | 2 |
| `.github/workflows/ci-performance.yml` | Performance baselines | 2 |
| `.github/workflows/emergency-rollback.yml` | Recovery | 2 |
| `scripts/setup-team-member.sh` | Onboarding | 1 |
| `scripts/refresh-databases.sh` | DB regeneration | 1 |
| `claude/tools/core/paths.py` | Path resolution | 1 |
| `claude/tools/core/user_prefs.py` | User preferences | 1 |
| `claude/hooks/contribution_reviewer.py` | Quality validation | 3 |
| `claude/tools/sre/validate_core_schema.py` | Schema validation | 2 |
| `tests/core/test_context_loading.py` | Core tests | 3 |
| `tests/core/test_agent_routing.py` | Core tests | 3 |
| `docs/QUICK_REFERENCE.md` | Quick reference | 4 |

### Files to Modify

| File | Change | Phase |
|------|--------|-------|
| `.gitignore` | Add database exclusions | 1 |
| `claude/hooks/swarm_auto_loader.py` | Add PID to session path | 1 |
| 8 tools with hardcoded paths | Use dynamic paths | 1 |
| `claude/tools/sre/performance_baseline.py` | Implement fully | 2 |
| `README.md` | Add team usage section | 4 |

### Files to Move (Migration)

| Current | New | Notes |
|---------|-----|-------|
| `claude/context/personal/profile.md` | `~/.maia/context/personal/profile.md` | Template in setup |
| `claude/data/user_preferences.json` | `~/.maia/data/user_preferences.json` | Template in setup |
| `claude/data/databases/user/*` | `~/.maia/data/databases/user/*` | Per-user |

---

## 10. Team Onboarding

### Setup Script

```bash
#!/bin/bash
# scripts/setup-team-member.sh

set -e

echo "🚀 Setting up Maia for team development..."
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

MAIA_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ═══════════════════════════════════════════════════════════
# 1. Create local data directory
# ═══════════════════════════════════════════════════════════
echo "📁 Creating local data directory (~/.maia/)..."
mkdir -p ~/.maia/{data/databases/user,data/checkpoints,context/personal,projects}
echo -e "${GREEN}   ✓ Directory structure created${NC}"

# ═══════════════════════════════════════════════════════════
# 2. Initialize personal profile
# ═══════════════════════════════════════════════════════════
if [ ! -f ~/.maia/context/personal/profile.md ]; then
    echo "👤 Creating personal profile template..."
    cat > ~/.maia/context/personal/profile.md << 'EOF'
# Personal Profile

## Identity
- **Name**: [Your Full Name]
- **Role**: [Your Role/Title]
- **Team**: [Your Team]

## Preferences
- **Default Agent**: sre_principal_engineer_agent
- **Working Style**: [e.g., "Prefer detailed explanations"]
- **Focus Areas**: [e.g., "Security", "SRE", "Data Analysis"]

## Local Paths
- **Work Projects**: ~/work_projects/

## Contact
- **Email**: [Your work email]
EOF
    echo -e "${YELLOW}   → Edit ~/.maia/context/personal/profile.md with your details${NC}"
else
    echo -e "${GREEN}   ✓ Personal profile already exists${NC}"
fi

# ═══════════════════════════════════════════════════════════
# 3. Initialize user preferences
# ═══════════════════════════════════════════════════════════
if [ ! -f ~/.maia/data/user_preferences.json ]; then
    echo "⚙️  Creating user preferences..."
    cat > ~/.maia/data/user_preferences.json << EOF
{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "version": "1.0",
  "description": "User-specific Maia preferences",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
    echo -e "${GREEN}   ✓ User preferences created${NC}"
else
    echo -e "${GREEN}   ✓ User preferences already exists${NC}"
fi

# ═══════════════════════════════════════════════════════════
# 4. Install Git hooks
# ═══════════════════════════════════════════════════════════
echo "🪝 Installing Git hooks..."
HOOKS_DIR="${MAIA_ROOT}/.git/hooks"

# Pre-commit
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/bash
set -e
echo "🔍 Running pre-commit checks..."

# Check for personal data
if git diff --cached --name-only | xargs grep -l "naythandawe\|/Users/naythan" 2>/dev/null; then
    echo "❌ Personal data detected in staged files"
    exit 1
fi

# Check for hardcoded paths
staged_py=$(git diff --cached --name-only | grep "\.py$" || true)
if [ -n "$staged_py" ]; then
    if echo "$staged_py" | xargs grep -l "/Users/\|/home/" 2>/dev/null | grep -v "test_"; then
        echo "❌ Hardcoded user paths detected"
        exit 1
    fi
fi

# TDD gate
if [ -f "claude/hooks/pre_commit_tdd_gate.py" ]; then
    python3 claude/hooks/pre_commit_tdd_gate.py
fi

echo "✅ Pre-commit passed"
HOOK
chmod +x "$HOOKS_DIR/pre-commit"

# Pre-push
cat > "$HOOKS_DIR/pre-push" << 'HOOK'
#!/bin/bash
set -e

current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')
if [ "$current_branch" = "main" ]; then
    echo "❌ Direct push to main not allowed. Create a feature branch."
    exit 1
fi

if [ -f "claude/hooks/contribution_reviewer.py" ]; then
    echo "🤖 Running contribution review..."
    python3 claude/hooks/contribution_reviewer.py --local
fi

echo "✅ Ready to push"
HOOK
chmod +x "$HOOKS_DIR/pre-push"

# Post-merge
cat > "$HOOKS_DIR/post-merge" << 'HOOK'
#!/bin/bash
echo "🔄 Refreshing local databases..."
python3 claude/tools/sre/capabilities_registry.py scan --quiet 2>/dev/null || true
echo "✅ Post-merge complete"
HOOK
chmod +x "$HOOKS_DIR/post-merge"

echo -e "${GREEN}   ✓ Git hooks installed${NC}"

# ═══════════════════════════════════════════════════════════
# 5. Generate local databases
# ═══════════════════════════════════════════════════════════
echo "🗄️  Generating local databases..."
cd "$MAIA_ROOT"
if python3 claude/tools/sre/capabilities_registry.py scan --quiet 2>/dev/null; then
    echo -e "${GREEN}   ✓ Capabilities database generated${NC}"
else
    echo -e "${YELLOW}   → Database will generate on first Maia use${NC}"
fi

# ═══════════════════════════════════════════════════════════
# 6. Summary
# ═══════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Edit your profile:    vim ~/.maia/context/personal/profile.md"
echo "  2. Start Maia:           Open Claude Code in ${MAIA_ROOT}"
echo "  3. Load context:         Type 'load' in Claude Code"
echo ""
echo "To contribute:"
echo "  1. Create branch:        git checkout -b feature/your-feature"
echo "  2. Make changes"
echo "  3. Push and create PR:   git push -u origin feature/your-feature"
echo ""
echo "Documentation: .github/CONTRIBUTING.md"
echo ""
```

### First Contribution Checklist

```markdown
# First Contribution Checklist

## Before You Start
- [ ] Ran `./scripts/setup-team-member.sh` successfully
- [ ] Edited `~/.maia/context/personal/profile.md` with your details
- [ ] Verified Maia loads: type `load` in Claude Code
- [ ] Read `.github/CONTRIBUTING.md`

## Your First PR
- [ ] Created feature branch: `git checkout -b feature/my-feature`
- [ ] Made changes in allowed paths (see CODEOWNERS)
- [ ] Ran tests locally: `python -m pytest tests/`
- [ ] Committed with descriptive message
- [ ] Pushed branch: `git push -u origin feature/my-feature`
- [ ] Created PR on GitHub
- [ ] CI checks passed (green checkmarks)
- [ ] Requested review from appropriate owner

## Questions?
- Slack: #maia-support
- Docs: `.github/CONTRIBUTING.md`
```

---

## 11. Operational Procedures

### Weekly Tasks (15 min)

**Monday Morning**:
- Check CI health (any failed runs?)
- Review open PRs (any stale?)
- Scan core change alerts

### Monthly Review (30 min)

- Review protection metrics vs SLOs
- Analyze false positive rate
- Collect team feedback
- Document improvement actions

### Quarterly Maintenance (4 hours)

- Update performance baselines
- Review CI workflow efficiency
- Update documentation
- Dependency updates
- Team retrospective

---

## 12. Success Metrics

### Protection SLOs

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Core protection success | >99.9% | Any unauthorized change |
| CI uptime | >99.5% | <99% in 1 hour |
| CI execution time | <5 min P95 | >10 min |
| Emergency rollback MTTR | <5 min | >10 min |
| False positive rate | <2% | >5% |

### Team Productivity SLOs

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| PR review time (non-core) | <4 hours | >24 hours |
| PR review time (core) | <24 hours | >72 hours |
| Team toil (Git workflow) | <5 min/week | >30 min/week |
| Onboarding time | <30 min | >1 hour |

---

## 13. Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Personal data committed | Medium | High | Pre-commit hook, CI scan |
| CI pipeline down | Low | High | Health monitoring, manual fallback |
| Breaking change merged | Low | High | Multi-layer protection, rollback |
| Owner unavailable | Medium | Medium | Document backup approvers |
| False positive blocking | Medium | Low | Tunable thresholds, bypass option |

### Rollback Plan

If collaboration infrastructure causes more problems than it solves:

1. **Immediate**: Disable branch protection (Settings)
2. **Short-term**: Remove CODEOWNERS, keep CI as optional
3. **Full rollback**: Return to single-user model

**Rollback time**: <30 minutes

---

## Superseded Documents

This document supersedes:
- `MAIA_MULTI_USER_ARCHITECTURE_PLAN.md` (archive after implementation)
- `GIT_REPOSITORY_GOVERNANCE_PROJECT.md` (archive after implementation)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | DevOps Principal Architect Agent | Consolidated from two source documents |

---

**Status**: ✅ IMPLEMENTATION READY

**Next Action**: Begin Phase 1 - Foundation
