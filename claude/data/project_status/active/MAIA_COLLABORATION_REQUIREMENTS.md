# Maia Collaboration Infrastructure - Requirements

**Project ID**: COLLAB-INFRA-001
**Created**: 2026-01-03
**Status**: Approved
**Related**: [MAIA_COLLABORATION_INFRASTRUCTURE.md](MAIA_COLLABORATION_INFRASTRUCTURE.md)

---

## Problem Statement

Maia is a personal AI infrastructure (200+ tools, 49 agents) currently designed for single-user operation. The system needs to support multi-user collaboration while:
1. Preventing personal data leakage into the shared repository
2. Protecting core system integrity from breaking changes
3. Enabling team contribution with minimal friction

---

## Functional Requirements

### FR1: Data Isolation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Personal profile data must NOT be stored in the shared repository | **Must** |
| FR1.2 | User preferences must NOT be stored in the shared repository | **Must** |
| FR1.3 | User-specific databases must NOT be stored in the shared repository | **Must** |
| FR1.4 | Personal data must reside in `~/.maia/` (user home directory) | **Must** |
| FR1.5 | Session files must include user identifier to prevent collisions | **Must** |
| FR1.6 | Users may optionally sync `~/.maia/` to their own Git/cloud - Maia does not enforce or manage this | **Should** |

### FR2: Repository Protection

| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Core system files (CLAUDE.md, agents, hooks, core context) require owner approval to modify | **Must** |
| FR2.2 | Domain tools allow team contribution with automated quality gates | **Should** |
| FR2.3 | Extension/plugin areas allow open contribution without approval | **Should** |
| FR2.4 | Direct push to main branch must be blocked | **Must** |
| FR2.5 | PRs with personal data or hardcoded paths must be rejected by CI | **Must** |
| FR2.6 | PRs with potential secrets must be flagged | **Must** |

### FR3: Quality Gates

| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Pre-commit hook validates no personal data in staged files | **Must** |
| FR3.2 | Pre-push hook blocks direct push to main | **Must** |
| FR3.3 | CI validates security, naming conventions, and test coverage | **Should** |
| FR3.4 | Post-merge hook regenerates local databases from source files | **Should** |

### FR4: Team Onboarding

| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | New team member can set up and run Maia in <30 minutes | **Should** |
| FR4.2 | Setup script creates required local directory structure | **Must** |
| FR4.3 | Setup script installs Git hooks automatically | **Should** |
| FR4.4 | Setup script provides template for personal profile | **Should** |

### FR5: Emergency Recovery

| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Breaking changes to core can be reverted in <5 minutes | **Should** |
| FR5.2 | Emergency rollback workflow available via GitHub Actions | **Should** |
| FR5.3 | Rollback automatically creates post-mortem issue | **Nice to have** |

---

## Non-Functional Requirements

### NFR1: Simplicity

| ID | Requirement |
|----|-------------|
| NFR1.1 | No Git submodules - avoid complexity and technical debt |
| NFR1.2 | Single mental model: shared repo + personal `~/.maia/` |
| NFR1.3 | Personal backup strategy is user's choice, not Maia's responsibility |
| NFR1.4 | Minimal new infrastructure - leverage existing Git/GitHub features |

### NFR2: Compatibility

| ID | Requirement |
|----|-------------|
| NFR2.1 | Existing single-user workflows continue to work |
| NFR2.2 | No breaking changes to tool invocation patterns |
| NFR2.3 | Databases regenerate from source files (no migration needed) |

### NFR3: Performance

| ID | Requirement |
|----|-------------|
| NFR3.1 | CI pipeline completes in <5 minutes (P95) |
| NFR3.2 | No additional latency to Maia startup from multi-user changes |

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| No Git submodules | Technical debt, complexity, poor UX |
| No enforced personal sync | User autonomy, avoid coupling |
| Owner approval for core | Single point of accountability |
| Squash merge only | Linear history, cleaner git log |

---

## Out of Scope

| Item | Reason |
|------|--------|
| Automatic personal data sync | User responsibility |
| Multi-tenant SaaS deployment | This is for team collaboration, not multi-tenancy |
| Role-based access control | GitHub CODEOWNERS sufficient |
| Audit logging | Not required for current team size |

---

## Acceptance Criteria

| Scenario | Expected Outcome |
|----------|------------------|
| New user clones repo and runs setup script | Maia works within 30 minutes |
| User commits file with hardcoded path `/Users/naythan/` | Pre-commit hook blocks |
| User pushes PR modifying `claude/agents/*.md` | Owner approval required |
| User pushes PR modifying `claude/tools/sre/*.py` | CI gates run, owner notified |
| Core context loading breaks after merge | Emergency rollback in <5 min |
| User pulls latest changes | Post-merge hook regenerates databases |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | DevOps Principal Architect Agent | Initial requirements capture |
